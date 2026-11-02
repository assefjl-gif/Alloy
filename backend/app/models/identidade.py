"""Identidade, acesso e organização acadêmica (BANCO_DE_DADOS §3.1)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, Index, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, ComCriacao, ComId, lista_sql

STATUS_USUARIO = ("ativo", "bloqueado", "pendente", "anonimizado")
PAPEIS_INSTITUCIONAIS = ("admin_institucional", "professor", "estudante", "pesquisador")
PAPEIS_TURMA = ("estudante", "monitor", "professor_assistente")
STATUS_MATRICULA = ("ativa", "trancada", "concluida")
FINALIDADES_TOKEN = ("verificar_email", "redefinir_senha")


class Usuario(ComId, ComCriacao, Base):
    __tablename__ = "usuarios"
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    senha_hash: Mapped[Optional[str]] = mapped_column(Text)
    email_verificado_em: Mapped[Optional[datetime]]
    admin_geral: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default="pendente")
    ultimo_acesso_em: Mapped[Optional[datetime]]
    __table_args__ = (
        CheckConstraint(f"status IN ({lista_sql(STATUS_USUARIO)})", name="status"),
        CheckConstraint("email = lower(email)", name="email_minusculo"),
    )


class Sessao(ComId, Base):
    __tablename__ = "sessoes"
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    token_sha256: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True)
    csrf_sha256: Mapped[bytes] = mapped_column(LargeBinary(32))
    criada_em: Mapped[datetime]
    ultimo_uso_em: Mapped[datetime]
    expira_em: Mapped[datetime]
    revogada_em: Mapped[Optional[datetime]]
    ip_criacao: Mapped[Optional[str]] = mapped_column(String(45))
    agente_usuario: Mapped[Optional[str]] = mapped_column(String(200))
    __table_args__ = (Index("ix_sessoes_usuario_ativas", "usuario_id", "revogada_em"),)


class TokenUsoUnico(ComId, Base):
    __tablename__ = "tokens_uso_unico"
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    finalidade: Mapped[str] = mapped_column(String(30))
    token_sha256: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True)
    expira_em: Mapped[datetime]
    usado_em: Mapped[Optional[datetime]]
    __table_args__ = (CheckConstraint(f"finalidade IN ({lista_sql(FINALIDADES_TOKEN)})", name="finalidade"),)


class Consentimento(ComId, Base):
    __tablename__ = "consentimentos"
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    finalidade: Mapped[str] = mapped_column(String(60))
    versao_texto: Mapped[str] = mapped_column(String(20))
    concedido_em: Mapped[datetime]
    revogado_em: Mapped[Optional[datetime]]


class Instituicao(ComId, ComCriacao, Base):
    __tablename__ = "instituicoes"
    nome: Mapped[str] = mapped_column(String(200))
    sigla: Mapped[Optional[str]] = mapped_column(String(30))
    configuracoes: Mapped[dict] = mapped_column(default=dict)
    arquivado_em: Mapped[Optional[datetime]]


class VinculoInstitucional(ComId, ComCriacao, Base):
    __tablename__ = "vinculos_institucionais"
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    instituicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituicoes.id", ondelete="RESTRICT"))
    papel: Mapped[str] = mapped_column(String(30))
    __table_args__ = (
        UniqueConstraint("usuario_id", "instituicao_id", "papel", name="uq_vinculo"),
        CheckConstraint(f"papel IN ({lista_sql(PAPEIS_INSTITUCIONAIS)})", name="papel"),
    )


class Curso(ComId, Base):
    __tablename__ = "cursos"
    instituicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituicoes.id", ondelete="RESTRICT"))
    nome: Mapped[str] = mapped_column(String(200))
    codigo: Mapped[str] = mapped_column(String(30))
    __table_args__ = (UniqueConstraint("instituicao_id", "codigo", name="uq_curso_codigo"),)


class Turma(ComId, ComCriacao, Base):
    __tablename__ = "turmas"
    instituicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituicoes.id", ondelete="RESTRICT"), index=True)
    curso_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cursos.id", ondelete="RESTRICT"))
    disciplina: Mapped[str] = mapped_column(String(200))
    periodo: Mapped[str] = mapped_column(String(10))
    professor_responsavel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    codigo_convite: Mapped[Optional[str]] = mapped_column(String(16), unique=True)
    arquivada_em: Mapped[Optional[datetime]]


class Matricula(ComId, ComCriacao, Base):
    __tablename__ = "matriculas"
    turma_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("turmas.id", ondelete="RESTRICT"))
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True)
    papel_turma: Mapped[str] = mapped_column(String(30), default="estudante")
    status: Mapped[str] = mapped_column(String(20), default="ativa")
    __table_args__ = (
        UniqueConstraint("turma_id", "usuario_id", name="uq_matricula"),
        CheckConstraint(f"papel_turma IN ({lista_sql(PAPEIS_TURMA)})", name="papel_turma"),
        CheckConstraint(f"status IN ({lista_sql(STATUS_MATRICULA)})", name="status"),
    )


class PreferenciasUsuario(Base):
    __tablename__ = "preferencias_usuario"
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    tema: Mapped[Optional[str]] = mapped_column(String(10))
    idioma: Mapped[Optional[str]] = mapped_column(String(10))
    cores_elementos: Mapped[dict] = mapped_column(default=dict)
    atualizado_em: Mapped[Optional[datetime]]
