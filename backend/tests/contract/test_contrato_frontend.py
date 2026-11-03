"""Contrato API ↔ frontend com servidor HTTP real (uvicorn) e os schemas Zod do frontend.

Pulado se Node ou as dependências do frontend não estiverem instaladas (ex.: CI só de backend).
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from app.core.config import Settings
from app.main import create_app

RAIZ = Path(__file__).resolve().parents[3]
FRONTEND = RAIZ / "_origem" / "C_alloy_frontend" / "alloy-frontend"   # Fase 5: passa a ser RAIZ / "frontend"
TSX = FRONTEND / "node_modules" / ".bin" / ("tsx.cmd" if shutil.which("cmd") else "tsx")


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servidor():
    porta = _porta_livre()
    config = uvicorn.Config(create_app(Settings(_env_file=None)), host="127.0.0.1", port=porta, log_level="warning")
    servidor = uvicorn.Server(config)
    fio = threading.Thread(target=servidor.run, daemon=True)
    fio.start()
    for _ in range(100):
        if servidor.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{porta}"
    servidor.should_exit = True
    fio.join(timeout=5)


@pytest.mark.skipif(not TSX.exists() or shutil.which("node") is None,
                    reason="Node ou dependências do frontend ausentes (npm install no frontend)")
def test_respostas_reais_aceitas_pelos_schemas_do_frontend(servidor):
    processo = subprocess.run(  # noqa: S603 — argumentos fixos do próprio repositório
        [str(TSX), str(RAIZ / "scripts" / "contrato_frontend.mts"), servidor, str(FRONTEND)],
        cwd=RAIZ, capture_output=True, text=True, timeout=120, encoding="utf-8")
    saida = processo.stdout + processo.stderr
    print(saida)  # contagem visível no log do CI
    assert processo.returncode == 0, saida
    assert "respostas aceitas pelos schemas do frontend" in saida
