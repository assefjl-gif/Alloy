"""Seed da tabela periódica (ADR-018): integridade, convenções, faixas físicas e conferência com fontes.

Testes puros sobre ``database/seeds/tabela_periodica/elementos.json`` (sem banco).
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
SEED = json.loads((RAIZ / "database" / "seeds" / "tabela_periodica" / "elementos.json").read_text(encoding="utf-8"))
ELEMENTOS = SEED["elementos"]
POR_SIMBOLO = {e["simbolo"]: e for e in ELEMENTOS}
UNIDADES = {"peso_atomico_padrao": "adimensional", "massa_isotopica_referencia": "u", "eletronegatividade": "Pauling",
            "raio_van_der_waals": "pm", "energia_ionizacao_1": "eV", "afinidade_eletronica": "eV",
            "temperatura_fusao": "K", "temperatura_ebulicao": "K", "densidade": "g/cm³"}
#: faixas físicas plausíveis — pegam erro de unidade (ex.: °C no lugar de K, nm no lugar de pm)
FAIXAS = {"eletronegatividade": (0.7, 4.0), "raio_van_der_waals": (100, 400), "energia_ionizacao_1": (3.5, 25),
          "afinidade_eletronica": (0, 3.7), "temperatura_fusao": (0.9, 4000), "temperatura_ebulicao": (4, 6000),
          "densidade": (5e-5, 41), "peso_atomico_padrao": (1, 239), "massa_isotopica_referencia": (90, 300)}


def prop(simbolo: str, codigo: str):
    return next((p for p in POR_SIMBOLO[simbolo]["propriedades"] if p["codigo"] == codigo), None)


def test_118_elementos_com_numeros_atomicos_contiguos_e_simbolos_unicos():
    assert len(ELEMENTOS) == 118
    assert [e["numero_atomico"] for e in ELEMENTOS] == list(range(1, 119))
    assert len({e["simbolo"] for e in ELEMENTOS}) == 118
    assert all(e["nome"] and e["nome_en"] for e in ELEMENTOS)


def test_blocos_grupos_e_periodos_seguem_a_tabela_de_18_colunas():
    assert Counter(e["bloco"] for e in ELEMENTOS) == {"s": 14, "p": 36, "d": 38, "f": 30}
    assert Counter(e["periodo"] for e in ELEMENTOS) == {1: 2, 2: 8, 3: 8, 4: 18, 5: 18, 6: 32, 7: 32}
    for e in ELEMENTOS:
        assert (e["bloco"] == "f") == (e["grupo"] is None), e["simbolo"]
    assert [e["simbolo"] for e in ELEMENTOS if e["grupo"] == 18] == ["He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"]
    assert [e["simbolo"] for e in ELEMENTOS if e["grupo"] == 1] == ["H", "Li", "Na", "K", "Rb", "Cs", "Fr"]
    assert (POR_SIMBOLO["Fe"]["periodo"], POR_SIMBOLO["Fe"]["grupo"]) == (4, 8)
    assert POR_SIMBOLO["Ts"]["grupo"] == 17   # a Wikipédia lista 15: erro da fonte registrado na conferência


def test_conferencia_contra_a_wikipedia_so_tem_a_divergencia_conhecida_do_tenesso():
    assert SEED["conferencias"] == ["Ts: grupo 17 (regra) × 15 (Wikipédia)"]


def test_toda_propriedade_tem_fonte_citada_unidade_certa_e_valor_finito_na_faixa():
    for e in ELEMENTOS:
        for p in e["propriedades"]:
            assert p["fonte"] in SEED["fontes"], (e["simbolo"], p)
            assert p["unidade"] == UNIDADES[p["codigo"]], (e["simbolo"], p)
            v = float(p["valor"])
            lo, hi = FAIXAS[p["codigo"]]
            assert math.isfinite(v) and lo <= v <= hi, (e["simbolo"], p["codigo"], v)


def test_fontes_tem_citacao_url_licenca_e_data_de_acesso():
    for chave, f in SEED["fontes"].items():
        assert f["citacao"] and f["url"] and f["licenca"] and f["acessado_em"], chave
    assert SEED["fontes"]["ciaaw_2024"]["doi"] == "10.1515/pac-2019-0603"
    assert len(SEED["fontes_brutas"]) == 4 and all(len(m["sha256"]) == 64 for m in SEED["fontes_brutas"].values())


def test_peso_atomico_padrao_so_da_ciaaw_e_massa_de_referencia_marcada_como_tal():
    com_peso = [e["simbolo"] for e in ELEMENTOS if prop(e["simbolo"], "peso_atomico_padrao")]
    assert len(com_peso) == 84
    for s in ("Tc", "Pm", "Po", "Rn", "Og"):
        assert prop(s, "peso_atomico_padrao") is None and prop(s, "massa_isotopica_referencia")
        assert "não é peso atômico padrão" in prop(s, "massa_isotopica_referencia")["nota"]
    for s in ("Bi", "Th", "Pa", "U"):            # radioativos COM composição terrestre característica
        assert prop(s, "peso_atomico_padrao")
    for e in ELEMENTOS:
        p = prop(e["simbolo"], "peso_atomico_padrao")
        if p and "intervalo_min" in p:
            # o valor ABREVIADO é arredondado e pode cair fora do intervalo (ex.: O 15,999 × [15,99903; 15,99977]);
            # o que a CIAAW garante é que valor ± incerteza cobre o intervalo padrão
            v, u = float(p["valor"]), float(p["incerteza"])
            assert v - u <= float(p["intervalo_min"]) and float(p["intervalo_max"]) <= v + u, e["simbolo"]


@pytest.mark.parametrize("simbolo, valor, incerteza", [
    ("H", "1.0080", "0.0002"), ("C", "12.011", "0.002"), ("Fe", "55.845", "0.002"),
    ("Zr", "91.222", "0.003"),   # revisão CIAAW 2024 (era 91,224)
])
def test_pesos_atomicos_conferidos_na_tabela_da_ciaaw(simbolo, valor, incerteza):
    p = prop(simbolo, "peso_atomico_padrao")
    assert (p["valor"], p["incerteza"]) == (valor, incerteza)


def test_inversoes_conhecidas_de_massa_na_tabela_periodica():
    """Ar > K, Co > Ni e Te > I: dados reais, não ordenados artificialmente."""
    peso = lambda s: float(prop(s, "peso_atomico_padrao")["valor"])  # noqa: E731
    assert peso("Ar") > peso("K") and peso("Co") > peso("Ni") and peso("Te") > peso("I")


def test_fusao_abaixo_da_ebulicao_quando_ambas_existem():
    for e in ELEMENTOS:
        tf, te = prop(e["simbolo"], "temperatura_fusao"), prop(e["simbolo"], "temperatura_ebulicao")
        if tf and te and e["simbolo"] != "As":   # arsênio sublima a 1 atm (a fonte dá ponto triplo > sublimação)
            assert float(tf["valor"]) < float(te["valor"]), e["simbolo"]


def test_estados_e_classificacao_coerentes():
    assert POR_SIMBOLO["Hg"]["estado_padrao"] == "liquido" and POR_SIMBOLO["Br"]["estado_padrao"] == "liquido"
    assert {s for s, e in POR_SIMBOLO.items() if e["estado_padrao"] == "gas"} == {
        "H", "He", "N", "O", "F", "Ne", "Cl", "Ar", "Kr", "Xe", "Rn"}
    assert POR_SIMBOLO["Fe"]["conhecido_antiguidade"] and POR_SIMBOLO["Fe"]["ano_descoberta"] is None
    assert not POR_SIMBOLO["Og"]["conhecido_antiguidade"] and POR_SIMBOLO["Og"]["ano_descoberta"] == 2006


def test_nomes_em_portugues_do_brasil():
    for s, nome in {"As": "Arsênio", "Se": "Selênio", "Mo": "Molibdênio", "Np": "Netúnio", "Og": "Oganessônio",
                    "Fe": "Ferro", "W": "Tungstênio", "N": "Nitrogênio"}.items():
        assert POR_SIMBOLO[s]["nome"] == nome


#: Divergências ENTRE o seed antigo (Callister/v1.4, usado pelos motores) e as fontes novas. Não foram
#: corrigidas em silêncio: dependem do validador científico (Q-03). Se a lista mudar, a documentação muda junto.
DIVERGENCIAS_CONHECIDAS = {
    "temperatura_fusao": {"Cr"},                     # v1.4 1857 °C × 2180 K (1906,85 °C)
    # diferença > 0,105: tabelas de Pauling distintas (Callister antigo × valores revisados de Allred)
    "eletronegatividade": {"Al", "Au", "Mg", "Mo", "Pb", "W", "Ni"},
}


def test_divergencias_com_o_seed_antigo_sao_exatamente_as_documentadas():
    arquivo = RAIZ / "database" / "seeds" / "cristalografia" / "propriedades_v14.json"
    v14 = json.loads(arquivo.read_text(encoding="utf-8"))
    achadas = {"temperatura_fusao": set(), "eletronegatividade": set()}
    for v in v14["valores"]:
        novo = prop(v["simbolo"], v["codigo"]) if v["simbolo"] in POR_SIMBOLO else None
        if v["codigo"] == "temperatura_fusao" and novo and abs(float(novo["valor"]) - (v["valor"] + 273.15)) > 5:
            achadas["temperatura_fusao"].add(v["simbolo"])
        if v["codigo"] == "eletronegatividade" and novo and abs(float(novo["valor"]) - v["valor"]) > 0.105:
            achadas["eletronegatividade"].add(v["simbolo"])
    assert achadas == DIVERGENCIAS_CONHECIDAS
