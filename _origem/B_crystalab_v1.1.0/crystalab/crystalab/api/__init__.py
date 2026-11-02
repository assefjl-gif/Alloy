"""Camada HTTP (FastAPI) do CrystaLab. Ponto de entrada: ``create_app``."""

from .app import create_app

__all__ = ["create_app"]
