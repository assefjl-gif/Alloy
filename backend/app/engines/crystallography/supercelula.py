"""Supercélulas n×n×n (portado da v1.4 — RQ-CIE-08; fecha a pendência D-10 do frontend).

Cúbicas: bloco de células convencionais. HC: bloco de células PRIMITIVAS (a₁, a₂ a 120°, c),
com a mesma base de ``ESTRUTURAS["HC"]["base"]`` usada pelo CIF. Átomos das faces da caixa
são incluídos (imagens periódicas), como no desenho da célula unitária.
"""

from __future__ import annotations

import itertools
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .constantes import EPS, SUPERCELULA_MAXIMA, Vetor
from .erros import EntradaInvalida
from .estruturas import ESTRUTURAS, c_a_ideal
from .geometria import frac_para_cart


def pontos_na_caixa(base: Sequence[Sequence[float]], n: int) -> List[Vetor]:
    """Posições fracionárias i + b (b na base) dentro de [0, n]³, bordas incluídas."""
    pontos: List[Vetor] = []
    for i, j, k in itertools.product(range(-1, n + 1), repeat=3):
        for b in base:
            f = (i + float(b[0]), j + float(b[1]), k + float(b[2]))
            if all(-EPS <= v <= n + EPS for v in f):
                pontos.append(f)
    return pontos


def validar_tamanho(n: Any) -> int:
    try:
        valor = int(n)
    except (TypeError, ValueError):
        raise EntradaInvalida("A supercélula deve ser um inteiro de 1 a "
                              f"{SUPERCELULA_MAXIMA}.") from None
    if isinstance(n, bool) or not 1 <= valor <= SUPERCELULA_MAXIMA:
        raise EntradaInvalida(f"A supercélula vai de 1 a {SUPERCELULA_MAXIMA} células por aresta.")
    return valor


def geometria_supercelula(estrutura: str, c_a: Optional[float], n: int
                          ) -> Tuple[List[Dict[str, Any]], List[List[Vetor]]]:
    """Átomos (posição cartesiana em unidades de a, fracionária e tipo) e as 12 arestas da caixa."""
    n = validar_tamanho(n)
    if estrutura == "HC" and c_a is None:
        c_a = c_a_ideal()
    base = [frac for frac, _tipo in ESTRUTURAS[estrutura]["base"]]
    atomos = [
        {"pos": list(frac_para_cart(estrutura, f, c_a)), "frac": list(f), "tipo": "rede"}
        for f in pontos_na_caixa(base, n)
    ]
    cantos = [(float(x), float(y), float(z)) for x in (0, n) for y in (0, n) for z in (0, n)]
    arestas = [
        [frac_para_cart(estrutura, a, c_a), frac_para_cart(estrutura, b, c_a)]
        for i, a in enumerate(cantos)
        for b in cantos[i + 1:]
        if abs(sum(abs(p - q) for p, q in zip(a, b, strict=True)) - n) < EPS
    ]
    return atomos, arestas


def cantos_da_caixa(estrutura: str, c_a: Optional[float], n: int) -> List[Vetor]:
    return [frac_para_cart(estrutura, (x, y, z), c_a) for x in (0, n) for y in (0, n) for z in (0, n)]
