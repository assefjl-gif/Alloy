"""/api/v1/elements (ADR-018): contrato, filtros, busca, procedência, produção e entradas maliciosas."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.core.config import Settings
from app.main import create_app

from .banco import preparar_banco


@pytest.fixture(scope="module")
def motor(tmp_path_factory):
    url = f"sqlite:///{tmp_path_factory.mktemp('tp') / 'alloy.db'}"
    preparar_banco(url)
    return create_engine(url)


@pytest.fixture(scope="module", params=["json", "banco"])
def cliente(request, motor):
    app = create_app(Settings(_env_file=None), motor_banco=motor if request.param == "banco" else None)
    return TestClient(app, raise_server_exceptions=False)


def test_lista_os_118_com_resumo_e_procedencia(cliente):
    r = cliente.get("/api/v1/elements")
    assert r.status_code == 200 and r.headers["cache-control"] == "public, max-age=3600"
    res = r.json()["result"]
    assert res["total"] == 118 and [e["numero_atomico"] for e in res["itens"]] == list(range(1, 119))
    fe = res["itens"][25]
    assert fe == {"numero_atomico": 26, "simbolo": "Fe", "nome": "Ferro", "nome_en": "iron", "periodo": 4, "grupo": 8,
                  "bloco": "d", "categoria": "metal de transição", "estado_padrao": "solido",
                  "massa": {"codigo": "peso_atomico_padrao", "valor": 55.845, "unidade": "adimensional"}}
    proc = res["procedencia"]
    assert proc["versao_dados"] == "2026.11.3-tp" and set(proc["fontes"]) == {
        "ciaaw_2024", "pubchem_tabela_periodica", "wikipedia_pt_elementos"}
    assert proc["avisos"] and "aguardando_validacao" in proc["avisos"][0]


@pytest.mark.parametrize("consulta, total", [
    ("bloco=f", 30), ("grupo=18", 7), ("periodo=1", 2), ("estado_padrao=liquido", 2),
    ("categoria=gás nobre", 7), ("bloco=d&periodo=4", 10), ("grupo=1&periodo=7", 1),
])
def test_filtros(cliente, consulta, total):
    assert cliente.get(f"/api/v1/elements?{consulta}").json()["result"]["total"] == total


@pytest.mark.parametrize("ref", ["Fe", "fe", "FE", "26"])
def test_detalhe_por_simbolo_ou_numero_atomico(cliente, ref):
    res = cliente.get(f"/api/v1/elements/{ref}").json()["result"]
    assert res["simbolo"] == "Fe" and res["configuracao_eletronica"] == "[Ar]4s2 3d6"
    props = {p["codigo"]: p for p in res["propriedades"]}
    assert props["peso_atomico_padrao"]["fonte"] == "ciaaw_2024"
    assert props["temperatura_fusao"] == {**props["temperatura_fusao"], "valor": 1811.0, "unidade": "K"}
    assert all(p["estado"] == "aguardando_validacao" for p in res["propriedades"])


def test_intervalo_e_massa_de_referencia(cliente):
    h = {p["codigo"]: p for p in cliente.get("/api/v1/elements/H").json()["result"]["propriedades"]}
    assert h["peso_atomico_padrao"]["intervalo"] == [1.00784, 1.00811]
    tc = {p["codigo"]: p for p in cliente.get("/api/v1/elements/Tc").json()["result"]["propriedades"]}
    assert "peso_atomico_padrao" not in tc and "não é peso atômico padrão" in tc["massa_isotopica_referencia"]["nota"]


@pytest.mark.parametrize("ref, status", [("Xx", 404), ("0", 404), ("119", 404), ("9999", 422), ("Fe1", 422)])
def test_referencias_invalidas(cliente, ref, status):
    r = cliente.get(f"/api/v1/elements/{ref}")
    assert r.status_code == status and r.json()["ok"] is False


@pytest.mark.parametrize("url", [
    "/api/v1/elements/Fe' OR '1'='1",
    "/api/v1/elements/%27%3B%20DROP%20TABLE%20elementos%3B--",
    "/api/v1/elements/..%2F..%2Fetc%2Fpasswd",
    "/api/v1/elements?grupo=1%20OR%201=1",
    "/api/v1/elements?bloco=f'--",
    "/api/v1/elements?periodo=99",
])
def test_entradas_maliciosas_sao_recusadas_sem_vazar_detalhes(cliente, url):
    r = cliente.get(url)
    assert r.status_code in (404, 422), r.text
    assert "Traceback" not in r.text and "sqlite" not in r.text.lower()


def test_categoria_com_aspas_nao_quebra_nem_retorna_tudo(cliente):
    r = cliente.get("/api/v1/elements", params={"categoria": "x' OR '1'='1"})
    assert r.status_code == 200 and r.json()["result"]["total"] == 0
    assert cliente.get("/api/v1/elements/Fe").status_code == 200   # a tabela continua lá


def test_producao_entrega_com_aviso_de_validacao(motor):
    app = create_app(Settings(_env_file=None, env="prod", demo="proibido", database_url="sqlite://",
                              session_secret="s" * 40, csrf_secret="c" * 40, rate_limit=False), motor_banco=motor)
    r = TestClient(app).get("/api/v1/elements/Fe")
    assert r.status_code == 200 and r.json()["result"]["procedencia"]["avisos"]


def test_openapi_documenta_as_rotas(cliente):
    caminhos = cliente.get("/api/v1/openapi.json").json()["paths"]
    assert "/api/v1/elements" in caminhos and "/api/v1/elements/{ref}" in caminhos
