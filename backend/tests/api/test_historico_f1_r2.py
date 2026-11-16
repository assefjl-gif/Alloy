"""R2-BE-03 / F-1: cálculo autenticado pela API HTTP real sobre banco PREEXISTENTE.

"Preexistente" = banco carregado antes desta rodada: a tabela ``motores`` tem versões antigas, não as de
agora (crystallography 2.1.0, thermodynamics 2.0.0, hea 2.0.0). Antes da correção, a inserção em
``execucoes_calculo`` violava ``fk_execucoes_calculo_motor`` na mesma transação do cálculo e a requisição
devolvia HTTP 500. As chaves estrangeiras são impostas aqui (PRAGMA ligado por ``criar_motor_banco``).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import create_app
from app.models import ExecucaoCalculo, Motor
from app.repositories.motores import motores_do_catalogo
from app.services.provedor import criar_motor_banco

from .banco import preparar_banco

SENHA = "cristal-cubico-2026"
VERSAO_ANTIGA = "0.0.1-antes-R2"


@pytest.fixture
def motor(tmp_path):
    url = f"sqlite:///{tmp_path / 'preexistente.db'}"
    preparar_banco(url)
    motor = criar_motor_banco(Settings(_env_file=None, env="test", database_url=url))
    assert motor is not None
    with Session(motor) as s:   # simula o banco carregado antes destas entregas
        s.execute(delete(Motor))
        for codigo, _versao in motores_do_catalogo():
            s.add(Motor(codigo=codigo, versao=VERSAO_ANTIGA))
        s.commit()
    yield motor
    motor.dispose()


@pytest.fixture
def cliente(motor):
    app = create_app(Settings(_env_file=None, env="test", rate_limit=False), motor_banco=motor)
    return TestClient(app, base_url="https://testserver", raise_server_exceptions=False)


def _logado(cliente):
    email = "preexistente@exemplo.test"
    r = cliente.post("/api/v1/auth/register", json={"nome": "Estudante", "email": email, "senha": SENHA})
    assert r.status_code == 201, r.text
    r = cliente.post("/api/v1/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == 200, r.text
    return {"X-Alloy-CSRF": r.json()["result"]["csrf"]}


@pytest.mark.parametrize(("rota", "corpo"), [
    ("/api/v1/crystallography/cells", {"nome": "Cu"}),
    ("/api/v1/thermodynamics/thermal", {"material": "Fe", "temperatura_c": 500}),
    ("/api/v1/hea/analyses", {"composicao": {"Co": 1, "Ni": 1}}),
])
def test_calculo_autenticado_em_banco_preexistente_nao_da_500(cliente, motor, rota, corpo):
    cabecalhos = _logado(cliente)
    resposta = cliente.post(rota, json=corpo, headers=cabecalhos)
    assert resposta.status_code == 200, resposta.text
    historico = cliente.get("/api/v1/me/history").json()["result"]
    assert historico["total"] == 1
    with Session(motor) as s:
        execucao = s.scalars(select(ExecucaoCalculo)).one()
        assert s.get(Motor, (execucao.motor_codigo, execucao.motor_versao)) is not None
        assert s.get(Motor, (execucao.motor_codigo, VERSAO_ANTIGA)) is not None
