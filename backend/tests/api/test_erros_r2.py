"""Regressões dos defeitos de mensagem e de ``details`` apontados pelo QA R2 (R2-BE-02).

Cobre QA-R2-03 (mensagem em pt-BR, sem a expressão regular), QA-R2-04 (índice de lista inteiro em
``details[].loc``, contrato R1 §4.2) e QA-R2-06 (valor do usuário ecoado é truncado em 16 caracteres).
Os payloads são os do relatório ``docs/agent_reports/2026-11-15_qa_R2.md``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

from .banco import motor_de_teste, preparar_banco

LIGAS = "/api/v1/crystallography/solid-solutions"
CELULAS = "/api/v1/crystallography/cells"
TERMICO = "/api/v1/thermodynamics/thermal"
HEA = "/api/v1/hea/analyses"
CIF = "/api/v1/exports/cif"
REGISTRO = "/api/v1/auth/register"

SENHA = "cristal-cubico-2026"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(Settings(_env_file=None)), raise_server_exceptions=False)


@pytest.fixture(scope="module")
def client_com_banco(tmp_path_factory):
    url = f"sqlite:///{tmp_path_factory.mktemp('erros_r2') / 'alloy.db'}"
    preparar_banco(url)
    app = create_app(Settings(_env_file=None, env="test", rate_limit=False), motor_banco=motor_de_teste(url))
    return TestClient(app, base_url="https://testserver", raise_server_exceptions=False)


# --------------------------------------------------------------------------- QA-R2-03
def test_qa_r2_03_email_invalido_nao_vaza_a_expressao_regular(client_com_banco):
    resposta = client_com_banco.post(REGISTRO, json={"email": "xx", "senha": SENHA, "nome": "Nome"})
    corpo = resposta.json()
    assert resposta.status_code == 422, corpo
    detalhe = corpo["details"][0]
    assert detalhe["type"] == "string_pattern_mismatch"   # o subtipo é contrato: não muda
    assert detalhe["loc"] == ["email"]
    assert detalhe["msg"] == "informe um e-mail válido, no formato nome@dominio.com"
    for proibido in ("pattern", "String should", "[^@", r"\s", "{1,64}"):
        assert proibido not in detalhe["msg"], detalhe
        assert proibido not in corpo["error"], corpo
    assert corpo["error"] == ("Validação falhou em 'email': "
                              "informe um e-mail válido, no formato nome@dominio.com")


def test_qa_r2_03_nome_curto_responde_em_portugues(client_com_banco):
    resposta = client_com_banco.post(REGISTRO, json={"email": "a@b.invalid", "senha": SENHA, "nome": "W"})
    corpo = resposta.json()
    assert resposta.status_code == 422, corpo
    detalhe = corpo["details"][0]
    assert detalhe["type"] == "string_too_short" and detalhe["loc"] == ["nome"]
    assert detalhe["msg"] == "deve ter pelo menos 2 caracteres"
    assert "String should" not in corpo["error"]


def test_qa_r2_03_parametro_de_rota_com_formato_invalido(client):
    corpo = client.get("/api/v1/elements/1-2").json()
    detalhe = corpo["details"][0]
    assert detalhe["type"] == "string_pattern_mismatch"
    assert detalhe["msg"] == "use o símbolo do elemento (ex.: Fe) ou o número atômico (ex.: 26)"
    assert "pattern" not in corpo["error"]


def test_qa_r2_03_nenhuma_mensagem_de_validacao_sai_em_ingles(client):
    """Varredura: nenhum ``details[].msg`` das rotas de cálculo repassa o texto cru do validador."""
    payloads = [
        (LIGAS, {"base": "Fe", "solutos": [{"elemento": "Ni", "x": "abc"}]}),
        (LIGAS, {"base": "Fe", "solutos": [{"elemento": "Ni", "x": 1, "modo": "voador"}]}),
        (LIGAS, {"base": "Fe", "solutos": []}),
        (CELULAS, {"nome": "Fe", "raio": "x"}),
        (CELULAS, {"nome": "Fe", "c_a": True}),
        (CELULAS, {}),
        (TERMICO, {"material": "Fe"}),
        ("/api/v1/crystallography/miller", {"estrutura": "CFC", "indices": [1, 1]}),
        ("/api/v1/crystallography/supercell", {"estrutura": "CFC", "n": 99}),
    ]
    for rota, payload in payloads:
        corpo = client.post(rota, json=payload).json()
        for detalhe in corpo.get("details", []):
            msg = detalhe["msg"]
            for proibido in ("String should", "Input should", "Value error", "value is not", "pattern"):
                assert proibido not in msg, (rota, payload, detalhe)


# --------------------------------------------------------------------------- QA-R2-04
def test_qa_r2_04_indice_de_lista_e_inteiro_no_erro_de_dominio(client):
    corpo = client.post(LIGAS, json={"base": "Cu", "solutos": [{"elemento": "Zzz", "x": 5}]}).json()
    assert corpo["code"] == "MATERIAL_DESCONHECIDO"
    assert corpo["details"][0]["loc"] == ["solutos", 0, "elemento"]
    assert corpo["details"][0]["loc"][1] == 0 and isinstance(corpo["details"][0]["loc"][1], int)


def test_qa_r2_04_indice_de_lista_e_inteiro_no_erro_de_esquema(client):
    corpo = client.post(LIGAS, json={"base": "Cu", "solutos": [{"elemento": "Ni", "x": 5},
                                                               {"elemento": "Cr", "x": "abc"}]}).json()
    locs = [d["loc"] for d in corpo["details"]]
    assert ["solutos", 1, "x"] in locs, corpo
    assert all(not isinstance(p, str) or not p.isdigit() for loc in locs for p in loc), corpo


def test_qa_r2_04_chave_de_objeto_continua_texto(client):
    """Guarda: ``composicao`` é objeto — uma chave numérica do usuário NÃO vira índice inteiro."""
    corpo = client.post(HEA, json={"composicao": {"0": 1, "Ni": 1}}).json()
    assert corpo["details"][0]["loc"] == ["composicao", "0"], corpo


# --------------------------------------------------------------------------- QA-R2-06
@pytest.mark.parametrize(("rota", "payload"), [
    (TERMICO, {"material": "W" * 32, "temperatura_c": 25}),
    (CELULAS, {"nome": "Q" * 64}),
    (CIF, {"nome": "Q" * 64}),
    (HEA, {"composicao": {"X" * 200: 1, "Ni": 1}}),
    (LIGAS, {"base": "Z" * 32, "soluto": "Ni", "x": 5}),
])
def test_qa_r2_06_valor_ecoado_truncado_em_16_caracteres(client, rota, payload):
    corpo = client.post(rota, json=payload).json()
    mensagem = corpo["error"]
    assert corpo["status"] in (400, 422), corpo
    for letra in ("W", "Q", "X", "Z"):
        assert letra * 17 not in mensagem, corpo
    detalhes = " ".join(str(d.get("msg", "")) for d in corpo.get("details", []))
    for letra in ("W", "Q", "X", "Z"):
        assert letra * 17 not in detalhes, corpo


def test_qa_r2_06_estrutura_desconhecida_tambem_e_truncada(client):
    corpo = client.post(CELULAS, json={"nome": "Fe", "estrutura": "K" * 30}).json()
    assert "K" * 17 not in corpo["error"], corpo
