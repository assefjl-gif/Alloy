"""Manifesto do módulo para a plataforma Alloy (preparação para o ranking BE-5).

Cada módulo do Alloy (HEA, CrystaLab, futuros: DRX, difusão, siderurgia...)
declara aqui o que ocupa — prefixo de URL, porta própria, comandos de terminal,
chaves de armazenamento — para que dois módulos nunca disputem o mesmo recurso.
A plataforma lê ``MANIFESTO`` e monta o módulo com ``montar_em``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Tuple

from . import __version__

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI


@dataclass(frozen=True)
class ManifestoModulo:
    id: str
    nome: str
    versao: str
    prefixo_montagem: str
    porta_padrao: int
    fabrica_app: str
    rotas_api: Tuple[str, ...] = field(default_factory=tuple)
    comandos_terminal: Tuple[str, ...] = field(default_factory=tuple)
    prefixo_armazenamento_local: str = ""


MANIFESTO = ManifestoModulo(
    id="crystalab",
    nome="CrystaLab: Fundamentos Estruturais",
    versao=__version__,
    prefixo_montagem="/crystalab",
    # A matriz HEA Virtual Lab usa 8000; o CrystaLab passa a usar 8010 (achado BE-16 / seção 3).
    porta_padrao=8010,
    fabrica_app="crystalab.api.app:create_app",
    rotas_api=("/v1/crystals", "/v1/crystallography", "/v1/calculations", "/v1/export"),
    comandos_terminal=("ajuda", "usar", "estrutura", "plano", "direcao", "calcular densidade",
                       "aplicar", "listar", "esferas", "girar", "eixos", "tema", "limpar"),
    prefixo_armazenamento_local="crystalab-",
)


def montar_em(plataforma: FastAPI, prefixo: str = MANIFESTO.prefixo_montagem) -> None:
    """Monta o CrystaLab como sub-aplicação isolada dentro da plataforma Alloy.

    A UI usa apenas URLs relativas, então funciona tanto em ``/`` quanto em ``/crystalab/``.
    """
    from .api import create_app

    plataforma.mount(prefixo, create_app(), name=MANIFESTO.id)
