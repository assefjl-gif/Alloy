"""Serviço de cálculo: procedência completa, histórico persistido e política por ambiente (Fluxos A/B)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.engines.procedencia import DadoNaoValidado, PoliticaDados, sha256_parametros
from app.models import ExecucaoCalculo, Usuario
from app.repositories.materiais_sql import RepositorioSQL
from app.repositories.seed_sql import carregar_seeds
from app.services.calculo import ServicoCalculo


@pytest.fixture
def servico_e_usuario(sessao):
    carregar_seeds(sessao)
    usuario = Usuario(nome="Estudante Teste", email="estudante.teste@exemplo.test", status="ativo",
                      email_verificado_em=datetime.now(timezone.utc))
    sessao.add(usuario)
    sessao.commit()
    repo = RepositorioSQL(sessao)
    return ServicoCalculo(repo, repo, PoliticaDados(permitir_nao_validado=True), sessao), usuario.id, sessao


def test_celula_traz_procedencia_e_fica_no_historico(servico_e_usuario):
    servico, usuario_id, sessao = servico_e_usuario
    payload = {"nome": "Cu"}
    resultado = servico.celula(payload, usuario_id)
    sessao.commit()
    p = resultado["procedencia"]
    assert p["classe"] == "analitico"
    assert p["versao_dados"] == "2026.10.1+2026.11.1-v14+2026.11.2-hea"
    assert p["calculado_em"].endswith("+00:00")
    assert any("aguardam validação" in a for a in p["avisos"])
    execucao = sessao.scalars(select(ExecucaoCalculo).where(ExecucaoCalculo.usuario_id == usuario_id)).one()
    assert execucao.operacao == "celula"
    assert execucao.parametros_sha256 == bytes.fromhex(sha256_parametros(payload))
    assert execucao.resultado["densidade"] == pytest.approx(resultado["densidade"])


def test_calculo_anonimo_nao_grava_historico(servico_e_usuario):
    servico, _, sessao = servico_e_usuario
    servico.celula({"nome": "Fe"})
    assert sessao.scalars(select(ExecucaoCalculo)).first() is None


@pytest.mark.parametrize(("operacao", "payload"), [
    ("miller", {"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1], "supercelula": 2}),
    ("solucao_solida", {"base": "Cu", "soluto": "Ni", "x": 30}),
    ("termico", {"material": "Fe", "temperatura_c": 1000}),
    ("termico", {"liga": {"base": "Cu", "soluto": "Ni", "x": 30}, "temperatura_c": 500}),
    ("termico", {"liga": {"base": "Fe", "soluto": "C", "x": 2}, "temperatura_c": 500}),
])
def test_todas_as_operacoes_sao_registradas(servico_e_usuario, operacao, payload):
    servico, usuario_id, sessao = servico_e_usuario
    getattr(servico, operacao)(payload, usuario_id)
    sessao.commit()
    assert sessao.scalars(select(ExecucaoCalculo.operacao)).all() == [operacao]


def test_termico_de_liga_usa_vizinhos_de_vegard(servico_e_usuario):
    servico, _, _ = servico_e_usuario
    r = servico.termico({"liga": {"base": "Cu", "soluto": "Ni", "x": 30}, "temperatura_c": 20})
    r_medio = 0.7 * 0.1278 + 0.3 * 0.1246
    assert r["u_nm"] / r["razao_lindemann"] == pytest.approx(2 * r_medio, rel=1e-12)


def test_politica_de_producao_recusa_dado_em_rascunho(sessao):
    carregar_seeds(sessao)
    repo = RepositorioSQL(sessao)
    servico = ServicoCalculo(repo, repo, PoliticaDados(permitir_nao_validado=False))
    with pytest.raises(DadoNaoValidado):
        servico.termico({"material": "Fe", "temperatura_c": 500})
    assert servico.celula({"nome": "Fe"})["densidade"] > 0   # célula usa o seed base, com aviso


def test_configuracao_de_producao_e_estrita(monkeypatch):
    monkeypatch.setenv("ALLOY_ENV", "prod")
    with pytest.raises(ValueError, match="ALLOY_DEMO=proibido"):
        Settings(_env_file=None)
    monkeypatch.setenv("ALLOY_DEMO", "proibido")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u@localhost/x")
    monkeypatch.setenv("ALLOY_SESSION_SECRET", "s" * 40)
    monkeypatch.setenv("ALLOY_CSRF_SECRET", "c" * 40)
    config = Settings(_env_file=None)
    assert config.politica_dados().permitir_nao_validado is False
    assert config.demo_permitido is False
    assert config.rate_limit_ativo is True
    assert config.docs_ativas is False


def test_id_de_usuario_inexistente_falha_na_chave_estrangeira(sessao):
    carregar_seeds(sessao)
    repo = RepositorioSQL(sessao)
    servico = ServicoCalculo(repo, repo, PoliticaDados(True), sessao)
    with pytest.raises(IntegrityError):
        servico.celula({"nome": "Cu"}, uuid.uuid4())
    sessao.rollback()


def test_hea_pelo_banco_igual_ao_json_e_registrado(servico_e_usuario):
    from app.repositories.materiais_json import repositorio_padrao

    servico, usuario_id, sessao = servico_e_usuario
    payload = {"nome": "AlCoCrFeNi", "composicao": dict.fromkeys(("Al", "Co", "Cr", "Fe", "Ni"), 1)}
    do_banco = servico.hea(payload, usuario_id)
    sessao.commit()
    json_repo = repositorio_padrao()
    do_json = ServicoCalculo(json_repo, json_repo, PoliticaDados(permitir_nao_validado=True)).hea(payload)
    for campo in ("dS", "delta", "VEC", "Tm", "fase", "indisponiveis"):
        assert do_banco[campo] == do_json[campo], campo
    assert do_banco["procedencia"]["dados_usados"] == do_json["procedencia"]["dados_usados"]
    execucao = sessao.scalars(select(ExecucaoCalculo)).one()
    assert (execucao.operacao, execucao.motor_codigo, execucao.classe_resultado) == ("hea_analise", "hea",
                                                                                    "estimativa_modelo")
