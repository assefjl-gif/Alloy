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

from .autenticacao import LimitadorLogin, ServicoAutenticacao
from .calculo import ServicoCalculo
from .educacao import ServicoEducacao
from .erros import CapacidadeIndisponivel


def criar_motor_banco(settings: Settings) -> Optional[Engine]:
    if not settings.database_url:
        return None
    return create_engine(settings.database_url, pool_pre_ping=True)


@contextmanager
def unidade_de_trabalho(motor_banco: Optional[Engine]) -> Iterator[Optional[Session]]:
    """Uma sessão por requisição, compartilhada por todos os serviços dela; commit no fim, rollback em erro."""
    if motor_banco is None:
        yield None
        return
    with Session(motor_banco) as sessao:
        try:
            yield sessao
            sessao.commit()
        except BaseException:
            sessao.rollback()
            raise


def montar_servico_calculo(settings: Settings, sessao: Optional[Session]) -> ServicoCalculo:
    if sessao is None:
        repo = repositorio_padrao()
        return ServicoCalculo(repo, repo, settings.politica_dados())
    repo_sql = RepositorioSQL(sessao)
    return ServicoCalculo(repo_sql, repo_sql, settings.politica_dados(), sessao)


@contextmanager
def servico_calculo(settings: Settings, motor_banco: Optional[Engine]) -> Iterator[ServicoCalculo]:
    with unidade_de_trabalho(motor_banco) as sessao:
        yield montar_servico_calculo(settings, sessao)


def montar_servico_autenticacao(sessao: Optional[Session], limitador: LimitadorLogin) -> ServicoAutenticacao:
    if sessao is None:
        raise CapacidadeIndisponivel("Contas de usuário exigem banco de dados (DATABASE_URL); "
                                     "este servidor roda só com o seed JSON.")
    return ServicoAutenticacao(sessao, limitador)


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


def montar_servico_educacao(sessao: Optional[Session]) -> ServicoEducacao:
    if sessao is None:
        raise CapacidadeIndisponivel("Questões e progresso exigem banco de dados (DATABASE_URL).")
    return ServicoEducacao(sessao, RepositorioSQL(sessao))
