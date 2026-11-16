"""Tratamento de erros padronizado (origem: CrystaLab v1.1.0 ``api/erros.py``; API.md §1.4).

Mudanças na consolidação: todo erro traz ``request_id``; ``correlation_id`` (erro 500) passa a ser o
próprio ``request_id``; ``ErroDominio`` usa o status HTTP de ``STATUS_POR_CODIGO`` (padrão 400).

Texto original:

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
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_id import request_id_de
from app.engines.crystallography.erros import ErroDominio
from app.services.erros import STATUS_HTTP as STATUS_SERVICOS

logger = logging.getLogger("alloy.api")

#: Erros de domínio cujo status não é 400 (API.md §1.4).
STATUS_POR_CODIGO = {"DADO_NAO_VALIDADO": 422, **STATUS_SERVICOS}

_CODIGOS_HTTP = {
    400: "REQUISICAO_INVALIDA", 401: "NAO_AUTENTICADO", 403: "PROIBIDO", 404: "NAO_ENCONTRADO",
    405: "METODO_NAO_PERMITIDO", 409: "CONFLITO", 413: "CORPO_GRANDE_DEMAIS", 415: "TIPO_NAO_SUPORTADO",
    422: "VALIDACAO", 429: "LIMITE_DE_REQUISICOES", 500: "ERRO_INTERNO",
}


def envelope_erro(mensagem: str, codigo: str, status_code: int, *,
                  request_id: Optional[str] = None,
                  correlation_id: Optional[str] = None,
                  details: Optional[List[Dict[str, Any]]] = None,
                  headers: Optional[Dict[str, str]] = None) -> JSONResponse:
    corpo: Dict[str, Any] = {"ok": False, "error": mensagem, "code": codigo, "status": status_code}
    if request_id:
        corpo["request_id"] = request_id
    if correlation_id:
        corpo["correlation_id"] = correlation_id
    if details:
        corpo["details"] = details
    return JSONResponse(status_code=status_code, content=corpo, headers=headers)


#: Campos com ``pattern`` no esquema: mensagem de usuário, SEM expor a expressão regular (QA-R2-03).
_FORMATO_POR_CAMPO = {
    "email": "informe um e-mail válido, no formato nome@dominio.com",
    "ref": "use o símbolo do elemento (ex.: Fe) ou o número atômico (ex.: 26)",
}
#: Mensagem de formato quando o campo não está no mapa acima.
_FORMATO_GENERICO = "não está no formato esperado para este campo"


def _campo(erro: Dict[str, Any]) -> str:
    """Último segmento textual de ``loc`` (nome do campo), ou ``""``."""
    for parte in reversed(list(erro.get("loc") or ())):
        if isinstance(parte, str) and parte not in ("body", "query", "path", "header", "cookie"):
            return parte
    return ""


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
        "bool_parsing": "deve ser verdadeiro ou falso",
        "bool_type": "deve ser verdadeiro ou falso",
        "uuid_parsing": "deve ser um identificador (UUID) válido",
        "uuid_type": "deve ser um identificador (UUID) válido",
        "datetime_parsing": "deve ser uma data e hora no formato ISO 8601",
        "datetime_type": "deve ser uma data e hora no formato ISO 8601",
        "date_parsing": "deve ser uma data no formato AAAA-MM-DD",
        "date_type": "deve ser uma data no formato AAAA-MM-DD",
    }
    if tipo in traducoes:
        return traducoes[tipo]
    if tipo == "string_pattern_mismatch":
        # NUNCA ecoar ``ctx['pattern']`` (expressão regular interna) ao usuário — QA-R2-03.
        return _FORMATO_POR_CAMPO.get(_campo(erro), _FORMATO_GENERICO)
    if tipo == "string_too_short":
        minimo = ctx.get("min_length")
        return (f"deve ter pelo menos {minimo} caracteres" if minimo != 1
                else "não pode ficar em branco")
    if tipo == "greater_than_equal":
        return f"deve ser ≥ {ctx.get('ge')}"
    if tipo == "less_than_equal":
        return f"deve ser ≤ {ctx.get('le')}"
    if tipo == "greater_than":
        return f"deve ser > {ctx.get('gt')}"
    if tipo == "less_than":
        return f"deve ser < {ctx.get('lt')}"
    if tipo == "literal_error":
        # O validador escreve a lista em inglês ("'a', 'b' or 'c'"); a mensagem do contrato é só com vírgulas.
        return f"deve ser um de: {str(ctx.get('expected')).replace(' or ', ', ')}"
    if tipo == "too_short":
        return f"deve ter pelo menos {ctx.get('min_length')} itens"
    if tipo == "too_long":
        return f"deve ter no máximo {ctx.get('max_length')} itens"
    if tipo == "string_too_long":
        return f"deve ter no máximo {ctx.get('max_length')} caracteres"
    mensagem = str(erro.get("msg", "valor inválido"))
    padrao = ctx.get("pattern")
    if padrao and str(padrao) in mensagem:
        # Rede de proteção: nenhum tipo novo do validador pode vazar a expressão regular (QA-R2-03).
        return _FORMATO_POR_CAMPO.get(_campo(erro), _FORMATO_GENERICO)
    return mensagem.removeprefix("Value error, ")


def _loc(partes: Sequence[Any]) -> List[Any]:
    """Contrato R1 §4.2: índice de lista é inteiro (``["solutos", 0, "x"]``); nome de campo é texto."""
    return [p if isinstance(p, int) else str(p) for p in partes if p != "body"]


#: Campos do contrato que são LISTA: o segmento seguinte em ``loc`` é índice, portanto inteiro (§4.2).
_LISTAS_DO_CONTRATO = ("solutos",)


def _loc_dominio(partes: Sequence[Any]) -> List[Any]:
    """Normaliza o ``loc`` dos erros de domínio: índice de lista como inteiro, chave de objeto como texto.

    Só converte o segmento que vem depois de um campo-lista conhecido do contrato, para não transformar
    em número a chave de um objeto (ex.: ``["composicao", "0"]``, onde "0" é a chave enviada pelo usuário).
    """
    saida: List[Any] = []
    anterior: Any = None
    for parte in partes:
        if isinstance(parte, str) and parte.isdigit() and anterior in _LISTAS_DO_CONTRATO:
            saida.append(int(parte))
        else:
            saida.append(parte if isinstance(parte, int) else str(parte))
        anterior = parte
    return saida


def _detalhes_dominio(detalhes: Any) -> Optional[List[Dict[str, Any]]]:
    if not (isinstance(detalhes, (list, tuple)) and detalhes):
        return None
    saida: List[Dict[str, Any]] = []
    for item in detalhes:
        if isinstance(item, dict) and "loc" in item:
            saida.append({**item, "loc": _loc_dominio(item.get("loc") or ())})
        else:
            saida.append(item)
    return saida


def resumo_validacao(erros: Sequence[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    """Mensagem curta (1º erro) + lista serializável (sem objetos de exceção em ``ctx``)."""
    detalhes = [
        {"loc": _loc(e.get("loc", ())), "msg": _texto_erro(e), "type": e.get("type")}
        for e in erros
    ]
    if not detalhes:
        return "Payload inválido.", []
    primeiro = detalhes[0]
    if primeiro["type"] == "json_invalid":
        return "JSON inválido no corpo da requisição.", detalhes
    local = ".".join(str(p) for p in primeiro["loc"]) or "payload"
    return f"Validação falhou em '{local}': {primeiro['msg']}", detalhes


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ErroDominio)
    async def _dominio(request: Request, exc: ErroDominio) -> JSONResponse:
        # Contrato R1 §4: o erro de domínio que carrega ``detalhes`` (subtipo estável em ``type``) os repassa
        # em ``details``, no mesmo formato do 422 de esquema. Erros sem a lista continuam como antes.
        detalhes = _detalhes_dominio(getattr(exc, "detalhes", None))
        return envelope_erro(str(exc), exc.codigo, STATUS_POR_CODIGO.get(exc.codigo, status.HTTP_400_BAD_REQUEST),
                             request_id=request_id_de(request), details=detalhes)

    @app.exception_handler(RequestValidationError)
    async def _validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
        mensagem, detalhes = resumo_validacao(exc.errors())
        return envelope_erro(mensagem, "VALIDACAO", 422, details=detalhes, request_id=request_id_de(request))

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        mensagem = exc.detail if isinstance(exc.detail, str) else "Erro HTTP."
        if exc.status_code == 404 and mensagem == "Not Found":
            mensagem = "Rota não encontrada."
        if exc.status_code == 405 and mensagem == "Method Not Allowed":
            mensagem = "Método não permitido nesta rota."
        codigo = _CODIGOS_HTTP.get(exc.status_code, f"HTTP_{exc.status_code}")
        return envelope_erro(mensagem, codigo, exc.status_code, headers=getattr(exc, "headers", None),
                             request_id=request_id_de(request))

    @app.exception_handler(Exception)
    async def _generico(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = request_id_de(request) or uuid.uuid4().hex
        # BE-05: o detalhe vai SOMENTE para o log; o cliente recebe mensagem genérica.
        logger.exception("erro interno [%s] em %s %s", correlation_id, request.method, request.url.path)
        return envelope_erro("Erro interno. Informe o código de correlação ao suporte.",
                             "ERRO_INTERNO", status.HTTP_500_INTERNAL_SERVER_ERROR,
                             request_id=correlation_id, correlation_id=correlation_id)
