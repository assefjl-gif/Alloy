"""Monta o ``ServicoCalculo`` com a fonte de dados certa para o ambiente.

Sem banco: seed JSON (desenvolvimento). Com banco: uma sessão por unidade de trabalho e um
retrato dos dados vigentes (``RepositorioSQL``); commit ao final, rollback em erro.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.repositories.materiais_json import repositorio_padrao
from app.repositories.materiais_sql import RepositorioSQL

from .calculo import ServicoCalculo


def criar_motor_banco(settings: Settings) -> Optional[Engine]:
    if not settings.database_url:
        return None
    return create_engine(settings.database_url, pool_pre_ping=True)


@contextmanager
def servico_calculo(settings: Settings, motor_banco: Optional[Engine]) -> Iterator[ServicoCalculo]:
    if motor_banco is None:
        repo = repositorio_padrao()
        yield ServicoCalculo(repo, repo, settings.politica_dados())
        return
    with Session(motor_banco) as sessao:
        repo = RepositorioSQL(sessao)
        yield ServicoCalculo(repo, repo, settings.politica_dados(), sessao)
        sessao.commit()


def banco_responde(motor_banco: Optional[Engine]) -> Optional[bool]:
    """None = sem banco configurado; True/False = respondeu ou não ao SELECT 1."""
    if motor_banco is None:
        return None
    try:
        with motor_banco.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — health check: qualquer falha de conexão é "não pronto"
        return False
