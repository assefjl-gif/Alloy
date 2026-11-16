"""Validação da composição do HEA (contrato R1, seções 1.1 e 4.1; auditoria R1-HEA-01, seção 2.1).

Ordem de aplicação: quantidade → símbolo → existência → repetição → zeros → contagem. A conversão de base
mássica e a fração mínima ficam em ``analitico`` (dependem das massas do repositório).

Corrige A-02 (elemento inexistente aceito), A-03 (caixa do símbolo e duplicata), A-08 (estouro numérico → 500),
A-09 (texto e booleano aceitos como número) e A-10 (códigos de erro diferentes para a mesma regra).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Tuple

from .erros import EntradaHeaInvalida, detalhe, eco
from .referencia import Identidades

MAX_ELEMENTOS = 12
QUANTIDADE_MAXIMA = 1e6  # limite operacional (evita estouro de ponto flutuante); sem base científica
FRACAO_MINIMA = 1e-6     # resolução da saída (% com 4 casas)
_SIMBOLO = re.compile(r"[A-Za-z]{1,2}")

MSG_INSUFICIENTES = "Uma liga precisa de pelo menos 2 elementos com quantidade maior que zero."
BASES = ("atomica", "massica")


@dataclass(frozen=True)
class ComposicaoValidada:
    #: (símbolo canônico, quantidade > 0, chave como foi enviada), em ordem alfabética do símbolo
    itens: Tuple[Tuple[str, float, str], ...]
    zeros: Tuple[str, ...]
    soma: float


def _quantidade_valida(valor: Any) -> bool:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return False
    try:
        return math.isfinite(valor) and 0 <= valor <= QUANTIDADE_MAXIMA
    except OverflowError:  # inteiro grande demais para virar float
        return False


def validar_base(bruta: Any) -> str:
    base = "atomica" if bruta is None else bruta
    if base not in BASES:
        raise EntradaHeaInvalida([{"loc": ["base"], "type": "base_invalida",
                                   "msg": "Base da composição inválida: use 'atomica' ou 'massica'."}])
    return str(base)


def validar_composicao(bruta: Any, identidades: Identidades) -> ComposicaoValidada:
    if not isinstance(bruta, Mapping) or not bruta:
        raise EntradaHeaInvalida([detalhe(None, "elementos_insuficientes", MSG_INSUFICIENTES)])
    if len(bruta) > MAX_ELEMENTOS:
        raise EntradaHeaInvalida([detalhe(None, "elementos_demais", f"No máximo {MAX_ELEMENTOS} elementos por liga.")])

    # 1. quantidade: número (não texto, não booleano), finito, 0 ≤ q ≤ 1e6
    erros = [detalhe(chave, "quantidade_invalida",
                     f"A quantidade de {eco(str(chave).strip())} deve ser um número entre 0 e 1 000 000.")
             for chave, valor in bruta.items() if not _quantidade_valida(valor)]
    if erros:
        raise EntradaHeaInvalida(erros)

    # 2. símbolo: 1 ou 2 letras; forma canônica "Xx"
    canonicos: Dict[Any, str] = {}
    for chave in bruta:
        texto = str(chave).strip()
        if not isinstance(chave, str) or not _SIMBOLO.fullmatch(texto):
            erros.append(detalhe(chave, "simbolo_invalido",
                                 f"Símbolo inválido: '{eco(chave)}'. Use o símbolo químico do elemento, "
                                 "com 1 ou 2 letras (ex.: Fe, Ni, Co)."))
        else:
            canonicos[chave] = texto[0].upper() + texto[1:].lower()
    if erros:
        raise EntradaHeaInvalida(erros)

    # 3. existência na tabela periódica (identidade; nenhuma propriedade é lida)
    erros = [detalhe(chave, "elemento_desconhecido",
                     f"Elemento desconhecido: '{simbolo}'. Não existe na tabela periódica.")
             for chave, simbolo in canonicos.items() if simbolo not in identidades]
    if erros:
        raise EntradaHeaInvalida(erros)

    # 4. repetição depois da normalização: nunca somar duplicatas em silêncio
    primeira: Dict[str, Any] = {}
    for chave, simbolo in canonicos.items():
        if simbolo in primeira:
            erros.append(detalhe(chave, "elemento_repetido",
                                 f"Elemento repetido: '{eco(primeira[simbolo])}' e '{eco(chave)}' são o mesmo "
                                 f"elemento ({simbolo}). Informe cada elemento uma única vez."))
        else:
            primeira[simbolo] = chave
    if erros:
        raise EntradaHeaInvalida(erros)

    # 5 e 6. zeros descartados (com aviso na procedência) e pelo menos 2 elementos
    itens: List[Tuple[str, float, str]] = []
    zeros: List[str] = []
    for chave, simbolo in canonicos.items():
        quantidade = float(bruta[chave])
        if quantidade > 0:
            itens.append((simbolo, quantidade, str(chave)))
        else:
            zeros.append(simbolo)
    if len(itens) < 2:
        raise EntradaHeaInvalida([detalhe(None, "elementos_insuficientes", MSG_INSUFICIENTES)])
    itens.sort(key=lambda item: item[0])
    soma = math.fsum(q for _, q, _ in itens)
    return ComposicaoValidada(itens=tuple(itens), zeros=tuple(sorted(zeros)), soma=soma)
