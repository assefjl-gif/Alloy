"""Dependências injetáveis da API (``Depends``): a API só conhece serviços (ARQUITETURA_FINAL §2)."""

from __future__ import annotations

from typing import Iterator

from fastapi import Request

from app.core.config import Settings
from app.services.calculo import ServicoCalculo
from app.services.provedor import servico_calculo


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_servico(request: Request) -> Iterator[ServicoCalculo]:
    with servico_calculo(request.app.state.settings, request.app.state.motor_banco) as servico:
        yield servico
