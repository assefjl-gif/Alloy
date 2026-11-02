"""Soluções sólidas (recurso da v1.4, RQ-CIE-11).

Referências:
* Lei de Vegard (Vegard, Z. Phys. 5, 1921): a = (1−x)·a_A + x·a_B na estrutura do solvente.
* Conversão % atômica → % em peso: Callister & Rethwisch, eq. 4.6–4.7.
* Regras de Hume-Rothery (Callister, seção 4.3); Cu–Ni é o exemplo clássico de solubilidade total.
* Raio livre do sítio octaédrico: CCC (2/√3 − 1)·R ≈ 0,155·R; CFC (√2 − 1)·R ≈ 0,414·R.
* Superestruturas L1₂ (Cu₃Au), L1₀ (CuAu), B2 (CuZn).
"""

from __future__ import annotations

import math

import pytest

from app.engines.crystallography.constantes import N_AVOGADRO
from app.engines.crystallography.erros import ErroDominio
from app.engines.crystallography.ligas import calcular_solucao_solida
from app.engines.procedencia import DadoNaoValidado, PoliticaDados
from app.repositories.materiais_json import repositorio_padrao

REPO = repositorio_padrao()
DEV = PoliticaDados(permitir_nao_validado=True)
PROD = PoliticaDados(permitir_nao_validado=False)


def liga(politica=DEV, **payload):
    return calcular_solucao_solida(payload, REPO, REPO, politica)


def test_vegard_cu_ni():
    r = liga(base="Cu", soluto="Ni", x=30)
    r_medio = 0.7 * 0.1278 + 0.3 * 0.1246
    assert r["a_nm"] == pytest.approx(2 * math.sqrt(2) * r_medio, rel=1e-12)
    assert r["a_base_nm"] == pytest.approx(2 * math.sqrt(2) * 0.1278, rel=1e-12)


def test_percentual_em_peso_cu_ni():
    r = liga(base="Cu", soluto="Ni", x=30)
    esperado = 0.3 * 58.69 / (0.3 * 58.69 + 0.7 * 63.55) * 100
    assert r["pct_peso"] == pytest.approx(esperado, rel=1e-12)


def test_densidade_da_liga_usa_massa_media_e_avogadro_exato():
    r = liga(base="Cu", soluto="Ni", x=30)
    a_cm = r["a_nm"] * 1e-7
    esperado = 4 * (0.7 * 63.55 + 0.3 * 58.69) / (a_cm ** 3 * N_AVOGADRO)
    assert r["densidade"] == pytest.approx(esperado, rel=1e-12)


def test_cu_ni_atende_as_quatro_regras():
    r = liga(base="Cu", soluto="Ni", x=30)
    assert [regra["ok"] for regra in r["regras"]] == [True, True, True, True]


def test_em_producao_regras_sem_dado_validado_ficam_indisponiveis():
    r = liga(PROD, base="Cu", soluto="Ni", x=30)
    por_nome = {regra["criterio"]: regra for regra in r["regras"]}
    assert por_nome["Tamanho atômico"]["ok"] is True            # usa só raio (dado do seed B)
    assert por_nome["Estrutura cristalina"]["ok"] is True
    assert por_nome["Eletronegatividade"]["ok"] is None
    assert por_nome["Eletronegatividade"]["indisponivel"]
    assert por_nome["Valência"]["ok"] is None
    assert r["a_nm"] > 0 and r["densidade"] > 0                # Vegard e densidade continuam


def test_dados_nao_validados_aparecem_na_procedencia():
    r = liga(base="Cu", soluto="Ni", x=30)
    usados = {(u["simbolo"], u["codigo"]) for u in r["procedencia"]["dados_usados"]}
    assert ("Cu", "eletronegatividade") in usados
    assert r["procedencia"]["classe"] == "estimativa_modelo"
    assert any("sem validação" in aviso for aviso in r["procedencia"]["avisos"])


def test_ordenacao_l12_coloca_soluto_nos_vertices():
    n = 2
    r = liga(base="Cu", soluto="Au", x=25, arranjo="ordenado", n=n)
    assert r["fase_ordenada"].startswith("L1₂")
    assert r["n_soluto"] == (n + 1) ** 3


def test_ordenacao_b2_na_ccc_e_so_geometrica():
    # Fe–Cr real NÃO forma B2 (forma a fase σ): o motor monta o protótipo e avisa que é hipotético.
    n = 2
    r = liga(base="Fe", soluto="Cr", x=50, arranjo="ordenado", n=n)
    assert r["fase_ordenada"].startswith("B2")
    assert r["n_soluto"] == n ** 3      # centros dos cubos
    assert "hipotético" in r["nota_arranjo"]


def test_composicao_sem_superestrutura_cai_para_aleatorio_com_nota():
    r = liga(base="Cu", soluto="Ni", x=30, arranjo="ordenado")
    assert r["fase_ordenada"] is None
    assert r["nota_arranjo"]


def test_aleatorio_e_reprodutivel_pela_semente():
    a = liga(base="Cu", soluto="Ni", x=30, semente=7)
    b = liga(base="Cu", soluto="Ni", x=30, semente=7)
    c = liga(base="Cu", soluto="Ni", x=30, semente=8)
    assert [t["elemento"] for t in a["atomos"]] == [t["elemento"] for t in b["atomos"]]
    assert [t["elemento"] for t in a["atomos"]] != [t["elemento"] for t in c["atomos"]]
    assert a["n_soluto"] == round(0.30 * len(a["atomos"]))


def test_intersticial_fe_c_raio_do_sitio_octaedrico():
    r = liga(base="Fe", soluto="C", x=2)
    assert r["intersticial"] is True
    assert r["sitio"]["raio_nm"] == pytest.approx((2 / math.sqrt(3) - 1) * 0.1241, rel=1e-12)
    assert r["sitio"]["fator"] == pytest.approx(0.1547, abs=1e-4)
    assert r["a_nm"] == pytest.approx(r["a_base_nm"])  # a rede do solvente não muda neste modelo


def test_intersticial_em_producao_exige_dado_validado():
    with pytest.raises(DadoNaoValidado):
        liga(PROD, base="Fe", soluto="C", x=2)


def test_distorcao_e_rotulada_como_ilustrativa():
    r = liga(base="Cu", soluto="Ag", x=20, distorcer=True, n=2)
    assert r["distorcao"]["classe"] == "simulacao_ilustrativa"


@pytest.mark.parametrize("payload", [
    {"base": "Cu", "soluto": "Cu", "x": 10},
    {"base": "Cu", "soluto": "Ni", "x": 120},
    {"base": "Fe", "soluto": "C", "x": 25},
    {"base": "Xx", "soluto": "Ni", "x": 10},
    {"base": "Cu", "soluto": "Ni", "x": 10, "n": 9},
])
def test_entradas_invalidas(payload):
    with pytest.raises(ErroDominio):
        liga(**payload)
