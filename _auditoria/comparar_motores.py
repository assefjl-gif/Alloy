"""Auditoria (Fase 1): compara os motores científicos das bases A, B e D com as mesmas entradas.

A = crystalab_modulo1_v1.4.py (arquivo único, contém ligas/temperatura/planar)
B = crystalab/core (v1.1.0, modular, base da API FastAPI)
D = crystalab_modulo1.py (v1.0; idêntico a C/legacy, motor usado pelo frontend C)

Uso: .venv/Scripts/python _auditoria/comparar_motores.py
Nada nas bases de origem é alterado: os módulos são carregados por caminho.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "_origem"


def carregar(nome: str, caminho: Path):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


A = carregar("motor_a", ORIGEM / "A_crystalab_v1.4" / "crystalab" / "crystalab_modulo1_v1.4.py")
D = carregar("motor_d", ORIGEM / "D_crystalab_modulo1" / "crystalab_modulo1.py")
sys.path.insert(0, str(ORIGEM / "B_crystalab_v1.1.0" / "crystalab"))
from crystalab.core import calcular_estrutura as b_estrutura, calcular_miller as b_miller  # noqa: E402

CAMPOS = ("estrutura", "a_nm", "c_nm", "fea", "densidade", "densidade_exp", "erro_percent")


def resumo(r: dict) -> dict:
    return {c: r.get(c) for c in CAMPOS}


def diferenca_relativa(x, y):
    if x is None or y is None:
        return None
    return abs(x - y) / abs(y) * 100 if y else abs(x - y)


relatorio = {"estruturas": [], "miller": [], "divergencias": []}
for simbolo in sorted(A.METAIS):
    ra, rb, rd = A.calcular_estrutura({"nome": simbolo}), b_estrutura({"nome": simbolo}), D.calcular_estrutura({"nome": simbolo})
    linha = {"metal": simbolo, "A": resumo(ra), "B": resumo(rb), "D": resumo(rd), "B_a_fonte": rb.get("a_fonte")}
    relatorio["estruturas"].append(linha)
    for campo in ("a_nm", "fea", "densidade"):
        valores = {k: linha[k][campo] for k in ("A", "B", "D")}
        if None in valores.values():
            continue
        maior = max(diferenca_relativa(valores[x], valores["B"]) for x in ("A", "D"))
        if maior > 0.01:
            relatorio["divergencias"].append({"metal": simbolo, "campo": campo, **{k: round(v, 6) for k, v in valores.items()}, "maior_dif_rel_pct": round(maior, 4)})

CASOS_MILLER = [
    ("CS", "plano", [1, 0, 0]), ("CCC", "plano", [1, 1, 0]), ("CFC", "plano", [1, 1, 1]), ("CFC", "plano", [1, 0, 0]),
    ("CFC", "plano", [2, 0, 0]), ("HC", "plano", [0, 0, 0, 1]), ("HC", "plano", [1, 0, -1, 1]),
    ("CCC", "direcao", [1, 1, 1]), ("CFC", "direcao", [1, 1, 0]), ("HC", "direcao", [2, -1, -1, 0]),
]
for estrutura, tipo, indices in CASOS_MILLER:
    payload = {"estrutura": estrutura, "tipo": tipo, "indices": indices}
    saidas = {}
    for rotulo, fn in (("A", A.calcular_miller), ("B", b_miller), ("D", D.calcular_miller)):
        try:
            r = fn(dict(payload))
            saidas[rotulo] = {
                "notacao": r.get("notacao"),
                "n_atomos_marcados": len(r.get("atomos", [])),
                "d_rel": r.get("d_rel"), "area_rel": r.get("area_rel"),
                "comprimento_rel": r.get("comprimento_rel"), "atomos_contados": r.get("atomos_contados"),
                "atomos_plano (planar)": r.get("atomos_plano"), "fracao_planar": r.get("fracao_planar"),
            }
        except Exception as erro:  # registra a falha em vez de interromper a comparação
            saidas[rotulo] = {"erro": f"{type(erro).__name__}: {erro}"}
    relatorio["miller"].append({"caso": f"{estrutura} {tipo} {indices}", **saidas})

saida = RAIZ / "_auditoria" / "comparacao_motores.json"
saida.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"{'metal':5} {'est':4} | {'a_nm A':>8} {'a_nm B':>8} {'a_nm D':>8} | {'ρ A':>7} {'ρ B':>7} {'ρ D':>7} {'ρ exp':>6} | B usa")
for l in relatorio["estruturas"]:
    a, b, d = l["A"], l["B"], l["D"]
    f = lambda v, n=4: "—" if v is None else f"{v:.{n}f}"  # noqa: E731
    print(f"{l['metal']:5} {a['estrutura']:4} | {f(a['a_nm'])} {f(b['a_nm'])} {f(d['a_nm'])} | {f(a['densidade'],3)} {f(b['densidade'],3)} {f(d['densidade'],3)} {f(a['densidade_exp'],2):>6} | {l['B_a_fonte']}")
print(f"\nDivergências > 0,01% entre motores: {len(relatorio['divergencias'])}")
for dv in relatorio["divergencias"]:
    print("  ", dv)
print("\nMiller (A | B | D):")
for m in relatorio["miller"]:
    partes = []
    for k in ("A", "B", "D"):
        s = m[k]
        if "erro" in s:
            partes.append(f"{k}: ERRO {s['erro'][:60]}")
        else:
            extra = f" planar={s['atomos_plano (planar)']}" if s.get("atomos_plano (planar)") is not None else ""
            partes.append(f"{k}: {s['notacao']} marcados={s['n_atomos_marcados']} d={s['d_rel'] and round(s['d_rel'],4)}{extra}")
    print(f"  {m['caso']:26} " + " | ".join(partes))
print(f"\nJSON completo: {saida.relative_to(RAIZ)}")
