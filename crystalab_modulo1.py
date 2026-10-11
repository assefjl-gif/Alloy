import argparse
import json
import math
import socket
import unicodedata
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse


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

    atomos, arestas = geometria_celula(estrutura, c_a)
    contagem: List[Dict[str, Any]] = []
    for atomo in atomos:
        fracao, fracao_txt = _fracao(estrutura, atomo["tipo"])
        atomo["fracao"] = fracao
        atomo["fracao_txt"] = fracao_txt
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
        "interpretacao": interpretacao,
    }


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
    atomos, arestas = geometria_celula(estrutura, c_a)

    if tipo == "plano":
        return _calcular_plano(estrutura, indices, c_a, a_nm, atomos, arestas)
    return _calcular_direcao(estrutura, indices, c_a, a_nm, atomos)


def _calcular_plano(
    estrutura: str,
    indices: List[int],
    c_a: Optional[float],
    a_nm: Optional[float],
    atomos: List[Dict[str, Any]],
    arestas: List[List[List[float]]],
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

    def funcao(p: Sequence[float]) -> float:
        f = cart_para_frac(estrutura, p, c_a)
        return h * f[0] + k * f[1] + l * f[2] - deslocamento

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
        raise ValueError("Com a origem padrão, esse plano não intercepta a célula unitária desenhada.")

    gradiente = gradiente_plano(estrutura, h, k, l, c_a)
    modulo = _norma(gradiente)
    normal = (gradiente[0] / modulo, gradiente[1] / modulo, gradiente[2] / modulo)
    centro = tuple(sum(p[j] for p in pontos) / len(pontos) for j in range(3))
    eixo_u = _sub(pontos[0], centro)
    eixo_u = tuple(v / _norma(eixo_u) for v in eixo_u)
    eixo_v = _cross(normal, eixo_u)
    pontos.sort(key=lambda p: math.atan2(_dot(_sub(p, centro), eixo_v), _dot(_sub(p, centro), eixo_u)))

    area_vetor = (0.0, 0.0, 0.0)
    for idx, p in enumerate(pontos):
        q = pontos[(idx + 1) % len(pontos)]
        c = _cross(p, q)
        area_vetor = (area_vetor[0] + c[0], area_vetor[1] + c[1], area_vetor[2] + c[2])
    area = abs(_dot(area_vetor, normal)) / 2.0

    d_rel = 1.0 / modulo
    no_plano = [idx for idx, atomo in enumerate(atomos) if abs(funcao(atomo["pos"])) < EPS]

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
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
  <style>
    :root {
      color-scheme: light;
      --ink: #10131a;
      --ink-soft: #29313f;
      --graphite: #11151c;
      --graphite-2: #171d26;
      --panel: #f5f7fb;
      --panel-2: #ffffff;
      --line: #dbe2eb;
      --muted: #687386;
      --cyan: #1aa7d9;
      --green: #19a56b;
      --amber: #d79319;
      --red: #ce3f4f;
      --violet: #7256d9;
      --radius: 8px;
      --shadow: 0 18px 44px rgba(10, 14, 20, 0.18);
      --topbar-bg: rgba(255, 255, 255, 0.86);
      --track: #e6ebf2;
      --code-bg: #eef2f7;
      --chip-bg: rgba(255, 255, 255, 0.88);
      --stage-bg: #eef2f7;
      --stage-glow: #ffffff;
      --row-active: rgba(26, 167, 217, 0.1);
    }

    :root[data-theme="dark"] {
      color-scheme: dark;
      --ink: #eef3f8;
      --ink-soft: #c6d0dc;
      --panel: #0f141b;
      --panel-2: #161d27;
      --line: #263241;
      --muted: #8d9aab;
      --shadow: 0 18px 44px rgba(0, 0, 0, 0.45);
      --topbar-bg: rgba(17, 21, 28, 0.86);
      --track: #253040;
      --code-bg: #0f151d;
      --chip-bg: rgba(17, 21, 28, 0.82);
      --stage-bg: #0a0e13;
      --stage-glow: #1a2533;
      --row-active: rgba(68, 197, 242, 0.12);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", Arial, sans-serif;
      background: #0b0d10;
      color: var(--ink);
    }

    button,
    textarea,
    input {
      font: inherit;
    }

    .app-shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: minmax(340px, 430px) minmax(0, 1fr);
      background: var(--panel);
    }

    .left-lab {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto minmax(230px, 0.92fr) minmax(330px, 1.08fr);
      gap: 14px;
      padding: 18px;
      background: linear-gradient(180deg, #11151c 0%, #161c24 100%);
      color: #eef5f8;
      border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    .brand-row {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
    }

    .brand-row h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.08;
      color: #44c5f2;
      letter-spacing: 0;
    }

    .brand-row p {
      margin: 6px 0 0;
      color: #a9b6c6;
      font-size: 12px;
      line-height: 1.35;
    }

    .lab-badge {
      flex: 0 0 auto;
      min-width: 62px;
      padding: 7px 9px;
      border: 1px solid rgba(68, 197, 242, 0.38);
      border-radius: 999px;
      color: #d8f5ff;
      text-align: center;
      font-size: 11px;
      background: rgba(68, 197, 242, 0.09);
    }

    .block-bank,
    .terminal-panel {
      min-width: 0;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.035);
    }

    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      min-height: 40px;
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      color: #f3f7fb;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0;
    }

    .count-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 26px;
      height: 22px;
      padding: 0 8px;
      border-radius: 999px;
      color: #10131a;
      background: #44c5f2;
      font-size: 12px;
      font-weight: 800;
    }

    .block-list {
      height: calc(100% - 41px);
      overflow: auto;
      padding: 10px;
      display: grid;
      gap: 10px;
      align-content: start;
    }

    .alloy-block {
      min-height: 86px;
      padding: 11px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: var(--radius);
      background: #202833;
      cursor: grab;
      transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
      user-select: none;
    }

    .alloy-block:hover,
    .alloy-block.is-active {
      transform: translateY(-1px);
      border-color: rgba(68, 197, 242, 0.65);
      background: #263140;
    }

    .alloy-block:active {
      cursor: grabbing;
    }

    .block-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .block-name {
      min-width: 0;
      color: #ffffff;
      font-size: 14px;
      font-weight: 750;
      overflow-wrap: anywhere;
    }

    .block-tag {
      flex: 0 0 auto;
      padding: 3px 7px;
      border-radius: 999px;
      color: #11151c;
      background: #f2c85b;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .block-tag[data-s="CFC"] {
      background: #39c38d;
    }

    .block-tag[data-s="HC"] {
      background: #b9a6ff;
    }

    .block-tag[data-s="CS"] {
      background: #c9d4e2;
    }

    .block-tag[data-s="gen"] {
      background: #44c5f2;
    }

    .block-formula {
      margin: 8px 0 9px;
      color: #aebccc;
      font-size: 12px;
      line-height: 1.3;
    }

    .composition-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 5px;
    }

    .element-chip {
      min-height: 24px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 5px;
      background: rgba(68, 197, 242, 0.12);
      color: #dff7ff;
      border: 1px solid rgba(68, 197, 242, 0.18);
      font-size: 11px;
      font-weight: 700;
    }

    .terminal-panel {
      display: grid;
      grid-template-rows: auto minmax(96px, 0.78fr) auto minmax(110px, 1fr) auto;
    }

    .composition-editor {
      width: 100%;
      min-height: 92px;
      resize: none;
      border: 0;
      outline: 0;
      padding: 12px;
      color: #f7fbff;
      background: #202833;
      line-height: 1.38;
      font-family: Consolas, "Courier New", monospace;
      font-size: 13px;
    }

    .composition-editor.is-drop-target {
      box-shadow: inset 0 0 0 2px #44c5f2;
      background: #253243;
    }

    .shortcut-row {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 7px;
      padding: 9px 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(0, 0, 0, 0.1);
    }

    .shortcut-row button,
    .terminal-submit,
    .primary-action {
      min-height: 34px;
      border: 0;
      border-radius: 6px;
      color: #071017;
      background: #44c5f2;
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
    }

    .shortcut-row button:nth-child(2) {
      background: #39c38d;
    }

    .shortcut-row button:nth-child(3) {
      background: #f2c85b;
    }

    .shortcut-row button:nth-child(4) {
      background: #c9d4e2;
    }

    .terminal-log {
      overflow: auto;
      padding: 12px;
      color: #dce6ef;
      background: #131922;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
    }

    .terminal-entry {
      color: #9de4ff;
    }

    .terminal-error {
      color: #ff9cab;
    }

    .terminal-ok {
      color: #91f2c3;
    }

    .terminal-step {
      color: #f2d68a;
    }

    .terminal-input-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 86px;
      gap: 8px;
      padding: 10px;
      background: #202833;
    }

    .terminal-input {
      width: 100%;
      min-height: 36px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 6px;
      outline: 0;
      padding: 0 10px;
      color: #f8fbff;
      background: #10151d;
    }

    .output-panel {
      min-width: 0;
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      background: var(--panel);
    }

    .topbar {
      min-height: 76px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 18px;
      padding: 16px 22px;
      border-bottom: 1px solid var(--line);
      background: var(--topbar-bg);
      backdrop-filter: blur(12px);
    }

    .topbar h2 {
      margin: 0;
      color: var(--ink);
      font-size: 23px;
      line-height: 1.08;
      letter-spacing: 0;
    }

    .topbar p {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    .topbar-actions {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .theme-toggle {
      min-height: 40px;
      padding: 0 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel-2);
      color: var(--ink);
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
    }

    .primary-action {
      min-width: 130px;
      min-height: 40px;
      background: #11151c;
      color: #ffffff;
    }

    :root[data-theme="dark"] .primary-action {
      background: #44c5f2;
      color: #071017;
    }

    .result-scroll {
      min-width: 0;
      overflow: auto;
      padding: 18px 22px 26px;
      display: grid;
      gap: 16px;
      align-content: start;
    }

    .status-band {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(180px, 0.42fr);
      gap: 12px;
      align-items: stretch;
    }

    .verdict-box,
    .phase-box,
    .metric,
    .chart-panel,
    .table-panel,
    .interpretation-panel,
    .composition-panel {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel-2);
      box-shadow: var(--shadow);
    }

    .verdict-box,
    .phase-box {
      padding: 15px;
    }

    .label {
      display: block;
      margin-bottom: 7px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0;
    }

    .verdict-text {
      margin: 0;
      color: var(--cyan);
      font-size: 20px;
      font-weight: 850;
      line-height: 1.22;
      overflow-wrap: anywhere;
    }

    .verdict-sub {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    .phase-box strong {
      display: block;
      color: var(--ink);
      font-size: 16px;
      line-height: 1.25;
    }

    .phase-box span {
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(6, minmax(105px, 1fr));
      gap: 10px;
    }

    .metric {
      min-height: 86px;
      padding: 12px;
      box-shadow: none;
    }

    .metric-value {
      display: block;
      color: var(--ink);
      font-size: 22px;
      font-weight: 850;
      line-height: 1.08;
    }

    .metric-unit {
      display: block;
      margin-top: 7px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.25;
    }

    .chart-panel {
      display: grid;
      overflow: hidden;
    }

    .viewer-panel {
      grid-template-rows: auto auto minmax(0, 1fr) auto;
    }

    .panel-title {
      min-height: 42px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 11px 13px;
      border-bottom: 1px solid var(--line);
      color: var(--ink);
      font-size: 13px;
      font-weight: 800;
    }

    .panel-title span {
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
    }

    .viewer-toolbar {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 13px;
      border-bottom: 1px solid var(--line);
    }

    .miller-form,
    .toggle-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .segmented {
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
    }

    .segmented button {
      min-height: 34px;
      padding: 0 12px;
      border: 0;
      background: transparent;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
    }

    .segmented button.is-on {
      background: #11151c;
      color: #ffffff;
    }

    :root[data-theme="dark"] .segmented button.is-on {
      background: #44c5f2;
      color: #071017;
    }

    .miller-input {
      width: 150px;
      min-height: 34px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      outline: 0;
      background: var(--panel-2);
      color: var(--ink);
      font-family: Consolas, "Courier New", monospace;
      font-size: 13px;
    }

    .miller-input:focus {
      border-color: var(--cyan);
    }

    .tool-btn {
      min-height: 34px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel-2);
      color: var(--ink-soft);
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
    }

    .tool-btn.is-on {
      border-color: rgba(26, 167, 217, 0.7);
      background: var(--row-active);
      color: var(--cyan);
    }

    .tool-btn.primary {
      border-color: #44c5f2;
      background: #44c5f2;
      color: #071017;
    }

    .viewer-stage {
      position: relative;
      height: clamp(380px, 58vh, 660px);
      overflow: hidden;
      background: radial-gradient(circle at 50% 42%, var(--stage-glow) 0%, var(--stage-bg) 72%);
      cursor: grab;
      touch-action: none;
    }

    .viewer-stage:active {
      cursor: grabbing;
    }

    .viewer-stage canvas {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      display: block;
    }

    .viewer-legend {
      position: absolute;
      left: 12px;
      bottom: 12px;
      z-index: 2;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      pointer-events: none;
    }

    .legend-chip,
    .overlay-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 9px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--chip-bg);
      color: var(--ink-soft);
      font-size: 11px;
      font-weight: 700;
    }

    .legend-chip i,
    .overlay-chip i {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }

    .overlay-chip em {
      color: var(--muted);
      font-style: normal;
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

    .overlay-list {
      min-height: 46px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      padding: 10px 13px;
      border-top: 1px solid var(--line);
    }

    .overlay-empty {
      color: var(--muted);
      font-size: 12px;
    }

    code {
      padding: 1px 5px;
      border-radius: 4px;
      background: var(--code-bg);
      color: var(--ink);
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
    }

    .lower-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(270px, 0.8fr);
      gap: 14px;
    }

    .table-panel,
    .interpretation-panel,
    .composition-panel {
      overflow: hidden;
      box-shadow: none;
    }

    .table-scroll {
      overflow-x: auto;
    }

    .comparison-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .comparison-table th,
    .comparison-table td {
      padding: 11px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
    }

    .comparison-table th {
      color: #ffffff;
      background: #263140;
      font-size: 12px;
    }

    .comparison-table td {
      color: var(--ink-soft);
      background: var(--panel-2);
    }

    .comparison-table tr.is-current td {
      background: var(--row-active);
      color: var(--ink);
      font-weight: 700;
    }

    .comparison-table tr.is-current td:first-child {
      box-shadow: inset 3px 0 0 var(--cyan);
    }

    .table-note {
      margin: 0;
      padding: 10px 12px;
      color: var(--muted);
      font-size: 12px;
    }

    .interpretation-body,
    .composition-body {
      padding: 13px;
      display: grid;
      gap: 10px;
    }

    .interpretation-body p {
      margin: 0;
      color: var(--ink-soft);
      font-size: 13px;
      line-height: 1.45;
    }

    .count-row {
      display: grid;
      grid-template-columns: 112px minmax(0, 1fr) 96px;
      gap: 9px;
      align-items: center;
      color: var(--ink-soft);
      font-size: 13px;
    }

    .count-row span:last-child {
      text-align: right;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
    }

    .count-total {
      padding-top: 9px;
      border-top: 1px solid var(--line);
      color: var(--ink);
      font-weight: 800;
    }

    .bar-track {
      height: 9px;
      border-radius: 99px;
      background: var(--track);
      overflow: hidden;
    }

    .bar-fill {
      display: block;
      height: 100%;
      border-radius: 99px;
      background: linear-gradient(90deg, var(--cyan), var(--green));
    }

    .density-panel {
      box-shadow: var(--shadow);
    }

    .density-steps {
      padding: 13px;
      display: grid;
      gap: 12px;
    }

    .step {
      display: grid;
      grid-template-columns: 28px minmax(0, 1fr);
      gap: 10px;
      align-items: start;
    }

    .step-index {
      width: 28px;
      height: 28px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      background: #11151c;
      color: #ffffff;
      font-size: 12px;
      font-weight: 800;
    }

    :root[data-theme="dark"] .step-index {
      background: #44c5f2;
      color: #071017;
    }

    .step strong {
      display: block;
      color: var(--ink);
      font-size: 13px;
    }

    .step pre {
      margin: 6px 0 0;
      padding: 9px 11px;
      border-radius: 6px;
      background: var(--code-bg);
      color: var(--ink);
      font-family: Consolas, "Courier New", monospace;
      font-size: 12.5px;
      line-height: 1.5;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .step p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }

    .density-close {
      min-height: 26px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
    }

    @media (max-width: 1180px) {
      .metrics-grid {
        grid-template-columns: repeat(3, minmax(105px, 1fr));
      }

      .lower-grid,
      .status-band {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 860px) {
      .app-shell {
        grid-template-columns: 1fr;
      }

      .left-lab {
        min-height: auto;
        grid-template-rows: auto minmax(220px, 360px) minmax(330px, 420px);
      }

      .output-panel {
        min-height: auto;
      }

      .topbar {
        align-items: stretch;
        flex-direction: column;
      }

      .topbar-actions {
        width: 100%;
      }

      .primary-action {
        flex: 1;
      }
    }

    @media (max-width: 560px) {
      .left-lab,
      .result-scroll,
      .topbar {
        padding-left: 12px;
        padding-right: 12px;
      }

      .metrics-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .shortcut-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .miller-input {
        flex: 1;
        width: auto;
      }

      .count-row {
        grid-template-columns: 96px minmax(0, 1fr) 86px;
      }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="left-lab">
      <header class="brand-row">
        <div>
          <h1>CRYSTALAB: FUNDAMENTOS ESTRUTURAIS</h1>
          <p>Módulo 1 · células unitárias, índices de Miller e densidade teórica</p>
        </div>
        <div class="lab-badge">M1 · v1.0</div>
      </header>

      <section class="block-bank" aria-label="Metais e estruturas">
        <div class="section-title">
          <span>Blocos de cristais</span>
          <span class="count-pill" id="blockCount">0</span>
        </div>
        <div class="block-list" id="blockList" data-testid="block-list"></div>
      </section>

      <section class="terminal-panel" aria-label="Terminal do cristal">
        <div class="section-title">
          <span>Parâmetros da célula</span>
          <span id="currentName">Fe · CCC</span>
        </div>
        <textarea id="parameterEditor" class="composition-editor" spellcheck="false" data-testid="parameter-editor"></textarea>
        <div class="shortcut-row">
          <button type="button" data-command="calcular densidade">densidade</button>
          <button type="button" data-command="plano 1 1 1">plano 111</button>
          <button type="button" data-command="direcao 1 1 0">direção 110</button>
          <button type="button" data-command="limpar">limpar</button>
        </div>
        <div id="terminalLog" class="terminal-log" data-testid="terminal-log"></div>
        <form class="terminal-input-row" id="terminalForm">
          <input id="terminalInput" class="terminal-input" autocomplete="off" aria-label="Comando" placeholder="comando (ex.: usar Cu)" />
          <button class="terminal-submit" type="submit">enviar</button>
        </form>
      </section>
    </aside>

    <section class="output-panel">
      <header class="topbar">
        <div>
          <h2 id="resultTitle">Célula unitária</h2>
          <p id="resultSubtitle">Modelo de esferas rígidas · N_A = 6,022 × 10²³ átomos/mol</p>
        </div>
        <div class="topbar-actions">
          <button class="theme-toggle" id="themeToggle" type="button">☾ escuro</button>
          <button class="primary-action" id="renderButton" type="button" data-testid="render-button">RENDERIZAR</button>
        </div>
      </header>

      <main class="result-scroll" id="resultRoot" data-testid="result-root">
        <section class="status-band">
          <div class="verdict-box">
            <span class="label">Estrutura cristalina</span>
            <p class="verdict-text" id="structureVerdict">—</p>
            <p class="verdict-sub" id="structureSub"></p>
          </div>
          <div class="phase-box">
            <span class="label">Geometria</span>
            <strong id="phaseMain">—</strong>
            <span id="phaseSub"></span>
          </div>
        </section>

        <section class="metrics-grid" id="metricsGrid"></section>

        <section class="chart-panel viewer-panel">
          <div class="panel-title">Visualização 3D da célula unitária <span>arraste para girar · role para aproximar</span></div>
          <div class="viewer-toolbar">
            <form class="miller-form" id="millerForm">
              <div class="segmented" role="group" aria-label="Tipo de índice">
                <button type="button" data-mode="plano" class="is-on">Plano (hkl)</button>
                <button type="button" data-mode="direcao">Direção [uvw]</button>
              </div>
              <input id="millerInput" class="miller-input" value="1 1 1" autocomplete="off" aria-label="Índices de Miller" placeholder="1 1 1 ou 1 0 -1 1" />
              <button type="submit" class="tool-btn primary">desenhar</button>
              <button type="button" class="tool-btn" id="clearOverlaysButton">limpar índices</button>
            </form>
            <div class="toggle-row">
              <button type="button" class="tool-btn" data-toggle="rigid">esferas rígidas</button>
              <button type="button" class="tool-btn" data-toggle="rotate">auto-rotação</button>
              <button type="button" class="tool-btn is-on" data-toggle="axes">eixos</button>
              <button type="button" class="tool-btn" id="resetViewButton">resetar vista</button>
            </div>
          </div>
          <div class="viewer-stage" id="viewerStage" data-testid="viewer-stage">
            <div class="viewer-legend" id="viewerLegend"></div>
          </div>
          <div class="overlay-list" id="overlayList"></div>
        </section>

        <section class="interpretation-panel density-panel" id="densityPanel" hidden>
          <div class="panel-title">Passo a passo: densidade teórica <button type="button" class="density-close" id="densityClose">ocultar</button></div>
          <div class="density-steps" id="densitySteps"></div>
        </section>

        <section class="lower-grid">
          <div class="table-panel">
            <div class="panel-title">Comparação entre estruturas <span>modelo de esferas rígidas</span></div>
            <div class="table-scroll" id="comparisonTable"></div>
          </div>
          <div class="composition-panel">
            <div class="panel-title">Átomos por célula <span>contribuição por posição</span></div>
            <div class="composition-body" id="countBody"></div>
          </div>
        </section>

        <section class="interpretation-panel">
          <div class="panel-title">Interpretação didática <span id="interpretationTag">módulo 1</span></div>
          <div class="interpretation-body" id="interpretationBody"></div>
        </section>
      </main>
    </section>
  </div>

  <script>
    window.BOOTSTRAP_DATA = __BOOTSTRAP_JSON__;
  </script>
  <script>
    const data = window.BOOTSTRAP_DATA;
    const TYPE_COLORS = { vertice: "#1aa7d9", centro: "#d79319", face: "#19a56b", basal: "#19a56b", interior: "#7256d9" };
    const TYPE_LABELS = { vertice: "vértice", centro: "centro do cubo", face: "centro de face", basal: "centro basal", interior: "interior" };
    const OVERLAY_COLORS = ["#ce3f4f", "#f2a73b", "#7256d9", "#19a56b", "#ff6fa5", "#3f6ecf"];
    const state = {
      current: null,
      selectedKey: "",
      mode: "plano",
      overlays: [],
      rigid: false,
      autoRotate: false,
      showAxes: true,
      densityVisible: false,
      theme: "light"
    };

    const blockList = document.getElementById("blockList");
    const blockCount = document.getElementById("blockCount");
    const editor = document.getElementById("parameterEditor");
    const terminalLog = document.getElementById("terminalLog");
    const terminalForm = document.getElementById("terminalForm");
    const terminalInput = document.getElementById("terminalInput");
    const currentName = document.getElementById("currentName");
    const renderButton = document.getElementById("renderButton");
    const themeToggle = document.getElementById("themeToggle");
    const resultTitle = document.getElementById("resultTitle");
    const resultSubtitle = document.getElementById("resultSubtitle");
    const viewerStage = document.getElementById("viewerStage");
    const viewerLegend = document.getElementById("viewerLegend");
    const overlayList = document.getElementById("overlayList");
    const millerForm = document.getElementById("millerForm");
    const millerInput = document.getElementById("millerInput");
    const densityPanel = document.getElementById("densityPanel");
    const densitySteps = document.getElementById("densitySteps");

    function ptNumber(value, digits = 2) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/d";
      if (!Number.isFinite(Number(value))) return "∞";
      return Number(value).toLocaleString("pt-BR", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
      });
    }

    function compactNumber(value) {
      const number = Number(value);
      if (!Number.isFinite(number)) return String(value);
      if (Math.abs(number - Math.round(number)) < 0.0001) return String(Math.round(number));
      return number.toFixed(2).replace(".", ",");
    }

    function plainText(text) {
      return String(text).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
    }

    function parseNumber(text) {
      if (text === undefined || text === null) return null;
      const clean = String(text).trim().replace(",", ".");
      if (!clean) return null;
      const value = Number(clean);
      return Number.isFinite(value) ? value : NaN;
    }

    function logLine(text, className = "") {
      const line = document.createElement("div");
      if (className) line.className = className;
      line.textContent = text;
      terminalLog.appendChild(line);
      terminalLog.scrollTop = terminalLog.scrollHeight;
    }

    async function postJson(url, payload) {
      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const body = await response.json();
        if (!response.ok || !body.ok) {
          logLine(body.error || "Falha na requisição.", "terminal-error");
          return null;
        }
        return body.result;
      } catch (error) {
        logLine(`erro de comunicação: ${error.message}`, "terminal-error");
        return null;
      }
    }

    /* ---------- Visualizador 3D (Three.js) ---------- */

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
      const font = "700 64px Segoe UI, Arial";
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
      sprite.scale.set(size * (width / 96), size, 1);
      sprite.renderOrder = 10;
      return sprite;
    }

    function makeArrow(start, end, color, radius) {
      const s = new THREE.Vector3(...start);
      const e = new THREE.Vector3(...end);
      const direction = e.clone().sub(s);
      const length = direction.length();
      direction.normalize();
      const headLength = Math.min(0.13, length * 0.3);
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

      init() {
        if (!window.THREE) {
          viewerStage.insertAdjacentHTML("beforeend", '<div class="viewer-fallback">Não foi possível carregar o Three.js (verifique a conexão com a internet).<br />Os cálculos de FEA, densidade e índices continuam disponíveis.</div>');
          logLine("Three.js indisponível: visualização 3D desativada.", "terminal-error");
          return;
        }
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setClearColor(0x000000, 0);
        viewerStage.insertBefore(renderer.domElement, viewerLegend);

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(36, 1, 0.01, 100);
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

        Object.assign(this, { renderer, scene, camera, pivot, frame, atomsGroup, edgesGroup, overlaysGroup, axesGroup });
        this.sphereGeometry = new THREE.SphereGeometry(1, 36, 24);

        if (THREE.OrbitControls) {
          this.controls = new THREE.OrbitControls(camera, renderer.domElement);
          this.controls.enableDamping = true;
          this.controls.dampingFactor = 0.08;
          this.controls.autoRotateSpeed = 1.6;
          this.controls.enablePan = false;
        } else {
          this.setupManualControls();
        }

        const resize = () => {
          const width = viewerStage.clientWidth || 600;
          const height = viewerStage.clientHeight || 420;
          renderer.setSize(width, height);
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
        };
        if (window.ResizeObserver) new ResizeObserver(resize).observe(viewerStage);
        window.addEventListener("resize", resize);
        resize();

        const loop = () => {
          requestAnimationFrame(loop);
          if (this.controls) {
            this.controls.autoRotate = state.autoRotate;
            this.controls.update();
          } else if (state.autoRotate) {
            this.pivot.rotation.y += 0.006;
          }
          renderer.render(scene, camera);
        };
        this.ready = true;
        loop();
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

        const edgeGeometry = new THREE.BufferGeometry();
        edgeGeometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
        this.edgeMaterial = new THREE.LineBasicMaterial({ color: this.edgeColor() });
        this.edgesGroup.add(new THREE.LineSegments(edgeGeometry, this.edgeMaterial));

        this.atomMeshes = result.atomos.map((atom) => {
          const material = new THREE.MeshStandardMaterial({
            color: TYPE_COLORS[atom.tipo] || "#1aa7d9",
            roughness: 0.32,
            metalness: 0.22,
            emissive: 0x000000
          });
          const mesh = new THREE.Mesh(this.sphereGeometry, material);
          mesh.position.set(...atom.pos);
          this.atomsGroup.add(mesh);
          return mesh;
        });
        this.updateAtomScale();
        this.buildAxes(result);
        this.renderLegend(result);
        this.resetView();
      },

      updateAtomScale() {
        if (!this.ready || !state.current) return;
        const radius = state.current.raio_relativo * (state.rigid ? 1 : 0.32);
        this.atomMeshes.forEach((mesh) => mesh.scale.setScalar(radius));
      },

      buildAxes(result) {
        disposeGroup(this.axesGroup);
        const vectors = result.estrutura === "HC"
          ? [
              [[1.3, 0, 0], "a₁", "#ce3f4f"],
              [[-0.65, 1.126, 0], "a₂", "#19a56b"],
              [[-0.65, -1.126, 0], "a₃", "#d79319"],
              [[0, 0, result.c_a * 1.28], "c", "#1aa7d9"]
            ]
          : [
              [[1.32, 0, 0], "x", "#ce3f4f"],
              [[0, 1.32, 0], "y", "#19a56b"],
              [[0, 0, 1.32], "z", "#1aa7d9"]
            ];
        vectors.forEach(([tip, label, color]) => {
          this.axesGroup.add(makeArrow([0, 0, 0], tip, color, 0.007));
          const sprite = makeLabel(label, color, 0.11);
          sprite.position.set(tip[0] * 1.08, tip[1] * 1.08, tip[2] * 1.06);
          this.axesGroup.add(sprite);
        });
        const origin = makeLabel("O", state.theme === "dark" ? "#c6d0dc" : "#29313f", 0.09);
        origin.position.set(-0.07, -0.07, -0.07);
        this.axesGroup.add(origin);
        this.axesGroup.visible = state.showAxes;
      },

      renderLegend(result) {
        viewerLegend.innerHTML = result.contagem.map((group) => `
          <span class="legend-chip"><i style="background:${TYPE_COLORS[group.tipo]}"></i>${TYPE_LABELS[group.tipo]} (${group.fracao_txt})</span>
        `).join("");
      },

      resetView() {
        if (!this.ready) return;
        const distance = Math.max(2.4, this.boundRadius * 3.3);
        const direction = new THREE.Vector3(1, 0.62, -0.48).normalize();
        this.camera.position.copy(direction.multiplyScalar(distance));
        this.camera.lookAt(0, 0, 0);
        this.pivot.rotation.set(0, 0, 0);
        if (this.controls) {
          this.controls.target.set(0, 0, 0);
          this.controls.minDistance = distance * 0.35;
          this.controls.maxDistance = distance * 3;
          this.controls.update();
        }
      },

      addOverlay(overlay) {
        if (!this.ready) return;
        const group = new THREE.Group();
        if (overlay.tipo === "plano") {
          const points = overlay.poligono;
          const center = overlay.centro;
          const triangles = [];
          for (let i = 0; i < points.length; i++) {
            triangles.push(...center, ...points[i], ...points[(i + 1) % points.length]);
          }
          const geometry = new THREE.BufferGeometry();
          geometry.setAttribute("position", new THREE.Float32BufferAttribute(triangles, 3));
          const fill = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
            color: overlay.color,
            transparent: true,
            opacity: 0.32,
            side: THREE.DoubleSide,
            depthWrite: false
          }));
          fill.renderOrder = 2;
          const outlineGeometry = new THREE.BufferGeometry();
          outlineGeometry.setAttribute("position", new THREE.Float32BufferAttribute(points.flat(), 3));
          const outline = new THREE.LineLoop(outlineGeometry, new THREE.LineBasicMaterial({ color: overlay.color }));
          const label = makeLabel(overlay.notacao, overlay.color, 0.12);
          label.position.set(center[0] + overlay.normal[0] * 0.06, center[1] + overlay.normal[1] * 0.06, center[2] + overlay.normal[2] * 0.06);
          group.add(fill, outline, label);
        } else {
          group.add(makeArrow(overlay.inicio, overlay.fim, overlay.color, 0.016));
          const label = makeLabel(overlay.notacao, overlay.color, 0.12);
          label.position.set(
            overlay.inicio[0] + (overlay.fim[0] - overlay.inicio[0]) * 0.6,
            overlay.inicio[1] + (overlay.fim[1] - overlay.inicio[1]) * 0.6,
            overlay.inicio[2] + (overlay.fim[2] - overlay.inicio[2]) * 0.6 + 0.08
          );
          group.add(label);
        }
        this.overlaysGroup.add(group);
        this.highlightAtoms();
      },

      clearOverlays() {
        if (!this.ready) return;
        disposeGroup(this.overlaysGroup);
        this.highlightAtoms();
      },

      highlightAtoms() {
        const colorByAtom = new Map();
        state.overlays.forEach((overlay) => {
          overlay.atomos.forEach((index) => {
            if (!colorByAtom.has(index)) colorByAtom.set(index, overlay.color);
          });
        });
        this.atomMeshes.forEach((mesh, index) => {
          const color = colorByAtom.get(index);
          mesh.material.emissive.set(color || 0x000000);
          mesh.material.emissiveIntensity = color ? 0.45 : 0;
        });
      },

      applyTheme() {
        if (!this.ready || !state.current) return;
        if (this.edgeMaterial) this.edgeMaterial.color.setHex(this.edgeColor());
        this.buildAxes(state.current);
        disposeGroup(this.overlaysGroup);
        state.overlays.forEach((overlay) => this.addOverlay(overlay));
      }
    };

    /* ---------- Blocos, editor e painéis ---------- */

    function blockItems() {
      const generic = data.estruturas.map((structure) => ({
        key: `gen:${structure.sigla}`,
        name: `Célula ${structure.sigla}`,
        tag: "genérica",
        tagKey: "gen",
        formula: `${structure.nome} · ${structure.relacao}`,
        chips: [structure.sigla, `NC ${structure.nc}`, `n = ${structure.n}`],
        payload: { nome: structure.sigla }
      }));
      const metals = Object.entries(data.metais).map(([symbol, metal]) => ({
        key: symbol,
        name: `${symbol} · ${metal.nome}`,
        tag: metal.estrutura,
        tagKey: metal.estrutura,
        formula: `R = ${ptNumber(metal.raio, 4)} nm · A = ${ptNumber(metal.peso, 2)} g/mol`,
        chips: [metal.estrutura, `NC ${metal.nc}`, `ρ ${ptNumber(metal.densidade_exp, 2)}`],
        payload: { nome: symbol }
      }));
      return [...metals, ...generic];
    }

    function renderBlocks() {
      blockList.innerHTML = "";
      const items = blockItems();
      blockCount.textContent = items.length;

      for (const item of items) {
        const block = document.createElement("article");
        block.className = "alloy-block";
        block.draggable = true;
        block.dataset.key = item.key;
        block.tabIndex = 0;
        block.innerHTML = `
          <div class="block-head">
            <div class="block-name">${item.name}</div>
            <div class="block-tag" data-s="${item.tagKey}">${item.tag}</div>
          </div>
          <div class="block-formula">${item.formula}</div>
          <div class="composition-strip">
            ${item.chips.map((chip) => `<span class="element-chip">${chip}</span>`).join("")}
          </div>
        `;
        block.addEventListener("click", () => loadStructure(item.payload));
        block.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            loadStructure(item.payload);
          }
        });
        block.addEventListener("dragstart", (event) => {
          event.dataTransfer.setData("text/plain", item.key);
          event.dataTransfer.effectAllowed = "copy";
        });
        blockList.appendChild(block);
      }
    }

    function markActiveBlock() {
      document.querySelectorAll(".alloy-block").forEach((block) => {
        block.classList.toggle("is-active", block.dataset.key === state.selectedKey);
      });
    }

    function resultToEditor(result) {
      const lines = [
        `elemento = ${result.simbolo || "(genérico)"}`,
        `estrutura = ${result.estrutura}`,
        `raio = ${result.raio_nm ?? ""}`.padEnd(18) + "# nm",
        `peso = ${result.peso ?? ""}`.padEnd(18) + "# g/mol"
      ];
      if (result.estrutura === "HC") lines.push(`c/a = ${Number(result.c_a.toFixed(4))}`);
      editor.value = lines.join("\n");
    }

    function parseEditor() {
      const payload = {};
      const keys = {
        elemento: "nome", metal: "nome", nome: "nome",
        estrutura: "estrutura",
        raio: "raio", r: "raio",
        peso: "peso", massa: "peso",
        "c/a": "c_a", ca: "c_a"
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

    async function loadStructure(payload) {
      const result = await postJson("/api/estrutura", payload);
      if (result) applyResult(result);
      return result;
    }

    function applyEditor() {
      const payload = parseEditor();
      if (!payload.nome && !payload.estrutura) {
        logLine("Informe 'elemento = Fe' ou 'estrutura = CFC' no editor.", "terminal-error");
        return;
      }
      loadStructure(payload);
    }

    function applyResult(result) {
      state.current = result;
      state.selectedKey = result.simbolo && !result.editado ? result.simbolo : (result.generica && !result.raio_nm ? `gen:${result.estrutura}` : "");
      currentName.textContent = result.simbolo ? `${result.simbolo} · ${result.estrutura}` : `genérica · ${result.estrutura}`;
      resultToEditor(result);
      markActiveBlock();
      renderSummary(result);
      renderLower(result);
      if (state.densityVisible) renderDensity(result);
      state.overlays = [];
      renderOverlayList();
      viewer.build(result);

      const density = result.densidade ? ` · ρ = ${ptNumber(result.densidade, 3)} g/cm³` : "";
      logLine(`${result.rotulo}: ${result.estrutura} · NC ${result.nc} · FEA ${ptNumber(result.fea, 3)}${density}`, "terminal-ok");
    }

    function metric(label, value, unit) {
      return `
        <article class="metric">
          <span class="label">${label}</span>
          <span class="metric-value">${value}</span>
          <span class="metric-unit">${unit}</span>
        </article>
      `;
    }

    function renderSummary(result) {
      resultTitle.textContent = result.rotulo;
      resultSubtitle.textContent = result.generica && !result.raio_nm
        ? "Célula genérica em unidades do raio atômico R · informe r e A para obter a densidade"
        : "Modelo de esferas rígidas · N_A = 6,022 × 10²³ átomos/mol";
      document.getElementById("structureVerdict").textContent = `${result.estrutura_nome} (${result.estrutura})`;
      document.getElementById("structureSub").textContent = `Os átomos se tocam ao longo da ${result.contato} · ${result.relacao_a}`;
      document.getElementById("phaseMain").textContent = `NC = ${result.nc} · n = ${result.n} átomos/célula`;
      document.getElementById("phaseSub").textContent = result.estrutura === "HC"
        ? `c/a = ${ptNumber(result.c_a, 3)} (ideal 1,633)`
        : `Vazios: ${ptNumber(result.vazios * 100, 1)}% do volume da célula`;

      const lattice = result.a_nm
        ? metric("Parâmetro a", ptNumber(result.a_nm, 4), result.c_nm ? `nm · c = ${ptNumber(result.c_nm, 4)} nm` : "nm")
        : metric("Parâmetro a", `${ptNumber(result.a_em_R, 3)} R`, result.relacao_a);
      const densityUnit = result.densidade_exp ? `g/cm³ · exp. ${ptNumber(result.densidade_exp, 2)}` : "g/cm³";
      document.getElementById("metricsGrid").innerHTML = `
        ${metric("Estrutura", result.estrutura, result.estrutura_nome)}
        ${lattice}
        ${metric("FEA", ptNumber(result.fea, 3), `${ptNumber(result.vazios * 100, 1)}% de vazios`)}
        ${metric("Densidade", result.densidade ? ptNumber(result.densidade, 3) : "n/d", densityUnit)}
        ${metric("Coordenação", result.nc, "vizinhos mais próximos")}
        ${metric("Átomos/célula", result.n, "n efetivo")}
      `;
    }

    function renderLower(result) {
      const rows = data.estruturas.map((structure) => `
        <tr class="${structure.sigla === result.estrutura ? "is-current" : ""}">
          <td>${structure.sigla} · ${structure.nome}</td>
          <td>${structure.n}</td>
          <td>${structure.nc}</td>
          <td>${structure.relacao}</td>
          <td>${ptNumber(structure.fea, 3)}</td>
        </tr>
      `).join("");
      const hcNote = result.estrutura === "HC" && Math.abs(result.c_a - 1.633) > 0.002
        ? `<p class="table-note">FEA da HC na tabela usa c/a ideal (1,633). Com c/a = ${ptNumber(result.c_a, 3)} o FEA é ${ptNumber(result.fea, 4)}.</p>`
        : "";
      document.getElementById("comparisonTable").innerHTML = `
        <table class="comparison-table">
          <thead>
            <tr>
              <th>Estrutura</th>
              <th>n</th>
              <th>NC</th>
              <th>Relação a–R</th>
              <th>FEA</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
        ${hcNote}
      `;

      document.getElementById("countBody").innerHTML = result.contagem.map((group) => `
        <div class="count-row">
          <strong>${group.rotulo}</strong>
          <span class="bar-track"><span class="bar-fill" style="width:${Math.min(100, (group.contribuicao / result.n) * 100)}%"></span></span>
          <span>${group.quantidade} × ${group.fracao_txt} = ${compactNumber(group.contribuicao)}</span>
        </div>
      `).join("") + `
        <div class="count-row count-total">
          <strong>Total (n)</strong>
          <span></span>
          <span>${result.n} átomo${result.n > 1 ? "s" : ""}</span>
        </div>
      `;

      document.getElementById("interpretationTag").textContent = result.estrutura;
      document.getElementById("interpretationBody").innerHTML = result.interpretacao.map((line) => `<p>${line}</p>`).join("");
    }

    function renderDensity(result) {
      densityPanel.hidden = false;
      densitySteps.innerHTML = result.passos_densidade.map((step, index) => `
        <div class="step">
          <span class="step-index">${index + 1}</span>
          <div>
            <strong>${step.titulo}</strong>
            <pre>${step.formula}</pre>
            ${step.detalhe ? `<p>${step.detalhe}</p>` : ""}
          </div>
        </div>
      `).join("");
    }

    function showDensity() {
      const result = state.current;
      if (!result) return;
      state.densityVisible = true;
      renderDensity(result);
      densityPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      if (!result.densidade) {
        logLine(result.passos_densidade[0].detalhe, "terminal-error");
        return;
      }
      logLine(`densidade teórica — ${result.rotulo}`, "terminal-ok");
      result.passos_densidade.forEach((step, index) => logLine(`${index + 1}. ${step.titulo}\n   ${step.formula.replace(/\n/g, "\n   ")}`, "terminal-step"));
    }

    /* ---------- Índices de Miller ---------- */

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
        return `d = ${spacing} · ${overlay.atomos.length} centros atômicos no plano`;
      }
      const length = overlay.comprimento_nm ? `${ptNumber(overlay.comprimento_nm, 4)} nm` : `${ptNumber(overlay.comprimento_rel, 3)} a`;
      let linear = "";
      if (overlay.densidade_linear_nm) linear = ` · DL = ${ptNumber(overlay.densidade_linear_nm, 2)} át/nm`;
      else if (overlay.densidade_linear_rel) linear = ` · DL = ${ptNumber(overlay.densidade_linear_rel, 3)} át/a`;
      return `|v| = ${length}${linear}`;
    }

    function renderOverlayList() {
      if (!state.overlays.length) {
        overlayList.innerHTML = '<span class="overlay-empty">Nenhum plano ou direção desenhado. Ex.: <code>plano 1 1 1</code> · <code>direcao 1 1 0</code> · na HC: <code>plano 1 0 -1 1</code></span>';
        return;
      }
      overlayList.innerHTML = state.overlays.map((overlay) => `
        <span class="overlay-chip"><i style="background:${overlay.color}"></i><strong>${overlay.notacao}</strong>${overlay.notacao_alternativa ? ` <em>${overlay.notacao_alternativa}</em>` : ""} · ${overlayDetail(overlay)}</span>
      `).join("");
    }

    async function drawMiller(type, indices) {
      const result = state.current;
      if (!result) return;
      if (!indices || indices.length < 3) {
        logLine("Informe 3 índices inteiros (ou 4 na notação de Miller-Bravais para HC). Ex.: plano 1 1 1", "terminal-error");
        return;
      }
      const overlay = await postJson("/api/miller", {
        estrutura: result.estrutura,
        c_a: result.c_a,
        a_nm: result.a_nm,
        tipo: type,
        indices
      });
      if (!overlay || state.current !== result) return;
      overlay.color = OVERLAY_COLORS[state.overlays.length % OVERLAY_COLORS.length];
      state.overlays.push(overlay);
      viewer.addOverlay(overlay);
      renderOverlayList();
      const name = overlay.tipo === "plano" ? "plano" : "direção";
      const extra = overlay.notacao_alternativa ? ` = ${overlay.notacao_alternativa}` : "";
      logLine(`${name} ${overlay.notacao}${extra}: ${overlayDetail(overlay)}`, "terminal-ok");
      if (overlay.tipo === "direcao" && overlay.densidade_linear_rel === null) {
        logLine("o vetor não termina em um ponto da rede dentro da célula; densidade linear não calculada.", "terminal-step");
      }
    }

    function clearOverlays() {
      state.overlays = [];
      viewer.clearOverlays();
      renderOverlayList();
    }

    function setMode(mode) {
      state.mode = mode;
      document.querySelectorAll(".segmented button").forEach((button) => {
        button.classList.toggle("is-on", button.dataset.mode === mode);
      });
    }

    /* ---------- Terminal ---------- */

    function setToggle(name, value) {
      if (name === "rigid") {
        state.rigid = value;
        viewer.updateAtomScale();
      }
      if (name === "rotate") state.autoRotate = value;
      if (name === "axes") {
        state.showAxes = value;
        if (viewer.ready) viewer.axesGroup.visible = value;
      }
      const button = document.querySelector(`[data-toggle="${name}"]`);
      if (button) button.classList.toggle("is-on", value);
    }

    function executeCommand(rawCommand) {
      const command = rawCommand.trim();
      if (!command) return;
      logLine(`> ${command}`, "terminal-entry");
      const lower = plainText(command);

      if (lower === "ajuda" || lower === "help") {
        logLine([
          "comandos disponíveis:",
          "  usar Fe                      carrega um metal (Fe, Cu, Al, Mg, Ti, ...)",
          "  estrutura CFC [r=0.128 A=63.55 c/a=1.62]   célula genérica (CS, CCC, CFC, HC)",
          "  plano 1 1 1 | plano 1 0 -1 1 desenha um plano (hkl) ou (hkil)",
          "  direcao 1 1 0               desenha uma direção [uvw] ou [uvtw]",
          "  calcular densidade           passo a passo da densidade teórica",
          "  aplicar                      usa os parâmetros do editor",
          "  listar | esferas | girar | eixos | tema | limpar"
        ].join("\n"));
        return;
      }
      if (lower === "limpar") {
        clearOverlays();
        terminalLog.innerHTML = "";
        logLine("planos, direções e terminal limpos.", "terminal-ok");
        return;
      }
      if (lower === "calcular densidade" || lower === "densidade") {
        showDensity();
        return;
      }
      if (lower === "aplicar" || lower === "renderizar") {
        applyEditor();
        return;
      }
      if (lower === "listar") {
        const metals = Object.entries(data.metais).map(([symbol, metal]) => `${symbol} (${metal.estrutura})`).join(", ");
        logLine(`metais: ${metals}\nestruturas: ${data.estruturas.map((s) => s.sigla).join(", ")}`);
        return;
      }
      if (lower === "esferas") {
        setToggle("rigid", !state.rigid);
        logLine(state.rigid ? "esferas rígidas (raio real R)." : "esferas reduzidas.", "terminal-ok");
        return;
      }
      if (lower === "girar") {
        setToggle("rotate", !state.autoRotate);
        logLine(state.autoRotate ? "auto-rotação ligada." : "auto-rotação desligada.", "terminal-ok");
        return;
      }
      if (lower === "eixos") {
        setToggle("axes", !state.showAxes);
        return;
      }
      if (lower === "tema") {
        setTheme(state.theme === "dark" ? "light" : "dark");
        return;
      }

      const useMatch = command.match(/^usar\s+(.+)$/i);
      if (useMatch) {
        loadStructure({ nome: useMatch[1].trim() });
        return;
      }

      const structureMatch = lower.match(/^estrutura\s+([a-z]+)(.*)$/);
      if (structureMatch) {
        let rest = structureMatch[2];
        const payload = { nome: structureMatch[1] };
        const ratio = rest.match(/c\/a\s*=\s*([\d.,]+)/);
        if (ratio) {
          payload.c_a = ratio[1].replace(",", ".");
          rest = rest.replace(ratio[0], " ");
        }
        const radius = rest.match(/(?:^|\s)r\s*=\s*([\d.,]+)/);
        const weight = rest.match(/(?:^|\s)a\s*=\s*([\d.,]+)/);
        if (radius) payload.raio = radius[1].replace(",", ".");
        if (weight) payload.peso = weight[1].replace(",", ".");
        loadStructure(payload);
        return;
      }

      const planeMatch = lower.match(/^plano\s+(.+)$/);
      if (planeMatch) {
        setMode("plano");
        millerInput.value = planeMatch[1].replace(/[()]/g, "").trim();
        drawMiller("plano", parseIndices(planeMatch[1]));
        return;
      }

      const directionMatch = lower.match(/^direcao\s+(.+)$/);
      if (directionMatch) {
        setMode("direcao");
        millerInput.value = directionMatch[1].replace(/[\[\]]/g, "").trim();
        drawMiller("direcao", parseIndices(directionMatch[1]));
        return;
      }

      logLine("comando não reconhecido. digite 'ajuda'.", "terminal-error");
    }

    /* ---------- Tema ---------- */

    function setTheme(theme, persist = true) {
      state.theme = theme;
      document.documentElement.dataset.theme = theme;
      themeToggle.textContent = theme === "dark" ? "☀ claro" : "☾ escuro";
      if (persist) {
        try { localStorage.setItem("crystalab-theme", theme); } catch (error) {}
      }
      viewer.applyTheme();
    }

    function initTheme() {
      let stored = null;
      try { stored = localStorage.getItem("crystalab-theme"); } catch (error) {}
      const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(stored || (prefersDark ? "dark" : "light"), false);
    }

    /* ---------- Eventos ---------- */

    terminalForm.addEventListener("submit", (event) => {
      event.preventDefault();
      executeCommand(terminalInput.value);
      terminalInput.value = "";
    });

    document.querySelectorAll(".shortcut-row button").forEach((button) => {
      button.addEventListener("click", () => executeCommand(button.dataset.command));
    });

    document.querySelectorAll(".segmented button").forEach((button) => {
      button.addEventListener("click", () => setMode(button.dataset.mode));
    });

    document.querySelectorAll("[data-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const name = button.dataset.toggle;
        const current = { rigid: state.rigid, rotate: state.autoRotate, axes: state.showAxes }[name];
        setToggle(name, !current);
      });
    });

    millerForm.addEventListener("submit", (event) => {
      event.preventDefault();
      executeCommand(`${state.mode} ${millerInput.value}`);
    });

    document.getElementById("clearOverlaysButton").addEventListener("click", () => {
      clearOverlays();
      logLine("planos e direções removidos.", "terminal-ok");
    });
    document.getElementById("resetViewButton").addEventListener("click", () => viewer.resetView());
    document.getElementById("densityClose").addEventListener("click", () => {
      state.densityVisible = false;
      densityPanel.hidden = true;
    });

    renderButton.addEventListener("click", applyEditor);
    themeToggle.addEventListener("click", () => setTheme(state.theme === "dark" ? "light" : "dark"));

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

    renderBlocks();
    initTheme();
    viewer.init();
    applyResult(data.inicial);
    logLine("terminal pronto. digite 'ajuda' para ver os comandos.");
  </script>
</body>
</html>
"""


def bootstrap_payload() -> Dict[str, Any]:
    return {
        "metais": metais_publicos(),
        "estruturas": tabela_estruturas(),
        "inicial": calcular_estrutura({"nome": "Fe"}),
    }


def render_index() -> bytes:
    payload = json.dumps(bootstrap_payload(), ensure_ascii=False)
    return HTML_TEMPLATE.replace("__BOOTSTRAP_JSON__", payload).encode("utf-8")


class CrystaLabRequestHandler(BaseHTTPRequestHandler):
    server_version = "CrystaLab/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_bytes(self, body: bytes, content_type: str = "text/html; charset=utf-8", status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status)

    def _responder_calculo(self, funcao: Any, payload: Dict[str, Any]) -> None:
        try:
            resultado = funcao(payload)
        except ValueError as erro:
            self._send_json({"ok": False, "error": str(erro)}, 400)
            return
        self._send_json({"ok": True, "result": resultado})

    def do_GET(self) -> None:
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
        self._send_json({"ok": False, "error": "Rota não encontrada."}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "JSON inválido."}, 400)
            return
        if not isinstance(payload, dict):
            self._send_json({"ok": False, "error": "O corpo da requisição deve ser um objeto JSON."}, 400)
            return

        if path == "/api/estrutura":
            self._responder_calculo(calcular_estrutura, payload)
            return
        if path == "/api/miller":
            self._responder_calculo(calcular_miller, payload)
            return

        self._send_json({"ok": False, "error": "Rota não encontrada."}, 404)


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
    parser = argparse.ArgumentParser(description="CrystaLab: Fundamentos Estruturais")
    parser.add_argument("--port", type=int, default=8000, help="porta inicial do servidor")
    parser.add_argument("--open", action="store_true", help="abrir no navegador padrão")
    args = parser.parse_args()

    porta = encontrar_porta(args.port)
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), CrystaLabRequestHandler)
    url = f"http://127.0.0.1:{porta}"

    print(f"CrystaLab: Fundamentos Estruturais disponível em {url}")
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
