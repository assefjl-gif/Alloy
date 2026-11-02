"""Gera database/seeds/cristalografia/propriedades_v14.json a partir do código da v1.4.

Os valores são COPIADOS do CrystaLab v1.4 (PROPRIEDADES_EXTRAS, INTERSTICIAIS, ALOTROPIA)
sem redigitação, e entram como ``rascunho`` e sem fonte: a v1.4 não registrou procedência
(achado CIE-03). Só alimentam o motor em produção depois de validados (ADR-014, Q-03).

Uso: .venv/Scripts/python scripts/gerar_seed_v14.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM_A = RAIZ / "_origem" / "A_crystalab_v1.4" / "crystalab" / "crystalab_modulo1_v1.4.py"
DESTINO = RAIZ / "database" / "seeds" / "cristalografia" / "propriedades_v14.json"

spec = importlib.util.spec_from_file_location("crystalab_v14", ORIGEM_A)
v14 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v14)

ORIGEM = "CrystaLab v1.4 (PROPRIEDADES_EXTRAS / INTERSTICIAIS / ALOTROPIA) — sem fonte registrada"


def valor(simbolo, codigo, numero, unidade):
    return {"simbolo": simbolo, "codigo": codigo, "valor": numero, "unidade": unidade,
            "estado": "rascunho", "fonte": None, "origem": ORIGEM}


valores = []
for simbolo, (_a, _c, alfa, fusao, chi, valencia, _cor) in sorted(v14.PROPRIEDADES_EXTRAS.items()):
    valores += [
        valor(simbolo, "coef_dilatacao_linear", alfa, "1e-6/K"),
        valor(simbolo, "temperatura_fusao", fusao, "°C"),
        valor(simbolo, "eletronegatividade", chi, "Pauling"),
        valor(simbolo, "valencia", valencia, "adimensional"),
    ]
intersticiais = []
for simbolo, dados in sorted(v14.INTERSTICIAIS.items()):
    intersticiais.append({"simbolo": simbolo, "nome": dados["nome"], "aliases": dados["aliases"]})
    valores += [
        valor(simbolo, "raio_atomico", dados["raio"], "nm"),
        valor(simbolo, "massa_atomica", dados["peso"], "g/mol"),
        valor(simbolo, "eletronegatividade", dados["eletroneg"], "Pauling"),
    ]
transicoes = [
    {"simbolo": s, "de_c": de, "ate_c": ate, "fase": fase, "estrutura": est, "estado": "rascunho", "fonte": None}
    for s, faixas in sorted(v14.ALOTROPIA.items()) for de, ate, fase, est in faixas
]
cores = {s: dados[6] for s, dados in sorted(v14.PROPRIEDADES_EXTRAS.items())}
cores.update({s: d["cor"] for s, d in v14.INTERSTICIAIS.items()})

DESTINO.write_text(json.dumps({
    "versao_dados": "2026.11.1-v14",
    "descricao": "Dados introduzidos pela v1.4. TODOS em rascunho até validação humana com fonte (Q-03).",
    "valores": valores,
    "intersticiais": intersticiais,
    "transicoes_alotropicas": transicoes,
    "cores_padrao": {"esquema": "Jmol/CPK (convenção de visualização, não dado científico)", "cores": cores},
}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"{len(valores)} valores, {len(intersticiais)} intersticiais, {len(transicoes)} transições → {DESTINO.relative_to(RAIZ)}")
