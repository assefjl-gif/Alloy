"""Auditoria de latência (input lag) entre a API e o banco de dados.

    python scripts/auditoria_latencia_banco.py --rotulo antes    # mede e salva var/latencia_antes.json
    python scripts/auditoria_latencia_banco.py --rotulo depois   # idem, depois de uma otimização
    python scripts/auditoria_latencia_banco.py --rotulo antes --sem-cache   # comportamento anterior, mesmas condições

O que é medido, por rota, em dois modos (sem banco = seed JSON; SQLite em arquivo, migrado e com seed):
* latência dentro do processo (TestClient: roteamento + validação + serviço + banco + serialização);
* latência por HTTP real (uvicorn em 127.0.0.1, conexão mantida): soma a pilha de rede local;
* número de comandos SQL por requisição (evento ``before_cursor_execute`` do SQLAlchemy);
* custo isolado de montar o retrato dos dados (``RepositorioSQL``) e de listar a tabela periódica.
Percentis p50/p95/p99 sobre N amostras depois de um aquecimento. PostgreSQL não está disponível nesta
máquina: os números valem para SQLite e servem para comparar antes × depois, não como meta de produção.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import platform
import socket
import statistics
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))
os.environ.setdefault("ALLOY_ENV", "dev")

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

VAR = RAIZ / "var"
N, AQUECIMENTO = 300, 30
ROTAS = [
    ("GET", "/api/v1/crystallography/metals", None),
    ("POST", "/api/v1/crystallography/cells", {"nome": "Fe"}),
    ("POST", "/api/v1/crystallography/solid-solutions", {"base": "Cu", "soluto": "Ni", "x": 30, "n": 2}),
    ("POST", "/api/v1/thermodynamics/thermal", {"material": "Fe", "temperatura_c": 600}),
    ("POST", "/api/v1/hea/analyses", {"composicao": {"Co": 1, "Cr": 1, "Fe": 1, "Ni": 1}}),
    ("GET", "/api/v1/elements", None),
    ("GET", "/api/v1/elements/Fe", None),
    ("GET", "/health/ready", None),
]


def pct(amostras: list[float], p: float) -> float:
    s = sorted(amostras)
    return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))]


def resumo(amostras_ms: list[float]) -> dict:
    return {"p50": round(pct(amostras_ms, 50), 3), "p95": round(pct(amostras_ms, 95), 3),
            "p99": round(pct(amostras_ms, 99), 3), "media": round(statistics.fmean(amostras_ms), 3),
            "n": len(amostras_ms)}


def preparar_banco() -> str:
    from alembic import command
    from alembic.config import Config
    from app.repositories.seed_sql import carregar_seeds

    VAR.mkdir(exist_ok=True)
    arquivo = VAR / "auditoria_latencia.db"
    arquivo.unlink(missing_ok=True)
    url = f"sqlite:///{arquivo.as_posix()}"
    os.environ["DATABASE_URL"] = url
    command.upgrade(Config(str(RAIZ / "backend" / "alembic.ini")), "head")
    motor = create_engine(url)
    with Session(motor) as s:
        carregar_seeds(s)
        s.commit()
    motor.dispose()
    return url


def medir_in_process(app, contador) -> dict:
    from fastapi.testclient import TestClient

    cliente = TestClient(app)
    out = {}
    for metodo, rota, corpo in ROTAS:
        chamar = (lambda: cliente.get(rota)) if metodo == "GET" else (lambda: cliente.post(rota, json=corpo))
        for _ in range(AQUECIMENTO):
            assert chamar().status_code == 200, rota
        tempos, consultas = [], []
        for _ in range(N):
            antes = contador["n"]
            t0 = time.perf_counter()
            chamar()
            tempos.append((time.perf_counter() - t0) * 1000)
            consultas.append(contador["n"] - antes)
        out[f"{metodo} {rota}"] = {**resumo(tempos), "sql_por_req": round(statistics.fmean(consultas), 2)}
    return out


def medir_http(app) -> dict:
    import uvicorn

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=porta, log_level="error"))
    fio = threading.Thread(target=servidor.run, daemon=True)
    fio.start()
    while not servidor.started:
        time.sleep(0.02)
    out = {}
    try:
        conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=10)
        for metodo, rota, corpo in ROTAS:
            dados = json.dumps(corpo).encode() if corpo is not None else None
            cab = {"Content-Type": "application/json"} if dados else {}

            def chamar():
                conexao.request(metodo, rota, body=dados, headers=cab)
                r = conexao.getresponse()
                r.read()
                return r.status
            for _ in range(AQUECIMENTO):
                assert chamar() == 200, rota
            tempos = []
            for _ in range(N):
                t0 = time.perf_counter()
                chamar()
                tempos.append((time.perf_counter() - t0) * 1000)
            out[f"{metodo} {rota}"] = resumo(tempos)
        conexao.close()
    finally:
        servidor.should_exit = True
        fio.join(timeout=5)
    return out


def medir_componentes(url: str) -> dict:
    from app.repositories.elementos import RepositorioElementosSQL
    from app.repositories.materiais_sql import RepositorioSQL

    motor = create_engine(url)
    out = {}
    for nome, fabrica in (("RepositorioSQL(sessao) — retrato p/ cálculo", lambda s: RepositorioSQL(s)),
                          ("RepositorioElementosSQL.listar()", lambda s: RepositorioElementosSQL(s).listar())):
        tempos = []
        for i in range(AQUECIMENTO + N):
            with Session(motor) as s:
                t0 = time.perf_counter()
                fabrica(s)
                if i >= AQUECIMENTO:
                    tempos.append((time.perf_counter() - t0) * 1000)
        out[nome] = resumo(tempos)
    motor.dispose()
    return out


def desligar_cache() -> None:
    """Reproduz a versão anterior: retrato remontado a cada requisição (sem ``cache_dados``)."""
    from app.repositories.elementos import RepositorioElementosSQL
    from app.repositories.materiais_sql import RepositorioSQL
    from app.services import provedor

    provedor.retrato_materiais = RepositorioSQL
    provedor.retrato_elementos = RepositorioElementosSQL


def medir_ab(url: str) -> dict:
    """A/B intercalado no MESMO processo: cada amostra alterna retrato remontado (A, versão anterior) e
    retrato em cache (B). Neutraliza a variação da máquina entre execuções (CPU, outros processos)."""
    from app.core.config import Settings
    from app.main import create_app
    from app.repositories.elementos import RepositorioElementosSQL, retrato_elementos
    from app.repositories.materiais_sql import RepositorioSQL, retrato_materiais
    from app.services import provedor
    from fastapi.testclient import TestClient

    variantes = {"A_sem_cache": (RepositorioSQL, RepositorioElementosSQL),
                 "B_com_cache": (retrato_materiais, retrato_elementos)}
    motor = create_engine(url)
    contador = {"n": 0}
    event.listen(motor, "before_cursor_execute", lambda *a, **k: contador.__setitem__("n", contador["n"] + 1))
    cliente = TestClient(create_app(Settings(_env_file=None, env="dev", rate_limit=False), motor_banco=motor))
    out = {}
    try:
        for metodo, rota, corpo in ROTAS:
            def chamar():
                return cliente.get(rota) if metodo == "GET" else cliente.post(rota, json=corpo)
            tempos = {v: [] for v in variantes}
            consultas = {v: [] for v in variantes}
            for i in range(AQUECIMENTO + N):
                for nome, (mat, ele) in (variantes.items() if i % 2 else reversed(variantes.items())):
                    provedor.retrato_materiais, provedor.retrato_elementos = mat, ele
                    antes = contador["n"]
                    t0 = time.perf_counter()
                    assert chamar().status_code == 200, rota
                    if i >= AQUECIMENTO:
                        tempos[nome].append((time.perf_counter() - t0) * 1000)
                        consultas[nome].append(contador["n"] - antes)
            out[f"{metodo} {rota}"] = {nome: {**resumo(tempos[nome]),
                                              "sql_por_req": round(statistics.fmean(consultas[nome]), 2)}
                                       for nome in variantes}
    finally:
        provedor.retrato_materiais, provedor.retrato_elementos = retrato_materiais, retrato_elementos
        motor.dispose()
    return out


def medir(rotulo: str, sem_cache: bool = False) -> None:
    from app.core.config import Settings
    from app.main import create_app

    if sem_cache:
        desligar_cache()

    url = preparar_banco()
    resultado = {"rotulo": rotulo, "quando": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "ambiente": {"python": platform.python_version(), "so": platform.platform(),
                              "cpu": platform.processor() or platform.machine(), "n": N, "aquecimento": AQUECIMENTO},
                 "cache_retratos": not sem_cache}
    for modo in ("json", "sqlite"):
        contador = {"n": 0}
        motor = None
        if modo == "sqlite":
            motor = create_engine(url)
            event.listen(motor, "before_cursor_execute", lambda *a, **k: contador.__setitem__("n", contador["n"] + 1))
        app = create_app(Settings(_env_file=None, env="dev", rate_limit=False), motor_banco=motor)
        resultado[f"in_process_{modo}"] = medir_in_process(app, contador)
        resultado[f"http_{modo}"] = medir_http(app)
        if motor is not None:
            motor.dispose()
    resultado["componentes"] = medir_componentes(url)
    if not sem_cache:
        resultado["ab_intercalado_sqlite"] = medir_ab(url)
    destino = VAR / f"latencia_{rotulo}.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"salvo em {destino}")
    for chave in ("in_process_json", "in_process_sqlite"):
        print(chave)
        for rota, r in resultado[chave].items():
            print(f"  {rota:52s} p50 {r['p50']:7.2f}  p95 {r['p95']:7.2f}  p99 {r['p99']:7.2f} ms  SQL/req {r['sql_por_req']}")
    for rota, r in resultado.get("ab_intercalado_sqlite", {}).items():
        a, b = r["A_sem_cache"], r["B_com_cache"]
        print(f"  A/B {rota:48s} p50 {a['p50']:7.2f} -> {b['p50']:7.2f}  p95 {a['p95']:7.2f} -> {b['p95']:7.2f} ms"
              f"  SQL {a['sql_por_req']} -> {b['sql_por_req']}")
    print("componentes")
    for nome, r in resultado["componentes"].items():
        print(f"  {nome:52s} p50 {r['p50']:7.2f}  p95 {r['p95']:7.2f} ms")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rotulo", default="antes")
    ap.add_argument("--sem-cache", action="store_true")
    args = ap.parse_args()
    medir(args.rotulo, args.sem_cache)
