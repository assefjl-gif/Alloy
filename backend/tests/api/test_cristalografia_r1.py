"""Testes de contrato da rodada R1 para as rotas de ligas e de células (contrato R1 §6: T-L1 a T-L8, T-C1, T-C2).

Verificam a resposta HTTP de ``POST /api/v1/crystallography/solid-solutions`` e
``POST /api/v1/crystallography/cells``, os erros da tabela §4.2 (status, ``code`` e ``details[].type``)
e a recusa de liga multicomponente no cálculo térmico (decisão D-a).
"""

from __future__ import annotations

import json
import math

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

LIGAS = "/api/v1/crystallography/solid-solutions"
CELULAS = "/api/v1/crystallography/cells"
TERMICO = "/api/v1/thermodynamics/thermal"

CAMPOS_NOVOS_LIGA = ("composicao", "realizacao", "modelo", "prototipo", "fases", "verificacoes",
                     "regras_por_soluto", "conclusao_global", "sitios", "elementos", "convencoes",
                     "indisponiveis")
CAMPOS_LEGADOS_LIGA = ("rotulo", "base", "soluto", "intersticial", "estrutura", "estrutura_nome", "nc",
                       "c_a", "supercelula", "semente", "x_pct", "pct_peso", "a_nm", "c_nm", "a_base_nm",
                       "raio_relativo", "densidade", "densidade_base", "n_soluto", "n_solvente",
                       "fase_ordenada", "nota_arranjo", "sitio", "regras", "conclusao", "passos",
                       "distorcao", "atomos", "arestas", "procedencia")
CAMPOS_NOVOS_ATOMO = ("id", "imagem", "imagem_de", "pos_nm", "celula", "frac_celula", "ocupacao",
                      "sitio", "fase", "pos_ideal")


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(Settings(_env_file=None)), raise_server_exceptions=False)


def _resultado(client, payload, rota=LIGAS):
    resposta = client.post(rota, json=payload)
    corpo = resposta.json()
    assert resposta.status_code == 200, corpo
    assert corpo["ok"]
    return corpo["result"]


# --------------------------------------------------------------------------- T-L1
def test_tl1_pedido_binario_antigo_tem_campos_antigos_e_novos(client):
    r = _resultado(client, {"base": "Cu", "soluto": "Ni", "x": 30, "n": 2})
    for campo in CAMPOS_LEGADOS_LIGA:
        assert campo in r, campo
    for campo in CAMPOS_NOVOS_LIGA:
        assert campo in r, campo
    for atomo in r["atomos"][:5]:
        for campo in CAMPOS_NOVOS_ATOMO:
            assert campo in atomo, campo
    assert r["procedencia"]["versao_motor"] == "2.1.0"
    comp = r["composicao"]
    assert comp["n_sitios_rede"] == 32 and comp["n_desenhados"] == 63
    assert r["n_soluto"] + r["n_solvente"] == 32


# --------------------------------------------------------------------------- T-L2
def test_tl2_formas_equivalentes_e_ordem_indiferente(client):
    def limpa(d):
        copia = json.loads(json.dumps(d))
        copia["procedencia"].pop("parametros_sha256")
        copia["procedencia"].pop("calculado_em")
        return copia

    legado = _resultado(client, {"base": "Cu", "soluto": "Ni", "x": 30, "n": 2})
    novo = _resultado(client, {"base": "Cu", "solutos": [{"elemento": "Ni", "x": 30}], "n": 2})
    assert limpa(legado) == limpa(novo)

    a = _resultado(client, {"base": "Fe", "n": 2,
                            "solutos": [{"elemento": "Cr", "x": 12}, {"elemento": "C", "x": 2}]})
    b = _resultado(client, {"base": "Fe", "n": 2,
                            "solutos": [{"elemento": "C", "x": 2}, {"elemento": "Cr", "x": 12}]})
    assert limpa(a) == limpa(b)


def test_fe_cr_c_e_representavel(client):
    r = _resultado(client, {"base": "Fe", "n": 3, "semente": 7,
                            "solutos": [{"elemento": "Cr", "x": 12}, {"elemento": "Ni", "x": 8},
                                        {"elemento": "C", "x": 1, "modo": "intersticial",
                                         "sitio": "octaedrico"}]})
    assert [c["elemento"] for c in r["composicao"]["representada"]] == ["Fe", "Cr", "Ni", "C"]
    assert r["modelo"]["tipo_solucao"] == "mista"
    assert len(r["sitios"]) == 1 and r["sitios"][0]["elemento"] == "C"
    assert len(r["regras_por_soluto"]) == 3


# --------------------------------------------------------------------------- T-L3
@pytest.mark.parametrize("payload", [
    {"base": "Cu", "soluto": "Ni", "x": 30, "n": 2},
    {"base": "Fe", "soluto": "C", "x": 4, "n": 3},
    {"base": "Mg", "soluto": "Al", "x": 10, "n": 2},
    {"base": "Fe", "n": 2, "solutos": [{"elemento": "Cr", "x": 10}, {"elemento": "C", "x": 2}]},
])
def test_tl3_contagens_fecham_com_atomos_unicos(client, payload):
    r = _resultado(client, payload)
    comp = r["composicao"]
    unicos = [a for a in r["atomos"] if not a["imagem"]]
    assert len(r["atomos"]) == comp["n_desenhados"]
    assert len(unicos) == comp["n_atomos_unicos"]
    assert comp["n_atomos_unicos"] == comp["n_sitios_rede"] + comp["n_intersticiais"]
    assert r["n_soluto"] + r["n_solvente"] == comp["n_atomos_unicos"]
    soma = sum(c["n_atomos"] for c in comp["representada"])
    assert soma == comp["n_atomos_unicos"]
    assert sum(c["at_pct"] for c in comp["representada"]) == pytest.approx(100.0, abs=1e-9)
    assert sum(c["at_pct"] for c in comp["solicitada"]) == pytest.approx(100.0, abs=1e-9)
    assert sum(c["massa_pct"] for c in comp["solicitada"]) == pytest.approx(100.0, abs=1e-9)


# --------------------------------------------------------------------------- T-L4
def test_tl4_imagens_apontam_para_o_atomo_de_origem(client):
    r = _resultado(client, {"base": "Fe", "soluto": "Cr", "x": 20, "n": 2, "semente": 4})
    por_id = {a["id"]: a for a in r["atomos"] if not a["imagem"]}
    imagens = [a for a in r["atomos"] if a["imagem"]]
    assert len(imagens) == 19 and len(por_id) == 16
    for imagem in imagens:
        origem = por_id[imagem["imagem_de"]]
        assert imagem["elemento"] == origem["elemento"]
        assert imagem["ocupacao"] == origem["ocupacao"]
        assert imagem["sitio"] == origem["sitio"]
        assert imagem["id"].startswith(origem["id"] + "+")
        assert max(imagem["celula"]) == 2
    outra = _resultado(client, {"base": "Fe", "soluto": "Cr", "x": 40, "n": 2, "semente": 99})
    assert [a["id"] for a in outra["atomos"]] == [a["id"] for a in r["atomos"]]


# --------------------------------------------------------------------------- T-L5
def test_tl5_semente_reprodutivel_e_zero_e_valida(client):
    a = _resultado(client, {"base": "Fe", "soluto": "Cr", "x": 12, "n": 2, "semente": 0})
    b = _resultado(client, {"base": "Fe", "soluto": "Cr", "x": 12, "n": 2, "semente": 0})
    c = _resultado(client, {"base": "Fe", "soluto": "Cr", "x": 12, "n": 2, "semente": 1})
    assert a["realizacao"]["semente"] == 0 and a["semente"] == 0
    assert [x["elemento"] for x in a["atomos"]] == [x["elemento"] for x in b["atomos"]]
    assert [x["elemento"] for x in a["atomos"]] != [x["elemento"] for x in c["atomos"]]


# --------------------------------------------------------------------------- T-L6 (tabela §4.2)
@pytest.mark.parametrize(("payload", "status", "codigo", "subtipo", "loc"), [
    ({"base": "Fe", "soluto": "Cr", "x": 12, "solutos": [{"elemento": "Ni", "x": 2}]},
     422, "VALIDACAO", "x_com_solutos", ["x"]),
    ({"base": "Fe"}, 422, "VALIDACAO", "soluto_ou_solutos", []),
    ({"base": "Fe", "solutos": []}, 422, "VALIDACAO", "too_short", ["solutos"]),
    ({"base": "Fe", "solutos": [{"elemento": "Ni", "x": 1}] * 7},
     422, "VALIDACAO", "too_long", ["solutos"]),
    ({"base": "Fe", "solutos": [{"elemento": "Ni", "x": 1, "modo": "voador"}]},
     422, "VALIDACAO", "literal_error", ["solutos", 0, "modo"]),
    ({"base": "Fe", "soluto": "Ni", "base_composicao": "molar"},
     422, "VALIDACAO", "literal_error", ["base_composicao"]),
    ({"base": "Fe", "soluto": "Xx", "x": 2},
     400, "MATERIAL_DESCONHECIDO", "material_desconhecido", ["soluto"]),
    ({"base": "Fe", "solutos": [{"elemento": "Cr", "x": 2}, {"elemento": "cromo", "x": 3}]},
     400, "ENTRADA_INVALIDA", "soluto_repetido", ["solutos", 1, "elemento"]),
    ({"base": "Fe", "solutos": [{"elemento": "Fe", "x": 2}]},
     400, "ENTRADA_INVALIDA", "soluto_igual_ao_solvente", ["solutos", 0, "elemento"]),
    ({"base": "Fe", "solutos": [{"elemento": "Ni", "x": 2, "modo": "intersticial"}]},
     400, "ENTRADA_INVALIDA", "modo_sem_dados", ["solutos", 0, "modo"]),
    ({"base": "Fe", "solutos": [{"elemento": "C", "x": 2, "modo": "substitucional"}]},
     400, "ENTRADA_INVALIDA", "modo_sem_dados", ["solutos", 0, "modo"]),
    ({"base": "Fe", "solutos": [{"elemento": "C", "x": 2, "sitio": "cubico"}]},
     400, "ENTRADA_INVALIDA", "sitio_incompativel", ["solutos", 0, "sitio"]),
    ({"base": "Fe", "solutos": [{"elemento": "Cr", "x": 2, "sitio": "octaedrico"}]},
     400, "ENTRADA_INVALIDA", "sitio_incompativel", ["solutos", 0, "sitio"]),
    ({"base": "Fe", "solutos": [{"elemento": "Cr", "x": 60}, {"elemento": "Ni", "x": 50}]},
     400, "ENTRADA_INVALIDA", "soma_solutos_invalida", ["solutos"]),
    ({"base": "Fe", "soluto": "C", "x": 25},
     400, "ENTRADA_INVALIDA", "intersticial_acima_do_limite", ["x"]),
])
def test_tl6_erros_com_codigo_e_subtipo(client, payload, status, codigo, subtipo, loc):
    resposta = client.post(LIGAS, json=payload)
    corpo = resposta.json()
    assert resposta.status_code == status, corpo
    assert corpo["code"] == codigo
    assert corpo["details"][0]["type"] == subtipo
    assert corpo["details"][0]["loc"] == loc
    assert corpo["error"]


def test_nenhuma_entrada_malformada_produz_500(client):
    for payload in [{}, {"base": ""}, {"base": "Fe", "soluto": "Ni", "x": "abc"},
                    {"base": "Fe", "soluto": "Ni", "n": 99}, {"base": "Fe", "soluto": "Ni", "semente": -1},
                    {"base": "Fe", "soluto": "Ni", "campo_estranho": 1},
                    {"base": "Fe", "solutos": [{"elemento": "Ni", "x": None}]},
                    {"base": "Fe", "solutos": "Ni"}, {"base": "Fe", "solutos": [[1, 2]]}]:
        resposta = client.post(LIGAS, json=payload)
        assert resposta.status_code in (400, 422), (payload, resposta.status_code)


# --------------------------------------------------------------------------- T-L7
def test_tl7_fases_verificacoes_e_avisos(client):
    r = _resultado(client, {"base": "Fe", "n": 2,
                            "solutos": [{"elemento": "Cr", "x": 12}, {"elemento": "Ni", "x": 8}]})
    assert len(r["fases"]) == 1
    assert r["fases"][0]["fracao"] is None and r["fases"][0]["fracao_motivo"]
    assert r["fases"][0]["origem"] == "imposta_pelo_modelo"
    assert r["verificacoes"]["limite_solubilidade"]["verificado"] is False
    assert r["verificacoes"]["limite_solubilidade"]["valor"] is None
    assert r["verificacoes"]["fases_secundarias"]["previstas"] is None
    assert any("Modelo de fase única" in a for a in r["procedencia"]["avisos"])
    assert r["conclusao_global"] is None
    assert r["indisponiveis"]["conclusao_global"]


# --------------------------------------------------------------------------- T-L8
def test_tl8_pior_caso_mede_o_tamanho_da_resposta(client):
    payload = {"base": "Cu", "n": 4, "semente": 1, "solutos": [
        {"elemento": "Ni", "x": 10}, {"elemento": "Au", "x": 8}, {"elemento": "Ag", "x": 6},
        {"elemento": "Al", "x": 5}, {"elemento": "Pb", "x": 4},
        {"elemento": "C", "x": 20, "modo": "intersticial", "sitio": "octaedrico"}]}
    resposta = client.post(LIGAS, json=payload)
    assert resposta.status_code == 200, resposta.json()
    r = resposta.json()["result"]
    comp = r["composicao"]
    assert comp["n_sitios_rede"] == 256
    assert comp["n_intersticiais"] == 64            # ⌊256·0,20/0,80 + ½⌋ = 64, dentro dos 256 sítios
    assert comp["n_desenhados"] == len(r["atomos"])
    tamanho_kb = len(resposta.content) / 1024.0
    # Medição desta execução (o contrato §2.4 estimava 250 a 350 kB e pedia a medição):
    assert tamanho_kb < 600, tamanho_kb
    print(f"T-L8: resposta do pior caso = {tamanho_kb:.1f} kB; "
          f"{comp['n_desenhados']} esferas, {comp['n_atomos_unicos']} átomos únicos")


# --------------------------------------------------------------------------- T-C1 e T-C2
@pytest.mark.parametrize(("simbolo", "fea"), [("Mg", 0.736418), ("Ti", 0.720132), ("Co", 0.735968),
                                              ("Zn", 0.651508)])
def test_tc1_fea_do_hc_na_api(client, simbolo, fea):
    r = _resultado(client, {"nome": simbolo}, CELULAS)
    assert r["fea"] == pytest.approx(fea, abs=1e-6)
    assert r["fea"] <= math.pi / (3 * math.sqrt(2)) * (1 + 1e-12)
    assert r["vazios"] == pytest.approx(1 - fea, abs=1e-6)
    assert r["fea_modelo"] == "esferas_rigidas"
    assert r["raio_contato_rel"] is not None
    assert r["c_a_ideal"] == pytest.approx(math.sqrt(8 / 3))
    assert len(r["vizinhos"]) == 2
    assert [g["n"] for g in r["vizinhos"]] == [6, 6]
    assert r["procedencia"]["versao_motor"] == "2.1.0"


def test_tc2_estrutura_cubica_e_hc_ideal(client):
    cubica = _resultado(client, {"nome": "Fe"}, CELULAS)
    assert cubica["raio_contato_rel"] is None and cubica["contato_tipo"] is None
    assert cubica["c_a_ideal"] is None and cubica["c_a_natureza"] is None
    assert cubica["vizinhos"] is None
    assert cubica["nc_txt"] == str(cubica["nc"]) == "8"

    ideal = _resultado(client, {"nome": "HC", "raio": 0.16}, CELULAS)
    assert ideal["contato_tipo"] == "ambos"
    assert ideal["nc_txt"] == "12"
    assert ideal["c_a_natureza"] == "ideal"
    assert ideal["fea"] == pytest.approx(math.pi / (3 * math.sqrt(2)), rel=1e-12)


def test_cells_hc_fora_do_ideal_tem_rotulo_6_mais_6(client):
    r = _resultado(client, {"nome": "Mg"}, CELULAS)
    assert r["nc"] == 12 and r["nc_txt"] == "6 + 6"
    assert r["contato_tipo"] == "entre_planos"
    assert "planos" in r["contato"]
    assert any("6 + 6" in (p.get("detalhe") or "") for p in r["passos_parametro"])
    assert any("R_c" in (p.get("formula") or "") for p in r["passos_fea"])


# --------------------------------------------------------------------------- térmico (decisão D-a)
def test_termico_recusa_liga_multicomponente(client):
    resposta = client.post(TERMICO, json={"temperatura_c": 500, "liga": {
        "base": "Fe", "solutos": [{"elemento": "Cr", "x": 12}, {"elemento": "Ni", "x": 8}]}})
    corpo = resposta.json()
    assert resposta.status_code == 400
    assert corpo["code"] == "ENTRADA_INVALIDA"
    assert corpo["details"][0]["type"] == "liga_multicomponente_nao_suportada"


def test_termico_aceita_um_soluto_nas_duas_formas(client):
    for liga in ({"base": "Cu", "soluto": "Ni", "x": 30},
                 {"base": "Cu", "solutos": [{"elemento": "Ni", "x": 30}]}):
        resposta = client.post(TERMICO, json={"temperatura_c": 500, "liga": liga})
        assert resposta.status_code == 200, resposta.json()
