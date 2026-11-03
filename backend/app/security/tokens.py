"""Tokens opacos de sessão e anti-CSRF (ADR-008). O banco guarda só o SHA-256 de cada um."""

from __future__ import annotations

import hashlib
import hmac
import secrets

COOKIE_SESSAO = "alloy_sessao"
CABECALHO_CSRF = "X-Alloy-CSRF"
BYTES_TOKEN = 32  # 256 bits


def novo_token() -> str:
    return secrets.token_urlsafe(BYTES_TOKEN)


def sha256(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def confere(token: str, hash_armazenado: bytes) -> bool:
    return hmac.compare_digest(sha256(token), hash_armazenado)
