"""Contratos de dados que o motor HEA recebe por injeção (puro, sem I/O — ADR-004).

* ``IdentidadeElemento``: identidade e classificação do elemento (símbolo, nome, número atômico, categoria,
  grupo). NÃO traz valor de propriedade: o motor HEA continua lendo propriedades só do repositório de
  materiais (ADR-018 mantido; decisão D-1 do portão G1).
* ``RepositorioEntalpias``: matriz de entalpias de mistura por par (auditoria R1-HEA-01, seção 2.4.5).
  Sem matriz cadastrada, ``entalpia_par`` devolve ``None`` para todo par e ΔH_mix fica indisponível.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, Tuple, runtime_checkable

from ..procedencia import ValorReferencia

CODIGO_PAR = "entalpia_mistura_par"
UNIDADE_PAR = "kJ/mol"


@dataclass(frozen=True)
class IdentidadeElemento:
    simbolo: str
    nome: str
    numero_atomico: int
    categoria: str
    grupo: Optional[int] = None


def chave_par(a: str, b: str) -> Tuple[str, str]:
    """Par NÃO ordenado: sempre em ordem alfabética."""
    return (a, b) if a <= b else (b, a)


def rotulo_par(a: str, b: str) -> str:
    primeiro, segundo = chave_par(a, b)
    return f"{primeiro}-{segundo}"


@runtime_checkable
class RepositorioEntalpias(Protocol):
    versao_dados: Optional[str]

    def entalpia_par(self, a: str, b: str) -> Optional[ValorReferencia]:
        """Entalpia de mistura do par na composição equiatômica, kJ/mol. Simétrica em (a, b)."""
        ...

    def resumo(self) -> Dict[str, Any]:
        """``{"disponivel": bool, "n_pares": int, "fonte": texto ou None, "estado": texto ou None}``."""
        ...


class SemEntalpias:
    """Nenhuma matriz de pares: é a situação real do repositório nesta rodada (Q-01 aberta)."""

    versao_dados: Optional[str] = None

    def entalpia_par(self, a: str, b: str) -> Optional[ValorReferencia]:
        return None

    def resumo(self) -> Dict[str, Any]:
        return {"disponivel": False, "n_pares": 0, "fonte": None, "estado": None}


Identidades = Mapping[str, IdentidadeElemento]
