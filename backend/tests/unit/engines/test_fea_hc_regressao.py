"""Regressão do achado E-1 (R1-CRI-01 §1.4) e dos campos de contexto do FEA — contrato R1 §3 (T-C1, T-C2, R16).

Antes da correção o motor fixava R = a/2 no HC para qualquer c/a e devolvia FEA acima do limite de
empacotamento de esferas rígidas iguais, π/(3√2) ≈ 0,740480 (fisicamente impossível: as esferas se
interpenetravam). Valores do motor ANTES → DEPOIS (V-15):

| metal | c/a | FEA antes | FEA depois |
|---|---|---|---|
| Mg | 1,6240 | 0,744581 | 0,736418 |
| Ti | 1,587259 (de a e c medidos) | 0,761816 | 0,720132 |
| Co | 1,6230 | 0,745040 | 0,735968 |
| Zn | 1,8560 | 0,651508 | 0,651508 (inalterado: c/a > ideal) |

Derivação (parecer §1.4): para esferas rígidas o raio é metade da MENOR distância entre vizinhos,
R_c = ½·mín(a, c, d_fora), com d_fora = a·√(1/3 + (c/a)²/4); FEA = (2π/(3√3))·(2R_c/a)³/(c/a).

R2-BE-01 (ressalva R-1 do parecer de termodinâmica, 2026-11-13 §7.a): a translação de rede ``c`` entrou
no mínimo. Ela só é a menor distância quando c/a < 2/3, faixa inalcançável pela API (``FAIXA_C_A`` começa
em 1,0) mas alcançável na função do motor — e lá o FEA voltava a crescer (≈1,2 em c/a = 0,2).
Nenhum valor desta tabela muda: para c/a ≥ 2/3 a fórmula é idêntica à anterior.

Ressalva R-2: os valores de referência são GERADOS do c/a do seed (não copiados do parecer) e comparados
com tolerância. O parecer obteve à mão Mg 0,736427 / Ti 0,720162 / Co 0,735900; o motor dá
0,73641753 / 0,72013184 / 0,73596760. A diferença (até 6,8e-5) é do cálculo manual do parecer, não do
motor: ``test_fea_do_hc_confere_com_aritmetica_de_40_digitos`` reproduz os valores do motor com
``decimal`` a 40 dígitos, concordando até ~1e-16.
"""

from __future__ import annotations

import math

import pytest

from app.engines.crystallography.estruturas import c_a_ideal
from app.engines.crystallography.geometria import (
    contato_tipo_hc,
    distancia_entre_planos_hc,
    fator_empacotamento,
    raio_contato_rel_hc,
)

from ._motor import calcular_estrutura

FEA_MAXIMO = math.pi / (3 * math.sqrt(2))

#: c/a do seed (``propriedades_v14.json``), com todos os dígitos que o motor usa.
#: Ti é derivado de a e c medidos; os outros são tabelados.
C_A_SEED = {"Mg": 1.624, "Ti": 1.587258556421552, "Co": 1.623, "Zn": 1.856}
#: Tolerância dos valores de regressão. 1e-9 é ~1e3 vezes a precisão de ponto flutuante acumulada nas
#: poucas operações da fórmula e ~1e4 vezes menor que a sensibilidade que importa cientificamente
#: (dFEA/d(c/a) ≈ 0,45, logo 1e-9 em FEA ≡ 2e-9 em c/a, muito abaixo do 4º dígito do dado de entrada).
TOL_FEA = 1e-9
#: Valores que o motor devolvia antes da correção (R = a/2 em qualquer c/a).
FEA_ANTIGO = {"Mg": 0.744581, "Ti": 0.761816, "Co": 0.745040, "Zn": 0.651508}


def _fea_esperado(c_a: float) -> float:
    """Derivação independente (parecer §1.4), sem chamar o motor: 2 esferas de raio R_c na célula primitiva."""
    rc = 0.5 * min(1.0, c_a, math.sqrt(1 / 3 + c_a * c_a / 4))
    return 2 * (4 / 3) * math.pi * rc ** 3 / (math.sqrt(3) / 2 * c_a)


#: Valores de regressão GERADOS do c/a do seed (ressalva R-2): nada é copiado do parecer.
FEA_ESPERADO = {s: _fea_esperado(c) for s, c in C_A_SEED.items()}


def _fea_antigo(c_a: float) -> float:
    """Fórmula anterior: 6 esferas de raio a/2 no prisma hexagonal (sobrepostas quando c/a < ideal)."""
    return 6 * (4.0 / 3.0) * math.pi / ((3.0 * math.sqrt(3) / 2.0) * 2.0 ** 3 * c_a)


# --------------------------------------------------------------------------- T-C1 e R16
@pytest.mark.parametrize("simbolo", sorted(C_A_SEED))
def test_fea_do_hc_real_e_o_de_esferas_rigidas(simbolo):
    r = calcular_estrutura({"nome": simbolo})
    assert r["estrutura"] == "HC"
    assert r["c_a"] == pytest.approx(C_A_SEED[simbolo], rel=1e-15)   # o c/a do seed não mudou
    assert r["fea"] == pytest.approx(FEA_ESPERADO[simbolo], abs=TOL_FEA)
    assert r["vazios"] == pytest.approx(1.0 - FEA_ESPERADO[simbolo], abs=TOL_FEA)
    assert r["fea"] <= FEA_MAXIMO * (1 + 1e-12)
    # o valor antigo é reproduzido pela fórmula antiga: a mudança é de fórmula, não de dado
    assert _fea_antigo(r["c_a"]) == pytest.approx(FEA_ANTIGO[simbolo], abs=1e-6)


def test_fea_do_hc_abaixo_do_ideal_era_impossivel_e_deixou_de_ser():
    for simbolo in ("Mg", "Ti", "Co"):
        r = calcular_estrutura({"nome": simbolo})
        assert r["c_a"] < c_a_ideal()
        assert _fea_antigo(r["c_a"]) > FEA_MAXIMO          # o valor antigo violava o limite de Kepler/Hales
        assert r["fea"] < FEA_MAXIMO
        assert r["contato_tipo"] == "entre_planos"


@pytest.mark.parametrize("c_a", [1.0, 1.1, 1.3, 1.5, 1.6, 1.632993161855452, 1.7, 1.856, 2.0, 2.5])
def test_fea_nunca_passa_do_limite_de_empacotamento(c_a):
    fea = fator_empacotamento("HC", c_a)
    assert fea <= FEA_MAXIMO * (1 + 1e-12)
    # conferência independente: 2 esferas de raio R_c na célula primitiva (√3/2)·a²·c
    assert fea == pytest.approx(_fea_esperado(c_a), rel=1e-12)


# --------------------------------------------------------------------------- R2-BE-01 / ressalva R-1
@pytest.mark.parametrize("c_a", [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.6, 2 / 3, 0.7, 0.8, 0.8164965809277261,
                                 0.9, 1.0, 1.2, 1.4, 1.5, 1.6, 1.632993161855452, 1.7, 1.856, 2.0, 2.5,
                                 3.0, 5.0, 10.0, 100.0])
def test_invariante_fea_vale_em_toda_a_faixa_de_c_a(c_a):
    """FEA ≤ π/(3√2) em TODO c/a > 0, inclusive abaixo de 2/3, onde a translação c é a menor distância."""
    fea = fator_empacotamento("HC", c_a)
    assert 0.0 < fea <= FEA_MAXIMO * (1 + 1e-12)
    assert fea == pytest.approx(_fea_esperado(c_a), rel=1e-12)


@pytest.mark.parametrize("c_a", [0.01, 0.1, 0.2, 0.3, 0.5, 0.6])
def test_abaixo_de_dois_tercos_a_translacao_c_limita_o_raio(c_a):
    """Sem a translação c no mínimo, o raio ficava grande demais e o FEA chegava a ~1,2 em c/a = 0,2."""
    sem_c = 0.5 * min(1.0, math.sqrt(1 / 3 + c_a * c_a / 4))        # fórmula anterior à correção
    assert raio_contato_rel_hc(c_a) == pytest.approx(0.5 * c_a, rel=1e-12)
    assert raio_contato_rel_hc(c_a) < sem_c
    fea_sem_c = 2 * (4 / 3) * math.pi * sem_c ** 3 / (math.sqrt(3) / 2 * c_a)
    if c_a <= 0.3:
        assert fea_sem_c > FEA_MAXIMO            # o valor anterior era impossível (0,86 em 0,3; 1,22 em 0,2)
    assert fator_empacotamento("HC", c_a) <= FEA_MAXIMO * (1 + 1e-12)


def test_acima_de_dois_tercos_nada_mudou():
    """Para c/a ≥ 2/3 (toda a faixa aceita pela API) a correção R-1 não altera nenhum valor."""
    for i in range(0, 200):
        c_a = 2 / 3 + i * 0.01
        sem_c = 0.5 * min(1.0, math.sqrt(1 / 3 + c_a * c_a / 4))
        assert raio_contato_rel_hc(c_a) == pytest.approx(sem_c, rel=1e-15)


def test_fea_do_hc_confere_com_aritmetica_de_40_digitos():
    """Ressalva R-2: a diferença com os valores manuais do parecer é do cálculo manual, não do motor."""
    from decimal import Decimal, getcontext
    getcontext().prec = 40
    pi = Decimal("3.1415926535897932384626433832795028841971693993751")
    for simbolo, c_a in C_A_SEED.items():
        razao = Decimal(repr(c_a))
        d_fora = (Decimal(1) / 3 + razao * razao / 4).sqrt()
        rc = min(Decimal(1), razao, d_fora) / 2
        esperado = (2 * (Decimal(4) / 3) * pi * rc ** 3) / (Decimal(3).sqrt() / 2 * razao)
        assert fator_empacotamento("HC", c_a) == pytest.approx(float(esperado), rel=1e-15), simbolo


def test_fea_maximo_no_c_a_ideal():
    ideal = c_a_ideal()
    assert fator_empacotamento("HC", ideal) == pytest.approx(FEA_MAXIMO, rel=1e-12)
    for desvio in (-0.05, -0.01, 0.01, 0.05):
        assert fator_empacotamento("HC", ideal + desvio) < FEA_MAXIMO


@pytest.mark.parametrize("c_a", [1.5, 1.6, 1.70, 1.856, 2.0])
def test_fea_acima_do_ideal_nao_mudou(c_a):
    # Para c/a ≥ ideal o contato é basal (R = a/2) e a fórmula nova coincide com a anterior.
    if c_a >= c_a_ideal():
        assert fator_empacotamento("HC", c_a) == pytest.approx(_fea_antigo(c_a), rel=1e-12)
    else:
        assert fator_empacotamento("HC", c_a) < _fea_antigo(c_a)


# --------------------------------------------------------------------------- T-C2 e campos de contexto
def test_campos_de_contexto_do_hc_fora_do_ideal():
    r = calcular_estrutura({"nome": "Mg"})
    assert r["fea_modelo"] == "esferas_rigidas"
    assert r["nc"] == 12 and r["nc_txt"] == "6 + 6"
    assert r["c_a_ideal"] == pytest.approx(math.sqrt(8 / 3), rel=1e-15)
    assert r["c_a_natureza"] == "tabelado"
    assert r["raio_contato_rel"] == pytest.approx(0.498166, abs=1e-6)
    basal, fora = r["vizinhos"]
    assert (basal["grupo"], basal["n"], basal["d_rel"]) == ("basal", 6, 1.0)
    assert fora["grupo"] == "entre_planos" and fora["n"] == 6
    assert fora["d_rel"] == pytest.approx(0.996332, abs=1e-6)
    assert fora["d_nm"] == pytest.approx(fora["d_rel"] * r["a_nm"], rel=1e-12)
    assert basal["d_nm"] == pytest.approx(r["a_nm"], rel=1e-12)


def test_c_a_natureza_do_titanio_vem_de_a_e_c_medidos():
    r = calcular_estrutura({"nome": "Ti"})
    assert r["c_a_natureza"] == "derivado_de_a_c_medidos"
    assert r["c_a"] == pytest.approx(r["c_nm"] / r["a_nm"], rel=1e-12)


def test_c_a_informado_pelo_usuario_e_rotulado():
    r = calcular_estrutura({"nome": "HC", "raio": 0.16, "peso": 24.31, "c_a": 1.624})
    assert r["c_a_natureza"] == "informado"
    assert r["fea"] == pytest.approx(0.736418, abs=1e-6)


def test_hc_ideal_tem_contato_ambos_e_nc_12():
    r = calcular_estrutura({"nome": "HC", "raio": 0.16})
    assert r["c_a_natureza"] == "ideal"
    assert r["contato_tipo"] == "ambos"
    assert r["nc_txt"] == "12"
    assert r["raio_contato_rel"] == pytest.approx(0.5, rel=1e-12)
    assert r["fea"] == pytest.approx(FEA_MAXIMO, rel=1e-12)
    assert "basal" in r["contato"] and "planos" in r["contato"]


@pytest.mark.parametrize("estrutura", ["CS", "CCC", "CFC"])
def test_estrutura_cubica_nao_tem_campos_de_hc(estrutura):
    r = calcular_estrutura({"nome": estrutura, "raio": 0.13})
    assert r["raio_contato_rel"] is None
    assert r["contato_tipo"] is None
    assert r["c_a_ideal"] is None
    assert r["c_a_natureza"] is None
    assert r["vizinhos"] is None
    assert r["nc_txt"] == str(r["nc"])
    assert r["fea_modelo"] == "esferas_rigidas"


def test_tolerancia_do_rotulo_de_contato():
    ideal = c_a_ideal()
    assert contato_tipo_hc(ideal) == "ambos"
    assert contato_tipo_hc(ideal * (1 + 9e-5)) == "ambos"
    assert contato_tipo_hc(ideal * (1 + 2e-4)) == "basal"
    assert contato_tipo_hc(ideal * (1 - 2e-4)) == "entre_planos"
    assert raio_contato_rel_hc(ideal) == pytest.approx(0.5, rel=1e-12)
    assert distancia_entre_planos_hc(ideal) == pytest.approx(1.0, rel=1e-12)
