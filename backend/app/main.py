"""Aplicação FastAPI do Alloy Virtual Lab (origem: CrystaLab v1.1.0 ``api/app.py``).

Uso: ``uvicorn app.main:create_app --factory`` (dentro de ``backend/``).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from . import __version__
from .api.erros import register_exception_handlers
from .api.v1 import auth, rotas
from .api.v1.schemas import HealthResponse
from .core.config import Settings
from .core.request_id import RequestIdMiddleware
from .security.middlewares import CabecalhosSegurancaMiddleware, LimiteCorpoMiddleware, RateLimitMiddleware
from .services.autenticacao import LimitadorLogin
from .services.provedor import banco_responde, criar_motor_banco, servico_calculo

logger = logging.getLogger("alloy.api")

ROTAS_DOCS = ("/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json")


def create_app(settings: Optional[Settings] = None, motor_banco: Optional[Engine] = None) -> FastAPI:
    settings = settings or Settings()
    motor_banco = motor_banco if motor_banco is not None else criar_motor_banco(settings)
    docs = settings.docs_ativas

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=("API do Alloy Virtual Lab — cristalografia (células, Miller, densidade, FEA, planar, "
                     "supercélulas, soluções sólidas), temperatura, HEA, exportação CIF/XYZ e contas. "
                     "Todo resultado científico traz `procedencia` (classe, motor, versão, dados usados)."),
        docs_url=ROTAS_DOCS[0] if docs else None,
        redoc_url=ROTAS_DOCS[1] if docs else None,
        openapi_url=ROTAS_DOCS[2] if docs else None,
    )
    app.state.settings = settings
    app.state.motor_banco = motor_banco
    app.state.limitador_login = LimitadorLogin()

    # Ordem: o último adicionado é o mais externo (o ID de requisição envolve tudo).
    if settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                           allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                           allow_headers=["Content-Type", "X-Alloy-CSRF", "X-Request-ID", "If-Match"])
    app.add_middleware(RateLimitMiddleware, enabled=settings.rate_limit_ativo,
                       requests=settings.rate_limit_requests, window_seconds=settings.rate_limit_window_seconds)
    app.add_middleware(LimiteCorpoMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(CabecalhosSegurancaMiddleware, rotas_sem_csp=ROTAS_DOCS)
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)
    app.include_router(rotas.router)
    app.include_router(auth.router)
    app.include_router(rotas.alias)

    @app.get("/health", response_model=HealthResponse, tags=["plataforma"], summary="Saúde (compatível com o B e o C)")
    def health() -> dict:
        with servico_calculo(settings, motor_banco) as servico:
            return {"ok": True, "status": "healthy", "version": __version__, "data_version": servico.versao_dados()}

    @app.get("/health/live", response_model=HealthResponse, tags=["plataforma"])
    def health_live() -> dict:
        return {"ok": True, "status": "alive", "version": __version__}

    @app.get("/health/ready", response_model=HealthResponse, tags=["plataforma"])
    def health_ready(request: Request) -> dict:
        checks = {}
        banco = banco_responde(motor_banco)
        if banco is not None:
            checks["banco"] = banco
        try:
            with servico_calculo(settings, motor_banco) as servico:
                checks["dados"] = servico.quantidade_materiais() > 0
                versao_dados = servico.versao_dados()
        except Exception:  # noqa: BLE001 — readiness: falha de dados = não pronto, detalhe só no log
            logger.exception("readiness: falha ao carregar dados")
            checks["dados"], versao_dados = False, None
        pronto = all(checks.values())
        return {"ok": pronto, "status": "ready" if pronto else "degraded", "version": __version__,
                "data_version": versao_dados, "checks": checks}

    logger.info("Alloy Virtual Lab %s pronto (ambiente %s, banco %s, docs %s)", __version__, settings.env,
                "sim" if motor_banco is not None else "não (seed JSON)", "on" if docs else "off")
    return app
