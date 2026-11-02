"""Educacional, professor, caderno, arquivos e auditoria (BANCO_DE_DADOS §3.4–3.5)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, ComCriacao, ComId, agora, lista_sql

TIPOS_ATIVIDADE = ("exercicio", "abp", "quiz", "simulacao")
ESTADOS_ATIVIDADE = ("rascunho", "publicada", "arquivada")
TIPOS_QUESTAO = ("numerico", "multipla_escolha", "verdadeiro_falso", "miller", "texto_curto", "tabela_numerica")
TIPOS_ERRO = ("unidade", "fator_10n", "sinal", "indice_oposto", "conceitual", "nao_classificado")
STATUS_ENTREGA = ("em_andamento", "entregue", "avaliada")
EXTENSOES_ARQUIVO = ("txt", "md", "mp4", "webm", "pdf", "csv", "xlsx", "xls", "ods", "docx", "doc", "odt")
CATEGORIAS_ARQUIVO = ("tutorial", "anexo_atividade", "anexo_nota")


class Atividade(ComId, ComCriacao, Base):
    __tablename__ = "atividades"
    instituicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituicoes.id", ondelete="RESTRICT"))
    autor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    titulo: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(15))
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    materiais_ids: Mapped[list] = mapped_column(default=list)
    estado: Mapped[str] = mapped_column(String(15), default="rascunho")
    versao: Mapped[int] = mapped_column(default=1)
    __mapper_args__ = {"version_id_col": versao}
    __table_args__ = (
        CheckConstraint(f"tipo IN ({lista_sql(TIPOS_ATIVIDADE)})", name="tipo"),
        CheckConstraint(f"estado IN ({lista_sql(ESTADOS_ATIVIDADE)})", name="estado"),
    )


class Questao(ComId, ComCriacao, Base):
    """``gabarito`` e ``resolucao`` NUNCA são serializados para estudante (A/docs/3, RQ-EDU-04)."""

    __tablename__ = "questoes"
    instituicao_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("instituicoes.id", ondelete="RESTRICT"))
    autor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    versao: Mapped[int] = mapped_column(default=1)
    tipo: Mapped[str] = mapped_column(String(20))
    titulo: Mapped[str] = mapped_column(String(120))
    enunciado: Mapped[str] = mapped_column(Text)
    pergunta_publica: Mapped[dict] = mapped_column(default=dict)
    gabarito: Mapped[dict]
    parametros: Mapped[Optional[dict]]
    politica: Mapped[dict] = mapped_column(default=dict)
    resolucao: Mapped[Optional[list]]
    dicas: Mapped[list] = mapped_column(default=list)
    topicos: Mapped[list] = mapped_column(default=list)
    dificuldade: Mapped[int] = mapped_column(default=1)
    publicada: Mapped[bool] = mapped_column(default=False)
    __mapper_args__ = {"version_id_col": versao}
    __table_args__ = (
        CheckConstraint(f"tipo IN ({lista_sql(TIPOS_QUESTAO)})", name="tipo"),
        CheckConstraint("dificuldade BETWEEN 1 AND 5", name="dificuldade"),
    )


class AtividadeQuestao(Base):
    __tablename__ = "atividade_questoes"
    atividade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("atividades.id", ondelete="CASCADE"), primary_key=True)
    questao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questoes.id", ondelete="RESTRICT"), primary_key=True)
    ordem: Mapped[int]
    peso: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(1))


class Atribuicao(ComId, ComCriacao, Base):
    __tablename__ = "atribuicoes"
    atividade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("atividades.id", ondelete="RESTRICT"))
    turma_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("turmas.id", ondelete="RESTRICT"))
    abre_em: Mapped[Optional[datetime]]
    fecha_em: Mapped[Optional[datetime]]
    criterios: Mapped[dict] = mapped_column(default=dict)
    criado_por: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    __table_args__ = (CheckConstraint("fecha_em IS NULL OR abre_em IS NULL OR fecha_em > abre_em", name="prazo"),)


class InstanciaQuestao(ComId, ComCriacao, Base):
    __tablename__ = "instancias_questao"
    questao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questoes.id", ondelete="RESTRICT"))
    questao_versao: Mapped[int]
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    atribuicao_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("atribuicoes.id", ondelete="RESTRICT"))
    semente: Mapped[int] = mapped_column(BigInteger)
    parametros_sorteados: Mapped[dict] = mapped_column(default=dict)
    gabarito_calculado: Mapped[dict]
    versao_motor: Mapped[Optional[str]] = mapped_column(String(20))
    __table_args__ = (UniqueConstraint("questao_id", "usuario_id", "atribuicao_id", "semente", name="uq_instancia"),)


class Tentativa(ComId, ComCriacao, Base):
    __tablename__ = "tentativas"
    instancia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instancias_questao.id", ondelete="RESTRICT"))
    n: Mapped[int]
    resposta: Mapped[dict]
    resposta_normalizada: Mapped[Optional[dict]]
    correta: Mapped[bool]
    pontuacao: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    tipo_erro: Mapped[Optional[str]] = mapped_column(String(20))
    tempo_ms: Mapped[Optional[int]]
    dicas_usadas: Mapped[int] = mapped_column(default=0)
    gabarito_visto: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (
        UniqueConstraint("instancia_id", "n", name="uq_tentativa_n"),
        CheckConstraint(f"tipo_erro IS NULL OR tipo_erro IN ({lista_sql(TIPOS_ERRO)})", name="tipo_erro"),
        CheckConstraint("tempo_ms IS NULL OR (tempo_ms >= 0 AND tempo_ms <= 3600000)", name="tempo"),
    )


class Entrega(ComId, Base):
    __tablename__ = "entregas"
    atribuicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("atribuicoes.id", ondelete="RESTRICT"))
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(15), default="em_andamento")
    entregue_em: Mapped[Optional[datetime]]
    __table_args__ = (
        UniqueConstraint("atribuicao_id", "usuario_id", name="uq_entrega"),
        CheckConstraint(f"status IN ({lista_sql(STATUS_ENTREGA)})", name="status"),
        Index("ix_entregas_painel", "atribuicao_id", "status"),
    )


class Nota(ComId, Base):
    __tablename__ = "notas"
    entrega_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entregas.id", ondelete="RESTRICT"))
    valor: Mapped[Decimal] = mapped_column(Numeric)
    lancada_por: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    lancada_em: Mapped[datetime] = mapped_column(default=agora)
    comentario: Mapped[Optional[str]] = mapped_column(Text)
    substitui_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("notas.id", ondelete="RESTRICT"))


class CadernoNota(ComId, Base):
    __tablename__ = "caderno_notas"
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    conteudo: Mapped[str] = mapped_column(Text, default="")
    cena: Mapped[Optional[dict]]
    atualizado_em: Mapped[datetime] = mapped_column(default=agora)
    versao: Mapped[int] = mapped_column(default=1)
    __mapper_args__ = {"version_id_col": versao}


class Arquivo(ComId, ComCriacao, Base):
    __tablename__ = "arquivos"
    sha256: Mapped[bytes] = mapped_column(LargeBinary(32))
    nome_original: Mapped[str] = mapped_column(String(160))
    tipo_mime: Mapped[str] = mapped_column(String(120))
    extensao: Mapped[str] = mapped_column(String(5))
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger)
    categoria: Mapped[str] = mapped_column(String(20))
    dono_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    instituicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituicoes.id", ondelete="RESTRICT"))
    visibilidade: Mapped[str] = mapped_column(String(15), default="instituicao")
    arquivado_em: Mapped[Optional[datetime]]
    __table_args__ = (
        CheckConstraint(f"extensao IN ({lista_sql(EXTENSOES_ARQUIVO)})", name="extensao"),
        CheckConstraint(f"categoria IN ({lista_sql(CATEGORIAS_ARQUIVO)})", name="categoria"),
        CheckConstraint("tamanho_bytes >= 0", name="tamanho"),
        Index("ix_arquivos_biblioteca", "instituicao_id", "categoria"),
    )


class Auditoria(Base):
    """Append-only: o usuário de banco da aplicação não recebe UPDATE nem DELETE nesta tabela."""

    __tablename__ = "auditoria"
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True,
                                    autoincrement=True)
    ator_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    acao: Mapped[str] = mapped_column(String(60))
    entidade: Mapped[str] = mapped_column(String(40))
    entidade_id: Mapped[Optional[str]] = mapped_column(String(60))
    antes: Mapped[Optional[dict]]
    depois: Mapped[Optional[dict]]
    request_id: Mapped[Optional[str]] = mapped_column(String(64))
    ip: Mapped[Optional[str]] = mapped_column(String(45))
    criado_em: Mapped[datetime] = mapped_column(default=agora)
