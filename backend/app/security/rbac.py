"""Autorização por papel com escopo (ADR-009): global, instituição, turma e dono.

``autorizar(ator, acao, contexto)`` é a ÚNICA porta de decisão; os serviços chamam e traduzem a
recusa em 404 quando o recurso é de outra instituição (não revela existência) ou 403 quando o
ator enxerga o recurso mas não pode agir sobre ele. A matriz é testada célula a célula.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Optional, Set

PAPEIS = ("admin_geral", "admin_institucional", "professor", "estudante", "pesquisador")

#: ação → papéis que podem executá-la NO ESCOPO do recurso (instituição ou turma do recurso).
MATRIZ: Dict[str, FrozenSet[str]] = {
    "turma.criar": frozenset({"admin_institucional", "professor"}),
    "turma.ver": frozenset({"admin_institucional", "professor", "estudante_matriculado", "monitor"}),
    "turma.editar": frozenset({"admin_institucional", "professor_responsavel"}),
    "turma.matricular": frozenset({"admin_institucional", "professor_responsavel"}),
    "atividade.publicar": frozenset({"admin_institucional", "professor_responsavel", "professor_assistente"}),
    "atividade.responder": frozenset({"estudante_matriculado"}),
    "progresso.ver_turma": frozenset({"admin_institucional", "professor_responsavel", "professor_assistente",
                                      "monitor"}),
    "questao.criar": frozenset({"admin_institucional", "professor", "pesquisador"}),
    "dado.revisar": frozenset({"pesquisador", "admin_institucional"}),
}


@dataclass(frozen=True)
class Ator:
    usuario_id: uuid.UUID
    admin_geral: bool = False
    #: instituição → papéis institucionais
    papeis_instituicao: Dict[uuid.UUID, FrozenSet[str]] = field(default_factory=dict)
    #: turma → papéis na turma (inclui "professor_responsavel" e "estudante_matriculado" derivados)
    papeis_turma: Dict[uuid.UUID, FrozenSet[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Contexto:
    instituicao_id: Optional[uuid.UUID] = None
    turma_id: Optional[uuid.UUID] = None
    dono_id: Optional[uuid.UUID] = None


def papeis_no_contexto(ator: Ator, contexto: Contexto) -> Set[str]:
    papeis: Set[str] = set()
    if contexto.instituicao_id is not None:
        papeis |= ator.papeis_instituicao.get(contexto.instituicao_id, frozenset())
    if contexto.turma_id is not None:
        papeis |= ator.papeis_turma.get(contexto.turma_id, frozenset())
    return papeis


def autorizar(ator: Optional[Ator], acao: str, contexto: Contexto = Contexto()) -> bool:
    if acao not in MATRIZ:
        raise KeyError(f"ação desconhecida na matriz RBAC: {acao}")
    if ator is None:
        return False
    if ator.admin_geral:
        return True
    if contexto.dono_id is not None and contexto.dono_id == ator.usuario_id and acao.endswith(".ver"):
        return True
    return bool(papeis_no_contexto(ator, contexto) & MATRIZ[acao])


def enxerga_instituicao(ator: Optional[Ator], instituicao_id: uuid.UUID) -> bool:
    """Sem vínculo com a instituição do recurso → o serviço responde 404 (ADR-009)."""
    if ator is None:
        return False
    return ator.admin_geral or instituicao_id in ator.papeis_instituicao
