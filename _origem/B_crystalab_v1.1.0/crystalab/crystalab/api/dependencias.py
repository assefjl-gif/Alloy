"""Dependências injetáveis (``Depends``). Trocar a fonte de dados = trocar só isto."""

from __future__ import annotations

from fastapi import Request

from ..core.repositorio import RepositorioMateriais
from .config import Settings


def get_repositorio(request: Request) -> RepositorioMateriais:
    return request.app.state.repositorio


def get_settings(request: Request) -> Settings:
    return request.app.state.settings
