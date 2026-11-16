"""Erros de entrada do motor HEA com subtipo estável (contrato R1, seção 4.1).

Cada erro carrega ``detalhes``: lista de ``{"loc": [...], "type": "<subtipo>", "msg": "<pt-BR>"}``, no mesmo
formato que a API já usa no 422 de esquema. O tratador da API repassa a lista em ``details``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from ..crystallography.erros import EntradaInvalida
from ..procedencia import DadoNaoValidado

#: Chave ou valor do usuário ecoado em mensagem é truncado (contrato R1, seção 4).
MAX_ECO = 16


def eco(texto: Any) -> str:
    """Texto do usuário seguro para mensagem: no máximo ``MAX_ECO`` caracteres."""
    bruto = str(texto)
    return bruto if len(bruto) <= MAX_ECO else bruto[:MAX_ECO] + "…"


def detalhe(chave: Any, subtipo: str, mensagem: str) -> Dict[str, Any]:
    loc: List[str] = ["composicao"] if chave is None else ["composicao", str(chave)]
    return {"loc": loc, "type": subtipo, "msg": mensagem}


class EntradaHeaInvalida(EntradaInvalida):
    """400 ``ENTRADA_INVALIDA`` com ``detalhes``; a mensagem do erro é a do primeiro item."""

    def __init__(self, detalhes: Sequence[Dict[str, Any]]) -> None:
        super().__init__(str(detalhes[0]["msg"]))
        self.detalhes: List[Dict[str, Any]] = list(detalhes)


class MassaNaoValidada(DadoNaoValidado):
    """422 ``DADO_NAO_VALIDADO``: base mássica pedida e a massa existe, mas não pode ser usada neste ambiente."""

    def __init__(self, detalhes: Sequence[Dict[str, Any]]) -> None:
        super().__init__(str(detalhes[0]["msg"]))
        self.detalhes: List[Dict[str, Any]] = list(detalhes)
