"""Motor HEA analítico (Fase 6): valores conferidos à mão e política de dados."""

from __future__ import annotations

import math

import pytest

from app.engines.crystallography import EntradaInvalida
from app.engines.hea.analitico import R_GASES, analisar_liga, entropia_mistura
from app.engines.procedencia import PoliticaDados
from app.repositories.materiais_json import repositorio_padrao

REPO = repositorio_padrao()
DEV = PoliticaDados(permitir_nao_validado=True)
PROD = PoliticaDados(permitir_nao_validado=False)


def _analisar(composicao, politica=DEV):
    return analisar_liga({"nome": "t", "composicao": composicao}, REPO, REPO, politica)


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_entropia_equimolar_e_r_ln_n(n):
    assert entropia_mistura([(str(i), 1.0 / n) for i in range(n)]) == pytest.approx(R_GASES * math.log(n))


def test_alcocrfeni_conferido_a_mao():
    r = _analisar(dict.fromkeys(("Al", "Co", "Cr", "Fe", "Ni"), 1))
    raios = {"Al": 0.1431, "Co": 0.1253, "Cr": 0.1249, "Fe": 0.1241, "Ni": 0.1246}
    r_medio = sum(raios.values()) / 5
    delta = 100 * math.sqrt(sum(0.2 * (1 - ri / r_medio) ** 2 for ri in raios.values()))
    assert r["delta"] == pytest.approx(delta, abs=1e-4)
    assert r["VEC"] == pytest.approx((3 + 9 + 6 + 8 + 10) / 5)
    assert r["Tm"] == pytest.approx((660 + 1495 + 1857 + 1538 + 1455) / 5 + 273.15, abs=0.1)
    assert r["fase"].startswith("CFC + CCC") and "estrutura_sugerida" not in r


def test_normaliza_quantidades_e_ordena():
    r = _analisar({"Ni": 50, "Cu": 50})
    assert r["fracoes"] == {"Cu": 0.5, "Ni": 0.5} and r["comp_percent"] == {"Cu": 50.0, "Ni": 50.0}
    assert any("Menos de 5 elementos" in a for a in r["procedencia"]["avisos"])


def test_vec_baixo_sugere_ccc():
    r = _analisar({"Cr": 1, "Mo": 1, "W": 1})
    assert r["VEC"] == pytest.approx(6.0) and r["estrutura_sugerida"] == "CCC"


def test_nunca_inventa_entalpia_omega_dureza_ou_gibbs():
    r = _analisar(dict.fromkeys(("Co", "Cr", "Fe", "Ni"), 1))
    assert r["dH"] is None and r["omega"] is None and r["dureza"] is None and r["gibbs"] == []
    assert "Q-01" in r["indisponiveis"]["dH"]


def test_producao_bloqueia_dados_nao_validados():
    r = _analisar(dict.fromkeys(("Co", "Cr", "Fe", "Ni"), 1), PROD)
    assert r["dS"] == pytest.approx(R_GASES * math.log(4), abs=1e-4)
    assert r["delta"] is None and r["VEC"] is None and r["Tm"] is None
    assert r["procedencia"]["dados_usados"] == []


def test_dados_usados_registram_estado_e_fonte():
    r = _analisar({"Co": 1, "Ni": 1})
    usados = {(u["simbolo"], u["codigo"]): u for u in r["procedencia"]["dados_usados"]}
    assert usados[("Co", "vec")]["fonte"] == "guo2011"
    assert usados[("Ni", "raio_atomico")]["estado"] == "aguardando_validacao"
    assert r["procedencia"]["avisos"]   # dados sem validação → aviso explícito


@pytest.mark.parametrize("composicao", [{}, {"Fe": 1}, {"Fe": -1, "Ni": 1}, {"Fe": "x", "Ni": 1},
                                        {"Fe": 0, "Ni": 1}, {f"E{i}": 1 for i in range(13)}])
def test_entradas_invalidas(composicao):
    with pytest.raises(EntradaInvalida):
        _analisar(composicao)
