"""Linha de comando: ``python -m crystalab [--open] [--port 8010] [--reload]`` (achado BE-11)."""

from __future__ import annotations

import argparse
import socket
import threading
import time
import webbrowser

from . import __version__
from .modulo import MANIFESTO


def _encontrar_porta_livre(host: str, preferida: int, tentativas: int = 50) -> int:
    for porta in range(preferida, preferida + tentativas):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as teste:
            try:
                teste.bind((host, porta))
            except OSError:
                continue
            return porta
    raise SystemExit(f"Nenhuma porta livre entre {preferida} e {preferida + tentativas - 1}.")


def _abrir_quando_pronto(host: str, porta: int, url: str, limite_s: float = 20.0) -> None:
    """Abre o navegador só depois que o servidor aceitar conexões (antes havia corrida)."""
    alvo = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    fim = time.monotonic() + limite_s
    while time.monotonic() < fim:
        try:
            with socket.create_connection((alvo, porta), timeout=0.5):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.2)


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m crystalab", description=f"{MANIFESTO.nome} {__version__}")
    parser.add_argument("--host", default="127.0.0.1", help="host de bind (padrão: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=MANIFESTO.porta_padrao,
                        help=f"porta inicial (padrão {MANIFESTO.porta_padrao}; busca a próxima livre)")
    parser.add_argument("--open", action="store_true", help="abrir a UI no navegador quando o servidor subir")
    parser.add_argument("--reload", action="store_true", help="recarregar ao editar o código (desenvolvimento)")
    parser.add_argument("--log-level", default="info",
                        choices=["critical", "error", "warning", "info", "debug", "trace"])
    args = parser.parse_args()

    import uvicorn

    porta = _encontrar_porta_livre(args.host, args.port)
    url = f"http://{'127.0.0.1' if args.host in ('0.0.0.0', '::') else args.host}:{porta}"
    print(f"{MANIFESTO.nome} {__version__} disponível em {url}")
    print(f"Documentação interativa (Swagger UI): {url}/docs")
    print("Use Ctrl+C para encerrar.")
    if args.open:
        threading.Thread(target=_abrir_quando_pronto, args=(args.host, porta, url), daemon=True).start()

    # Import string + factory: permite --reload e múltiplos workers (antes uvicorn.run(app)).
    uvicorn.run(MANIFESTO.fabrica_app, factory=True, host=args.host, port=porta,
                log_level=args.log_level, reload=args.reload)


if __name__ == "__main__":
    main()
