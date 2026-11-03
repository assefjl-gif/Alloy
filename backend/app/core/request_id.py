"""Identificador de correlação por requisição (ARQUITETURA_FINAL §9, RQ-API-04).

Aceita ``X-Request-ID`` do cliente (se for curto e seguro), senão gera um. O valor fica em
``scope["state"]["request_id"]`` (lido pelos handlers de erro) e volta na resposta.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Awaitable, Callable, Dict

Scope = Dict[str, Any]
Message = Dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

CABECALHO = b"x-request-id"
_SEGURO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        recebido = next((v.decode("latin-1") for k, v in scope.get("headers", []) if k == CABECALHO), "")
        request_id = recebido if _SEGURO.match(recebido) else uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def enviar(msg: Message) -> None:
            if msg["type"] == "http.response.start":
                cabecalhos = [(k, v) for k, v in msg.get("headers", []) if k.lower() != CABECALHO]
                cabecalhos.append((CABECALHO, request_id.encode("latin-1")))
                msg = {**msg, "headers": cabecalhos}
            await send(msg)

        await self.app(scope, receive, enviar)


def request_id_de(scope_ou_request: Any) -> str | None:
    estado = getattr(scope_ou_request, "scope", scope_ou_request).get("state") or {}
    return estado.get("request_id")
