"""Configurações por ambiente (achados BE-10, BE-12, SE-06).

Variáveis de ambiente com prefixo ``CRYSTALAB_`` (ou arquivo ``.env``):

=============================  ===========================================  ==================
Variável                       Efeito                                       Padrão
=============================  ===========================================  ==================
CRYSTALAB_ENVIRONMENT          ``development`` ou ``production``            development
CRYSTALAB_DOCS_ENABLED         expõe /docs, /redoc, /openapi.json           (dev: sim; prod: não)
CRYSTALAB_CORS_ORIGINS         lista JSON de origens permitidas             [] (só mesma origem)
CRYSTALAB_MAX_BODY_BYTES       limite do corpo da requisição (HTTP 413)     1048576
CRYSTALAB_RATE_LIMIT_ENABLED   limite simples por IP (em memória)           false
CRYSTALAB_JWT_ENABLED          autenticação JWT — ainda NÃO implementada    false
=============================  ===========================================  ==================
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .. import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CRYSTALAB_", env_file=".env", extra="ignore")

    app_name: str = "CrystaLab: Fundamentos Estruturais"
    environment: Literal["development", "production"] = "development"
    docs_enabled: Optional[bool] = None

    cors_origins: List[str] = []
    cors_allow_credentials: bool = False
    cors_allow_methods: List[str] = ["GET", "POST"]
    cors_allow_headers: List[str] = ["Content-Type", "Authorization"]

    max_body_bytes: int = 1_048_576

    rate_limit_enabled: bool = False
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    rate_limit_max_clients: int = 10_000

    jwt_enabled: bool = False
    jwt_secret: Optional[SecretStr] = None
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    @property
    def version(self) -> str:
        return __version__

    @property
    def docs_ativas(self) -> bool:
        if self.docs_enabled is not None:
            return self.docs_enabled
        return self.environment == "development"

    @model_validator(mode="after")
    def _validar(self) -> Settings:
        if self.jwt_enabled:
            # BE-10: antes, ligar a flag fazia TODAS as rotas /v1 responderem 401/501.
            # Agora a aplicação se recusa a iniciar, com mensagem clara.
            raise ValueError(
                "CRYSTALAB_JWT_ENABLED=true, mas a validação JWT ainda não foi implementada nesta versão. "
                "Mantenha a flag desligada até a etapa de autenticação (ranking BE-4).")
        if self.environment == "production" and "*" in self.cors_origins:
            raise ValueError("CORS '*' não é permitido em produção: liste as origens em CRYSTALAB_CORS_ORIGINS.")
        if self.max_body_bytes < 1024:
            raise ValueError("CRYSTALAB_MAX_BODY_BYTES deve ser pelo menos 1024.")
        return self
