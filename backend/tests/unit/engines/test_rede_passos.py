"""Caminho inverso a → R e passo a passo de a e do FEA (recursos da v1.4, RQ-CIE-02/10).

Referências: relações de contato a = 2R (CS, HC), a√3 = 4R (CCC), a√2 = 4R (CFC) e
FEA ideal 0,52 / 0,68 / 0,74 / 0,74 (Callister & Rethwisch, seções 3.4 e 3.5).
"""

from __future__ import annotations

import math

import pytest

from ._motor import calcular_estrutura


def test_a_informado_define_r_pela_condicao_de_contato():
    r = calcular_estrutura({"nome": "Fe", "a": "0,30"})
    assert r["a_nm"] == pytest.approx(0.30)
    assert r["raio_nm"] == pytest.approx(0.30 * math.sqrt(3) / 4)
    assert r["a_fonte"] == "informado"
    assert r["editado"] is True
    assert r["densidade_exp"] is None  # dado editado não é comparado com o experimental


def test_a_igual_ao_do_modelo_nao_conta_como_edicao():
    # Cu: R = 0,1278 nm → a = 2√2·R = 0,36148 nm; 0,3615 difere < 1e-4 relativo
    r = calcular_estrutura({"nome": "Cu", "a": 0.3615})
    assert r["editado"] is False
    assert r["densidade_exp"] == pytest.approx(8.94)


def test_a_tem_prioridade_sobre_raio_e_gera_aviso():
    r = calcular_estrutura({"nome": "CFC", "a": 0.40, "raio": 0.15})
    assert r["a_nm"] == pytest.approx(0.40)
    assert any("raio informado foi ignorado" in aviso for aviso in r["avisos"])


def test_a_fora_da_faixa_e_recusado():
    from app.engines.crystallography import EntradaInvalida
    with pytest.raises(EntradaInvalida):
        calcular_estrutura({"nome": "Cu", "a": 5})


@pytest.mark.parametrize(("estrutura", "contato"), [("CS", "a = 2R"), ("CCC", "a√3 = 4R"),
                                                     ("CFC", "a√2 = 4R"), ("HC", "a = 2R")])
def test_passos_do_parametro_comecam_pela_condicao_de_contato(estrutura, contato):
    r = calcular_estrutura({"nome": estrutura})
    assert r["passos_parametro"][0]["formula"].startswith(contato)


def test_passos_do_parametro_com_rede_medida_mostram_os_dois_valores():
    r = calcular_estrutura({"nome": "Ti"})
    assert r["a_fonte"] == "medido"
    textos = " ".join(p["formula"] + " " + (p["detalhe"] or "") for p in r["passos_parametro"])
    assert "0,2951" in textos          # a medido
    assert "0,2890" in textos          # a = 2R do modelo de contato


@pytest.mark.parametrize(("estrutura", "fea"), [("CS", math.pi / 6), ("CCC", math.pi * math.sqrt(3) / 8),
                                                ("CFC", math.pi / (3 * math.sqrt(2))),
                                                ("HC", math.pi / (3 * math.sqrt(2)))])
def test_passos_do_fea_terminam_no_valor_do_motor(estrutura, fea):
    r = calcular_estrutura({"nome": estrutura})
    assert r["fea"] == pytest.approx(fea, rel=1e-9)
    final = next(p for p in r["passos_fea"] if p["titulo"] == "Fator de empacotamento")
    assert final["formula"].endswith(f"{fea:.4f}".replace(".", ","))


def test_passos_do_fea_hc_explicam_efeito_de_c_a():
    r = calcular_estrutura({"nome": "Zn"})  # c/a 1,856 > ideal 1,633
    titulos = [p["titulo"] for p in r["passos_fea"]]
    assert "Efeito da razão c/a" in titulos
    assert r["fea"] < math.pi / (3 * math.sqrt(2))
