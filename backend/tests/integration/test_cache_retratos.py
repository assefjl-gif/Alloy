"""Cache de retratos (auditoria de latência): reutiliza, mas nunca serve dado vencido depois de mudança."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.models import PropriedadeElemento, ValorPropriedade, VersaoDados
from app.repositories.cache_dados import CacheRetratos, cache_retratos
from app.repositories.elementos import retrato_elementos
from app.repositories.materiais_sql import retrato_materiais
from app.repositories.seed_sql import carregar_seeds


def _contar_sql(motor):
    contador = {"n": 0}
    event.listen(motor, "before_cursor_execute", lambda *a, **k: contador.__setitem__("n", contador["n"] + 1))
    return contador


def test_reusa_o_retrato_com_uma_unica_consulta_por_chamada(motor_banco):
    with Session(motor_banco) as s:
        carregar_seeds(s)
        s.commit()
    cache_retratos.invalidar()
    contador = _contar_sql(motor_banco)
    with Session(motor_banco) as s:
        a = retrato_materiais(s)
        primeira = contador["n"]
        b = retrato_materiais(s)
        assert a is b and contador["n"] - primeira == 1          # só a conferência de versão
        assert retrato_elementos(s).listar()[25]["simbolo"] == "Fe"


def test_commit_de_valor_cientifico_invalida(motor_banco):
    with Session(motor_banco) as s:
        carregar_seeds(s)
        s.commit()
        antes = retrato_elementos(s)
        fe = s.scalar(select(PropriedadeElemento).where(PropriedadeElemento.elemento_simbolo == "Fe",
                                                        PropriedadeElemento.propriedade_codigo == "densidade"))
        fe.estado = "validado"      # revisão humana registrada (ADR-014)
        s.commit()
        depois = retrato_elementos(s)
    assert depois is not antes
    props = {p["codigo"]: p for p in depois.listar()[25]["propriedades"]}
    assert props["densidade"]["estado"] == "validado"


def test_rollback_nao_invalida_e_troca_de_versao_invalida(motor_banco):
    with Session(motor_banco) as s:
        carregar_seeds(s)
        s.commit()
        antes = retrato_materiais(s)
        v = s.scalar(select(ValorPropriedade))
        v.valor = v.valor + Decimal(1)
        s.flush()
        s.rollback()
        assert retrato_materiais(s) is antes
        s.get(VersaoDados, "hea").versao = "outra"   # outro processo recarregou o seed: muda a chave
        s.flush()
        assert retrato_materiais(s) is not antes
        s.rollback()


def test_ttl_expira():
    cache = CacheRetratos(ttl=0)
    assert cache.obter("k", object) is not cache.obter("k", object)
    cache = CacheRetratos(ttl=60)
    assert cache.obter("k", object) is cache.obter("k", object) and (cache.acertos, cache.faltas) == (1, 1)
