"""Modelos SQLAlchemy 2.x do Alloy Virtual Lab (esquema em docs/BANCO_DE_DADOS.md)."""

from .base import Base
from .ciencia import (
    Composicao,
    ComposicaoItem,
    Elemento,
    EntalpiaPar,
    Estrutura,
    ExecucaoCalculo,
    Fonte,
    Material,
    MaterialEstrutura,
    Motor,
    Processamento,
    Propriedade,
    RevisaoValidacao,
    ValorPropriedade,
    VersaoDados,
)
from .educacional import (
    Arquivo,
    Atividade,
    AtividadeQuestao,
    Atribuicao,
    Auditoria,
    CadernoNota,
    Entrega,
    InstanciaQuestao,
    Nota,
    Questao,
    Tentativa,
)
from .identidade import (
    Consentimento,
    Curso,
    Instituicao,
    Matricula,
    PreferenciasUsuario,
    Sessao,
    TokenUsoUnico,
    Turma,
    Usuario,
    VinculoInstitucional,
)

__all__ = [
    "Arquivo", "Atividade", "AtividadeQuestao", "Atribuicao", "Auditoria", "Base", "CadernoNota", "Composicao",
    "ComposicaoItem", "Consentimento", "Curso", "Elemento", "EntalpiaPar", "Entrega", "Estrutura",
    "ExecucaoCalculo", "Fonte", "InstanciaQuestao", "Instituicao", "Material", "MaterialEstrutura", "Matricula",
    "Motor", "Nota", "PreferenciasUsuario", "Processamento", "Propriedade", "Questao", "RevisaoValidacao",
    "Sessao", "Tentativa", "TokenUsoUnico", "Turma", "Usuario", "ValorPropriedade", "VersaoDados",
    "VinculoInstitucional",
]
