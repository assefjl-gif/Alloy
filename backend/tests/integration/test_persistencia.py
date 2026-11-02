"""Persistência científica: migrações reais + seed + repositório SQL (RQ-DAD-01/03/04/06, RQ-CIE-13).

Critério central: o motor alimentado pelo BANCO dá resultado idêntico, campo a campo, ao motor
alimentado pelo JSON. Isso prova que a ida e volta pelo banco não perde nem altera dado.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.engines.crystallography import calcular_estrutura, calcular_miller, gerar_cif
from app.engines.crystallography.ligas import calcular_solucao_solida
from app.engines.procedencia import PoliticaDados
from app.engines.thermodynamics.termico import calcular_termico
from app.models import Material, ValorPropriedade, VersaoDados
from app.repositories.materiais_json import repositorio_padrao
from app.repositories.materiais_sql import RepositorioSQL
from app.repositories.seed_sql import SeedJaCarregadoComOutraVersao, carregar_seeds

JSON = repositorio_padrao()
DEV = PoliticaDados(permitir_nao_validado=True)


@pytest.fixture
def banco(sessao):
    carregar_seeds(sessao)
    sessao.commit()
    return sessao


def test_seed_e_idempotente(banco):
    antes = banco.scalar(select(func.count()).select_from(ValorPropriedade))
    assert carregar_seeds(banco) == {"fontes": 0, "elementos": 0, "materiais": 0, "valores": 0,
                                     "estruturas_material": 0}
    assert banco.scalar(select(func.count()).select_from(ValorPropriedade)) == antes


def test_seed_com_outra_versao_e_recusado(banco):
    registro = banco.get(VersaoDados, "cristalografia")
    registro.versao = "1999.01.1"
    banco.flush()
    with pytest.raises(SeedJaCarregadoComOutraVersao):
        carregar_seeds(banco)
    banco.rollback()


def test_nada_entra_como_validado(banco):
    estados = set(banco.scalars(select(ValorPropriedade.estado)))
    assert "validado" not in estados
    assert estados == {"aguardando_validacao", "rascunho"}
    assert set(banco.scalars(select(Material.estado))) == {"aguardando_validacao", "rascunho"}


def test_motor_identico_com_json_e_com_banco(banco):
    sql = RepositorioSQL(banco)
    assert [m.simbolo for m in sql.listar()] == sorted(m.simbolo for m in JSON.listar())
    assert sql.versao_dados == JSON.versao_dados
    for metal in JSON.listar():
        assert sql.obter(metal.simbolo) == metal, metal.simbolo
        assert calcular_estrutura({"nome": metal.simbolo}, sql) == calcular_estrutura({"nome": metal.simbolo}, JSON)
    assert calcular_miller({"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1], "supercelula": 2}) is not None
    cif_sql = gerar_cif({"nome": "Ti"}, sql)["content"]
    cif_json = gerar_cif({"nome": "Ti"}, JSON)["content"]
    assert cif_sql.splitlines()[2:] == cif_json.splitlines()[2:]   # linhas 0–1 trazem data e hora


@pytest.mark.parametrize("payload", [
    {"base": "Cu", "soluto": "Ni", "x": 30, "semente": 3},
    {"base": "Fe", "soluto": "C", "x": 2, "distorcer": True},
    {"base": "Mg", "soluto": "Zn", "x": 10, "n": 2},
])
def test_ligas_identicas_com_json_e_com_banco(banco, payload):
    sql = RepositorioSQL(banco)
    assert calcular_solucao_solida(payload, sql, sql, DEV) == calcular_solucao_solida(payload, JSON, JSON, DEV)


def test_termico_identico_com_json_e_com_banco(banco):
    sql = RepositorioSQL(banco)
    entrada = {"simbolo": "Fe", "estrutura": "CCC", "a_nm": 0.2866, "d_nn_nm": 0.2482, "densidade": 7.88,
               "temperatura_c": 1000}
    assert calcular_termico(entrada, sql, DEV) == calcular_termico(entrada, JSON, DEV)


def test_banco_recusa_validado_sem_fonte(banco):
    valor = banco.scalars(select(ValorPropriedade).where(ValorPropriedade.fonte_id.is_(None))).first()
    valor.estado = "validado"
    with pytest.raises(IntegrityError):
        banco.flush()
    banco.rollback()


def test_banco_recusa_dois_valores_vigentes_para_a_mesma_propriedade(banco):
    original = banco.scalars(select(ValorPropriedade)).first()
    banco.add(ValorPropriedade(material_id=original.material_id, propriedade_codigo=original.propriedade_codigo,
                               valor=original.valor, unidade=original.unidade, classe="importado",
                               estado="rascunho", vigente=True))
    with pytest.raises(IntegrityError):
        banco.flush()
    banco.rollback()


def test_correcao_preserva_versao_anterior(banco):
    """ADR-014: corrigir = nova linha vigente apontando para a antiga, que deixa de ser vigente."""
    antiga = banco.scalars(select(ValorPropriedade).where(ValorPropriedade.propriedade_codigo == "valencia")).first()
    antiga.vigente = False
    banco.flush()
    nova = ValorPropriedade(material_id=antiga.material_id, propriedade_codigo="valencia", valor=antiga.valor,
                            unidade=antiga.unidade, classe="importado", estado="rascunho", vigente=True,
                            substitui_id=antiga.id)
    banco.add(nova)
    banco.commit()
    historico = banco.scalars(select(ValorPropriedade).where(
        ValorPropriedade.material_id == antiga.material_id, ValorPropriedade.propriedade_codigo == "valencia")).all()
    assert len(historico) == 2
    assert {v.vigente for v in historico} == {True, False}
