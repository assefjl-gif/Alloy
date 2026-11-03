"""Questões com correção no servidor (RQ-EDU-01..04) e isolamento por instituição/usuário (ADR-009)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.educational.geradores import corrigir, gerar
from app.main import create_app
from app.models import InstanciaQuestao, Instituicao, Usuario, VinculoInstitucional
from app.repositories.materiais_json import repositorio_padrao

from .banco import preparar_banco

SENHA = "cristal-cubico-2026"


@pytest.fixture(scope="module")
def motor(tmp_path_factory):
    url = f"sqlite:///{tmp_path_factory.mktemp('edu') / 'alloy.db'}"
    preparar_banco(url)
    return create_engine(url)


@pytest.fixture(scope="module")
def app(motor):
    return create_app(Settings(_env_file=None, env="test", rate_limit=False), motor_banco=motor)


@pytest.fixture(scope="module")
def instituicao(motor):
    with Session(motor) as s:
        inst = Instituicao(nome="Universidade de Teste", sigla="UT")
        s.add(inst)
        s.commit()
        return inst.id


class Pessoa:
    def __init__(self, app, motor, papel=None, instituicao=None):
        self.email = f"p{uuid.uuid4().hex[:10]}@exemplo.test"
        self.c = TestClient(app, base_url="https://testserver", raise_server_exceptions=False)
        assert self.c.post("/api/v1/auth/register", json={"nome": "Pessoa Teste", "email": self.email,
                                                         "senha": SENHA}).status_code == 201
        if papel:
            with Session(motor) as s:
                uid = s.scalar(select(Usuario.id).where(Usuario.email == self.email))
                s.add(VinculoInstitucional(usuario_id=uid, instituicao_id=instituicao, papel=papel))
                s.commit()
        login = self.c.post("/api/v1/auth/login", json={"email": self.email, "senha": SENHA})
        self.h = {"X-Alloy-CSRF": login.json()["result"]["csrf"]}

    def post(self, url, corpo=None):
        return self.c.post(url, json=corpo or {}, headers=self.h)


def _questao(prof, instituicao, gerador="densidade_cubica", **extra):
    r = prof.post("/api/v1/edu/questions", {"gerador": gerador, "instituicao_id": str(instituicao), **extra})
    assert r.status_code == 201, r.text
    return r.json()["result"]


# ------------------------------------------------------------------ geradores (puros)
@pytest.mark.parametrize("gerador", ["densidade_cubica", "fea_estrutura", "espacamento_cubico"])
def test_gerador_reprodutivel_e_gabarito_do_motor(gerador):
    repo = repositorio_padrao()
    a, b = gerar(gerador, 1234, repo), gerar(gerador, 1234, repo)
    assert a == b
    assert corrigir(a.gabarito["valor"], a.gabarito) == (True, None)
    assert len({gerar(gerador, s, repo).publico["enunciado"] for s in range(30)}) > 1


def test_classificacao_de_erros():
    g = {"valor": 8.93, "tolerancia_relativa": 0.02}
    assert corrigir(8.93e3, g) == (False, "fator_10n") and corrigir(-8.93, g) == (False, "sinal")
    assert corrigir(4.0, g) == (False, "nao_classificado") and corrigir(8.80, g) == (True, None)


# ------------------------------------------------------------------ API
def test_estudante_nao_cria_questao_e_publica_exige_admin(app, motor, instituicao):
    aluno = Pessoa(app, motor, "estudante", instituicao)
    r = aluno.post("/api/v1/edu/questions", {"gerador": "fea_estrutura", "instituicao_id": str(instituicao)})
    assert r.status_code == 403
    prof = Pessoa(app, motor, "professor", instituicao)
    assert prof.post("/api/v1/edu/questions", {"gerador": "fea_estrutura"}).status_code == 403
    assert prof.post("/api/v1/edu/questions", {"gerador": "inexistente",
                                               "instituicao_id": str(instituicao)}).status_code == 400


def test_fluxo_completo_sem_vazar_gabarito(app, motor, instituicao):
    prof = Pessoa(app, motor, "professor", instituicao)
    q = _questao(prof, instituicao, max_tentativas=2)
    aluno = Pessoa(app, motor, "estudante", instituicao)
    assert q["id"] in [x["id"] for x in aluno.c.get("/api/v1/edu/questions").json()["result"]]

    inst = aluno.post(f"/api/v1/edu/questions/{q['id']}/instances")
    assert inst.status_code == 201
    corpo = inst.json()["result"]
    assert "gabarito" not in inst.text and "valor" not in corpo and inst.headers["cache-control"] == "no-store"
    with Session(motor) as s:
        gabarito = s.get(InstanciaQuestao, uuid.UUID(corpo["id"])).gabarito_calculado["valor"]

    errada = aluno.post(f"/api/v1/edu/instances/{corpo['id']}/attempts", {"resposta": gabarito * 1000})
    assert errada.json()["result"] == {"correta": False, "tentativa": 1, "restantes": 1, "tipo_erro": "fator_10n",
                                       "gabarito": None}
    com_virgula = f"{gabarito:.4f}".replace(".", ",")
    certa = aluno.post(f"/api/v1/edu/instances/{corpo['id']}/attempts", {"resposta": com_virgula})
    resultado = certa.json()["result"]
    assert resultado["correta"] is True and resultado["gabarito"]["valor"] == pytest.approx(gabarito)
    assert resultado["gabarito"]["resolucao"]   # passos do próprio motor
    assert aluno.post(f"/api/v1/edu/instances/{corpo['id']}/attempts", {"resposta": 1}).status_code == 409

    progresso = aluno.c.get("/api/v1/me/progress").json()["result"]
    assert progresso["resolvidas"] == 1 and progresso["instancias"] == 1
    assert {t["topico"] for t in progresso["topicos"]} == {"densidade", "celula_unitaria"}


def test_tentativas_esgotadas_liberam_gabarito(app, motor, instituicao):
    prof = Pessoa(app, motor, "professor", instituicao)
    q = _questao(prof, instituicao, gerador="fea_estrutura", max_tentativas=1)
    aluno = Pessoa(app, motor, "estudante", instituicao)
    inst = aluno.post(f"/api/v1/edu/questions/{q['id']}/instances").json()["result"]
    r = aluno.post(f"/api/v1/edu/instances/{inst['id']}/attempts", {"resposta": 0.1}).json()["result"]
    assert r["correta"] is False and r["restantes"] == 0 and r["gabarito"]["unidade"] == "adimensional"
    assert aluno.post(f"/api/v1/edu/instances/{inst['id']}/attempts", {"resposta": 0.74}).status_code == 409


def test_idor_instancia_de_outro_estudante_e_404(app, motor, instituicao):
    prof = Pessoa(app, motor, "professor", instituicao)
    q = _questao(prof, instituicao, gerador="espacamento_cubico")
    ana, bia = Pessoa(app, motor, "estudante", instituicao), Pessoa(app, motor, "estudante", instituicao)
    inst = ana.post(f"/api/v1/edu/questions/{q['id']}/instances").json()["result"]
    r = bia.post(f"/api/v1/edu/instances/{inst['id']}/attempts", {"resposta": 0.2})
    assert r.status_code == 404
    assert bia.post("/api/v1/edu/instances/nao-e-uuid/attempts", {"resposta": 0.2}).status_code == 404


def test_questao_de_outra_instituicao_e_invisivel(app, motor, instituicao):
    prof = Pessoa(app, motor, "professor", instituicao)
    q = _questao(prof, instituicao)
    with Session(motor) as s:
        outra = Instituicao(nome="Outra Universidade")
        s.add(outra)
        s.commit()
        outra_id = outra.id
    de_fora = Pessoa(app, motor, "estudante", outra_id)
    assert q["id"] not in [x["id"] for x in de_fora.c.get("/api/v1/edu/questions").json()["result"]]
    assert de_fora.post(f"/api/v1/edu/questions/{q['id']}/instances").status_code == 404
    r = de_fora.post("/api/v1/edu/questions", {"gerador": "fea_estrutura", "instituicao_id": str(instituicao)})
    assert r.status_code == 404   # não revela que a instituição existe


def test_exige_login_e_banco(app):
    anonimo = TestClient(app, base_url="https://testserver", raise_server_exceptions=False)
    assert anonimo.get("/api/v1/edu/questions").status_code == 401
    assert anonimo.get("/api/v1/edu/generators").status_code == 200
    sem_banco = TestClient(create_app(Settings(_env_file=None)), raise_server_exceptions=False)
    assert sem_banco.get("/api/v1/me/progress").status_code == 401
