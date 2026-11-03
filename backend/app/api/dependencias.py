"""Dependências injetáveis da API (``Depends``): a API só conhece serviços (ARQUITETURA_FINAL §2).

A sessão de banco é UMA por requisição (``get_sessao_db``, cacheada pelo FastAPI) e é compartilhada
pelo serviço de cálculo e pelo de autenticação — o histórico e a sessão do usuário entram no mesmo
commit do cálculo.
"""

from __future__ import annotations

from typing import Any, Iterator, Optional

from fastapi import Depends, Request

from app.core.config import Settings
from app.security.tokens import CABECALHO_CSRF, COOKIE_SESSAO
from app.services.autenticacao import Autenticado, ServicoAutenticacao
from app.services.calculo import ServicoCalculo
from app.services.erros import NaoAutenticado
from app.services.provedor import montar_servico_autenticacao, montar_servico_calculo, unidade_de_trabalho

METODOS_ESCRITA = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_sessao_db(request: Request) -> Iterator[Optional[Any]]:
    with unidade_de_trabalho(request.app.state.motor_banco) as sessao:
        yield sessao


def get_servico(request: Request, sessao=Depends(get_sessao_db)) -> ServicoCalculo:
    return montar_servico_calculo(request.app.state.settings, sessao)


def get_servico_auth(request: Request, sessao=Depends(get_sessao_db)) -> ServicoAutenticacao:
    return montar_servico_autenticacao(sessao, request.app.state.limitador_login)


def get_autenticado_opcional(request: Request, sessao=Depends(get_sessao_db)) -> Optional[Autenticado]:
    """Usuário da sessão, se houver cookie. Em escrita com cookie, o cabeçalho anti-CSRF é obrigatório.

    Sem banco não há contas: o cookie é ignorado e a requisição segue anônima.
    """
    token = request.cookies.get(COOKIE_SESSAO)
    if not token or sessao is None:
        return None
    servico = montar_servico_autenticacao(sessao, request.app.state.limitador_login)
    return servico.autenticar(token, csrf=request.headers.get(CABECALHO_CSRF),
                              exigir_csrf=request.method in METODOS_ESCRITA)


def get_autenticado(autenticado: Optional[Autenticado] = Depends(get_autenticado_opcional)) -> Autenticado:
    if autenticado is None:
        raise NaoAutenticado("Entre na sua conta para usar este recurso.")
    return autenticado


def usuario_id(autenticado: Optional[Autenticado]):
    return autenticado.usuario.id if autenticado else None
