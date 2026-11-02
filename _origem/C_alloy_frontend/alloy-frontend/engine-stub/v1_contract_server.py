"""Servidor de CONTRATO v1 — uso exclusivo em testes do front-end.

Por que existe
--------------
A versão FastAPI do CrystaLab (deepseek_python_20261012_784017.py) expõe as rotas
/v1/* e a exportação CIF/XYZ, mas o FastAPI e o pydantic-settings não podem ser
instalados neste ambiente (registro PyPI bloqueado, HTTP 403). Para testar o
adaptador v1 do front-end sem inventar respostas, este servidor:

  * importa o motor matemático ORIGINAL de legacy/crystalab_modulo1.py, sem alterá-lo;
  * reproduz, linha a linha, as funções puras `calcular_densidade`, `gerar_cif` e
    `gerar_xyz` da versão FastAPI (seções 5 e 6 do arquivo 784017);
  * responde nas mesmas rotas e com o mesmo envelope {ok, result} / {ok:false, error}.

Não é um back-end de produção. Não tem validação Pydantic, CORS, rate limit nem
OpenAPI. Fica fora do pacote entregue ao servidor.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "legacy"))

from crystalab_modulo1 import (  # noqa: E402  (motor original, sem modificações)
    calcular_estrutura,
    calcular_miller,
    metais_publicos,
    tabela_estruturas,
)


# ---- Seção 5 do arquivo FastAPI 784017 (cópia literal) -----------------------
def calcular_densidade(payload: Dict[str, Any]) -> Dict[str, Any]:
    resultado = calcular_estrutura(payload)
    return {
        "rotulo": resultado["rotulo"],
        "estrutura": resultado["estrutura"],
        "n": resultado["n"], "nc": resultado["nc"],
        "fea": resultado["fea"], "vazios": resultado["vazios"],
        "densidade": resultado["densidade"],
        "densidade_exp": resultado["densidade_exp"],
        "erro_percent": resultado["erro_percent"],
        "volume_cm3": resultado["volume_cm3"],
        "raio_nm": resultado["raio_nm"], "peso": resultado["peso"],
        "passos": resultado["passos_densidade"],
    }


# ---- Seção 6 do arquivo FastAPI 784017 (cópia literal) -----------------------
_ANGLES = {"CS": (90.0, 90.0, 90.0), "CCC": (90.0, 90.0, 90.0),
           "CFC": (90.0, 90.0, 90.0), "HC": (90.0, 90.0, 120.0)}


def _simbolo_quimico(resultado: Dict[str, Any]) -> str:
    if resultado.get("simbolo"):
        return resultado["simbolo"]
    return f"X{resultado['estrutura']}"


def gerar_cif(payload: Dict[str, Any]) -> Dict[str, Any]:
    resultado = calcular_estrutura(payload)
    simbolo = _simbolo_quimico(resultado)
    formula = payload.get("formula") or simbolo
    estrutura = resultado["estrutura"]

    if resultado["a_nm"] is None:
        raise ValueError("Informe raio atômico para exportar CIF com parâmetros de rede absolutos.")

    a = resultado["a_nm"]
    b = a
    if estrutura == "HC":
        c = resultado["c_nm"]
        alpha, beta, gamma = _ANGLES["HC"]
    else:
        c = a
        alpha, beta, gamma = _ANGLES[estrutura]

    lines = [
        f"data_crystalab_{simbolo.lower()}",
        "_audit_creation_method 'CrystaLab v1.0 (FastAPI)'",
        f"_chemical_formula_sum '{formula}'",
        f"_cell_length_a {a:.6f}",
        f"_cell_length_b {b:.6f}",
        f"_cell_length_c {c:.6f}",
        f"_cell_angle_alpha {alpha:.2f}",
        f"_cell_angle_beta {beta:.2f}",
        f"_cell_angle_gamma {gamma:.2f}",
        "_symmetry_space_group_name_H-M 'P 1'",
        "_symmetry_Int_Tables_number 1",
        "",
        "loop_",
        "_atom_site_label",
        "_atom_site_type_symbol",
        "_atom_site_fract_x",
        "_atom_site_fract_y",
        "_atom_site_fract_z",
        "_atom_site_occupancy",
    ]
    for idx, atomo in enumerate(resultado["atomos"], start=1):
        x, y, z = atomo["pos"]
        lines.append(f"{simbolo}{idx} {simbolo} {x:.6f} {y:.6f} {z:.6f} 1.0000")
    lines.append("")
    return {
        "formato": "cif",
        "filename": f"crystalab_{simbolo.lower()}_{estrutura.lower()}.cif",
        "content": "\n".join(lines),
        "content_type": "chemical/x-cif",
    }


def gerar_xyz(payload: Dict[str, Any]) -> Dict[str, Any]:
    resultado = calcular_estrutura(payload)
    simbolo = _simbolo_quimico(resultado)
    comentario = payload.get("comentario") or \
        f"CrystaLab · {resultado['rotulo']} · {resultado['estrutura']}"
    a_nm = resultado["a_nm"]
    escala = a_nm * 10.0 if a_nm else 1.0

    linhas = [str(len(resultado["atomos"])), comentario]
    for atomo in resultado["atomos"]:
        x, y, z = atomo["pos"]
        linhas.append(f"{simbolo} {x * escala:.6f} {y * escala:.6f} {z * escala:.6f}")

    return {
        "formato": "xyz",
        "filename": f"crystalab_{simbolo.lower()}_{resultado['estrutura'].lower()}.xyz",
        "content": "\n".join(linhas) + "\n",
        "content_type": "text/plain",
    }


ROTAS_POST = {
    "/v1/crystals/structure": calcular_estrutura,
    "/v1/crystallography/miller": calcular_miller,
    "/v1/calculations/density": calcular_densidade,
    "/v1/export/cif": gerar_cif,
    "/v1/export/xyz": gerar_xyz,
    "/api/estrutura": calcular_estrutura,
    "/api/miller": calcular_miller,
}


class Handler(BaseHTTPRequestHandler):
    server_version = "CrystaLabV1ContractStub/0.1"

    def log_message(self, format: str, *args: Any) -> None:  # silencioso nos testes
        return

    def _json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._json({"ok": True, "status": "healthy", "version": "1.0.0-contract-stub"})
        elif path == "/v1/crystals/metals":
            self._json({"ok": True, "result": metais_publicos()})
        elif path == "/v1/crystals/structures":
            self._json({"ok": True, "result": tabela_estruturas()})
        elif path == "/api/bootstrap":
            self._json({"metais": metais_publicos(), "estruturas": tabela_estruturas(), "inicial": calcular_estrutura({"nome": "Fe"})})
        else:
            self._json({"ok": False, "error": "Rota não encontrada."}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        funcao = ROTAS_POST.get(path)
        if funcao is None:
            self._json({"ok": False, "error": "Rota não encontrada."}, 404)
            return
        tamanho = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(tamanho).decode("utf-8") if tamanho else "{}")
        except json.JSONDecodeError:
            self._json({"ok": False, "error": "JSON inválido."}, 400)
            return
        if not isinstance(payload, dict):
            self._json({"ok": False, "error": "O corpo da requisição deve ser um objeto JSON."}, 400)
            return
        try:
            self._json({"ok": True, "result": funcao(payload)})
        except ValueError as erro:
            self._json({"ok": False, "error": str(erro)}, 400)


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor de contrato v1 (somente testes)")
    parser.add_argument("--port", type=int, default=8011)
    args = parser.parse_args()
    servidor = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"contrato v1 em http://127.0.0.1:{args.port}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
