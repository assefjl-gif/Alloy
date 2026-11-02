"""Tratamento de erros padronizado (achados BE-04, BE-05, BE-06).

Todas as respostas de erro têm o mesmo envelope, compatível com a UI da v1.0
(``ok`` + ``error``) e já com os campos que permitem migrar para RFC 9457:

    {"ok": false, "error": "...", "code": "ENTRADA_INVALIDA", "status": 400,
     "correlation_id": "...", "details": [...]}
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Sequence

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.erros import ErroDominio

logger = logging.getLogger("crystalab.api")

_CODIGOS_HTTP = {
    400: "REQUISICAO_INVALIDA", 401: "NAO_AUTENTICADO", 403: "PROIBIDO", 404: "NAO_ENCONTRADO",
    405: "METODO_NAO_PERMITIDO", 413: "CORPO_GRANDE_DEMAIS", 415: "TIPO_NAO_SUPORTADO",
    422: "VALIDACAO", 429: "LIMITE_DE_REQUISICOES", 500: "ERRO_INTERNO",
}


def envelope_erro(mensagem: str, codigo: str, status_code: int, *,
                  correlation_id: Optional[str] = None,
                  details: Optional[List[Dict[str, Any]]] = None,
                  headers: Optional[Dict[str, str]] = None) -> JSONResponse:
    corpo: Dict[str, Any] = {"ok": False, "error": mensagem, "code": codigo, "status": status_code}
    if correlation_id:
        corpo["correlation_id"] = correlation_id
    if details:
        corpo["details"] = details
    return JSONResponse(status_code=status_code, content=corpo, headers=headers)


def _texto_erro(erro: Dict[str, Any]) -> str:
    tipo = erro.get("type", "")
    ctx = erro.get("ctx") or {}
    traducoes = {
        "missing": "campo obrigatório",
        "extra_forbidden": "campo não reconhecido",
        "float_parsing": "deve ser um número",
        "float_type": "deve ser um número",
        "int_parsing": "deve ser um número inteiro",
        "int_type": "deve ser um número inteiro",
        "int_from_float": "deve ser um número inteiro",
        "finite_number": "deve ser um número finito",
        "string_type": "deve ser texto",
        "list_type": "deve ser uma lista, ex.: [1, 1, 1]",
        "json_invalid": "JSON inválido",
        "model_attributes_type": "o corpo deve ser um objeto JSON",
        "dict_type": "o corpo deve ser um objeto JSON",
    }
    if tipo in traducoes:
        return traducoes[tipo]
    if tipo == "greater_than_equal":
        return f"deve ser ≥ {ctx.get('ge')}"
    if tipo == "less_than_equal":
        return f"deve ser ≤ {ctx.get('le')}"
    if tipo == "literal_error":
        return f"deve ser um de: {ctx.get('expected')}"
    if tipo == "too_short":
        return f"deve ter pelo menos {ctx.get('min_length')} itens"
    if tipo == "too_long":
        return f"deve ter no máximo {ctx.get('max_length')} itens"
    if tipo == "string_too_long":
        return f"deve ter no máximo {ctx.get('max_length')} caracteres"
    mensagem = str(erro.get("msg", "valor inválido"))
    return mensagem.removeprefix("Value error, ")


def resumo_validacao(erros: Sequence[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    """Mensagem curta (1º erro) + lista serializável (sem objetos de exceção em ``ctx``)."""
    detalhes = [
        {"loc": [str(p) for p in e.get("loc", ()) if p != "body"], "msg": _texto_erro(e), "type": e.get("type")}
        for e in erros
    ]
    if not detalhes:
        return "Payload inválido.", []
    primeiro = detalhes[0]
    if primeiro["type"] == "json_invalid":
        return "JSON inválido no corpo da requisição.", detalhes
    local = ".".join(primeiro["loc"]) or "payload"
    return f"Validação falhou em '{local}': {primeiro['msg']}", detalhes


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ErroDominio)
    async def _dominio(_: Request, exc: ErroDominio) -> JSONResponse:
        return envelope_erro(str(exc), exc.codigo, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
        mensagem, detalhes = resumo_validacao(exc.errors())
        return envelope_erro(mensagem, "VALIDACAO", 422, details=detalhes)

    @app.exception_handler(ValidationError)
    async def _validacao_interna(_: Request, exc: ValidationError) -> JSONResponse:
        # Usado pelas rotas legadas, que validam o corpo manualmente (status 400 como na v1.0).
        mensagem, detalhes = resumo_validacao(exc.errors())
        return envelope_erro(mensagem, "VALIDACAO", status.HTTP_400_BAD_REQUEST, details=detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        mensagem = exc.detail if isinstance(exc.detail, str) else "Erro HTTP."
        if exc.status_code == 404 and mensagem == "Not Found":
            mensagem = "Rota não encontrada."
        if exc.status_code == 405 and mensagem == "Method Not Allowed":
            mensagem = "Método não permitido nesta rota."
        codigo = _CODIGOS_HTTP.get(exc.status_code, f"HTTP_{exc.status_code}")
        return envelope_erro(mensagem, codigo, exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(Exception)
    async def _generico(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = uuid.uuid4().hex[:12]
        # BE-05: o detalhe vai SOMENTE para o log; o cliente recebe mensagem genérica.
        logger.exception("erro interno [%s] em %s %s", correlation_id, request.method, request.url.path)
        return envelope_erro("Erro interno. Informe o código de correlação ao suporte.",
                             "ERRO_INTERNO", status.HTTP_500_INTERNAL_SERVER_ERROR,
                             correlation_id=correlation_id)
