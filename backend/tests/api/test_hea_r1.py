"""Contrato R1 do HEA na API: testes T-H1 a T-H9 (contrato, seção 6) e regressão das falhas da auditoria
R1-HEA-01 (A-01, A-02, A-03, A-07, A-08, A-09), com os payloads do relatório.

O caminho "com matriz de entalpias" é testado no motor (tests/unit/engines/test_hea.py), com matriz FICTÍCIA
injetada só no teste: a API real não tem matriz cadastrada.
"""

from __future__ import annotations

import json
import math

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

from .banco import preparar_banco

ROTA = "/api/v1/hea/analyses"
R = 8.314462618
EXISTENTES = {"nome", "veredito", "fase", "estrutura_sugerida", "ductilidade", "dureza", "dureza_indice", "dS", "dH",
              "delta", "omega", "VEC", "Tm", "comp_percent", "fracoes", "interpretacao", "fragilidade", "gibbs",
              "indisponiveis", "procedencia"}
NOVOS = {"base_entrada", "soma_informada", "fracoes_massa", "comp_massa_pct", "massa_molar_media", "dS_R",
         "classe_entropia", "raio_medio_nm", "pares_faltantes", "dados_faltantes", "curva_T", "T_sup_k", "dG_Tm",
         "T_cruzamento_k", "energia_formacao", "criterios", "triagem", "vec_aplicavel", "classes"}
COCRFENI = {"Co": 1, "Cr": 1, "Fe": 1, "Ni": 1}
TREZE = dict.fromkeys(("Ag", "Al", "Au", "Co", "Cr", "Cu", "Fe", "Mg", "Mo", "Ni", "Pb", "Ti", "W"), 1)


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(Settings(_env_file=None)), raise_server_exceptions=False)


@pytest.fixture(scope="module")
def producao(tmp_path_factory):
    url = f"sqlite:///{tmp_path_factory.mktemp('prod_hea') / 'alloy.db'}"
    preparar_banco(url)
    settings = Settings(_env_file=None, env="prod", demo="proibido", session_secret="s" * 40, csrf_secret="c" * 40,
                        database_url=url)
    return TestClient(create_app(settings), raise_server_exceptions=False)


def _post(cliente, corpo):
    if isinstance(corpo, (bytes, str)):   # JSON escrito à mão: NaN, Infinity, 1e400
        return cliente.post(ROTA, content=corpo, headers={"content-type": "application/json"})
    return cliente.post(ROTA, json=corpo)


def _ok(cliente, composicao, **extra):
    r = _post(cliente, {"composicao": composicao, **extra})
    assert r.status_code == 200, r.text
    return r.json()["result"]


# ------------------------------------------------------------------ T-H1
def test_th1_pedido_antigo_devolve_campos_existentes_e_novos(client):
    res = _ok(client, COCRFENI, nome="CoCrFeNi")
    assert EXISTENTES | NOVOS <= set(res), (EXISTENTES | NOVOS) - set(res)
    assert res["base_entrada"] == "atomica" and res["soma_informada"] == 4
    assert res["dS"] == pytest.approx(11.5263, abs=1e-4) and res["dS_R"] == pytest.approx(1.3863, abs=1e-4)
    assert res["classe_entropia"] == "media"
    # valores existentes inalterados (regressão do motor 1.0.0)
    assert res["delta"] == pytest.approx(0.3512, abs=1e-4) and res["VEC"] == pytest.approx(8.25)
    assert res["Tm"] == pytest.approx(1859.4, abs=0.1) and res["estrutura_sugerida"] == "CFC"
    assert res["procedencia"]["versao_motor"] == "2.0.0" and res["procedencia"]["calculado_em"]
    assert res["procedencia"]["classe"] == "estimativa_modelo" and res["procedencia"]["motor"] == "hea"
    assert set(res["classes"]) == {"dS", "delta", "VEC", "Tm", "dH", "omega", "curva_T.menos_TdS", "curva_T.dG",
                                   "comp_massa_pct"}
    assert set(res["criterios"][0]) == {"codigo", "grandeza", "operador", "limiar", "unidade", "valor", "atende",
                                        "aplicavel", "proximo_do_limiar", "natureza", "fonte", "verificada", "motivo"}


# ------------------------------------------------------------------ T-H2
@pytest.mark.parametrize("composicao", [COCRFENI, {"Co": 1, "Cr": 1, "Fe": 1, "Mn": 1, "Ni": 1}, {"Al": 1, "Mg": 1},
                                        {"He": 1, "O": 1}, {"Pb": 1, "Fe": 1}])
def test_th2_todo_campo_nulo_tem_motivo(client, producao, composicao):
    for cliente in (client, producao):
        res = _ok(cliente, composicao)
        nulos = [campo for campo, valor in res.items() if valor is None]
        assert "energia_formacao" in nulos and "estrutura_sugerida" in res        # sempre enviado, nunca omitido
        for campo in nulos:
            assert res["indisponiveis"].get(campo), f"{campo} nulo sem motivo"
        assert res["indisponiveis"]["energia_formacao"] == (
            "Este sistema não calcula energia de formação: exige cálculo de primeiros princípios (DFT), CALPHAD ou "
            "medida calorimétrica da fase. ΔH_mix e ΔG_mix do modelo não a substituem.")
        assert not any("Q-01" in motivo for motivo in res["indisponiveis"].values())


# ------------------------------------------------------------------ T-H3 (tabela 4.1 do contrato)
TABELA_4_1 = [
    # (corpo, status, code, type, loc)
    ({"composicao": {"Fe": "1", "Ni": 1}}, 422, "VALIDACAO", "float_type", ["composicao", "Fe"]),                # A-09
    ({"composicao": {"Fe": True, "Ni": 1}}, 422, "VALIDACAO", "float_type", ["composicao", "Fe"]),               # A-09
    ({"composicao": TREZE}, 422, "VALIDACAO", "too_long", ["composicao"]),
    ({"composicao": {"Fe": 1, "Ni": 1}, "base": "massa"}, 422, "VALIDACAO", "literal_error", ["base"]),
    ({"composicao": {"Fe": 1, "Ni": 1}, "temperatura_k": 300}, 422, "VALIDACAO", "extra_forbidden",
     ["temperatura_k"]),
    ({"composicao": {"Fe": 1}}, 422, "VALIDACAO", "elementos_insuficientes", ["composicao"]),
    ({"composicao": {}}, 422, "VALIDACAO", "elementos_insuficientes", ["composicao"]),
    ({"composicao": {"Fe": 0, "Ni": 1}}, 422, "VALIDACAO", "elementos_insuficientes", ["composicao"]),
    ({"composicao": {"Fe": 0, "Ni": 0}}, 422, "VALIDACAO", "elementos_insuficientes", ["composicao"]),
    ({"composicao": {"Fe": -1, "Ni": 1}}, 400, "ENTRADA_INVALIDA", "quantidade_invalida", ["composicao", "Fe"]),
    ({"composicao": {"Fe": 1e7, "Ni": 1}}, 400, "ENTRADA_INVALIDA", "quantidade_invalida", ["composicao", "Fe"]),
    (b'{"composicao":{"Fe":NaN,"Ni":1}}', 400, "ENTRADA_INVALIDA", "quantidade_invalida", ["composicao", "Fe"]),
    (b'{"composicao":{"Fe":Infinity,"Ni":1}}', 400, "ENTRADA_INVALIDA", "quantidade_invalida", ["composicao", "Fe"]),
    (b'{"composicao":{"Fe":-Infinity,"Ni":1}}', 400, "ENTRADA_INVALIDA", "quantidade_invalida", ["composicao", "Fe"]),
    (b'{"composicao":{"Fe":1e400,"Ni":1}}', 400, "ENTRADA_INVALIDA", "quantidade_invalida", ["composicao", "Fe"]),
    ({"composicao": {"Fe": 1e308, "Ni": 1e308}}, 400, "ENTRADA_INVALIDA", "quantidade_invalida",
     ["composicao", "Fe"]),                                                                                      # A-08
    ({"composicao": {"": 1, "Fe": 1}}, 400, "ENTRADA_INVALIDA", "simbolo_invalido", ["composicao", ""]),         # A-02
    ({"composicao": {"<b>x</b>": 1, "Fe2O3": 1}}, 400, "ENTRADA_INVALIDA", "simbolo_invalido",
     ["composicao", "<b>x</b>"]),                                                                                # A-02
    ({"composicao": {"Xx": 1, "Fe": 1}}, 400, "ENTRADA_INVALIDA", "elemento_desconhecido", ["composicao", "Xx"]),  # A2
    ({"composicao": {"fe": 1, "Fe": 1, "Ni": 1}}, 400, "ENTRADA_INVALIDA", "elemento_repetido",
     ["composicao", "Fe"]),                                                                                      # A-03
    ({"composicao": {"Fe": 1, "Mn": 1}, "base": "massica"}, 400, "ENTRADA_INVALIDA", "massa_indisponivel",
     ["composicao", "Mn"]),
    ({"composicao": {"Fe": 1e-12, "Ni": 1}}, 400, "ENTRADA_INVALIDA", "fracao_abaixo_do_minimo",
     ["composicao", "Fe"]),
]


@pytest.mark.parametrize(("corpo", "status", "codigo", "tipo", "loc"), TABELA_4_1)
def test_th3_tabela_de_erros(client, corpo, status, codigo, tipo, loc):
    r = _post(client, corpo)
    envelope = r.json()
    assert (r.status_code, envelope["code"], envelope["status"]) == (status, codigo, status), envelope
    assert envelope["ok"] is False and envelope["request_id"] == r.headers["x-request-id"]
    assert envelope["details"][0]["type"] == tipo and envelope["details"][0]["loc"] == loc, envelope["details"]
    assert all(set(d) == {"loc", "type", "msg"} for d in envelope["details"])
    if status == 400:
        assert envelope["error"] == envelope["details"][0]["msg"]      # `error` repete a 1ª mensagem


def test_th3_producao_base_massica_com_massa_nao_validada(producao):
    r = _post(producao, {"composicao": COCRFENI, "base": "massica"})
    envelope = r.json()
    assert (r.status_code, envelope["code"]) == (422, "DADO_NAO_VALIDADO")
    assert [d["type"] for d in envelope["details"]] == ["massa_indisponivel"] * 4
    assert [d["loc"] for d in envelope["details"]] == [["composicao", s] for s in ("Co", "Cr", "Fe", "Ni")]


ENTRADAS_HOSTIS = [
    {"composicao": {"Fe": 1e308, "Ni": 1e308}}, {"composicao": {"Fe": 1e-300, "Ni": 1e-300}},
    {"composicao": {"Fe": 5e-324, "Ni": 1e6}}, {"composicao": {"A" * 5000: 1, "Fe": 1}},
    {"composicao": {"Fé": 1, "Ni": 1}}, {"composicao": {"𝐅e": 1, "Ni": 1}}, {"composicao": {"Fe\u0000": 1, "Ni": 1}},
    {"composicao": {"Fe": None, "Ni": 1}}, {"composicao": {"Fe": [1], "Ni": 1}},
    {"composicao": {"Fe": {"a": 1}, "Ni": 1}},
    {"composicao": [["Fe", 1], ["Ni", 1]]}, {"composicao": "Fe1Ni1"}, {"composicao": None}, {},
    {"composicao": {"Fe": 1, "Ni": 1}, "base": None}, {"composicao": {"Fe": 1, "Ni": 1}, "base": 1},
    {"composicao": {"Fe": 1, "Ni": 1}, "nome": "x" * 81},
    b'{"composicao":{"Fe":1,"Fe":1,"Ni":1}}', b'{"composicao":{"Fe":-0.0,"Ni":1,"Co":1}}',
    b'{"composicao":{"Fe":' + b"9" * 400 + b',"Ni":1}}', b'{"composicao":{"Fe":' + b"9" * 5000 + b',"Ni":1}}',
    b'{"composicao":{"Fe":1e-400,"Ni":1,"Co":1}}', b'[1,2]', b'"texto"', b'{"composicao":',
]


@pytest.mark.parametrize("corpo", ENTRADAS_HOSTIS)
def test_th3_nenhuma_entrada_produz_500(client, producao, corpo):
    for cliente in (client, producao):
        r = _post(cliente, corpo)
        assert r.status_code in (200, 400, 422), (r.status_code, r.text[:300])
        assert r.json()["ok"] is (r.status_code == 200)


def test_mensagem_de_erro_trunca_a_chave_enviada(client):
    envelope = _post(client, {"composicao": {"A" * 5000: 1, "Fe": 1}}).json()
    assert envelope["details"][0]["type"] == "simbolo_invalido" and len(envelope["error"]) < 200


# ------------------------------------------------------------------ T-H4
def test_th4_normaliza_simbolos_recusa_repeticao_e_descarta_zero(client):
    res = _ok(client, {"fe": 1, "NI": 1})                                   # A-03: antes "NI" ficava sem dados
    assert res["comp_percent"] == {"Fe": 50.0, "Ni": 50.0} and res["fracoes"] == {"Fe": 0.5, "Ni": 0.5}
    assert res["delta"] is not None and res["VEC"] == pytest.approx(9.0) and res["Tm"] is not None
    r = _post(client, {"composicao": {"Fe": 1, "fe": 1}})
    assert r.status_code == 400 and r.json()["details"][0]["type"] == "elemento_repetido"
    assert "'Fe' e 'fe' são o mesmo elemento (Fe)" in r.json()["error"]
    res = _ok(client, {"Fe": 1, "Ni": 1, "Cu": 0})
    assert set(res["comp_percent"]) == {"Fe", "Ni"}
    assert "Elementos com quantidade zero foram ignorados: Cu." in res["procedencia"]["avisos"]


# ------------------------------------------------------------------ T-H5 (A-01)
@pytest.mark.parametrize(("composicao", "n"), [(COCRFENI, 4), ({"Fe": 1, "Ni": 1}, 2),
                                               ({"Al": 1, "Co": 1, "Cr": 1, "Cu": 1, "Fe": 1, "Ni": 1}, 6)])
def test_th5_sem_matriz_de_pares(client, producao, composicao, n):
    for cliente in (client, producao):
        res = _ok(cliente, composicao)
        for campo in ("dH", "omega", "dG_Tm", "T_cruzamento_k"):
            assert res[campo] is None and res["indisponiveis"][campo], campo
        assert all(p["dG"] is None for p in res["curva_T"]) and res["gibbs"] == [] and res["indisponiveis"]["gibbs"]
        assert len(res["pares_faltantes"]) == n * (n - 1) // 2
        assert res["pares_faltantes"] == sorted(res["pares_faltantes"])
        assert all(a < b for a, b in (par.split("-") for par in res["pares_faltantes"]))
        pares = [d for d in res["dados_faltantes"] if d["codigo"] == "entalpia_mistura_par"]
        assert [d["simbolo"] for d in pares] == res["pares_faltantes"] and {d["situacao"] for d in pares} == {"ausente"}
        assert res["indisponiveis"]["dH"].startswith("ΔH_mix indisponível: a tabela de entalpias de mistura por par")


def test_a01_motivos_que_faltavam(client):
    """A-01: antes `indisponiveis` = {dH, omega}; `gibbs`, `dureza` e `ductilidade` vazios não tinham motivo."""
    res = _ok(client, COCRFENI)
    assert res["dH"] is None and res["omega"] is None and res["gibbs"] == []
    assert {"dH", "omega", "gibbs", "dureza", "ductilidade"} <= set(res["indisponiveis"])


# ------------------------------------------------------------------ T-H6
@pytest.mark.parametrize(("composicao", "t_sup"), [(COCRFENI, 1900.0), ({"Cr": 1, "Mo": 1, "W": 1}, 3000.0),
                                                   ({"Co": 1, "Cr": 1, "Fe": 1, "Mn": 1, "Ni": 1}, 2000.0)])
def test_th6_curva_t(client, composicao, t_sup):
    res = _ok(client, composicao)
    temperaturas = [p["T"] for p in res["curva_T"]]
    assert temperaturas[0] == 300 and temperaturas[-1] == res["T_sup_k"] == t_sup
    assert all(b - a == 50 for a, b in zip(temperaturas, temperaturas[1:])) and len(temperaturas) <= 115
    ds = R * -sum(x * math.log(x) for x in res["fracoes"].values())
    for ponto in res["curva_T"]:
        assert ponto["menos_TdS"] == pytest.approx(-ponto["T"] * ds / 1000, abs=1e-4)
        assert ponto["menos_TdS"] == pytest.approx(-ponto["T"] * res["dS"] / 1000, abs=5e-4)   # dS vem com 4 casas
    if res["Tm"] is None:
        assert any("faixa de temperatura nominal" in a for a in res["procedencia"]["avisos"])
    else:
        assert 0 <= res["T_sup_k"] - res["Tm"] < 100


def test_th6_exemplo_do_contrato(producao):
    """Seção 1.4 do contrato: CoCrFeNi em produção. R·ln 4 = 11,5263; −300·ΔS/1000 = −3,4579; −2000 → −23,0526."""
    res = _ok(producao, COCRFENI, nome="CoCrFeNi")
    assert res["dS"] == 11.5263 and res["dS_R"] == 1.3863 and res["classe_entropia"] == "media"
    assert res["T_sup_k"] == 2000 and len(res["curva_T"]) == 35
    assert res["curva_T"][0] == {"T": 300, "menos_TdS": -3.4579, "dG": None}
    assert res["curva_T"][1] == {"T": 350, "menos_TdS": -4.0342, "dG": None}
    assert res["curva_T"][-1] == {"T": 2000, "menos_TdS": -23.0526, "dG": None}
    for campo in ("dH", "delta", "omega", "VEC", "Tm", "raio_medio_nm", "fracoes_massa", "comp_massa_pct",
                  "massa_molar_media", "estrutura_sugerida"):
        assert res[campo] is None, campo
    assert res["fase"] == "não avaliada: VEC indisponível" and res["vec_aplicavel"] is False
    assert res["triagem"]["estado"] == "inconclusiva" and res["veredito"].startswith("TRIAGEM INCONCLUSIVA: δ e Ω")
    assert {"simbolo": "Co", "codigo": "raio_atomico", "situacao": "nao_validado"} in res["dados_faltantes"]
    assert {"simbolo": "Co-Cr", "codigo": "entalpia_mistura_par", "situacao": "ausente"} in res["dados_faltantes"]
    assert res["procedencia"]["dados_usados"] == []
    ds_alta = next(c for c in res["criterios"] if c["codigo"] == "ds_alta_entropia")
    assert (ds_alta["valor"], ds_alta["atende"], ds_alta["limiar"], ds_alta["unidade"]) == (1.3863, False, 1.5, "R")
    delta = next(c for c in res["criterios"] if c["codigo"] == "delta_yang_zhang")
    assert delta["valor"] is None and delta["atende"] is None and delta["motivo"].startswith("δ indisponível")


# ------------------------------------------------------------------ T-H7
@pytest.mark.parametrize("composicao", [COCRFENI, {"Mg": 1, "Fe": 1, "Pb": 1, "Al": 1, "W": 1}, {"Al": 1, "Mg": 1},
                                        {"Co": 1, "Cr": 1, "Fe": 1, "Mn": 1, "Ni": 1}, {"He": 1, "O": 1}])
def test_th7_triagem_sem_estavel(client, producao, composicao):
    for cliente in (client, producao):
        res = _ok(cliente, composicao)
        assert res["triagem"]["estado"] in ("favoravel", "desfavoravel", "inconclusiva")
        assert res["veredito"] == res["triagem"]["texto"] and res["veredito"].startswith("TRIAGEM ")
        assert "ESTÁVEL" not in json.dumps(res, ensure_ascii=False).upper().replace("INSTÁVEL", "")
        assert res["criterios"] and all(c["verificada"] is False for c in res["criterios"])


def test_th7_delta_alto_sem_omega_e_desfavoravel(client):
    """V-4: δ > 6,6 % sem Ω passa de "INCONCLUSIVO — δ desfavorável" a `desfavoravel` (a conjunção já falha)."""
    res = _ok(client, {"Mg": 1, "Fe": 1, "Pb": 1, "Al": 1, "W": 1})
    assert res["delta"] == pytest.approx(12.0488, abs=1e-4) and res["triagem"]["estado"] == "desfavoravel"


# ------------------------------------------------------------------ A-07 (domínio do VEC)
@pytest.mark.parametrize(("composicao", "vec"), [({"Al": 1, "Mg": 1}, 2.5), ({"Mg": 1, "Ti": 1, "Zn": 1}, 6.0),
                                                 ({"Fe": 99.9, "Ni": 0.1}, 8.002)])
def test_a07_vec_fora_do_dominio_nao_sugere_estrutura(client, composicao, vec):
    """A-07: antes Al–Mg e Mg–Ti–Zn recebiam "CCC" e Fe quase puro recebia "CFC", com `estrutura_sugerida`."""
    res = _ok(client, composicao)
    assert res["VEC"] == pytest.approx(vec, abs=1e-3)
    assert res["vec_aplicavel"] is False and res["estrutura_sugerida"] is None
    assert res["fase"].startswith("não avaliada") and "CCC" not in res["fase"] and "CFC" not in res["fase"]
    assert res["indisponiveis"]["estrutura_sugerida"]
    assert any("sem fonte bibliográfica" in a for a in res["procedencia"]["avisos"])


# ------------------------------------------------------------------ T-H8
def test_th8_ida_e_volta_atomica_massica(client):
    ida = _ok(client, {"Al": 0.5, "Co": 1, "Cr": 1, "Cu": 1, "Fe": 1, "Ni": 1})
    assert sum(ida["fracoes"].values()) == pytest.approx(1.0, abs=1e-12)
    assert sum(ida["fracoes_massa"].values()) == pytest.approx(1.0, abs=1e-12)
    assert sum(ida["comp_massa_pct"].values()) == pytest.approx(100.0, abs=6e-4)
    assert sum(ida["comp_percent"].values()) == pytest.approx(100.0, abs=6e-4)
    volta = _ok(client, ida["fracoes_massa"], base="massica")
    assert volta["base_entrada"] == "massica"
    for simbolo, x in ida["fracoes"].items():
        assert volta["fracoes"][simbolo] == pytest.approx(x, abs=1e-12)
    for campo in ("dS", "delta", "VEC", "Tm", "massa_molar_media"):
        assert volta[campo] == pytest.approx(ida[campo], rel=1e-9), campo
    massas = [u for u in ida["procedencia"]["dados_usados"] if u["codigo"] == "massa_atomica"]
    assert len(massas) == 6 and {u["unidade"] for u in massas} == {"g/mol"}
    r = _post(client, {"composicao": {"Fe": 50, "Mn": 50}, "base": "massica"})       # Mn: sem massa no repositório
    assert (r.status_code, r.json()["code"], r.json()["details"][0]["type"]) == (400, "ENTRADA_INVALIDA",
                                                                                 "massa_indisponivel")


# ------------------------------------------------------------------ T-H9
def test_th9_bootstrap(client, producao):
    r = client.get("/api/v1/hea/bootstrap")
    boot = r.json()["result"]
    assert r.status_code == 200 and r.headers["cache-control"] == "public, max-age=300"
    # campos existentes inalterados
    assert set(boot["alloys"]) == {"CoCrFeNi", "AlCoCrFeNi", "CoCrCuFeNi", "Al0.5CoCrCuFeNi"}
    assert boot["reference"] == {"dS": 12.472, "omega": 1.1, "delta": 6.6, "VEC": 8.0, "dH": None,
                                 "T_padrao": "não se aplica (ΔS_mix ideal)", "P_padrao": "não se aplica"}
    assert len(boot["elements"]) == 15 and boot["elements"]["Fe"]["raio_nm"] == 0.1241
    assert boot["elements"]["Fe"]["tem_fusao"] is True and boot["elements"]["Pb"]["tem_vec"] is False
    assert boot["versao_motor"] == "2.0.0"
    # campos novos
    assert boot["elements"]["Fe"]["tem_massa"] is True
    assert len(boot["elementos_aceitos"]) == 118
    assert [e["numero_atomico"] for e in boot["elementos_aceitos"]] == list(range(1, 119))
    assert boot["entalpias"] == {"disponivel": False, "n_pares": 0, "fonte": None, "estado": None}
    assert [g["n"] for g in boot["guias_entropia"]] == [2, 3, 4, 5, 6]
    assert len(boot["definicoes"]) == 9 and len(boot["avisos_fixos"]) == 3
    assert len(boot["criterios"]) == 5 and all(c["verificada"] is False for c in boot["criterios"])
    assert set(boot["criterios"][0]) == {"codigo", "grandeza", "operador", "limiar", "unidade", "natureza", "fonte",
                                         "verificada"}
    assert len(boot["samples"]) == 4
    for amostra in boot["samples"]:
        assert EXISTENTES - {"procedencia"} | NOVOS <= set(amostra)
        assert amostra["triagem"]["estado"] == "inconclusiva" and amostra["dH"] is None
    assert "ESTÁVEL" not in r.text
    prod = producao.get("/api/v1/hea/bootstrap").json()["result"]
    assert prod["samples"][0]["delta"] is None and prod["samples"][0]["dS"] == 11.5263   # mesma política de dados
    assert prod["elements"]["Fe"]["tem_massa"] is False and prod["entalpias"]["disponivel"] is False


# ------------------------------------------------------------------ T-G1 (parte do HEA)
def test_tg1_openapi_tem_os_campos_novos_e_os_obsoletos(client):
    esquemas = client.get("/api/v1/openapi.json").json()["components"]["schemas"]
    resposta, bootstrap = esquemas["HeaResponse"]["properties"], esquemas["HeaBootstrap"]["properties"]
    assert NOVOS <= set(resposta) and resposta["gibbs"]["deprecated"] is True
    assert {"elementos_aceitos", "criterios", "entalpias", "guias_entropia", "definicoes",
            "avisos_fixos"} <= set(bootstrap)
    assert bootstrap["reference"]["deprecated"] is True
    assert esquemas["HeaRequest"]["properties"]["base"]["enum"] == ["atomica", "massica"]
    assert "tem_massa" in esquemas["HeaElement"]["properties"]


def test_capacidades_sem_codigo_interno(client, producao):
    for cliente in (client, producao):
        motivo = cliente.get("/api/v1/meta/capabilities").json()["result"]["hea"]["motivo"]
        assert "Parcial" in motivo and "Q-01" not in motivo
