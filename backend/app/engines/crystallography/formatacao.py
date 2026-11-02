"""Formatação de números para os textos didáticos (pt-BR)."""

from __future__ import annotations

import math
from typing import Sequence

SOBRESCRITO = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def txt(valor: float, casas: int = 3) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def sci(valor: float, casas: int = 3) -> str:
    if valor == 0:
        return "0"
    expoente = math.floor(math.log10(abs(valor)))
    mantissa = valor / 10 ** expoente
    return f"{txt(mantissa, casas)} × 10{str(expoente).translate(SOBRESCRITO)}"


def sinal(valor: float) -> str:
    return "+" if valor >= 0 else ""


def notacao(indices: Sequence[int], abre: str, fecha: str) -> str:
    def barra(valor: int) -> str:
        if valor >= 0:
            return str(valor)
        return "".join(digito + "̄" for digito in str(-valor))

    return abre + " ".join(barra(v) for v in indices) + fecha
