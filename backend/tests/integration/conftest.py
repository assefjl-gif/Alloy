"""Banco de teste criado pelas MIGRAÇÕES reais (alembic upgrade head), não por create_all.

* SQLite em arquivo temporário: sempre (teste rápido; ADR-003 o aceita só para isto).
* PostgreSQL: só quando ALLOY_TEST_POSTGRES_URL aponta para um banco DESCARTÁVEL (marcador ``postgres``).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

RAIZ_BACKEND = Path(__file__).resolve().parents[2]


def _urls():
    yield pytest.param("sqlite", id="sqlite")
    yield pytest.param("postgres", id="postgres", marks=[
        pytest.mark.postgres,
        pytest.mark.skipif(not os.environ.get("ALLOY_TEST_POSTGRES_URL"),
                           reason="ALLOY_TEST_POSTGRES_URL não definida (PostgreSQL indisponível nesta máquina, L-01)"),
    ])


def _migrar(url: str, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", url)
    configuracao = Config(str(RAIZ_BACKEND / "alembic.ini"))
    command.upgrade(configuracao, "head")


@pytest.fixture(params=list(_urls()))
def motor_banco(request, tmp_path, monkeypatch):
    if request.param == "sqlite":
        url = f"sqlite:///{tmp_path / 'teste.db'}"
    else:
        url = os.environ["ALLOY_TEST_POSTGRES_URL"]
        limpar = create_engine(url)
        with limpar.begin() as conexao:
            conexao.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
        limpar.dispose()
    _migrar(url, monkeypatch)
    motor = create_engine(url)
    if motor.dialect.name == "sqlite":
        # SQLite só impõe chaves estrangeiras com este PRAGMA (o PostgreSQL impõe sempre).
        event.listen(motor, "connect", lambda conexao, _registro: conexao.execute("PRAGMA foreign_keys=ON"))
    yield motor
    motor.dispose()


@pytest.fixture
def sessao(motor_banco):
    with Session(motor_banco) as s:
        yield s
