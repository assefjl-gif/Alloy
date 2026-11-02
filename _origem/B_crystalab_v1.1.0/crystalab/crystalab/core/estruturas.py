"""Definição dos tipos de estrutura (CS, CCC, CFC, HC).

Isto é modelo cristalográfico (geometria e simetria), não dado de material:
fica em código. Os dados de materiais ficam em ``core/dados/metais.json``.
"""

from __future__ import annotations

import math
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from .constantes import SQRT2, SQRT3

ESTRUTURAS: Dict[str, Dict[str, Any]] = {
    "CS": {
        "nome": "Cúbica Simples", "sistema": "cubico",
        "n": 1, "nc": 6, "z": 1,
        "a_em_R": 2.0, "relacao": "a = 2R", "substituicao": "2 × {R}",
        "contato": "aresta do cubo",
        # Base cristalográfica (sítios únicos em [0,1)) no referencial do motor.
        "base": [((0.0, 0.0, 0.0), "vertice")],
        "grupo_espacial": {"hm": "P m -3 m", "numero": 221, "rede": "P",
                           "wyckoff": "1a", "sitio": (0.0, 0.0, 0.0)},
    },
    "CCC": {
        "nome": "Cúbica de Corpo Centrado", "sistema": "cubico",
        "n": 2, "nc": 8, "z": 2,
        "a_em_R": 4.0 / SQRT3, "relacao": "a = 4R/√3", "substituicao": "4 × {R} / √3",
        "contato": "diagonal do cubo",
        "base": [((0.0, 0.0, 0.0), "vertice"), ((0.5, 0.5, 0.5), "centro")],
        "grupo_espacial": {"hm": "I m -3 m", "numero": 229, "rede": "I",
                           "wyckoff": "2a", "sitio": (0.0, 0.0, 0.0)},
    },
    "CFC": {
        "nome": "Cúbica de Face Centrada", "sistema": "cubico",
        "n": 4, "nc": 12, "z": 4,
        "a_em_R": 2.0 * SQRT2, "relacao": "a = 2R√2", "substituicao": "2 × {R} × √2",
        "contato": "diagonal da face",
        "base": [((0.0, 0.0, 0.0), "vertice"), ((0.5, 0.5, 0.0), "face"),
                 ((0.5, 0.0, 0.5), "face"), ((0.0, 0.5, 0.5), "face")],
        "grupo_espacial": {"hm": "F m -3 m", "numero": 225, "rede": "F",
                           "wyckoff": "4a", "sitio": (0.0, 0.0, 0.0)},
    },
    "HC": {
        "nome": "Hexagonal Compacta", "sistema": "hexagonal",
        # n = 6 refere-se ao prisma hexagonal desenhado (3 células primitivas);
        # z = 2 é o conteúdo da célula primitiva hexagonal usada no CIF.
        "n": 6, "nc": 12, "z": 2,
        "a_em_R": 2.0, "relacao": "a = 2R", "substituicao": "2 × {R}",
        "contato": "aresta do hexágono basal",
        "c_a_ideal": math.sqrt(8.0 / 3.0),
        "base": [((0.0, 0.0, 0.0), "basal"), ((2.0 / 3.0, 1.0 / 3.0, 0.5), "interior")],
        "grupo_espacial": {"hm": "P 63/m m c", "numero": 194, "rede": "P",
                           "wyckoff": "2c", "sitio": (1.0 / 3.0, 2.0 / 3.0, 0.25)},
    },
}

ALIASES_ESTRUTURA: Dict[str, str] = {
    "CS": "CS", "SC": "CS", "CUBICASIMPLES": "CS",
    "CCC": "CCC", "BCC": "CCC", "CUBICADECORPOCENTRADO": "CCC",
    "CFC": "CFC", "FCC": "CFC", "CUBICADEFACECENTRADA": "CFC",
    "HC": "HC", "HCP": "HC", "HEXAGONALCOMPACTA": "HC",
}

FRACOES: Dict[str, Any] = {
    "vertice": {"CS": (1 / 8, "1/8"), "CCC": (1 / 8, "1/8"), "CFC": (1 / 8, "1/8"), "HC": (1 / 6, "1/6")},
    "centro": (1.0, "1"),
    "face": (0.5, "1/2"),
    "basal": (0.5, "1/2"),
    "interior": (1.0, "1"),
}

ROTULOS_TIPO: Dict[str, str] = {
    "vertice": "Vértices",
    "centro": "Centro do cubo",
    "face": "Centros de face",
    "basal": "Centros basais",
    "interior": "Interior",
}


def sem_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn").strip().lower()


def normalizar_estrutura(texto: Optional[str]) -> Optional[str]:
    chave = sem_acentos(str(texto or "")).upper().replace(" ", "")
    return ALIASES_ESTRUTURA.get(chave)


def fracao(estrutura: str, tipo: str) -> Tuple[float, str]:
    regra = FRACOES[tipo]
    return regra[estrutura] if isinstance(regra, dict) else regra


def c_a_ideal() -> float:
    return float(ESTRUTURAS["HC"]["c_a_ideal"])


def lista_siglas() -> List[str]:
    return list(ESTRUTURAS)
