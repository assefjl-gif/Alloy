"""Erros dos serviços de plataforma (identidade, educação). Mapeados para HTTP em api/erros.py."""

from __future__ import annotations

from app.engines.crystallography.erros import ErroDominio


class NaoAutenticado(ErroDominio):
    codigo = "NAO_AUTENTICADO"


class CsrfInvalido(ErroDominio):
    codigo = "CSRF_INVALIDO"


class Proibido(ErroDominio):
    codigo = "PROIBIDO"


class NaoEncontrado(ErroDominio):
    codigo = "NAO_ENCONTRADO"


class Conflito(ErroDominio):
    codigo = "CONFLITO"


class MuitasTentativas(ErroDominio):
    codigo = "MUITAS_TENTATIVAS"


class CapacidadeIndisponivel(ErroDominio):
    codigo = "CAPACIDADE_INDISPONIVEL"


STATUS_HTTP = {
    "NAO_AUTENTICADO": 401, "CSRF_INVALIDO": 403, "PROIBIDO": 403, "NAO_ENCONTRADO": 404,
    "CONFLITO": 409, "MUITAS_TENTATIVAS": 429, "CAPACIDADE_INDISPONIVEL": 503,
}
