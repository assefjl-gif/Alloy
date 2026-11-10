"""Linha de comando de operação (BANCO_DE_DADOS §6, DEPLOY).

    python -m app.cli migrar      # alembic upgrade head (usa DATABASE_URL)
    python -m app.cli seed        # carrega os seeds que faltam (idempotente por versão)
    python -m app.cli preparar    # migrar + seed (primeiro deploy, CI, dev com SQLite)
    python -m app.cli backup ARQ  # cópia consistente do banco (SQLite: API de backup; PostgreSQL: pg_dump)
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


def backup(url: str, destino: Path) -> dict:
    """SQLite: cópia online consistente (``sqlite3.Connection.backup``) + verificação de integridade.

    PostgreSQL: o backup é responsabilidade do ``pg_dump`` (formato custom), executado pelo operador;
    este comando só devolve o comando recomendado, sem guardar senha (docs/DEPLOY.md §3).
    """
    import sqlite3

    if not url.startswith("sqlite:///"):
        comando = 'pg_dump --format=custom --no-owner --file=BACKUP.dump "$DATABASE_URL"'
        return {"modo": "postgresql", "comando": comando}
    origem = sqlite3.connect(url.removeprefix("sqlite:///"))
    destino.parent.mkdir(parents=True, exist_ok=True)
    copia = sqlite3.connect(destino)
    try:
        origem.backup(copia)
        integridade = copia.execute("PRAGMA integrity_check").fetchone()[0]
        tabelas = copia.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    finally:
        copia.close()
        origem.close()
    if integridade != "ok":
        raise RuntimeError(f"backup corrompido: {integridade}")
    return {"modo": "sqlite", "arquivo": str(destino), "tabelas": tabelas, "integridade": integridade}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("comando", choices=("migrar", "seed", "preparar", "backup"))
    parser.add_argument("destino", nargs="?", help="arquivo de destino do backup")
    args = parser.parse_args(argv)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL não definida.", file=sys.stderr)
        return 2
    if args.comando == "backup":
        if not args.destino:
            print("informe o arquivo de destino: python -m app.cli backup var/backup.db", file=sys.stderr)
            return 2
        print(f"backup: {backup(url, Path(args.destino))}")
        return 0
    if args.comando in ("migrar", "preparar"):
        migrar()
        print("migrações aplicadas (head)")
    if args.comando in ("seed", "preparar"):
        print(f"seed: {seed(url)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
