"""Álgebra vetorial, conversões de coordenadas e geometria da célula desenhada.

Convenções (inalteradas desde a v1.0):
* cúbicas: coordenadas em unidades de ``a``, origem num vértice;
* HC: coordenadas cartesianas em unidades de ``a``, a₁ = (1, 0, 0),
  a₂ = (−½, √3/2, 0), c = (0, 0, c/a); o prisma hexagonal desenhado contém
  3 células primitivas.

Mudança da v1.1 (CR-07 / CR-08): a geometria é calculada sem arredondamento e
devolve separadamente a BASE cristalográfica (sítios únicos) e os átomos de
DESENHO (com réplicas de fronteira).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .constantes import CASAS_SAIDA, SQRT3, TOLERANCIA_EDICAO, Vetor
from .estruturas import ESTRUTURAS


def sub(a: Sequence[float], b: Sequence[float]) -> Vetor:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Sequence[float], b: Sequence[float]) -> Vetor:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def norma(a: Sequence[float]) -> float:
    return math.sqrt(dot(a, a))


def arredondar(p: Sequence[float], casas: int = CASAS_SAIDA) -> List[float]:
    """Arredonda SOMENTE para saída (o ``+ 0.0`` remove o −0.0)."""
    return [round(float(v), casas) + 0.0 for v in p]


def cart_para_frac(estrutura: str, p: Sequence[float], c_a: Optional[float]) -> Vetor:
    if estrutura == "HC":
        return p[0] + p[1] / SQRT3, 2.0 * p[1] / SQRT3, p[2] / float(c_a or 1.0)
    return float(p[0]), float(p[1]), float(p[2])


def frac_para_cart(estrutura: str, f: Sequence[float], c_a: Optional[float]) -> Vetor:
    if estrutura == "HC":
        return f[0] - f[1] / 2.0, SQRT3 / 2.0 * f[1], f[2] * float(c_a or 1.0)
    return float(f[0]), float(f[1]), float(f[2])


def gradiente_plano(estrutura: str, h: int, k: int, l: int, c_a: Optional[float]) -> Vetor:  # noqa: E741
    if estrutura == "HC":
        return float(h), (h + 2.0 * k) / SQRT3, l / float(c_a or 1.0)
    return float(h), float(k), float(l)


def volume_em_r(estrutura: str, c_a: Optional[float]) -> float:
    """Volume da célula desenhada em unidades de R³ (modelo de esferas rígidas)."""
    a_r = ESTRUTURAS[estrutura]["a_em_R"]
    if estrutura == "HC":
        return (3.0 * SQRT3 / 2.0) * a_r ** 3 * float(c_a or 1.0)
    return a_r ** 3


def c_a_ideal_hc() -> float:
    return float(ESTRUTURAS["HC"]["c_a_ideal"])


def distancia_entre_planos_hc(c_a: float) -> float:
    """Distância (em unidades de ``a``) de um átomo aos 6 vizinhos do plano vizinho: √(1/3 + (c/a)²/4)."""
    return math.sqrt(1.0 / 3.0 + float(c_a) ** 2 / 4.0)


def raio_contato_rel_hc(c_a: float) -> float:
    """R_c/a = ½·mín(1, c/a, d_entre_planos/a) — maior esfera rígida SEM sobreposição.

    Três distâncias candidatas entre vizinhos, em unidades de ``a``: a aresta basal (1), a translação
    de rede ``c`` (= c/a) e a distância aos 6 átomos do plano vizinho (√(1/3 + (c/a)²/4)).
    A translação ``c`` só é a menor quando c/a < 2/3 (ressalva R-1 do parecer de termodinâmica,
    2026-11-13 §7.a): sem ela o FEA voltava a crescer e ultrapassava π/(3√2) (≈1,2 em c/a = 0,2).
    Para c/a ≥ 2/3 o valor é idêntico ao anterior, e a entrada da API é limitada a c/a ≥ 1
    (``FAIXA_C_A``), de modo que nenhum resultado alcançável pela API muda.
    """
    razao = float(c_a)
    return 0.5 * min(1.0, razao, distancia_entre_planos_hc(razao))


def contato_tipo_hc(c_a: float) -> str:
    """Onde ocorre o primeiro contato: ``basal`` (c/a > ideal), ``entre_planos`` (c/a < ideal) ou ``ambos``."""
    ideal = c_a_ideal_hc()
    if abs(float(c_a) - ideal) <= TOLERANCIA_EDICAO * ideal:
        return "ambos"
    return "basal" if float(c_a) > ideal else "entre_planos"


def vizinhos_hc(c_a: float) -> List[Dict[str, Any]]:
    """Os dois grupos de primeiros vizinhos do HC (6 no plano basal a ``a``; 6 entre planos)."""
    return [
        {"grupo": "basal", "n": 6, "d_rel": 1.0},
        {"grupo": "entre_planos", "n": 6, "d_rel": distancia_entre_planos_hc(c_a)},
    ]


def fator_empacotamento(estrutura: str, c_a: Optional[float] = None) -> float:
    """FEA do modelo de esferas rígidas SEM sobreposição.

    Nas cúbicas (e no HC com c/a ≥ ideal) o raio de contato é a/2 e o valor é o clássico.
    No HC com c/a < √(8/3) os planos basais se aproximam: o raio de contato passa a ser metade da
    distância entre planos, senão as esferas de raio a/2 se interpenetram e o FEA ultrapassa o limite
    de empacotamento π/(3√2) ≈ 0,74048 (achado E-1, parecer R1-CRI-01, seção 1.4).
    FEA = (2π/(3√3))·(2R_c/a)³/(c/a); coincide com o valor anterior para c/a ≥ ideal.
    Com R_c = ½·mín(a, c, d_entre_planos) (ressalva R-1, parecer de termodinâmica §7.a) o invariante
    FEA ≤ π/(3√2) vale em TODO o domínio de c/a > 0, inclusive abaixo de 2/3.
    """
    if estrutura == "HC":
        razao = float(c_a if c_a is not None else c_a_ideal_hc())
        return (2.0 * math.pi / (3.0 * SQRT3)) * (2.0 * raio_contato_rel_hc(razao)) ** 3 / razao
    n = ESTRUTURAS[estrutura]["n"]
    return n * (4.0 / 3.0) * math.pi / volume_em_r(estrutura, c_a)


Atomo = Dict[str, Any]
Aresta = List[List[float]]


def geometria_celula(estrutura: str, c_a: Optional[float] = None) -> Tuple[List[Atomo], List[Aresta]]:
    """Átomos de DESENHO (com réplicas de fronteira) e arestas da célula, sem arredondar."""
    if estrutura == "HC":
        return _geometria_hc(float(c_a or ESTRUTURAS["HC"]["c_a_ideal"]))

    vertices = [(float(x), float(y), float(z)) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    arestas = [
        [list(a), list(b)]
        for i, a in enumerate(vertices)
        for b in vertices[i + 1:]
        if sum(abs(p - q) for p, q in zip(a, b, strict=True)) == 1
    ]
    atomos: List[Atomo] = [{"pos": list(v), "tipo": "vertice"} for v in vertices]
    if estrutura == "CCC":
        atomos.append({"pos": [0.5, 0.5, 0.5], "tipo": "centro"})
    if estrutura == "CFC":
        for face in [(0.5, 0.5, 0), (0.5, 0.5, 1), (0.5, 0, 0.5),
                     (0.5, 1, 0.5), (0, 0.5, 0.5), (1, 0.5, 0.5)]:
            atomos.append({"pos": [float(v) for v in face], "tipo": "face"})
    return atomos, arestas


def _geometria_hc(c_a: float) -> Tuple[List[Atomo], List[Aresta]]:
    hexagono = [(math.cos(math.radians(60 * i)), math.sin(math.radians(60 * i))) for i in range(6)]
    base = [[x, y, 0.0] for x, y in hexagono]
    topo = [[x, y, c_a] for x, y in hexagono]

    arestas: List[Aresta] = []
    for i in range(6):
        j = (i + 1) % 6
        arestas.append([base[i], base[j]])
        arestas.append([topo[i], topo[j]])
        arestas.append([base[i], topo[i]])

    atomos: List[Atomo] = [{"pos": list(p), "tipo": "vertice"} for p in base + topo]
    atomos.append({"pos": [0.0, 0.0, 0.0], "tipo": "basal"})
    atomos.append({"pos": [0.0, 0.0, c_a], "tipo": "basal"})
    raio_interno = 1.0 / SQRT3
    for angulo in (30, 150, 270):
        rad = math.radians(angulo)
        atomos.append({
            "pos": [raio_interno * math.cos(rad), raio_interno * math.sin(rad), c_a / 2.0],
            "tipo": "interior",
        })
    return atomos, arestas


def base_cristalografica(estrutura: str) -> List[Dict[str, Any]]:
    """Sítios únicos (frações em [0,1)) da célula convencional/primitiva — usados por exportadores."""
    return [{"frac": list(frac), "tipo": tipo} for frac, tipo in ESTRUTURAS[estrutura]["base"]]


def vetores_de_rede(estrutura: str, a: float, c: Optional[float] = None) -> List[Vetor]:
    """Vetores a, b, c da célula cristalográfica (mesma unidade de ``a``)."""
    if estrutura == "HC":
        cc = float(c if c is not None else a * ESTRUTURAS["HC"]["c_a_ideal"])
        return [(a, 0.0, 0.0), (-a / 2.0, a * SQRT3 / 2.0, 0.0), (0.0, 0.0, cc)]
    return [(a, 0.0, 0.0), (0.0, a, 0.0), (0.0, 0.0, a)]
