"""API /api/v1 e aliases /v1 (RQ-API-01..04). Parte migrada de B ``tests/test_api.py``.

Não migrados (com motivo): página/estáticos do B (o frontend sai da API, ADR-011), rotas legadas
/api/* da v1.0 (removidas, API.md §3) e o teste da flag JWT (autenticação por sessão, ADR-008).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import __version__
from app.core.config import Settings
from app.main import create_app

from .banco import preparar_banco

ROTAS_ALIAS = [
    ("post", "/v1/crystals/structure", "/api/v1/crystallography/cells", {"nome": "Fe"}),
    ("post", "/v1/calculations/density", "/api/v1/crystallography/density", {"nome": "Cu"}),
    ("post", "/v1/crystallography/miller", "/api/v1/crystallography/miller",
     {"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1]}),
    ("post", "/v1/export/xyz", "/api/v1/exports/xyz", {"nome": "Mg"}),
    ("get", "/v1/crystals/metals", "/api/v1/crystallography/metals", None),
    ("get", "/v1/crystals/structures", "/api/v1/crystallography/structures", None),
]


def _producao(**extra) -> Settings:
    extra.setdefault("database_url", "sqlite://")
    return Settings(_env_file=None, env="prod", demo="proibido",
                    session_secret="s" * 40, csrf_secret="c" * 40, **extra)


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(Settings(_env_file=None)), raise_server_exceptions=False)


def _chamar(client, metodo, url, corpo):
    return client.post(url, json=corpo) if metodo == "post" else client.get(url)


# --------------------------------------------------------------- migrados do B
def test_estrutura(client):
    r = client.post("/api/v1/crystallography/cells", json={"nome": "Fe"})
    corpo = r.json()
    assert r.status_code == 200 and corpo["ok"]
    assert len(corpo["result"]["base"]) == 2 and corpo["result"]["grupo_espacial"]["numero"] == 229


def test_aceita_virgula_decimal(client):
    r = client.post("/api/v1/crystallography/cells", json={"nome": "CFC", "raio": "0,128", "peso": "63,55"})
    assert r.status_code == 200 and r.json()["result"]["densidade"] > 8


@pytest.mark.parametrize(("payload", "status", "codigo"), [
    ({"nome": "Xx"}, 400, "MATERIAL_DESCONHECIDO"),
    ({"nome": "Fe", "raio": 9}, 422, "VALIDACAO"),
    ({"nome": "Fe", "inexistente": 1}, 422, "VALIDACAO"),
    ({"nome": "Fe", "raio": "NaN"}, 422, "VALIDACAO"),
])
def test_erros_padronizados(client, payload, status, codigo):
    r = client.post("/api/v1/crystallography/cells", json=payload)
    corpo = r.json()
    assert r.status_code == status and corpo["ok"] is False and corpo["code"] == codigo
    assert corpo["error"] and corpo["request_id"] == r.headers["x-request-id"]


def test_validacao_com_value_error_nao_vira_500(client):
    r = client.post("/api/v1/crystallography/miller", json={"estrutura": "CFC", "indices": [0, 0, 0]})
    assert r.status_code == 422 and "nulos" in r.json()["error"]


def test_miller_avisos_e_tipo_em_ingles(client):
    r = client.post("/api/v1/crystallography/miller", json={"estrutura": "CFC", "indices": [2, 2, 2]})
    assert r.json()["result"]["ordem"] == 2
    r = client.post("/api/v1/crystallography/miller",
                    json={"estrutura": "CFC", "indices": [1, 1, 0], "tipo": "direction"})
    assert r.json()["result"]["tipo"] == "direcao"


def test_export(client):
    r = client.post("/api/v1/exports/cif", json={"nome": "Fe"})
    assert "_cell_length_a                    2.86" in r.json()["result"]["content"]


def test_limite_de_corpo_413(client):
    r = client.post("/api/v1/crystallography/cells", content=b"x" * 2_000_000,
                    headers={"content-type": "application/json"})
    assert r.status_code == 413 and r.json()["code"] == "CORPO_GRANDE_DEMAIS"


def test_erro_interno_nao_vaza_detalhes():
    app = create_app(Settings(_env_file=None))

    @app.get("/explode")
    def explode():
        raise ValueError("segredo interno")

    r = TestClient(app, raise_server_exceptions=False).get("/explode")
    corpo = r.json()
    assert r.status_code == 500 and "segredo" not in r.text
    assert corpo["correlation_id"] and corpo["request_id"] == corpo["correlation_id"]


def test_health(client):
    assert client.get("/health").json()["version"] == __version__
    pronto = client.get("/health/ready").json()
    assert pronto["status"] == "ready" and all(pronto["checks"].values())


def test_docs_desligadas_em_producao():
    app = create_app(_producao(), motor_banco=None)
    cliente = TestClient(app)
    assert cliente.get("/api/v1/docs").status_code == 404
    assert cliente.get("/api/v1/openapi.json").status_code == 404


# --------------------------------------------------------------- aliases /v1
@pytest.mark.parametrize(("metodo", "alias", "canonica", "corpo"), ROTAS_ALIAS)
def test_alias_responde_igual_e_aponta_a_sucessora(client, metodo, alias, canonica, corpo):
    antigo = _chamar(client, metodo, alias, corpo)
    novo = _chamar(client, metodo, canonica, corpo)
    assert antigo.status_code == novo.status_code == 200
    assert antigo.headers["deprecation"] == "true"
    assert antigo.headers["link"] == f'<{canonica}>; rel="successor-version"'
    assert "deprecation" not in novo.headers
    a, b = antigo.json()["result"], novo.json()["result"]
    if isinstance(a, dict):
        a.pop("procedencia", None), b.pop("procedencia", None)   # só 'calculado_em' muda
    assert a == b


def test_alias_cif_ainda_existe(client):
    assert client.post("/v1/export/cif", json={"nome": "Cu"}).headers["deprecation"] == "true"


# --------------------------------------------------------------- recursos novos
def test_celula_traz_passos_e_procedencia(client):
    r = client.post("/api/v1/crystallography/cells", json={"nome": "Ti"}).json()["result"]
    assert r["a_fonte"] == "medido" and r["passos_parametro"] and r["passos_fea"]
    assert r["procedencia"]["classe"] == "analitico" and r["procedencia"]["calculado_em"]


def test_a_informado(client):
    r = client.post("/api/v1/crystallography/cells", json={"nome": "CFC", "a": "0,40"}).json()["result"]
    assert r["a_fonte"] == "informado" and r["a_nm"] == pytest.approx(0.40)


def test_miller_planar_e_familia(client):
    r = client.post("/api/v1/crystallography/miller",
                    json={"estrutura": "CFC", "indices": [1, 1, 1], "supercelula": 3}).json()["result"]
    assert r["planar"]["validado"] is True and r["planar"]["fracao_planar"] == pytest.approx(0.9069, abs=1e-4)
    assert len(r["familia"]) == 8


def test_supercelula(client):
    r = client.post("/api/v1/crystallography/supercells", json={"estrutura": "CFC", "n": 3}).json()["result"]
    assert len(r["atomos"]) == 172 and len(r["arestas"]) == 12 and r["vetores_rede"][0] == [1.0, 0.0, 0.0]


def test_solucao_solida_e_termico_em_dev(client):
    liga = client.post("/api/v1/crystallography/solid-solutions",
                       json={"base": "Cu", "soluto": "Ni", "x": 30}).json()["result"]
    assert [r["ok"] for r in liga["regras"]] == [True, True, True, True]
    termico = client.post("/api/v1/thermodynamics/thermal",
                          json={"liga": {"base": "Cu", "soluto": "Ni", "x": 30}, "temperatura_c": 500})
    assert termico.status_code == 200 and termico.json()["result"]["procedencia"]["classe"] == "estimativa_modelo"


def test_termico_exige_material_ou_liga(client):
    r = client.post("/api/v1/thermodynamics/thermal", json={"temperatura_c": 10})
    assert r.status_code == 422


def test_hea_analise_calcula_so_o_que_tem_base(client):
    corpo = {"nome": "CoCrFeNi", "composicao": {"Co": 1, "Cr": 1, "Fe": 1, "Ni": 1}}
    r = client.post("/api/v1/hea/analyses", json=corpo)
    assert r.status_code == 200, r.text
    res = r.json()["result"]
    assert res["dS"] == pytest.approx(8.314462618 * 1.3862944, abs=1e-3)   # R·ln 4
    assert res["dH"] is None and res["omega"] is None and "dH" in res["indisponiveis"]
    assert res["VEC"] == pytest.approx(8.25) and res["estrutura_sugerida"] == "CFC"
    assert res["veredito"].startswith("INCONCLUSIVO") and res["gibbs"] == []
    assert res["procedencia"]["classe"] == "estimativa_modelo" and res["procedencia"]["motor"] == "hea"


def test_hea_bootstrap_e_erros(client):
    boot = client.get("/api/v1/hea/bootstrap").json()["result"]
    assert "CoCrFeNi" in boot["alloys"] and boot["reference"]["delta"] == 6.6 and boot["reference"]["dH"] is None
    assert client.post("/api/v1/hea/analyses", json={"composicao": {"Fe": 1}}).status_code == 422
    r = client.post("/api/v1/hea/analyses", json={"composicao": {"Fe": 1, "Xx": 1}})
    assert r.status_code == 200 and r.json()["result"]["delta"] is None   # elemento sem dados → δ indisponível
    assert "Xx" in r.json()["result"]["indisponiveis"]["delta"]
    assert client.post("/api/v1/hea/predictions", json={}).status_code == 404


def test_request_id_do_cliente_e_respeitado(client):
    r = client.post("/api/v1/crystallography/cells", json={"nome": "Xx"}, headers={"X-Request-ID": "teste-12345678"})
    assert r.headers["x-request-id"] == "teste-12345678" and r.json()["request_id"] == "teste-12345678"
    r = client.get("/health", headers={"X-Request-ID": "<script>"})
    assert r.headers["x-request-id"] != "<script>"


def test_cabecalhos_de_seguranca(client):
    r = client.get("/api/v1/crystallography/structures")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in r.headers["content-security-policy"]


# --------------------------------------------------------------- produção (política no servidor)
@pytest.fixture(scope="module")
def producao(tmp_path_factory):
    """Produção realista: banco migrado pelo Alembic e com o seed carregado (não um banco vazio)."""
    url = f"sqlite:///{tmp_path_factory.mktemp('prod') / 'alloy.db'}"
    preparar_banco(url)
    return TestClient(create_app(_producao(database_url=url)), raise_server_exceptions=False)


def test_producao_recusa_dado_em_rascunho_com_422(producao):
    r = producao.post("/api/v1/thermodynamics/thermal", json={"material": "Fe", "temperatura_c": 500})
    assert r.status_code == 422 and r.json()["code"] == "DADO_NAO_VALIDADO"
    r = producao.post("/api/v1/crystallography/solid-solutions", json={"base": "Fe", "soluto": "C", "x": 2})
    assert r.status_code == 422 and r.json()["code"] == "DADO_NAO_VALIDADO"


def test_producao_liga_substitucional_sai_com_regras_indisponiveis(producao):
    r = producao.post("/api/v1/crystallography/solid-solutions", json={"base": "Cu", "soluto": "Ni", "x": 30})
    regras = {x["criterio"]: x for x in r.json()["result"]["regras"]}
    assert r.status_code == 200 and regras["Eletronegatividade"]["ok"] is None


def test_producao_capacidades(producao):
    cap = producao.get("/api/v1/meta/capabilities").json()["result"]
    assert cap["ambiente"] == "prod"
    assert all(cap[s]["demo_permitido"] is False for s in ("crystallography", "thermodynamics", "hea", "ia"))
    assert cap["thermodynamics"]["disponivel"] is False and cap["hea"]["disponivel"] is True
    assert "Parcial" in cap["hea"]["motivo"]


def test_producao_hea_so_entropia(producao):
    """Em produção nenhum dado validado existe ainda: só ΔS_mix (sem dados) sai; o resto, com motivo."""
    r = producao.post("/api/v1/hea/analyses", json={"composicao": {"Al": 1, "Co": 1, "Cr": 1, "Fe": 1, "Ni": 1}})
    assert r.status_code == 200, r.text
    res = r.json()["result"]
    assert res["dS"] == pytest.approx(13.3816, abs=1e-3)
    assert res["delta"] is None and res["VEC"] is None and res["Tm"] is None
    assert {"delta", "VEC", "Tm", "dH", "omega"} <= set(res["indisponiveis"])
    assert res["procedencia"]["dados_usados"] == []


def test_rate_limit_429():
    app = create_app(Settings(_env_file=None, rate_limit=True, rate_limit_requests=3))
    cliente = TestClient(app)
    codigos = [cliente.get("/api/v1/crystallography/structures").status_code for _ in range(4)]
    assert codigos == [200, 200, 200, 429]


# --------------------------------------------------------------- OpenAPI
def test_openapi_documenta_rotas_e_procedencia(client):
    esquema = client.get("/api/v1/openapi.json").json()
    caminhos = set(esquema["paths"])
    for rota in ("/api/v1/crystallography/cells", "/api/v1/crystallography/miller",
                 "/api/v1/crystallography/solid-solutions", "/api/v1/thermodynamics/thermal",
                 "/api/v1/exports/cif", "/api/v1/meta/capabilities", "/v1/crystals/structure"):
        assert rota in caminhos, rota
    assert "Procedencia" in esquema["components"]["schemas"]
    assert esquema["paths"]["/v1/crystals/structure"]["post"]["deprecated"] is True
