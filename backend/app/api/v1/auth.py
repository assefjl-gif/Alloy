"""Rotas de conta e sessão (/api/v1/auth, /api/v1/me — ADR-008, API.md §2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.config import Settings
from app.security.tokens import COOKIE_SESSAO
from app.services.autenticacao import VIDA_MAXIMA, Autenticado, ServicoAutenticacao

from ..dependencias import get_autenticado, get_servico_auth, get_settings
from .schemas import (
    ErroEnvelope,
    HistoryPage,
    LoginRequest,
    OkEnvelope,
    RegisterRequest,
    SessionInfo,
    UserInfo,
)

_ERROS = {401: {"model": ErroEnvelope}, 403: {"model": ErroEnvelope}, 409: {"model": ErroEnvelope},
          422: {"model": ErroEnvelope}, 429: {"model": ErroEnvelope}, 503: {"model": ErroEnvelope}}

router = APIRouter(prefix="/api/v1", responses=_ERROS, tags=["conta"])


def _gravar_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(COOKIE_SESSAO, token, max_age=int(VIDA_MAXIMA.total_seconds()), path="/api",
                        httponly=True, secure=settings.cookie_seguro, samesite="lax")


def _apagar_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(COOKIE_SESSAO, path="/api", httponly=True, secure=settings.cookie_seguro, samesite="lax")


def _sem_cache(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post("/auth/register", response_model=OkEnvelope[UserInfo], status_code=201, summary="Cria uma conta")
def registrar(payload: RegisterRequest, response: Response, servico: ServicoAutenticacao = Depends(get_servico_auth)):
    _sem_cache(response)
    return {"ok": True, "result": servico.registrar(payload.nome, payload.email, payload.senha)}


@router.post("/auth/login", response_model=OkEnvelope[SessionInfo], summary="Abre sessão (cookie HttpOnly)")
def entrar(payload: LoginRequest, request: Request, response: Response,
           servico: ServicoAutenticacao = Depends(get_servico_auth), settings: Settings = Depends(get_settings)):
    """Devolve o token anti-CSRF no corpo; o token de sessão vai SÓ no cookie."""
    ip = request.client.host if request.client else None
    aberta = servico.entrar(payload.email, payload.senha, ip, request.headers.get("user-agent"))
    _gravar_cookie(response, settings, aberta.token)
    _sem_cache(response)
    return {"ok": True, "result": {"usuario": aberta.usuario, "csrf": aberta.csrf,
                                   "expira_em": aberta.expira_em.isoformat(timespec="seconds")}}


@router.get("/auth/me", response_model=OkEnvelope[SessionInfo], summary="Usuário da sessão + CSRF renovado")
def eu(response: Response, autenticado: Autenticado = Depends(get_autenticado),
       servico: ServicoAutenticacao = Depends(get_servico_auth)):
    usuario, csrf = servico.eu(autenticado)
    _sem_cache(response)
    expira = autenticado.sessao.expira_em
    return {"ok": True, "result": {"usuario": usuario, "csrf": csrf, "expira_em": expira.isoformat(timespec="seconds")}}


@router.post("/auth/logout", response_model=OkEnvelope[dict], summary="Encerra esta sessão")
def sair(response: Response, autenticado: Autenticado = Depends(get_autenticado),
         servico: ServicoAutenticacao = Depends(get_servico_auth), settings: Settings = Depends(get_settings)):
    servico.sair(autenticado)
    _apagar_cookie(response, settings)
    return {"ok": True, "result": {"encerradas": 1}}


@router.post("/auth/logout-all", response_model=OkEnvelope[dict], summary="Encerra todas as sessões da conta")
def sair_de_todos(response: Response, autenticado: Autenticado = Depends(get_autenticado),
                  servico: ServicoAutenticacao = Depends(get_servico_auth),
                  settings: Settings = Depends(get_settings)):
    encerradas = servico.sair_de_todos(autenticado)
    _apagar_cookie(response, settings)
    return {"ok": True, "result": {"encerradas": encerradas}}


@router.get("/me/history", response_model=OkEnvelope[HistoryPage], summary="Histórico pessoal de cálculos")
def historico(response: Response, limite: int = Query(20, ge=1, le=100), pagina: int = Query(1, ge=1, le=10_000),
              autenticado: Autenticado = Depends(get_autenticado),
              servico: ServicoAutenticacao = Depends(get_servico_auth)):
    _sem_cache(response)
    return {"ok": True, "result": servico.historico(autenticado, limite, pagina)}
