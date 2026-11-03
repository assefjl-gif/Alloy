"""Linha de comando de operação (BANCO_DE_DADOS §6, DEPLOY).

    python -m app.cli migrar      # alembic upgrade head (usa DATABASE_URL)
    python -m app.cli seed        # carrega os seeds que faltam (idempotente por versão)
    python -m app.cli preparar    # migrar + seed (primeiro deploy, CI, dev com SQLite)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.repositories.seed_sql import carregar_seeds

RAIZ_BACKEND = Path(__file__).resolve().parents[1]


def migrar() -> None:
    command.upgrade(Config(str(RAIZ_BACKEND / "alembic.ini")), "head")


def seed(url: str) -> dict:
    motor = create_engine(url)
    try:
        with Session(motor) as sessao:
            contagem = carregar_seeds(sessao)
            sessao.commit()
        return contagem
    finally:
        motor.dispose()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("comando", choices=("migrar", "seed", "preparar"))
    args = parser.parse_args(argv)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL não definida.", file=sys.stderr)
        return 2
    if args.comando in ("migrar", "preparar"):
        migrar()
        print("migrações aplicadas (head)")
    if args.comando in ("seed", "preparar"):
        print(f"seed: {seed(url)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
