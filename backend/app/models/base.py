"""Base declarativa e tipos portáveis (PostgreSQL em produção; SQLite só no teste rápido — ADR-003)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, MetaData, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

#: Nomes determinísticos de constraints: migrações Alembic estáveis e legíveis.
CONVENCAO = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

#: JSON portátil: JSONB no PostgreSQL (indexável), JSON no SQLite.
JsonB = JSON().with_variant(JSONB(), "postgresql")


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO)
    type_annotation_map = {dict: JsonB, list: JsonB, uuid.UUID: Uuid, datetime: DateTime(timezone=True)}


class ComId:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class ComCriacao:
    criado_em: Mapped[datetime] = mapped_column(default=agora)


def lista_sql(valores) -> str:
    """Valores para CHECK ... IN (...), com aspas simples escapadas."""
    return ", ".join("'" + v.replace("'", "''") + "'" for v in valores)
