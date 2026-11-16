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
    return atomos, arestas_da_caixa(estrutura, c_a, n)


def arestas_da_caixa(estrutura: str, c_a: Optional[float], n: int) -> List[List[Vetor]]:
    """As 12 arestas da caixa n×n×n (mesma geometria usada pelo desenho da supercélula)."""
    cantos = [(float(x), float(y), float(z)) for x in (0, n) for y in (0, n) for z in (0, n)]
    return [
        [frac_para_cart(estrutura, a, c_a), frac_para_cart(estrutura, b, c_a)]
        for i, a in enumerate(cantos)
        for b in cantos[i + 1:]
        if abs(sum(abs(p - q) for p, q in zip(a, b, strict=True)) - n) < EPS
    ]


def cantos_da_caixa(estrutura: str, c_a: Optional[float], n: int) -> List[Vetor]:
    return [frac_para_cart(estrutura, (x, y, z), c_a) for x in (0, n) for y in (0, n) for z in (0, n)]


# --------------------------------------------------------------------------- supercélula PERIÓDICA (R1)
# Achados L-1 e L-5 (parecer R1-CRI-01, §2.2, §2.3 e §3.1): a lista de ``pontos_na_caixa`` inclui as
# bordas de propósito, para o DESENHO. Usá-la como lista de átomos quebra a periodicidade: o mesmo
# átomo aparece várias vezes, pode receber elementos diferentes em cada cópia e as contagens deixam de
# ser a composição de uma célula periódica. As funções abaixo separam os dois conceitos:
#   * átomo ÚNICO  = classe de posições iguais módulo n (um átomo da supercélula periódica);
#   * imagem       = cópia de fronteira, só para o desenho, nunca contada.

def sitios_unicos(base: Sequence[Sequence[float]], n: int) -> List[Dict[str, Any]]:
    """Sítios únicos f = (i + b) com i ∈ {0..n−1}, na ORDEM CANÔNICA (i, j, k, índice da base).

    Índice canônico: s = ((i·n + j)·n + k)·Z + b. Total = Z·n³.
    """
    sitios: List[Dict[str, Any]] = []
    z = len(base)
    for i, j, k in itertools.product(range(n), repeat=3):
        for b, ponto in enumerate(base):
            indice = ((i * n + j) * n + k) * z + b
            sitios.append({
                "indice": indice,
                "celula": (i, j, k),
                "base": b,
                "frac_celula": (float(ponto[0]), float(ponto[1]), float(ponto[2])),
                "frac": (i + float(ponto[0]), j + float(ponto[1]), k + float(ponto[2])),
            })
    sitios.sort(key=lambda s: s["indice"])
    return sitios


def translacoes_de_imagem(frac: Sequence[float], n: int) -> List[Tuple[int, int, int]]:
    """Translações (tx, ty, tz) ∈ {0, n}³ que levam o sítio a uma IMAGEM de fronteira dentro da caixa.

    Um sítio com coordenada fracionária nula em S eixos gera 2^|S| − 1 imagens (uma por subconjunto
    não vazio de S). Conferência (parecer §3.1): CCC n = 2 → 16 únicos + 19 imagens = 35 esferas,
    exatamente o desenho anterior.
    """
    eixos = [m for m in range(3) if abs(float(frac[m])) < EPS]
    translacoes: List[Tuple[int, int, int]] = []
    for tamanho in range(1, len(eixos) + 1):
        for combinacao in itertools.combinations(eixos, tamanho):
            deslocamento = [0, 0, 0]
            for m in combinacao:
                deslocamento[m] = n
            translacoes.append((deslocamento[0], deslocamento[1], deslocamento[2]))
    return translacoes
