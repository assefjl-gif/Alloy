"""Testes da API (TestClient): contrato v1, erros, segurança e rotas legadas."""

from __future__ import annotations

import re

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from crystalab import __version__  # noqa: E402
from crystalab.api import create_app  # noqa: E402
from crystalab.api.config import Settings  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(Settings()), raise_server_exceptions=False)


def test_index_com_bootstrap_e_csp(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert f"M1 · v{__version__}" in r.text
    assert "cdnjs" not in r.text and "jsdelivr" not in r.text  # SE-01
    assert "__BOOTSTRAP_JSON__" not in r.text
    corpo = re.search(r'type="application/json">(.*?)</script>', r.text, re.S).group(1)
    assert "<" not in corpo  # SE-03: JSON escapado


@pytest.mark.parametrize("caminho", ["/static/js/main.js", "/static/css/crystalab.css",
                                     "/static/vendor/three/three.min.js", "/static/vendor/three/OrbitControls.js"])
def test_estaticos(client, caminho):
    assert client.get(caminho).status_code == 200


def test_v1_estrutura(client):
    r = client.post("/v1/crystals/structure", json={"nome": "Fe"})
    corpo = r.json()
    assert r.status_code == 200 and corpo["ok"]
    assert len(corpo["result"]["base"]) == 2 and corpo["result"]["grupo_espacial"]["numero"] == 229


def test_v1_aceita_virgula_decimal(client):
    r = client.post("/v1/crystals/structure", json={"nome": "CFC", "raio": "0,128", "peso": "63,55"})
    assert r.status_code == 200 and r.json()["result"]["densidade"] > 8


@pytest.mark.parametrize("payload,status,codigo", [
    ({"nome": "Xx"}, 400, "MATERIAL_DESCONHECIDO"),
    ({"nome": "Fe", "raio": 9}, 422, "VALIDACAO"),
    ({"nome": "Fe", "inexistente": 1}, 422, "VALIDACAO"),
    ({"nome": "Fe", "raio": "NaN"}, 422, "VALIDACAO"),
])
def test_erros_padronizados(client, payload, status, codigo):
    r = client.post("/v1/crystals/structure", json=payload)
    corpo = r.json()
    assert r.status_code == status and corpo["ok"] is False and corpo["code"] == codigo
    assert corpo["error"]


def test_validacao_com_value_error_nao_vira_500(client):
    # Na v1.0, um ValueError do field_validator tornava a resposta não serializável.
    r = client.post("/v1/crystallography/miller", json={"estrutura": "CFC", "indices": [0, 0, 0]})
    assert r.status_code == 422 and "nulos" in r.json()["error"]


def test_miller_avisos_e_tipo_em_ingles(client):
    r = client.post("/v1/crystallography/miller", json={"estrutura": "CFC", "indices": [2, 2, 2]})
    assert r.json()["result"]["ordem"] == 2
    r = client.post("/v1/crystallography/miller", json={"estrutura": "CFC", "indices": [1, 1, 0], "tipo": "direction"})
    assert r.json()["result"]["tipo"] == "direcao"


def test_export(client):
    r = client.post("/v1/export/cif", json={"nome": "Fe"})
    assert "_cell_length_a                    2.86" in r.json()["result"]["content"]


def test_limite_de_corpo_413(client):
    r = client.post("/v1/crystals/structure", content=b"x" * 2_000_000,
                    headers={"content-type": "application/json"})
    assert r.status_code == 413 and r.json()["code"] == "CORPO_GRANDE_DEMAIS"


def test_erro_interno_nao_vaza_detalhes():
    app = create_app(Settings())

    @app.get("/explode")
    def explode():
        raise ValueError("segredo interno")

    r = TestClient(app, raise_server_exceptions=False).get("/explode")
    assert r.status_code == 500 and "segredo" not in r.text and r.json()["correlation_id"]


def test_legado_marcado_como_obsoleto(client):
    r = client.post("/api/estrutura", json={"nome": "Cu", "extra": "ignorado"})
    assert r.status_code == 200 and r.headers["deprecation"] == "true"
    r = client.post("/api/estrutura", json={"nome": "Cu", "raio": "abc"})
    assert r.status_code == 400 and r.json()["ok"] is False


def test_health(client):
    assert client.get("/health").json()["version"] == __version__
    pronto = client.get("/health/ready").json()
    assert pronto["status"] == "ready" and all(pronto["checks"].values())


def test_jwt_ligado_impede_inicializacao():
    with pytest.raises(ValueError):
        Settings(jwt_enabled=True)


def test_docs_desligadas_em_producao():
    app = create_app(Settings(environment="production"))
    assert TestClient(app).get("/docs").status_code == 404
