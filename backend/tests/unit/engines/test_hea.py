"""Motor HEA 2.0.0 (rodada R1): casos analíticos e de regressão T-01 a T-21 da auditoria R1-HEA-01 (seção 2.9.1).

Os testes "com matriz" usam uma matriz de entalpias SINTÉTICA, FICTÍCIA, criada só aqui para conferir a álgebra.
Nenhum valor dela é dado de material e nenhum existe em ``database/seeds``. O mesmo vale para os repositórios
sintéticos de raio, massa e temperatura de fusão (``RepoFicticio``).
"""

from __future__ import annotations

import itertools
import json
import math
import re

import pytest

from app.engines.crystallography import EntradaInvalida
from app.engines.crystallography.erros import ErroDeDados
from app.engines.crystallography.referencia import Metal
from app.engines.hea.analitico import R_GASES, VERSAO_MOTOR, analisar_liga, catalogo, entropia_mistura
from app.engines.hea.erros import EntradaHeaInvalida, MassaNaoValidada
from app.engines.procedencia import DadoNaoValidado, PoliticaDados, ValorReferencia
from app.repositories.entalpias_json import (
    CAMINHO_ENTALPIAS,
    RepositorioEntalpiasMemoria,
    carregar_entalpias,
    entalpias_padrao,
)
from app.repositories.identidade_elementos import identidades_padrao
from app.repositories.materiais_json import repositorio_padrao

REPO = repositorio_padrao()
IDENT = identidades_padrao()
DEV = PoliticaDados(permitir_nao_validado=True)
PROD = PoliticaDados(permitir_nao_validado=False)
CANTOR = ("Co", "Cr", "Fe", "Mn", "Ni")
SIGLAS = re.compile(r"\b(CFC|FCC|CCC|BCC|HC|HCP|HEX|CS|SC)\b", re.IGNORECASE)   # as que o front procura em `fase`


def _analisar(composicao, politica=DEV, *, base=None, entalpias=None, repo=REPO, props=None):
    payload = {"nome": "t", "composicao": composicao}
    if base is not None:
        payload["base"] = base
    return analisar_liga(payload, repo, props if props is not None else repo, politica,
                         identidades=IDENT, entalpias=entalpias)


def _equi(*simbolos):
    return dict.fromkeys(simbolos, 1)


class RepoFicticio:
    """Repositório SINTÉTICO de teste: raio, massa e T_f FICTÍCIOS, só para conferir a álgebra."""

    versao_dados = "ficticio-de-teste"

    def __init__(self, raios=None, massas=None, t_fusao_c=None):
        self._raios, self._massas, self._tf = raios or {}, massas or {}, t_fusao_c or {}

    def obter(self, simbolo):
        if simbolo not in self._raios and simbolo not in self._massas:
            return None
        return Metal(simbolo=simbolo, nome=simbolo, estrutura="CFC", raio_nm=self._raios.get(simbolo, 1.0),
                     peso_g_mol=self._massas.get(simbolo, 1.0), fonte="ficticio-de-teste")

    def listar(self):
        return tuple(self.obter(s) for s in sorted(set(self._raios) | set(self._massas)))

    def propriedade(self, simbolo, codigo):
        if codigo == "temperatura_fusao" and simbolo in self._tf:
            return ValorReferencia(simbolo, codigo, self._tf[simbolo], "°C", "rascunho", None)
        return None


def _matriz_ficticia(pares, estado="aguardando_validacao"):
    """Matriz SINTÉTICA de teste (valores FICTÍCIOS, sem significado físico). Nunca vai para ``database/seeds``."""
    return RepositorioEntalpiasMemoria({
        "versao_dados": "ficticia-de-teste", "unidade": "kJ/mol",
        "fontes": {"ficticia": {"citacao": "valores fictícios de teste; não são dados de material"}},
        "pares": [{"a": min(a, b), "b": max(a, b), "valor": h, "unidade": "kJ/mol", "estado": estado,
                   "fonte": "ficticia", "origem": "teste"} for (a, b), h in pares.items()],
    }, simbolos=set(IDENT))


def _todos_os_pares(simbolos, h):
    return {par: h for par in itertools.combinations(sorted(simbolos), 2)}


#: T_f fictícia que dá T_m = 1500 K exatos pela regra das misturas (1500 − 273,15 °C).
TM_1500 = RepoFicticio(raios={"Fe": 1.0, "Ni": 1.0}, t_fusao_c={"Fe": 1226.85, "Ni": 1226.85})


# ------------------------------------------------------------------ T-01, T-02: ΔS_mix
@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_entropia_equimolar_e_r_ln_n(n):
    assert entropia_mistura([(str(i), 1.0 / n) for i in range(n)]) == pytest.approx(R_GASES * math.log(n))


@pytest.mark.parametrize(("simbolos", "esperado"), [
    (("Fe", "Ni"), 5.763146), (("Cr", "Mo", "W"), 9.134371), (("Co", "Cr", "Fe", "Ni"), 11.526293),
    (("Al", "Co", "Cr", "Fe", "Ni"), 13.381611), (("Al", "Co", "Cr", "Cu", "Fe", "Ni"), 14.897517)])
def test_t01_ds_da_liga_equimolar(simbolos, esperado):
    r = _analisar(_equi(*simbolos))
    assert r["dS"] == pytest.approx(esperado, abs=5e-5)
    assert r["dS_R"] == pytest.approx(math.log(len(simbolos)), abs=5e-5)
    assert r["classe_entropia"] == ("alta" if len(simbolos) >= 5 else "media" if len(simbolos) >= 3 else "baixa")


def test_t02_invariancia_de_escala():
    resultados = [_analisar(c) for c in ({"Fe": 1, "Ni": 1}, {"Fe": 50, "Ni": 50}, {"Fe": 0.5, "Ni": 0.5})]
    assert [r["soma_informada"] for r in resultados] == [2.0, 100.0, 1.0]
    for r in resultados:
        r.pop("soma_informada")
        r["procedencia"].pop("parametros_sha256")   # o hash é do pedido como foi enviado
    assert resultados[0] == resultados[1] == resultados[2]


# ------------------------------------------------------------------ T-03 a T-05: δ, VEC, T_m
def test_t03_delta_com_raios_sinteticos():
    repo = RepoFicticio(raios={"Fe": 1.0, "Ni": 1.1})
    r = _analisar({"Fe": 1, "Ni": 1}, repo=repo)
    assert r["delta"] == pytest.approx(100 * 0.1 / 2.1, abs=5e-5)    # a saída tem 4 casas
    assert r["raio_medio_nm"] == pytest.approx(1.05)
    assert _analisar({"Fe": 1, "Ni": 1}, repo=RepoFicticio(raios={"Fe": 1.0, "Ni": 1.0}))["delta"] == 0.0


@pytest.mark.parametrize(("composicao", "delta", "vec", "tm", "ds"), [
    (_equi("Al", "Co", "Cr", "Fe", "Ni"), 5.7324, 7.2, 1674.2, 13.3816),          # T-04
    (_equi("Co", "Cr", "Fe", "Ni"), 0.3512, 8.25, 1859.4, 11.5263),               # T-05
    (_equi("Cr", "Mo", "W"), 4.1970, 6.0, 2907.2, 9.1344),
    ({"Al": 0.5, "Co": 1, "Cr": 1, "Cu": 1, "Fe": 1, "Ni": 1}, 4.1368, 8.2727, 1684.1, 14.698),
    (_equi("Co", "Cr", "Cu", "Fe", "Ni"), 1.0299, 8.8, 1759.2, 13.3816),
    (_equi("Fe", "Ni"), 0.201, 9.0, 1769.7, 5.7631),
    (_equi("Ag", "Au", "Cu", "Zn"), 5.2277, 11.25, 1155.9, 11.5263),
    (_equi("Mg", "Ti", "Zn"), 7.5296, 6.0, 1185.8, 9.1344),
    ({"Fe": 99.9, "Ni": 0.1}, 0.0127, 8.002, 1811.1, 0.0657),
    ({"Ti": 3, "W": 1, "Mo": 2.5, "Cu": 0.7}, 3.7954, 5.6528, 2459.7, 10.2505)])
def test_t04_t05_regressao_valores_existentes_inalterados(composicao, delta, vec, tm, ds):
    """Regressão sobre os seeds atuais (NÃO são valores de literatura): o motor 2.0.0 não muda ΔS, δ, VEC nem T_m.

    Valores esperados: saída do motor 1.0.0 (versão do último commit), executado em 12/11/2026 com os mesmos seeds.
    """
    r = _analisar(composicao)
    assert r["delta"] == pytest.approx(delta, abs=1e-4)
    assert r["VEC"] == pytest.approx(vec, abs=1e-4)
    assert r["Tm"] == pytest.approx(tm, abs=0.1)
    assert r["dS"] == pytest.approx(ds, abs=1e-4)


def test_alcocrfeni_conferido_a_mao():
    r = _analisar(_equi("Al", "Co", "Cr", "Fe", "Ni"))
    raios = {"Al": 0.1431, "Co": 0.1253, "Cr": 0.1249, "Fe": 0.1241, "Ni": 0.1246}
    r_medio = sum(raios.values()) / 5
    delta = 100 * math.sqrt(sum(0.2 * (1 - ri / r_medio) ** 2 for ri in raios.values()))
    assert r["delta"] == pytest.approx(delta, abs=1e-4) and r["raio_medio_nm"] == pytest.approx(r_medio)
    assert r["VEC"] == pytest.approx((3 + 9 + 6 + 8 + 10) / 5)
    assert r["Tm"] == pytest.approx((660 + 1495 + 1857 + 1538 + 1455) / 5 + 273.15, abs=0.1)
    assert r["fase"].startswith("CFC + CCC") and r["estrutura_sugerida"] is None
    assert "estrutura_sugerida" in r["indisponiveis"]


def test_normaliza_quantidades_e_ordena():
    r = _analisar({"Ni": 50, "Cu": 50})
    assert r["fracoes"] == {"Cu": 0.5, "Ni": 0.5} and r["comp_percent"] == {"Cu": 50.0, "Ni": 50.0}
    assert any("Menos de 5 elementos" in a for a in r["procedencia"]["avisos"])
    assert r["base_entrada"] == "atomica" and r["procedencia"]["versao_motor"] == VERSAO_MOTOR == "2.0.0"


# ------------------------------------------------------------------ T-06 a T-08: base mássica
def test_t06_conversao_com_massas_sinteticas():
    repo = RepoFicticio(massas={"Fe": 10.0, "Ni": 30.0})
    r = _analisar({"Fe": 1, "Ni": 1}, repo=repo)
    assert r["fracoes_massa"] == pytest.approx({"Fe": 0.25, "Ni": 0.75}, abs=1e-12)
    assert r["comp_massa_pct"] == {"Fe": 25.0, "Ni": 75.0} and r["massa_molar_media"] == pytest.approx(20.0)
    volta = _analisar({"Fe": 25, "Ni": 75}, repo=repo, base="massica")
    assert volta["base_entrada"] == "massica" and volta["soma_informada"] == 100.0
    assert volta["fracoes"] == pytest.approx({"Fe": 0.5, "Ni": 0.5}, abs=1e-12)


@pytest.mark.parametrize("composicao", [_equi("Co", "Cr", "Fe", "Ni"), _equi("Al", "Co", "Cr", "Fe", "Ni"),
                                        {"Al": 0.5, "Co": 1, "Cr": 1, "Cu": 1, "Fe": 1, "Ni": 1},
                                        {"Cr": 3, "Mo": 1, "W": 2}])
def test_t08_ida_e_volta_atomica_massica(composicao):
    """Massas do repositório de materiais (as que o motor já lê). wᵢ = xᵢMᵢ/Σ xⱼMⱼ conferido à parte."""
    ida = _analisar(composicao)
    massas = {s: REPO.obter(s).peso_g_mol for s in composicao}
    m_media = sum(ida["fracoes"][s] * massas[s] for s in composicao)
    assert ida["massa_molar_media"] == pytest.approx(m_media, abs=1e-4)
    for s in composicao:
        assert ida["fracoes_massa"][s] == pytest.approx(ida["fracoes"][s] * massas[s] / m_media, abs=1e-12)
    assert sum(ida["fracoes"].values()) == pytest.approx(1.0, abs=1e-12)
    assert sum(ida["fracoes_massa"].values()) == pytest.approx(1.0, abs=1e-12)
    assert sum(ida["comp_percent"].values()) == pytest.approx(100.0, abs=1e-4 * len(composicao))
    assert sum(ida["comp_massa_pct"].values()) == pytest.approx(100.0, abs=1e-4 * len(composicao))
    volta = _analisar(ida["fracoes_massa"], base="massica")
    for s in composicao:
        assert volta["fracoes"][s] == pytest.approx(ida["fracoes"][s], abs=1e-12)
        assert volta["fracoes_massa"][s] == pytest.approx(ida["fracoes_massa"][s], abs=1e-12)
    for campo in ("dS", "delta", "VEC", "Tm"):
        assert volta[campo] == pytest.approx(ida[campo], rel=1e-9), campo
    usados = {(u["simbolo"], u["codigo"]): u for u in ida["procedencia"]["dados_usados"]}
    primeiro = sorted(composicao)[0]
    assert usados[(primeiro, "massa_atomica")]["unidade"] == "g/mol"
    assert usados[(primeiro, "massa_atomica")]["valor"] == massas[primeiro]


def test_base_massica_sem_massa_e_erro_e_base_atomica_e_parcial():
    with pytest.raises(EntradaHeaInvalida) as erro:   # Mn não tem massa no repositório de materiais
        _analisar(_equi(*CANTOR), base="massica")
    assert erro.value.codigo == "ENTRADA_INVALIDA"
    assert [(d["loc"], d["type"]) for d in erro.value.detalhes] == [(["composicao", "Mn"], "massa_indisponivel")]
    r = _analisar(_equi(*CANTOR))
    assert r["comp_massa_pct"] is None and r["fracoes_massa"] is None and r["massa_molar_media"] is None
    assert "Mn" in r["indisponiveis"]["comp_massa_pct"]
    assert {"simbolo": "Mn", "codigo": "massa_atomica", "situacao": "ausente"} in r["dados_faltantes"]


def test_base_invalida():
    with pytest.raises(EntradaHeaInvalida) as erro:
        _analisar({"Fe": 1, "Ni": 1}, base="massa")
    assert erro.value.detalhes[0]["type"] == "base_invalida"


# ------------------------------------------------------------------ T-09 a T-13: ΔH_mix, Ω, ΔG (matriz FICTÍCIA)
def test_t09_dh_mix_com_matriz_ficticia():
    binaria = _analisar({"Fe": 1, "Ni": 1}, entalpias=_matriz_ficticia({("Fe", "Ni"): -10.0}))
    assert binaria["dH"] == pytest.approx(-10.0, abs=1e-9) and binaria["pares_faltantes"] == []
    cinco = ("Al", "Co", "Cr", "Fe", "Ni")
    r = _analisar(_equi(*cinco), entalpias=_matriz_ficticia(_todos_os_pares(cinco, -10.0)))
    assert r["dH"] == pytest.approx(2 * -10.0 * 4 / 5, abs=1e-9)                     # 2h(n−1)/n = −16
    tres = _analisar({"Co": 5, "Cr": 3, "Fe": 2}, entalpias=_matriz_ficticia(
        {("Co", "Cr"): -10.0, ("Co", "Fe"): 5.0, ("Cr", "Fe"): 0.0}))
    assert tres["dH"] == pytest.approx(-4.0, abs=1e-9)
    usados = {(u["simbolo"], u["codigo"]): u for u in tres["procedencia"]["dados_usados"]}
    assert usados[("Co-Cr", "entalpia_mistura_par")]["unidade"] == "kJ/mol"
    assert usados[("Co-Cr", "entalpia_mistura_par")]["fonte"] == "ficticia"
    assert tres["procedencia"]["versao_dados"].endswith("+ficticia-de-teste")
    assert "dH" not in tres["indisponiveis"]


@pytest.mark.parametrize("h", [-10.0, 10.0])
def test_t10_omega_sintetico(h):
    r = _analisar({"Fe": 1, "Ni": 1}, repo=TM_1500, entalpias=_matriz_ficticia({("Fe", "Ni"): h}))
    assert r["Tm"] == pytest.approx(1500.0) and r["dH"] == pytest.approx(h)
    assert r["omega"] == pytest.approx(0.864472, abs=5e-5)    # a saída tem 4 casas


def test_t11_dh_zero_omega_indefinido():
    r = _analisar({"Fe": 1, "Ni": 1}, repo=TM_1500, entalpias=_matriz_ficticia({("Fe", "Ni"): 0.0}))
    assert r["dH"] == 0.0 and r["omega"] is None
    assert "divisão por zero" in r["indisponiveis"]["omega"]
    assert r["T_cruzamento_k"] is None and "Não se aplica" in r["indisponiveis"]["T_cruzamento_k"]
    assert all(p["dG"] == p["menos_TdS"] for p in r["curva_T"])


def test_dh_pequeno_gera_aviso():
    r = _analisar({"Fe": 1, "Ni": 1}, repo=TM_1500, entalpias=_matriz_ficticia({("Fe", "Ni"): 0.5}))
    assert r["omega"] is not None and any("próximo de zero" in a for a in r["procedencia"]["avisos"])


def test_t12_par_ausente_nao_ha_soma_parcial():
    matriz = _matriz_ficticia({("Co", "Cr"): -10.0, ("Co", "Fe"): 5.0})   # falta Cr-Fe
    r = _analisar({"Co": 5, "Cr": 3, "Fe": 2}, entalpias=matriz)
    assert r["dH"] is None and r["omega"] is None and r["pares_faltantes"] == ["Cr-Fe"]
    assert "1 de 3 pares: Cr-Fe" in r["indisponiveis"]["dH"]
    assert {"simbolo": "Cr-Fe", "codigo": "entalpia_mistura_par", "situacao": "ausente"} in r["dados_faltantes"]
    assert not any(u["codigo"] == "entalpia_mistura_par" for u in r["procedencia"]["dados_usados"])
    assert all(p["dG"] is None for p in r["curva_T"]) and r["gibbs"] == []


def test_matriz_nao_validada_nao_e_usada_em_producao():
    matriz = _matriz_ficticia({("Fe", "Ni"): -10.0})
    r = _analisar({"Fe": 1, "Ni": 1}, PROD, entalpias=matriz)
    assert r["dH"] is None and r["pares_faltantes"] == ["Fe-Ni"]
    assert {"simbolo": "Fe-Ni", "codigo": "entalpia_mistura_par", "situacao": "nao_validado"} in r["dados_faltantes"]
    validada = _analisar({"Fe": 1, "Ni": 1}, PROD, entalpias=_matriz_ficticia({("Fe", "Ni"): -10.0}, "validado"))
    assert validada["dH"] == pytest.approx(-10.0)


def test_t13_dg_e_temperatura_de_cruzamento():
    r = _analisar({"Fe": 1, "Ni": 1}, repo=TM_1500, entalpias=_matriz_ficticia({("Fe", "Ni"): 10.0}))
    ponto = next(p for p in r["curva_T"] if p["T"] == 1000.0)
    assert ponto["dG"] == pytest.approx(4.236854, abs=1e-4)
    assert r["T_cruzamento_k"] == pytest.approx(1735.163, abs=1e-3)
    assert r["omega"] == pytest.approx(r["Tm"] / r["T_cruzamento_k"], abs=1e-4)      # Ω = T_m/T* para ΔH > 0
    assert r["dG_Tm"] == pytest.approx(10.0 - 1500.0 * R_GASES * math.log(2) / 1000.0, abs=1e-4)
    assert [g["T"] for g in r["gibbs"]] == [p["T"] for p in r["curva_T"]]
    assert all(g["G"] == pytest.approx(1000.0 * p["dG"]) for g, p in zip(r["gibbs"], r["curva_T"]))   # J/mol
    assert "gibbs" not in r["indisponiveis"] and "dG_Tm" not in r["indisponiveis"]


# ------------------------------------------------------------------ T-14: curva analítica sem ΔH
@pytest.mark.parametrize("politica", [DEV, PROD])
def test_t14_curva_menos_tds_sempre_presente(politica):
    r = _analisar(_equi("Al", "Co", "Cr", "Fe", "Ni"), politica)
    ponto = next(p for p in r["curva_T"] if p["T"] == 1000.0)
    assert ponto["menos_TdS"] == pytest.approx(-13.381611, abs=1e-4) and ponto["dG"] is None
    temperaturas = [p["T"] for p in r["curva_T"]]
    assert temperaturas[0] == 300.0 and temperaturas[-1] == r["T_sup_k"]
    assert all(b - a == 50.0 for a, b in zip(temperaturas, temperaturas[1:]))
    assert all(p["menos_TdS"] == pytest.approx(-p["T"] * R_GASES * math.log(5) / 1000.0, abs=1e-4)
               for p in r["curva_T"])
    if politica is PROD:    # sem T_m: faixa nominal, com aviso
        assert r["T_sup_k"] == 2000.0 and any("faixa de temperatura nominal" in a for a in r["procedencia"]["avisos"])
    else:                   # T_m = 1674,2 K → 1700 K
        assert r["T_sup_k"] == 1700.0


# ------------------------------------------------------------------ T-15: validação de entrada
@pytest.mark.parametrize(("composicao", "subtipo", "loc"), [
    ({"Xx": 1, "Fe": 1}, "elemento_desconhecido", ["composicao", "Xx"]),            # A-02
    ({"Fe": 1, "Zz": 1}, "elemento_desconhecido", ["composicao", "Zz"]),
    ({"": 1, "Fe": 1}, "simbolo_invalido", ["composicao", ""]),                     # A-02
    ({"<b>x</b>": 1, "Fe2O3": 1}, "simbolo_invalido", ["composicao", "<b>x</b>"]),  # A-02
    ({"Uue": 1, "Fe": 1}, "simbolo_invalido", ["composicao", "Uue"]),
    ({"fe": 1, "Fe": 1, "Ni": 1}, "elemento_repetido", ["composicao", "Fe"]),       # A-03
    ({" Fe ": 1, "Fe": 1, "Ni": 1}, "elemento_repetido", ["composicao", "Fe"]),
    ({"Fe": 1e308, "Ni": 1e308}, "quantidade_invalida", ["composicao", "Fe"]),      # A-08
    ({"Fe": "1", "Ni": 1}, "quantidade_invalida", ["composicao", "Fe"]),            # A-09 (no motor)
    ({"Fe": True, "Ni": 1}, "quantidade_invalida", ["composicao", "Fe"]),           # A-09 (no motor)
    ({"Fe": "x", "Ni": 1}, "quantidade_invalida", ["composicao", "Fe"]),
    ({"Fe": float("nan"), "Ni": 1}, "quantidade_invalida", ["composicao", "Fe"]),
    ({"Fe": float("inf"), "Ni": 1}, "quantidade_invalida", ["composicao", "Fe"]),
    ({"Fe": 10 ** 400, "Ni": 1}, "quantidade_invalida", ["composicao", "Fe"]),
    ({"Fe": 1e7, "Ni": 1}, "quantidade_invalida", ["composicao", "Fe"]),
    ({"Fe": -1, "Ni": 1}, "quantidade_invalida", ["composicao", "Fe"]),
    ({}, "elementos_insuficientes", ["composicao"]),
    ({"Fe": 1}, "elementos_insuficientes", ["composicao"]),
    ({"Fe": 0, "Ni": 1}, "elementos_insuficientes", ["composicao"]),                # A-10: mesmo subtipo
    ({"Fe": 1e-12, "Ni": 1}, "fracao_abaixo_do_minimo", ["composicao", "Fe"]),      # A-11
    (dict.fromkeys(("Ag", "Al", "Au", "Co", "Cr", "Cu", "Fe", "Mg", "Mo", "Ni", "Pb", "Ti", "W"), 1),
     "elementos_demais", ["composicao"]),
])
def test_t15_entradas_invalidas(composicao, subtipo, loc):
    with pytest.raises(EntradaInvalida) as erro:
        _analisar(composicao)
    assert isinstance(erro.value, EntradaHeaInvalida) and erro.value.codigo == "ENTRADA_INVALIDA"
    assert erro.value.detalhes[0]["type"] == subtipo and erro.value.detalhes[0]["loc"] == loc
    assert str(erro.value) == erro.value.detalhes[0]["msg"]


def test_t15_normaliza_caixa_e_espacos_descarta_zero_com_aviso():
    r = _analisar({"fe": 1, " NI ": 1, "cu": 0})                                     # A-03
    assert r["comp_percent"] == {"Fe": 50.0, "Ni": 50.0} and r["fracoes"] == {"Fe": 0.5, "Ni": 0.5}
    assert r["delta"] is not None and r["VEC"] == pytest.approx(9.0)
    assert "Elementos com quantidade zero foram ignorados: Cu." in r["procedencia"]["avisos"]


def test_mensagem_trunca_o_que_o_usuario_enviou():
    with pytest.raises(EntradaHeaInvalida) as erro:
        _analisar({"A" * 500: 1, "Fe": 1})
    assert "A" * 17 not in erro.value.detalhes[0]["msg"] and "A" * 16 in erro.value.detalhes[0]["msg"]


# ------------------------------------------------------------------ T-16, T-17: domínio do VEC (A-07)
@pytest.mark.parametrize("composicao", [{"Al": 1, "Mg": 1}, {"Mg": 1, "Ti": 1, "Zn": 1}, {"Fe": 99.9, "Ni": 0.1},
                                        _equi("Ag", "Au", "Cu", "Zn")])
def test_t16_fora_do_dominio_nao_sugere_estrutura(composicao):
    r = _analisar(composicao)
    assert r["VEC"] is not None                       # o VEC é só uma média: continua calculado
    assert r["vec_aplicavel"] is False and r["estrutura_sugerida"] is None
    assert r["fase"].startswith("não avaliada: critério de VEC fora do domínio de validade")
    assert not SIGLAS.search(r["fase"]), r["fase"]    # o front procura as siglas no texto
    assert "estrutura_sugerida" in r["indisponiveis"]
    assert any("delimitação conservadora do especialista, sem fonte" in a for a in r["procedencia"]["avisos"])
    vec = [c for c in r["criterios"] if c["grandeza"] == "VEC"]
    assert all(c["aplicavel"] is False and c["atende"] is None and c["motivo"] for c in vec)


def test_t16_dentro_do_dominio():
    cfc = _analisar(_equi("Co", "Cr", "Fe", "Ni"))
    assert cfc["vec_aplicavel"] is True and cfc["estrutura_sugerida"] == "CFC"
    assert cfc["fase"] == "CFC sugerida pelo critério empírico de VEC (VEC ≥ 8,0; Guo et al., 2011)"
    ccc = _analisar(_equi("Cr", "Mo", "W"))
    assert ccc["VEC"] == pytest.approx(6.0) and ccc["estrutura_sugerida"] == "CCC"
    assert ccc["fase"].startswith("CCC sugerida pelo critério empírico de VEC")
    meio = _analisar(_equi("Al", "Co", "Cr", "Fe", "Ni"))
    assert meio["vec_aplicavel"] is True and meio["estrutura_sugerida"] is None
    assert meio["fase"].startswith("CFC + CCC sugeridas pelo critério empírico de VEC")


def test_vec_indisponivel():
    r = _analisar(_equi(*CANTOR))
    assert r["VEC"] is None and r["vec_aplicavel"] is False and r["fase"] == "não avaliada: VEC indisponível"
    assert not SIGLAS.search(r["fase"])
    r = _analisar(_equi("Sc", "Cs", "Fe"))            # símbolos que o front leria como siglas de estrutura
    assert not SIGLAS.search(r["fase"])


def test_t17_limiar_exato_do_vec_e_estavel_a_permutacoes():
    """VEC = 33,6/4,2 = 8 por construção: a comparação usa tolerância e ``fsum``; a ordem das chaves não importa."""
    base = {"Al": 0.2, "Co": 1, "Cr": 1, "Fe": 1, "Ni": 1}
    for ordem in itertools.permutations(base):
        r = _analisar({s: base[s] for s in ordem})
        assert r["VEC"] == pytest.approx(8.0) and r["estrutura_sugerida"] == "CFC", ordem


# ------------------------------------------------------------------ T-18: triagem
def test_t18_triagem_sem_matriz():
    ruim = _analisar(_equi("Mg", "Fe", "Pb", "Al", "W"))
    assert ruim["delta"] == pytest.approx(12.0488, abs=1e-4)
    assert ruim["triagem"]["estado"] == "desfavoravel"                # antes: "INCONCLUSIVO — δ desfavorável"
    assert ruim["triagem"]["texto"].startswith("TRIAGEM DESFAVORÁVEL") and "Ω não foi avaliado" in ruim["veredito"]
    neutro = _analisar(_equi("Co", "Cr", "Fe", "Ni"))
    assert neutro["triagem"]["estado"] == "inconclusiva" and neutro["veredito"] == neutro["triagem"]["texto"]
    assert neutro["veredito"].startswith("TRIAGEM INCONCLUSIVA: δ = 0,35 % ≤ 6,6 % (atendido)")


def test_t18_tres_estados_com_matriz_ficticia():
    liga = ("Co", "Cr", "Fe", "Ni")
    favoravel = _analisar(_equi(*liga), entalpias=_matriz_ficticia(_todos_os_pares(liga, -5.0)))
    assert favoravel["dH"] == pytest.approx(-7.5) and favoravel["omega"] > 1.1
    assert favoravel["triagem"]["estado"] == "favoravel" and favoravel["veredito"].startswith("TRIAGEM FAVORÁVEL")
    desfavoravel = _analisar(_equi(*liga), entalpias=_matriz_ficticia(_todos_os_pares(liga, -40.0)))
    assert desfavoravel["omega"] < 1.1 and desfavoravel["triagem"]["estado"] == "desfavoravel"
    assert desfavoravel["vec_aplicavel"] is False and desfavoravel["estrutura_sugerida"] is None
    assert any("Os critérios discordam" in a for a in desfavoravel["procedencia"]["avisos"])
    pares = _todos_os_pares(liga, -5.0)
    pares.pop(("Co", "Cr"))
    assert _analisar(_equi(*liga), entalpias=_matriz_ficticia(pares))["triagem"]["estado"] == "inconclusiva"


def test_elemento_nao_metalico_deixa_a_triagem_inconclusiva():
    r = _analisar({"He": 1, "O": 1})
    assert r["triagem"]["estado"] == "inconclusiva" and "não metálico" in r["veredito"]
    assert sum("não é metal" in a for a in r["procedencia"]["avisos"]) == 2


# ------------------------------------------------------------------ T-19: motivo para toda grandeza nula
CASOS_T19 = [
    (_equi("Co", "Cr", "Fe", "Ni"), DEV, None), (_equi("Co", "Cr", "Fe", "Ni"), PROD, None),
    (_equi(*CANTOR), DEV, None), ({"Pb": 1, "Fe": 1}, DEV, None), ({"Al": 1, "Mg": 1}, DEV, None),
    ({"He": 1, "O": 1}, DEV, None), (_equi("Al", "Co", "Cr", "Fe", "Ni"), DEV, None),
    ({"Fe": 1, "Ni": 1}, DEV, {("Fe", "Ni"): -10.0}), ({"Fe": 1, "Ni": 1}, DEV, {("Fe", "Ni"): 0.0}),
    ({"Fe": 1, "Ni": 1}, DEV, {("Fe", "Ni"): 10.0}), ({"Fe": 1, "Mn": 1}, DEV, {("Fe", "Mn"): 10.0}),
]


@pytest.mark.parametrize(("composicao", "politica", "pares"), CASOS_T19)
def test_t19_toda_grandeza_nula_tem_motivo(composicao, politica, pares):
    r = _analisar(composicao, politica, entalpias=None if pares is None else _matriz_ficticia(pares))
    for campo, valor in r.items():
        if valor is None or (campo == "gibbs" and valor == []):
            assert r["indisponiveis"].get(campo), f"{campo} nulo sem motivo"
    assert r["energia_formacao"] is None
    assert r["indisponiveis"]["energia_formacao"].startswith("Este sistema não calcula energia de formação")
    for campo, motivo in r["indisponiveis"].items():
        assert campo in r and "Q-01" not in motivo                    # chave = nome exato do campo; sem código interno
    texto = json.dumps(r, ensure_ascii=False)
    assert "ESTÁVEL" not in texto and "estável" not in texto.lower() and "fase prevista" not in texto
    assert "mais prováveis" not in texto and r["veredito"] == r["triagem"]["texto"]
    assert all(c["verificada"] is False for c in r["criterios"]) and len(r["criterios"]) == 5
    assert [c["codigo"] for c in r["criterios"]] == ["delta_yang_zhang", "omega_yang_zhang", "vec_cfc_guo",
                                                     "vec_ccc_guo", "ds_alta_entropia"]
    for criterio in r["criterios"]:
        if criterio["valor"] is None:
            assert criterio["atende"] is None and criterio["motivo"] and criterio["proximo_do_limiar"] is False
    assert r["classes"]["dS"] == "analitico" and r["classes"]["curva_T.menos_TdS"] == "analitico"
    assert r["procedencia"]["classe"] == "estimativa_modelo"


def test_a01_sem_matriz_tudo_nulo_com_motivo_e_lista_de_pares():
    """A-01: {"Co":1,"Cr":1,"Fe":1,"Ni":1}. Antes só `dH` e `omega` tinham motivo; `gibbs`, `dureza` e
    `ductilidade` não tinham."""
    r = _analisar(_equi("Co", "Cr", "Fe", "Ni"))
    assert r["dH"] is None and r["omega"] is None and r["dureza"] is None and r["gibbs"] == []
    assert {"dH", "omega", "gibbs", "dureza", "ductilidade", "dG_Tm", "T_cruzamento_k",
            "energia_formacao"} <= set(r["indisponiveis"])
    assert "ainda não foi cadastrada" in r["indisponiveis"]["dH"]
    assert r["pares_faltantes"] == ["Co-Cr", "Co-Fe", "Co-Ni", "Cr-Fe", "Cr-Ni", "Fe-Ni"]
    assert len(r["curva_T"]) == 33 and r["T_sup_k"] == 1900.0          # T_m = 1859,4 K → 1900 K


# ------------------------------------------------------------------ T-20: produção
def test_t20_producao_so_o_que_nao_depende_de_dado_nao_validado():
    r = _analisar(_equi("Co", "Cr", "Fe", "Ni"), PROD)
    assert r["dS"] == pytest.approx(R_GASES * math.log(4), abs=1e-4)
    for campo in ("delta", "VEC", "Tm", "raio_medio_nm", "comp_massa_pct", "fracoes_massa", "massa_molar_media"):
        assert r[campo] is None and "sem validação com fonte" in r["indisponiveis"][campo], campo
    assert r["procedencia"]["dados_usados"] == []
    assert {"simbolo": "Co", "codigo": "raio_atomico", "situacao": "nao_validado"} in r["dados_faltantes"]
    assert {"simbolo": "Ni", "codigo": "massa_atomica", "situacao": "nao_validado"} in r["dados_faltantes"]
    assert r["curva_T"] and len(r["criterios"]) == 5
    assert r["triagem"]["estado"] == "inconclusiva" and r["veredito"].startswith("TRIAGEM INCONCLUSIVA: δ e Ω")
    assert r["vec_aplicavel"] is False and r["fase"] == "não avaliada: VEC indisponível"


def test_t20_producao_base_massica_e_dado_nao_validado():
    with pytest.raises(DadoNaoValidado) as erro:
        _analisar(_equi("Co", "Cr", "Fe", "Ni"), PROD, base="massica")
    assert isinstance(erro.value, MassaNaoValidada) and erro.value.codigo == "DADO_NAO_VALIDADO"
    assert {d["type"] for d in erro.value.detalhes} == {"massa_indisponivel"} and len(erro.value.detalhes) == 4


# ------------------------------------------------------------------ T-21: elemento real sem dados
def test_t21_cantor_calculo_parcial():
    r = _analisar(_equi(*CANTOR))
    assert r["dS"] == pytest.approx(13.3816, abs=1e-4) and r["classe_entropia"] == "alta"
    assert r["delta"] is None and r["Tm"] is None and r["VEC"] is None
    for codigo in ("raio_atomico", "temperatura_fusao", "vec", "massa_atomica"):
        assert {"simbolo": "Mn", "codigo": codigo, "situacao": "ausente"} in r["dados_faltantes"]
    assert "Mn" in r["indisponiveis"]["delta"] and "Mn" in r["indisponiveis"]["Tm"]
    assert r["procedencia"]["dados_usados"] == []      # só entra o que foi de fato usado num resultado


def test_dados_usados_registram_estado_e_fonte():
    r = _analisar({"Co": 1, "Ni": 1})
    usados = {(u["simbolo"], u["codigo"]): u for u in r["procedencia"]["dados_usados"]}
    assert usados[("Co", "vec")]["fonte"] == "guo2011"
    assert usados[("Ni", "raio_atomico")]["estado"] == "aguardando_validacao"
    assert usados[("Ni", "massa_atomica")]["estado"] == "aguardando_validacao"
    assert r["procedencia"]["avisos"]   # dados sem validação → aviso explícito


def test_proximo_do_limiar_gera_aviso():
    r = _analisar({"Al": 0.2, "Co": 1, "Cr": 1, "Fe": 1, "Ni": 1})   # VEC = 8,0: em cima do limiar
    criterio = next(c for c in r["criterios"] if c["codigo"] == "vec_cfc_guo")
    assert criterio["proximo_do_limiar"] is True and criterio["atende"] is True
    assert any("VEC está a menos de 2 % do limiar" in a for a in r["procedencia"]["avisos"])


# ------------------------------------------------------------------ catálogo (bootstrap)
def test_catalogo_campos_novos():
    c = catalogo(REPO, REPO, DEV, identidades=IDENT)
    assert len(c["elementos_aceitos"]) == 118
    assert [e["numero_atomico"] for e in c["elementos_aceitos"]] == list(range(1, 119))
    mn = next(e for e in c["elementos_aceitos"] if e["simbolo"] == "Mn")
    assert (mn["tem_raio"], mn["tem_fusao"], mn["tem_vec"], mn["tem_massa"]) == (False, False, False, False)
    assert set(mn) == {"simbolo", "nome", "numero_atomico", "categoria", "tem_raio", "tem_fusao", "tem_vec",
                       "tem_massa"}                                    # identidade: nenhum valor de propriedade
    assert c["entalpias"] == {"disponivel": False, "n_pares": 0, "fonte": None, "estado": None}
    assert [g["n"] for g in c["guias_entropia"]] == [2, 3, 4, 5, 6]
    assert all(g["dS"] == pytest.approx(R_GASES * math.log(g["n"]), abs=1e-6) for g in c["guias_entropia"])
    assert {d["codigo"] for d in c["definicoes"]} == {"dS", "delta", "VEC", "Tm", "dH", "omega", "menos_TdS", "dG",
                                                      "energia_formacao"}
    disponivel = {d["codigo"]: d["disponivel"] for d in c["definicoes"]}
    assert disponivel["dS"] and not disponivel["dH"] and not disponivel["energia_formacao"]
    assert len(c["avisos_fixos"]) == 3 and all(k["verificada"] is False for k in c["criterios"])
    assert [s["nome"] for s in c["samples"]] == list(c["alloys"]) and c["samples"][0]["estrutura_sugerida"] == "CFC"
    assert len(c["elements"]) == 15 and c["elements"]["Fe"]["tem_massa"] is True
    producao = catalogo(REPO, REPO, PROD, identidades=IDENT)
    assert producao["elements"]["Fe"]["tem_massa"] is False and producao["samples"][0]["delta"] is None
    assert not any(e["tem_raio"] or e["tem_massa"] for e in producao["elementos_aceitos"])


# ------------------------------------------------------------------ leitor da matriz de pares
def test_nenhum_valor_de_entalpia_cadastrado_no_repositorio():
    """Rodada R1: o seed de entalpias NÃO existe; a matriz padrão está vazia e ΔH_mix fica indisponível."""
    assert not CAMINHO_ENTALPIAS.exists()
    padrao = entalpias_padrao()
    assert padrao.resumo() == {"disponivel": False, "n_pares": 0, "fonte": None, "estado": None}
    assert padrao.entalpia_par("Co", "Cr") is None and padrao.versao_dados is None


def test_leitor_arquivo_ausente_ou_vazio_e_matriz_vazia(tmp_path):
    assert carregar_entalpias(tmp_path / "nao_existe.json").resumo()["disponivel"] is False
    vazio = tmp_path / "vazio.json"
    vazio.write_text("", encoding="utf-8")
    assert carregar_entalpias(vazio).resumo()["n_pares"] == 0
    sem_pares = tmp_path / "sem_pares.json"
    sem_pares.write_text(json.dumps({"versao_dados": "x", "unidade": "kJ/mol", "fontes": {}, "pares": []}),
                         encoding="utf-8")
    assert carregar_entalpias(sem_pares).resumo()["disponivel"] is False


def test_leitor_le_arquivo_no_formato_da_auditoria_e_e_simetrico(tmp_path):
    arquivo = tmp_path / "ficticio.json"
    arquivo.write_text(json.dumps({
        "versao_dados": "ficticia-de-teste", "grandeza": "FICTÍCIA DE TESTE", "unidade": "kJ/mol",
        "fontes": {"ficticia": {"citacao": "valores fictícios de teste"}},
        "pares": [{"a": "Co", "b": "Cr", "valor": -1.5, "unidade": "kJ/mol", "estado": "aguardando_validacao",
                   "fonte": "ficticia", "origem": "teste"}]}), encoding="utf-8")
    repo = carregar_entalpias(arquivo)
    assert repo.entalpia_par("Co", "Cr") == repo.entalpia_par("Cr", "Co")
    assert repo.entalpia_par("Co", "Cr").valor == -1.5 and repo.entalpia_par("Co", "Cr").simbolo == "Co-Cr"
    assert repo.entalpia_par("Co", "Fe") is None
    assert repo.resumo() == {"disponivel": True, "n_pares": 1, "fonte": "ficticia", "estado": "aguardando_validacao"}


@pytest.mark.parametrize("par", [
    {"a": "Cr", "b": "Co", "valor": 1.0, "estado": "rascunho"},                       # fora de ordem
    {"a": "Co", "b": "Co", "valor": 1.0, "estado": "rascunho"},                       # diagonal
    {"a": "Co", "b": "Xx", "valor": 1.0, "estado": "rascunho"},                       # símbolo inexistente
    {"a": "Co", "b": "Cr", "valor": float("nan"), "estado": "rascunho"},              # não finito
    {"a": "Co", "b": "Cr", "valor": "1", "estado": "rascunho"},                       # texto
    {"a": "Co", "b": "Cr", "valor": 1.0, "estado": "validado"},                       # validado sem fonte
    {"a": "Co", "b": "Cr", "valor": 1.0, "estado": "inventado"},                      # estado desconhecido
    {"a": "Co", "b": "Cr", "valor": 1.0, "estado": "rascunho", "fonte": "nao_existe"},
    {"a": "Co", "b": "Cr", "valor": 1.0, "estado": "rascunho", "unidade": "eV/átomo"},
])
def test_leitor_recusa_dado_invalido(par):
    with pytest.raises(ErroDeDados):
        RepositorioEntalpiasMemoria({"versao_dados": "t", "unidade": "kJ/mol", "fontes": {}, "pares": [par]},
                                    simbolos=set(IDENT))


def test_leitor_recusa_par_duplicado_e_unidade_errada():
    par = {"a": "Co", "b": "Cr", "valor": 1.0, "estado": "rascunho"}
    with pytest.raises(ErroDeDados):
        RepositorioEntalpiasMemoria({"unidade": "kJ/mol", "pares": [par, dict(par)]}, simbolos=set(IDENT))
    with pytest.raises(ErroDeDados):
        RepositorioEntalpiasMemoria({"unidade": "J/mol", "pares": [par]}, simbolos=set(IDENT))


def test_identidades_sao_118_e_nao_trazem_propriedade():
    assert len(IDENT) == 118 and IDENT["Fe"].numero_atomico == 26 and IDENT["Al"].grupo == 13
    assert set(vars(IDENT["Fe"])) == {"simbolo", "nome", "numero_atomico", "categoria", "grupo"}
