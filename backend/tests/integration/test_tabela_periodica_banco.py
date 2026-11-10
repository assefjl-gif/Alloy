"""Tabela periódica no banco (ADR-018): migração sobre dados existentes, carga, restrições, equivalência
com o seed JSON e backup/restauração. SQLite sempre; PostgreSQL com ALLOY_TEST_POSTGRES_URL."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cli import backup
from app.models import Elemento, PropriedadeElemento, VersaoDados
from app.repositories.elementos import RepositorioElementosJSON, RepositorioElementosSQL
from app.repositories.seed_sql import SeedJaCarregadoComOutraVersao, carregar_seeds

from .conftest import RAIZ_BACKEND


def test_migracao_0003_preserva_dados_de_instalacao_existente(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'antigo.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config(str(RAIZ_BACKEND / "alembic.ini"))
    command.upgrade(cfg, "0002")
    motor = create_engine(url)
    with motor.begin() as c:   # instalação da versão anterior: elemento sem as colunas novas
        c.execute(text("INSERT INTO elementos (simbolo, nome, numero_atomico) VALUES ('Fe', 'Ferro', NULL)"))
    command.upgrade(cfg, "head")
    with motor.connect() as c:
        linha = c.execute(text("SELECT simbolo, nome, conhecido_antiguidade, grupo FROM elementos")).one()
    assert tuple(linha) == ("Fe", "Ferro", 0, None)
    command.downgrade(cfg, "0002")   # reversível, sem perder o que já existia
    with motor.connect() as c:
        assert tuple(c.execute(text("SELECT simbolo, nome FROM elementos")).one()) == ("Fe", "Ferro")
    motor.dispose()


def test_carga_completa_idempotente_e_com_versao(sessao):
    carregar_seeds(sessao)
    sessao.commit()
    assert sessao.scalar(select(func.count()).select_from(Elemento)) == 118
    assert sessao.scalar(select(func.count()).select_from(Elemento).where(Elemento.numero_atomico.is_not(None))) == 118
    assert sessao.scalar(select(func.count()).select_from(PropriedadeElemento)) == 763
    assert sessao.get(VersaoDados, "tabela_periodica").versao == "2026.11.3-tp"
    assert carregar_seeds(sessao)["valores"] == 0          # segunda carga: nada novo
    assert sessao.get(Elemento, "Fe").nome == "Ferro" and sessao.get(Elemento, "C").numero_atomico == 6


def test_versao_diferente_do_seed_e_recusada(sessao):
    carregar_seeds(sessao)
    sessao.get(VersaoDados, "tabela_periodica").versao = "0000.antiga"
    sessao.flush()
    with pytest.raises(SeedJaCarregadoComOutraVersao):
        carregar_seeds(sessao)


@pytest.mark.parametrize("sql", [
    "INSERT INTO elementos (simbolo, nome, numero_atomico, conhecido_antiguidade) VALUES ('Xx', 'X', 119, false)",
    "INSERT INTO elementos (simbolo, nome, periodo, grupo, bloco, conhecido_antiguidade) "
    "VALUES ('Xx', 'X', 6, 3, 'f', false)",
    "INSERT INTO elementos (simbolo, nome, bloco, grupo, conhecido_antiguidade) VALUES ('Xx', 'X', 'd', NULL, false)",
    "INSERT INTO elementos (simbolo, nome, estado_padrao, conhecido_antiguidade) VALUES ('Xx', 'X', 'plasma', false)",
    "INSERT INTO elementos (simbolo, nome, ano_descoberta, conhecido_antiguidade) VALUES ('Xx', 'X', 1900, true)",
], ids=["z-119", "bloco-f-com-grupo", "bloco-d-sem-grupo", "estado-invalido", "antiguidade-com-ano"])
def test_restricoes_do_elemento_sao_impostas_pelo_banco(sessao, sql):
    with pytest.raises(IntegrityError):
        sessao.execute(text(sql))
        sessao.flush()


def _valor(**kw):
    base = dict(id=uuid.uuid4(), elemento_simbolo="Fe", propriedade_codigo="raio_van_der_waals", valor=Decimal(1),
                unidade="pm", classe="importado", fonte_id="pubchem_tabela_periodica", estado="aguardando_validacao",
                conjunto_versao="t")
    base.update(kw)
    return PropriedadeElemento(**base)


@pytest.mark.parametrize("campos", [
    {"fonte_id": None},                                     # dado científico sem fonte: proibido
    {"classe": "chute"}, {"estado": "aprovado"},
    {"incerteza": Decimal(-1)}, {"intervalo_min": Decimal(2), "intervalo_max": Decimal(1)},
    {"elemento_simbolo": "Zz"}, {"propriedade_codigo": "inexistente"},
], ids=["sem-fonte", "classe", "estado", "incerteza-negativa", "intervalo-invertido", "elemento-inexistente",
        "propriedade-inexistente"])
def test_restricoes_das_propriedades_atomicas(sessao, campos):
    carregar_seeds(sessao)
    sessao.commit()
    sessao.add(_valor(**{"propriedade_codigo": "temperatura_ebulicao", **campos}) if "propriedade_codigo" not in campos
               else _valor(**campos))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_so_um_valor_vigente_por_elemento_e_propriedade(sessao):
    carregar_seeds(sessao)
    sessao.commit()
    sessao.add(_valor())          # Fe já tem raio de van der Waals vigente
    with pytest.raises(IntegrityError):
        sessao.flush()
    sessao.rollback()
    antigo = sessao.scalar(select(PropriedadeElemento).where(
        PropriedadeElemento.elemento_simbolo == "Fe", PropriedadeElemento.propriedade_codigo == "raio_van_der_waals"))
    antigo.vigente = False        # correção = nova linha que substitui a anterior (ADR-014)
    sessao.flush()
    sessao.add(_valor(substitui_id=antigo.id, valor=Decimal(195)))
    sessao.commit()


def test_repositorio_sql_igual_ao_json_campo_a_campo(sessao):
    carregar_seeds(sessao)
    sessao.commit()
    sql, js = RepositorioElementosSQL(sessao), RepositorioElementosJSON()
    assert sql.versao_dados == js.versao_dados
    assert sql.listar() == js.listar()
    assert sql.fontes() == js.fontes()


def test_backup_sqlite_restaura_com_os_mesmos_dados(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'origem.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(Config(str(RAIZ_BACKEND / "alembic.ini")), "head")
    motor = create_engine(url)
    with Session(motor) as s:
        carregar_seeds(s)
        s.commit()
    info = backup(url, tmp_path / "copia.db")
    assert info["integridade"] == "ok" and info["tabelas"] > 30
    restaurado = create_engine(f"sqlite:///{tmp_path / 'copia.db'}")
    consulta = "SELECT count(*) FROM propriedades_elemento"
    with motor.connect() as a, restaurado.connect() as b:
        assert a.execute(text(consulta)).scalar() == b.execute(text(consulta)).scalar() == 763
    motor.dispose()
    restaurado.dispose()
    assert backup("postgresql+psycopg://u@h/db", tmp_path / "x")["modo"] == "postgresql"
