"""Densidade e fração planar (portado da v1.4 — RQ-CIE-05, achado CIE-04).

Regra de contagem dentro do polígono de corte da célula: átomo no vértice conta
ângulo/360°, na aresta 1/2, no interior 1. Ela só é exata quando o polígono é uma
unidade de repetição do plano. Por isso o resultado só é PUBLICADO para as famílias
conferidas com a literatura (Callister & Rethwisch, seção 3.11); para as demais o
motor devolve ``validado: False`` com o motivo, sem número (PI-02).
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Sequence

from .constantes import Vetor
from .estruturas import ESTRUTURAS
from .geometria import dot, norma, sub

TOLERANCIA = 1e-6

#: Famílias com densidade planar conferida (índices reduzidos, em módulo e ordenados).
FAMILIAS_VALIDADAS = {
    "CS": {(0, 0, 1), (0, 1, 1), (1, 1, 1)},
    "CCC": {(0, 0, 1), (0, 1, 1), (1, 1, 1)},
    "CFC": {(0, 0, 1), (0, 1, 1), (1, 1, 1)},
}


def atomos_no_poligono(pontos: Sequence[Vetor], posicoes: Sequence[Sequence[float]]) -> float:
    soma = 0.0
    for p in posicoes:
        vertice = next((i for i, q in enumerate(pontos) if norma(sub(p, q)) < TOLERANCIA), None)
        if vertice is not None:
            q = pontos[vertice]
            u = sub(pontos[vertice - 1], q)
            v = sub(pontos[(vertice + 1) % len(pontos)], q)
            cosseno = max(-1.0, min(1.0, dot(u, v) / (norma(u) * norma(v))))
            soma += math.acos(cosseno) / (2.0 * math.pi)
            continue
        na_aresta = False
        for i, a in enumerate(pontos):
            ab = sub(pontos[(i + 1) % len(pontos)], a)
            t = dot(sub(p, a), ab) / dot(ab, ab)
            projecao = (a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2])
            if 0.0 < t < 1.0 and norma(sub(p, projecao)) < TOLERANCIA:
                na_aresta = True
                break
        soma += 0.5 if na_aresta else 1.0
    return soma


def familia_validada(estrutura: str, hkl: Sequence[int], ordem: int) -> bool:
    if ordem != 1:
        return False
    h, k, l = hkl  # noqa: E741
    if estrutura == "HC":
        return h == 0 and k == 0 and abs(l) == 1  # plano basal (0001)
    return tuple(sorted(abs(v) for v in (h, k, l))) in FAMILIAS_VALIDADAS.get(estrutura, set())


def calcular_planar(estrutura: str, hkl: Sequence[int], ordem: int, pontos: Sequence[Vetor],
                    posicoes: Sequence[Sequence[float]], area_rel: float,
                    a_nm: Optional[float]) -> Dict[str, Any]:
    """Bloco ``planar`` da resposta de Miller."""
    if not familia_validada(estrutura, hkl, ordem):
        motivo = ("Índices com fator comum: a densidade planar vale para o plano reduzido."
                  if ordem != 1 else
                  "Densidade planar publicada só para planos conferidos com a literatura "
                  "({100}, {110}, {111} cúbicos e (0001) da HC).")
        return {"validado": False, "motivo": motivo, "atomos_no_plano": None,
                "densidade_rel": None, "densidade_nm2": None, "fracao_planar": None,
                "fonte": None}
    atomos = atomos_no_poligono(pontos, posicoes)
    densidade_rel = atomos / area_rel                     # átomos por a²
    raio_rel = 1.0 / float(ESTRUTURAS[estrutura]["a_em_R"])  # R/a no modelo de esferas rígidas
    return {
        "validado": True,
        "motivo": None,
        "atomos_no_plano": atomos,
        "densidade_rel": densidade_rel,
        "densidade_nm2": densidade_rel / a_nm ** 2 if a_nm else None,
        "fracao_planar": atomos * math.pi * raio_rel ** 2 / area_rel,
        "fonte": "Callister & Rethwisch, Ciência e Engenharia de Materiais, seção 3.11 (densidade planar)",
    }
