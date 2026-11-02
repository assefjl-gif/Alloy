"""Configuração por ambiente (ARQUITETURA_FINAL §8). Base: ``Settings`` do CrystaLab v1.1.0.

Variáveis com prefixo ``ALLOY_`` (ou ``.env``); ``DATABASE_URL`` sem prefixo (padrão do ecossistema).
Em ``prod`` a política é imposta aqui, não no frontend (ADR-016, PI-01/02):
demonstração proibida e dados científicos não validados recusados pelos motores.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.engines.procedencia import PoliticaDados


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ALLOY_", env_file=".env", extra="ignore")

    app_name: str = "Alloy Virtual Lab"
    env: Literal["dev", "test", "prod"] = "dev"
    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    demo: Literal["permitido", "proibido"] = "permitido"
    docs: Optional[bool] = None

    cors_origins: List[str] = []
    max_body_bytes: int = 1_048_576
    rate_limit: Optional[bool] = None
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    session_secret: Optional[SecretStr] = None
    csrf_secret: Optional[SecretStr] = None
    storage_dir: str = "./var/arquivos"
    ia_enabled: bool = False

    @property
    def producao(self) -> bool:
        return self.env == "prod"

    @property
    def docs_ativas(self) -> bool:
        return self.docs if self.docs is not None else not self.producao

    @property
    def rate_limit_ativo(self) -> bool:
        return self.rate_limit if self.rate_limit is not None else self.env != "dev"

    @property
    def demo_permitido(self) -> bool:
        return self.demo == "permitido" and not self.producao

    def politica_dados(self) -> PoliticaDados:
        return PoliticaDados(permitir_nao_validado=not self.producao)

    @model_validator(mode="after")
    def _validar(self) -> Settings:
        if self.producao:
            if self.demo != "proibido":
                raise ValueError("Em produção defina ALLOY_DEMO=proibido (ADR-016).")
            if not self.database_url:
                raise ValueError("Em produção DATABASE_URL é obrigatória.")
            if self.session_secret is None or self.csrf_secret is None:
                raise ValueError("Em produção defina ALLOY_SESSION_SECRET e ALLOY_CSRF_SECRET.")
            if "*" in self.cors_origins:
                raise ValueError("CORS '*' não é permitido em produção.")
            if self.ia_enabled:
                raise ValueError("IA não pode ser ligada em produção antes da decisão registrada (RQ-EDU-05).")
        if self.max_body_bytes < 1024:
            raise ValueError("ALLOY_MAX_BODY_BYTES deve ser pelo menos 1024.")
        return self
