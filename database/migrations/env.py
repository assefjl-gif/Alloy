"""Ambiente Alembic. A URL vem de DATABASE_URL (nunca do arquivo .ini — RQ-SEG-06)."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

url = os.environ.get("DATABASE_URL")
if not url:
    raise RuntimeError("Defina DATABASE_URL (ex.: postgresql+psycopg://usuario:senha@localhost:5432/alloy).")
config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
target_metadata = Base.metadata

#: Índices com expressão (ex.: ``criado_em DESC``): o autogenerate do Alembic não sabe compará-los e
#: acusaria remoção/criação a cada ``alembic check``. São mantidos à mão nas migrações.
INDICES_COM_EXPRESSAO = {"ix_execucoes_usuario_data"}


def incluir_objeto(objeto, nome, tipo, refletido, comparado_com) -> bool:
    return not (tipo == "index" and nome in INDICES_COM_EXPRESSAO)


def run_migrations_offline() -> None:
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, include_object=incluir_objeto,
                      dialect_opts={"paramstyle": "named"}, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conectavel = engine_from_config(config.get_section(config.config_ini_section, {}),
                                    prefix="sqlalchemy.", poolclass=pool.NullPool)
    with conectavel.connect() as conexao:
        context.configure(connection=conexao, target_metadata=target_metadata, compare_type=True,
                          include_object=incluir_objeto,
                          render_as_batch=conexao.dialect.name == "sqlite")
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
