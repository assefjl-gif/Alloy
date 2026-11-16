"""Ligas multicomponentes sobre a supercélula periódica — casos R1 a R17 do parecer R1-CRI-01 §3.9.

Tolerâncias do parecer: contagens e conjuntos de índices EXATOS; composições e conversões abs = 1e-4
(pontos percentuais); geometria e fatores rel = 1e-9; densidade abs = 1e-4.

Regressões dos achados confirmados:
* L-1 (crítico): o sorteio era feito sobre as esferas DESENHADAS; imagens do mesmo átomo recebiam
  elementos diferentes e `n_soluto`/`n_solvente` contavam esferas. Agora o sorteio é sobre os Z·n³
  átomos ÚNICOS e as imagens herdam o elemento da origem (V-8, V-9).
* L-5 (crítico): intersticiais calculados sobre esferas desenhadas, com mínimo forçado de 1 e sorteio
  sobre sítios desenhados. Agora: N = ⌊N_rede·x/(1−x) + ½⌋, sem mínimo, sobre sítios únicos (V-10).
* L-2: só liga binária. Agora até 6 solutos, substitucionais e/ou intersticiais.
* L-3: um tipo de sítio por rede e nenhum campo por átomo. Agora octaédricos e tetraédricos (`sitios.py`)
  e os campos `id`, `imagem`, `ocupacao`, `sitio`, `fase`, `pos_nm`, `celula`, `frac_celula`.
* L-4: nenhum aviso de solubilidade/fases. Agora `verificacoes` e avisos obrigatórios.
* L-6: contagem do protótipo por esferas. Agora átomos únicos (25/50/75 at% exatos).
* L-11: `semente: 0` virava 1. Agora é respeitada (V-11).
* L-13: `x = 100` aceito em silêncio. Agora aceito com aviso explícito.
"""

from __future__ import annotations

import itertools
import json
import math
from typing import Any, Dict, List

import pytest

from app.engines.crystallography.estruturas import ESTRUTURAS, c_a_ideal
from app.engines.crystallography.geometria import frac_para_cart
from app.engines.crystallography.ligas import calcular_solucao_solida
from app.engines.crystallography.sitios import (
    distancias_vizinhos,
    fator_raio_livre,
    nc_texto,
    posicoes,
    sitios_por_celula,
)
from app.engines.procedencia import PoliticaDados
from app.repositories.materiais_json import repositorio_padrao

REPO = repositorio_padrao()
DEV = PoliticaDados(permitir_nao_validado=True)


def liga(**payload: Any) -> Dict[str, Any]:
    return calcular_solucao_solida(payload, REPO, REPO, DEV)


def _por_elemento(bloco: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {item["elemento"]: item for item in bloco}


def _indice_canonico(atomo: Dict[str, Any], n: int, z: int) -> int:
    i, j, k = atomo["celula"]
    b = int(atomo["id"].rsplit(":", 1)[1])
    return ((i * n + j) * n + k) * z + b


def _unicos(r: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [a for a in r["atomos"] if not a["imagem"]]


# --------------------------------------------------------------------------- R1 e R2
def test_r1_fe_cr_12_at_pct_n2():
    r = liga(base="Fe", soluto="Cr", x=12, n=2, semente=1)
    comp = r["composicao"]
    assert comp["n_sitios_rede"] == 16
    assert comp["n_atomos_unicos"] == 16 and comp["n_intersticiais"] == 0
    rep = _por_elemento(comp["representada"])
    assert (rep["Cr"]["n_atomos"], rep["Fe"]["n_atomos"]) == (2, 14)      # ⌊1,92 + ½⌋ = 2
    assert rep["Cr"]["at_pct"] == pytest.approx(12.5, abs=1e-4)
    assert rep["Cr"]["massa_pct"] == pytest.approx(11.7395, abs=1e-4)
    sol = _por_elemento(comp["solicitada"])
    assert sol["Cr"]["at_pct"] == pytest.approx(12.0, abs=1e-9)
    assert sol["Cr"]["massa_pct"] == pytest.approx(11.2660, abs=1e-4)
    assert comp["n_desenhados"] == 35 == len(r["atomos"])
    assert len(_unicos(r)) == 16
    assert comp["resolucao_at_pct"] == pytest.approx(100 / 16, rel=1e-12)
    assert comp["desvio_maximo_at_pct"] == pytest.approx(0.5, abs=1e-9)
    assert (r["n_soluto"], r["n_solvente"]) == (2, 14)


@pytest.mark.parametrize(("x", "indices"), [(12, [9, 13]), (25, [0, 8, 9, 13])])
def test_r2_indices_canonicos_da_semente_1(x, indices):
    # Vetores de teste do parecer §3.2/§3.9: algoritmo mt19937-chaves-v1, semente 1, N = 16.
    r = liga(base="Fe", soluto="Cr", x=x, n=2, semente=1)
    sorteados = sorted(_indice_canonico(a, 2, 2) for a in _unicos(r) if a["elemento"] == "Cr")
    assert sorteados == indices
    assert r["realizacao"]["algoritmo"] == "mt19937-chaves-v1"
    # aninhamento: aumentar x acrescenta solutos aos já sorteados
    assert set([9, 13]).issubset(set(sorteados))


def test_r2_sitios_do_cr_na_semente_1():
    r = liga(base="Fe", soluto="Cr", x=12, n=2, semente=1)
    fracoes = sorted(tuple(a["frac"]) for a in _unicos(r) if a["elemento"] == "Cr")
    assert fracoes == [(1.5, 0.5, 0.5), (1.5, 1.5, 0.5)]


def test_r3_fe_cr_12_at_pct_n3():
    r = liga(base="Fe", soluto="Cr", x=12, n=3)
    comp = r["composicao"]
    rep = _por_elemento(comp["representada"])
    assert comp["n_sitios_rede"] == 54
    assert rep["Cr"]["n_atomos"] == 6                     # alvo 6,48
    assert rep["Cr"]["at_pct"] == pytest.approx(11.1111, abs=1e-4)
    assert rep["Cr"]["massa_pct"] == pytest.approx(10.4250, abs=1e-4)


# --------------------------------------------------------------------------- R4 e R5 (intersticiais)
@pytest.mark.parametrize(("n", "n_rede", "n_c", "at_pct", "massa_pct"), [
    (2, 16, 1, 5.8824, 1.3263),
    (3, 54, 2, 3.5714, 0.7902),
    (4, 128, 5, 3.7594, 0.8331),
])
def test_r4_fe_c_4_at_pct(n, n_rede, n_c, at_pct, massa_pct):
    r = liga(base="Fe", soluto="C", x=4, n=n)
    comp = r["composicao"]
    rep = _por_elemento(comp["representada"])
    assert comp["n_sitios_rede"] == n_rede
    assert rep["Fe"]["n_atomos"] == n_rede
    assert rep["C"]["n_atomos"] == n_c == comp["n_intersticiais"]
    assert rep["C"]["at_pct"] == pytest.approx(at_pct, abs=1e-4)
    assert rep["C"]["massa_pct"] == pytest.approx(massa_pct, abs=1e-4)
    assert _por_elemento(comp["solicitada"])["C"]["massa_pct"] == pytest.approx(0.8881, abs=1e-4)
    assert comp["n_atomos_unicos"] == n_rede + n_c
    assert r["a_nm"] == pytest.approx(r["a_base_nm"], rel=1e-12)   # intersticial não dilata a rede


def test_r5_sem_minimo_forcado_de_um_intersticial():
    # Antes: min(len(sitios), max(1, ...)) punha 1 átomo de C (= 5,88 at% para 0,5 at% pedidos).
    r = liga(base="Fe", soluto="C", x=0.5, n=2)
    assert r["composicao"]["n_intersticiais"] == 0                 # alvo 0,080
    assert r["n_soluto"] == 0
    assert r["realizacao"]["tipo"] == "sem_soluto"
    assert any("abaixo da resolução" in a for a in r["procedencia"]["avisos"])


def test_intersticial_minusculo_nao_vira_um_atomo():
    r = liga(base="Fe", soluto="C", x=0.01, n=1)
    assert r["composicao"]["n_intersticiais"] == 0


# --------------------------------------------------------------------------- R6 a R9 (multicomponente)
def test_r6_fe_cr_c_multicomponente():
    r = liga(base="Fe", n=3, solutos=[{"elemento": "Cr", "x": 12},
                                      {"elemento": "C", "x": 2, "modo": "intersticial"}])
    comp = r["composicao"]
    rep = _por_elemento(comp["representada"])
    assert (rep["Fe"]["n_atomos"], rep["Cr"]["n_atomos"], rep["C"]["n_atomos"]) == (47, 7, 1)
    assert comp["n_atomos_unicos"] == 55
    assert [rep[s]["at_pct"] for s in ("Fe", "Cr", "C")] == pytest.approx(
        [85.4545, 12.7273, 1.8182], abs=1e-4)
    assert [rep[s]["massa_pct"] for s in ("Fe", "Cr", "C")] == pytest.approx(
        [87.4703, 12.1294, 0.4002], abs=1e-4)
    sol = _por_elemento(comp["solicitada"])
    assert [sol[s]["massa_pct"] for s in ("Fe", "Cr", "C")] == pytest.approx(
        [88.1121, 11.4472, 0.4407], abs=1e-4)
    assert r["a_nm"] == pytest.approx(0.286823, abs=1e-6)
    assert r["densidade"] == pytest.approx(7.8288, abs=1e-4)
    assert r["modelo"]["tipo_solucao"] == "mista"
    assert r["n_soluto"] == 8 and r["n_solvente"] == 47


def test_r7_entrada_em_massa():
    r = liga(base="Fe", base_composicao="massica", n=2,
             solutos=[{"elemento": "Cr", "x": 12}, {"elemento": "C", "x": 0.4, "modo": "intersticial"}])
    sol = _por_elemento(r["composicao"]["solicitada"])
    assert [sol[s]["at_pct"] for s in ("Fe", "Cr", "C")] == pytest.approx(
        [85.5900, 12.5927, 1.8173], abs=1e-4)
    assert [sol[s]["massa_pct"] for s in ("Fe", "Cr", "C")] == pytest.approx(
        [87.6, 12.0, 0.4], abs=1e-4)
    assert r["composicao"]["base_entrada"] == "massica"


def test_r8_maior_resto_e_desempate_pela_ordem_canonica():
    r = liga(base="Fe", n=2, solutos=[{"elemento": "Ni", "x": 10}, {"elemento": "Cr", "x": 10},
                                      {"elemento": "Mo", "x": 5}])
    rep = _por_elemento(r["composicao"]["representada"])
    # alvos 1,6 / 1,6 / 0,8; S = ⌊4,0 + ½⌋ = 4; Mo pelo maior resto; empate Cr × Ni pela ordem de símbolo
    assert [rep[s]["n_atomos"] for s in ("Fe", "Cr", "Mo", "Ni")] == [12, 2, 1, 1]
    assert [c["elemento"] for c in r["composicao"]["representada"]] == ["Fe", "Cr", "Mo", "Ni"]


def test_r9_ordem_do_pedido_nao_altera_a_resposta():
    def limpa(d: Dict[str, Any]) -> Dict[str, Any]:
        copia = json.loads(json.dumps(d))
        copia["procedencia"].pop("parametros_sha256")
        return copia

    a = liga(base="Fe", n=2, solutos=[{"elemento": "Cr", "x": 12}, {"elemento": "C", "x": 2}])
    b = liga(base="Fe", n=2, solutos=[{"elemento": "C", "x": 2}, {"elemento": "Cr", "x": 12}])
    assert limpa(a) == limpa(b)


def test_equivalencia_entre_a_forma_legada_e_solutos():
    def limpa(d: Dict[str, Any]) -> Dict[str, Any]:
        copia = json.loads(json.dumps(d))
        copia["procedencia"].pop("parametros_sha256")
        return copia

    legado = liga(base="Cu", soluto="Ni", x=30, n=2)
    novo = liga(base="Cu", n=2, solutos=[{"elemento": "Ni", "x": 30}])
    assert limpa(legado) == limpa(novo)


# --------------------------------------------------------------------------- R10 e R11 (ordenado)
@pytest.mark.parametrize(("x", "n_au", "strukturbericht"), [(25, 8, "L1₂"), (50, 16, "L1₀"), (75, 24, "L1₂")])
def test_r10_prototipos_contam_atomos_unicos(x, n_au, strukturbericht):
    r = liga(base="Cu", soluto="Au", x=x, arranjo="ordenado", n=2)
    assert r["n_soluto"] == n_au
    assert r["composicao"]["n_sitios_rede"] == 32
    assert _por_elemento(r["composicao"]["representada"])["Au"]["at_pct"] == pytest.approx(x, abs=1e-9)
    assert r["prototipo"]["strukturbericht"] == strukturbericht
    assert r["realizacao"]["tipo"] == "ordenada_prototipo"
    assert r["modelo"]["ordenacao"] == "ordenada_prototipo"
    assert "hipotético" in r["nota_arranjo"]


def test_r11_estequiometria_do_prototipo_difere_da_solicitada_com_aviso():
    r = liga(base="Fe", soluto="Cr", x=48.5, arranjo="ordenado", n=2)
    assert r["fase_ordenada"].startswith("B2")
    assert r["n_soluto"] == 8
    assert _por_elemento(r["composicao"]["representada"])["Cr"]["at_pct"] == pytest.approx(50.0, abs=1e-9)
    assert r["x_pct"] == pytest.approx(48.5)
    assert any("estequiometria ideal do protótipo" in a for a in r["procedencia"]["avisos"])


def test_mais_de_um_substitucional_nao_tem_prototipo():
    r = liga(base="Cu", n=2, arranjo="ordenado",
             solutos=[{"elemento": "Au", "x": 12.5}, {"elemento": "Ni", "x": 12.5}])
    assert r["fase_ordenada"] is None and r["prototipo"] is None
    assert "Mais de um soluto substitucional" in r["nota_arranjo"]
    assert r["modelo"]["ordenacao"] == "desordenada"


# --------------------------------------------------------------------------- R12 (sítios intersticiais)
def _camadas_do_sitio(estrutura: str, frac_sitio, c_a, n: int = 3):
    """Distâncias do sítio aos átomos da rede, por contagem periódica independente."""
    base = [f for f, _t in ESTRUTURAS[estrutura]["base"]]
    centro = [v + 1 for v in frac_sitio]
    alvo = frac_para_cart(estrutura, centro, c_a)
    distancias = []
    for i, j, k in itertools.product(range(n), repeat=3):
        for b in base:
            p = frac_para_cart(estrutura, (i + b[0], j + b[1], k + b[2]), c_a)
            distancias.append(math.dist(p, alvo))
    camadas: List[List[float]] = []
    for d in sorted(distancias):
        if camadas and abs(camadas[-1][0] - d) < 1e-9:
            camadas[-1].append(d)
        else:
            camadas.append([d])
    return [(c[0], len(c)) for c in camadas[:3]]


@pytest.mark.parametrize(("estrutura", "tipo", "por_celula", "fator", "nc_esperado"), [
    ("CS", "cubico", 1, math.sqrt(3) - 1, "8"),
    ("CCC", "octaedrico", 6, 2 / math.sqrt(3) - 1, "2 + 4"),
    ("CCC", "tetraedrico", 12, math.sqrt(5 / 3) - 1, "4"),
    ("CFC", "octaedrico", 4, math.sqrt(2) - 1, "6"),
    ("CFC", "tetraedrico", 8, math.sqrt(1.5) - 1, "4"),
    ("HC", "octaedrico", 2, math.sqrt(2) - 1, "6"),
    ("HC", "tetraedrico", 4, math.sqrt(1.5) - 1, "4"),
])
def test_r12_sitios_por_estrutura(estrutura, tipo, por_celula, fator, nc_esperado):
    c_a = c_a_ideal() if estrutura == "HC" else None
    assert sitios_por_celula(estrutura, tipo) == por_celula
    assert fator_raio_livre(estrutura, tipo, c_a) == pytest.approx(fator, rel=1e-9)
    nc, nc_txt = nc_texto(estrutura, tipo, c_a)
    assert nc_txt == nc_esperado
    # conferência independente: contagem periódica dos vizinhos do sítio na rede ideal
    camadas = _camadas_do_sitio(estrutura, posicoes(estrutura, tipo)[0], c_a)
    tabela = distancias_vizinhos(estrutura, tipo, c_a)
    assert [q for _d, q in camadas[:len(tabela)]] == [q for _d, q in tabela]
    assert [d for d, _q in camadas[:len(tabela)]] == pytest.approx([d for d, _q in tabela], rel=1e-9)
    assert sum(q for _d, q in tabela) == nc
    # r_livre = d_min − R, com R = metade da menor distância entre átomos
    d1 = {"CS": 1.0, "CCC": math.sqrt(3) / 2, "CFC": 1 / math.sqrt(2), "HC": 1.0}[estrutura]
    assert fator_raio_livre(estrutura, tipo, c_a) == pytest.approx(
        (min(d for d, _q in tabela) - d1 / 2) / (d1 / 2), rel=1e-9)


@pytest.mark.parametrize(("simbolo", "oct_fator", "tet_fator"), [
    ("Mg", 0.4116, 0.2180), ("Ti", 0.4011, 0.1904), ("Co", 0.4113, 0.2172), ("Zn", 0.4814, 0.2444),
])
def test_raio_livre_do_hc_usa_o_c_a_real(simbolo, oct_fator, tet_fator):
    # L-10: o motor usava sempre o fator do c/a ideal (0,4142) em qualquer HC.
    c_a = REPO.obter(simbolo).c_a_efetivo
    assert fator_raio_livre("HC", "octaedrico", c_a) == pytest.approx(oct_fator, abs=1e-4)
    assert fator_raio_livre("HC", "tetraedrico", c_a) == pytest.approx(tet_fator, abs=1e-4)


def test_sitio_tetraedrico_escolhido_no_pedido():
    r = liga(base="Fe", n=2, solutos=[{"elemento": "C", "x": 4, "modo": "intersticial",
                                       "sitio": "tetraedrico"}])
    sitio = r["sitios"][0]
    assert (sitio["tipo"], sitio["escolha"], sitio["sitios_por_celula"]) == ("tetraedrico", "informado", 12)
    assert sitio["fator"] == pytest.approx(math.sqrt(5 / 3) - 1, rel=1e-9)
    assert sitio["raio_nm"] == pytest.approx(sitio["fator"] * 0.1241, rel=1e-12)
    assert sitio["wyckoff"] is None and sitio["padrao_verificado"] is False
    assert r["sitio"] == sitio                                   # campo legado = primeiro sítio


def test_sitio_padrao_e_octaedrico_com_justificativa_de_nao_ser_o_maior_na_ccc():
    r = liga(base="Fe", soluto="C", x=2, n=2)
    sitio = r["sitios"][0]
    assert (sitio["tipo"], sitio["escolha"]) == ("octaedrico", "padrao")
    assert "MENOR" in sitio["justificativa"] and "martensita" in sitio["justificativa"]
    assert sitio["nc"] == 6 and sitio["nc_txt"] == "2 + 4"


# --------------------------------------------------------------------------- R13 (periodicidade)
@pytest.mark.parametrize(("base", "n"), [("Fe", 2), ("Fe", 3), ("Cu", 2)])
def test_r13_periodicidade_dos_intersticiais(base, n):
    ocupados_por_id = set()
    for semente in range(40):
        r = liga(base=base, soluto="C", x=8, n=n, semente=semente)
        unicos = {a["id"] for a in _unicos(r)}
        intersticiais = [a for a in r["atomos"] if a["tipo"] == "intersticial"]
        origens = {a["id"] for a in intersticiais if not a["imagem"]}
        # nenhum sítio único ocupado mais de uma vez
        assert len(origens) == len([a for a in intersticiais if not a["imagem"]])
        assert len(origens) == r["composicao"]["n_intersticiais"]
        # toda imagem aponta para um único existente, com o mesmo elemento e sítio
        for imagem in (a for a in r["atomos"] if a["imagem"]):
            assert imagem["imagem_de"] in unicos
        ocupados_por_id |= origens
    assert ocupados_por_id


@pytest.mark.parametrize(("base", "n"), [("Fe", 2), ("Cu", 3), ("Mg", 2), ("Po", 2)])
def test_imagens_tem_sempre_o_elemento_da_origem(base, n):
    # L-1: antes, cópias do mesmo átomo único recebiam elementos diferentes em 200/200 sementes.
    for semente in range(25):
        r = liga(base=base, soluto="Ni" if base != "Cu" else "Au", x=20, n=n, semente=semente)
        por_id = {a["id"]: a for a in _unicos(r)}
        imagens = [a for a in r["atomos"] if a["imagem"]]
        assert imagens
        for imagem in imagens:
            origem = por_id[imagem["imagem_de"]]
            assert imagem["elemento"] == origem["elemento"]
            assert imagem["ocupacao"] == origem["ocupacao"]
            assert imagem["tipo"] == origem["tipo"]
            assert imagem["sitio"] == origem["sitio"]
            assert imagem["fase"] == origem["fase"]
        # composição representada = composição dos átomos ÚNICOS
        contagem = {}
        for a in _unicos(r):
            contagem[a["elemento"]] = contagem.get(a["elemento"], 0) + 1
        for item in r["composicao"]["representada"]:
            assert item["n_atomos"] == contagem.get(item["elemento"], 0)


@pytest.mark.parametrize("estrutura_e_n", [("Fe", 1), ("Fe", 2), ("Fe", 3), ("Fe", 4),
                                           ("Cu", 2), ("Mg", 3), ("Po", 4)])
def test_contagem_de_unicos_e_desenhados(estrutura_e_n):
    simbolo, n = estrutura_e_n
    r = liga(base=simbolo, soluto="Ni" if simbolo != "Ni" else "Cu", x=10, n=n)
    z = len(ESTRUTURAS[r["estrutura"]]["base"])
    comp = r["composicao"]
    assert comp["n_sitios_rede"] == z * n ** 3
    assert len(_unicos(r)) == comp["n_atomos_unicos"]
    assert len(r["atomos"]) == comp["n_desenhados"]
    assert r["n_soluto"] + r["n_solvente"] == comp["n_sitios_rede"] + comp["n_intersticiais"] - \
        comp["n_intersticiais"] + sum(1 for a in _unicos(r) if a["tipo"] == "intersticial")


def test_ids_sao_estaveis_entre_sementes_e_composicoes():
    base = [a["id"] for a in _unicos(liga(base="Fe", soluto="Cr", x=12, n=2, semente=1))]
    outra = [a["id"] for a in _unicos(liga(base="Fe", soluto="Cr", x=30, n=2, semente=5))]
    assert base == outra
    assert base[0] == "r:0.0.0:0"


# --------------------------------------------------------------------------- R15 (semente) e R14
def test_r15_semente_zero_e_respeitada():
    # L-11: ``int(payload.get("semente") or 1)`` trocava 0 por 1 em silêncio.
    zero = liga(base="Fe", soluto="Cr", x=12, n=2, semente=0)
    um = liga(base="Fe", soluto="Cr", x=12, n=2, semente=1)
    assert zero["semente"] == 0 and zero["realizacao"]["semente"] == 0
    assert sorted(_indice_canonico(a, 2, 2) for a in _unicos(zero) if a["elemento"] == "Cr") == [3, 15]
    assert [a["elemento"] for a in zero["atomos"]] != [a["elemento"] for a in um["atomos"]]


def test_r14_fica_pendente_parametro_de_rede_medido_do_solvente():
    """V-14 está FORA do contrato R1 (decisão 7.6): a liga continua usando a = k·R̄.

    O caso R14 do parecer (Ti com a = 0,2951 nm e ρ = 4,5005) NÃO foi implementado; a resposta avisa
    que existe rede medida e que usá-la depende de aprovação.
    """
    r = liga(base="Ti", soluto="Cr", x=0, n=2)
    assert r["a_base_nm"] == pytest.approx(0.2890, abs=1e-4)
    assert r["modelo"]["parametro_rede_solvente"] == "derivado_de_R"
    assert any("pendência V-14" in a for a in r["procedencia"]["avisos"])


# --------------------------------------------------------------------------- R17 (erros de domínio)
@pytest.mark.parametrize(("payload", "subtipo"), [
    ({"base": "Fe", "solutos": [{"elemento": "Cr", "x": 2}, {"elemento": "cromo", "x": 3}]},
     "soluto_repetido"),
    ({"base": "Fe", "solutos": [{"elemento": "Fe", "x": 2}]}, "soluto_igual_ao_solvente"),
    ({"base": "Fe", "solutos": [{"elemento": "Cr", "x": 60}, {"elemento": "Ni", "x": 50}]},
     "soma_solutos_invalida"),
    ({"base": "Fe", "solutos": [{"elemento": "C", "x": 25, "modo": "intersticial"}]},
     "intersticial_acima_do_limite"),
    ({"base": "Fe", "solutos": [{"elemento": "Ni", "x": 5, "modo": "intersticial"}]}, "modo_sem_dados"),
    ({"base": "Fe", "solutos": [{"elemento": "C", "x": 5, "modo": "substitucional"}]}, "modo_sem_dados"),
    ({"base": "Fe", "solutos": [{"elemento": "C", "x": 5, "sitio": "cubico"}]}, "sitio_incompativel"),
    ({"base": "Fe", "solutos": [{"elemento": "Cr", "x": 5, "sitio": "octaedrico"}]}, "sitio_incompativel"),
    ({"base": "Fe", "soluto": "Cr", "x": 12, "solutos": [{"elemento": "Ni", "x": 2}]}, "soluto_ou_solutos"),
    ({"base": "Fe"}, "soluto_ou_solutos"),
    ({"base": "Fe", "x": 5, "solutos": [{"elemento": "Ni", "x": 2}]}, "x_com_solutos"),
    ({"base": "Fe", "solutos": [{"elemento": "Ni"}]}, "missing"),
    ({"base": "Fe", "solutos": []}, "too_short"),
    ({"base": "Fe", "solutos": [{"elemento": "Ni", "x": 1}] * 7}, "too_long"),
    ({"base": "Fe", "solutos": [{"elemento": "Ni", "x": 1, "modo": "voador"}]}, "literal_error"),
    ({"base": "Fe", "soluto": "Ni", "base_composicao": "molar"}, "literal_error"),
    ({"base": "Fe", "soluto": "Ni", "estrutura_matriz": "cubica"}, "literal_error"),
])
def test_r17_erros_de_dominio_com_subtipo(payload, subtipo):
    from app.engines.crystallography.erros import ErroDominio
    with pytest.raises(ErroDominio) as excecao:
        calcular_solucao_solida(payload, REPO, REPO, DEV)
    detalhes = getattr(excecao.value, "detalhes", None)
    assert detalhes and detalhes[0]["type"] == subtipo


def test_soluto_desconhecido_continua_material_desconhecido():
    from app.engines.crystallography.erros import MaterialDesconhecido
    with pytest.raises(MaterialDesconhecido) as excecao:
        calcular_solucao_solida({"base": "Fe", "solutos": [{"elemento": "Xx", "x": 2}]}, REPO, REPO, DEV)
    assert excecao.value.detalhes[0]["loc"] == ["solutos", "0", "elemento"]


def test_l13_x_100_continua_aceito_com_aviso():
    r = liga(base="Cu", soluto="Ni", x=100, n=2)
    assert r["n_solvente"] == 0
    assert any("sem solvente" in a for a in r["procedencia"]["avisos"])


# --------------------------------------------------------------------------- blocos de natureza
def test_blocos_de_modelo_fases_e_verificacoes():
    r = liga(base="Fe", soluto="C", x=2, n=2)
    assert r["modelo"]["fases"] == "monofasica_imposta"
    assert r["modelo"]["geometria"] == "idealizada"
    assert "intersticiais não dilatam a rede" in r["modelo"]["hipoteses"]
    assert r["fases"] == [{"id": "matriz", "nome": "solução sólida na estrutura do solvente",
                           "estrutura": "CCC", "origem": "imposta_pelo_modelo",
                           "composicao": r["composicao"]["representada"],
                           "fracao": None,
                           "fracao_motivo": "o motor não calcula equilíbrio de fases"}]
    assert r["verificacoes"]["limite_solubilidade"] == {
        "verificado": False, "valor": None, "motivo": "não há dados de diagrama de fases no repositório"}
    assert r["verificacoes"]["fases_secundarias"]["previstas"] is None
    avisos = r["procedencia"]["avisos"]
    assert any("Modelo de fase única" in a for a in avisos)
    assert any("carbonetos ou nitretos" in a for a in avisos)
    assert any("superestimar a densidade" in a for a in avisos)


def test_conclusao_global_nula_com_mais_de_um_soluto():
    r = liga(base="Fe", n=2, solutos=[{"elemento": "Cr", "x": 12}, {"elemento": "Ni", "x": 8}])
    assert r["conclusao_global"] is None
    assert r["indisponiveis"]["conclusao_global"]
    assert [b["soluto"] for b in r["regras_por_soluto"]] == ["Cr", "Ni"]
    assert r["conclusao"] == r["regras_por_soluto"][0]["conclusao"]
    assert r["soluto"] == "Cr" and r["intersticial"] is False


def test_conclusao_global_igual_a_conclusao_com_um_soluto():
    r = liga(base="Cu", soluto="Ni", x=30, n=2)
    assert r["conclusao_global"] == r["conclusao"]
    assert "não é previsto por este motor" in r["conclusao"]
    assert "possivelmente completa" not in r["conclusao"]        # V-12: redação de critério


def test_elementos_puros_tem_estado_do_dado_e_fonte():
    r = liga(base="Fe", n=2, solutos=[{"elemento": "Cr", "x": 12}, {"elemento": "C", "x": 1}])
    por_simbolo = {e["simbolo"]: e for e in r["elementos"]}
    assert por_simbolo["Fe"]["papel"] == "solvente"
    assert por_simbolo["Fe"]["estrutura_elemento_puro"] == "CCC"
    assert por_simbolo["Fe"]["fonte"]
    assert por_simbolo["C"]["estado_do_dado"] == "rascunho"
    assert por_simbolo["C"]["estrutura_elemento_puro"] is None
    assert r["indisponiveis"]["elementos.C.estrutura_elemento_puro"]
    assert r["indisponiveis"]["elementos.C.fonte"]


def test_campos_por_atomo():
    r = liga(base="Mg", soluto="Al", x=10, n=2, semente=3)
    for atomo in r["atomos"]:
        assert set(atomo) >= {"id", "imagem", "imagem_de", "pos", "pos_nm", "frac", "celula",
                              "frac_celula", "tipo", "ocupacao", "elemento", "raio_rel", "sitio",
                              "fase", "pos_ideal"}
        assert atomo["pos_nm"] == pytest.approx([v * r["a_nm"] for v in atomo["pos"]], rel=1e-12)
        assert atomo["frac"] == pytest.approx([c + f for c, f in zip(atomo["celula"],
                                                                     atomo["frac_celula"])], abs=1e-12)
        assert atomo["sitio"]["wyckoff"] is None
        assert atomo["fase"] == "matriz"
        assert atomo["pos_ideal"] is None
    assert r["c_a"] == pytest.approx(1.624)
    assert r["modelo"]["c_a"] == "tabelado"
    assert {a["sitio"]["nc_txt"] for a in r["atomos"] if a["tipo"] == "rede"} == {"6 + 6"}


def test_distorcao_usa_atomos_unicos_e_devolve_posicao_ideal():
    # L-12: antes, cópias do mesmo átomo recebiam deslocamentos diferentes.
    r = liga(base="Cu", soluto="Ag", x=10, distorcer=True, n=2, semente=2)
    assert r["distorcao"]["classe"] == "simulacao_ilustrativa"
    por_id = {a["id"]: a for a in _unicos(r)}
    deslocados = [a for a in _unicos(r) if a["pos_ideal"] is not None]
    assert deslocados
    for imagem in (a for a in r["atomos"] if a["imagem"]):
        origem = por_id[imagem["imagem_de"]]
        deslocamento_origem = (None if origem["pos_ideal"] is None else
                               [p - i for p, i in zip(origem["pos"], origem["pos_ideal"])])
        if deslocamento_origem is None:
            assert imagem["pos_ideal"] is None
        else:
            assert [p - i for p, i in zip(imagem["pos"], imagem["pos_ideal"])] == pytest.approx(
                deslocamento_origem, abs=1e-12)


def test_convencoes_e_realizacao():
    r = liga(base="Fe", soluto="Cr", x=12, n=2)
    assert any("imagem" in c for c in r["convencoes"])
    assert any("raio de DESENHO" in c for c in r["convencoes"])
    assert r["realizacao"]["aviso"].startswith("Uma realização estatística")
    assert r["realizacao"]["n"] == 2


def test_estrutura_matriz_imposta_gera_aviso():
    r = liga(base="Fe", soluto="Ni", x=10, n=2, estrutura_matriz="CFC")
    assert r["estrutura"] == "CFC"
    assert r["composicao"]["n_sitios_rede"] == 32
    assert any("foi imposta à matriz" in a for a in r["procedencia"]["avisos"])
