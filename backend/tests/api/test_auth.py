"""Contas e sessões pela API real, com banco migrado (ADR-008, RQ-SEG-01..06)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import create_app
from app.models import ExecucaoCalculo, Sessao
from app.security.tokens import COOKIE_SESSAO

from .banco import preparar_banco

SENHA = "cristal-cubico-2026"


@pytest.fixture(scope="module")
def motor(tmp_path_factory):
    url = f"sqlite:///{tmp_path_factory.mktemp('auth') / 'alloy.db'}"
    preparar_banco(url)
    return create_engine(url)


@pytest.fixture
def app(motor):
    # Ambiente "test": cookie Secure → o cliente usa https://; rate limit desligado para não interferir.
    return create_app(Settings(_env_file=None, env="test", rate_limit=False), motor_banco=motor)


def _cliente(app) -> TestClient:
    return TestClient(app, base_url="https://testserver", raise_server_exceptions=False)


_contador = iter(range(10_000))


def _conta(app, nome="Estudante Teste"):
    email = f"pessoa{next(_contador)}@exemplo.test"
    r = _cliente(app).post("/api/v1/auth/register", json={"nome": nome, "email": email, "senha": SENHA})
    assert r.status_code == 201, r.text
    return email


def _logado(app, email):
    cliente = _cliente(app)
    r = cliente.post("/api/v1/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == 200, r.text
    return cliente, r.json()["result"]["csrf"], r


def test_cadastro_valida_senha_e_duplicidade(app):
    c = _cliente(app)
    fraca = c.post("/api/v1/auth/register", json={"nome": "Ana", "email": "ana@exemplo.test", "senha": "1234567890"})
    assert fraca.status_code == 400 and "comum" in fraca.json()["error"]
    curta = c.post("/api/v1/auth/register", json={"nome": "Ana", "email": "ana@exemplo.test", "senha": "curta"})
    assert curta.status_code == 400
    invalido = {"nome": "Ana", "email": "nao-e-email", "senha": SENHA}
    assert c.post("/api/v1/auth/register", json=invalido).status_code == 422
    email = _conta(app)
    dup = c.post("/api/v1/auth/register", json={"nome": "Outra", "email": email.upper(), "senha": SENHA})
    assert dup.status_code == 409 and dup.json()["code"] == "CONFLITO"


def test_login_cookie_seguro_e_token_so_no_cookie(app, motor):
    email = _conta(app)
    _, csrf, r = _logado(app, email)
    cookie = r.headers["set-cookie"]
    for atributo in ("HttpOnly", "Secure", "Path=/api", "SameSite=lax"):
        assert atributo.lower() in cookie.lower(), atributo
    token = r.cookies[COOKIE_SESSAO]
    assert token not in r.text and csrf and len(token) >= 40
    assert r.headers["cache-control"] == "no-store"
    with Session(motor) as s:   # o banco guarda só o hash (32 bytes), nunca o token
        assert all(len(x.token_sha256) == 32 and token.encode() not in x.token_sha256
                   for x in s.scalars(select(Sessao)))


def test_login_errado_nao_revela_se_a_conta_existe(app):
    email = _conta(app)
    c = _cliente(app)
    senha_errada = c.post("/api/v1/auth/login", json={"email": email, "senha": "outra-senha-qualquer"})
    inexistente = c.post("/api/v1/auth/login", json={"email": "ninguem@exemplo.test", "senha": SENHA})
    assert senha_errada.status_code == inexistente.status_code == 401
    assert senha_errada.json()["error"] == inexistente.json()["error"]


def test_bloqueio_progressivo_por_conta(app):
    email = _conta(app)
    c = _cliente(app)
    for _ in range(5):
        assert c.post("/api/v1/auth/login", json={"email": email, "senha": "senha-errada-x"}).status_code == 401
    r = c.post("/api/v1/auth/login", json={"email": email, "senha": SENHA})   # até a senha certa é barrada
    assert r.status_code == 429 and r.json()["code"] == "MUITAS_TENTATIVAS"


def test_me_renova_csrf_e_exige_sessao(app):
    assert _cliente(app).get("/api/v1/auth/me").status_code == 401
    cliente, csrf, _ = _logado(app, _conta(app, "Bea Souza"))
    me = cliente.get("/api/v1/auth/me")
    assert me.status_code == 200 and me.json()["result"]["usuario"]["nome"] == "Bea Souza"
    novo = me.json()["result"]["csrf"]
    assert novo != csrf
    corpo = {"nome": "Fe"}
    assert cliente.post("/api/v1/crystallography/cells", json=corpo, headers={"X-Alloy-CSRF": csrf}).status_code == 403
    assert cliente.post("/api/v1/crystallography/cells", json=corpo, headers={"X-Alloy-CSRF": novo}).status_code == 200


def test_csrf_obrigatorio_com_cookie_e_historico_pessoal(app):
    cliente, csrf, _ = _logado(app, _conta(app))
    sem = cliente.post("/api/v1/crystallography/cells", json={"nome": "Cu"})
    assert sem.status_code == 403 and sem.json()["code"] == "CSRF_INVALIDO"
    h = {"X-Alloy-CSRF": csrf}
    assert cliente.post("/api/v1/crystallography/cells", json={"nome": "Cu"}, headers=h).status_code == 200
    assert cliente.post("/api/v1/hea/analyses", json={"composicao": {"Co": 1, "Ni": 1}}, headers=h).status_code == 200
    hist = cliente.get("/api/v1/me/history").json()["result"]
    assert hist["total"] == 2 and [i["operacao"] for i in hist["itens"]] == ["hea_analise", "celula"]
    assert hist["itens"][1]["parametros"] == {"nome": "Cu"}


def test_historico_isolado_entre_usuarios_e_anonimo_nao_grava(app, motor):
    ana, csrf_ana, _ = _logado(app, _conta(app))
    bia, _, _ = _logado(app, _conta(app))
    ana.post("/api/v1/crystallography/cells", json={"nome": "Mg"}, headers={"X-Alloy-CSRF": csrf_ana})
    assert bia.get("/api/v1/me/history").json()["result"]["total"] == 0
    with Session(motor) as s:
        antes = len(s.scalars(select(ExecucaoCalculo)).all())
    assert _cliente(app).post("/api/v1/crystallography/cells", json={"nome": "Mg"}).status_code == 200
    with Session(motor) as s:
        assert len(s.scalars(select(ExecucaoCalculo)).all()) == antes


def test_logout_revoga_e_logout_all_encerra_todas(app):
    email = _conta(app)
    a, csrf_a, _ = _logado(app, email)
    b, _, _ = _logado(app, email)
    c, csrf_c, _ = _logado(app, email)
    assert a.post("/api/v1/auth/logout", headers={"X-Alloy-CSRF": csrf_a}).status_code == 200
    assert a.get("/api/v1/auth/me").status_code == 401
    assert b.get("/api/v1/auth/me").status_code == 200
    r = c.post("/api/v1/auth/logout-all", headers={"X-Alloy-CSRF": csrf_c})
    assert r.status_code == 200 and r.json()["result"]["encerradas"] == 2
    assert b.get("/api/v1/auth/me").status_code == 401


def test_sessao_expira_por_inatividade_e_por_idade(app, motor):
    for campo, delta in (("ultimo_uso_em", timedelta(days=8)), ("expira_em", timedelta(seconds=1))):
        cliente, _, r = _logado(app, _conta(app))
        assert cliente.get("/api/v1/auth/me").status_code == 200
        with Session(motor) as s:
            alvo = datetime.now(timezone.utc) - delta
            s.execute(update(Sessao).where(Sessao.revogada_em.is_(None)).values(**{campo: alvo}))
            s.commit()
        assert cliente.get("/api/v1/auth/me").status_code == 401, campo


def test_cookie_forjado_e_rejeitado(app):
    c = _cliente(app)
    c.cookies.set(COOKIE_SESSAO, "token-inventado", domain="testserver", path="/api")
    assert c.get("/api/v1/auth/me").status_code == 401


def test_sem_banco_contas_ficam_indisponiveis():
    c = TestClient(create_app(Settings(_env_file=None)), raise_server_exceptions=False)
    r = c.post("/api/v1/auth/register", json={"nome": "Ana", "email": "ana@exemplo.test", "senha": SENHA})
    assert r.status_code == 503 and r.json()["code"] == "CAPACIDADE_INDISPONIVEL"
    assert c.get("/api/v1/meta/capabilities").json()["result"]["autenticacao"]["disponivel"] is False
