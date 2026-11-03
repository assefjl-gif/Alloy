"""Prepara um banco de teste pelo caminho real: migrações Alembic + carga do seed."""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.repositories.seed_sql import carregar_seeds

RAIZ_BACKEND = Path(__file__).resolve().parents[2]


def preparar_banco(url: str) -> None:
    anterior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(Config(str(RAIZ_BACKEND / "alembic.ini")), "head")
    finally:
        if anterior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = anterior
    motor = create_engine(url)
    with Session(motor) as sessao:
        carregar_seeds(sessao)
        sessao.commit()
    motor.dispose()
