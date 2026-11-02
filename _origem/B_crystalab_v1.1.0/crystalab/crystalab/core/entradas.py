"""Leitura defensiva de entradas numéricas vindas de dicionários (payloads)."""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional, Tuple

from .erros import EntradaInvalida
from .formatacao import txt


def numero_opcional(payload: Mapping[str, Any], chave: str, faixa: Tuple[float, float],
                    descricao: str) -> Optional[float]:
    """Converte ``payload[chave]`` em float dentro da faixa; aceita vírgula decimal."""
    bruto = payload.get(chave)
    if bruto is None or (isinstance(bruto, str) and not bruto.strip()):
        return None
    if isinstance(bruto, bool):
        raise EntradaInvalida(f"Valor inválido para {descricao}: {bruto}")
    try:
        valor = float(str(bruto).replace(",", "."))
    except (TypeError, ValueError):
        raise EntradaInvalida(f"Valor inválido para {descricao}: {bruto}") from None
    minimo, maximo = faixa
    if not math.isfinite(valor) or not (minimo <= valor <= maximo):
        raise EntradaInvalida(f"{descricao[:1].upper()}{descricao[1:]} deve estar entre "
                              f"{txt(minimo, 2)} e {txt(maximo, 2)}.")
    return valor
