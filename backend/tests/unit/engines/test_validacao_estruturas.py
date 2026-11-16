"""Casos de referência das quatro estruturas (R1-CRI-01, parecer de cristalografia de 12/11/2026).

Cada teste compara o motor com uma conferência INDEPENDENTE feita aqui: redução periódica das posições,
contagem de vizinhos, volume por determinante e empacotamento de esferas em contato. As referências são
derivações analíticas do modelo de esferas rígidas (as mesmas dos livros-texto):

* CS:  a = 2R,      NC 6,  FEA = π/6
* CCC: a = 4R/√3,   NC 8,  FEA = π√3/8
* CFC: a = 2R√2,    NC 12, FEA = π/(3√2)
* HC ideal: a = 2R, c/a = √(8/3), NC 12, FEA = π/(3√2); prisma desenhado = 3 células primitivas (n = 6, z = 2)

Este arquivo só contém o que foi validado como correto. O FEA do HC com c/a ABAIXO do ideal (achado E-1) e a
representação de ligas (achados L-*) estão documentados em docs/agent_reports/2026-11-12_parecer_cristalografia.md
e ganham testes de regressão junto com a correção.
"""

from __future__ import annotations

import itertools
import math
from typing import Dict, List, Optional, Sequence, Tuple

import pytest

from app.engines.crystallography.estruturas import ESTRUTURAS, c_a_ideal
from app.engines.crystallography.geometria import (
    cart_para_frac,
    fator_empacotamento,
    frac_para_cart,
    vetores_de_rede,
    volume_em_r,
)
from app.engines.crystallography.supercelula import geometria_supercelula

from ._motor import calcular_estrutura

CUBICAS = ("CS", "CCC", "CFC")
TODAS = ("CS", "CCC", "CFC", "HC")

#: Átomos na célula replicada pela supercélula (cúbicas: convencional; HC: primitiva).
Z_CELULA = {"CS": 1, "CCC": 2, "CFC": 4, "HC": 2}
NC_REF = {"CS": 6, "CCC": 8, "CFC": 12, "HC": 12}
#: Distância ao primeiro vizinho, em unidades de a.
D1_REF = {"CS": 1.0, "CCC": math.sqrt(3) / 2, "CFC": 1 / math.sqrt(2), "HC": 1.0}
A_EM_R_REF = {"CS": 2.0, "CCC": 4 / math.sqrt(3), "CFC": 2 * math.sqrt(2), "HC": 2.0}
FEA_REF = {"CS": math.pi / 6, "CCC": math.pi * math.sqrt(3) / 8,
           "CFC": math.pi / (3 * math.sqrt(2)), "HC": math.pi / (3 * math.sqrt(2))}
#: Maior empacotamento possível de esferas rígidas iguais (CFC e HC ideal).
FEA_MAXIMO = math.pi / (3 * math.sqrt(2))

Ponto = Tuple[float, float, float]


def _c_a(estrutura: str) -> Optional[float]:
    return c_a_ideal() if estrutura == "HC" else None


def _det(v: Sequence[Sequence[float]]) -> float:
    a, b, c = v
    return (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0]))


def _chave(frac: Sequence[float], n: int) -> Ponto:
    """Coordenada fracionária reduzida a [0, n): identifica o átomo único de uma imagem periódica."""
    reduzida = []
    for v in frac:
        w = round(v % n, 6)
        reduzida.append(0.0 if abs(w - n) < 1e-6 else w)
    return reduzida[0], reduzida[1], reduzida[2]


def _unicos(estrutura: str, c_a: Optional[float], n: int) -> Dict[Ponto, List[Sequence[float]]]:
    atomos, _ = geometria_supercelula(estrutura, c_a, n)
    classes: Dict[Ponto, List[Sequence[float]]] = {}
    for atomo in atomos:
        classes.setdefault(_chave(atomo["frac"], n), []).append(atomo["frac"])
    return classes


def _camadas(estrutura: str, c_a: Optional[float], n: int = 3, tol: float = 1e-6) -> List[List[Tuple[float, int]]]:
    """Para cada átomo único: [(distância, quantidade), ...] das 3 primeiras camadas, com condição periódica."""
    # A chave arredondada só identifica o átomo; a geometria usa a cópia de origem, sem arredondar.
    classes = _unicos(estrutura, c_a, n)
    unicos = [min(copias, key=lambda f: (sum(f), tuple(f))) for _chave_unica, copias in sorted(classes.items())]
    vetores = [tuple(n * x for x in v) for v in vetores_de_rede(estrutura, 1.0, c_a)]
    cart = [frac_para_cart(estrutura, f, c_a) for f in unicos]
    saida = []
    for i, p in enumerate(cart):
        distancias = []
        for j, q in enumerate(cart):
            for t in itertools.product((-1, 0, 1), repeat=3):
                if i == j and t == (0, 0, 0):
                    continue
                imagem = [q[k] + sum(t[m] * vetores[m][k] for m in range(3)) for k in range(3)]
                distancias.append(math.dist(p, imagem))
        camadas: List[List[float]] = []
        for d in sorted(distancias):
            if camadas and abs(d - camadas[-1][0]) < tol:
                camadas[-1][1] += 1
            else:
                camadas.append([d, 1])
        saida.append([(d, int(q)) for d, q in camadas[:3]])
    return saida


# --------------------------------------------------------------------------- periodicidade e n
@pytest.mark.parametrize("estrutura", TODAS)
@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_supercelula_tem_z_n3_atomos_unicos(estrutura, n):
    classes = _unicos(estrutura, _c_a(estrutura), n)
    assert len(classes) == Z_CELULA[estrutura] * n ** 3


@pytest.mark.parametrize("estrutura", TODAS)
def test_supercelula_nao_desenha_atomo_duplicado(estrutura):
    c_a = _c_a(estrutura)
    atomos, arestas = geometria_supercelula(estrutura, c_a, 2)
    posicoes = [a["pos"] for a in atomos]
    menor = min(math.dist(p, q) for i, p in enumerate(posicoes) for q in posicoes[i + 1:])
    assert menor == pytest.approx(D1_REF[estrutura], rel=1e-9)   # nenhum par mais perto que o 1º vizinho
    assert len(arestas) == 12


@pytest.mark.parametrize("estrutura", TODAS)
def test_esferas_extras_sao_imagens_de_fronteira_de_um_atomo_de_origem(estrutura):
    n = 2
    atomos, _ = geometria_supercelula(estrutura, _c_a(estrutura), n)
    origem = {_chave(a["frac"], n) for a in atomos if all(v < n - 1e-9 for v in a["frac"])}
    imagens = [a for a in atomos if any(abs(v - n) < 1e-9 for v in a["frac"])]
    assert len(origem) == Z_CELULA[estrutura] * n ** 3
    assert len(origem) + len(imagens) == len(atomos)
    assert all(_chave(a["frac"], n) in origem for a in imagens)


@pytest.mark.parametrize(("estrutura", "desenhados", "n_celula"),
                         [("CS", 8, 1), ("CCC", 9, 2), ("CFC", 14, 4), ("HC", 17, 6)])
def test_celula_desenhada_soma_das_fracoes_igual_a_n(estrutura, desenhados, n_celula):
    r = calcular_estrutura({"nome": estrutura})
    assert len(r["atomos"]) == desenhados
    assert sum(a["fracao"] for a in r["atomos"]) == pytest.approx(n_celula, abs=1e-9)
    assert r["n"] == n_celula
    assert r["z"] == Z_CELULA[estrutura]


@pytest.mark.parametrize("estrutura", TODAS)
def test_atomos_da_celula_desenhada_pertencem_a_rede(estrutura):
    r = calcular_estrutura({"nome": estrutura})
    base = [b for b, _tipo in ESTRUTURAS[estrutura]["base"]]
    for atomo in r["atomos"]:
        f = cart_para_frac(estrutura, atomo["pos"], r["c_a"])
        assert any(all(abs((f[k] - b[k]) - round(f[k] - b[k])) < 1e-5 for k in range(3)) for b in base)


# --------------------------------------------------------------------------- coordenação e a(R)
@pytest.mark.parametrize("estrutura", TODAS)
def test_numero_de_coordenacao_por_contagem_de_vizinhos(estrutura):
    for camadas in _camadas(estrutura, _c_a(estrutura)):
        distancia, quantidade = camadas[0]
        assert quantidade == NC_REF[estrutura] == ESTRUTURAS[estrutura]["nc"]
        assert distancia == pytest.approx(D1_REF[estrutura], rel=1e-9)


@pytest.mark.parametrize(("estrutura", "segunda"),
                         [("CS", (math.sqrt(2), 12)), ("CCC", (1.0, 6)), ("CFC", (1.0, 6)), ("HC", (math.sqrt(2), 6))])
def test_segunda_camada_de_vizinhos(estrutura, segunda):
    distancia, quantidade = _camadas(estrutura, _c_a(estrutura))[0][1]
    assert quantidade == segunda[1]
    assert distancia == pytest.approx(segunda[0], rel=1e-9)


@pytest.mark.parametrize("estrutura", TODAS)
def test_parametro_de_rede_em_funcao_do_raio(estrutura):
    # Esferas rígidas em contato: 2R = d1, logo a/R = 2/(d1/a).
    assert ESTRUTURAS[estrutura]["a_em_R"] == pytest.approx(A_EM_R_REF[estrutura], rel=1e-12)
    assert ESTRUTURAS[estrutura]["a_em_R"] == pytest.approx(2.0 / D1_REF[estrutura], rel=1e-12)


# --------------------------------------------------------------------------- empacotamento
@pytest.mark.parametrize("estrutura", TODAS)
def test_fea_ideal_analitico_e_por_esferas_em_contato(estrutura):
    c_a = _c_a(estrutura)
    assert fator_empacotamento(estrutura, c_a) == pytest.approx(FEA_REF[estrutura], rel=1e-12)
    # Conferência independente: Z esferas de raio d1/2 no volume da célula replicada (determinante).
    volume = abs(_det(vetores_de_rede(estrutura, 1.0, c_a)))
    contato = Z_CELULA[estrutura] * (4.0 / 3.0) * math.pi * (D1_REF[estrutura] / 2.0) ** 3 / volume
    assert contato == pytest.approx(FEA_REF[estrutura], rel=1e-12)
    assert fator_empacotamento(estrutura, c_a) <= FEA_MAXIMO * (1 + 1e-12)


def test_volume_do_motor_corresponde_a_celula_desenhada():
    for estrutura in CUBICAS:
        assert volume_em_r(estrutura, None) == pytest.approx(A_EM_R_REF[estrutura] ** 3, rel=1e-12)
    # HC: o prisma hexagonal desenhado (n = 6) tem exatamente 3 células primitivas (z = 2).
    c_a = c_a_ideal()
    primitiva = abs(_det(vetores_de_rede("HC", 1.0, c_a)))
    prisma = volume_em_r("HC", c_a) / ESTRUTURAS["HC"]["a_em_R"] ** 3
    assert primitiva == pytest.approx(math.sqrt(3) / 2 * c_a, rel=1e-12)
    assert prisma / primitiva == pytest.approx(3.0, rel=1e-12)
    assert ESTRUTURAS["HC"]["n"] == 3 * ESTRUTURAS["HC"]["z"]


@pytest.mark.parametrize("c_a", [1.70, 1.856, 2.0])
def test_fea_hc_com_c_a_acima_do_ideal_e_o_de_esferas_rigidas(c_a):
    # Acima do ideal o contato é no plano basal (R = a/2) e não há sobreposição: o valor do motor é o rígido.
    d_fora = math.sqrt(1.0 / 3.0 + c_a * c_a / 4.0)
    assert d_fora > 1.0
    rigido = 2 * (4.0 / 3.0) * math.pi * 0.5 ** 3 / (math.sqrt(3) / 2 * c_a)
    assert fator_empacotamento("HC", c_a) == pytest.approx(rigido, rel=1e-12)
    assert fator_empacotamento("HC", c_a) < FEA_MAXIMO


# --------------------------------------------------------------------------- HC: c/a, base e referencial
def test_c_a_ideal_e_raiz_de_8_sobre_3_e_iguala_as_doze_distancias():
    c_a = c_a_ideal()
    assert c_a == pytest.approx(math.sqrt(8.0 / 3.0), rel=1e-15)
    # Vizinho fora do plano: a/√3 na horizontal e c/2 na vertical; no ideal a distância é exatamente a.
    assert math.sqrt(1.0 / 3.0 + c_a * c_a / 4.0) == pytest.approx(1.0, rel=1e-12)
    a, b = (0.0, 0.0, 0.0), (2.0 / 3.0, 1.0 / 3.0, 0.5)
    assert math.dist(frac_para_cart("HC", a, c_a), frac_para_cart("HC", b, c_a)) == pytest.approx(1.0, rel=1e-12)


def test_referencial_hexagonal_a1_a2_a_120_graus_e_ida_e_volta():
    a1, a2, c = vetores_de_rede("HC", 1.0, 1.6)
    cosseno = (a1[0] * a2[0] + a1[1] * a2[1]) / (math.hypot(*a1[:2]) * math.hypot(*a2[:2]))
    assert math.degrees(math.acos(cosseno)) == pytest.approx(120.0, abs=1e-9)
    assert c == pytest.approx((0.0, 0.0, 1.6))
    ponto = (0.37, -0.21, 0.83)
    assert cart_para_frac("HC", frac_para_cart("HC", ponto, 1.6), 1.6) == pytest.approx(ponto, abs=1e-12)


def test_base_hc_do_motor_e_a_posicao_2c_com_a_origem_deslocada():
    # Wyckoff 2c de P6₃/mmc: (1/3, 2/3, 1/4) e (2/3, 1/3, 3/4). Somando (1/3, 2/3, 1/4) chega-se à base do motor.
    wyckoff_2c = [(1 / 3, 2 / 3, 1 / 4), (2 / 3, 1 / 3, 3 / 4)]
    deslocamento = (1 / 3, 2 / 3, 1 / 4)
    base = [frac for frac, _tipo in ESTRUTURAS["HC"]["base"]]
    assert len(base) == len(wyckoff_2c) == ESTRUTURAS["HC"]["z"]

    def mesmo_ponto(p, q):   # igualdade módulo translação de rede
        return all(abs((p[k] - q[k]) - round(p[k] - q[k])) < 1e-9 for k in range(3))

    for sitio in wyckoff_2c:
        deslocado = tuple(sitio[k] + deslocamento[k] for k in range(3))
        assert sum(1 for b in base if mesmo_ponto(deslocado, b)) == 1
    assert ESTRUTURAS["HC"]["grupo_espacial"]["numero"] == 194
    assert ESTRUTURAS["HC"]["grupo_espacial"]["sitio"] == pytest.approx(wyckoff_2c[0])


@pytest.mark.parametrize(("simbolo", "abaixo_do_ideal"), [("Mg", True), ("Ti", True), ("Co", True), ("Zn", False)])
def test_hc_real_tem_seis_mais_seis_vizinhos(simbolo, abaixo_do_ideal):
    # Fora do c/a ideal os 12 vizinhos se separam em 6 no plano basal (d = a) e 6 entre planos.
    c_a = calcular_estrutura({"nome": simbolo})["c_a"]
    assert (c_a < c_a_ideal()) is abaixo_do_ideal
    d_fora = math.sqrt(1.0 / 3.0 + c_a * c_a / 4.0)
    (d1, q1), (d2, q2) = _camadas("HC", c_a)[0][:2]
    assert (q1, q2) == (6, 6)
    assert (d1, d2) == pytest.approx(tuple(sorted((1.0, d_fora))), rel=1e-9)


# --------------------------------------------------------------------------- densidade teórica
@pytest.mark.parametrize("simbolo", ["Po", "Fe", "Cu", "Mg", "Ti"])
def test_densidade_teorica_confere_com_calculo_independente(simbolo):
    r = calcular_estrutura({"nome": simbolo})
    a_cm = r["a_nm"] * 1e-7
    if r["estrutura"] == "HC":
        volume = (3 * math.sqrt(3) / 2) * a_cm ** 2 * (r["c_nm"] * 1e-7)   # prisma, n = 6
    else:
        volume = a_cm ** 3
    esperado = r["n"] * r["peso"] / (volume * 6.02214076e23)
    assert r["densidade"] == pytest.approx(esperado, rel=1e-12)
