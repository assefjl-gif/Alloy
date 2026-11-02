"""Repositório científico versionado e cálculos (BANCO_DE_DADOS §3.2–3.3, ADR-014)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, ComCriacao, ComId, lista_sql

ESTADOS = ("rascunho", "aguardando_validacao", "validado", "rejeitado", "arquivado")
CLASSES_VALOR = ("medido", "calculado", "estimado", "importado", "demonstrativo")
CLASSES_RESULTADO = ("analitico", "estimativa_modelo", "experimental", "simulacao_ilustrativa", "demonstrativo")
TIPOS_MATERIAL = ("elemento_puro", "liga", "hea", "composto", "intersticial")
TIPOS_FONTE = ("livro", "artigo", "norma", "base_dados", "relatorio", "outro")
STATUS_EXECUCAO = ("pendente", "em_execucao", "concluido", "falhou")


class Fonte(Base):
    __tablename__ = "fontes"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20))
    citacao: Mapped[str] = mapped_column(Text)
    doi: Mapped[Optional[str]] = mapped_column(String(200))
    url: Mapped[Optional[str]] = mapped_column(Text)
    edicao_pagina: Mapped[Optional[str]] = mapped_column(String(120))
    licenca: Mapped[Optional[str]] = mapped_column(String(120))
    observacao: Mapped[Optional[str]] = mapped_column(Text)
    conferida_por: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    conferida_em: Mapped[Optional[datetime]]
    __table_args__ = (CheckConstraint(f"tipo IN ({lista_sql(TIPOS_FONTE)})", name="tipo"),)


class Elemento(Base):
    __tablename__ = "elementos"
    simbolo: Mapped[str] = mapped_column(String(3), primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    numero_atomico: Mapped[Optional[int]] = mapped_column(unique=True)


class Estrutura(Base):
    __tablename__ = "estruturas"
    codigo: Mapped[str] = mapped_column(String(4), primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    grupo_espacial_hm: Mapped[str] = mapped_column(String(20))
    grupo_espacial_numero: Mapped[int]
    wyckoff: Mapped[str] = mapped_column(String(4))
    n: Mapped[int]
    nc: Mapped[int]


class Material(ComId, ComCriacao, Base):
    __tablename__ = "materiais"
    tipo: Mapped[str] = mapped_column(String(20))
    nome: Mapped[str] = mapped_column(String(200))
    elemento_simbolo: Mapped[Optional[str]] = mapped_column(ForeignKey("elementos.simbolo", ondelete="RESTRICT"))
    aliases: Mapped[list] = mapped_column(default=list)
    estado: Mapped[str] = mapped_column(String(25), default="rascunho")
    visibilidade: Mapped[str] = mapped_column(String(15), default="publico")
    instituicao_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("instituicoes.id", ondelete="RESTRICT"))
    origem: Mapped[str] = mapped_column(String(20), default="curado")
    criado_por: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    atualizado_em: Mapped[Optional[datetime]]
    __table_args__ = (
        CheckConstraint(f"tipo IN ({lista_sql(TIPOS_MATERIAL)})", name="tipo"),
        CheckConstraint(f"estado IN ({lista_sql(ESTADOS)})", name="estado"),
        CheckConstraint("visibilidade IN ('publico', 'instituicao', 'privado')", name="visibilidade"),
        CheckConstraint("origem IN ('curado', 'contribuicao', 'demonstrativo')", name="origem"),
        CheckConstraint("tipo NOT IN ('elemento_puro', 'intersticial') OR elemento_simbolo IS NOT NULL",
                        name="elemento_obrigatorio"),
        CheckConstraint("visibilidade = 'publico' OR instituicao_id IS NOT NULL", name="escopo_instituicao"),
        Index("ix_materiais_catalogo", "estado", "visibilidade", "tipo"),
        Index("uq_materiais_elemento_puro", "elemento_simbolo", unique=True,
              postgresql_where=text("tipo IN ('elemento_puro', 'intersticial')"),
              sqlite_where=text("tipo IN ('elemento_puro', 'intersticial')")),
    )


class Composicao(ComId, ComCriacao, Base):
    __tablename__ = "composicoes"
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materiais.id", ondelete="RESTRICT"))
    versao: Mapped[int]
    base: Mapped[str] = mapped_column(String(10))
    tolerancia_soma: Mapped[Decimal] = mapped_column(Numeric, default=Decimal("0.001"))
    vigente: Mapped[bool] = mapped_column(default=True)
    __table_args__ = (
        UniqueConstraint("material_id", "versao", name="uq_composicao_versao"),
        CheckConstraint("base IN ('atomica', 'massa')", name="base"),
    )


class ComposicaoItem(Base):
    __tablename__ = "composicao_itens"
    composicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("composicoes.id", ondelete="CASCADE"),
                                                     primary_key=True)
    elemento_simbolo: Mapped[str] = mapped_column(ForeignKey("elementos.simbolo", ondelete="RESTRICT"),
                                                  primary_key=True)
    fracao: Mapped[Decimal] = mapped_column(Numeric)
    __table_args__ = (CheckConstraint("fracao > 0 AND fracao <= 1", name="fracao"),)


class Propriedade(Base):
    __tablename__ = "propriedades"
    codigo: Mapped[str] = mapped_column(String(40), primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    grupo: Mapped[str] = mapped_column(String(20))
    unidade_si: Mapped[str] = mapped_column(String(30))
    unidade_exibicao: Mapped[str] = mapped_column(String(30))
    __table_args__ = (CheckConstraint("grupo IN ('fisica', 'mecanica', 'termica', 'cristalografica', 'quimica')",
                                      name="grupo"),)


class ValorPropriedade(ComId, ComCriacao, Base):
    """Linha imutável: corrigir = nova linha com ``substitui_id`` (ADR-014)."""

    __tablename__ = "valores_propriedade"
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materiais.id", ondelete="RESTRICT"))
    propriedade_codigo: Mapped[str] = mapped_column(ForeignKey("propriedades.codigo", ondelete="RESTRICT"))
    valor: Mapped[Decimal] = mapped_column(Numeric)
    incerteza: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    unidade: Mapped[str] = mapped_column(String(30))
    classe: Mapped[str] = mapped_column(String(15))
    condicoes: Mapped[Optional[dict]]
    fonte_id: Mapped[Optional[str]] = mapped_column(ForeignKey("fontes.id", ondelete="RESTRICT"))
    estado: Mapped[str] = mapped_column(String(25), default="rascunho")
    substitui_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("valores_propriedade.id",
                                                                         ondelete="RESTRICT"))
    vigente: Mapped[bool] = mapped_column(default=True)
    origem: Mapped[Optional[str]] = mapped_column(Text)
    criado_por: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    __table_args__ = (
        CheckConstraint(f"classe IN ({lista_sql(CLASSES_VALOR)})", name="classe"),
        CheckConstraint(f"estado IN ({lista_sql(ESTADOS)})", name="estado"),
        CheckConstraint("estado <> 'validado' OR fonte_id IS NOT NULL", name="validado_exige_fonte"),
        Index("uq_valores_vigentes", "material_id", "propriedade_codigo", unique=True,
              postgresql_where=text("vigente"), sqlite_where=text("vigente")),
    )


class MaterialEstrutura(ComId, Base):
    """Estrutura e rede medida por fase/faixa de temperatura (substitui ALOTROPIA e o a medido)."""

    __tablename__ = "materiais_estruturas"
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materiais.id", ondelete="RESTRICT"))
    estrutura_codigo: Mapped[str] = mapped_column(ForeignKey("estruturas.codigo", ondelete="RESTRICT"))
    fase: Mapped[Optional[str]] = mapped_column(String(20))
    temperatura_min_c: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    temperatura_max_c: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    referencia_ambiente: Mapped[bool] = mapped_column(default=False)
    c_a: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    a_nm: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    c_nm: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    fonte_id: Mapped[Optional[str]] = mapped_column(ForeignKey("fontes.id", ondelete="RESTRICT"))
    fonte_rede_id: Mapped[Optional[str]] = mapped_column(ForeignKey("fontes.id", ondelete="RESTRICT"))
    estado: Mapped[str] = mapped_column(String(25), default="rascunho")
    __table_args__ = (
        CheckConstraint(f"estado IN ({lista_sql(ESTADOS)})", name="estado"),
        CheckConstraint("estado <> 'validado' OR fonte_id IS NOT NULL", name="validado_exige_fonte"),
        CheckConstraint("c_nm IS NULL OR a_nm IS NOT NULL", name="c_exige_a"),
    )


class Processamento(ComId, Base):
    __tablename__ = "processamentos"
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materiais.id", ondelete="RESTRICT"))
    descricao: Mapped[str] = mapped_column(Text)
    tratamento_termico: Mapped[Optional[dict]]
    fonte_id: Mapped[Optional[str]] = mapped_column(ForeignKey("fontes.id", ondelete="RESTRICT"))


class RevisaoValidacao(ComId, ComCriacao, Base):
    __tablename__ = "revisoes_validacao"
    entidade: Mapped[str] = mapped_column(String(30))
    entidade_id: Mapped[uuid.UUID]
    de_estado: Mapped[str] = mapped_column(String(25))
    para_estado: Mapped[str] = mapped_column(String(25))
    revisor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    comentario: Mapped[Optional[str]] = mapped_column(Text)


class EntalpiaPar(Base):
    __tablename__ = "entalpias_pares"
    elemento_a: Mapped[str] = mapped_column(ForeignKey("elementos.simbolo", ondelete="RESTRICT"), primary_key=True)
    elemento_b: Mapped[str] = mapped_column(ForeignKey("elementos.simbolo", ondelete="RESTRICT"), primary_key=True)
    fonte_id: Mapped[str] = mapped_column(ForeignKey("fontes.id", ondelete="RESTRICT"), primary_key=True)
    dh_mix_kj_mol: Mapped[Decimal] = mapped_column(Numeric)
    modelo: Mapped[Optional[str]] = mapped_column(String(40))
    __table_args__ = (CheckConstraint("elemento_a < elemento_b", name="par_ordenado"),)


class Motor(Base):
    __tablename__ = "motores"
    codigo: Mapped[str] = mapped_column(String(30), primary_key=True)
    versao: Mapped[str] = mapped_column(String(20), primary_key=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(default=True)


class ExecucaoCalculo(ComId, ComCriacao, Base):
    __tablename__ = "execucoes_calculo"
    usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    instituicao_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("instituicoes.id", ondelete="RESTRICT"))
    motor_codigo: Mapped[str] = mapped_column(String(30))
    motor_versao: Mapped[str] = mapped_column(String(20))
    versao_dados: Mapped[str] = mapped_column(String(60))
    operacao: Mapped[str] = mapped_column(String(30))
    parametros: Mapped[dict]
    parametros_sha256: Mapped[bytes] = mapped_column(LargeBinary(32), index=True)
    resultado: Mapped[Optional[dict]]
    classe_resultado: Mapped[str] = mapped_column(String(25))
    status: Mapped[str] = mapped_column(String(15), default="concluido")
    erro: Mapped[Optional[str]] = mapped_column(Text)
    duracao_ms: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    material_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("materiais.id", ondelete="RESTRICT"))
    __table_args__ = (
        CheckConstraint(f"classe_resultado IN ({lista_sql(CLASSES_RESULTADO)})", name="classe"),
        CheckConstraint(f"status IN ({lista_sql(STATUS_EXECUCAO)})", name="status"),
        Index("ix_execucoes_usuario_data", "usuario_id", text("criado_em DESC")),
        ForeignKeyConstraint(["motor_codigo", "motor_versao"], ["motores.codigo", "motores.versao"],
                             name="fk_execucoes_calculo_motor", ondelete="RESTRICT"),
    )


class VersaoDados(Base):
    """Versão de cada conjunto de seed carregado (vai para ``procedencia.versao_dados``)."""

    __tablename__ = "versoes_dados"
    conjunto: Mapped[str] = mapped_column(String(40), primary_key=True)
    versao: Mapped[str] = mapped_column(String(40))
    carregado_em: Mapped[datetime]
