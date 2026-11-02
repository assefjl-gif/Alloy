"""Teste de fumaça da interface no navegador (Playwright) — critério 7.3 do relatório.

Rodar:  pip install playwright && playwright install chromium && pytest tests/test_ui_e2e.py
É ignorado automaticamente se o Playwright não estiver instalado.
"""

from __future__ import annotations

import socket
import threading
import time

import pytest

pytest.importorskip("fastapi")
sync_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def base_url():
    import uvicorn

    from crystalab.api import create_app

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    servidor = uvicorn.Server(uvicorn.Config(create_app(), host="127.0.0.1", port=porta, log_level="warning"))
    thread = threading.Thread(target=servidor.run, daemon=True)
    thread.start()
    for _ in range(100):
        if servidor.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{porta}/"
    servidor.should_exit = True
    thread.join(timeout=5)


def test_fluxo_basico(base_url):
    erros = []
    with sync_api.sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()
        pagina.on("pageerror", lambda e: erros.append(str(e)))
        pagina.goto(base_url)
        pagina.locator(".alloy-block[data-key=Cu]").click()
        for comando in ("plano 1 1 1", "calcular densidade"):
            pagina.fill("#terminalInput", comando)
            pagina.press("#terminalInput", "Enter")
            pagina.wait_for_timeout(400)
        log = pagina.locator("[data-testid=terminal-log]").inner_text()
        assert "Cu — Cobre" in log and "plano (1 1 1)" in log and "8,937 g/cm³" in log
        assert pagina.locator("#densitySteps .step").count() == 5
        assert "(CFC)" in pagina.locator("[data-testid=result-root] #structureVerdict").inner_text()
        navegador.close()
    assert erros == []
