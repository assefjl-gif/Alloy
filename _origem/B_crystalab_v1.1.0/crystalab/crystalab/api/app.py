"""Fábrica da aplicação FastAPI do CrystaLab (achados BE-08, BE-11, BE-12, BE-14).

Uso direto:          uvicorn crystalab.api.app:create_app --factory
Dentro do Alloy:     plataforma.mount("/crystalab", create_app())   (ver crystalab/modulo.py)
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .. import __version__
from ..core.repositorio import RepositorioMateriais, repositorio_padrao
from . import rotas_legado, rotas_v1, web
from .config import Settings
from .erros import register_exception_handlers
from .schemas import HealthResponse
from .seguranca import CabecalhosSegurancaMiddleware, LimiteCorpoMiddleware, RateLimitMiddleware

logger = logging.getLogger("crystalab.api")

ROTAS_DOCS = ("/docs", "/redoc", "/openapi.json")


def create_app(settings: Optional[Settings] = None,
               repositorio: Optional[RepositorioMateriais] = None) -> FastAPI:
    settings = settings or Settings()
    repositorio = repositorio or repositorio_padrao()
    docs = settings.docs_ativas

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=("API educacional de Ciência dos Materiais — células unitárias CS/CCC/CFC/HC, "
                     "índices de Miller, densidade teórica, FEA e exportação CIF/XYZ. "
                     "Módulo 1 do laboratório didático Alloy."),
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings
    app.state.repositorio = repositorio
    app.state.index_html = web.montar_index(repositorio)

    # Ordem: o último adicionado é o mais externo.
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        )
    app.add_middleware(RateLimitMiddleware, enabled=settings.rate_limit_enabled,
                       requests=settings.rate_limit_requests,
                       window_seconds=settings.rate_limit_window_seconds,
                       max_clients=settings.rate_limit_max_clients)
    app.add_middleware(LimiteCorpoMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(CabecalhosSegurancaMiddleware, rotas_sem_csp=ROTAS_DOCS)

    register_exception_handlers(app)

    app.include_router(rotas_v1.router)
    app.include_router(rotas_legado.router)
    app.include_router(web.router)
    app.mount("/static", web.arquivos_estaticos(), name="static")

    @app.get("/health", response_model=HealthResponse, tags=["meta"], summary="Healthcheck (compatível v1.0)")
    def health() -> dict:
        return {"ok": True, "status": "healthy", "version": __version__,
                "data_version": repositorio.versao_dados}

    @app.get("/health/live", response_model=HealthResponse, tags=["meta"], summary="Liveness")
    def health_live() -> dict:
        return {"ok": True, "status": "alive", "version": __version__}

    @app.get("/health/ready", response_model=HealthResponse, tags=["meta"], summary="Readiness")
    def health_ready(request: Request) -> dict:
        checks = {
            "dados": len(request.app.state.repositorio.listar()) > 0,
            "interface": (web.DIRETORIO_ESTATICO / "js" / "main.js").is_file(),
            "three_js_local": (web.DIRETORIO_ESTATICO / "vendor" / "three" / "three.min.js").is_file(),
        }
        pronto = all(checks.values())
        return {"ok": pronto, "status": "ready" if pronto else "degraded", "version": __version__,
                "data_version": request.app.state.repositorio.versao_dados, "checks": checks}

    logger.info("CrystaLab %s pronto (dados %s, ambiente %s, docs %s)",
                __version__, repositorio.versao_dados, settings.environment, "on" if docs else "off")
    return app
