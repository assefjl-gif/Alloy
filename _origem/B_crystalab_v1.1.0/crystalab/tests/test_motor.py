"""Testes do núcleo cristalográfico — valores de referência da seção 7 do relatório de auditoria."""

from __future__ import annotations

import itertools
import math

import pytest

from crystalab.core import (
    ESTRUTURAS,
    ErroDominio,
    IndiceMillerInvalido,
    MaterialDesconhecido,
    PlanoForaDaCelula,
    calcular_estrutura,
    calcular_miller,
    cart_para_frac,
    fator_empacotamento,
    frac_para_cart,
    reduzir,
    repositorio_padrao,
)
from crystalab.core.constantes import N_AVOGADRO

# --------------------------------------------------------------------------- densidades (seção 7.1)
# Valores medidos na v1.0; a v1.1 usa N_A exato (CODATA), o que muda ~0,004 % — tolerância 0,05 %.
GOLDEN = {"Fe": 7.880, "Cu": 8.937, "Al": 2.703, "Au": 19.284, "Mg": 1.752, "Zn": 7.149, "Po": 9.149}


@pytest.mark.parametrize("simbolo,esperado", GOLDEN.items())
def test_densidades_golden(simbolo, esperado):
    r = calcular_estrutura({"nome": simbolo})
    assert r["densidade"] == pytest.approx(esperado, rel=5e-4)
    assert abs(r["erro_percent"]) < 0.7
    assert r["avisos"] == []


def test_ti_corrigido_cr01():
    r = calcular_estrutura({"nome": "Ti"})
    assert r["a_fonte"] == "medido"
    assert r["a_nm"] == pytest.approx(0.2951)
    assert r["c_nm"] == pytest.approx(0.4684)
    assert r["densidade"] == pytest.approx(4.50, abs=0.01)
    assert abs(r["erro_percent"]) < 1.0


def test_ti_ida_e_volta_do_editor_nao_marca_edicao():
    # O editor da UI devolve c/a com 4 casas: não pode virar "parâmetros editados".
    r = calcular_estrutura({"nome": "Ti", "estrutura": "HC", "raio": "0.1445", "peso": "47.87", "c_a": "1.5873"})
    assert r["editado"] is False and r["densidade_exp"] == 4.51


def test_aviso_desvio_acima_de_3_porcento():
    r = calcular_estrutura({"nome": "Cu", "raio": 0.12})  # raio editado → sem experimental
    assert r["densidade_exp"] is None
    # sem valor experimental não há aviso de desvio
    assert not any("Desvio" in a for a in r["avisos"])


def test_troca_de_estrutura_emite_aviso_cr02():
    r = calcular_estrutura({"nome": "Fe", "estrutura": "CFC"})
    assert r["editado"] and r["densidade_exp"] is None
    assert any("Goldschmidt" in a for a in r["avisos"])
    r = calcular_estrutura({"nome": "Mg", "estrutura": "CCC"})
    assert r["c_a"] is None and any("c/a do Mg foi descartado" in a for a in r["avisos"])


def test_fea_ideal():
    assert fator_empacotamento("CS") == pytest.approx(0.5236, abs=1e-4)
    assert fator_empacotamento("CCC") == pytest.approx(0.6802, abs=1e-4)
    assert fator_empacotamento("CFC") == pytest.approx(0.7405, abs=1e-4)
    assert fator_empacotamento("HC", ESTRUTURAS["HC"]["c_a_ideal"]) == pytest.approx(0.7405, abs=1e-4)


@pytest.mark.parametrize("metal", [m.simbolo for m in repositorio_padrao().listar()])
def test_propriedade_rho_v_na_igual_n_a(metal):
    r = calcular_estrutura({"nome": metal})
    assert r["densidade"] * r["volume_cm3"] * N_AVOGADRO == pytest.approx(r["n"] * r["peso"], rel=1e-12)


def test_base_separada_das_replicas_cr07():
    contagens = {"Po": (8, 1), "Fe": (9, 2), "Cu": (14, 4), "Mg": (17, 2)}
    for simbolo, (desenho, base) in contagens.items():
        r = calcular_estrutura({"nome": simbolo})
        assert len(r["atomos"]) == desenho
        assert len(r["base"]) == base == r["z"]
        assert all(0 <= v < 1 for s in r["base"] for v in s["frac"])
        assert sum(g["contribuicao"] for g in r["contagem"]) == pytest.approx(r["n"])


def test_resolucao_de_nomes_sem_choque():
    assert calcular_estrutura({"nome": "cs"})["estrutura"] == "CS"
    assert calcular_estrutura({"nome": "ferro"})["simbolo"] == "Fe"
    assert calcular_estrutura({"nome": "fe"})["simbolo"] == "Fe"
    assert calcular_estrutura({"nome": "bcc"})["generica"] is True
    with pytest.raises(MaterialDesconhecido):
        calcular_estrutura({"nome": "Xx"})


def test_entrada_invalida_e_erro_de_dominio():
    with pytest.raises(ErroDominio):
        calcular_estrutura({"nome": "Fe", "raio": 3})
    with pytest.raises(ErroDominio):
        calcular_estrutura({})


# --------------------------------------------------------------------------- Miller
def test_plano_111_cfc():
    r = calcular_miller({"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1]})
    assert len(r["poligono"]) == 3 and r["d_rel"] == pytest.approx(0.57735, abs=1e-5)
    assert len(r["atomos"]) == 6 and r["ordem"] == 1 and r["avisos"] == []


def test_plano_222_sinaliza_ordem_cr03():
    r = calcular_miller({"estrutura": "CFC", "tipo": "plano", "indices": [2, 2, 2]})
    assert r["ordem"] == 2 and r["indices_reduzidos"] == [1, 1, 1]
    assert r["d_rel"] == pytest.approx(0.28868, abs=1e-5) and r["avisos"]


@pytest.mark.parametrize("estrutura,indices,atomos,dl", [
    ("CFC", [1, 1, 0], 2.0, math.sqrt(2)),
    ("CCC", [1, 1, 1], 2.0, 2 / math.sqrt(3)),
])
def test_direcoes_compactas(estrutura, indices, atomos, dl):
    r = calcular_miller({"estrutura": estrutura, "tipo": "direcao", "indices": indices})
    assert r["atomos_contados"] == atomos
    assert r["densidade_linear_rel"] == pytest.approx(dl)


def test_direcao_210_sem_densidade_linear():
    r = calcular_miller({"estrutura": "CFC", "tipo": "direcao", "indices": [2, 1, 0]})
    assert r["densidade_linear_rel"] is None


def test_hc_miller_bravais():
    r = calcular_miller({"estrutura": "HC", "tipo": "direcao", "indices": [2, -1, -1, 0]})
    assert "[1 0 0]" in r["notacao_alternativa"] and r["densidade_linear_rel"] == pytest.approx(1.0)
    with pytest.raises(IndiceMillerInvalido):
        calcular_miller({"estrutura": "HC", "tipo": "plano", "indices": [1, 0, 0, 1]})


def test_varredura_geometrica_cr06():
    """Para todo (hkl) em −3..3: ou o plano não corta a célula, ou o polígono é válido."""
    for estrutura in ESTRUTURAS:
        c_a = ESTRUTURAS["HC"]["c_a_ideal"] if estrutura == "HC" else None
        for idx in itertools.product(range(-3, 4), repeat=3):
            if not any(idx):
                continue
            try:
                r = calcular_miller({"estrutura": estrutura, "tipo": "plano", "indices": list(idx), "c_a": c_a})
            except PlanoForaDaCelula:
                continue
            assert len(r["poligono"]) >= 3 and r["area_rel"] > 1e-9
            assert sum(v * v for v in r["normal"]) == pytest.approx(1.0, abs=1e-5)
            pts = r["poligono"]
            dist = min(math.dist(pts[i], pts[j]) for i in range(len(pts)) for j in range(i + 1, len(pts)))
            assert dist > 1e-4, f"vértices duplicados em {estrutura} {idx}"


def test_regressao_arredondamento_hc_cr08():
    # Na v1.0 o vértice (½, −√3/2, 0) ficava fora de (−3 −1 0) por erro de arredondamento.
    r = calcular_miller({"estrutura": "HC", "tipo": "plano", "indices": [-3, -1, 0], "c_a": 1.633})
    assert 5 in r["atomos"]


def test_reduzir_idempotente_e_conversoes_inversas():
    for idx in itertools.product(range(-4, 5), repeat=3):
        if any(idx):
            assert reduzir(reduzir(idx)) == reduzir(idx)
    for f in [(0.1, 0.7, 0.3), (2 / 3, 1 / 3, 0.5), (1, 0, 1)]:
        for estrutura in ("CFC", "HC"):
            ida = frac_para_cart(estrutura, f, 1.6)
            assert cart_para_frac(estrutura, ida, 1.6) == pytest.approx(f)
