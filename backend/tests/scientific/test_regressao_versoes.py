"""Regressão entre versões: o motor consolidado contra as saídas congeladas de A v1.4, B v1.1.0 e D v1.0.

RQ-QA-03 / INT-02: toda divergência precisa estar EXPLICADA aqui. As explicações aceitas são:
* N_A: A e D usam 6,022e23; o motor usa o valor exato CODATA 2018 (CIE-02);
* Ti: A e D derivam a de R; o motor usa a rede medida (ADR-005, CIE-01);
* geometria HC: A e D arredondam os vértices do hexágono para 6 casas ANTES de calcular
  (``_arred`` na construção da célula), o que desloca a área em ~5e-7 relativo; o B e o motor
  calculam sem arredondar e só arredondam na saída (achado CR-08 do B). Diferença verificada
  na Fase 3: B = motor exatamente; A = D = −4,7e-7 e −4,5e-7.
Qualquer outra diferença quebra o teste.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engines.crystallography import calcular_miller
from app.engines.crystallography.constantes import N_AVOGADRO

from ..unit.engines._motor import calcular_estrutura

REF = json.loads((Path(__file__).parent / "dados" / "referencia_versoes.json").read_text(encoding="utf-8"))
METAIS = sorted(REF["estruturas"])
NA_ANTIGO = 6.022e23
COM_REDE_MEDIDA = {"Ti"}


@pytest.mark.parametrize("metal", METAIS)
def test_motor_reproduz_b_exatamente(metal):
    atual = calcular_estrutura({"nome": metal})
    b = REF["estruturas"][metal]["B"]
    for campo in ("a_nm", "fea", "densidade"):
        assert atual[campo] == pytest.approx(b[campo], rel=1e-12), campo


@pytest.mark.parametrize("versao", ["A", "D"])
@pytest.mark.parametrize("metal", METAIS)
def test_diferencas_para_a_e_d_sao_so_as_explicadas(metal, versao):
    atual = calcular_estrutura({"nome": metal})
    antigo = REF["estruturas"][metal][versao]
    assert atual["fea"] == pytest.approx(antigo["fea"], rel=2e-4 if metal in COM_REDE_MEDIDA else 1e-12)
    if metal in COM_REDE_MEDIDA:
        # Explicação ADR-005: rede medida 0,2951 nm × 2R = 0,2890 nm → densidade cai ~6 %.
        assert atual["a_fonte"] == "medido"
        assert antigo["a_nm"] == pytest.approx(2 * 0.1445, rel=1e-12)
        assert atual["densidade"] < antigo["densidade"] * 0.95
        return
    assert atual["a_nm"] == pytest.approx(antigo["a_nm"], rel=1e-12)
    # Explicação CIE-02: só a constante de Avogadro muda a densidade.
    assert atual["densidade"] == pytest.approx(antigo["densidade"] * NA_ANTIGO / N_AVOGADRO, rel=1e-12)


@pytest.mark.parametrize("caso", REF["miller"], ids=lambda c: c["caso"])
def test_miller_identico_nas_tres_versoes(caso):
    estrutura, tipo, *_ = caso["caso"].split(" ")
    indices = json.loads(caso["caso"].split(" ", 2)[2])
    atual = calcular_miller({"estrutura": estrutura, "tipo": tipo, "indices": indices})
    for versao in ("A", "B", "D"):
        antigo = caso[versao]
        # CR-08: só A e D na HC carregam o arredondamento prematuro dos vértices.
        tolerancia = 1e-6 if (estrutura == "HC" and versao in ("A", "D")) else 1e-12
        assert atual["notacao"] == antigo["notacao"]
        assert len(atual["atomos"]) == antigo["n_atomos_marcados"]
        if antigo["d_rel"] is not None:
            assert atual["d_rel"] == pytest.approx(antigo["d_rel"], rel=tolerancia)
        if antigo["area_rel"] is not None:
            assert atual["area_rel"] == pytest.approx(antigo["area_rel"], rel=tolerancia)
        if antigo["atomos_contados"] is not None:
            assert atual["atomos_contados"] == pytest.approx(antigo["atomos_contados"])
