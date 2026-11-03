"""Geradores de questões parametrizadas (RQ-EDU-01..03): o GABARITO É CALCULADO PELO MOTOR.

Cada gerador recebe uma semente e o repositório de materiais, sorteia os parâmetros com
``random.Random(semente)`` (reprodutível: mesma semente → mesma questão) e devolve:
* ``publico``: enunciado e parâmetros mostrados ao estudante;
* ``gabarito``: valor, unidade e tolerância — fica SÓ no servidor até a política liberar.
Nenhum número de gabarito é escrito à mão aqui: vem de ``calcular_estrutura``/``calcular_miller``.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from app.engines.crystallography import calcular_estrutura, calcular_miller
from app.engines.crystallography.formatacao import txt
from app.engines.crystallography.referencia import RepositorioMateriais
from app.engines.crystallography.versao import VERSAO_MOTOR

NOMES_ESTRUTURA = {"CS": "cúbica simples", "CCC": "cúbica de corpo centrado", "CFC": "cúbica de faces centradas"}
PLANOS = ((1, 0, 0), (1, 1, 0), (1, 1, 1), (2, 0, 0), (2, 1, 0), (2, 1, 1), (2, 2, 0))


@dataclass(frozen=True)
class QuestaoGerada:
    publico: Dict[str, Any]
    gabarito: Dict[str, Any]
    versao_motor: str = VERSAO_MOTOR


def _passos(passos: List[Mapping[str, Any]]) -> List[str]:
    return [f"{p['titulo']}: {p['formula']}" for p in passos]


def _cubicos(repo: RepositorioMateriais) -> List[Any]:
    return sorted((m for m in repo.listar() if m.estrutura in ("CCC", "CFC")), key=lambda m: m.simbolo)


def densidade_cubica(semente: int, repo: RepositorioMateriais) -> QuestaoGerada:
    rng = random.Random(semente)  # noqa: S311 — sorteio didático reprodutível, não criptográfico
    metal = rng.choice(_cubicos(repo))
    celula = calcular_estrutura({"nome": metal.simbolo}, repo)
    return QuestaoGerada(
        publico={"enunciado": (f"O {metal.nome} ({metal.simbolo}) tem estrutura {NOMES_ESTRUTURA[metal.estrutura]} "
                               f"({metal.estrutura}), raio atômico R = {txt(metal.raio_nm, 4)} nm e massa atômica "
                               f"A = {txt(metal.peso_g_mol, 2)} g/mol. Calcule a densidade teórica."),
                 "parametros": {"simbolo": metal.simbolo, "estrutura": metal.estrutura, "raio_nm": metal.raio_nm,
                                "peso_g_mol": metal.peso_g_mol},
                 "unidade": "g/cm³"},
        gabarito={"valor": celula["densidade"], "unidade": "g/cm³", "tolerancia_relativa": 0.02,
                  "resolucao": _passos(celula["passos_densidade"])})


def fea_estrutura(semente: int, repo: RepositorioMateriais) -> QuestaoGerada:
    rng = random.Random(semente)  # noqa: S311 — sorteio didático reprodutível, não criptográfico
    estrutura = rng.choice(("CS", "CCC", "CFC"))
    celula = calcular_estrutura({"nome": estrutura}, repo)
    return QuestaoGerada(
        publico={"enunciado": (f"Calcule o fator de empacotamento atômico (FEA) da estrutura "
                               f"{NOMES_ESTRUTURA[estrutura]} ({estrutura}), com átomos como esferas rígidas "
                               "em contato."),
                 "parametros": {"estrutura": estrutura}, "unidade": "adimensional"},
        gabarito={"valor": celula["fea"], "unidade": "adimensional", "tolerancia_absoluta": 0.005,
                  "resolucao": _passos(celula["passos_fea"])})


def espacamento_cubico(semente: int, repo: RepositorioMateriais) -> QuestaoGerada:
    rng = random.Random(semente)  # noqa: S311 — sorteio didático reprodutível, não criptográfico
    metal = rng.choice(_cubicos(repo))
    h, k, l = rng.choice(PLANOS)
    celula = calcular_estrutura({"nome": metal.simbolo}, repo)
    plano = calcular_miller({"estrutura": metal.estrutura, "tipo": "plano", "indices": [h, k, l],
                             "a_nm": celula["a_nm"]})
    return QuestaoGerada(
        publico={"enunciado": (f"No {metal.nome} ({metal.estrutura}, a = {txt(celula['a_nm'], 4)} nm), calcule a "
                               f"distância interplanar d dos planos ({h}{k}{l})."),
                 "parametros": {"simbolo": metal.simbolo, "estrutura": metal.estrutura, "a_nm": celula["a_nm"],
                                "indices": [h, k, l]},
                 "unidade": "nm"},
        gabarito={"valor": plano["d_nm"], "unidade": "nm", "tolerancia_relativa": 0.01,
                  "resolucao": [f"d = a / √(h² + k² + l²) = {txt(celula['a_nm'], 4)} / √{h * h + k * k + l * l}"]})


GERADORES: Dict[str, Tuple[str, Tuple[str, ...], Callable[[int, RepositorioMateriais], QuestaoGerada]]] = {
    "densidade_cubica": ("Densidade teórica de metal cúbico", ("densidade", "celula_unitaria"), densidade_cubica),
    "fea_estrutura": ("Fator de empacotamento atômico", ("fea", "celula_unitaria"), fea_estrutura),
    "espacamento_cubico": ("Distância interplanar em rede cúbica", ("miller", "planos"), espacamento_cubico),
}


def gerar(gerador: str, semente: int, repo: RepositorioMateriais) -> QuestaoGerada:
    if gerador not in GERADORES:
        raise KeyError(gerador)
    return GERADORES[gerador][2](semente, repo)


def corrigir(resposta: float, gabarito: Mapping[str, Any]) -> Tuple[bool, Optional[str]]:
    """Compara com a tolerância do gabarito e classifica o erro mais comum quando errado."""
    alvo = float(gabarito["valor"])
    if not math.isfinite(resposta):
        return False, "nao_classificado"
    if "tolerancia_absoluta" in gabarito:
        def dentro(valor: float) -> bool:
            return abs(valor - alvo) <= float(gabarito["tolerancia_absoluta"])
    else:
        def dentro(valor: float) -> bool:
            return abs(valor - alvo) <= float(gabarito["tolerancia_relativa"]) * abs(alvo)
    if dentro(resposta):
        return True, None
    if dentro(-resposta):
        return False, "sinal"
    if resposta and alvo:
        expoente = math.log10(abs(resposta / alvo))
        if abs(expoente - round(expoente)) < 0.01 and round(expoente) != 0 and dentro(resposta / 10 ** round(expoente)):
            return False, "fator_10n"
    return False, "nao_classificado"
