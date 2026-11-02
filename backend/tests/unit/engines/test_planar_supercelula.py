"""Densidade/fração planar, supercélulas e famílias de planos (recursos da v1.4, RQ-CIE-05/08).

Valores de referência:
* Frações planares: expressões fechadas das densidades planares de Callister & Rethwisch,
  "Ciência e Engenharia de Materiais", seção 3.11 (PD·πR²), p. ex. CFC(111) = π/(2√3).
* Contagens de átomos em supercélula e em planos da família: calculadas aqui por
  força bruta independente (enumeração de pontos de rede), não pelo motor.
"""

from __future__ import annotations

import itertools
import math

import pytest

from app.engines.crystallography import calcular_miller
from app.engines.crystallography.supercelula import geometria_supercelula

RAIZ3 = math.sqrt(3.0)
RAIZ2 = math.sqrt(2.0)

# (estrutura, índices) -> (átomos equivalentes no polígono, fração planar fechada)
REFERENCIA_PLANAR = {
    ("CS", (1, 0, 0)): (1.0, math.pi / 4),
    ("CCC", (1, 0, 0)): (1.0, 3 * math.pi / 16),
    ("CCC", (1, 1, 0)): (2.0, 3 * math.pi / (8 * RAIZ2)),
    ("CFC", (1, 0, 0)): (2.0, math.pi / 4),
    ("CFC", (1, 1, 0)): (2.0, math.pi / (4 * RAIZ2)),
    ("CFC", (1, 1, 1)): (2.0, math.pi / (2 * RAIZ3)),
    ("HC", (0, 0, 0, 1)): (3.0, math.pi / (2 * RAIZ3)),
}


@pytest.mark.parametrize(("estrutura", "indices"), list(REFERENCIA_PLANAR))
def test_fracao_planar_bate_com_expressao_fechada(estrutura, indices):
    atomos_esperados, fracao_esperada = REFERENCIA_PLANAR[(estrutura, indices)]
    r = calcular_miller({"estrutura": estrutura, "tipo": "plano", "indices": list(indices)})
    assert r["planar"]["validado"] is True
    assert r["planar"]["atomos_no_plano"] == pytest.approx(atomos_esperados, abs=1e-9)
    assert r["planar"]["fracao_planar"] == pytest.approx(fracao_esperada, rel=1e-9)


def test_densidade_planar_em_nm2_usa_a():
    # Cu: a = 0,3615 nm; CFC(111): 2 átomos em (√3/2)·a²
    a = 0.3615
    r = calcular_miller({"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1], "a_nm": a})
    assert r["planar"]["densidade_nm2"] == pytest.approx(2.0 / ((RAIZ3 / 2) * a * a), rel=1e-9)


def test_familia_com_sinal_trocado_tambem_e_validada():
    r = calcular_miller({"estrutura": "CFC", "tipo": "plano", "indices": [-1, 1, 1]})
    assert r["planar"]["validado"] is True
    assert r["planar"]["fracao_planar"] == pytest.approx(math.pi / (2 * RAIZ3), rel=1e-9)


@pytest.mark.parametrize(("estrutura", "indices"), [("HC", [1, 0, -1, 1]), ("CFC", [1, 2, 0]), ("CFC", [2, 0, 0])])
def test_planos_sem_validacao_nao_publicam_numero(estrutura, indices):
    """CIE-04: densidade planar fora dos planos validados fica oculta, com motivo."""
    r = calcular_miller({"estrutura": estrutura, "tipo": "plano", "indices": indices})
    assert r["planar"]["validado"] is False
    assert r["planar"]["fracao_planar"] is None
    assert r["planar"]["densidade_nm2"] is None
    assert r["planar"]["motivo"]


# ----------------------------------------------------------------- supercélula (força bruta)
def _contar_pontos(base, n):
    total = 0
    for i, j, k in itertools.product(range(-1, n + 1), repeat=3):
        for b in base:
            f = (i + b[0], j + b[1], k + b[2])
            if all(-1e-9 <= v <= n + 1e-9 for v in f):
                total += 1
    return total


BASES = {
    "CS": [(0, 0, 0)],
    "CCC": [(0, 0, 0), (0.5, 0.5, 0.5)],
    "CFC": [(0, 0, 0), (0.5, 0.5, 0), (0.5, 0, 0.5), (0, 0.5, 0.5)],
    "HC": [(0, 0, 0), (2 / 3, 1 / 3, 0.5)],
}


@pytest.mark.parametrize("estrutura", list(BASES))
@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_supercelula_conta_os_pontos_de_rede(estrutura, n):
    atomos, arestas = geometria_supercelula(estrutura, None, n)
    assert len(atomos) == _contar_pontos(BASES[estrutura], n)
    assert len(arestas) == 12


def test_supercelula_cfc_3_tem_172_atomos():
    # (n+1)³ vértices + 3·n²·(n+1) centros de face = 64 + 108
    assert len(geometria_supercelula("CFC", None, 3)[0]) == 172


def test_supercelula_rejeita_tamanho_fora_da_faixa():
    from app.engines.crystallography import EntradaInvalida
    with pytest.raises(EntradaInvalida):
        geometria_supercelula("CFC", None, 5)


def test_familia_de_planos_na_supercelula():
    n = 3
    r = calcular_miller({"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1], "supercelula": n})
    # h+k+l = m corta a caixa [0,3]³ com polígono para m = 1..8 (m = 0 e 9 tocam só um vértice)
    assert len(r["familia"]) == 8
    # o plano destacado é o do meio; conferir a contagem por força bruta
    m = round(sum(r["familia"][len(r["familia"]) // 2]["centro"]))
    esperado = 0
    for i, j, k in itertools.product(range(-1, n + 1), repeat=3):
        for b in BASES["CFC"]:
            f = (i + b[0], j + b[1], k + b[2])
            if all(-1e-9 <= v <= n + 1e-9 for v in f) and abs(sum(f) - m) < 1e-9:
                esperado += 1
    assert len(r["atomos"]) == esperado


def test_sem_supercelula_nao_ha_familia():
    r = calcular_miller({"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1]})
    assert r["familia"] is None
