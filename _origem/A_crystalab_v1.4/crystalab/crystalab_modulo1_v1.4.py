import argparse
import json
import math
import os
import random
import re
import socket
import threading
import unicodedata
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, quote, unquote, urlparse


N_AVOGADRO = 6.022e23
SQRT2 = math.sqrt(2.0)
SQRT3 = math.sqrt(3.0)
EPS = 1e-6
Vetor = Tuple[float, float, float]

# Raios atômicos, pesos atômicos e densidades experimentais (Callister, Tabela 3.1 e apêndices).
METAIS: Dict[str, Dict[str, Any]] = {
    "Fe": {"nome": "Ferro (α)", "estrutura": "CCC", "raio": 0.1241, "peso": 55.85, "densidade_exp": 7.87, "aliases": ["ferro", "iron"]},
    "Cr": {"nome": "Cromo", "estrutura": "CCC", "raio": 0.1249, "peso": 52.00, "densidade_exp": 7.19, "aliases": ["cromo", "chromium"]},
    "Mo": {"nome": "Molibdênio", "estrutura": "CCC", "raio": 0.1363, "peso": 95.94, "densidade_exp": 10.22, "aliases": ["molibdenio"]},
    "W": {"nome": "Tungstênio", "estrutura": "CCC", "raio": 0.1371, "peso": 183.84, "densidade_exp": 19.30, "aliases": ["tungstenio", "tungsten"]},
    "Cu": {"nome": "Cobre", "estrutura": "CFC", "raio": 0.1278, "peso": 63.55, "densidade_exp": 8.94, "aliases": ["cobre", "copper"]},
    "Al": {"nome": "Alumínio", "estrutura": "CFC", "raio": 0.1431, "peso": 26.98, "densidade_exp": 2.71, "aliases": ["aluminio", "aluminum"]},
    "Ni": {"nome": "Níquel", "estrutura": "CFC", "raio": 0.1246, "peso": 58.69, "densidade_exp": 8.90, "aliases": ["niquel", "nickel"]},
    "Ag": {"nome": "Prata", "estrutura": "CFC", "raio": 0.1445, "peso": 107.87, "densidade_exp": 10.49, "aliases": ["prata", "silver"]},
    "Au": {"nome": "Ouro", "estrutura": "CFC", "raio": 0.1442, "peso": 196.97, "densidade_exp": 19.32, "aliases": ["ouro", "gold"]},
    "Pb": {"nome": "Chumbo", "estrutura": "CFC", "raio": 0.1750, "peso": 207.20, "densidade_exp": 11.35, "aliases": ["chumbo", "lead"]},
    "Mg": {"nome": "Magnésio", "estrutura": "HC", "raio": 0.1600, "peso": 24.31, "densidade_exp": 1.74, "c_a": 1.624, "aliases": ["magnesio", "magnesium"]},
    "Ti": {"nome": "Titânio (α)", "estrutura": "HC", "raio": 0.1445, "peso": 47.87, "densidade_exp": 4.51, "c_a": 1.587, "aliases": ["titanio", "titanium"]},
    "Zn": {"nome": "Zinco", "estrutura": "HC", "raio": 0.1332, "peso": 65.41, "densidade_exp": 7.13, "c_a": 1.856, "aliases": ["zinco", "zinc"]},
    "Co": {"nome": "Cobalto", "estrutura": "HC", "raio": 0.1253, "peso": 58.93, "densidade_exp": 8.90, "c_a": 1.623, "aliases": ["cobalto", "cobalt"]},
    "Po": {"nome": "Polônio (α)", "estrutura": "CS", "raio": 0.1680, "peso": 209.00, "densidade_exp": 9.20, "aliases": ["polonio", "polonium"]},
}

# a e c medidos por difração (nm, 20 °C), α linear (10⁻⁶/°C, 20–100 °C), fusão (°C),
# eletronegatividade e valência (tabela das regras de Hume-Rothery do Callister) e cor padrão Jmol/CPK.
PROPRIEDADES_EXTRAS: Dict[str, Tuple[float, Optional[float], float, float, float, int, str]] = {
    "Fe": (0.2866, None, 11.8, 1538, 1.8, 2, "#e06633"),
    "Cr": (0.2884, None, 6.2, 1857, 1.6, 3, "#8a99c7"),
    "Mo": (0.3147, None, 4.9, 2623, 1.8, 4, "#54b5b5"),
    "W": (0.3165, None, 4.5, 3422, 1.7, 4, "#2194d6"),
    "Cu": (0.3615, None, 17.0, 1085, 1.9, 2, "#c88033"),
    "Al": (0.4049, None, 23.6, 660, 1.5, 3, "#bfa6a6"),
    "Ni": (0.3524, None, 13.3, 1455, 1.8, 2, "#50d050"),
    "Ag": (0.4086, None, 19.7, 962, 1.9, 1, "#c0c0c0"),
    "Au": (0.4078, None, 14.2, 1064, 2.4, 1, "#ffd123"),
    "Pb": (0.4950, None, 29.0, 327, 1.8, 2, "#575961"),
    "Mg": (0.3209, 0.5211, 25.2, 650, 1.2, 2, "#8aff00"),
    "Ti": (0.2951, 0.4683, 8.6, 1668, 1.5, 4, "#bfc2c7"),
    "Zn": (0.2665, 0.4947, 30.2, 420, 1.6, 2, "#7d80b0"),
    "Co": (0.2507, 0.4069, 13.0, 1495, 1.8, 2, "#f090a0"),
    "Po": (0.3359, None, 23.5, 254, 2.0, 4, "#ab5c00"),
}
for _simbolo, (_a, _c, _alfa, _fusao, _chi, _val, _cor) in PROPRIEDADES_EXTRAS.items():
    METAIS[_simbolo].update({"a_exp": _a, "c_exp": _c, "alfa": _alfa, "fusao": _fusao, "eletroneg": _chi, "valencia": _val, "cor": _cor})

# Solutos intersticiais (Callister, tabela das regras de Hume-Rothery).
INTERSTICIAIS: Dict[str, Dict[str, Any]] = {
    "C": {"nome": "Carbono", "raio": 0.071, "peso": 12.011, "eletroneg": 2.5, "cor": "#909090", "aliases": ["carbono", "carbon"]},
    "N": {"nome": "Nitrogênio", "raio": 0.065, "peso": 14.007, "eletroneg": 3.0, "cor": "#3050f8", "aliases": ["nitrogenio", "nitrogen", "azoto"]},
    "H": {"nome": "Hidrogênio", "raio": 0.046, "peso": 1.008, "eletroneg": 2.1, "cor": "#e8e8e8", "aliases": ["hidrogenio", "hydrogen"]},
}

# Maior sítio intersticial de cada rede: raio livre = fator·R e posições fracionárias representativas.
SITIOS: Dict[str, Dict[str, Any]] = {
    "CS": {"nome": "cúbico", "fator": SQRT3 - 1.0, "nc": 8, "frac": [(0.5, 0.5, 0.5)]},
    "CCC": {"nome": "octaédrico", "fator": 2.0 / SQRT3 - 1.0, "nc": 6,
            "frac": [(0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5), (0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, 0.5)]},
    "CFC": {"nome": "octaédrico", "fator": SQRT2 - 1.0, "nc": 6,
            "frac": [(0.5, 0.5, 0.5), (0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, 0.5)]},
    "HC": {"nome": "octaédrico", "fator": SQRT2 - 1.0, "nc": 6, "frac": [(1 / 3, 2 / 3, 0.25), (1 / 3, 2 / 3, 0.75)]},
}

# Base de átomos em coordenadas fracionárias (HC na célula primitiva a₁, a₂ a 120°, c).
BASES: Dict[str, List[Tuple[float, float, float]]] = {
    "CS": [(0.0, 0.0, 0.0)],
    "CCC": [(0.0, 0.0, 0.0), (0.5, 0.5, 0.5)],
    "CFC": [(0.0, 0.0, 0.0), (0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5)],
    "HC": [(0.0, 0.0, 0.0), (2 / 3, 1 / 3, 0.5)],
}

# Formas alotrópicas: (de °C, até °C, fase, estrutura).
ALOTROPIA: Dict[str, List[Tuple[float, float, str, str]]] = {
    "Fe": [(-273.15, 912, "α", "CCC"), (912, 1394, "γ", "CFC"), (1394, 1538, "δ", "CCC")],
    "Ti": [(-273.15, 882, "α", "HC"), (882, 1668, "β", "CCC")],
    "Co": [(-273.15, 422, "ε", "HC"), (422, 1495, "β", "CFC")],
}

LINDEMANN = 0.10

ESTRUTURAS: Dict[str, Dict[str, Any]] = {
    "CS": {
        "nome": "Cúbica Simples",
        "n": 1,
        "nc": 6,
        "a_em_R": 2.0,
        "relacao": "a = 2R",
        "substituicao": "2 × {R}",
        "contato": "aresta do cubo",
    },
    "CCC": {
        "nome": "Cúbica de Corpo Centrado",
        "n": 2,
        "nc": 8,
        "a_em_R": 4.0 / SQRT3,
        "relacao": "a = 4R/√3",
        "substituicao": "4 × {R} / √3",
        "contato": "diagonal do cubo",
    },
    "CFC": {
        "nome": "Cúbica de Face Centrada",
        "n": 4,
        "nc": 12,
        "a_em_R": 2.0 * SQRT2,
        "relacao": "a = 2R√2",
        "substituicao": "2 × {R} × √2",
        "contato": "diagonal da face",
    },
    "HC": {
        "nome": "Hexagonal Compacta",
        "n": 6,
        "nc": 12,
        "a_em_R": 2.0,
        "relacao": "a = 2R",
        "substituicao": "2 × {R}",
        "contato": "aresta do hexágono basal",
        "c_a_ideal": math.sqrt(8.0 / 3.0),
    },
}

for _sigla, _equacao in {"CS": "a = 2R", "CCC": "a√3 = 4R", "CFC": "a√2 = 4R", "HC": "a = 2R"}.items():
    ESTRUTURAS[_sigla]["contato_eq"] = _equacao

ALIASES_ESTRUTURA = {
    "CS": "CS", "SC": "CS", "CUBICASIMPLES": "CS",
    "CCC": "CCC", "BCC": "CCC", "CUBICADECORPOCENTRADO": "CCC",
    "CFC": "CFC", "FCC": "CFC", "CUBICADEFACECENTRADA": "CFC",
    "HC": "HC", "HCP": "HC", "HEXAGONALCOMPACTA": "HC",
}

FRACOES = {
    "vertice": {"CS": (1 / 8, "1/8"), "CCC": (1 / 8, "1/8"), "CFC": (1 / 8, "1/8"), "HC": (1 / 6, "1/6")},
    "centro": (1.0, "1"),
    "face": (0.5, "1/2"),
    "basal": (0.5, "1/2"),
    "interior": (1.0, "1"),
}

ROTULOS_TIPO = {
    "vertice": "Vértices",
    "centro": "Centro do cubo",
    "face": "Centros de face",
    "basal": "Centros basais",
    "interior": "Interior",
}

INTERPRETACOES = {
    "CS": [
        "Na cúbica simples os átomos se tocam ao longo da aresta: a = 2R.",
        "Só 52% do volume é ocupado por átomos (NC = 6). É rara em metais; o exemplo clássico é o Po-α.",
    ],
    "CCC": [
        "Na CCC os átomos se tocam ao longo da diagonal do cubo: 4R = a√3.",
        "FEA = 0,68 → 32% de espaços vazios. Cada átomo tem 8 vizinhos mais próximos.",
        "Exemplos: Fe-α, Cr, Mo, W. A direção compacta é a família ⟨111⟩.",
    ],
    "CFC": [
        "Na CFC os átomos se tocam ao longo da diagonal da face: 4R = a√2.",
        "FEA = 0,74, o máximo para esferas iguais. Os planos {111} são compactos e se empilham na sequência ABCABC.",
        "Exemplos: Cu, Al, Ni, Ag, Au. A direção compacta é a família ⟨110⟩.",
    ],
    "HC": [
        "Na HC os planos basais (0001) são compactos e se empilham na sequência ABAB.",
        "Com c/a ideal = 1,633 o FEA vale 0,74, igual ao da CFC. Um c/a real diferente altera o FEA.",
        "Exemplos: Mg, Ti-α, Zn, Co. Índices de Miller-Bravais (h k i l) usam i = -(h + k).",
    ],
}

SOBRESCRITO = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _txt(valor: float, casas: int = 3) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _sci(valor: float, casas: int = 3) -> str:
    if valor == 0:
        return "0"
    expoente = math.floor(math.log10(abs(valor)))
    mantissa = valor / 10 ** expoente
    return f"{_txt(mantissa, casas)} × 10{str(expoente).translate(SOBRESCRITO)}"


def _desvio(valor: float, casas: int = 2) -> str:
    texto = _txt(valor, casas)
    if texto.lstrip("-").replace("0", "").replace(",", "") == "":
        return _txt(0.0, casas)
    return ("+" if valor > 0 else "") + texto


def _sem_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn").strip().lower()


def _sub(a: Sequence[float], b: Sequence[float]) -> Vetor:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Sequence[float], b: Sequence[float]) -> Vetor:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norma(a: Sequence[float]) -> float:
    return math.sqrt(_dot(a, a))


def _arred(p: Sequence[float]) -> List[float]:
    return [round(float(v), 6) + 0.0 for v in p]


def normalizar_estrutura(texto: str) -> Optional[str]:
    chave = _sem_acentos(texto).upper().replace(" ", "")
    return ALIASES_ESTRUTURA.get(chave)


def buscar_metal(texto: str) -> Optional[str]:
    alvo = (texto or "").strip()
    if not alvo:
        return None
    for simbolo in METAIS:
        if alvo.lower() == simbolo.lower():
            return simbolo
    alvo_normalizado = _sem_acentos(alvo)
    for simbolo, dados in METAIS.items():
        if alvo_normalizado in dados["aliases"] or alvo_normalizado == _sem_acentos(dados["nome"]):
            return simbolo
    return None


def volume_em_R(estrutura: str, c_a: Optional[float]) -> float:
    a_R = ESTRUTURAS[estrutura]["a_em_R"]
    if estrutura == "HC":
        return (3.0 * SQRT3 / 2.0) * a_R ** 3 * float(c_a)
    return a_R ** 3


def fator_empacotamento(estrutura: str, c_a: Optional[float] = None) -> float:
    n = ESTRUTURAS[estrutura]["n"]
    return n * (4.0 / 3.0) * math.pi / volume_em_R(estrutura, c_a)


def cart_para_frac(estrutura: str, p: Sequence[float], c_a: Optional[float]) -> Vetor:
    if estrutura == "HC":
        return (p[0] + p[1] / SQRT3, 2.0 * p[1] / SQRT3, p[2] / float(c_a))
    return (p[0], p[1], p[2])


def frac_para_cart(estrutura: str, f: Sequence[float], c_a: Optional[float]) -> Vetor:
    if estrutura == "HC":
        return (f[0] - f[1] / 2.0, SQRT3 / 2.0 * f[1], f[2] * float(c_a))
    return (f[0], f[1], f[2])


def gradiente_plano(estrutura: str, h: int, k: int, l: int, c_a: Optional[float]) -> Vetor:
    if estrutura == "HC":
        return (float(h), (h + 2.0 * k) / SQRT3, l / float(c_a))
    return (float(h), float(k), float(l))


def geometria_celula(estrutura: str, c_a: Optional[float] = None) -> Tuple[List[Dict[str, Any]], List[List[List[float]]]]:
    if estrutura == "HC":
        return _geometria_hc(float(c_a))

    vertices = [(float(x), float(y), float(z)) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    arestas = [
        [list(a), list(b)]
        for i, a in enumerate(vertices)
        for b in vertices[i + 1:]
        if sum(abs(p - q) for p, q in zip(a, b)) == 1
    ]
    atomos = [{"pos": list(v), "tipo": "vertice"} for v in vertices]
    if estrutura == "CCC":
        atomos.append({"pos": [0.5, 0.5, 0.5], "tipo": "centro"})
    if estrutura == "CFC":
        for face in [(0.5, 0.5, 0), (0.5, 0.5, 1), (0.5, 0, 0.5), (0.5, 1, 0.5), (0, 0.5, 0.5), (1, 0.5, 0.5)]:
            atomos.append({"pos": [float(v) for v in face], "tipo": "face"})
    return atomos, arestas


def _geometria_hc(c_a: float) -> Tuple[List[Dict[str, Any]], List[List[List[float]]]]:
    hexagono = [(math.cos(math.radians(60 * i)), math.sin(math.radians(60 * i))) for i in range(6)]
    base = [_arred((x, y, 0.0)) for x, y in hexagono]
    topo = [_arred((x, y, c_a)) for x, y in hexagono]

    arestas: List[List[List[float]]] = []
    for i in range(6):
        j = (i + 1) % 6
        arestas.append([base[i], base[j]])
        arestas.append([topo[i], topo[j]])
        arestas.append([base[i], topo[i]])

    atomos: List[Dict[str, Any]] = [{"pos": p, "tipo": "vertice"} for p in base + topo]
    atomos.append({"pos": [0.0, 0.0, 0.0], "tipo": "basal"})
    atomos.append({"pos": _arred((0.0, 0.0, c_a)), "tipo": "basal"})
    raio_interno = 1.0 / SQRT3
    for angulo in (30, 150, 270):
        rad = math.radians(angulo)
        atomos.append({"pos": _arred((raio_interno * math.cos(rad), raio_interno * math.sin(rad), c_a / 2.0)), "tipo": "interior"})
    return atomos, arestas


def _fracao(estrutura: str, tipo: str) -> Tuple[float, str]:
    regra = FRACOES[tipo]
    return regra[estrutura] if isinstance(regra, dict) else regra


def _numero_opcional(payload: Dict[str, Any], chave: str, minimo: float, maximo: float, descricao: str) -> Optional[float]:
    bruto = payload.get(chave)
    if bruto is None or (isinstance(bruto, str) and not bruto.strip()):
        return None
    try:
        valor = float(str(bruto).replace(",", "."))
    except (TypeError, ValueError):
        raise ValueError(f"Valor inválido para {descricao}: {bruto}")
    if not math.isfinite(valor) or not (minimo <= valor <= maximo):
        raise ValueError(f"{descricao.capitalize()} deve estar entre {_txt(minimo, 2)} e {_txt(maximo, 2)}.")
    return valor


def calcular_estrutura(payload: Dict[str, Any]) -> Dict[str, Any]:
    alvo = str(payload.get("nome") or "").strip()
    simbolo = buscar_metal(alvo)
    estrutura: Optional[str] = None
    raio: Optional[float] = None
    peso: Optional[float] = None
    c_a: Optional[float] = None
    densidade_exp: Optional[float] = None
    nome_metal: Optional[str] = None

    if simbolo:
        metal = METAIS[simbolo]
        estrutura = metal["estrutura"]
        raio = metal["raio"]
        peso = metal["peso"]
        c_a = metal.get("c_a")
        densidade_exp = metal["densidade_exp"]
        nome_metal = metal["nome"]
    elif alvo:
        estrutura = normalizar_estrutura(alvo)
        if not estrutura:
            raise ValueError(f"'{alvo}' não é um metal cadastrado nem uma estrutura conhecida (CS, CCC, CFC, HC).")

    editado = False
    estrutura_pedida = payload.get("estrutura")
    if estrutura_pedida not in (None, ""):
        nova_estrutura = normalizar_estrutura(str(estrutura_pedida))
        if not nova_estrutura:
            raise ValueError(f"Estrutura desconhecida: {estrutura_pedida}. Use CS, CCC, CFC ou HC.")
        if simbolo and nova_estrutura != estrutura:
            editado = True
            c_a = None
        estrutura = nova_estrutura
    if not estrutura:
        raise ValueError("Informe um elemento (ex.: Fe) ou uma estrutura (CS, CCC, CFC, HC).")

    novo_raio = _numero_opcional(payload, "raio", 0.02, 0.5, "raio atômico (nm)")
    novo_peso = _numero_opcional(payload, "peso", 1.0, 300.0, "peso atômico (g/mol)")
    novo_c_a = _numero_opcional(payload, "c_a", 1.0, 2.5, "razão c/a")
    if novo_raio is not None:
        editado = editado or (raio is not None and abs(novo_raio - raio) > 1e-9)
        raio = novo_raio
    if novo_peso is not None:
        editado = editado or (peso is not None and abs(novo_peso - peso) > 1e-9)
        peso = novo_peso
    # Caminho inverso: um a medido (difração) define o raio pela condição de contato.
    novo_a = _numero_opcional(payload, "a", 0.1, 1.2, "parâmetro de rede a (nm)")
    if novo_a is not None:
        raio_de_a = novo_a / ESTRUTURAS[estrutura]["a_em_R"]
        editado = editado or (raio is not None and abs(raio_de_a - raio) > 2e-4)
        raio = raio_de_a
    if estrutura == "HC":
        if novo_c_a is not None:
            editado = editado or (c_a is not None and abs(novo_c_a - c_a) > 1e-9)
            c_a = novo_c_a
        if c_a is None:
            c_a = ESTRUTURAS["HC"]["c_a_ideal"]
    else:
        c_a = None
    if editado:
        densidade_exp = None
    a_exp = METAIS[simbolo]["a_exp"] if (simbolo and not editado) else None
    c_exp = METAIS[simbolo]["c_exp"] if (simbolo and not editado) else None

    info = ESTRUTURAS[estrutura]
    n = info["n"]
    a_em_R = info["a_em_R"]
    vol_R = volume_em_R(estrutura, c_a)
    fea = fator_empacotamento(estrutura, c_a)

    a_nm = a_em_R * raio if raio is not None else None
    c_nm = a_nm * c_a if (a_nm is not None and c_a is not None) else None
    volume_nm3 = vol_R * raio ** 3 if raio is not None else None
    volume_cm3 = volume_nm3 * 1e-21 if volume_nm3 is not None else None
    densidade = n * peso / (volume_cm3 * N_AVOGADRO) if (volume_cm3 and peso is not None) else None
    erro = (densidade / densidade_exp - 1.0) * 100.0 if (densidade and densidade_exp) else None
    erro_a = (a_nm / a_exp - 1.0) * 100.0 if (a_nm and a_exp) else None

    atomos, arestas = geometria_celula(estrutura, c_a)
    contagem: List[Dict[str, Any]] = []
    for atomo in atomos:
        fracao, fracao_txt = _fracao(estrutura, atomo["tipo"])
        atomo["fracao"] = fracao
        atomo["fracao_txt"] = fracao_txt
        atomo["elemento"] = simbolo
        atomo["frac"] = _arred(cart_para_frac(estrutura, atomo["pos"], c_a))
        grupo = next((g for g in contagem if g["tipo"] == atomo["tipo"]), None)
        if grupo is None:
            grupo = {"tipo": atomo["tipo"], "rotulo": ROTULOS_TIPO[atomo["tipo"]], "quantidade": 0, "fracao": fracao, "fracao_txt": fracao_txt, "contribuicao": 0.0}
            contagem.append(grupo)
        grupo["quantidade"] += 1
        grupo["contribuicao"] = round(grupo["quantidade"] * fracao, 6)

    if simbolo and not editado:
        rotulo = f"{simbolo} — {nome_metal}"
    elif simbolo:
        rotulo = f"{simbolo} — parâmetros editados"
    else:
        rotulo = f"Célula genérica {estrutura}" + (f" · R = {_txt(raio, 4)} nm" if raio is not None else "")

    interpretacao = list(INTERPRETACOES[estrutura])
    if estrutura == "HC":
        interpretacao.append(f"c/a usado = {_txt(c_a, 3)} (ideal 1,633) → FEA = {_txt(fea, 4)}.")
    if densidade is not None:
        frase = f"Densidade teórica calculada: {_txt(densidade, 3)} g/cm³"
        if erro is not None:
            frase += f" (experimental {_txt(densidade_exp, 2)} g/cm³, desvio {'+' if erro >= 0 else ''}{_txt(erro, 2)}%)"
        interpretacao.append(frase + ".")
    else:
        interpretacao.append("Sem raio e peso atômico a célula é exibida em unidades de R e a densidade não pode ser calculada.")
    if erro_a is not None:
        interpretacao.append(f"Parâmetro de rede calculado {_txt(a_nm, 4)} nm; medido por difração {_txt(a_exp, 4)} nm (desvio {_desvio(erro_a)}%).")

    termico_base = None
    if simbolo and a_nm is not None and raio is not None:
        metal = METAIS[simbolo]
        termico_base = {
            "simbolo": simbolo, "estrutura": estrutura, "alfa": metal["alfa"], "fusao": metal["fusao"],
            "a_nm": a_nm, "d_nn": 2.0 * raio, "densidade": densidade,
        }

    return {
        "rotulo": rotulo,
        "simbolo": simbolo,
        "nome_metal": nome_metal,
        "editado": editado,
        "generica": simbolo is None,
        "estrutura": estrutura,
        "estrutura_nome": info["nome"],
        "relacao_a": info["relacao"],
        "contato": info["contato"],
        "n": n,
        "nc": info["nc"],
        "fea": fea,
        "vazios": 1.0 - fea,
        "a_em_R": a_em_R,
        "c_a": c_a,
        "raio_nm": raio,
        "peso": peso,
        "a_nm": a_nm,
        "c_nm": c_nm,
        "volume_nm3": volume_nm3,
        "volume_cm3": volume_cm3,
        "densidade": densidade,
        "densidade_exp": densidade_exp,
        "erro_percent": erro,
        "raio_relativo": 1.0 / a_em_R,
        "atomos": atomos,
        "arestas": arestas,
        "contagem": contagem,
        "passos_densidade": _passos_densidade(estrutura, raio, peso, c_a, a_nm, c_nm, volume_cm3, densidade, densidade_exp, erro),
        "passos_parametro": _passos_parametro(estrutura, raio, c_a, a_nm, c_nm, a_exp, c_exp, erro_a),
        "passos_fea": _passos_fea(estrutura, c_a, fea, raio, a_exp, c_exp),
        "a_exp": a_exp,
        "c_exp": c_exp,
        "erro_a": erro_a,
        "cor": METAIS[simbolo]["cor"] if simbolo else None,
        "termico_base": termico_base,
        "interpretacao": interpretacao,
    }


def _passos_parametro(
    estrutura: str,
    raio: Optional[float],
    c_a: Optional[float],
    a_nm: Optional[float],
    c_nm: Optional[float],
    a_exp: Optional[float],
    c_exp: Optional[float],
    erro_a: Optional[float],
) -> List[Dict[str, str]]:
    info = ESTRUTURAS[estrutura]
    passos = [{
        "titulo": "Condição de contato",
        "formula": f"{info['contato_eq']}  →  {info['relacao']}",
        "detalhe": f"As esferas rígidas se tocam ao longo da {info['contato']}; por isso a fica determinado pelo raio R.",
    }]
    if raio is None or a_nm is None:
        passos.append({
            "titulo": "Em unidades de R",
            "formula": f"a = {_txt(info['a_em_R'], 4)}·R",
            "detalhe": "Informe o raio atômico (ou 'a = valor' no editor) para obter a em nm.",
        })
        return passos
    passos.append({
        "titulo": "Substituição numérica",
        "formula": f"a = {info['substituicao'].format(R=_txt(raio, 4))} = {_txt(a_nm, 4)} nm = {_txt(a_nm * 10, 3)} Å",
        "detalhe": f"Distância entre vizinhos mais próximos: d = 2R = {_txt(2 * raio, 4)} nm.",
    })
    if estrutura == "HC" and c_nm is not None and c_a is not None:
        passos.append({
            "titulo": "Altura da célula",
            "formula": f"c = (c/a)·a = {_txt(c_a, 3)} × {_txt(a_nm, 4)} = {_txt(c_nm, 4)} nm",
            "detalhe": "Com c/a ideal = √(8/3) = 1,633 os planos basais se empilham sem folga.",
        })
    if a_exp is not None and erro_a is not None:
        formula = f"a exp = {_txt(a_exp, 4)} nm → desvio {_desvio(erro_a)} %"
        if c_exp:
            formula += f"\nc exp = {_txt(c_exp, 4)} nm (c/a exp = {_txt(c_exp / a_exp, 3)})"
        passos.append({
            "titulo": "Comparação com difração de raios X",
            "formula": formula,
            "detalhe": "O modelo de esferas rígidas reproduz a medida com erro típico abaixo de 1%.",
        })
    return passos


def _passos_fea(
    estrutura: str,
    c_a: Optional[float],
    fea: float,
    raio: Optional[float],
    a_exp: Optional[float],
    c_exp: Optional[float],
) -> List[Dict[str, str]]:
    info = ESTRUTURAS[estrutura]
    n = info["n"]
    vol_R = volume_em_R(estrutura, c_a)
    esferas_R = n * 4.0 / 3.0 * math.pi
    if estrutura == "HC":
        celula = f"Vc = (3√3/2)·a²·c = 2,598 × (2R)² × ({_txt(c_a, 3)} × 2R) = {_txt(vol_R, 3)}·R³"
    else:
        celula = f"Vc = a³ = ({info['relacao'].split('= ')[1]})³ = {_txt(vol_R, 3)}·R³"
    passos = [
        {
            "titulo": "Volume ocupado pelas esferas",
            "formula": f"Vs = n·(4/3)πR³ = {n} × 4,189·R³ = {_txt(esferas_R, 3)}·R³",
            "detalhe": f"A célula contém {n} átomo(s) inteiro(s) somando as frações de vértices, faces e interior.",
        },
        {
            "titulo": "Volume da célula",
            "formula": celula,
            "detalhe": "Escrever Vc em função de R faz o raio se cancelar: o FEA depende só da geometria.",
        },
        {
            "titulo": "Fator de empacotamento",
            "formula": f"FEA = Vs / Vc = {_txt(esferas_R, 3)} / {_txt(vol_R, 3)} = {_txt(fea, 4)}",
            "detalhe": f"{_txt((1 - fea) * 100, 1)}% do volume é espaço vazio, onde ficam os sítios intersticiais.",
        },
    ]
    if estrutura == "HC" and c_a is not None:
        passos.append({
            "titulo": "Efeito da razão c/a",
            "formula": f"FEA = 0,7405 × 1,633 / (c/a) = 0,7405 × 1,633 / {_txt(c_a, 3)} = {_txt(fea, 4)}",
            "detalhe": "Vc cresce com c/a; acima do ideal os planos basais se afastam e o FEA cai (caso do Zn).",
        })
    if raio is not None and a_exp is not None:
        vc_exp = (3.0 * SQRT3 / 2.0) * a_exp ** 2 * c_exp if (estrutura == "HC" and c_exp) else a_exp ** 3
        fea_exp = esferas_R * raio ** 3 / vc_exp
        passos.append({
            "titulo": "Com o a medido",
            "formula": f"FEA = n·(4/3)πR³ / Vc(exp) = {_txt(esferas_R, 3)} × {_txt(raio, 4)}³ / {_txt(vc_exp, 5)} = {_txt(fea_exp, 4)}",
            "detalhe": "A pequena diferença mostra o limite do modelo de esferas rígidas com raios tabelados.",
        })
    return passos


def _passos_densidade(
    estrutura: str,
    raio: Optional[float],
    peso: Optional[float],
    c_a: Optional[float],
    a_nm: Optional[float],
    c_nm: Optional[float],
    volume_cm3: Optional[float],
    densidade: Optional[float],
    densidade_exp: Optional[float],
    erro: Optional[float],
) -> List[Dict[str, str]]:
    info = ESTRUTURAS[estrutura]
    n = info["n"]
    if raio is None or peso is None or a_nm is None or volume_cm3 is None or densidade is None:
        faltando = " e ".join(nome for nome, valor in (("o raio atômico", raio), ("o peso atômico", peso)) if valor is None)
        return [{
            "titulo": "Dados insuficientes",
            "formula": "ρ = n·A / (Vc·N_A)",
            "detalhe": f"Informe {faltando} para calcular a densidade teórica. Ex.: estrutura {estrutura} r=0.128 A=63.55",
        }]

    a_cm = a_nm * 1e-7
    parametro = f"{info['relacao']} = {info['substituicao'].format(R=_txt(raio, 4))} = {_txt(a_nm, 4)} nm = {_sci(a_cm)} cm"
    if estrutura == "HC" and c_nm is not None and c_a is not None:
        parametro += f"\nc = (c/a)·a = {_txt(c_a, 3)} × {_txt(a_nm, 4)} = {_txt(c_nm, 4)} nm = {_sci(c_nm * 1e-7)} cm"
        volume = f"Vc = (3√3/2)·a²·c = 2,598 × ({_sci(a_cm)} cm)² × {_sci(c_nm * 1e-7)} cm = {_sci(volume_cm3)} cm³"
    else:
        volume = f"Vc = a³ = ({_sci(a_cm)} cm)³ = {_sci(volume_cm3)} cm³"

    passos = [
        {
            "titulo": "Dados de entrada",
            "formula": f"R = {_txt(raio, 4)} nm   A = {_txt(peso, 2)} g/mol   n = {n} átomos/célula   N_A = 6,022 × 10²³ átomos/mol",
            "detalhe": f"Na estrutura {estrutura} cada célula unitária contém {n} átomo(s) equivalente(s).",
        },
        {
            "titulo": "Parâmetro de rede",
            "formula": parametro,
            "detalhe": f"Os átomos se tocam ao longo da {info['contato']}.",
        },
        {
            "titulo": "Volume da célula unitária",
            "formula": volume,
            "detalhe": "1 nm = 10⁻⁷ cm, logo 1 nm³ = 10⁻²¹ cm³.",
        },
        {
            "titulo": "Densidade teórica",
            "formula": f"ρ = n·A / (Vc·N_A) = ({n} × {_txt(peso, 2)}) / ({_sci(volume_cm3)} × 6,022 × 10²³) = {_txt(densidade, 3)} g/cm³",
            "detalhe": "Massa dos átomos contidos na célula dividida pelo volume da célula.",
        },
    ]
    if densidade_exp is not None and erro is not None:
        passos.append({
            "titulo": "Comparação experimental",
            "formula": f"ρ exp = {_txt(densidade_exp, 2)} g/cm³ → desvio = {'+' if erro >= 0 else ''}{_txt(erro, 2)} %",
            "detalhe": "Diferenças vêm de raios tabelados arredondados, lacunas e expansão térmica.",
        })
    return passos


def _notacao(indices: Sequence[int], abre: str, fecha: str) -> str:
    def barra(valor: int) -> str:
        if valor >= 0:
            return str(valor)
        return "".join(digito + "̄" for digito in str(-valor))

    return abre + " ".join(barra(v) for v in indices) + fecha


def _reduzir(indices: Sequence[int]) -> List[int]:
    divisor = 0
    for valor in indices:
        divisor = math.gcd(divisor, abs(valor))
    return [v // divisor for v in indices] if divisor > 1 else list(indices)


def calcular_miller(payload: Dict[str, Any]) -> Dict[str, Any]:
    estrutura = normalizar_estrutura(str(payload.get("estrutura") or ""))
    if not estrutura:
        raise ValueError("Carregue uma estrutura (CS, CCC, CFC ou HC) antes de desenhar índices.")

    tipo = _sem_acentos(str(payload.get("tipo") or "plano"))
    if tipo in ("direcao", "direction", "dir"):
        tipo = "direcao"
    elif tipo not in ("plano", "plane"):
        raise ValueError("Tipo deve ser 'plano' ou 'direcao'.")
    else:
        tipo = "plano"

    brutos = payload.get("indices")
    if not isinstance(brutos, list):
        raise ValueError("Envie os índices como lista, ex.: [1, 1, 1].")
    try:
        indices = [int(round(float(v))) for v in brutos]
        if any(abs(float(v) - i) > 1e-9 for v, i in zip(brutos, indices)):
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("Índices de Miller devem ser números inteiros.")

    hexagonal = estrutura == "HC"
    if not hexagonal and len(indices) != 3:
        raise ValueError("Sistemas cúbicos usam 3 índices, ex.: plano 1 1 0.")
    if hexagonal and len(indices) not in (3, 4):
        raise ValueError("Na HC use 3 índices ou 4 (Miller-Bravais), ex.: plano 1 0 -1 1.")
    if all(v == 0 for v in indices):
        raise ValueError("Os índices não podem ser todos nulos.")
    if any(abs(v) > 9 for v in indices):
        raise ValueError("Use índices entre -9 e 9.")

    c_a = None
    if hexagonal:
        c_a = _numero_opcional(payload, "c_a", 1.0, 2.5, "razão c/a") or ESTRUTURAS["HC"]["c_a_ideal"]
    a_nm = _numero_opcional(payload, "a_nm", 0.01, 2.0, "parâmetro de rede (nm)")
    try:
        supercelula = int(payload.get("supercelula") or 1)
    except (TypeError, ValueError):
        raise ValueError("Supercélula inválida: use um inteiro de 1 a 4.")
    if not 1 <= supercelula <= 4:
        raise ValueError("A supercélula vai de 1 a 4 células por aresta.")
    atomos, arestas = geometria_celula(estrutura, c_a)

    if tipo == "plano":
        return _calcular_plano(estrutura, indices, c_a, a_nm, atomos, arestas, supercelula)
    if supercelula > 1:
        atomos = geometria_supercelula(estrutura, c_a, supercelula)[0]
    return _calcular_direcao(estrutura, indices, c_a, a_nm, atomos)


def _poligono_plano(
    funcao: Callable[[Sequence[float]], float],
    arestas: List[List[List[float]]],
    normal: Vetor,
) -> Optional[Tuple[List[Vetor], Vetor, float]]:
    """Polígono (ordenado), centro e área da interseção de um plano com as arestas de uma caixa."""
    pontos: List[Vetor] = []

    def adicionar(p: Sequence[float]) -> None:
        candidato = (float(p[0]), float(p[1]), float(p[2]))
        if not any(_norma(_sub(candidato, q)) < EPS for q in pontos):
            pontos.append(candidato)

    for a, b in arestas:
        fa, fb = funcao(a), funcao(b)
        if abs(fa) < EPS:
            adicionar(a)
        if abs(fb) < EPS:
            adicionar(b)
        if abs(fa) >= EPS and abs(fb) >= EPS and fa * fb < 0:
            t = fa / (fa - fb)
            adicionar((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2])))

    if len(pontos) < 3:
        return None
    centro = tuple(sum(p[j] for p in pontos) / len(pontos) for j in range(3))
    eixo_u = _sub(pontos[0], centro)
    if _norma(eixo_u) < EPS:
        return None
    eixo_u = tuple(v / _norma(eixo_u) for v in eixo_u)
    eixo_v = _cross(normal, eixo_u)
    pontos.sort(key=lambda p: math.atan2(_dot(_sub(p, centro), eixo_v), _dot(_sub(p, centro), eixo_u)))

    area_vetor = (0.0, 0.0, 0.0)
    for idx, p in enumerate(pontos):
        c = _cross(p, pontos[(idx + 1) % len(pontos)])
        area_vetor = (area_vetor[0] + c[0], area_vetor[1] + c[1], area_vetor[2] + c[2])
    area = abs(_dot(area_vetor, normal)) / 2.0
    if area < EPS:
        return None
    return pontos, centro, area


def _atomos_no_poligono(pontos: List[Vetor], posicoes: List[Sequence[float]]) -> float:
    """Átomos equivalentes dentro do polígono: vértice conta ângulo/360°, aresta 1/2, interior 1."""
    soma = 0.0
    for p in posicoes:
        vertice = next((i for i, q in enumerate(pontos) if _norma(_sub(p, q)) < 1e-4), None)
        if vertice is not None:
            q = pontos[vertice]
            u = _sub(pontos[vertice - 1], q)
            v = _sub(pontos[(vertice + 1) % len(pontos)], q)
            cosseno = max(-1.0, min(1.0, _dot(u, v) / (_norma(u) * _norma(v))))
            soma += math.acos(cosseno) / (2.0 * math.pi)
            continue
        na_aresta = False
        for i, a in enumerate(pontos):
            ab = _sub(pontos[(i + 1) % len(pontos)], a)
            t = _dot(_sub(p, a), ab) / _dot(ab, ab)
            projecao = (a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2])
            if 0 < t < 1 and _norma(_sub(p, projecao)) < 1e-4:
                na_aresta = True
                break
        soma += 0.5 if na_aresta else 1.0
    return soma


def _calcular_plano(
    estrutura: str,
    indices: List[int],
    c_a: Optional[float],
    a_nm: Optional[float],
    atomos: List[Dict[str, Any]],
    arestas: List[List[List[float]]],
    supercelula: int = 1,
) -> Dict[str, Any]:
    bravais = None
    if estrutura == "HC":
        if len(indices) == 4:
            h, k, i, l = indices
            if i != -(h + k):
                raise ValueError(f"Em Miller-Bravais, i = -(h + k). Para h={h} e k={k}, use i={-(h + k)}.")
        else:
            h, k, l = indices
            i = -(h + k)
        bravais = (h, k, i, l)
        deslocamento = 1.0 + (l if l < 0 else 0)
    else:
        h, k, l = indices
        deslocamento = 1.0 + sum(v for v in (h, k, l) if v < 0)

    def valor(p: Sequence[float]) -> float:
        f = cart_para_frac(estrutura, p, c_a)
        return h * f[0] + k * f[1] + l * f[2]

    def funcao(p: Sequence[float]) -> float:
        return valor(p) - deslocamento

    gradiente = gradiente_plano(estrutura, h, k, l, c_a)
    modulo = _norma(gradiente)
    normal = (gradiente[0] / modulo, gradiente[1] / modulo, gradiente[2] / modulo)
    poligono = _poligono_plano(funcao, arestas, normal)
    if poligono is None:
        raise ValueError("Com a origem padrão, esse plano não intercepta a célula unitária desenhada.")
    pontos, centro, area = poligono

    d_rel = 1.0 / modulo
    no_plano = [idx for idx, atomo in enumerate(atomos) if abs(funcao(atomo["pos"])) < EPS]
    atomos_plano = _atomos_no_poligono(pontos, [atomos[i]["pos"] for i in no_plano])
    r_rel = 1.0 / ESTRUTURAS[estrutura]["a_em_R"]
    dp_rel = atomos_plano / area

    familia: Optional[List[Dict[str, Any]]] = None
    if supercelula > 1:
        # Todos os planos paralelos h·x + k·y + l·z = m que cortam a supercélula da liga.
        atomos_super, arestas_super = geometria_supercelula(estrutura, c_a, supercelula)
        valores = [valor(frac_para_cart(estrutura, (x, y, z), c_a)) for x in (0, supercelula) for y in (0, supercelula) for z in (0, supercelula)]
        familia = []
        for m in range(math.ceil(min(valores) - EPS), math.floor(max(valores) + EPS) + 1):
            corte = _poligono_plano(lambda p, m=m: valor(p) - m, arestas_super, normal)
            if corte:
                familia.append({"pontos": [_arred(p) for p in corte[0]], "centro": _arred(corte[1])})
        familia = familia[:40]
        no_plano = []
        if familia:
            # Destaca só o plano rotulado: em várias redes todo átomo pertence a algum plano da família.
            meio = familia[len(familia) // 2]
            centro = meio["centro"]
            m_meio = round(valor(centro))
            no_plano = [idx for idx, atomo in enumerate(atomos_super) if abs(valor(atomo["pos"]) - m_meio) < 1e-5]

    return {
        "tipo": "plano",
        "estrutura": estrutura,
        "indices": indices,
        "notacao": _notacao(bravais if bravais else (h, k, l), "(", ")"),
        "notacao_alternativa": _notacao((h, k, l), "(", ")") + " em 3 índices" if bravais else None,
        "poligono": [_arred(p) for p in pontos],
        "centro": _arred(centro),
        "normal": _arred(normal),
        "area_rel": area,
        "area_nm2": area * a_nm ** 2 if a_nm else None,
        "d_rel": d_rel,
        "d_nm": d_rel * a_nm if a_nm else None,
        "atomos_plano": atomos_plano,
        "dp_rel": dp_rel,
        "dp_nm": dp_rel / a_nm ** 2 if a_nm else None,
        "fracao_planar": atomos_plano * math.pi * r_rel ** 2 / area,
        "poligonos": familia,
        "supercelula": supercelula,
        "atomos": no_plano,
    }


def _calcular_direcao(
    estrutura: str,
    indices: List[int],
    c_a: Optional[float],
    a_nm: Optional[float],
    atomos: List[Dict[str, Any]],
) -> Dict[str, Any]:
    alternativa = None
    if estrutura == "HC":
        if len(indices) == 4:
            u, v, t, w = indices
            if t != -(u + v):
                raise ValueError(f"Em Miller-Bravais, t = -(u + v). Para u={u} e v={v}, use t={-(u + v)}.")
            U, V, W = _reduzir([u - t, v - t, w])
            notacao = _notacao((u, v, t, w), "[", "]")
            alternativa = _notacao((U, V, W), "[", "]") + " em 3 índices"
        else:
            U, V, W = _reduzir(indices)
            quatro = _reduzir([2 * U - V, 2 * V - U, -(U + V), 3 * W])
            notacao = _notacao((U, V, W), "[", "]")
            alternativa = _notacao(quatro, "[", "]") + " em Miller-Bravais"
        inicio_frac: Vetor = (0.0, 0.0, 1.0 if W < 0 else 0.0)
    else:
        U, V, W = _reduzir(indices)
        notacao = _notacao((U, V, W), "[", "]")
        inicio_frac = tuple(1.0 if c < 0 else 0.0 for c in (U, V, W))

    maior = max(abs(U), abs(V), abs(W))
    fim_frac = (inicio_frac[0] + U / maior, inicio_frac[1] + V / maior, inicio_frac[2] + W / maior)
    inicio = frac_para_cart(estrutura, inicio_frac, c_a)
    fim = frac_para_cart(estrutura, fim_frac, c_a)
    vetor = _sub(fim, inicio)
    comprimento = _norma(vetor)

    na_direcao: List[int] = []
    contagem = 0.0
    for idx, atomo in enumerate(atomos):
        t = _dot(_sub(atomo["pos"], inicio), vetor) / comprimento ** 2
        projecao = (inicio[0] + t * vetor[0], inicio[1] + t * vetor[1], inicio[2] + t * vetor[2])
        if -EPS <= t <= 1 + EPS and _norma(_sub(projecao, atomo["pos"])) < EPS:
            na_direcao.append(idx)
            contagem += 0.5 if (abs(t) < EPS or abs(t - 1) < EPS) else 1.0

    ponto_de_rede = maior == 1
    densidade_rel = contagem / comprimento if ponto_de_rede else None

    return {
        "tipo": "direcao",
        "estrutura": estrutura,
        "indices": indices,
        "notacao": notacao,
        "notacao_alternativa": alternativa,
        "inicio": _arred(inicio),
        "fim": _arred(fim),
        "comprimento_rel": comprimento,
        "comprimento_nm": comprimento * a_nm if a_nm else None,
        "atomos_contados": contagem if ponto_de_rede else None,
        "densidade_linear_rel": densidade_rel,
        "densidade_linear_nm": densidade_rel / a_nm if (densidade_rel is not None and a_nm) else None,
        "atomos": na_direcao,
    }


def _pontos_na_caixa(base: Sequence[Sequence[float]], n: int) -> List[Vetor]:
    pontos: List[Vetor] = []
    for i in range(-1, n + 1):
        for j in range(-1, n + 1):
            for k in range(-1, n + 1):
                for b in base:
                    f = (i + b[0], j + b[1], k + b[2])
                    if all(-EPS <= v <= n + EPS for v in f):
                        pontos.append(f)
    return pontos


def geometria_supercelula(estrutura: str, c_a: Optional[float], n: int) -> Tuple[List[Dict[str, Any]], List[List[List[float]]]]:
    """Bloco n×n×n de células (primitivas na HC), com os átomos das faces incluídos."""
    atomos = [
        {"pos": _arred(frac_para_cart(estrutura, f, c_a)), "frac": _arred(f), "tipo": "rede"}
        for f in _pontos_na_caixa(BASES[estrutura], n)
    ]
    cantos = [(float(x), float(y), float(z)) for x in (0, n) for y in (0, n) for z in (0, n)]
    arestas = [
        [_arred(frac_para_cart(estrutura, a, c_a)), _arred(frac_para_cart(estrutura, b, c_a))]
        for i, a in enumerate(cantos)
        for b in cantos[i + 1:]
        if abs(sum(abs(p - q) for p, q in zip(a, b)) - n) < EPS
    ]
    return atomos, arestas


def _buscar_intersticial(texto: str) -> Optional[str]:
    alvo = _sem_acentos(texto or "")
    for simbolo, dados in INTERSTICIAIS.items():
        if alvo == simbolo.lower() or alvo in dados["aliases"]:
            return simbolo
    return None


def _elemento(simbolo: str) -> Dict[str, Any]:
    return METAIS.get(simbolo) or INTERSTICIAIS[simbolo]


def _regras_substitucional(base: str, soluto: str) -> Tuple[List[Dict[str, Any]], str]:
    b, s = METAIS[base], METAIS[soluto]
    dr = abs(s["raio"] - b["raio"]) / b["raio"] * 100.0
    dchi = abs(s["eletroneg"] - b["eletroneg"])
    regras = [
        {"criterio": "Tamanho atômico", "valor": f"ΔR = {_txt(dr, 1)}%", "ok": dr <= 15.0,
         "detalhe": "Raios até ±15% diferentes permitem substituição extensa."},
        {"criterio": "Estrutura cristalina", "valor": f"{b['estrutura']} e {s['estrutura']}", "ok": b["estrutura"] == s["estrutura"],
         "detalhe": "Solubilidade total exige a mesma estrutura nos dois metais puros."},
        {"criterio": "Eletronegatividade", "valor": f"Δχ = {_txt(dchi, 1)}", "ok": dchi <= 0.4,
         "detalhe": "Diferença grande favorece compostos intermetálicos em vez de solução sólida."},
        {"criterio": "Valência", "valor": f"+{b['valencia']} e +{s['valencia']}", "ok": b["valencia"] == s["valencia"],
         "detalhe": "Mesma valência favorece; um metal dissolve melhor outro de valência maior."},
    ]
    atendidas = sum(1 for r in regras if r["ok"])
    if atendidas == 4:
        conclusao = "Todas as regras atendidas: solubilidade sólida extensa, possivelmente completa (como no Cu–Ni)."
    elif regras[0]["ok"]:
        conclusao = f"{atendidas} de 4 regras atendidas: solubilidade parcial; acima do limite surgem outras fases."
    else:
        conclusao = "Diferença de tamanho acima de 15%: solubilidade substitucional muito limitada."
    return regras, conclusao


def _regras_intersticial(base: str, soluto: str) -> Tuple[List[Dict[str, Any]], str]:
    b, s = METAIS[base], INTERSTICIAIS[soluto]
    sitio = SITIOS[b["estrutura"]]
    r_sitio = sitio["fator"] * b["raio"]
    razao = s["raio"] / b["raio"]
    regras = [
        {"criterio": "Razão de raios", "valor": f"r/R = {_txt(razao, 3)}", "ok": razao <= 0.59,
         "detalhe": "Regra de Hägg: soluções intersticiais exigem r/R abaixo de ~0,59."},
        {"criterio": f"Sítio {sitio['nome']}", "valor": f"r livre = {_txt(r_sitio, 4)} nm", "ok": s["raio"] <= r_sitio,
         "detalhe": f"Raio livre do sítio = {_txt(sitio['fator'], 3)}·R. Soluto maior empurra os vizinhos."},
    ]
    if s["raio"] > r_sitio:
        conclusao = f"O {s['nome'].lower()} ({_txt(s['raio'], 3)} nm) é maior que o sítio: a rede se distorce e a solubilidade é baixa."
    else:
        conclusao = "O soluto cabe no sítio sem distorção: solubilidade intersticial alta."
    if base == "Fe" and soluto == "C":
        conclusao += " No Fe-α (CCC) o máximo é 0,022% C em peso (727 °C); no Fe-γ (CFC), cujo sítio é maior, chega a 2,14% (1147 °C)."
    return regras, conclusao


def _regra_ordenada(estrutura: str, x: float) -> Optional[Tuple[Callable[[Sequence[float]], bool], str]]:
    def inteiro(v: float) -> bool:
        return abs(v - round(v)) < EPS

    if estrutura == "CFC" and abs(x - 0.25) <= 0.02:
        return (lambda f: all(inteiro(v) for v in f)), "L1₂ (tipo Cu₃Au): soluto nos vértices"
    if estrutura == "CFC" and abs(x - 0.75) <= 0.02:
        return (lambda f: not all(inteiro(v) for v in f)), "L1₂ invertida: soluto nos centros de face"
    if estrutura == "CFC" and abs(x - 0.5) <= 0.02:
        return (lambda f: inteiro(f[2])), "L1₀ (tipo CuAu): camadas alternadas ao longo de z"
    if estrutura == "CCC" and abs(x - 0.5) <= 0.02:
        return (lambda f: not inteiro(f[0])), "B2 (tipo CuZn β′): soluto nos centros dos cubos"
    return None


def calcular_liga(payload: Dict[str, Any]) -> Dict[str, Any]:
    base = buscar_metal(str(payload.get("base") or ""))
    if not base:
        raise ValueError("Escolha o metal solvente (a rede hospedeira da liga).")
    texto_soluto = str(payload.get("soluto") or "")
    soluto = _buscar_intersticial(texto_soluto)
    intersticial = soluto is not None
    if not intersticial:
        soluto = buscar_metal(texto_soluto)
    if not soluto:
        raise ValueError("Escolha o soluto: um metal cadastrado ou C, N ou H (intersticiais).")
    if soluto == base:
        raise ValueError("O soluto precisa ser diferente do solvente.")

    x_max = 20.0 if intersticial else 100.0
    x_pct = _numero_opcional(payload, "x", 0.0, x_max, f"composição (% atômica, 0 a {_txt(x_max, 0)})")
    x_pct = 10.0 if x_pct is None else x_pct
    x = x_pct / 100.0
    try:
        n = int(payload.get("n") or 3)
        semente = int(payload.get("semente") or 1)
    except (TypeError, ValueError):
        raise ValueError("Supercélula e semente devem ser números inteiros.")
    if not 1 <= n <= 4:
        raise ValueError("A supercélula vai de 1 a 4 células por aresta.")
    arranjo = "ordenado" if str(payload.get("arranjo") or "") == "ordenado" else "aleatorio"
    distorcer = bool(payload.get("distorcer"))

    mb = METAIS[base]
    ms = _elemento(soluto)
    estrutura = mb["estrutura"]
    info = ESTRUTURAS[estrutura]
    c_a = mb.get("c_a")
    n_cel = info["n"]
    rb, ab = mb["raio"], mb["peso"]
    rs, as_ = ms["raio"], ms["peso"]
    a_base = info["a_em_R"] * rb
    vol_R = volume_em_R(estrutura, c_a)

    if intersticial:
        r_ef = rb
        a_nm = a_base
        solutos_cel = n_cel * x / (1.0 - x) if x < 1 else 0.0
        massa_cel = n_cel * ab + solutos_cel * as_
        pct_peso = solutos_cel * as_ / massa_cel * 100.0
        regras, conclusao = _regras_intersticial(base, soluto)
    else:
        r_ef = (1.0 - x) * rb + x * rs  # lei de Vegard aplicada ao raio médio
        a_nm = info["a_em_R"] * r_ef
        massa_cel = n_cel * ((1.0 - x) * ab + x * as_)
        pct_peso = x * as_ / (x * as_ + (1.0 - x) * ab) * 100.0 if x > 0 else 0.0
        regras, conclusao = _regras_substitucional(base, soluto)
    volume_cm3 = vol_R * (a_nm / info["a_em_R"]) ** 3 * 1e-21
    densidade = massa_cel / (volume_cm3 * N_AVOGADRO)
    densidade_base = n_cel * ab / (vol_R * rb ** 3 * 1e-21 * N_AVOGADRO)

    atomos, arestas = geometria_supercelula(estrutura, c_a, n)
    for atomo in atomos:
        atomo["elemento"] = base
    rng = random.Random(semente)
    fase_ordenada: Optional[str] = None
    nota_arranjo: Optional[str] = None
    if intersticial:
        sitios = _pontos_na_caixa(SITIOS[estrutura]["frac"], n)
        quantidade = 0 if x == 0 else min(len(sitios), max(1, round(len(atomos) * x / (1.0 - x))))
        for f in sorted(rng.sample(sitios, quantidade)):
            atomos.append({"pos": _arred(frac_para_cart(estrutura, f, c_a)), "frac": _arred(f), "tipo": "intersticial", "elemento": soluto})
        if arranjo == "ordenado":
            nota_arranjo = "Intersticiais são distribuídos ao acaso entre os sítios livres."
    else:
        regra = _regra_ordenada(estrutura, x) if arranjo == "ordenado" else None
        if regra:
            teste, fase_ordenada = regra
            for atomo in atomos:
                if teste(atomo["frac"]):
                    atomo["elemento"] = soluto
        else:
            if arranjo == "ordenado":
                nota_arranjo = "Sem superestrutura ordenada para essa composição; usada distribuição aleatória. Ordenadas disponíveis: CFC com 25, 50 ou 75% e CCC com 50%."
            for idx in rng.sample(range(len(atomos)), round(x * len(atomos))):
                atomos[idx]["elemento"] = soluto

    for atomo in atomos:
        atomo["raio_rel"] = _elemento(atomo["elemento"])["raio"] / a_nm

    if distorcer:
        _aplicar_distorcao(atomos, base, a_nm)

    n_soluto = sum(1 for a in atomos if a["elemento"] == soluto)
    n_solvente = len(atomos) - n_soluto
    sinal = "+" if a_nm >= a_base else ""
    passos = [{
        "titulo": "Composição em peso",
        "formula": f"C({soluto}) = x·A({soluto}) / [x·A({soluto}) + (1 − x)·A({base})] = {_txt(pct_peso, 2)} % em peso",
        "detalhe": f"x = {_txt(x, 3)} (fração atômica); A({soluto}) = {_txt(as_, 2)} e A({base}) = {_txt(ab, 2)} g/mol.",
    }]
    if intersticial:
        sitio = SITIOS[estrutura]
        passos.append({
            "titulo": f"Sítio {sitio['nome']}",
            "formula": f"r livre = {_txt(sitio['fator'], 3)} × R({base}) = {_txt(sitio['fator'] * rb, 4)} nm   r({soluto}) = {_txt(rs, 3)} nm",
            "detalhe": f"O {ms['nome'].lower()} ocupa vazios entre os átomos de {base}; a rede hospedeira mantém a = {_txt(a_nm, 4)} nm neste modelo.",
        })
        passos.append({
            "titulo": "Densidade da liga",
            "formula": f"ρ = [n·A({base}) + nₛ·A({soluto})] / (Vc·N_A) = ({n_cel} × {_txt(ab, 2)} + {_txt(solutos_cel, 3)} × {_txt(as_, 2)}) / ({_sci(volume_cm3)} × 6,022 × 10²³) = {_txt(densidade, 3)} g/cm³",
            "detalhe": f"nₛ = n·x/(1 − x) = {_txt(solutos_cel, 3)} átomos intersticiais por célula.",
        })
    else:
        passos.append({
            "titulo": "Lei de Vegard",
            "formula": f"R̄ = (1 − x)·R({base}) + x·R({soluto}) = {_txt(1 - x, 3)} × {_txt(rb, 4)} + {_txt(x, 3)} × {_txt(rs, 4)} = {_txt(r_ef, 4)} nm\n"
                       f"a = {info['substituicao'].format(R=_txt(r_ef, 4))} = {_txt(a_nm, 4)} nm ({sinal}{_txt((a_nm / a_base - 1) * 100, 2)}% em relação ao {base} puro)",
            "detalhe": "O parâmetro de rede varia linearmente entre os dos componentes na estrutura do solvente.",
        })
        passos.append({
            "titulo": "Densidade da liga",
            "formula": f"ρ = n·Ā / (Vc·N_A) = ({n_cel} × {_txt(massa_cel / n_cel, 2)}) / ({_sci(volume_cm3)} × 6,022 × 10²³) = {_txt(densidade, 3)} g/cm³",
            "detalhe": f"Ā = (1 − x)·A({base}) + x·A({soluto}) é a massa atômica média. {base} puro: {_txt(densidade_base, 3)} g/cm³.",
        })

    interpretacao = [conclusao]
    interpretacao.append(
        f"Na supercélula {n}×{n}×{n}, {n_soluto} de {len(atomos)} átomos são {soluto}. "
        "Átomos nas faces da caixa são imagens periódicas e também aparecem na contagem."
    )
    if fase_ordenada:
        interpretacao.append(f"Arranjo ordenado {fase_ordenada}. Aquecida, a liga tende a se desordenar.")
    if distorcer:
        interpretacao.append("Distorção ilustrativa: vizinhos do soluto se deslocam metade do desajuste de raios (limite de 0,12·a).")

    if intersticial:
        alfa, fusao, d_nn = mb["alfa"], mb["fusao"], 2.0 * rb
    else:
        alfa = (1.0 - x) * mb["alfa"] + x * ms["alfa"]
        fusao = (1.0 - x) * mb["fusao"] + x * ms["fusao"]
        d_nn = 2.0 * r_ef

    return {
        "rotulo": f"Liga {base}–{soluto}",
        "base": base,
        "soluto": soluto,
        "intersticial": intersticial,
        "estrutura": estrutura,
        "estrutura_nome": info["nome"],
        "nc": info["nc"],
        "c_a": c_a,
        "supercelula": n,
        "semente": semente,
        "x_pct": x_pct,
        "pct_peso": pct_peso,
        "a_nm": a_nm,
        "c_nm": a_nm * c_a if c_a else None,
        "a_base_nm": a_base,
        "raio_relativo": rb / a_nm,
        "densidade": densidade,
        "densidade_base": densidade_base,
        "n_soluto": n_soluto,
        "n_solvente": n_solvente,
        "fase_ordenada": fase_ordenada,
        "nota_arranjo": nota_arranjo,
        "sitio": {"nome": SITIOS[estrutura]["nome"], "raio_nm": SITIOS[estrutura]["fator"] * rb} if intersticial else None,
        "regras": regras,
        "conclusao": conclusao,
        "passos": passos,
        "interpretacao": interpretacao,
        "atomos": atomos,
        "arestas": arestas,
        "termico_base": {
            "simbolo": base, "estrutura": estrutura, "alfa": alfa, "fusao": fusao,
            "a_nm": a_nm, "d_nn": d_nn, "densidade": densidade, "liga": not intersticial,
        },
    }


def _aplicar_distorcao(atomos: List[Dict[str, Any]], base: str, a_nm: float) -> None:
    """Desloca os vizinhos de cada soluto em metade do desajuste de raios (ilustrativo, limitado a 0,12·a)."""
    r_base = METAIS[base]["raio"]
    hospedeiros = [i for i, a in enumerate(atomos) if a["elemento"] == base]
    deslocamentos = {i: [0.0, 0.0, 0.0] for i in hospedeiros}
    for atomo in atomos:
        if atomo["elemento"] == base:
            continue
        r_soluto = _elemento(atomo["elemento"])["raio"]
        distancias = [(i, _norma(_sub(atomos[i]["pos"], atomo["pos"]))) for i in hospedeiros]
        if not distancias:
            continue
        minima = min(d for _, d in distancias)
        for i, d in distancias:
            if d > minima * 1.05 or d < EPS:
                continue
            desajuste = (r_soluto + r_base - d * a_nm) / a_nm
            passo = max(-0.12, min(0.12, 0.5 * desajuste))
            direcao = _sub(atomos[i]["pos"], atomo["pos"])
            for j in range(3):
                deslocamentos[i][j] += passo * direcao[j] / d
    for i, (dx, dy, dz) in deslocamentos.items():
        total = math.sqrt(dx * dx + dy * dy + dz * dz)
        if total < 1e-9:
            continue
        escala = min(1.0, 0.15 / total)
        p = atomos[i]["pos"]
        atomos[i]["pos"] = _arred((p[0] + dx * escala, p[1] + dy * escala, p[2] + dz * escala))


def calcular_termico(payload: Dict[str, Any]) -> Dict[str, Any]:
    alfa = _numero_opcional(payload, "alfa", 0.1, 100.0, "coeficiente de dilatação (10⁻⁶/°C)")
    fusao = _numero_opcional(payload, "fusao", -100.0, 4000.0, "temperatura de fusão (°C)")
    a_nm = _numero_opcional(payload, "a_nm", 0.05, 2.0, "parâmetro de rede (nm)")
    d_nn = _numero_opcional(payload, "d_nn", 0.02, 1.5, "distância entre vizinhos (nm)")
    densidade = _numero_opcional(payload, "densidade", 0.1, 30.0, "densidade (g/cm³)")
    temperatura = _numero_opcional(payload, "temperatura", -273.15, 5000.0, "temperatura (°C)")
    if alfa is None or fusao is None or a_nm is None or d_nn is None:
        raise ValueError("Dados térmicos indisponíveis: escolha um metal cadastrado.")
    if temperatura is None:
        temperatura = 20.0

    t_k = temperatura + 273.15
    tf_k = fusao + 273.15
    fator = 1.0 + alfa * 1e-6 * (temperatura - 20.0)
    razao = LINDEMANN * math.sqrt(max(t_k, 0.0) / tf_k)
    u_nm = razao * d_nn
    homologa = t_k / tf_k
    fundido = temperatura >= fusao

    passos_curva = 60
    inicio, fim = -273.15, fusao + 200.0
    curva = []
    for i in range(passos_curva + 1):
        t = inicio + (fim - inicio) * i / passos_curva
        curva.append([round(t, 1), round(LINDEMANN * math.sqrt(max(t + 273.15, 0.0) / tf_k), 5)])

    notas: List[Dict[str, str]] = []
    if fundido:
        notas.append({"tipo": "alerta", "texto": "Acima da temperatura de fusão a ordem cristalina de longo alcance desaparece: o material é líquido."})
    elif homologa >= 0.5:
        notas.append({"tipo": "info", "texto": "Acima de ~0,5·Tf (em kelvin) a difusão é intensa: trabalho a quente, fluência e recristalização rápida."})
    elif homologa >= 0.3:
        notas.append({"tipo": "info", "texto": "Entre 0,3 e 0,5·Tf ocorrem recuperação e recristalização (faixa típica de recozimento)."})
    else:
        notas.append({"tipo": "info", "texto": "Abaixo de ~0,3·Tf a difusão é lenta: a deformação plástica encrua o metal (trabalho a frio)."})
    simbolo = str(payload.get("simbolo") or "")
    estrutura = str(payload.get("estrutura") or "")
    if payload.get("liga"):
        notas.append({"tipo": "info", "texto": "Na liga, α e Tf são estimados pela regra das misturas; consulte o diagrama de fases para o solidus real."})
    for de, ate, fase, estrutura_fase in ALOTROPIA.get(simbolo, []):
        if de <= temperatura < ate and not fundido:
            texto = f"Entre {_txt(max(de, -273.15), 0)} e {_txt(ate, 0)} °C a fase estável é {simbolo}-{fase} ({estrutura_fase})."
            if estrutura_fase != estrutura:
                notas.append({"tipo": "alerta", "texto": texto + f" A célula exibida ({estrutura}) não é a de equilíbrio nessa temperatura."})
            else:
                notas.append({"tipo": "info", "texto": texto})

    return {
        "temperatura": temperatura,
        "temperatura_k": t_k,
        "fusao": fusao,
        "homologa": homologa,
        "alfa": alfa,
        "fator": fator,
        "a_ref_nm": a_nm,
        "a_nm": a_nm * fator,
        "delta_a_pct": (fator - 1.0) * 100.0,
        "densidade": densidade / fator ** 3 if densidade else None,
        "delta_v_pct": (fator ** 3 - 1.0) * 100.0,
        "u_nm": u_nm,
        "razao": razao,
        "amplitude_rel": u_nm / a_nm,
        "lindemann": LINDEMANN,
        "fundido": fundido,
        "curva": curva,
        "notas": notas,
    }


def tabela_estruturas() -> List[Dict[str, Any]]:
    return [
        {
            "sigla": sigla,
            "nome": info["nome"],
            "n": info["n"],
            "nc": info["nc"],
            "a_em_R": info["a_em_R"],
            "relacao": info["relacao"],
            "fea": fator_empacotamento(sigla, info.get("c_a_ideal")),
        }
        for sigla, info in ESTRUTURAS.items()
    ]


def metais_publicos() -> Dict[str, Dict[str, Any]]:
    return {
        simbolo: {**{chave: valor for chave, valor in dados.items() if chave != "aliases"}, "nc": ESTRUTURAS[dados["estrutura"]]["nc"]}
        for simbolo, dados in METAIS.items()
    }


HTML_TEMPLATE = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CrystaLab: Fundamentos Estruturais</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
  <style>
    /* ---------- Tokens (alloy-ui; mesmos valores do v1.0) ---------- */
    :root {
      color-scheme: light;
      --font: "Atkinson Hyperlegible", "Segoe UI", system-ui, sans-serif;
      --mono: "JetBrains Mono", Consolas, "Courier New", monospace;
      --ink: #10131a;
      --ink-soft: #29313f;
      --muted: #5f6b7d;
      --panel: #f5f7fb;
      --panel-2: #ffffff;
      --line: #dbe2eb;
      --line-strong: #c3ccd8;
      --cyan: #1aa7d9;
      --cyan-ink: #08698c;
      --green: #19a56b;
      --amber: #d79319;
      --red: #ce3f4f;
      --violet: #7256d9;
      --code-bg: #eef2f7;
      --chip-bg: rgba(255, 255, 255, 0.9);
      --stage-bg: #e9eef5;
      --stage-glow: #ffffff;
      --row-active: rgba(26, 167, 217, 0.1);
      --track: #e6ebf2;
      --radius-s: 6px;
      --radius-m: 10px;

      /* Lateral grafite nos dois temas (decisão do v1.0) */
      --side-bg: #11151c;
      --side-raised: #1a212b;
      --side-hover: #222b37;
      --side-line: rgba(255, 255, 255, 0.08);
      --side-ink: #eef3f8;
      --side-muted: #9fadbf;
      --accent-on-dark: #44c5f2;

      /* Cor fixa por estrutura: o mesmo código na lateral, no título e na tabela */
      --s-CCC: #f2c85b;
      --s-CFC: #39c38d;
      --s-HC: #b9a6ff;
      --s-CS: #c9d4e2;
    }

    :root[data-theme="dark"] {
      color-scheme: dark;
      --ink: #eef3f8;
      --ink-soft: #c6d0dc;
      --muted: #93a1b3;
      --panel: #0f141b;
      --panel-2: #161d27;
      --line: #263241;
      --line-strong: #34435a;
      --cyan-ink: #44c5f2;
      --code-bg: #0f151d;
      --chip-bg: rgba(17, 21, 28, 0.85);
      --stage-bg: #0a0e13;
      --stage-glow: #1a2533;
      --row-active: rgba(68, 197, 242, 0.12);
      --track: #253040;
    }

    * { box-sizing: border-box; }

    html, body { margin: 0; }

    body {
      min-height: 100vh;
      font-family: var(--font);
      font-size: 15px;
      line-height: 1.5;
      background: var(--panel);
      color: var(--ink);
      font-variant-numeric: tabular-nums;
    }

    button, input, textarea { font: inherit; color: inherit; }
    button { cursor: pointer; }
    h1, h2, h3, p, dl, dd, ol { margin: 0; }

    :focus-visible {
      outline: 2px solid var(--cyan);
      outline-offset: 2px;
      border-radius: 4px;
    }

    .visually-hidden {
      position: absolute;
      width: 1px; height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }

    /* ---------- Shell ---------- */
    .app {
      display: grid;
      grid-template-columns: 216px minmax(0, 1fr);
      min-height: 100vh;
    }

    /* ---------- Lateral: escolha do material ---------- */
    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 18px;
      padding: 20px 16px 16px;
      background: var(--side-bg);
      color: var(--side-ink);
      border-right: 1px solid var(--side-line);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 0 4px;
    }

    .brand svg { flex: 0 0 auto; }

    .brand strong {
      display: block;
      font-size: 18px;
      line-height: 1.1;
    }

    .brand span {
      display: block;
      color: var(--side-muted);
      font-size: 12.5px;
    }

    .side-search {
      position: relative;
    }

    .side-search input {
      width: 100%;
      min-height: 38px;
      padding: 0 12px;
      border: 1px solid var(--side-line);
      border-radius: var(--radius-s);
      background: var(--side-raised);
      color: var(--side-ink);
      outline: 0;
    }

    .side-search input::placeholder { color: var(--side-muted); }
    .side-search input:focus { border-color: var(--accent-on-dark); }

    .element-groups {
      display: grid;
      gap: 16px;
    }

    .element-group h2 {
      display: flex;
      align-items: baseline;
      gap: 8px;
      margin: 0 4px 8px;
      font-size: 13px;
      font-weight: 700;
      color: var(--side-ink);
    }

    .element-group h2 span {
      color: var(--side-muted);
      font-weight: 400;
    }

    .element-group h2::before {
      content: "";
      align-self: center;
      width: 8px;
      height: 8px;
      border-radius: 2px;
      background: var(--group-color, var(--side-muted));
    }

    .tile-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 6px;
    }

    .element-tile {
      position: relative;
      min-width: 0;
      display: grid;
      grid-template-rows: auto auto auto;
      padding: 6px 8px 7px;
      border: 1px solid var(--side-line);
      border-top: 3px solid var(--tile-color, var(--side-muted));
      border-radius: var(--radius-s);
      background: var(--side-raised);
      text-align: left;
      cursor: pointer;
      user-select: none;
    }

    .element-tile:hover { background: var(--side-hover); }

    .element-tile.is-active {
      background: var(--side-hover);
      box-shadow: 0 0 0 2px var(--accent-on-dark);
    }

    .tile-mass {
      color: var(--side-muted);
      font-size: 10.5px;
      line-height: 1.2;
    }

    .tile-symbol {
      font-size: 22px;
      font-weight: 700;
      line-height: 1.15;
    }

    .tile-name {
      overflow: hidden;
      color: var(--side-muted);
      font-size: 11px;
      line-height: 1.25;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .side-empty {
      padding: 4px;
      color: var(--side-muted);
      font-size: 13px;
    }

    .side-foot {
      margin-top: auto;
      padding: 12px 4px 0;
      border-top: 1px solid var(--side-line);
      color: var(--side-muted);
      font-size: 12px;
    }

    /* ---------- Coluna principal ---------- */
    .main {
      min-width: 0;
      height: 100vh;
      display: grid;
      grid-template-rows: auto auto minmax(0, 1fr) auto;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      min-height: 56px;
      padding: 8px 24px;
      border-bottom: 1px solid var(--line);
      background: var(--panel-2);
    }

    .topbar-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }

    .crumb {
      min-width: 0;
      overflow: hidden;
      color: var(--muted);
      font-size: 14px;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .crumb strong { color: var(--ink); font-weight: 700; }

    .topbar-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 36px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius-s);
      background: var(--panel-2);
      color: var(--ink-soft);
      font-size: 14px;
      white-space: nowrap;
    }

    .btn:hover { border-color: var(--line-strong); color: var(--ink); }

    .btn-primary {
      border-color: var(--ink);
      background: var(--ink);
      color: var(--panel-2);
      font-weight: 700;
    }

    .btn-primary:hover { color: var(--panel-2); opacity: 0.9; }

    :root[data-theme="dark"] .btn-primary {
      border-color: var(--accent-on-dark);
      background: var(--accent-on-dark);
      color: #071017;
    }

    kbd {
      padding: 1px 6px;
      border: 1px solid var(--line);
      border-bottom-width: 2px;
      border-radius: 4px;
      background: var(--panel);
      color: var(--muted);
      font-family: var(--font);
      font-size: 12px;
    }

    .menu-button { padding: 0 10px; }

    /* ---------- Cabeçalho do material ---------- */
    .specimen {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px 24px;
      align-items: center;
      padding: 20px 24px 16px;
      background: var(--panel);
    }

    .specimen-id {
      display: flex;
      align-items: center;
      gap: 16px;
      min-width: 0;
    }

    .specimen-symbol {
      flex: 0 0 auto;
      display: grid;
      place-items: center;
      width: 64px;
      height: 64px;
      border: 1px solid var(--line);
      border-top: 4px solid var(--tile-color, var(--line-strong));
      border-radius: var(--radius-s);
      background: var(--panel-2);
      font-size: 28px;
      font-weight: 700;
      line-height: 1;
    }

    .specimen-symbol.is-generic { font-size: 18px; }

    .specimen-id h1 {
      font-size: 26px;
      line-height: 1.15;
      letter-spacing: -0.01em;
    }

    .specimen-id p {
      margin-top: 4px;
      color: var(--muted);
      font-size: 14.5px;
    }

    .mode-switch {
      display: inline-flex;
      padding: 3px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-2);
    }

    .mode-switch button {
      min-height: 34px;
      padding: 0 16px;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      font-size: 14px;
    }

    .mode-switch button[aria-selected="true"] {
      background: var(--ink);
      color: var(--panel-2);
      font-weight: 700;
    }

    :root[data-theme="dark"] .mode-switch button[aria-selected="true"] {
      background: var(--accent-on-dark);
      color: #071017;
    }

    /* Faixa de leitura: números lado a lado, sem cartões */
    .readout {
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }

    .readout > div {
      min-width: 0;
      padding: 10px 16px 10px 0;
    }

    .readout > div + div {
      padding-left: 16px;
      border-left: 1px solid var(--line);
    }

    .readout dt {
      color: var(--muted);
      font-size: 13px;
    }

    .readout dd {
      font-size: 21px;
      font-weight: 700;
      line-height: 1.25;
    }

    .readout dd small {
      margin-left: 3px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 400;
    }

    .readout .readout-note {
      display: block;
      overflow: hidden;
      color: var(--muted);
      font-size: 12.5px;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    /* ---------- Bancada: cena + inspetor ---------- */
    .workspace {
      min-height: 0;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 16px;
      padding: 0 24px 16px;
    }

    .stage-wrap {
      position: relative;
      container-type: inline-size;
      min-height: 0;
      border: 1px solid var(--line);
      border-radius: var(--radius-m);
      overflow: hidden;
    }

    .viewer-stage {
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at 50% 42%, var(--stage-glow) 0%, var(--stage-bg) 72%);
      cursor: grab;
      touch-action: none;
    }

    .viewer-stage:active { cursor: grabbing; }

    .viewer-stage canvas {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      display: block;
    }

    .layer-bar {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 4px;
      max-width: 100%;
      margin-left: auto;
      padding: 4px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--chip-bg);
      backdrop-filter: blur(8px);
    }

    .layer-bar button {
      min-height: 30px;
      padding: 0 10px;
      border: 0;
      border-radius: 5px;
      background: transparent;
      color: var(--muted);
      font-size: 13px;
    }

    .layer-bar button:hover { color: var(--ink); }

    .layer-bar button[aria-pressed="true"] {
      background: var(--row-active);
      color: var(--cyan-ink);
      font-weight: 700;
    }

    .viewer-legend {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      min-width: 0;
    }

    .legend-chip,
    .overlay-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 9px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--chip-bg);
      color: var(--ink-soft);
      font-size: 12.5px;
    }

    .legend-chip i,
    .overlay-chip i {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex: 0 0 auto;
    }

    .stage-hint {
      flex: 0 1 auto;
      color: var(--muted);
      font-size: 12.5px;
      text-align: right;
    }

    /* Cena estreita: a dica cederia espaço à legenda e as duas se sobreporiam */
    @container (max-width: 640px) {
      .stage-hint { display: none; }
    }

    .viewer-fallback {
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
      padding: 24px;
      color: var(--muted);
      text-align: center;
    }

    /* ---------- Inspetor (um painel por modo) ---------- */
    .inspector {
      min-height: 0;
      overflow-y: auto;
      border: 1px solid var(--line);
      border-radius: var(--radius-m);
      background: var(--panel-2);
    }

    .mode-panel { display: grid; }
    .mode-panel[hidden] { display: none; }

    .block {
      display: grid;
      gap: 10px;
      padding: 16px;
    }

    .block + .block { border-top: 1px solid var(--line); }

    .block h2 {
      font-size: 15px;
      line-height: 1.3;
    }

    .hint {
      color: var(--muted);
      font-size: 13px;
    }

    code {
      padding: 1px 5px;
      border-radius: 4px;
      background: var(--code-bg);
      font-family: var(--mono);
      font-size: 12.5px;
    }

    /* Átomos por célula */
    .count-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 2px 12px;
      align-items: baseline;
      font-size: 14px;
    }

    .count-row strong {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 400;
      color: var(--ink-soft);
    }

    .count-row strong i {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }

    .count-row .count-math { color: var(--muted); }

    .bar-track {
      grid-column: 1 / -1;
      height: 6px;
      border-radius: 99px;
      background: var(--track);
      overflow: hidden;
    }

    .bar-fill {
      display: block;
      height: 100%;
      border-radius: 99px;
    }

    .count-total {
      display: flex;
      justify-content: space-between;
      padding-top: 10px;
      border-top: 1px solid var(--line);
      font-weight: 700;
    }

    .interpretation p {
      color: var(--ink-soft);
      font-size: 14px;
    }

    .interpretation p + p { margin-top: 8px; }

    /* Comparação */
    .comparison-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
    }

    .comparison-table th,
    .comparison-table td {
      padding: 7px 6px;
      border-bottom: 1px solid var(--line);
      text-align: right;
    }

    .comparison-table th:first-child,
    .comparison-table td:first-child { text-align: left; }

    .comparison-table th {
      color: var(--muted);
      font-weight: 400;
    }

    .comparison-table td:first-child span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .comparison-table td:first-child span::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 2px;
      background: var(--row-color);
    }

    .comparison-table tr.is-current td {
      background: var(--row-active);
      font-weight: 700;
    }

    .table-note { color: var(--muted); font-size: 12.5px; }

    /* Editar */
    .composition-editor {
      width: 100%;
      min-height: 150px;
      resize: vertical;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius-s);
      outline: 0;
      background: var(--code-bg);
      color: var(--ink);
      font-family: var(--mono);
      font-size: 13px;
      line-height: 1.6;
    }

    .composition-editor:focus { border-color: var(--cyan); }

    .composition-editor.is-drop-target {
      border-color: var(--cyan);
      box-shadow: 0 0 0 3px var(--row-active);
    }

    .generic-row {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 6px;
    }

    .generic-row button {
      min-height: 36px;
      border: 1px solid var(--line);
      border-top: 3px solid var(--tile-color);
      border-radius: var(--radius-s);
      background: var(--panel-2);
      font-weight: 700;
    }

    .generic-row button:hover { background: var(--panel); }

    /* Medir */
    .miller-form {
      display: grid;
      gap: 10px;
    }

    .segmented {
      display: grid;
      grid-template-columns: 1fr 1fr;
      padding: 3px;
      border: 1px solid var(--line);
      border-radius: 8px;
    }

    .segmented button {
      min-height: 32px;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      font-size: 14px;
    }

    .segmented button[aria-pressed="true"] {
      background: var(--row-active);
      color: var(--cyan-ink);
      font-weight: 700;
    }

    .miller-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
    }

    .miller-input {
      min-width: 0;
      min-height: 38px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius-s);
      outline: 0;
      background: var(--panel-2);
      font-family: var(--mono);
      font-size: 14px;
    }

    .miller-input:focus { border-color: var(--cyan); }

    .overlay-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .overlay-chip { border-radius: 8px; line-height: 1.35; }
    .overlay-chip em { color: var(--muted); font-style: normal; }

    .overlay-empty { color: var(--muted); font-size: 13px; }

    .link-btn {
      justify-self: start;
      padding: 0;
      border: 0;
      background: none;
      color: var(--cyan-ink);
      font-size: 13.5px;
      text-decoration: underline;
      text-underline-offset: 3px;
    }

    .density-steps {
      display: grid;
      gap: 14px;
      padding: 0;
      list-style: none;
      counter-reset: passo;
    }

    .density-steps[hidden] { display: none; }

    .density-steps li {
      display: grid;
      grid-template-columns: 24px minmax(0, 1fr);
      gap: 10px;
      counter-increment: passo;
    }

    .density-steps li::before {
      content: counter(passo);
      display: grid;
      place-items: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--ink);
      color: var(--panel-2);
      font-size: 12.5px;
      font-weight: 700;
    }

    :root[data-theme="dark"] .density-steps li::before {
      background: var(--accent-on-dark);
      color: #071017;
    }

    .density-steps strong { display: block; font-size: 14px; }

    .density-steps .formula {
      margin-top: 6px;
      padding: 8px 10px;
      border-radius: var(--radius-s);
      background: var(--code-bg);
      font-size: 13.5px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .density-steps p {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
    }

    /* ---------- Terminal recolhível ---------- */
    .console {
      border-top: 1px solid var(--line);
      background: var(--panel-2);
    }

    .console-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 44px;
      padding: 4px 24px;
    }

    .console-toggle {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 34px;
      padding: 0 8px 0 4px;
      border: 0;
      background: none;
      color: var(--ink);
      font-weight: 700;
    }

    .console-toggle svg { transition: transform 160ms ease; }
    .console[data-open="true"] .console-toggle svg { transform: rotate(180deg); }

    .shortcut-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-left: auto;
    }

    .shortcut-row button {
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: transparent;
      color: var(--ink-soft);
      font-family: var(--mono);
      font-size: 12.5px;
    }

    .shortcut-row button:hover { border-color: var(--cyan); color: var(--cyan-ink); }

    .console-body {
      display: grid;
      grid-template-rows: minmax(0, 1fr) auto;
      height: clamp(160px, 30vh, 260px);
      border-top: 1px solid var(--line);
    }

    .console-body[hidden] { display: none; }

    .terminal-log {
      overflow: auto;
      padding: 12px 24px;
      background: #131922;
      color: #dce6ef;
      font-family: var(--mono);
      font-size: 12.5px;
      line-height: 1.55;
      white-space: pre-wrap;
    }

    .terminal-entry { color: #9de4ff; }
    .terminal-error { color: #ff9cab; }
    .terminal-ok { color: #91f2c3; }
    .terminal-step { color: #f2d68a; }

    .terminal-input-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      padding: 8px 24px;
      background: #1a212b;
    }

    .terminal-input {
      min-height: 36px;
      padding: 0 12px;
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: var(--radius-s);
      outline: 0;
      background: #10151d;
      color: #f8fbff;
      font-family: var(--mono);
      font-size: 13px;
    }

    .terminal-input:focus { border-color: var(--accent-on-dark); }

    .terminal-submit {
      min-height: 36px;
      padding: 0 14px;
      border: 0;
      border-radius: var(--radius-s);
      background: var(--accent-on-dark);
      color: #071017;
      font-weight: 700;
    }

    .scrim { display: none; }

    /* ---------- v1.4: lateral recolhível e cena maior ---------- */
    @media (min-width: 1024px) {
      .app[data-sidebar="collapsed"] { grid-template-columns: minmax(0, 1fr); }
      .app[data-sidebar="collapsed"] .sidebar { display: none; }
    }

    .app[data-focus="true"] .inspector,
    .app[data-focus="true"] .readout { display: none; }
    .app[data-focus="true"] .workspace { grid-template-columns: minmax(0, 1fr); }

    .app[data-mode="tutoriais"] .stage-wrap,
    .app[data-mode="tutoriais"] .inspector,
    .app[data-mode="tutoriais"] .readout { display: none; }
    .app[data-mode="tutoriais"] .workspace { grid-template-columns: minmax(0, 1fr); }

    .menu-button svg { flex: 0 0 auto; }

    button.specimen-symbol {
      padding: 0;
      color: var(--ink);
      cursor: pointer;
    }

    button.specimen-symbol:hover { border-color: var(--line-strong); }

    .tile-dot {
      position: absolute;
      top: 7px;
      right: 7px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.4);
    }

    /* Sobreposições da cena em fluxo: quebram linha em vez de se sobrepor */
    .stage-top,
    .stage-bottom {
      position: absolute;
      left: 12px;
      right: 12px;
      z-index: 3;
      pointer-events: none;
    }

    .stage-top {
      top: 12px;
      display: flex;
      flex-wrap: wrap;
      align-items: flex-start;
      gap: 8px;
    }

    .stage-bottom {
      bottom: 12px;
      display: grid;
      justify-items: start;
      gap: 8px;
    }

    .stage-top > *,
    .atom-card,
    .legend-chip.is-editable,
    .legend-reset { pointer-events: auto; }

    .stage-bottom-row {
      width: 100%;
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 8px;
    }

    .thermo {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 38px;
      padding: 4px 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--chip-bg);
      backdrop-filter: blur(8px);
      color: var(--ink-soft);
      font-size: 13px;
    }

    .thermo input[type="range"] { width: 140px; accent-color: var(--red); }

    .thermo output {
      min-width: 66px;
      color: var(--ink);
      font-weight: 700;
      text-align: right;
    }

    .thermo.is-disabled { opacity: 0.6; }
    .thermo.is-hot output { color: var(--red); }

    .layer-divider {
      flex: 0 0 1px;
      align-self: stretch;
      margin: 4px 2px;
      background: var(--line);
    }

    .layer-bar .icon-only {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 32px;
      padding: 0 7px;
    }

    .legend-chip.is-editable { padding-left: 4px; cursor: pointer; }
    .legend-chip em { color: var(--muted); font-style: normal; }
    .legend-reset { cursor: pointer; color: var(--cyan-ink); }

    input[type="color"] {
      width: 20px;
      height: 20px;
      padding: 0;
      border: 0;
      border-radius: 50%;
      background: none;
      cursor: pointer;
    }

    input[type="color"]::-webkit-color-swatch-wrapper { padding: 0; }
    input[type="color"]::-webkit-color-swatch { border: 1px solid rgba(0, 0, 0, 0.3); border-radius: 50%; }
    input[type="color"]::-moz-color-swatch { border: 1px solid rgba(0, 0, 0, 0.3); border-radius: 50%; }

    .atom-card {
      width: min(300px, 100%);
      padding: 10px 12px 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius-m);
      background: var(--panel-2);
      box-shadow: 0 8px 24px rgba(5, 8, 12, 0.18);
      font-size: 13px;
    }

    .atom-card[hidden] { display: none; }

    .atom-card header {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .atom-card header i {
      flex: 0 0 auto;
      width: 14px;
      height: 14px;
      border-radius: 50%;
    }

    .atom-card header strong { font-size: 14.5px; }

    .atom-card .close {
      margin-left: auto;
      min-width: 28px;
      min-height: 28px;
      border: 0;
      border-radius: 6px;
      background: none;
      color: var(--muted);
      font-size: 18px;
      line-height: 1;
    }

    .atom-card .close:hover { background: var(--panel); color: var(--ink); }

    .kv {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 3px 12px;
      margin-top: 6px;
    }

    .kv dt { color: var(--muted); }
    .kv dd { text-align: right; overflow-wrap: anywhere; }

    /* Inspetor: blocos novos */
    .mini-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px 12px;
    }

    .mini-stats dt { color: var(--muted); font-size: 12.5px; }
    .mini-stats dd { font-size: 15px; font-weight: 700; }
    .mini-stats dd small { color: var(--muted); font-size: 12px; font-weight: 400; }

    .thermal-chart { display: block; width: 100%; height: auto; }
    .thermal-chart .axis { stroke: var(--line-strong); stroke-width: 1; }
    .thermal-chart .guide { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 4 4; }
    .thermal-chart .curve { fill: none; stroke: var(--cyan); stroke-width: 2; }
    .thermal-chart .marker { fill: var(--red); stroke: var(--panel-2); stroke-width: 2; }
    .thermal-chart text { fill: var(--muted); font-size: 10px; font-family: var(--font); }

    .note {
      padding: 8px 10px;
      border-left: 3px solid var(--cyan);
      border-radius: 0 6px 6px 0;
      background: var(--code-bg);
      color: var(--ink-soft);
      font-size: 13px;
    }

    .note.is-alert { border-left-color: var(--red); }
    .note + .note { margin-top: 6px; }

    .preset-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .preset-row button {
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: transparent;
      color: var(--ink-soft);
      font-family: var(--mono);
      font-size: 12.5px;
    }

    .preset-row button:hover { border-color: var(--cyan); color: var(--cyan-ink); }

    .preset-row .tag {
      margin-left: 6px;
      color: var(--green);
      font-family: var(--font);
      font-size: 11px;
      font-weight: 700;
    }

    .segmented-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }

    .practice-feedback { font-size: 13.5px; }
    .practice-feedback.is-ok { color: var(--green); font-weight: 700; }
    .practice-feedback.is-bad { color: var(--red); }

    .field {
      display: grid;
      gap: 4px;
      min-width: 0;
      font-size: 13.5px;
    }

    .field > span { color: var(--muted); }
    .field > span small { margin-left: 4px; font-size: 12px; }

    .field select,
    .field input[type="number"] {
      width: 100%;
      min-height: 36px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: var(--radius-s);
      background: var(--panel-2);
    }

    .field select:focus,
    .field input[type="number"]:focus { border-color: var(--cyan); outline: 0; }

    .field-row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .range-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 76px auto;
      gap: 8px;
      align-items: center;
    }

    .range-row input[type="range"] { width: 100%; accent-color: var(--cyan); }

    .check {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      color: var(--ink-soft);
      font-size: 13.5px;
      cursor: pointer;
    }

    .check input { margin-top: 3px; accent-color: var(--cyan); }

    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .liga-form { display: grid; gap: 12px; }

    .rule-list { display: grid; gap: 10px; }

    .rule {
      display: grid;
      grid-template-columns: 22px minmax(0, 1fr) auto;
      gap: 2px 8px;
      align-items: baseline;
      font-size: 14px;
    }

    .rule-mark {
      display: grid;
      place-items: center;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
    }

    .rule-mark.is-ok { background: var(--green); }
    .rule-mark.is-bad { background: var(--red); }
    .rule-value { color: var(--ink-soft); font-family: var(--mono); font-size: 12.5px; }
    .rule small { grid-column: 2 / -1; color: var(--muted); font-size: 12.5px; }

    /* ---------- Tela de entrada ---------- */
    .login {
      position: fixed;
      inset: 0;
      z-index: 100;
      display: grid;
      place-items: center;
      padding: 16px;
      overflow: auto;
      background: radial-gradient(circle at 30% 18%, #1c2a3a 0%, #0b0f15 72%);
    }

    .login[hidden] { display: none; }

    .login-card {
      width: min(420px, 100%);
      display: grid;
      gap: 12px;
      padding: 28px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      background: #11151c;
      color: #eef3f8;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
    }

    .login-card .brand { padding: 0; margin-bottom: 8px; }
    .login-card .brand span { color: #9fadbf; }
    .login-card h1 { font-size: 24px; line-height: 1.2; }
    .login-lead { color: #b5c1d0; font-size: 14.5px; }
    .login-card label[for] { margin-top: 4px; color: #c6d0dc; font-size: 13.5px; }

    .login-card input[type="email"] {
      min-height: 46px;
      padding: 0 12px;
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 8px;
      outline: 0;
      background: #1a212b;
      color: #f8fbff;
    }

    .login-card input[type="email"]:focus { border-color: var(--accent-on-dark); }
    .login-card input[aria-invalid="true"] { border-color: #ff9cab; }
    .login-error { min-height: 1.3em; color: #ff9cab; font-size: 13px; }
    .login-card .check { color: #c6d0dc; }

    .login-card .btn-primary {
      width: 100%;
      min-height: 46px;
      border-color: var(--accent-on-dark);
      background: var(--accent-on-dark);
      color: #071017;
    }

    .login-foot { color: #9fadbf; font-size: 12.5px; }

    .user-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 36px;
      max-width: 280px;
      padding: 0 4px 0 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--ink-soft);
      font-size: 13px;
    }

    .user-chip[hidden] { display: none; }

    .user-avatar {
      flex: 0 0 auto;
      display: grid;
      place-items: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--row-active);
      color: var(--cyan-ink);
      font-size: 12px;
      font-weight: 700;
    }

    .user-email {
      min-width: 0;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .user-chip button {
      min-height: 28px;
      padding: 0 10px;
      border: 0;
      border-radius: 999px;
      background: var(--panel);
      color: var(--ink-soft);
      font-size: 12.5px;
    }

    .user-chip button:hover { color: var(--red); }

    /* ---------- Biblioteca de tutoriais ---------- */
    .library {
      min-height: 0;
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      gap: 16px;
    }

    .library[hidden] { display: none; }

    .library-side {
      min-height: 0;
      overflow-y: auto;
      display: grid;
      align-content: start;
      gap: 12px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--radius-m);
      background: var(--panel-2);
    }

    .library-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .library-head h2 { font-size: 17px; }

    .library-side .miller-input { width: 100%; font-family: var(--font); }
    .library-side { overflow-x: hidden; }
    .library-side code { overflow-wrap: anywhere; word-break: break-all; }

    .filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .filter-row button {
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: transparent;
      color: var(--ink-soft);
      font-size: 13px;
    }

    .filter-row button[aria-pressed="true"] {
      border-color: var(--cyan);
      background: var(--row-active);
      color: var(--cyan-ink);
      font-weight: 700;
    }

    .tutorial-list {
      display: grid;
      gap: 4px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .tutorial-item {
      width: 100%;
      display: grid;
      grid-template-columns: 44px minmax(0, 1fr);
      gap: 1px 10px;
      align-items: center;
      padding: 8px;
      border: 1px solid transparent;
      border-radius: var(--radius-s);
      background: none;
      text-align: left;
    }

    .tutorial-item:hover { background: var(--panel); }
    .tutorial-item.is-active { border-color: var(--cyan); background: var(--row-active); }

    .file-badge {
      grid-row: span 2;
      display: grid;
      place-items: center;
      height: 40px;
      border-radius: 6px;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }

    .file-badge[data-tipo="texto"] { background: #5f6b7d; }
    .file-badge[data-tipo="video"] { background: #ce3f4f; }
    .file-badge[data-tipo="pdf"] { background: #a8323f; }
    .file-badge[data-tipo="planilha"] { background: #19a56b; }
    .file-badge[data-tipo="documento"] { background: #3f6ecf; }

    .tutorial-item strong {
      overflow: hidden;
      font-size: 14px;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .tutorial-item small { color: var(--muted); font-size: 12px; }

    .upload-progress { display: grid; gap: 4px; color: var(--muted); font-size: 12.5px; }
    .upload-progress[hidden] { display: none; }
    .upload-progress progress { width: 100%; accent-color: var(--cyan); }
    .library-status { font-size: 13px; }
    .library-status.is-error { color: var(--red); }

    .library-viewer {
      min-height: 0;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: var(--radius-m);
      background: var(--panel-2);
    }

    .viewer-head {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px 12px;
      padding: 12px 16px;
      border-bottom: 1px solid var(--line);
    }

    .viewer-head h3 {
      min-width: 0;
      margin: 0 auto 0 0;
      font-size: 16px;
      overflow-wrap: anywhere;
    }

    .viewer-head small { color: var(--muted); }
    .viewer-head a.btn { text-decoration: none; }
    .btn-danger:hover { border-color: var(--red); color: var(--red); }

    .viewer-body { min-height: 0; overflow: auto; }
    .viewer-body video { display: block; width: 100%; max-height: 100%; background: #000; }

    .tutorial-frame {
      display: block;
      width: 100%;
      height: 100%;
      min-height: 480px;
      border: 0;
      background: #fff;
    }

    .tutorial-text {
      margin: 0;
      padding: 16px 20px;
      font-family: var(--mono);
      font-size: 13.5px;
      line-height: 1.6;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .sheet-tabs {
      display: flex;
      gap: 6px;
      padding: 8px 12px;
      border-bottom: 1px solid var(--line);
      overflow-x: auto;
    }

    .data-table { border-collapse: collapse; font-size: 13px; }
    .data-table th, .data-table td { padding: 4px 8px; border: 1px solid var(--line); white-space: nowrap; }
    .data-table th { background: var(--code-bg); font-weight: 700; }

    .dropzone {
      display: grid;
      place-content: center;
      justify-items: center;
      gap: 10px;
      min-height: 320px;
      margin: 16px;
      padding: 24px;
      border: 2px dashed var(--line-strong);
      border-radius: var(--radius-m);
      color: var(--muted);
      text-align: center;
    }

    .dropzone strong { color: var(--ink); font-size: 16px; }
    .library.is-dragging .library-viewer { border-color: var(--cyan); background: var(--row-active); }

    /* ---------- Telas menores ---------- */
    @media (max-width: 1180px) {
      .workspace { grid-template-columns: minmax(0, 1fr) 320px; }
      .readout { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .readout > div:nth-child(4) { padding-left: 0; border-left: 0; }
      .readout > div:nth-child(n + 4) { border-top: 1px solid var(--line); }
    }

    /* Projetor e notebooks baixos: cabeçalho mais compacto para sobrar altura à cena */
    @media (min-width: 1024px) and (max-height: 820px) {
      .specimen { padding-top: 12px; padding-bottom: 10px; gap: 10px 24px; }
      .specimen-symbol { width: 52px; height: 52px; font-size: 23px; }
      .specimen-id h1 { font-size: 22px; }
      .readout > div { padding-top: 6px; padding-bottom: 6px; }
      .readout dd { font-size: 18px; }
    }

    @media (max-width: 1023px) {
      .app { grid-template-columns: minmax(0, 1fr); }
      .btn, .mode-switch button, .layer-bar button, .console-toggle, .side-search input, .miller-input, .segmented button { min-height: 44px; }

      .sidebar {
        position: fixed;
        inset: 0 auto 0 0;
        z-index: 40;
        width: min(300px, 86vw);
        transform: translateX(-100%);
        transition: transform 200ms ease;
      }

      .app[data-menu="open"] .sidebar { transform: none; }

      .app[data-menu="open"] .scrim {
        display: block;
        position: fixed;
        inset: 0;
        z-index: 30;
        border: 0;
        background: rgba(5, 8, 12, 0.5);
      }


      .main { height: auto; min-height: 100vh; }

      .workspace { grid-template-columns: 1fr; }

      .stage-wrap { height: 62vh; min-height: 320px; }

      .inspector { overflow: visible; }
    }

    @media (max-width: 640px) {
      body { font-size: 14.5px; }
      .topbar, .specimen, .workspace, .console-bar { padding-left: 16px; padding-right: 16px; }
      .terminal-log, .terminal-input-row { padding-left: 16px; padding-right: 16px; }
      .specimen { grid-template-columns: 1fr; }
      .mode-switch { width: 100%; }
      .mode-switch button { flex: 1; padding: 0 8px; }
      .specimen-symbol { width: 52px; height: 52px; font-size: 22px; }
      .specimen-id h1 { font-size: 21px; }
      .readout { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .readout > div:nth-child(n) { padding-left: 0; border-left: 0; border-top: 0; }
      .readout > div:nth-child(even) { padding-left: 12px; border-left: 1px solid var(--line); }
      .readout > div:nth-child(n + 3) { border-top: 1px solid var(--line); }
      .readout dd { font-size: 18px; }
      .command-label, .stage-hint, .crumb-prefix { display: none; }
      .topbar { padding-top: 6px; padding-bottom: 6px; }
      .topbar .btn { padding: 0 10px; }
      .shortcut-row { display: none; }
      .layer-bar { width: 100%; flex-wrap: nowrap; justify-content: flex-start; overflow-x: auto; scrollbar-width: none; }
      .layer-bar::-webkit-scrollbar { display: none; }
      .layer-bar button { flex: 0 0 auto; }
    }

    @media (max-width: 1023px) {
      .library { grid-template-columns: minmax(0, 1fr); }
      .library-viewer { min-height: 70vh; }
    }

    @media (max-width: 640px) {
      #paletteButton, .menu-label, .user-email { display: none; }
      .stage-top, .stage-bottom { left: 8px; right: 8px; }
      .stage-top { top: 8px; }
      .stage-bottom { bottom: 8px; }
      .thermo { width: 100%; }
      .thermo input[type="range"] { flex: 1; width: auto; }
      .mode-switch { overflow-x: auto; }
      .mode-switch button { padding: 0 6px; font-size: 13.5px; }
      .atom-card { width: 100%; }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { transition: none !important; animation: none !important; }
    }
  </style>
</head>
<body>
  <div class="login" id="loginScreen" hidden>
    <form class="login-card" id="loginForm" novalidate>
      <div class="brand">
        <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
          <path d="M9 12 L22 12 L22 25 L9 25 Z M9 12 L14 7 L27 7 L22 12 M27 7 L27 20 L22 25" fill="none" stroke="#44c5f2" stroke-width="1.6" stroke-linejoin="round" />
          <circle cx="9" cy="12" r="2.4" fill="#44c5f2" /><circle cx="22" cy="12" r="2.4" fill="#44c5f2" />
          <circle cx="9" cy="25" r="2.4" fill="#44c5f2" /><circle cx="22" cy="25" r="2.4" fill="#44c5f2" />
          <circle cx="14" cy="7" r="2.4" fill="#44c5f2" /><circle cx="27" cy="7" r="2.4" fill="#44c5f2" />
          <circle cx="27" cy="20" r="2.4" fill="#44c5f2" /><circle cx="18" cy="16" r="3" fill="#f2c85b" />
        </svg>
        <div>
          <strong>CrystaLab</strong>
          <span>Fundamentos estruturais</span>
        </div>
      </div>
      <h1>Entrar no laboratório</h1>
      <p class="login-lead">Use seu e-mail institucional da UFC. Ele fica gravado neste computador para os próximos acessos.</p>
      <label for="loginEmail">E-mail da UFC</label>
      <input id="loginEmail" type="email" inputmode="email" autocomplete="email" placeholder="nome@alu.ufc.br" aria-describedby="loginError" />
      <p class="login-error" id="loginError" role="alert"></p>
      <label class="check"><input type="checkbox" id="loginRemember" checked /> Lembrar meu e-mail neste computador</label>
      <button class="btn btn-primary" type="submit">Entrar</button>
      <p class="login-foot">Aceita endereços terminados em ufc.br, como @alu.ufc.br. Não há senha: o e-mail identifica quem usa o laboratório.</p>
    </form>
  </div>

  <div class="app" id="app" data-menu="closed" data-sidebar="collapsed" data-mode="explorar" data-focus="false">
    <aside class="sidebar" id="sidebar" aria-label="Escolha do material">
      <div class="brand">
        <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
          <path d="M9 12 L22 12 L22 25 L9 25 Z M9 12 L14 7 L27 7 L22 12 M27 7 L27 20 L22 25" fill="none" stroke="#44c5f2" stroke-width="1.6" stroke-linejoin="round" />
          <circle cx="9" cy="12" r="2.4" fill="#44c5f2" /><circle cx="22" cy="12" r="2.4" fill="#44c5f2" />
          <circle cx="9" cy="25" r="2.4" fill="#44c5f2" /><circle cx="22" cy="25" r="2.4" fill="#44c5f2" />
          <circle cx="14" cy="7" r="2.4" fill="#44c5f2" /><circle cx="27" cy="7" r="2.4" fill="#44c5f2" />
          <circle cx="27" cy="20" r="2.4" fill="#44c5f2" /><circle cx="18" cy="16" r="3" fill="#f2c85b" />
        </svg>
        <div>
          <strong>CrystaLab</strong>
          <span>Fundamentos estruturais</span>
        </div>
      </div>

      <div class="side-search">
        <label class="visually-hidden" for="elementSearch">Buscar metal</label>
        <input id="elementSearch" type="search" placeholder="Buscar metal" autocomplete="off" />
      </div>

      <div class="element-groups" id="blockList" data-testid="block-list"></div>

      <div class="side-foot">Módulo 1, versão 1.4</div>
    </aside>
    <button class="scrim" id="scrim" type="button" aria-label="Fechar lista de metais"></button>

    <div class="main">
      <header class="topbar">
        <div class="topbar-left">
          <button class="btn menu-button" id="menuButton" type="button" aria-controls="sidebar" aria-expanded="false" title="Mostrar ou ocultar a lista de metais">
            <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><rect x="1.5" y="1.5" width="5" height="5" rx="1" fill="none" stroke="currentColor" stroke-width="1.5" /><rect x="9.5" y="1.5" width="5" height="5" rx="1" fill="none" stroke="currentColor" stroke-width="1.5" /><rect x="1.5" y="9.5" width="5" height="5" rx="1" fill="none" stroke="currentColor" stroke-width="1.5" /><rect x="9.5" y="9.5" width="5" height="5" rx="1" fill="none" stroke="currentColor" stroke-width="1.5" /></svg>
            <span class="menu-label">Metais</span>
          </button>
          <p class="crumb"><span class="crumb-prefix">Laboratório de células unitárias <span aria-hidden="true">/</span> </span><strong id="crumbCurrent">Fe</strong></p>
        </div>
        <div class="topbar-actions">
          <button class="btn" id="paletteButton" type="button" title="Abrir o terminal de comandos">
            <span class="command-label">Comando</span><kbd>Ctrl K</kbd>
          </button>
          <button class="btn" id="themeToggle" type="button" aria-pressed="false">Tema escuro</button>
          <div class="user-chip" id="userChip" hidden>
            <span class="user-avatar" id="userAvatar" aria-hidden="true"></span>
            <span class="user-email" id="userEmail"></span>
            <button type="button" id="logoutButton">Sair</button>
          </div>
        </div>
      </header>

      <section class="specimen" aria-labelledby="resultTitle">
        <div class="specimen-id">
          <button class="specimen-symbol" id="specimenSymbol" type="button" title="Escolher outro metal">Fe</button>
          <div>
            <h1 id="resultTitle">Ferro (α)</h1>
            <p id="resultSubtitle">Cúbica de corpo centrado</p>
          </div>
        </div>
        <div class="mode-switch" id="modeSwitch" role="tablist" aria-label="Modo de trabalho"></div>
        <dl class="readout" id="metricsGrid"></dl>
      </section>

      <main class="workspace" id="resultRoot" data-testid="result-root">
        <section class="stage-wrap" aria-label="Visualização 3D">
          <div class="viewer-stage" id="viewerStage" data-testid="viewer-stage"></div>
          <div class="stage-top">
            <div class="thermo" id="thermoBar" title="Temperatura da amostra">
              <label for="tempRange">Temperatura</label>
              <input type="range" id="tempRange" min="-273" max="1800" step="1" value="20" />
              <output id="tempValue" for="tempRange">20 °C</output>
            </div>
            <div class="layer-bar" role="toolbar" aria-label="Camadas da cena" id="layerBar">
              <button type="button" data-toggle="rigid" aria-pressed="false" title="Mostra os átomos com o raio real, encostando uns nos outros">Esferas em contato</button>
              <button type="button" data-toggle="edges" aria-pressed="true">Arestas</button>
              <button type="button" data-toggle="axes" aria-pressed="true">Eixos</button>
              <button type="button" data-toggle="rotate" aria-pressed="false">Girar</button>
              <button type="button" data-toggle="vibrate" aria-pressed="false" title="Átomos vibram com a amplitude da temperatura escolhida">Vibração</button>
              <button type="button" data-toggle="colorpos" aria-pressed="false" title="Colore pela posição na célula em vez do elemento">Cor por posição</button>
              <span class="layer-divider" aria-hidden="true"></span>
              <button type="button" class="icon-only" id="resetViewButton" title="Centralizar a vista" aria-label="Centralizar a vista">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="2.2" fill="currentColor" /><path d="M8 1v3M8 12v3M1 8h3M12 8h3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" /></svg>
              </button>
              <button type="button" class="icon-only" id="focusButton" aria-pressed="false" title="Expandir a cena (oculta os painéis)" aria-label="Expandir a cena">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </button>
              <button type="button" class="icon-only" id="exportPngButton" title="Salvar imagem PNG da cena" aria-label="Salvar imagem PNG">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><rect x="1.5" y="3" width="13" height="10" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5" /><circle cx="8" cy="8" r="2.5" fill="none" stroke="currentColor" stroke-width="1.5" /></svg>
              </button>
              <button type="button" class="icon-only" id="exportXyzButton" title="Exportar coordenadas .xyz (abre no VESTA, Jmol, OVITO ou Avogadro)" aria-label="Exportar coordenadas XYZ">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v8M4.5 6.5 8 10l3.5-3.5M2.5 13.5h11" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </button>
            </div>
          </div>
          <div class="stage-bottom">
            <div class="atom-card" id="atomCard" hidden aria-live="polite"></div>
            <div class="stage-bottom-row">
              <div class="viewer-legend" id="viewerLegend"></div>
              <p class="stage-hint">Clique num átomo para ver suas propriedades</p>
            </div>
          </div>
        </section>

        <aside class="inspector" id="inspector">
          <div class="mode-panel" data-panel="explorar" id="panel-explorar" role="tabpanel">
            <section class="block">
              <h2>Átomos por célula</h2>
              <div id="countBody"></div>
            </section>
            <section class="block interpretation">
              <h2>O que observar</h2>
              <div id="interpretationBody"></div>
            </section>
            <section class="block" id="thermalBlock">
              <h2>Temperatura e vibração</h2>
              <p class="hint" id="thermalHint">Use o controle de temperatura sobre a cena. O metal funde quando a vibração média chega a cerca de 10% da distância entre vizinhos (critério de Lindemann).</p>
              <dl class="mini-stats" id="thermalStats"></dl>
              <div id="thermalChart"></div>
              <div id="thermalNotes"></div>
            </section>
            <section class="block">
              <h2>Comparar estruturas</h2>
              <div id="comparisonTable"></div>
            </section>
          </div>

          <div class="mode-panel" data-panel="editar" id="panel-editar" role="tabpanel" hidden>
            <section class="block">
              <h2>Parâmetros da célula</h2>
              <p class="hint">Altere raio, massa atômica, estrutura ou c/a e aplique. Para partir de um a medido, apague o <code>#</code> da linha <code>a =</code>: o raio sai da condição de contato.</p>
              <label class="visually-hidden" for="parameterEditor">Parâmetros da célula</label>
              <textarea id="parameterEditor" class="composition-editor" spellcheck="false" data-testid="parameter-editor"></textarea>
              <button class="btn btn-primary" id="renderButton" type="button" data-testid="render-button">Aplicar parâmetros</button>
              <p class="hint">Atalho: Ctrl + Enter dentro do campo. Você também pode arrastar um metal da lateral para cá.</p>
            </section>
            <section class="block">
              <h2>Começar de uma célula genérica</h2>
              <p class="hint">Sem metal escolhido, a célula aparece em unidades do raio R.</p>
              <div class="generic-row" id="genericRow"></div>
            </section>
          </div>

          <div class="mode-panel" data-panel="medir" id="panel-medir" role="tabpanel" hidden>
            <section class="block">
              <h2>Planos e direções</h2>
              <p class="hint" id="millerScope">Desenhados na célula unitária.</p>
              <form class="miller-form" id="millerForm">
                <div class="segmented" role="group" aria-label="Tipo de índice">
                  <button type="button" data-mode="plano" aria-pressed="true">Plano (hkl)</button>
                  <button type="button" data-mode="direcao" aria-pressed="false">Direção [uvw]</button>
                </div>
                <div class="miller-row">
                  <label class="visually-hidden" for="millerInput">Índices de Miller</label>
                  <input id="millerInput" class="miller-input" value="1 1 1" autocomplete="off" placeholder="1 1 1 ou 1 0 -1 1" />
                  <button type="submit" class="btn btn-primary">Desenhar</button>
                </div>
              </form>
              <div class="preset-row" id="presetRow" aria-label="Planos e direções importantes"></div>
              <div class="overlay-list" id="overlayList"></div>
              <button type="button" class="link-btn" id="clearOverlaysButton">Remover planos e direções</button>
            </section>
            <section class="block" id="practiceBlock">
              <h2>Praticar: qual é o plano?</h2>
              <p class="hint">Um plano aparece sem rótulo na cena. Escreva os índices de Miller dele.</p>
              <div id="practiceBody"></div>
            </section>
            <section class="block" id="densityPanel">
              <h2>Cálculos passo a passo</h2>
              <div class="segmented segmented-3" id="stepsSwitch" role="group" aria-label="Cálculo exibido">
                <button type="button" data-steps="parametro" aria-pressed="true">Parâmetro a</button>
                <button type="button" data-steps="fea" aria-pressed="false">FEA</button>
                <button type="button" data-steps="densidade" aria-pressed="false">Densidade</button>
              </div>
              <ol class="density-steps" id="densitySteps"></ol>
            </section>
          </div>

          <div class="mode-panel" data-panel="liga" id="panel-liga" role="tabpanel" hidden>
            <section class="block">
              <h2>Formar uma liga</h2>
              <p class="hint">O solvente define a rede. Metais entram por substituição; C, N e H ocupam os interstícios.</p>
              <form class="liga-form" id="ligaForm">
                <div class="field-row">
                  <label class="field"><span>Solvente</span><select id="ligaBase"></select></label>
                  <label class="field"><span>Soluto</span><select id="ligaSoluto"></select></label>
                </div>
                <div class="field">
                  <span>Composição <small id="ligaXHint">% atômica do soluto</small></span>
                  <div class="range-row">
                    <input type="range" id="ligaXRange" min="0" max="100" step="1" value="30" aria-label="Composição em porcentagem atômica" />
                    <input type="number" id="ligaX" min="0" max="100" step="0.5" value="30" aria-label="Composição em porcentagem atômica" />
                    <span>%</span>
                  </div>
                  <small class="hint" id="ligaPeso"></small>
                </div>
                <div class="field-row">
                  <label class="field"><span>Supercélula</span>
                    <select id="ligaN"><option value="2">2 × 2 × 2</option><option value="3" selected>3 × 3 × 3</option><option value="4">4 × 4 × 4</option></select>
                  </label>
                  <label class="field"><span>Arranjo</span>
                    <select id="ligaArranjo"><option value="aleatorio">Aleatório</option><option value="ordenado">Ordenado</option></select>
                  </label>
                </div>
                <label class="check"><input type="checkbox" id="ligaDistorcer" /> Mostrar distorção local da rede (ilustrativa)</label>
                <label class="check"><input type="checkbox" id="ligaDestacar" /> Destacar o soluto (solvente translúcido)</label>
                <div class="button-row">
                  <button type="submit" class="btn btn-primary">Formar liga</button>
                  <button type="button" class="btn" id="ligaSorteio" title="Sorteia outra distribuição aleatória com a mesma composição">Nova distribuição</button>
                </div>
              </form>
              <button type="button" class="link-btn" id="ligaVoltar" hidden>Voltar à célula unitária do solvente</button>
            </section>
            <section class="block" id="ligaRegrasBlock" hidden>
              <h2>Regras de Hume-Rothery</h2>
              <div class="rule-list" id="ligaRegras"></div>
              <p class="note" id="ligaConclusao"></p>
            </section>
            <section class="block" id="ligaPropsBlock" hidden>
              <h2>Composição e propriedades</h2>
              <dl class="mini-stats" id="ligaProps"></dl>
              <div id="ligaNotas"></div>
            </section>
            <section class="block" id="ligaPassosBlock" hidden>
              <h2>Como os valores foram calculados</h2>
              <ol class="density-steps" id="ligaPassos"></ol>
            </section>
          </div>
        </aside>

        <section class="library" id="tutorialsView" role="tabpanel" hidden>
          <div class="library-side">
            <div class="library-head">
              <h2>Tutoriais</h2>
              <button class="btn btn-primary" id="uploadButton" type="button">Adicionar arquivos</button>
              <input type="file" id="uploadInput" multiple hidden />
            </div>
            <label class="visually-hidden" for="tutorialSearch">Buscar tutorial</label>
            <input type="search" id="tutorialSearch" class="miller-input" placeholder="Buscar pelo nome" autocomplete="off" />
            <div class="filter-row" id="tutorialFilters" role="group" aria-label="Filtrar por tipo"></div>
            <div class="upload-progress" id="uploadProgress" hidden>
              <span id="uploadLabel"></span>
              <progress id="uploadBar" max="100" value="0"></progress>
            </div>
            <p class="library-status hint" id="libraryStatus" role="status"></p>
            <ul class="tutorial-list" id="tutorialList"></ul>
            <p class="hint">Aceita .txt, .md, .mp4, .webm, .pdf, .csv, .xlsx, .xls, .ods, .docx, .doc e .odt. Arquivos copiados direto para a pasta <code id="tutorialFolder">tutoriais</code> também aparecem aqui.</p>
          </div>
          <div class="library-viewer" id="tutorialViewer"></div>
        </section>
      </main>

      <section class="console" id="console" data-open="false" aria-label="Terminal de comandos">
        <div class="console-bar">
          <button type="button" class="console-toggle" id="consoleToggle" aria-expanded="false" aria-controls="consoleBody">
            <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 10 L8 6 L12 10" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
            Terminal
          </button>
          <span class="hint">Ctrl J</span>
          <div class="shortcut-row">
            <button type="button" data-command="liga Cu Ni 30">liga Cu Ni 30</button>
            <button type="button" data-command="temperatura 800">temperatura 800</button>
            <button type="button" data-command="plano 1 1 1">plano 1 1 1</button>
            <button type="button" data-command="ajuda">ajuda</button>
          </div>
        </div>
        <div class="console-body" id="consoleBody" hidden>
          <div id="terminalLog" class="terminal-log" data-testid="terminal-log" role="log"></div>
          <form class="terminal-input-row" id="terminalForm">
            <label class="visually-hidden" for="terminalInput">Comando</label>
            <input id="terminalInput" class="terminal-input" autocomplete="off" placeholder="Digite um comando, por exemplo: usar Cu" />
            <button class="terminal-submit" type="submit">Enviar</button>
          </form>
        </div>
      </section>
    </div>
  </div>

  <script>
    window.BOOTSTRAP_DATA = __BOOTSTRAP_JSON__;
  </script>
  <script>
    /* =====================================================================
       Registro de módulos: modos, comandos e camadas conversam por eventos.
       ===================================================================== */
    const CrystaLab = (() => {
      const modos = [];
      const comandos = [];
      const camadas = [];
      const ouvintes = new Map();
      return {
        versao: "1.4",
        registrarModo(def) { modos.push(def); },
        modos() { return modos.slice(); },
        registrarComando(def) { comandos.push(def); },
        comandos() { return comandos.slice(); },
        registrarCamada(def) { camadas.push(def); },
        camadas() { return camadas.slice(); },
        publicar(evento, dados) {
          (ouvintes.get(evento) || []).forEach((fn) => {
            try { fn(dados); } catch (error) { console.error(`[CrystaLab] ${evento}:`, error); }
          });
        },
        assinar(evento, fn) {
          if (!ouvintes.has(evento)) ouvintes.set(evento, []);
          ouvintes.get(evento).push(fn);
          return () => ouvintes.set(evento, ouvintes.get(evento).filter((item) => item !== fn));
        }
      };
    })();
    window.CrystaLab = CrystaLab;

    const data = window.BOOTSTRAP_DATA;
    const STRUCTURE_ORDER = ["CCC", "CFC", "HC", "CS"];
    const STRUCTURE_COLORS = { CCC: "var(--s-CCC)", CFC: "var(--s-CFC)", HC: "var(--s-HC)", CS: "var(--s-CS)" };
    const TYPE_COLORS = { vertice: "#1aa7d9", centro: "#d79319", face: "#19a56b", basal: "#19a56b", interior: "#7256d9", rede: "#1aa7d9", intersticial: "#7256d9" };
    const TYPE_LABELS = { vertice: "vértice", centro: "centro do cubo", face: "centro de face", basal: "centro basal", interior: "interior", rede: "sítio da rede", intersticial: "sítio intersticial" };
    const OVERLAY_COLORS = ["#ce3f4f", "#f2a73b", "#7256d9", "#19a56b", "#ff6fa5", "#3f6ecf"];
    const UFC_EMAIL = /^[a-z0-9._%+-]+@([a-z0-9-]+\.)*ufc\.br$/i;
    const REDUCED_MOTION = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Planos e direções que todo curso cobra; "true" marca os compactos.
    const PRESETS = {
      CS: [["plano", [1, 0, 0], true], ["plano", [1, 1, 0]], ["plano", [1, 1, 1]], ["direcao", [1, 0, 0], true], ["direcao", [1, 1, 1]]],
      CCC: [["plano", [1, 1, 0], true], ["plano", [1, 0, 0]], ["plano", [1, 1, 1]], ["direcao", [1, 1, 1], true], ["direcao", [1, 0, 0]]],
      CFC: [["plano", [1, 1, 1], true], ["plano", [1, 0, 0]], ["plano", [1, 1, 0]], ["direcao", [1, 1, 0], true], ["direcao", [1, 0, 0]]],
      HC: [["plano", [0, 0, 0, 1], true], ["plano", [1, 0, -1, 0]], ["plano", [1, 0, -1, 1]], ["direcao", [2, -1, -1, 0], true], ["direcao", [0, 0, 0, 1]]]
    };
    const PRACTICE = {
      cubic: [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1], [-1, 1, 0], [1, -1, 1], [1, 1, -1], [2, 0, 0], [1, 2, 0]],
      HC: [[0, 0, 0, 1], [1, 0, -1, 0], [0, 1, -1, 0], [1, -1, 0, 0], [1, 0, -1, 1], [0, 1, -1, 1], [1, 1, -2, 0]]
    };
    const DEFAULT_SOLUTE = { Fe: "C", Cu: "Ni", Ni: "Cu", Al: "Mg", Ag: "Au", Au: "Ag", Cr: "Mo", Mo: "W", W: "Mo", Ti: "Al", Mg: "Zn", Zn: "Mg", Co: "Ni", Pb: "Ag", Po: "Pb" };
    const FILE_TYPES = {
      texto: { rotulo: "Textos", selo: "TXT" },
      video: { rotulo: "Vídeos", selo: "VÍDEO" },
      pdf: { rotulo: "PDFs", selo: "PDF" },
      planilha: { rotulo: "Planilhas", selo: "PLAN" },
      documento: { rotulo: "Documentos", selo: "DOC" }
    };
    const LIBS = {
      xlsx: "https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js",
      mammoth: "https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js"
    };

    const state = {
      user: null,
      current: null,
      liga: null,
      scene: "celula",
      selectedKey: "",
      workMode: "explorar",
      mode: "plano",
      overlays: [],
      rigid: false,
      autoRotate: false,
      showAxes: true,
      showEdges: true,
      vibrate: false,
      colorMode: "elemento",
      elementColors: {},
      temperature: 20,
      thermal: null,
      selectedAtom: null,
      stepsTab: "parametro",
      practice: null,
      highlightSolute: false,
      ligaSeed: 1,
      consoleOpen: false,
      theme: "light",
      sidebar: "collapsed",
      focus: false,
      tutorials: [],
      tutorialFolder: "",
      tutorialFilter: "todos",
      tutorialOpen: null
    };

    const $ = (id) => document.getElementById(id);
    const blockList = $("blockList");
    const editor = $("parameterEditor");
    const terminalLog = $("terminalLog");
    const terminalInput = $("terminalInput");
    const viewerStage = $("viewerStage");
    const viewerLegend = $("viewerLegend");
    const overlayList = $("overlayList");
    const millerInput = $("millerInput");
    const densitySteps = $("densitySteps");
    const themeToggle = $("themeToggle");
    const tempRange = $("tempRange");

    /* ---------- Armazenamento local tolerante a falhas ---------- */
    const store = {
      get(key, session = false) {
        try { return (session ? sessionStorage : localStorage).getItem(key); } catch (error) { return null; }
      },
      set(key, value, session = false) {
        try { (session ? sessionStorage : localStorage).setItem(key, value); } catch (error) {}
      },
      remove(key) {
        try { localStorage.removeItem(key); sessionStorage.removeItem(key); } catch (error) {}
      }
    };

    function ptNumber(value, digits = 2) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/d";
      if (!Number.isFinite(Number(value))) return "∞";
      return Number(value).toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    }

    function compactNumber(value) {
      const number = Number(value);
      if (!Number.isFinite(number)) return String(value);
      if (Math.abs(number - Math.round(number)) < 0.0001) return String(Math.round(number));
      return number.toFixed(2).replace(".", ",");
    }

    // Sinal explícito, sem "−0,00" quando o valor arredondado é zero
    function signedNumber(value, digits = 2) {
      const rounded = Number(Number(value).toFixed(digits));
      return `${rounded > 0 ? "+" : ""}${ptNumber(rounded === 0 ? 0 : rounded, digits)}`;
    }

    function fracText(value) {
      const number = Number(value);
      if (Math.abs(number - Math.round(number)) < 1e-4) return String(Math.round(number));
      for (let q = 2; q <= 6; q++) {
        const p = Math.round(number * q);
        if (Math.abs(number * q - p) < 1e-3) return `${p}/${q}`;
      }
      return ptNumber(number, 3);
    }

    function fileSize(bytes) {
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 ** 2) return `${ptNumber(bytes / 1024, 0)} KB`;
      if (bytes < 1024 ** 3) return `${ptNumber(bytes / 1024 ** 2, 1)} MB`;
      return `${ptNumber(bytes / 1024 ** 3, 2)} GB`;
    }

    function plainText(text) {
      return String(text).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
    }

    function escapeHtml(text) {
      return String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    }

    function logLine(text, className = "") {
      const line = document.createElement("div");
      if (className) line.className = className;
      line.textContent = text;
      terminalLog.appendChild(line);
      terminalLog.scrollTop = terminalLog.scrollHeight;
    }

    async function postJson(url, payload, { quiet = false } = {}) {
      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CrystaLab": "1" },
          body: JSON.stringify(payload)
        });
        const body = await response.json();
        if (!response.ok || !body.ok) {
          const message = body.error || "A requisição falhou.";
          if (!quiet) {
            logLine(message, "terminal-error");
            CrystaLab.publicar("erro", message);
          }
          return null;
        }
        return body.result;
      } catch (error) {
        const message = `Sem resposta do servidor: ${error.message}`;
        if (!quiet) {
          logLine(message, "terminal-error");
          CrystaLab.publicar("erro", message);
        }
        return null;
      }
    }

    function downloadUrl(url, name) {
      const link = document.createElement("a");
      link.href = url;
      link.download = name;
      document.body.appendChild(link);
      link.click();
      link.remove();
    }

    /* ---------- Elementos e cores ---------- */
    function elementInfo(symbol) {
      return (symbol && (data.metais[symbol] || data.intersticiais[symbol])) || null;
    }

    function elementColor(symbol) {
      return state.elementColors[symbol] || (elementInfo(symbol) || {}).cor || "#1aa7d9";
    }

    function atomColor(atom) {
      if (state.colorMode === "elemento" && atom.elemento) return elementColor(atom.elemento);
      return TYPE_COLORS[atom.tipo] || "#1aa7d9";
    }

    function sceneResult() {
      return state.scene === "liga" && state.liga ? state.liga : state.current;
    }

    /* =====================================================================
       Cena 3D (Three.js)
       ===================================================================== */

    function disposeGroup(group) {
      while (group.children.length) {
        const child = group.children[0];
        group.remove(child);
        child.traverse((object) => {
          if (object.geometry && object.geometry !== viewer.sphereGeometry) object.geometry.dispose();
          if (object.material) {
            const materials = Array.isArray(object.material) ? object.material : [object.material];
            materials.forEach((material) => {
              if (material.map) material.map.dispose();
              material.dispose();
            });
          }
        });
      }
    }

    function makeLabel(text, color, size = 0.13) {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      const font = "700 64px 'Atkinson Hyperlegible', Segoe UI, Arial";
      context.font = font;
      const width = Math.ceil(context.measureText(text).width) + 36;
      canvas.width = width;
      canvas.height = 96;
      context.font = font;
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.lineWidth = 10;
      context.strokeStyle = state.theme === "dark" ? "rgba(10,14,19,0.9)" : "rgba(255,255,255,0.92)";
      context.strokeText(text, width / 2, 50);
      context.fillStyle = color;
      context.fillText(text, width / 2, 50);
      const texture = new THREE.CanvasTexture(canvas);
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false, transparent: true }));
      const scaled = size * viewer.labelScale;
      sprite.scale.set(scaled * (width / 96), scaled, 1);
      sprite.renderOrder = 10;
      return sprite;
    }

    function makeArrow(start, end, color, radius) {
      const s = new THREE.Vector3(...start);
      const e = new THREE.Vector3(...end);
      const direction = e.clone().sub(s);
      const length = direction.length();
      direction.normalize();
      const headLength = Math.min(0.13 * viewer.labelScale, length * 0.3);
      const material = new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.1 });
      const orientation = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
      const shaft = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length - headLength, 14), material);
      shaft.position.copy(s).addScaledVector(direction, (length - headLength) / 2);
      shaft.quaternion.copy(orientation);
      const head = new THREE.Mesh(new THREE.ConeGeometry(radius * 3, headLength, 18), material);
      head.position.copy(s).addScaledVector(direction, length - headLength / 2);
      head.quaternion.copy(orientation);
      const group = new THREE.Group();
      group.add(shaft, head);
      return group;
    }

    const viewer = {
      ready: false,
      atomMeshes: [],
      boundRadius: 1,
      labelScale: 1,
      vibrating: false,

      init() {
        if (!window.THREE) {
          viewerStage.insertAdjacentHTML("beforeend", '<div class="viewer-fallback">A cena 3D não carregou porque o Three.js não foi baixado. Verifique a conexão com a internet e recarregue a página.<br />Os cálculos de FEA, densidade, ligas e índices continuam funcionando.</div>');
          logLine("Three.js indisponível: cena 3D desativada.", "terminal-error");
          return;
        }
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setClearColor(0x000000, 0);
        viewerStage.appendChild(renderer.domElement);

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(36, 1, 0.01, 200);
        scene.add(new THREE.AmbientLight(0xffffff, 0.55));
        const keyLight = new THREE.DirectionalLight(0xffffff, 0.85);
        keyLight.position.set(4, 6, 5);
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.35);
        fillLight.position.set(-5, -2, -4);
        scene.add(keyLight, fillLight);

        const pivot = new THREE.Group();
        const crystal = new THREE.Group();
        crystal.rotation.x = -Math.PI / 2;
        const frame = new THREE.Group();
        const atomsGroup = new THREE.Group();
        const edgesGroup = new THREE.Group();
        const overlaysGroup = new THREE.Group();
        const axesGroup = new THREE.Group();
        frame.add(edgesGroup, atomsGroup, overlaysGroup, axesGroup);
        crystal.add(frame);
        pivot.add(crystal);
        scene.add(pivot);

        Object.assign(this, { renderer, scene, camera, pivot, crystal, frame, atomsGroup, edgesGroup, overlaysGroup, axesGroup });
        this.sphereGeometry = new THREE.SphereGeometry(1, 32, 20);

        if (THREE.OrbitControls) {
          this.controls = new THREE.OrbitControls(camera, renderer.domElement);
          this.controls.enableDamping = true;
          this.controls.dampingFactor = 0.08;
          this.controls.autoRotateSpeed = 1.6;
          this.controls.enablePan = false;
        } else {
          this.setupManualControls();
        }
        this.setupPicking();

        const resize = () => {
          const width = viewerStage.clientWidth || 600;
          const height = viewerStage.clientHeight || 420;
          const before = this.ready ? this.fitDistance() : 0;
          renderer.setSize(width, height);
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
          // Mantém o enquadramento (sem desfazer a rotação do usuário) quando a cena muda de proporção
          if (before) {
            const after = this.fitDistance();
            camera.position.multiplyScalar(after / before);
            this.setDistanceLimits(after);
          }
        };
        if (window.ResizeObserver) new ResizeObserver(resize).observe(viewerStage);
        window.addEventListener("resize", resize);
        resize();

        const loop = (time) => {
          requestAnimationFrame(loop);
          if (this.controls) {
            this.controls.autoRotate = state.autoRotate;
            this.controls.update();
          } else if (state.autoRotate) {
            this.pivot.rotation.y += 0.006;
          }
          this.animateVibration((time || 0) / 1000);
          renderer.render(scene, camera);
        };
        this.ready = true;
        requestAnimationFrame(loop);
      },

      setupManualControls() {
        const canvas = this.renderer.domElement;
        let dragging = false;
        let lastX = 0;
        let lastY = 0;
        canvas.addEventListener("pointerdown", (event) => {
          dragging = true;
          lastX = event.clientX;
          lastY = event.clientY;
          canvas.setPointerCapture(event.pointerId);
        });
        canvas.addEventListener("pointermove", (event) => {
          if (!dragging) return;
          this.pivot.rotation.y += (event.clientX - lastX) * 0.01;
          this.pivot.rotation.x = Math.max(-1.4, Math.min(1.4, this.pivot.rotation.x + (event.clientY - lastY) * 0.01));
          lastX = event.clientX;
          lastY = event.clientY;
        });
        canvas.addEventListener("pointerup", () => { dragging = false; });
        canvas.addEventListener("wheel", (event) => {
          event.preventDefault();
          const factor = event.deltaY > 0 ? 1.08 : 0.92;
          this.camera.position.multiplyScalar(factor);
        }, { passive: false });
      },

      // Clique sem arrastar seleciona o átomo sob o cursor
      setupPicking() {
        const canvas = this.renderer.domElement;
        const raycaster = new THREE.Raycaster();
        const pointer = new THREE.Vector2();
        let start = null;
        canvas.addEventListener("pointerdown", (event) => { start = [event.clientX, event.clientY]; });
        canvas.addEventListener("pointerup", (event) => {
          if (!start || Math.hypot(event.clientX - start[0], event.clientY - start[1]) > 5) return;
          start = null;
          const rect = canvas.getBoundingClientRect();
          pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
          raycaster.setFromCamera(pointer, this.camera);
          const hits = raycaster.intersectObjects(this.atomMeshes, false);
          selectAtom(hits.length ? hits[0].object.userData.index : null);
        });
      },

      // Distância que enquadra a célula (com margem para eixos e esferas) no menor ângulo de visão
      fitDistance() {
        const halfV = THREE.MathUtils.degToRad(this.camera.fov / 2);
        const halfH = Math.atan(Math.tan(halfV) * this.camera.aspect);
        return (this.boundRadius + 0.3 * this.labelScale) / Math.tan(Math.min(halfV, halfH));
      },

      setDistanceLimits(distance) {
        if (!this.controls) return;
        this.controls.minDistance = distance * 0.25;
        this.controls.maxDistance = distance * 3;
      },

      edgeColor() {
        return state.theme === "dark" ? 0xa9b6c6 : 0x29313f;
      },

      build(result) {
        if (!this.ready) return;
        [this.atomsGroup, this.edgesGroup, this.overlaysGroup, this.axesGroup].forEach(disposeGroup);

        const min = [Infinity, Infinity, Infinity];
        const max = [-Infinity, -Infinity, -Infinity];
        const positions = [];
        result.arestas.forEach(([a, b]) => {
          positions.push(...a, ...b);
          [a, b].forEach((p) => p.forEach((v, i) => { min[i] = Math.min(min[i], v); max[i] = Math.max(max[i], v); }));
        });
        const center = min.map((v, i) => (v + max[i]) / 2);
        this.frame.position.set(-center[0], -center[1], -center[2]);
        this.boundRadius = Math.hypot(max[0] - min[0], max[1] - min[1], max[2] - min[2]) / 2;
        this.labelScale = Math.max(1, Math.pow(this.boundRadius / 0.866, 0.8));

        const edgeGeometry = new THREE.BufferGeometry();
        edgeGeometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
        this.edgeMaterial = new THREE.LineBasicMaterial({ color: this.edgeColor() });
        this.edgesGroup.add(new THREE.LineSegments(edgeGeometry, this.edgeMaterial));
        this.edgesGroup.visible = state.showEdges;

        this.atomMeshes = result.atomos.map((atom, index) => {
          const material = new THREE.MeshStandardMaterial({ color: atomColor(atom), roughness: 0.32, metalness: 0.22 });
          const mesh = new THREE.Mesh(this.sphereGeometry, material);
          mesh.position.set(...atom.pos);
          // Fases e frequências fixas por átomo: a vibração parece térmica sem sortear a cada quadro
          mesh.userData = {
            index,
            base: new THREE.Vector3(...atom.pos),
            radius: atom.raio_rel != null ? atom.raio_rel : result.raio_relativo,
            phase: [index * 2.399, index * 1.713 + 1, index * 0.911 + 2],
            freq: [9 + (index * 37 % 7) * 0.7, 10 + (index * 53 % 5) * 0.8, 8 + (index * 29 % 6) * 0.9]
          };
          this.atomsGroup.add(mesh);
          return mesh;
        });
        this.vibrating = false;
        this.updateAtomScale();
        this.applyAtomStyles();
        this.applyThermal();
        this.buildAxes(result);
        this.resetView();
      },

      updateAtomScale() {
        if (!this.ready) return;
        this.atomMeshes.forEach((mesh) => {
          const selected = mesh.userData.index === state.selectedAtom ? 1.12 : 1;
          mesh.scale.setScalar(mesh.userData.radius * (state.rigid ? 1 : 0.32) * selected);
        });
      },

      applyAtomStyles() {
        const result = sceneResult();
        if (!this.ready || !result) return;
        const colorByAtom = new Map();
        state.overlays.forEach((overlay) => {
          overlay.atomos.forEach((index) => {
            if (!colorByAtom.has(index)) colorByAtom.set(index, overlay.color);
          });
        });
        const fade = state.scene === "liga" && state.highlightSolute && state.liga;
        this.atomMeshes.forEach((mesh, index) => {
          const atom = result.atomos[index];
          const material = mesh.material;
          material.color.set(atomColor(atom));
          const glow = index === state.selectedAtom ? "#ffffff" : colorByAtom.get(index);
          material.emissive.set(glow || 0x000000);
          material.emissiveIntensity = index === state.selectedAtom ? 0.35 : (glow ? 0.45 : 0);
          const faded = fade && atom.elemento === state.liga.base;
          material.transparent = faded;
          material.opacity = faded ? 0.16 : 1;
          material.depthWrite = !faded;
          material.needsUpdate = true;
        });
      },

      applyThermal() {
        if (!this.ready) return;
        this.crystal.scale.setScalar(state.thermal ? state.thermal.fator : 1);
      },

      animateVibration(time) {
        if (!this.ready) return;
        const thermal = state.thermal;
        const amplitude = state.vibrate && thermal ? thermal.amplitude_rel * Math.sqrt(2 / 3) : 0;
        if (!amplitude) {
          if (this.vibrating) {
            this.atomMeshes.forEach((mesh) => mesh.position.copy(mesh.userData.base));
            this.vibrating = false;
          }
          return;
        }
        this.vibrating = true;
        const speed = REDUCED_MOTION ? 0.2 : 1;
        this.atomMeshes.forEach((mesh) => {
          const { base, phase, freq } = mesh.userData;
          mesh.position.set(
            base.x + amplitude * Math.sin(freq[0] * speed * time + phase[0]),
            base.y + amplitude * Math.sin(freq[1] * speed * time + phase[1]),
            base.z + amplitude * Math.sin(freq[2] * speed * time + phase[2])
          );
        });
      },

      buildAxes(result) {
        disposeGroup(this.axesGroup);
        const cells = result.supercelula || 1;
        const reach = cells > 1 ? cells + 0.35 : 1.32;
        let vectors;
        if (result.estrutura === "HC" && cells > 1) {
          vectors = [
            [[reach, 0, 0], "a₁", "#ce3f4f"],
            [[-reach / 2, reach * Math.sqrt(3) / 2, 0], "a₂", "#19a56b"],
            [[0, 0, result.c_a * (cells + 0.3)], "c", "#1aa7d9"]
          ];
        } else if (result.estrutura === "HC") {
          vectors = [
            [[1.3, 0, 0], "a₁", "#ce3f4f"],
            [[-0.65, 1.126, 0], "a₂", "#19a56b"],
            [[-0.65, -1.126, 0], "a₃", "#d79319"],
            [[0, 0, result.c_a * 1.28], "c", "#1aa7d9"]
          ];
        } else {
          vectors = [[[reach, 0, 0], "x", "#ce3f4f"], [[0, reach, 0], "y", "#19a56b"], [[0, 0, reach], "z", "#1aa7d9"]];
        }
        vectors.forEach(([tip, label, color]) => {
          this.axesGroup.add(makeArrow([0, 0, 0], tip, color, 0.007 * this.labelScale));
          const sprite = makeLabel(label, color, 0.11);
          sprite.position.set(tip[0] * 1.08, tip[1] * 1.08, tip[2] * 1.06);
          this.axesGroup.add(sprite);
        });
        const origin = makeLabel("O", state.theme === "dark" ? "#c6d0dc" : "#29313f", 0.09);
        origin.position.set(-0.07, -0.07, -0.07);
        this.axesGroup.add(origin);
        this.axesGroup.visible = state.showAxes;
      },

      resetView() {
        if (!this.ready) return;
        const distance = this.fitDistance();
        const direction = new THREE.Vector3(1, 0.62, -0.48).normalize();
        this.camera.position.copy(direction.multiplyScalar(distance));
        this.camera.lookAt(0, 0, 0);
        this.pivot.rotation.set(0, 0, 0);
        if (this.controls) {
          this.controls.target.set(0, 0, 0);
          this.setDistanceLimits(distance);
          this.controls.update();
        }
      },

      addOverlay(overlay) {
        if (!this.ready) return;
        const group = new THREE.Group();
        if (overlay.tipo === "plano") {
          const faces = overlay.poligonos && overlay.poligonos.length
            ? overlay.poligonos
            : [{ pontos: overlay.poligono, centro: overlay.centro }];
          faces.forEach((face) => {
            const triangles = [];
            for (let i = 0; i < face.pontos.length; i++) {
              triangles.push(...face.centro, ...face.pontos[i], ...face.pontos[(i + 1) % face.pontos.length]);
            }
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute("position", new THREE.Float32BufferAttribute(triangles, 3));
            const fill = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
              color: overlay.color, transparent: true, opacity: faces.length > 1 ? 0.22 : 0.32, side: THREE.DoubleSide, depthWrite: false
            }));
            fill.renderOrder = 2;
            const outlineGeometry = new THREE.BufferGeometry();
            outlineGeometry.setAttribute("position", new THREE.Float32BufferAttribute(face.pontos.flat(), 3));
            group.add(fill, new THREE.LineLoop(outlineGeometry, new THREE.LineBasicMaterial({ color: overlay.color })));
          });
          if (!overlay.hideLabel) {
            const label = makeLabel(overlay.notacao, overlay.color, 0.12);
            const c = overlay.centro;
            label.position.set(c[0] + overlay.normal[0] * 0.06, c[1] + overlay.normal[1] * 0.06, c[2] + overlay.normal[2] * 0.06);
            group.add(label);
          }
        } else {
          group.add(makeArrow(overlay.inicio, overlay.fim, overlay.color, 0.016 * this.labelScale));
          const label = makeLabel(overlay.notacao, overlay.color, 0.12);
          label.position.set(
            overlay.inicio[0] + (overlay.fim[0] - overlay.inicio[0]) * 0.6,
            overlay.inicio[1] + (overlay.fim[1] - overlay.inicio[1]) * 0.6,
            overlay.inicio[2] + (overlay.fim[2] - overlay.inicio[2]) * 0.6 + 0.08
          );
          group.add(label);
        }
        this.overlaysGroup.add(group);
        this.applyAtomStyles();
      },

      redrawOverlays() {
        if (!this.ready) return;
        disposeGroup(this.overlaysGroup);
        state.overlays.forEach((overlay) => this.addOverlay(overlay));
        this.applyAtomStyles();
      },

      applyTheme() {
        const result = sceneResult();
        if (!this.ready || !result) return;
        if (this.edgeMaterial) this.edgeMaterial.color.setHex(this.edgeColor());
        this.buildAxes(result);
        this.redrawOverlays();
      }
    };

    /* ---------- Legenda: cores editáveis por elemento ---------- */
    function renderLegend(result) {
      const symbols = result.base
        ? [result.base, result.soluto]
        : [...new Set(result.atomos.map((atom) => atom.elemento).filter(Boolean))];
      if (state.colorMode === "elemento" && symbols.length) {
        const custom = symbols.some((symbol) => state.elementColors[symbol]);
        viewerLegend.innerHTML = symbols.map((symbol) => {
          const info = elementInfo(symbol);
          return `<label class="legend-chip is-editable" title="Clique na bolinha para mudar a cor de ${escapeHtml(info.nome)}">
              <input type="color" data-element="${symbol}" value="${elementColor(symbol)}" aria-label="Cor de ${escapeHtml(info.nome)}" />
              <span>${symbol}</span><em>${escapeHtml(info.nome)}</em></label>`;
        }).join("") + (custom ? '<button type="button" class="legend-chip legend-reset" id="resetColors">Restaurar cores</button>' : "");
        return;
      }
      const groups = result.contagem
        ? result.contagem.map((group) => ({ tipo: group.tipo, texto: `${TYPE_LABELS[group.tipo]} (${group.fracao_txt})` }))
        : [...new Set(result.atomos.map((atom) => atom.tipo))].map((tipo) => ({ tipo, texto: TYPE_LABELS[tipo] }));
      viewerLegend.innerHTML = groups.map((group) => `
        <span class="legend-chip"><i style="background:${TYPE_COLORS[group.tipo]}"></i>${group.texto}</span>`).join("");
    }

    function setElementColor(symbol, color) {
      if (color) state.elementColors[symbol] = color;
      else delete state.elementColors[symbol];
      store.set("crystalab-cores", JSON.stringify(state.elementColors));
      viewer.applyAtomStyles();
      renderBlocks($("elementSearch").value);
      renderAtomCard();
    }

    /* ---------- Átomo selecionado ---------- */
    function selectAtom(index) {
      state.selectedAtom = index;
      viewer.updateAtomScale();
      viewer.applyAtomStyles();
      renderAtomCard();
    }

    function renderAtomCard() {
      const card = $("atomCard");
      const result = sceneResult();
      const atom = result && state.selectedAtom != null ? result.atomos[state.selectedAtom] : null;
      if (!atom) {
        card.hidden = true;
        return;
      }
      const info = elementInfo(atom.elemento);
      const frac = atom.frac || atom.pos;
      const a = result.a_nm;
      const rows = [
        ["Sítio", TYPE_LABELS[atom.tipo] + (atom.fracao_txt ? ` (conta ${atom.fracao_txt})` : "")],
        ["Posição fracionária", `(${frac.map(fracText).join(", ")})`]
      ];
      if (a) rows.push(["Posição (nm)", `(${atom.pos.map((v) => ptNumber(v * a, 3)).join("; ")})`]);
      if (info) {
        rows.push(["Raio atômico", `${ptNumber(info.raio, 4)} nm`]);
        rows.push(["Massa atômica", `${ptNumber(info.peso, 2)} g/mol`]);
        if (info.estrutura) rows.push(["Estrutura do puro", `${info.estrutura}, NC ${data.metais[atom.elemento].nc}`]);
        if (info.eletroneg) rows.push(["Eletronegatividade", ptNumber(info.eletroneg, 1)]);
        if (info.fusao) rows.push(["Fusão", `${ptNumber(info.fusao, 0)} °C`]);
      }
      const title = info ? `${atom.elemento} · ${info.nome}` : "Átomo da célula genérica";
      card.innerHTML = `
        <header>
          <i style="background:${atomColor(atom)}"></i>
          <strong>${escapeHtml(title)}</strong>
          <button type="button" class="close" id="atomCardClose" aria-label="Fechar">×</button>
        </header>
        <dl class="kv">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${escapeHtml(v)}</dd>`).join("")}</dl>`;
      card.hidden = false;
    }

    /* =====================================================================
       Camadas da cena
       ===================================================================== */

    CrystaLab.registrarCamada({
      id: "rigid", rotulo: "Esferas em contato",
      ler: () => state.rigid,
      definir: (on) => { state.rigid = on; viewer.updateAtomScale(); }
    });
    CrystaLab.registrarCamada({
      id: "edges", rotulo: "Arestas",
      ler: () => state.showEdges,
      definir: (on) => { state.showEdges = on; if (viewer.ready) viewer.edgesGroup.visible = on; }
    });
    CrystaLab.registrarCamada({
      id: "axes", rotulo: "Eixos",
      ler: () => state.showAxes,
      definir: (on) => { state.showAxes = on; if (viewer.ready) viewer.axesGroup.visible = on; }
    });
    CrystaLab.registrarCamada({
      id: "rotate", rotulo: "Girar",
      ler: () => state.autoRotate,
      definir: (on) => { state.autoRotate = on; }
    });
    CrystaLab.registrarCamada({
      id: "vibrate", rotulo: "Vibração térmica",
      ler: () => state.vibrate,
      definir: (on) => { state.vibrate = on; }
    });
    CrystaLab.registrarCamada({
      id: "colorpos", rotulo: "Cor por posição",
      ler: () => state.colorMode === "posicao",
      definir: (on) => {
        state.colorMode = on ? "posicao" : "elemento";
        viewer.applyAtomStyles();
        if (sceneResult()) renderLegend(sceneResult());
        renderAtomCard();
      }
    });

    function setToggle(name, value) {
      const layer = CrystaLab.camadas().find((item) => item.id === name);
      if (!layer) return;
      layer.definir(value);
      const button = document.querySelector(`[data-toggle="${name}"]`);
      if (button) button.setAttribute("aria-pressed", String(value));
    }

    function setFocus(on) {
      state.focus = on;
      $("app").dataset.focus = String(on);
      $("focusButton").setAttribute("aria-pressed", String(on));
      $("focusButton").title = on ? "Mostrar os painéis" : "Expandir a cena (oculta os painéis)";
    }

    /* =====================================================================
       Lateral: tabela de metais por estrutura
       ===================================================================== */

    function blockItems() {
      return Object.entries(data.metais).map(([symbol, metal]) => ({
        key: symbol,
        symbol,
        name: metal.nome,
        mass: ptNumber(metal.peso, 2),
        structure: metal.estrutura,
        search: plainText(`${symbol} ${metal.nome} ${metal.estrutura}`),
        payload: { nome: symbol }
      }));
    }

    function tileHtml(item) {
      return `
        <button type="button" class="element-tile alloy-block" data-key="${item.key}" draggable="true"
          style="--tile-color:${STRUCTURE_COLORS[item.structure]}" title="${escapeHtml(item.name)}"
          aria-label="${escapeHtml(item.name)}, ${item.structure}">
          <i class="tile-dot" style="background:${elementColor(item.symbol)}"></i>
          <span class="tile-mass">${item.mass}</span>
          <span class="tile-symbol">${item.symbol}</span>
          <span class="tile-name">${escapeHtml(item.name)}</span>
        </button>`;
    }

    function renderBlocks(filter = "") {
      const query = plainText(filter);
      const metals = blockItems().filter((item) => !query || item.search.includes(query));
      const structures = Object.fromEntries(data.estruturas.map((s) => [s.sigla, s]));
      const groups = STRUCTURE_ORDER
        .map((sigla) => ({ sigla, items: metals.filter((item) => item.structure === sigla) }))
        .filter((group) => group.items.length);

      blockList.innerHTML = groups.length
        ? groups.map((group) => `
          <section class="element-group" style="--group-color:${STRUCTURE_COLORS[group.sigla]}">
            <h2>${group.sigla} <span>${structures[group.sigla].nome.toLowerCase()}</span></h2>
            <div class="tile-grid">${group.items.map(tileHtml).join("")}</div>
          </section>`).join("")
        : '<p class="side-empty">Nenhum metal com esse nome. Tente o símbolo, como Cu ou Fe.</p>';
      markActiveBlock();
    }

    function renderGenericRow() {
      $("genericRow").innerHTML = data.estruturas.map((structure) => `
        <button type="button" data-generic="${structure.sigla}" style="--tile-color:${STRUCTURE_COLORS[structure.sigla]}"
          title="${structure.nome}">${structure.sigla}</button>`).join("");
    }

    function markActiveBlock() {
      document.querySelectorAll(".element-tile").forEach((tile) => {
        const active = tile.dataset.key === state.selectedKey;
        tile.classList.toggle("is-active", active);
        tile.setAttribute("aria-pressed", String(active));
      });
    }

    function isDesktop() {
      return window.matchMedia("(min-width: 1024px)").matches;
    }

    function setSidebar(open, persist = true) {
      state.sidebar = open ? "open" : "collapsed";
      $("app").dataset.sidebar = state.sidebar;
      $("menuButton").setAttribute("aria-expanded", String(open));
      if (persist) store.set("crystalab-lateral", state.sidebar);
    }

    function setMenu(open) {
      $("app").dataset.menu = open ? "open" : "closed";
      $("menuButton").setAttribute("aria-expanded", String(open));
    }

    function toggleMetals() {
      if (isDesktop()) setSidebar(state.sidebar !== "open");
      else setMenu($("app").dataset.menu !== "open");
    }

    /* =====================================================================
       Carregamento da estrutura (publica "estrutura:carregada")
       ===================================================================== */

    async function loadStructure(payload) {
      const result = await postJson("/api/estrutura", payload);
      if (result) applyResult(result);
      return result;
    }

    function applyResult(result) {
      state.current = result;
      state.selectedKey = result.simbolo && !result.editado ? result.simbolo : "";
      CrystaLab.publicar("estrutura:carregada", result);
      const density = result.densidade ? `, ρ = ${ptNumber(result.densidade, 3)} g/cm³` : "";
      logLine(`${result.rotulo}: ${result.estrutura}, NC ${result.nc}, FEA ${ptNumber(result.fea, 3)}${density}`, "terminal-ok");
    }

    CrystaLab.assinar("estrutura:carregada", (result) => {
      state.scene = "celula";
      state.liga = null;
      markActiveBlock();
      renderExplore(result);
      resultToEditor(result);
      renderSteps();
      syncLigaDefaults();
      renderScene();
    });

    // Redesenha tudo o que depende do que está na cena (célula ou liga)
    function renderScene() {
      const result = sceneResult();
      if (!result) return;
      state.overlays = [];
      state.selectedAtom = null;
      state.practice = null;
      if (state.scene === "liga") renderLigaSummary(result);
      else renderSummary(result);
      renderLegend(result);
      viewer.build(result);
      renderAtomCard();
      renderOverlayList();
      renderPresets();
      renderPractice();
      setupThermo();
      $("ligaVoltar").hidden = state.scene !== "liga";
      $("millerScope").textContent = state.scene === "liga"
        ? `Na liga, cada plano aparece com todos os paralelos da família dentro da supercélula ${result.supercelula}×${result.supercelula}×${result.supercelula}.`
        : "Desenhados na célula unitária, com a origem no vértice O.";
      CrystaLab.publicar("cena:alterada", { cena: state.scene, result });
    }

    function readoutItem(label, value, unit, note) {
      return `
        <div>
          <dt>${label}</dt>
          <dd>${value}${unit ? `<small>${unit}</small>` : ""}</dd>
          <span class="readout-note">${note || "&nbsp;"}</span>
        </div>`;
    }

    function structureLabel(name) {
      return name.charAt(0) + name.slice(1).toLowerCase();
    }

    function renderSummary(result) {
      const isGeneric = result.generica;
      const symbol = $("specimenSymbol");
      symbol.textContent = isGeneric ? result.estrutura : result.simbolo;
      symbol.classList.toggle("is-generic", isGeneric);
      symbol.style.setProperty("--tile-color", STRUCTURE_COLORS[result.estrutura]);

      let title;
      if (isGeneric) title = `Célula genérica ${result.estrutura}`;
      else if (result.editado) title = `${result.nome_metal}, parâmetros editados`;
      else title = result.nome_metal;
      $("resultTitle").textContent = title;
      $("crumbCurrent").textContent = isGeneric ? result.estrutura : result.simbolo;
      $("resultSubtitle").textContent = `${structureLabel(result.estrutura_nome)}. Os átomos se tocam ao longo da ${result.contato}.`;

      let latticeNote = result.relacao_a;
      if (result.c_nm) latticeNote = `c = ${ptNumber(result.c_nm, 4)} nm`;
      else if (result.erro_a != null) latticeNote = `Medido ${ptNumber(result.a_exp, 4)} nm (${signedNumber(result.erro_a, 2)}%)`;
      const lattice = result.a_nm
        ? readoutItem("Parâmetro de rede", ptNumber(result.a_nm, 4), "nm", latticeNote)
        : readoutItem("Parâmetro de rede", ptNumber(result.a_em_R, 3), "R", result.relacao_a);
      const densityNote = result.densidade_exp
        ? `Experimental ${ptNumber(result.densidade_exp, 2)} g/cm³`
        : (result.densidade ? "Sem valor experimental" : "Informe raio e massa atômica");
      $("metricsGrid").innerHTML = [
        lattice,
        readoutItem("Fator de empacotamento", ptNumber(result.fea, 3), "", `${ptNumber(result.vazios * 100, 1)}% de vazios`),
        readoutItem("Densidade teórica", result.densidade ? ptNumber(result.densidade, 3) : "n/d", result.densidade ? "g/cm³" : "", densityNote),
        readoutItem("Coordenação", result.nc, "", "vizinhos mais próximos"),
        readoutItem("Átomos por célula", result.n, "", result.estrutura === "HC" ? `c/a = ${ptNumber(result.c_a, 3)}` : "")
      ].join("");
    }

    function renderLigaSummary(liga) {
      const symbol = $("specimenSymbol");
      symbol.textContent = `${liga.base}${liga.soluto}`;
      symbol.classList.add("is-generic");
      symbol.style.setProperty("--tile-color", STRUCTURE_COLORS[liga.estrutura]);
      $("resultTitle").textContent = `Liga ${liga.base}–${liga.soluto}`;
      $("crumbCurrent").textContent = `${liga.base}–${liga.soluto}`;
      const kind = liga.intersticial ? "intersticial" : "substitucional";
      $("resultSubtitle").textContent = `Solução sólida ${kind} na rede ${liga.estrutura} do ${data.metais[liga.base].nome.toLowerCase()}. ${ptNumber(liga.x_pct, 1)}% at. de ${liga.soluto} = ${ptNumber(liga.pct_peso, 2)}% em peso.`;
      const delta = (liga.a_nm / liga.a_base_nm - 1) * 100;
      $("metricsGrid").innerHTML = [
        readoutItem("Parâmetro de rede", ptNumber(liga.a_nm, 4), "nm", liga.intersticial ? "rede do solvente" : `Vegard; ${liga.base} puro ${ptNumber(liga.a_base_nm, 4)} (${signedNumber(delta, 2)}%)`),
        readoutItem("Composição", ptNumber(liga.x_pct, 1), "% at.", `${ptNumber(liga.pct_peso, 2)}% em peso`),
        readoutItem("Densidade da liga", ptNumber(liga.densidade, 3), "g/cm³", `${liga.base} puro ${ptNumber(liga.densidade_base, 3)} g/cm³`),
        readoutItem("Coordenação", liga.nc, "", "da rede do solvente"),
        readoutItem("Átomos na supercélula", liga.atomos.length, "", `${liga.n_soluto} de ${liga.soluto}`)
      ].join("");
    }

    function renderExplore(result) {
      $("countBody").innerHTML = result.contagem.map((group) => `
        <div class="count-row">
          <strong><i style="background:${TYPE_COLORS[group.tipo]}"></i>${group.rotulo}</strong>
          <span class="count-math">${group.quantidade} × ${group.fracao_txt} = ${compactNumber(group.contribuicao)}</span>
          <span class="bar-track"><span class="bar-fill" style="width:${Math.min(100, (group.contribuicao / result.n) * 100)}%;background:${TYPE_COLORS[group.tipo]}"></span></span>
        </div>`).join("") + `
        <div class="count-total"><span>Total</span><span>${result.n} átomo${result.n > 1 ? "s" : ""}</span></div>`;

      $("interpretationBody").innerHTML = result.interpretacao.map((line) => `<p>${escapeHtml(line)}</p>`).join("");

      const rows = data.estruturas.map((structure) => `
        <tr class="${structure.sigla === result.estrutura ? "is-current" : ""}">
          <td><span style="--row-color:${STRUCTURE_COLORS[structure.sigla]}">${structure.sigla}</span></td>
          <td>${structure.n}</td>
          <td>${structure.nc}</td>
          <td>${ptNumber(structure.fea, 3)}</td>
        </tr>`).join("");
      const hcNote = result.estrutura === "HC" && Math.abs(result.c_a - 1.633) > 0.002
        ? `<p class="table-note">A linha HC usa c/a ideal (1,633). Com c/a = ${ptNumber(result.c_a, 3)}, o FEA é ${ptNumber(result.fea, 4)}.</p>`
        : "";
      $("comparisonTable").innerHTML = `
        <table class="comparison-table">
          <thead><tr><th scope="col">Estrutura</th><th scope="col">n</th><th scope="col">NC</th><th scope="col">FEA</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>${hcNote}`;
    }

    /* =====================================================================
       Temperatura: dilatação e vibração (critério de Lindemann)
       ===================================================================== */

    let thermalTimer = null;

    function thermalSource() {
      const result = sceneResult();
      return result ? result.termico_base : null;
    }

    function setupThermo() {
      const source = thermalSource();
      const bar = $("thermoBar");
      bar.classList.toggle("is-disabled", !source);
      tempRange.disabled = !source;
      if (!source) {
        state.thermal = null;
        viewer.applyThermal();
        $("tempValue").textContent = "sem dados";
        renderThermal();
        return;
      }
      tempRange.max = String(Math.round(source.fusao + 200));
      state.temperature = Math.min(state.temperature, Number(tempRange.max));
      tempRange.value = String(Math.round(state.temperature));
      requestThermal(0);
    }

    function requestThermal(delay = 50) {
      clearTimeout(thermalTimer);
      $("tempValue").textContent = `${Math.round(state.temperature)} °C`;
      thermalTimer = setTimeout(async () => {
        const source = thermalSource();
        if (!source) return;
        const result = await postJson("/api/termico", { ...source, temperatura: state.temperature }, { quiet: true });
        if (!result || thermalSource() !== source) return;
        state.thermal = result;
        viewer.applyThermal();
        renderThermal();
      }, delay);
    }

    function setTemperature(value, { vibrate = true } = {}) {
      state.temperature = Number(value);
      tempRange.value = String(Math.round(state.temperature));
      if (vibrate && !state.vibrate) setToggle("vibrate", true);
      requestThermal();
    }

    function thermalChart(thermal) {
      const W = 300, H = 132, L = 30, R = 10, T = 12, B = 22;
      const first = thermal.curva[0][0];
      const last = thermal.curva[thermal.curva.length - 1][0];
      const ymax = 0.13;
      const X = (t) => L + (t - first) / (last - first) * (W - L - R);
      const Y = (v) => T + (1 - Math.min(v, ymax) / ymax) * (H - T - B);
      const path = thermal.curva.map((p, i) => `${i ? "L" : "M"}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join("");
      const tf = X(thermal.fusao);
      const cx = X(Math.min(Math.max(thermal.temperatura, first), last));
      const cy = Y(thermal.razao);
      return `<svg class="thermal-chart" viewBox="0 0 ${W} ${H}" role="img"
          aria-label="Amplitude de vibração dividida pela distância entre vizinhos, de −273 °C até ${Math.round(last)} °C; valor atual ${ptNumber(thermal.razao, 3)}">
        <line class="axis" x1="${L}" y1="${Y(0)}" x2="${W - R}" y2="${Y(0)}" />
        <line class="axis" x1="${L}" y1="${T}" x2="${L}" y2="${Y(0)}" />
        <line class="guide" x1="${L}" y1="${Y(0.1)}" x2="${W - R}" y2="${Y(0.1)}" />
        <line class="guide" x1="${tf}" y1="${T}" x2="${tf}" y2="${Y(0)}" />
        <text x="${L + 4}" y="${Y(0.1) - 4}">Lindemann 0,10</text>
        <text x="${tf - 3}" y="${T + 8}" text-anchor="end">fusão</text>
        <text x="${L - 4}" y="${Y(0) + 3}" text-anchor="end">0</text>
        <text x="${L - 4}" y="${Y(0.1) + 3}" text-anchor="end">0,1</text>
        <text x="${L}" y="${H - 6}">−273 °C</text>
        <text x="${W - R}" y="${H - 6}" text-anchor="end">${Math.round(last)} °C</text>
        <text x="${L + 4}" y="${T - 2}">u/d</text>
        <path class="curve" d="${path}" />
        <circle class="marker" cx="${cx}" cy="${cy}" r="4.5" />
      </svg>`;
    }

    function renderThermal() {
      const thermal = state.thermal;
      $("thermoBar").classList.toggle("is-hot", Boolean(thermal && thermal.fundido));
      if (!thermal) {
        $("thermalStats").innerHTML = "";
        $("thermalChart").innerHTML = "";
        $("thermalNotes").innerHTML = thermalSource() ? "" : '<p class="note">Escolha um metal cadastrado (ou forme uma liga) para ver o efeito da temperatura.</p>';
        return;
      }
      const stat = (label, value, small = "") => `<div><dt>${label}</dt><dd>${value}${small ? ` <small>${small}</small>` : ""}</dd></div>`;
      $("thermalStats").innerHTML = [
        stat("Temperatura", `${ptNumber(thermal.temperatura, 0)} °C`, `${ptNumber(thermal.temperatura_k, 0)} K`),
        stat("T / T fusão", ptNumber(thermal.homologa, 2), "em kelvin"),
        stat("Parâmetro a(T)", `${ptNumber(thermal.a_nm, 4)} nm`, `${signedNumber(thermal.delta_a_pct, 2)}%`),
        stat("Densidade", thermal.densidade ? `${ptNumber(thermal.densidade, 3)}` : "n/d", `ΔV ${signedNumber(thermal.delta_v_pct, 2)}%`),
        stat("Vibração média", `${ptNumber(thermal.u_nm * 1000, 1)} pm`, `${ptNumber(thermal.razao * 100, 1)}% de d`),
        stat("Dilatação α", `${ptNumber(thermal.alfa, 1)}`, "×10⁻⁶ /°C")
      ].join("");
      $("thermalChart").innerHTML = thermalChart(thermal);
      $("thermalNotes").innerHTML = thermal.notas.map((note) => `<p class="note${note.tipo === "alerta" ? " is-alert" : ""}">${escapeHtml(note.texto)}</p>`).join("");
    }

    /* =====================================================================
       Modo Editar: editor de parâmetros
       ===================================================================== */

    function resultToEditor(result) {
      const lines = [
        `elemento = ${result.simbolo || "(genérico)"}`,
        `estrutura = ${result.estrutura}`,
        `raio = ${result.raio_nm != null ? Number(result.raio_nm.toFixed(5)) : ""}`.padEnd(18) + "# nm",
        `peso = ${result.peso ?? ""}`.padEnd(18) + "# g/mol"
      ];
      if (result.estrutura === "HC") lines.push(`c/a = ${Number(result.c_a.toFixed(4))}`);
      lines.push(`# a = ${result.a_nm ? Number(result.a_nm.toFixed(4)) : ""}`.padEnd(18) + "# nm: apague o primeiro # para calcular R a partir de a");
      editor.value = lines.join("\n");
    }

    function parseEditor() {
      const payload = {};
      const keys = {
        elemento: "nome", metal: "nome", nome: "nome",
        estrutura: "estrutura",
        raio: "raio", r: "raio",
        peso: "peso", massa: "peso",
        "c/a": "c_a", ca: "c_a",
        a: "a"
      };
      editor.value.split("\n").forEach((rawLine) => {
        const line = rawLine.split("#")[0];
        const match = line.match(/^\s*([^=:]+?)\s*[=:]\s*(.*?)\s*$/);
        if (!match) return;
        const key = keys[plainText(match[1])];
        if (!key) return;
        const value = match[2];
        if (key === "nome" || key === "estrutura") {
          if (value && !value.startsWith("(")) payload[key] = value;
        } else if (value) {
          payload[key] = value.replace(",", ".");
        }
      });
      return payload;
    }

    function applyEditor() {
      const payload = parseEditor();
      if (!payload.nome && !payload.estrutura) {
        logLine("Escreva 'elemento = Fe' ou 'estrutura = CFC' no editor.", "terminal-error");
        return;
      }
      if (payload.a) delete payload.raio;
      loadStructure(payload);
    }

    /* =====================================================================
       Modo Medir: índices de Miller, prática e cálculos
       ===================================================================== */

    function stepsHtml(steps) {
      return steps.map((step) => `
        <li>
          <div>
            <strong>${escapeHtml(step.titulo)}</strong>
            <div class="formula">${escapeHtml(step.formula)}</div>
            ${step.detalhe ? `<p>${escapeHtml(step.detalhe)}</p>` : ""}
          </div>
        </li>`).join("");
    }

    function renderSteps() {
      const result = state.current;
      if (!result) return;
      const steps = { parametro: result.passos_parametro, fea: result.passos_fea, densidade: result.passos_densidade }[state.stepsTab];
      densitySteps.innerHTML = stepsHtml(steps);
      document.querySelectorAll("#stepsSwitch button").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.steps === state.stepsTab));
      });
    }

    function setStepsTab(tab) {
      state.stepsTab = tab;
      renderSteps();
    }

    function showDensity() {
      const result = state.current;
      if (!result) return;
      setWorkMode("medir");
      setStepsTab("densidade");
      if (!result.densidade) {
        logLine(result.passos_densidade[0].detalhe, "terminal-error");
        return;
      }
      logLine(`densidade teórica de ${result.rotulo}`, "terminal-ok");
      result.passos_densidade.forEach((step, index) => logLine(`${index + 1}. ${step.titulo}\n   ${step.formula.replace(/\n/g, "\n   ")}`, "terminal-step"));
    }

    function parseIndices(text) {
      const clean = String(text).replace(/[()\[\]{}<>]/g, " ").trim();
      if (!clean) return null;
      const tokens = /[\s,;]/.test(clean) ? clean.split(/[\s,;]+/).filter(Boolean) : (clean.match(/-?\d/g) || []);
      const numbers = tokens.map(Number);
      if (!numbers.length || numbers.some((n) => !Number.isInteger(n))) return null;
      return numbers;
    }

    function overlayDetail(overlay) {
      if (overlay.tipo === "plano") {
        const spacing = overlay.d_nm ? `${ptNumber(overlay.d_nm, 4)} nm` : `${ptNumber(overlay.d_rel, 3)} a`;
        const planar = overlay.dp_nm ? `${ptNumber(overlay.dp_nm, 2)} át/nm²` : `${ptNumber(overlay.dp_rel, 3)} át/a²`;
        const family = overlay.poligonos && overlay.poligonos.length > 1 ? `, ${overlay.poligonos.length} planos paralelos` : "";
        return `d = ${spacing}, DP = ${planar}, FP = ${ptNumber(overlay.fracao_planar, 3)}${family}`;
      }
      const length = overlay.comprimento_nm ? `${ptNumber(overlay.comprimento_nm, 4)} nm` : `${ptNumber(overlay.comprimento_rel, 3)} a`;
      let linear = "";
      if (overlay.densidade_linear_nm) linear = `, DL = ${ptNumber(overlay.densidade_linear_nm, 2)} át/nm`;
      else if (overlay.densidade_linear_rel) linear = `, DL = ${ptNumber(overlay.densidade_linear_rel, 3)} át/a`;
      return `|v| = ${length}${linear}`;
    }

    function renderOverlayList() {
      $("clearOverlaysButton").hidden = !state.overlays.length;
      const result = sceneResult();
      if (!state.overlays.length) {
        overlayList.innerHTML = result && result.estrutura === "HC"
          ? '<span class="overlay-empty">Nenhum índice desenhado. Na HC, use 4 índices: <code>1 0 -1 1</code>.</span>'
          : '<span class="overlay-empty">Nenhum índice desenhado. Experimente <code>1 1 1</code> ou <code>1 1 0</code>.</span>';
        return;
      }
      overlayList.innerHTML = state.overlays.map((overlay) => {
        if (overlay.hideLabel) {
          return `<span class="overlay-chip"><i style="background:${overlay.color}"></i><span><strong>Plano misterioso</strong><br />Identifique os índices abaixo</span></span>`;
        }
        return `<span class="overlay-chip"><i style="background:${overlay.color}"></i><span><strong>${overlay.notacao}</strong>${overlay.notacao_alternativa ? ` <em>${overlay.notacao_alternativa}</em>` : ""}<br />${overlayDetail(overlay)}</span></span>`;
      }).join("");
    }

    function renderPresets() {
      const result = sceneResult();
      if (!result) return;
      $("presetRow").innerHTML = (PRESETS[result.estrutura] || []).map(([type, indices, compact]) => {
        const text = indices.map((v) => (v < 0 ? `${-v}̄` : v)).join(" ");
        const label = type === "plano" ? `(${text})` : `[${text}]`;
        return `<button type="button" data-preset-type="${type}" data-preset="${indices.join(",")}" title="${type === "plano" ? "Desenhar o plano" : "Desenhar a direção"} ${label}">${label}${compact ? '<span class="tag">compacto</span>' : ""}</button>`;
      }).join("");
    }

    function millerPayload(type, indices) {
      const result = sceneResult();
      return {
        estrutura: result.estrutura,
        c_a: result.c_a,
        a_nm: result.a_nm,
        tipo: type,
        indices,
        supercelula: state.scene === "liga" ? result.supercelula : 1
      };
    }

    async function drawMiller(type, indices) {
      const result = sceneResult();
      if (!result) return;
      if (!indices || indices.length < 3) {
        logLine("Informe 3 índices inteiros (ou 4 na HC). Exemplo: plano 1 1 1", "terminal-error");
        return;
      }
      if (state.practice && !state.practice.solved) clearOverlays();
      const overlay = await postJson("/api/miller", millerPayload(type, indices));
      if (!overlay || sceneResult() !== result) return;
      overlay.color = OVERLAY_COLORS[state.overlays.length % OVERLAY_COLORS.length];
      state.overlays.push(overlay);
      viewer.addOverlay(overlay);
      renderOverlayList();
      const name = overlay.tipo === "plano" ? "plano" : "direção";
      const extra = overlay.notacao_alternativa ? ` = ${overlay.notacao_alternativa}` : "";
      logLine(`${name} ${overlay.notacao}${extra}: ${overlayDetail(overlay)}`, "terminal-ok");
      if (overlay.tipo === "direcao" && overlay.densidade_linear_rel === null) {
        logLine("O vetor não termina num ponto da rede dentro da célula; densidade linear não calculada.", "terminal-step");
      }
    }

    function clearOverlays() {
      state.overlays = [];
      if (state.practice && !state.practice.solved) state.practice = null;
      viewer.redrawOverlays();
      renderOverlayList();
      renderPractice();
    }

    function setMode(mode) {
      state.mode = mode;
      document.querySelectorAll(".segmented button[data-mode]").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.mode === mode));
      });
      millerInput.placeholder = mode === "plano" ? "1 1 1 ou 1 0 -1 1" : "1 1 0 ou 2 -1 -1 0";
    }

    /* ---------- Prática ---------- */
    function sameIndices(a, b) {
      return a.length === b.length && a.every((v, i) => v === b[i]);
    }

    async function newPractice() {
      const result = sceneResult();
      if (!result) return;
      const pool = result.estrutura === "HC" ? PRACTICE.HC : PRACTICE.cubic;
      const previous = state.practice ? state.practice.target : null;
      let target = pool[Math.floor(Math.random() * pool.length)];
      if (previous && sameIndices(target, previous)) target = pool[(pool.indexOf(target) + 1) % pool.length];
      const overlay = await postJson("/api/miller", millerPayload("plano", target));
      if (!overlay || sceneResult() !== result) return;
      overlay.color = "#ce3f4f";
      overlay.hideLabel = true;
      state.overlays = [overlay];
      state.practice = { target, tries: 0, solved: false, feedback: "" };
      viewer.redrawOverlays();
      renderOverlayList();
      renderPractice();
      setWorkMode("medir");
      const input = $("practiceInput");
      if (input) input.focus();
    }

    function checkPractice(text) {
      const practice = state.practice;
      if (!practice || practice.solved) return;
      let answer = parseIndices(text);
      if (!answer) {
        practice.feedback = "Escreva os índices como números inteiros, por exemplo 1 1 0.";
        renderPractice();
        return;
      }
      const target = practice.target;
      if (target.length === 4 && answer.length === 3) answer = [answer[0], answer[1], -(answer[0] + answer[1]), answer[2]];
      const opposite = target.map((v) => -v || 0);
      practice.tries += 1;
      if (sameIndices(answer, target) || sameIndices(answer, opposite)) {
        revealPractice(`Correto em ${practice.tries} tentativa${practice.tries > 1 ? "s" : ""}!`);
        return;
      }
      practice.feedback = practice.tries >= 3
        ? "Ainda não. Dica: ache onde o plano corta cada eixo, tome os inversos e elimine as frações."
        : "Ainda não. Veja onde o plano intercepta os eixos x, y e z (ou a₁, a₂, c).";
      renderPractice();
    }

    function revealPractice(message) {
      const practice = state.practice;
      practice.solved = true;
      practice.feedback = message;
      state.overlays.forEach((overlay) => { overlay.hideLabel = false; });
      viewer.redrawOverlays();
      renderOverlayList();
      renderPractice();
    }

    function renderPractice() {
      const practice = state.practice;
      if (!practice) {
        $("practiceBody").innerHTML = '<button type="button" class="btn" id="practiceStart">Novo desafio</button>';
        return;
      }
      const ok = practice.solved && practice.tries > 0 && practice.feedback.startsWith("Correto");
      const feedbackClass = practice.solved ? (ok ? "is-ok" : "") : (practice.tries ? "is-bad" : "");
      $("practiceBody").innerHTML = `
        ${practice.solved ? "" : `
        <form class="miller-row" id="practiceForm">
          <label class="visually-hidden" for="practiceInput">Sua resposta</label>
          <input id="practiceInput" class="miller-input" autocomplete="off" placeholder="${practice.target.length === 4 ? "h k i l" : "h k l"}" />
          <button type="submit" class="btn btn-primary">Conferir</button>
        </form>`}
        <p class="practice-feedback ${feedbackClass}" role="status">${escapeHtml(practice.feedback)}</p>
        <div class="button-row">
          ${practice.solved ? "" : (practice.tries >= 3 ? '<button type="button" class="btn" id="practiceReveal">Mostrar resposta</button>' : "")}
          <button type="button" class="btn" id="practiceStart">${practice.solved ? "Próximo desafio" : "Trocar plano"}</button>
        </div>`;
    }

    /* =====================================================================
       Modo Liga: soluções sólidas
       ===================================================================== */

    function fillLigaSelects() {
      const metals = Object.entries(data.metais).sort((a, b) => STRUCTURE_ORDER.indexOf(a[1].estrutura) - STRUCTURE_ORDER.indexOf(b[1].estrutura));
      const option = ([symbol, info]) => `<option value="${symbol}">${symbol}, ${escapeHtml(info.nome)} (${info.estrutura})</option>`;
      $("ligaBase").innerHTML = metals.map(option).join("");
      $("ligaSoluto").innerHTML = `
        <optgroup label="Substitucionais (metais)">${metals.map(option).join("")}</optgroup>
        <optgroup label="Intersticiais">${Object.entries(data.intersticiais).map(([symbol, info]) => `<option value="${symbol}">${symbol}, ${escapeHtml(info.nome)}</option>`).join("")}</optgroup>`;
    }

    function isInterstitial(symbol) {
      return Boolean(data.intersticiais[symbol]);
    }

    function syncLigaDefaults() {
      const result = state.current;
      if (!result || !result.simbolo) return;
      $("ligaBase").value = result.simbolo;
      const solute = DEFAULT_SOLUTE[result.simbolo];
      if (solute && solute !== result.simbolo) $("ligaSoluto").value = solute;
      updateLigaComposition();
    }

    function updateLigaComposition(source) {
      const solute = $("ligaSoluto").value;
      const base = $("ligaBase").value;
      const interstitial = isInterstitial(solute);
      const max = interstitial ? 20 : 100;
      $("ligaXRange").max = String(max);
      $("ligaX").max = String(max);
      if (source === "range") $("ligaX").value = $("ligaXRange").value;
      let x = Math.min(max, Math.max(0, Number(String($("ligaX").value).replace(",", ".")) || 0));
      if (source !== "number") $("ligaX").value = String(x);
      $("ligaXRange").value = String(x);
      $("ligaXHint").textContent = interstitial ? "% atômica do soluto (máx. 20)" : "% atômica do soluto";
      $("ligaArranjo").disabled = interstitial;
      const A = elementInfo(solute).peso;
      const B = data.metais[base].peso;
      const f = x / 100;
      let weight;
      if (interstitial) {
        const n = data.estruturas.find((s) => s.sigla === data.metais[base].estrutura).n;
        const extra = f < 1 ? n * f / (1 - f) : 0;
        weight = extra * A / (n * B + extra * A) * 100;
      } else {
        weight = f > 0 ? f * A / (f * A + (1 - f) * B) * 100 : 0;
      }
      $("ligaPeso").textContent = `= ${ptNumber(weight, 2)}% em peso de ${solute}`;
    }

    function ligaPayload(seed) {
      return {
        base: $("ligaBase").value,
        soluto: $("ligaSoluto").value,
        x: $("ligaX").value,
        n: Number($("ligaN").value),
        arranjo: $("ligaArranjo").value,
        distorcer: $("ligaDistorcer").checked,
        semente: seed
      };
    }

    async function formLiga(seed = state.ligaSeed) {
      state.ligaSeed = seed;
      const result = await postJson("/api/liga", ligaPayload(seed));
      if (!result) return null;
      state.liga = result;
      state.scene = "liga";
      state.selectedKey = "";
      markActiveBlock();
      renderScene();
      renderLigaPanel(result);
      logLine(`${result.rotulo}: ${ptNumber(result.x_pct, 1)}% at. (${ptNumber(result.pct_peso, 2)}% em peso), a = ${ptNumber(result.a_nm, 4)} nm, ρ = ${ptNumber(result.densidade, 3)} g/cm³`, "terminal-ok");
      return result;
    }

    function renderLigaPanel(liga) {
      ["ligaRegrasBlock", "ligaPropsBlock", "ligaPassosBlock"].forEach((id) => { $(id).hidden = !liga; });
      if (!liga) return;
      $("ligaRegras").innerHTML = liga.regras.map((rule) => `
        <div class="rule">
          <span class="rule-mark ${rule.ok ? "is-ok" : "is-bad"}" aria-label="${rule.ok ? "atendida" : "não atendida"}">${rule.ok ? "✓" : "✗"}</span>
          <strong>${escapeHtml(rule.criterio)}</strong>
          <span class="rule-value">${escapeHtml(rule.valor)}</span>
          <small>${escapeHtml(rule.detalhe)}</small>
        </div>`).join("");
      $("ligaConclusao").textContent = liga.conclusao;
      const stat = (label, value, small = "") => `<div><dt>${label}</dt><dd>${value}${small ? ` <small>${small}</small>` : ""}</dd></div>`;
      const items = [
        stat("Composição", `${ptNumber(liga.x_pct, 1)}%`, "atômica"),
        stat("Em peso", `${ptNumber(liga.pct_peso, 2)}%`, liga.soluto),
        stat("Parâmetro a", `${ptNumber(liga.a_nm, 4)} nm`, liga.intersticial ? "do solvente" : "Vegard"),
        stat("Densidade", ptNumber(liga.densidade, 3), "g/cm³"),
        stat(`Átomos de ${liga.base}`, liga.n_solvente),
        stat(`Átomos de ${liga.soluto}`, liga.n_soluto)
      ];
      if (liga.sitio) items.push(stat(`Sítio ${liga.sitio.nome}`, `${ptNumber(liga.sitio.raio_nm, 4)} nm`, "raio livre"));
      $("ligaProps").innerHTML = items.join("");
      const notes = [...liga.interpretacao.slice(1)];
      if (liga.nota_arranjo) notes.unshift(liga.nota_arranjo);
      $("ligaNotas").innerHTML = notes.map((text) => `<p class="note">${escapeHtml(text)}</p>`).join("");
      $("ligaPassos").innerHTML = stepsHtml(liga.passos);
    }

    function backToCell() {
      if (!state.current) return;
      state.scene = "celula";
      state.selectedKey = state.current.simbolo && !state.current.editado ? state.current.simbolo : "";
      markActiveBlock();
      renderScene();
    }

    /* =====================================================================
       Exportação
       ===================================================================== */

    function sceneFileName() {
      const result = sceneResult();
      if (!result) return "crystalab";
      return state.scene === "liga"
        ? `crystalab-${result.base}-${result.soluto}-${String(result.x_pct).replace(".", ",")}pct`
        : `crystalab-${result.simbolo || result.estrutura}`;
    }

    function exportPng() {
      if (!viewer.ready) return;
      viewer.renderer.render(viewer.scene, viewer.camera);
      downloadUrl(viewer.renderer.domElement.toDataURL("image/png"), `${sceneFileName()}.png`);
      logLine("Imagem PNG salva.", "terminal-ok");
    }

    function exportXyz() {
      const result = sceneResult();
      if (!result) return;
      const scale = result.a_nm ? result.a_nm * 10 : 1;
      const lines = [
        String(result.atomos.length),
        `${result.rotulo} | ${result.estrutura} | coordenadas em ${result.a_nm ? "angstrom" : "unidades de a"} | CrystaLab ${CrystaLab.versao}`
      ];
      result.atomos.forEach((atom) => {
        lines.push([atom.elemento || "X", ...atom.pos.map((v) => (v * scale).toFixed(5))].join("  "));
      });
      const url = URL.createObjectURL(new Blob([lines.join("\n") + "\n"], { type: "chemical/x-xyz" }));
      downloadUrl(url, `${sceneFileName()}.xyz`);
      setTimeout(() => URL.revokeObjectURL(url), 2000);
      logLine("Arquivo .xyz salvo: abra no VESTA, Jmol, OVITO ou Avogadro.", "terminal-ok");
    }

    /* =====================================================================
       Modos de trabalho
       ===================================================================== */

    CrystaLab.registrarModo({ id: "explorar", rotulo: "Explorar", painel: "panel-explorar" });
    CrystaLab.registrarModo({ id: "editar", rotulo: "Editar", painel: "panel-editar", foco: () => editor.focus() });
    CrystaLab.registrarModo({ id: "medir", rotulo: "Medir", painel: "panel-medir" });
    CrystaLab.registrarModo({ id: "liga", rotulo: "Liga", painel: "panel-liga" });
    CrystaLab.registrarModo({ id: "tutoriais", rotulo: "Tutoriais", painel: "tutorialsView", entrar: () => loadTutorials() });

    function renderModeSwitch() {
      $("modeSwitch").innerHTML = CrystaLab.modos().map((mode) => `
        <button type="button" role="tab" id="tab-${mode.id}" data-work-mode="${mode.id}"
          aria-controls="${mode.painel}" aria-selected="${mode.id === state.workMode}"
          tabindex="${mode.id === state.workMode ? 0 : -1}">${mode.rotulo}</button>`).join("");
      CrystaLab.modos().forEach((mode) => {
        const panel = $(mode.painel);
        if (panel) panel.setAttribute("aria-labelledby", `tab-${mode.id}`);
      });
    }

    function setWorkMode(id, focus = false) {
      const mode = CrystaLab.modos().find((item) => item.id === id);
      if (!mode) return;
      const changed = state.workMode !== id;
      state.workMode = id;
      $("app").dataset.mode = id;
      CrystaLab.modos().forEach((item) => {
        const panel = $(item.painel);
        if (panel) panel.hidden = item.id !== id;
        const tab = $(`tab-${item.id}`);
        if (tab) {
          tab.setAttribute("aria-selected", String(item.id === id));
          tab.tabIndex = item.id === id ? 0 : -1;
        }
      });
      if (id !== "tutoriais" && state.focus) setFocus(false);
      if (changed && mode.entrar) mode.entrar();
      if (focus && mode.foco) mode.foco();
      CrystaLab.publicar("modo:alterado", id);
    }

    /* =====================================================================
       Tutoriais: biblioteca de arquivos
       ===================================================================== */

    const loadedScripts = new Map();

    function loadScript(src) {
      if (!loadedScripts.has(src)) {
        loadedScripts.set(src, new Promise((resolve, reject) => {
          const script = document.createElement("script");
          script.src = src;
          script.onload = resolve;
          script.onerror = () => {
            loadedScripts.delete(src);
            reject(new Error("biblioteca indisponível sem internet"));
          };
          document.head.appendChild(script);
        }));
      }
      return loadedScripts.get(src);
    }

    function tutorialUrl(name) {
      return `/tutoriais/${encodeURIComponent(name)}`;
    }

    function fileExtension(name) {
      const dot = name.lastIndexOf(".");
      return dot >= 0 ? name.slice(dot).toLowerCase() : "";
    }

    function setLibraryStatus(text, error = false) {
      const status = $("libraryStatus");
      status.textContent = text;
      status.classList.toggle("is-error", error);
    }

    async function loadTutorials() {
      try {
        const response = await fetch("/api/tutoriais");
        const body = await response.json();
        if (!body.ok) throw new Error(body.error || "falha ao listar");
        state.tutorials = body.result.arquivos;
        state.tutorialFolder = body.result.pasta;
        $("tutorialFolder").textContent = body.result.pasta;
        if (state.tutorialOpen && !state.tutorials.some((item) => item.nome === state.tutorialOpen)) state.tutorialOpen = null;
        renderTutorials();
      } catch (error) {
        setLibraryStatus(`Não foi possível listar os tutoriais: ${error.message}`, true);
      }
    }

    function renderTutorials() {
      const counts = { todos: state.tutorials.length };
      state.tutorials.forEach((item) => { counts[item.tipo] = (counts[item.tipo] || 0) + 1; });
      const filters = [["todos", "Todos"], ...Object.entries(FILE_TYPES).map(([id, info]) => [id, info.rotulo])];
      $("tutorialFilters").innerHTML = filters
        .filter(([id]) => id === "todos" || counts[id])
        .map(([id, label]) => `<button type="button" data-filter="${id}" aria-pressed="${state.tutorialFilter === id}">${label} ${counts[id] || 0}</button>`)
        .join("");
      const query = plainText($("tutorialSearch").value);
      const items = state.tutorials.filter((item) =>
        (state.tutorialFilter === "todos" || item.tipo === state.tutorialFilter) &&
        (!query || plainText(`${item.titulo} ${item.nome}`).includes(query)));
      $("tutorialList").innerHTML = items.length
        ? items.map((item) => `
          <li>
            <button type="button" class="tutorial-item${item.nome === state.tutorialOpen ? " is-active" : ""}" data-tutorial="${escapeHtml(item.nome)}">
              <span class="file-badge" data-tipo="${item.tipo}">${FILE_TYPES[item.tipo].selo}</span>
              <strong>${escapeHtml(item.titulo)}</strong>
              <small>.${item.extensao} · ${fileSize(item.tamanho)} · ${new Date(item.modificado).toLocaleDateString("pt-BR")}</small>
            </button>
          </li>`).join("")
        : `<li class="hint">${state.tutorials.length ? "Nenhum arquivo com esse filtro." : "Nenhum tutorial ainda. Adicione o primeiro."}</li>`;
      if (!state.tutorialOpen) renderTutorialEmpty();
    }

    function renderTutorialEmpty() {
      $("tutorialViewer").innerHTML = `
        <div class="viewer-head"><h3>Biblioteca de tutoriais</h3></div>
        <div class="viewer-body">
          <div class="dropzone">
            <strong>Arraste arquivos para cá</strong>
            <span>Textos, vídeos, PDFs, planilhas e documentos ficam disponíveis para todos que usam este computador.</span>
            <button type="button" class="btn btn-primary" data-upload>Escolher arquivos</button>
          </div>
        </div>`;
    }

    function sandboxDocument(html) {
      const style = "body{font-family:system-ui,sans-serif;margin:16px;line-height:1.5;color:#10131a}table{border-collapse:collapse;font-size:13px}td,th{border:1px solid #dbe2eb;padding:4px 8px}img{max-width:100%}";
      return `<!doctype html><html><head><meta charset="utf-8"><style>${style}</style></head><body>${html}</body></html>`;
    }

    function parseCsv(text) {
      const firstLine = text.split(/\r?\n/, 1)[0] || "";
      const delimiter = (firstLine.match(/;/g) || []).length > (firstLine.match(/,/g) || []).length ? ";" : ",";
      const rows = [];
      let row = [];
      let cell = "";
      let quoted = false;
      for (let i = 0; i < text.length; i++) {
        const char = text[i];
        if (quoted) {
          if (char === '"' && text[i + 1] === '"') { cell += '"'; i++; }
          else if (char === '"') quoted = false;
          else cell += char;
        } else if (char === '"') quoted = true;
        else if (char === delimiter) { row.push(cell); cell = ""; }
        else if (char === "\n") { row.push(cell.replace(/\r$/, "")); rows.push(row); row = []; cell = ""; }
        else cell += char;
      }
      if (cell || row.length) { row.push(cell); rows.push(row); }
      return rows;
    }

    function tableHtml(rows, limit = 500) {
      const [head = [], ...body] = rows;
      const shown = body.slice(0, limit);
      return `<table class="data-table"><thead><tr>${head.map((cell) => `<th>${escapeHtml(cell)}</th>`).join("")}</tr></thead>
        <tbody>${shown.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table>
        ${body.length > limit ? `<p class="hint" style="padding:8px 12px">Mostrando ${limit} de ${body.length} linhas. Baixe o arquivo para ver tudo.</p>` : ""}`;
    }

    async function openTutorial(name) {
      const item = state.tutorials.find((entry) => entry.nome === name);
      if (!item) return;
      state.tutorialOpen = name;
      renderTutorials();
      const url = tutorialUrl(name);
      const by = item.autor ? ` · enviado por ${escapeHtml(item.autor)}` : "";
      $("tutorialViewer").innerHTML = `
        <div class="viewer-head">
          <h3>${escapeHtml(item.titulo)} <small>.${item.extensao} · ${fileSize(item.tamanho)}${by}</small></h3>
          <a class="btn" href="${url}" target="_blank" rel="noopener">Abrir em nova aba</a>
          <a class="btn" href="${url}" download="${escapeHtml(name)}">Baixar</a>
          <button type="button" class="btn btn-danger" id="deleteTutorial">Excluir</button>
        </div>
        <div class="viewer-body" id="tutorialBody"><p class="hint" style="padding:16px">Carregando…</p></div>`;
      const body = $("tutorialBody");
      const ext = fileExtension(name);
      try {
        if (item.tipo === "video") {
          body.innerHTML = `<video controls preload="metadata" src="${url}"></video>`;
        } else if (item.tipo === "pdf") {
          body.innerHTML = `<iframe class="tutorial-frame" src="${url}" title="${escapeHtml(item.titulo)}"></iframe>`;
        } else if (item.tipo === "texto") {
          const text = await (await fetch(url)).text();
          body.innerHTML = '<pre class="tutorial-text"></pre>';
          body.firstElementChild.textContent = text;
        } else if (ext === ".csv") {
          const text = await (await fetch(url)).text();
          body.innerHTML = tableHtml(parseCsv(text));
        } else if (item.tipo === "planilha") {
          await loadScript(LIBS.xlsx);
          const workbook = XLSX.read(await (await fetch(url)).arrayBuffer(), { type: "array" });
          const showSheet = (sheetName) => {
            const html = XLSX.utils.sheet_to_html(workbook.Sheets[sheetName], { header: "", footer: "" });
            body.querySelectorAll(".sheet-tabs .btn").forEach((tab) => tab.setAttribute("aria-pressed", String(tab.dataset.sheet === sheetName)));
            body.querySelector("iframe").srcdoc = sandboxDocument(html);
          };
          body.innerHTML = `<div class="sheet-tabs">${workbook.SheetNames.map((sheet) => `<button type="button" class="btn" data-sheet="${escapeHtml(sheet)}">${escapeHtml(sheet)}</button>`).join("")}</div>
            <iframe class="tutorial-frame" sandbox title="${escapeHtml(item.titulo)}"></iframe>`;
          body.querySelector(".sheet-tabs").addEventListener("click", (event) => {
            const tab = event.target.closest("[data-sheet]");
            if (tab) showSheet(tab.dataset.sheet);
          });
          showSheet(workbook.SheetNames[0]);
        } else if (ext === ".docx") {
          await loadScript(LIBS.mammoth);
          const converted = await mammoth.convertToHtml({ arrayBuffer: await (await fetch(url)).arrayBuffer() });
          body.innerHTML = `<iframe class="tutorial-frame" sandbox title="${escapeHtml(item.titulo)}"></iframe>`;
          body.querySelector("iframe").srcdoc = sandboxDocument(converted.value);
        } else {
          body.innerHTML = `<div class="dropzone"><strong>Pré-visualização indisponível para .${item.extensao}</strong><span>Baixe o arquivo para abrir no Word, LibreOffice ou outro editor.</span><a class="btn btn-primary" href="${url}" download="${escapeHtml(name)}">Baixar arquivo</a></div>`;
        }
      } catch (error) {
        body.innerHTML = `<div class="dropzone"><strong>Não foi possível exibir o arquivo</strong><span>${escapeHtml(error.message)}. Use “Baixar” para abrir no seu computador.</span></div>`;
      }
    }

    async function deleteTutorial(name) {
      if (!window.confirm(`Excluir “${name}” da pasta de tutoriais? Essa ação não pode ser desfeita.`)) return;
      try {
        const response = await fetch(`/api/tutoriais/${encodeURIComponent(name)}`, { method: "DELETE", headers: { "X-CrystaLab": "1" } });
        const body = await response.json();
        if (!body.ok) throw new Error(body.error);
        state.tutorialOpen = null;
        setLibraryStatus(`“${name}” excluído.`);
        await loadTutorials();
      } catch (error) {
        setLibraryStatus(`Falha ao excluir: ${error.message}`, true);
      }
    }

    function uploadOne(file, index, total) {
      return new Promise((resolve) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `/api/tutoriais?nome=${encodeURIComponent(file.name)}`);
        xhr.setRequestHeader("X-CrystaLab", "1");
        xhr.setRequestHeader("Content-Type", "application/octet-stream");
        if (state.user) xhr.setRequestHeader("X-Usuario", encodeURIComponent(state.user));
        $("uploadLabel").textContent = `Enviando ${index + 1} de ${total}: ${file.name}`;
        $("uploadBar").value = 0;
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) $("uploadBar").value = Math.round((event.loaded / event.total) * 100);
        };
        xhr.onload = () => {
          let body = {};
          try { body = JSON.parse(xhr.responseText); } catch (error) {}
          resolve(body.ok ? { ok: true, nome: body.result.nome } : { ok: false, erro: body.error || `erro ${xhr.status}` });
        };
        xhr.onerror = () => resolve({ ok: false, erro: "conexão interrompida" });
        xhr.send(file);
      });
    }

    async function uploadFiles(fileList) {
      const files = Array.from(fileList || []);
      if (!files.length) return;
      const accepted = files.filter((file) => data.tutoriais.formatos.includes(fileExtension(file.name)) && file.size <= data.tutoriais.limite);
      const rejected = files.filter((file) => !accepted.includes(file));
      $("uploadProgress").hidden = false;
      const results = [];
      for (const [index, file] of accepted.entries()) {
        results.push({ file, ...(await uploadOne(file, index, accepted.length)) });
      }
      $("uploadProgress").hidden = true;
      const failed = results.filter((item) => !item.ok);
      const done = results.filter((item) => item.ok);
      const messages = [];
      if (done.length) messages.push(`${done.length} arquivo${done.length > 1 ? "s" : ""} adicionado${done.length > 1 ? "s" : ""}.`);
      if (rejected.length) messages.push(`Ignorado (formato ou tamanho): ${rejected.map((file) => file.name).join(", ")}.`);
      failed.forEach((item) => messages.push(`${item.file.name}: ${item.erro}.`));
      setLibraryStatus(messages.join(" "), Boolean(rejected.length || failed.length));
      await loadTutorials();
      if (done.length) openTutorial(done[done.length - 1].nome);
    }

    /* =====================================================================
       Entrada com e-mail da UFC
       ===================================================================== */

    function showLogin() {
      $("loginScreen").hidden = false;
      $("app").inert = true;
      $("app").setAttribute("aria-hidden", "true");
      const email = $("loginEmail");
      email.value = store.get("crystalab-ultimo-email") || "";
      setTimeout(() => email.focus(), 30);
    }

    function completeLogin(email, remember) {
      state.user = email;
      store.remove("crystalab-usuario");
      store.set("crystalab-usuario", email, !remember);
      if (remember) store.set("crystalab-ultimo-email", email);
      $("loginScreen").hidden = true;
      $("app").inert = false;
      $("app").removeAttribute("aria-hidden");
      $("userEmail").textContent = email;
      $("userAvatar").textContent = email.charAt(0).toUpperCase();
      $("userChip").title = `Conectado como ${email}`;
      $("userChip").hidden = false;
      postJson("/api/login", { email }, { quiet: true });
    }

    function logout() {
      state.user = null;
      store.remove("crystalab-usuario");
      $("userChip").hidden = true;
      showLogin();
    }

    $("loginForm").addEventListener("submit", (event) => {
      event.preventDefault();
      const input = $("loginEmail");
      const email = input.value.trim().toLowerCase();
      if (!UFC_EMAIL.test(email)) {
        input.setAttribute("aria-invalid", "true");
        $("loginError").textContent = email
          ? "Use um e-mail da UFC, terminado em ufc.br (por exemplo, nome@alu.ufc.br)."
          : "Digite seu e-mail institucional.";
        input.focus();
        return;
      }
      input.removeAttribute("aria-invalid");
      $("loginError").textContent = "";
      completeLogin(email, $("loginRemember").checked);
    });
    $("loginEmail").addEventListener("input", () => {
      $("loginEmail").removeAttribute("aria-invalid");
      $("loginError").textContent = "";
    });
    $("logoutButton").addEventListener("click", logout);

    /* =====================================================================
       Terminal: comandos registrados
       ===================================================================== */

    function setConsole(open, focusInput = false) {
      state.consoleOpen = open;
      $("console").dataset.open = String(open);
      $("consoleBody").hidden = !open;
      $("consoleToggle").setAttribute("aria-expanded", String(open));
      if (open && focusInput) terminalInput.focus();
    }

    const cmd = (nome, ajuda, testar, executar) => CrystaLab.registrarComando({ nome, ajuda, testar, executar });
    const LAYER_WORDS = { esferas: "rigid", girar: "rotate", eixos: "axes", arestas: "edges", vibracao: "vibrate" };

    cmd("ajuda", "lista os comandos", (l) => (l === "ajuda" || l === "help") && [], () => {
      const lines = ["Comandos disponíveis:"];
      CrystaLab.comandos().forEach((item) => lines.push(`  ${item.nome.padEnd(36)}${item.ajuda}`));
      logLine(lines.join("\n"));
    });
    cmd("limpar", "apaga índices e o histórico do terminal", (l) => l === "limpar" && [], () => {
      clearOverlays();
      terminalLog.innerHTML = "";
      logLine("Índices e terminal limpos.", "terminal-ok");
    });
    cmd("calcular densidade", "passo a passo da densidade teórica", (l) => (l === "calcular densidade" || l === "densidade") && [], showDensity);
    cmd("aplicar", "usa os parâmetros do editor", (l) => (l === "aplicar" || l === "renderizar") && [], applyEditor);
    cmd("listar", "mostra metais, intersticiais e estruturas", (l) => l === "listar" && [], () => {
      const metals = Object.entries(data.metais).map(([symbol, metal]) => `${symbol} (${metal.estrutura})`).join(", ");
      logLine(`Metais: ${metals}\nIntersticiais: ${Object.keys(data.intersticiais).join(", ")}\nEstruturas: ${data.estruturas.map((s) => s.sigla).join(", ")}`);
    });
    cmd("esferas | girar | eixos | arestas | vibracao", "liga ou desliga a camada", (l) => (LAYER_WORDS[l] ? [l] : null), ([l]) => {
      const layer = CrystaLab.camadas().find((item) => item.id === LAYER_WORDS[l]);
      setToggle(layer.id, !layer.ler());
      logLine(`${layer.rotulo}: ${layer.ler() ? "ligado" : "desligado"}.`, "terminal-ok");
    });
    cmd("cores elemento | posicao", "colore os átomos pelo elemento ou pela posição", (l) => l.match(/^cores?\s+(elemento|posicao)$/), (m) => {
      setToggle("colorpos", m[1] === "posicao");
      logLine(`Cores por ${m[1] === "posicao" ? "posição na célula" : "elemento"}.`, "terminal-ok");
    });
    cmd("tema", "alterna claro e escuro", (l) => l === "tema" && [], () => setTheme(state.theme === "dark" ? "light" : "dark"));
    cmd("modo explorar | editar | medir | liga | tutoriais", "troca o modo de trabalho", (l) => l.match(/^modo\s+(explorar|editar|medir|liga|tutoriais)$/), (m) => setWorkMode(m[1]));
    cmd("tutoriais", "abre a biblioteca de tutoriais", (l) => l === "tutoriais" && [], () => setWorkMode("tutoriais"));
    cmd("usar Fe", "carrega um metal (Fe, Cu, Mg, Ti...)", (l, raw) => raw.match(/^usar\s+(.+)$/i), (m) => loadStructure({ nome: m[1].trim() }));
    cmd("estrutura CFC [r=0.128 A=63.55 c/a=1.62]", "célula genérica CS, CCC, CFC ou HC", (l) => l.match(/^estrutura\s+([a-z]+)(.*)$/), (m) => {
      let rest = m[2];
      const payload = { nome: m[1] };
      const ratio = rest.match(/c\/a\s*=\s*([\d.,]+)/);
      if (ratio) { payload.c_a = ratio[1].replace(",", "."); rest = rest.replace(ratio[0], " "); }
      const radius = rest.match(/(?:^|\s)r\s*=\s*([\d.,]+)/);
      const weight = rest.match(/(?:^|\s)a\s*=\s*([\d.,]+)/);
      if (radius) payload.raio = radius[1].replace(",", ".");
      if (weight) payload.peso = weight[1].replace(",", ".");
      loadStructure(payload);
    });
    cmd("liga Cu Ni 30", "forma a liga solvente–soluto com x% atômico", (l, raw) => raw.match(/^liga\s+(\S+)\s+(\S+)(?:\s+([\d.,]+))?\s*$/i), (m) => {
      const pick = (text) => Object.keys(data.metais).concat(Object.keys(data.intersticiais)).find((symbol) => symbol.toLowerCase() === text.toLowerCase());
      const base = pick(m[1]);
      const solute = pick(m[2]);
      if (!base || !data.metais[base] || !solute) {
        logLine("Use símbolos: liga Cu Ni 30, liga Fe C 2 …", "terminal-error");
        return;
      }
      $("ligaBase").value = base;
      $("ligaSoluto").value = solute;
      if (m[3]) $("ligaX").value = m[3].replace(",", ".");
      updateLigaComposition("number");
      setWorkMode("liga");
      formLiga();
    });
    cmd("temperatura 500", "aquece a amostra (°C) e liga a vibração", (l) => l.match(/^temperatura\s+(-?[\d.,]+)$/), (m) => {
      if (!thermalSource()) {
        logLine("Escolha um metal cadastrado para usar a temperatura.", "terminal-error");
        return;
      }
      const value = Math.max(-273, Math.min(Number(tempRange.max), Number(m[1].replace(",", "."))));
      setTemperature(value);
      setWorkMode(state.scene === "liga" ? "liga" : "explorar");
      logLine(`Temperatura: ${ptNumber(value, 0)} °C.`, "terminal-ok");
    });
    cmd("exportar png | xyz", "salva imagem ou coordenadas da cena", (l) => l.match(/^exportar\s+(png|xyz)$/), (m) => (m[1] === "png" ? exportPng() : exportXyz()));
    cmd("plano 1 1 1 | plano 1 0 -1 1", "desenha um plano (hkl) ou (hkil)", (l) => l.match(/^plano\s+(.+)$/), (m) => {
      setMode("plano");
      setWorkMode("medir");
      millerInput.value = m[1].replace(/[()]/g, "").trim();
      drawMiller("plano", parseIndices(m[1]));
    });
    cmd("direcao 1 1 0", "desenha uma direção [uvw] ou [uvtw]", (l) => l.match(/^direcao\s+(.+)$/), (m) => {
      setMode("direcao");
      setWorkMode("medir");
      millerInput.value = m[1].replace(/[\[\]]/g, "").trim();
      drawMiller("direcao", parseIndices(m[1]));
    });

    function executeCommand(rawCommand) {
      const command = rawCommand.trim();
      if (!command) return;
      logLine(`> ${command}`, "terminal-entry");
      const lower = plainText(command);
      for (const item of CrystaLab.comandos()) {
        const match = item.testar(lower, command);
        if (match) {
          item.executar(match);
          return;
        }
      }
      logLine("Comando não reconhecido. Digite 'ajuda' para ver a lista.", "terminal-error");
      setConsole(true);
    }

    /* =====================================================================
       Tema
       ===================================================================== */

    function setTheme(theme, persist = true) {
      state.theme = theme;
      document.documentElement.dataset.theme = theme;
      themeToggle.textContent = theme === "dark" ? "Tema claro" : "Tema escuro";
      themeToggle.setAttribute("aria-pressed", String(theme === "dark"));
      if (persist) store.set("crystalab-theme", theme);
      viewer.applyTheme();
    }

    function initTheme() {
      const stored = store.get("crystalab-theme");
      const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(stored || (prefersDark ? "dark" : "light"), false);
    }

    /* =====================================================================
       Eventos de interface
       ===================================================================== */

    blockList.addEventListener("click", (event) => {
      const tile = event.target.closest(".element-tile");
      if (!tile) return;
      const item = blockItems().find((entry) => entry.key === tile.dataset.key);
      if (item) loadStructure(item.payload);
      if (state.workMode === "tutoriais") setWorkMode("explorar");
      setMenu(false);
    });
    blockList.addEventListener("dragstart", (event) => {
      const tile = event.target.closest(".element-tile");
      if (!tile) return;
      event.dataTransfer.setData("text/plain", tile.dataset.key);
      event.dataTransfer.effectAllowed = "copy";
    });
    $("elementSearch").addEventListener("input", (event) => renderBlocks(event.target.value));
    $("genericRow").addEventListener("click", (event) => {
      const button = event.target.closest("[data-generic]");
      if (button) loadStructure({ nome: button.dataset.generic });
    });

    $("modeSwitch").addEventListener("click", (event) => {
      const tab = event.target.closest("[data-work-mode]");
      if (tab) setWorkMode(tab.dataset.workMode, true);
    });
    $("modeSwitch").addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const ids = CrystaLab.modos().map((mode) => mode.id);
      let index = ids.indexOf(state.workMode);
      if (event.key === "ArrowLeft") index = (index - 1 + ids.length) % ids.length;
      if (event.key === "ArrowRight") index = (index + 1) % ids.length;
      if (event.key === "Home") index = 0;
      if (event.key === "End") index = ids.length - 1;
      setWorkMode(ids[index]);
      $(`tab-${ids[index]}`).focus();
    });

    $("layerBar").addEventListener("click", (event) => {
      const button = event.target.closest("[data-toggle]");
      if (!button) return;
      const layer = CrystaLab.camadas().find((item) => item.id === button.dataset.toggle);
      if (layer) setToggle(layer.id, !layer.ler());
    });
    $("resetViewButton").addEventListener("click", () => viewer.resetView());
    $("focusButton").addEventListener("click", () => setFocus(!state.focus));
    $("exportPngButton").addEventListener("click", exportPng);
    $("exportXyzButton").addEventListener("click", exportXyz);

    tempRange.addEventListener("input", () => setTemperature(tempRange.value));

    viewerLegend.addEventListener("input", (event) => {
      const input = event.target.closest("input[data-element]");
      if (input) setElementColor(input.dataset.element, input.value);
    });
    viewerLegend.addEventListener("change", () => {
      if (sceneResult()) renderLegend(sceneResult());
    });
    viewerLegend.addEventListener("click", (event) => {
      if (!event.target.closest("#resetColors")) return;
      state.elementColors = {};
      store.set("crystalab-cores", "{}");
      viewer.applyAtomStyles();
      renderBlocks($("elementSearch").value);
      renderLegend(sceneResult());
      renderAtomCard();
    });
    $("atomCard").addEventListener("click", (event) => {
      if (event.target.closest("#atomCardClose")) selectAtom(null);
    });

    $("terminalForm").addEventListener("submit", (event) => {
      event.preventDefault();
      executeCommand(terminalInput.value);
      terminalInput.value = "";
    });
    document.querySelectorAll(".shortcut-row button").forEach((button) => {
      button.addEventListener("click", () => {
        setConsole(true);
        executeCommand(button.dataset.command);
      });
    });
    $("consoleToggle").addEventListener("click", () => setConsole(!state.consoleOpen, !state.consoleOpen));
    $("paletteButton").addEventListener("click", () => setConsole(true, true));

    document.querySelectorAll(".segmented button[data-mode]").forEach((button) => {
      button.addEventListener("click", () => setMode(button.dataset.mode));
    });
    $("millerForm").addEventListener("submit", (event) => {
      event.preventDefault();
      executeCommand(`${state.mode} ${millerInput.value}`);
    });
    $("presetRow").addEventListener("click", (event) => {
      const button = event.target.closest("[data-preset]");
      if (!button) return;
      const indices = button.dataset.preset.split(",").map(Number);
      setMode(button.dataset.presetType);
      millerInput.value = indices.join(" ");
      drawMiller(button.dataset.presetType, indices);
    });
    $("clearOverlaysButton").addEventListener("click", () => {
      clearOverlays();
      logLine("Planos e direções removidos.", "terminal-ok");
    });
    $("stepsSwitch").addEventListener("click", (event) => {
      const button = event.target.closest("[data-steps]");
      if (button) setStepsTab(button.dataset.steps);
    });
    $("practiceBody").addEventListener("click", (event) => {
      if (event.target.closest("#practiceStart")) newPractice();
      if (event.target.closest("#practiceReveal")) revealPractice(`Resposta: ${state.overlays[0].notacao}.`);
    });
    $("practiceBody").addEventListener("submit", (event) => {
      event.preventDefault();
      checkPractice($("practiceInput").value);
      const input = $("practiceInput");
      if (input) input.focus();
    });

    $("ligaForm").addEventListener("submit", (event) => {
      event.preventDefault();
      formLiga();
    });
    $("ligaSorteio").addEventListener("click", () => formLiga(state.ligaSeed + 1));
    $("ligaVoltar").addEventListener("click", backToCell);
    $("ligaXRange").addEventListener("input", () => updateLigaComposition("range"));
    $("ligaX").addEventListener("input", () => updateLigaComposition("number"));
    $("ligaX").addEventListener("change", () => updateLigaComposition());
    $("ligaSoluto").addEventListener("change", () => updateLigaComposition());
    $("ligaBase").addEventListener("change", () => updateLigaComposition());
    $("ligaDestacar").addEventListener("change", (event) => {
      state.highlightSolute = event.target.checked;
      viewer.applyAtomStyles();
    });

    $("renderButton").addEventListener("click", applyEditor);
    themeToggle.addEventListener("click", () => setTheme(state.theme === "dark" ? "light" : "dark"));
    $("menuButton").addEventListener("click", toggleMetals);
    $("specimenSymbol").addEventListener("click", () => {
      if (isDesktop()) setSidebar(true);
      else setMenu(true);
      $("elementSearch").focus();
    });
    $("scrim").addEventListener("click", () => setMenu(false));

    editor.addEventListener("dragover", (event) => {
      event.preventDefault();
      editor.classList.add("is-drop-target");
    });
    editor.addEventListener("dragleave", () => editor.classList.remove("is-drop-target"));
    editor.addEventListener("drop", (event) => {
      event.preventDefault();
      editor.classList.remove("is-drop-target");
      const key = event.dataTransfer.getData("text/plain");
      const item = blockItems().find((entry) => entry.key === key);
      if (item) loadStructure(item.payload);
    });
    editor.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        applyEditor();
      }
    });

    /* ---------- Tutoriais: eventos ---------- */
    $("uploadButton").addEventListener("click", () => $("uploadInput").click());
    $("uploadInput").accept = data.tutoriais.formatos.join(",");
    $("uploadInput").addEventListener("change", (event) => {
      uploadFiles(event.target.files);
      event.target.value = "";
    });
    $("tutorialSearch").addEventListener("input", renderTutorials);
    $("tutorialFilters").addEventListener("click", (event) => {
      const button = event.target.closest("[data-filter]");
      if (!button) return;
      state.tutorialFilter = button.dataset.filter;
      renderTutorials();
    });
    $("tutorialList").addEventListener("click", (event) => {
      const button = event.target.closest("[data-tutorial]");
      if (button) openTutorial(button.dataset.tutorial);
    });
    $("tutorialViewer").addEventListener("click", (event) => {
      if (event.target.closest("[data-upload]")) $("uploadInput").click();
      if (event.target.closest("#deleteTutorial") && state.tutorialOpen) deleteTutorial(state.tutorialOpen);
    });
    const library = $("tutorialsView");
    library.addEventListener("dragover", (event) => {
      if (!event.dataTransfer.types.includes("Files")) return;
      event.preventDefault();
      library.classList.add("is-dragging");
    });
    library.addEventListener("dragleave", (event) => {
      if (!library.contains(event.relatedTarget)) library.classList.remove("is-dragging");
    });
    library.addEventListener("drop", (event) => {
      if (!event.dataTransfer.files.length) return;
      event.preventDefault();
      library.classList.remove("is-dragging");
      uploadFiles(event.dataTransfer.files);
    });

    document.addEventListener("keydown", (event) => {
      if (!$("loginScreen").hidden) return;
      const mod = event.ctrlKey || event.metaKey;
      if (mod && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setConsole(true, true);
      } else if (mod && event.key.toLowerCase() === "j") {
        event.preventDefault();
        setConsole(!state.consoleOpen, !state.consoleOpen);
      } else if (event.key === "Escape") {
        if ($("app").dataset.menu === "open") setMenu(false);
        else if (state.consoleOpen && $("console").contains(document.activeElement)) {
          setConsole(false);
          $("consoleToggle").focus();
        } else if (state.selectedAtom != null) selectAtom(null);
        else if (state.focus) setFocus(false);
      }
    });

    CrystaLab.assinar("erro", () => setConsole(true));

    /* ---------- Início ---------- */
    try { state.elementColors = JSON.parse(store.get("crystalab-cores") || "{}") || {}; } catch (error) { state.elementColors = {}; }
    renderModeSwitch();
    renderBlocks();
    renderGenericRow();
    fillLigaSelects();
    setSidebar(store.get("crystalab-lateral") === "open", false);
    initTheme();
    viewer.init();
    applyResult(data.inicial);
    renderLigaPanel(null);
    logLine("Terminal pronto. Digite 'ajuda' para ver os comandos.");

    const savedUser = store.get("crystalab-usuario") || store.get("crystalab-usuario", true);
    if (savedUser && UFC_EMAIL.test(savedUser)) completeLogin(savedUser, Boolean(store.get("crystalab-usuario")));
    else showLogin();
  </script>
</body>
</html>
"""


PASTA_BASE = Path(__file__).resolve().parent
PASTA_TUTORIAIS = PASTA_BASE / "tutoriais"
ARQUIVO_USUARIOS = PASTA_BASE / "crystalab_usuarios.json"
ARQUIVO_INDICE = ".crystalab_indice.json"
LIMITE_UPLOAD = 2 * 1024 ** 3
_TRAVA = threading.Lock()
EMAIL_UFC = re.compile(r"^[a-z0-9._%+-]+@([a-z0-9-]+\.)*ufc\.br$", re.IGNORECASE)

# Extensão → (categoria, tipo MIME). Nada que o navegador execute (HTML, SVG, JS) é aceito.
TIPOS_TUTORIAL: Dict[str, Tuple[str, str]] = {
    ".txt": ("texto", "text/plain; charset=utf-8"),
    ".md": ("texto", "text/plain; charset=utf-8"),
    ".mp4": ("video", "video/mp4"),
    ".webm": ("video", "video/webm"),
    ".pdf": ("pdf", "application/pdf"),
    ".csv": ("planilha", "text/csv; charset=utf-8"),
    ".xlsx": ("planilha", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ".xls": ("planilha", "application/vnd.ms-excel"),
    ".ods": ("planilha", "application/vnd.oasis.opendocument.spreadsheet"),
    ".docx": ("documento", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ".doc": ("documento", "application/msword"),
    ".odt": ("documento", "application/vnd.oasis.opendocument.text"),
}


def _ler_json(caminho: Path, padrao: Any) -> Any:
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, ValueError):
        return padrao


def _gravar_json(caminho: Path, dados: Any) -> None:
    temporario = caminho.with_name(caminho.name + ".tmp")
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, caminho)


def email_valido(texto: str) -> Optional[str]:
    email = (texto or "").strip().lower()
    return email if (len(email) <= 120 and EMAIL_UFC.match(email)) else None


def registrar_login(payload: Dict[str, Any]) -> Dict[str, Any]:
    email = email_valido(str(payload.get("email") or ""))
    if not email:
        raise ValueError("Use seu e-mail institucional da UFC (terminado em ufc.br, como @alu.ufc.br).")
    agora = datetime.now().isoformat(timespec="seconds")
    with _TRAVA:
        usuarios = _ler_json(ARQUIVO_USUARIOS, {})
        registro = usuarios.get(email) or {"primeiro_acesso": agora, "acessos": 0}
        registro["ultimo_acesso"] = agora
        registro["acessos"] = int(registro.get("acessos", 0)) + 1
        usuarios[email] = registro
        _gravar_json(ARQUIVO_USUARIOS, usuarios)
    return {"email": email, **registro}


def nome_seguro(nome: str) -> str:
    nome = unicodedata.normalize("NFC", os.path.basename(str(nome or "").replace("\\", "/")))
    nome = re.sub(r'[\x00-\x1f<>:"/\\|?*]', "_", nome).strip().strip(".").strip()
    extensao = os.path.splitext(nome)[1].lower()
    if not nome or len(nome) > 160 or not os.path.splitext(nome)[0].strip():
        raise ValueError("Nome de arquivo inválido.")
    if extensao not in TIPOS_TUTORIAL:
        raise ValueError(f"Formato não aceito ({extensao or 'sem extensão'}). Use: {', '.join(TIPOS_TUTORIAL)}.")
    return nome


def caminho_tutorial(nome: str) -> Path:
    pasta = PASTA_TUTORIAIS.resolve()
    caminho = (pasta / nome_seguro(nome)).resolve()
    if caminho.parent != pasta:
        raise ValueError("Caminho inválido.")
    return caminho


def _titulo_arquivo(raiz: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_]+", " ", raiz)).strip()


def _descrever_tutorial(caminho: Path, indice: Dict[str, Any]) -> Dict[str, Any]:
    info = caminho.stat()
    extensao = caminho.suffix.lower()
    return {
        "nome": caminho.name,
        "titulo": _titulo_arquivo(caminho.stem),
        "tipo": TIPOS_TUTORIAL[extensao][0],
        "extensao": extensao[1:],
        "tamanho": info.st_size,
        "modificado": datetime.fromtimestamp(info.st_mtime).isoformat(timespec="minutes"),
        "autor": (indice.get(caminho.name) or {}).get("autor"),
    }


def listar_tutoriais() -> Dict[str, Any]:
    PASTA_TUTORIAIS.mkdir(parents=True, exist_ok=True)
    indice = _ler_json(PASTA_TUTORIAIS / ARQUIVO_INDICE, {})
    arquivos = [
        _descrever_tutorial(item, indice)
        for item in sorted(PASTA_TUTORIAIS.iterdir(), key=lambda p: p.name.lower())
        if item.is_file() and not item.name.startswith(".") and item.suffix.lower() in TIPOS_TUTORIAL
    ]
    return {"pasta": str(PASTA_TUTORIAIS), "arquivos": arquivos}


def _nome_livre(nome: str) -> Path:
    raiz, extensao = os.path.splitext(nome)
    candidato = PASTA_TUTORIAIS / nome
    contador = 2
    while candidato.exists():
        candidato = PASTA_TUTORIAIS / f"{raiz} ({contador}){extensao}"
        contador += 1
    return candidato


def bootstrap_payload() -> Dict[str, Any]:
    return {
        "metais": metais_publicos(),
        "intersticiais": {simbolo: {chave: valor for chave, valor in dados.items() if chave != "aliases"} for simbolo, dados in INTERSTICIAIS.items()},
        "estruturas": tabela_estruturas(),
        "inicial": calcular_estrutura({"nome": "Fe"}),
        "tutoriais": {"formatos": list(TIPOS_TUTORIAL), "limite": LIMITE_UPLOAD},
    }


def render_index() -> bytes:
    payload = json.dumps(bootstrap_payload(), ensure_ascii=False).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__BOOTSTRAP_JSON__", payload).encode("utf-8")


class CrystaLabRequestHandler(BaseHTTPRequestHandler):
    server_version = "CrystaLab/1.4"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_bytes(self, body: bytes, content_type: str = "text/html; charset=utf-8", status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status)

    def _erro(self, mensagem: str, status: int = 400) -> None:
        self._send_json({"ok": False, "error": mensagem}, status)

    def _responder_calculo(self, funcao: Any, payload: Dict[str, Any]) -> None:
        try:
            resultado = funcao(payload)
        except ValueError as erro:
            self._erro(str(erro))
            return
        self._send_json({"ok": True, "result": resultado})

    def _host_permitido(self) -> bool:
        # Barra DNS rebinding: só atende quem chama pelo endereço local.
        host = (self.headers.get("Host") or "").strip().lower()
        if host.startswith("["):
            host = host[1:].split("]")[0]
        else:
            host = host.split(":")[0]
        if host in ("127.0.0.1", "localhost", "::1"):
            return True
        self._erro("Acesso permitido apenas por 127.0.0.1 ou localhost.", 403)
        return False

    def _escrita_permitida(self) -> bool:
        # O cabeçalho próprio força preflight CORS, que este servidor não autoriza: outros sites não conseguem escrever.
        if not self._host_permitido():
            return False
        if self.headers.get("X-CrystaLab") != "1":
            self._erro("Requisição sem o cabeçalho X-CrystaLab.", 403)
            return False
        return True

    def do_GET(self) -> None:
        if not self._host_permitido():
            return
        url = urlparse(self.path)
        path = url.path
        if path == "/":
            self._send_bytes(render_index())
            return
        if path == "/api/bootstrap":
            self._send_json(bootstrap_payload())
            return
        if path == "/api/metais":
            self._send_json({"ok": True, "metais": metais_publicos()})
            return
        if path == "/api/estruturas":
            self._send_json({"ok": True, "estruturas": tabela_estruturas()})
            return
        if path == "/api/estrutura":
            consulta = {chave: valores[0] for chave, valores in parse_qs(url.query).items()}
            self._responder_calculo(calcular_estrutura, consulta)
            return
        if path == "/api/tutoriais":
            self._send_json({"ok": True, "result": listar_tutoriais()})
            return
        if path.startswith("/tutoriais/"):
            self._enviar_tutorial(unquote(path[len("/tutoriais/"):]))
            return
        self._erro("Rota não encontrada.", 404)

    def do_HEAD(self) -> None:
        if not self._host_permitido():
            return
        path = urlparse(self.path).path
        if path.startswith("/tutoriais/"):
            self._enviar_tutorial(unquote(path[len("/tutoriais/"):]), corpo=False)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        if not self._escrita_permitida():
            return
        url = urlparse(self.path)
        path = url.path
        if path == "/api/tutoriais":
            self._receber_tutorial(parse_qs(url.query))
            return

        content_length = int(self.headers.get("Content-Length", "0") or 0)
        if content_length > 1024 * 1024:
            self.close_connection = True
            self._erro("Corpo da requisição grande demais.", 413)
            return
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            self._erro("JSON inválido.")
            return
        if not isinstance(payload, dict):
            self._erro("O corpo da requisição deve ser um objeto JSON.")
            return

        rotas = {
            "/api/estrutura": calcular_estrutura,
            "/api/miller": calcular_miller,
            "/api/liga": calcular_liga,
            "/api/termico": calcular_termico,
            "/api/login": registrar_login,
        }
        if path in rotas:
            self._responder_calculo(rotas[path], payload)
            return
        self._erro("Rota não encontrada.", 404)

    def do_DELETE(self) -> None:
        if not self._escrita_permitida():
            return
        path = urlparse(self.path).path
        if not path.startswith("/api/tutoriais/"):
            self._erro("Rota não encontrada.", 404)
            return
        try:
            caminho = caminho_tutorial(unquote(path[len("/api/tutoriais/"):]))
        except ValueError as erro:
            self._erro(str(erro))
            return
        if not caminho.is_file():
            self._erro("Arquivo não encontrado.", 404)
            return
        with _TRAVA:
            caminho.unlink()
            indice_arquivo = PASTA_TUTORIAIS / ARQUIVO_INDICE
            indice = _ler_json(indice_arquivo, {})
            if indice.pop(caminho.name, None) is not None:
                _gravar_json(indice_arquivo, indice)
        self._send_json({"ok": True, "result": {"nome": caminho.name}})

    def _receber_tutorial(self, consulta: Dict[str, List[str]]) -> None:
        try:
            nome = nome_seguro((consulta.get("nome") or [""])[0])
        except ValueError as erro:
            self.close_connection = True
            self._erro(str(erro))
            return
        try:
            tamanho = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.close_connection = True
            self._erro("Envie o tamanho do arquivo (Content-Length).", 411)
            return
        if tamanho < 0 or tamanho > LIMITE_UPLOAD:
            self.close_connection = True
            self._erro(f"Arquivo acima do limite de {LIMITE_UPLOAD // 1024 ** 3} GB.", 413)
            return

        PASTA_TUTORIAIS.mkdir(parents=True, exist_ok=True)
        with _TRAVA:
            destino = _nome_livre(nome)
            temporario = destino.with_name(destino.name + ".parte")
            temporario.touch()
        restante = tamanho
        try:
            with open(temporario, "wb") as arquivo:
                while restante > 0:
                    bloco = self.rfile.read(min(1024 * 1024, restante))
                    if not bloco:
                        raise ConnectionError("envio interrompido")
                    arquivo.write(bloco)
                    restante -= len(bloco)
            with _TRAVA:
                destino = _nome_livre(nome) if destino.exists() else destino
                os.replace(temporario, destino)
                autor = email_valido(unquote(self.headers.get("X-Usuario") or ""))
                indice_arquivo = PASTA_TUTORIAIS / ARQUIVO_INDICE
                indice = _ler_json(indice_arquivo, {})
                indice[destino.name] = {"autor": autor, "enviado": datetime.now().isoformat(timespec="seconds")}
                _gravar_json(indice_arquivo, indice)
                item = _descrever_tutorial(destino, indice)
        except (OSError, ConnectionError) as erro:
            try:
                temporario.unlink()
            except OSError:
                pass
            self.close_connection = True
            self._erro(f"Falha ao gravar o arquivo: {erro}", 500)
            return
        self._send_json({"ok": True, "result": item})

    def _enviar_tutorial(self, nome: str, corpo: bool = True) -> None:
        try:
            caminho = caminho_tutorial(nome)
        except ValueError:
            self._erro("Arquivo não encontrado.", 404)
            return
        if not caminho.is_file():
            self._erro("Arquivo não encontrado.", 404)
            return
        tamanho = caminho.stat().st_size
        inicio, fim, status = 0, tamanho - 1, 200
        faixa = (self.headers.get("Range") or "").strip()
        combinacao = re.match(r"bytes=(\d*)-(\d*)$", faixa)
        if combinacao and (combinacao.group(1) or combinacao.group(2)) and tamanho > 0:
            if combinacao.group(1):
                inicio = int(combinacao.group(1))
                fim = min(int(combinacao.group(2)), tamanho - 1) if combinacao.group(2) else tamanho - 1
            else:
                inicio = max(0, tamanho - int(combinacao.group(2)))
            if inicio > fim:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{tamanho}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            status = 206

        self.send_response(status)
        self.send_header("Content-Type", TIPOS_TUTORIAL[caminho.suffix.lower()][1])
        self.send_header("Content-Length", str(max(0, fim - inicio + 1)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Disposition", f"inline; filename*=UTF-8''{quote(caminho.name)}")
        if status == 206:
            self.send_header("Content-Range", f"bytes {inicio}-{fim}/{tamanho}")
        self.end_headers()
        if not corpo or tamanho == 0:
            return
        try:
            with open(caminho, "rb") as arquivo:
                arquivo.seek(inicio)
                restante = fim - inicio + 1
                while restante > 0:
                    bloco = arquivo.read(min(256 * 1024, restante))
                    if not bloco:
                        break
                    self.wfile.write(bloco)
                    restante -= len(bloco)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # O player de vídeo cancela requisições ao pular para outro trecho.
            return


def encontrar_porta(preferida: int) -> int:
    for porta in range(preferida, preferida + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as teste:
            teste.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                teste.bind(("127.0.0.1", porta))
            except OSError:
                continue
            return porta
    raise RuntimeError("Nenhuma porta livre encontrada.")


def main() -> None:
    global PASTA_TUTORIAIS
    parser = argparse.ArgumentParser(description="CrystaLab: Fundamentos Estruturais")
    parser.add_argument("--port", type=int, default=8000, help="porta inicial do servidor")
    parser.add_argument("--open", action="store_true", help="abrir no navegador padrão")
    parser.add_argument("--tutoriais", type=Path, default=PASTA_TUTORIAIS, help="pasta com os arquivos da aba Tutoriais")
    args = parser.parse_args()

    PASTA_TUTORIAIS = args.tutoriais.expanduser().resolve()
    PASTA_TUTORIAIS.mkdir(parents=True, exist_ok=True)
    porta = encontrar_porta(args.port)
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), CrystaLabRequestHandler)
    url = f"http://127.0.0.1:{porta}"

    print(f"CrystaLab: Fundamentos Estruturais disponível em {url}")
    print(f"Tutoriais: {PASTA_TUTORIAIS}")
    print("Use Ctrl+C para encerrar.")

    if args.open:
        webbrowser.open(url)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
