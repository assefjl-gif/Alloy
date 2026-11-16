"""Sítios intersticiais por estrutura (parecer R1-CRI-01, seção 3.4; contrato R1 §2.2).

Antes da rodada R1 o motor conhecia UM sítio por estrutura (``ligas.SITIOS``), com o comentário
"maior sítio intersticial de cada rede" — falso na CCC, onde o octaédrico é o MENOR (achado L-3).
Aqui estão os dois poliedros de cada rede, com posições, multiplicidade, número de vizinhos e razão
de raio livre.

Derivações (R = raio do solvente pela condição de contato de cada estrutura) — parecer §3.4:

* CS cúbico (½,½,½): 8 vértices a √3·a/2; a = 2R ⇒ r_livre = (√3 − 1)·R.
* CCC octaédrico (½,½,0): 2 vizinhos a a/2 e 4 a a/√2 (poliedro ACHATADO); a = 4R/√3 ⇒
  r_livre = (2/√3 − 1)·R ≈ 0,1547·R, medido no eixo curto.
* CCC tetraédrico (½,¼,0): 4 vizinhos a (√5/4)·a ⇒ r_livre = (√(5/3) − 1)·R ≈ 0,2910·R.
* CFC octaédrico (½,½,½): 6 vizinhos a a/2; a = 2√2·R ⇒ r_livre = (√2 − 1)·R ≈ 0,4142·R.
* CFC tetraédrico (¼,¼,¼): 4 vizinhos a (√3/4)·a ⇒ r_livre = (√(3/2) − 1)·R ≈ 0,2247·R.
* HC (base do motor, origem deslocada de (⅓,⅔,¼) em relação ao CIF): 1 octaédrico e 2 tetraédricos
  por átomo. Com c/a REAL as distâncias mudam: d_oct = a·√(⅓ + (c/a)²/16) e, no tetraédrico,
  d_tet = mín(3c/8, a·√(⅓ + (c/a)²/64)) — fora do c/a ideal o tetraedro deixa de ser equidistante
  (1 + 3 vizinhos). Com c/a ideal os dois reduzem aos fatores 0,4142·R e 0,2247·R do empacotamento compacto.

Letras de Wyckoff: o parecer as cita de memória; por decisão D-e do portão G1 a API devolve
``wyckoff: null`` até a conferência do auditor bibliográfico. As MULTIPLICIDADES (números de sítios)
são fato verificado por contagem.

Sítio padrão (``sitio = "auto"``): octaédrico em CCC, CFC e HC; cúbico em CS — é o comportamento
anterior do motor, mantido por decisão conservadora. A justificativa de cada caso vai na resposta e
``padrao_verificado`` é ``false`` enquanto não houver parecer com fonte (parecer §3.4).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .constantes import SQRT2, SQRT3
from .estruturas import c_a_ideal

Vetor3 = Tuple[float, float, float]

_UM_TERCO = 1.0 / 3.0
_DOIS_TERCOS = 2.0 / 3.0

#: Posições fracionárias (na célula replicada pela supercélula), NC e rótulos de cada sítio.
SITIOS_INTERSTICIAIS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "CS": {
        "cubico": {"nome": "cúbico", "nc": 8, "nc_txt": "8",
                   "frac": [(0.5, 0.5, 0.5)]},
    },
    "CCC": {
        "octaedrico": {"nome": "octaédrico", "nc": 6, "nc_txt": "2 + 4",
                       "frac": [(0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5),
                                (0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, 0.5)]},
        "tetraedrico": {"nome": "tetraédrico", "nc": 4, "nc_txt": "4",
                        "frac": [(0.5, 0.25, 0.0), (0.5, 0.75, 0.0), (0.25, 0.5, 0.0), (0.75, 0.5, 0.0),
                                 (0.5, 0.0, 0.25), (0.5, 0.0, 0.75), (0.25, 0.0, 0.5), (0.75, 0.0, 0.5),
                                 (0.0, 0.5, 0.25), (0.0, 0.5, 0.75), (0.0, 0.25, 0.5), (0.0, 0.75, 0.5)]},
    },
    "CFC": {
        "octaedrico": {"nome": "octaédrico", "nc": 6, "nc_txt": "6",
                       "frac": [(0.5, 0.5, 0.5), (0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, 0.5)]},
        "tetraedrico": {"nome": "tetraédrico", "nc": 4, "nc_txt": "4",
                        "frac": [(x, y, z) for x in (0.25, 0.75) for y in (0.25, 0.75) for z in (0.25, 0.75)]},
    },
    "HC": {
        "octaedrico": {"nome": "octaédrico", "nc": 6, "nc_txt": "6",
                       "frac": [(_UM_TERCO, _DOIS_TERCOS, 0.25), (_UM_TERCO, _DOIS_TERCOS, 0.75)]},
        "tetraedrico": {"nome": "tetraédrico", "nc": 4, "nc_txt": "4",
                        "frac": [(0.0, 0.0, 0.375), (0.0, 0.0, 0.625),
                                 (_DOIS_TERCOS, _UM_TERCO, 0.125), (_DOIS_TERCOS, _UM_TERCO, 0.875)]},
    },
}

#: Sítio usado quando o pedido não escolhe (``sitio = "auto"``) — comportamento anterior do motor.
SITIO_PADRAO: Dict[str, str] = {"CS": "cubico", "CCC": "octaedrico", "CFC": "octaedrico", "HC": "octaedrico"}

#: Justificativa do padrão, por estrutura. Nenhuma delas é previsão de solubilidade.
JUSTIFICATIVA_PADRAO: Dict[str, str] = {
    "CS": "A cúbica simples tem um único tipo de sítio intersticial, no centro do cubo.",
    "CCC": ("Na CCC o sítio octaédrico é o MENOR dos dois (r_livre ≈ 0,155·R contra ≈ 0,291·R do "
            "tetraédrico). A literatura de aços atribui o carbono ao octaédrico porque ali ele desloca "
            "principalmente os 2 vizinhos do eixo curto — origem da tetragonalidade da martensita. "
            "Esta atribuição não foi conferida na fonte."),
    "CFC": ("Na CFC o sítio octaédrico é o maior dos dois (r_livre ≈ 0,414·R contra ≈ 0,225·R do "
            "tetraédrico). Atribuição usual para C e N em ferro CFC, não conferida na fonte."),
    "HC": ("No empacotamento compacto o sítio octaédrico é o maior (r_livre ≈ 0,414·R contra ≈ 0,225·R "
           "no c/a ideal). Atribuição não conferida na fonte."),
}

#: Para o hidrogênio o sítio preferido depende do metal (parecer §3.4): o padrão fica declarado como hipótese.
AVISO_H = ("Para o hidrogênio o sítio preferido depende do metal (em vários metais CCC e HC é o "
           "tetraédrico). O motor usa o octaédrico por padrão, sem fonte conferida: escolha o sítio "
           "explicitamente se o seu caso exigir outro.")


def tipos_de_sitio(estrutura: str) -> List[str]:
    return list(SITIOS_INTERSTICIAIS[estrutura])


def sitio_padrao(estrutura: str) -> str:
    return SITIO_PADRAO[estrutura]


def posicoes(estrutura: str, tipo: str) -> List[Vetor3]:
    return [tuple(float(v) for v in f) for f in SITIOS_INTERSTICIAIS[estrutura][tipo]["frac"]]  # type: ignore[misc]


def sitios_por_celula(estrutura: str, tipo: str) -> int:
    return len(SITIOS_INTERSTICIAIS[estrutura][tipo]["frac"])


def distancias_vizinhos(estrutura: str, tipo: str, c_a: Optional[float] = None) -> List[Tuple[float, int]]:
    """Distâncias (em unidades de ``a``) e quantidade de vizinhos do sítio, na rede IDEAL do solvente.

    Valores derivados em §3.4 do parecer; no HC dependem do c/a em uso.
    """
    if estrutura == "CS":
        return [(SQRT3 / 2.0, 8)]
    if estrutura == "CCC":
        return [(0.5, 2), (1.0 / SQRT2, 4)] if tipo == "octaedrico" else [(math.sqrt(5.0) / 4.0, 4)]
    if estrutura == "CFC":
        return [(0.5, 6)] if tipo == "octaedrico" else [(SQRT3 / 4.0, 4)]
    razao = float(c_a if c_a is not None else c_a_ideal())
    if tipo == "octaedrico":
        return [(math.sqrt(_UM_TERCO + razao ** 2 / 16.0), 6)]
    vertical = 3.0 * razao / 8.0
    lateral = math.sqrt(_UM_TERCO + razao ** 2 / 64.0)
    camadas = sorted(((vertical, 1), (lateral, 3)))
    if abs(vertical - lateral) <= 1e-12 * max(vertical, lateral):
        return [(vertical, 4)]
    return camadas


def fator_raio_livre(estrutura: str, tipo: str, c_a: Optional[float] = None) -> float:
    """r_livre/R: a menor distância sítio–átomo menos R, em unidades de R (R = metade da aresta de contato).

    Nas cúbicas vale o fator analítico; no HC é calculado pela geometria com o c/a em uso (corrige L-10,
    que usava sempre o fator do c/a ideal).
    """
    if estrutura == "CS":
        return SQRT3 - 1.0
    if estrutura == "CCC":
        return (2.0 / SQRT3 - 1.0) if tipo == "octaedrico" else (math.sqrt(5.0 / 3.0) - 1.0)
    if estrutura == "CFC":
        return (SQRT2 - 1.0) if tipo == "octaedrico" else (math.sqrt(1.5) - 1.0)
    # HC: R = a/2 (contato basal), distância em unidades de a → fator = 2·d_min/a − 1.
    d_min = min(d for d, _n in distancias_vizinhos("HC", tipo, c_a))
    return 2.0 * d_min - 1.0


def nc_texto(estrutura: str, tipo: str, c_a: Optional[float] = None) -> Tuple[int, str]:
    """(nc inteiro, nc como texto). O texto separa os grupos de vizinhos quando o poliedro é irregular."""
    camadas = distancias_vizinhos(estrutura, tipo, c_a)
    total = sum(n for _d, n in camadas)
    if len(camadas) == 1:
        return total, str(total)
    return total, " + ".join(str(n) for _d, n in camadas)


def descrever(estrutura: str, tipo: str, *, c_a: Optional[float] = None, raio_solvente_nm: float,
              elemento: str, escolha: str, simbolos_h: Sequence[str] = ("H",)) -> Dict[str, Any]:
    """Bloco ``SitioIntersticial`` do contrato (campos legados ``nome``, ``fator``, ``raio_nm``, ``nc`` + novos)."""
    fator = fator_raio_livre(estrutura, tipo, c_a)
    nc, nc_txt = nc_texto(estrutura, tipo, c_a)
    justificativa = JUSTIFICATIVA_PADRAO[estrutura]
    if escolha == "informado":
        justificativa = f"Sítio {SITIOS_INTERSTICIAIS[estrutura][tipo]['nome']} escolhido no pedido."
    elif elemento in simbolos_h:
        justificativa = f"{justificativa} {AVISO_H}"
    return {
        "nome": SITIOS_INTERSTICIAIS[estrutura][tipo]["nome"],
        "fator": fator,
        "raio_nm": fator * raio_solvente_nm,
        "nc": nc,
        "elemento": elemento,
        "tipo": tipo,
        "nc_txt": nc_txt,
        "sitios_por_celula": sitios_por_celula(estrutura, tipo),
        "wyckoff": None,
        "escolha": escolha,
        "justificativa": justificativa,
        "padrao_verificado": False,
    }
