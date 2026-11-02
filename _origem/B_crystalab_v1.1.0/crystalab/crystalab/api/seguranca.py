"""Segurança de base (achados BE-09, BE-10, BE-15, SE-03, SE-04).

Middlewares ASGI puros (sem ``BaseHTTPMiddleware``, que tem limitações com
streaming e tarefas em segundo plano).
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict, deque
from typing import Any, Awaitable, Callable, Deque, Dict, Iterable, Optional, Tuple

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

Scope = Dict[str, Any]
Message = Dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_bearer = HTTPBearer(auto_error=False)


async def current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Dict[str, Any]:
    """Usuário atual. Hoje sempre anônimo.

    Ponto único de extensão para a autenticação futura (ranking BE-4): a
    implementação JWT/OIDC substitui esta função sem tocar nas rotas.
    Ligar ``CRYSTALAB_JWT_ENABLED`` impede a inicialização (ver ``config.py``).
    """
    return {"sub": "anonymous", "role": "public"}


async def _responder_json(send: Send, status: int, corpo: Dict[str, Any],
                          extras: Iterable[Tuple[bytes, bytes]] = ()) -> None:
    dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
    await send({
        "type": "http.response.start", "status": status,
        "headers": [(b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(dados)).encode()), *extras],
    })
    await send({"type": "http.response.body", "body": dados})


def _erro(mensagem: str, codigo: str, status: int) -> Dict[str, Any]:
    return {"ok": False, "error": mensagem, "code": codigo, "status": status}


class _CorpoGrandeDemais(HTTPException):
    """Subclasse de HTTPException: o FastAPI a repassa intacta ao ler o corpo (vira 413, não 400)."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(status_code=413, detail=mensagem)


class LimiteCorpoMiddleware:
    """Rejeita corpos maiores que ``max_bytes`` com HTTP 413 (com ou sem Content-Length)."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        mensagem = f"Corpo da requisição maior que o limite de {self.max_bytes} bytes."
        for nome, valor in scope.get("headers", []):
            if nome == b"content-length":
                try:
                    tamanho = int(valor)
                except ValueError:
                    await _responder_json(send, 400, _erro("Cabeçalho Content-Length inválido.",
                                                           "REQUISICAO_INVALIDA", 400))
                    return
                if tamanho > self.max_bytes:
                    await _responder_json(send, 413, _erro(mensagem, "CORPO_GRANDE_DEMAIS", 413))
                    return

        recebido = 0
        resposta_iniciada = False

        async def receive_limitado() -> Message:
            nonlocal recebido
            msg = await receive()
            if msg["type"] == "http.request":
                recebido += len(msg.get("body", b""))
                if recebido > self.max_bytes:
                    raise _CorpoGrandeDemais(mensagem)
            return msg

        async def send_rastreado(msg: Message) -> None:
            nonlocal resposta_iniciada
            if msg["type"] == "http.response.start":
                resposta_iniciada = True
            await send(msg)

        try:
            await self.app(scope, receive_limitado, send_rastreado)
        except _CorpoGrandeDemais:
            if not resposta_iniciada:
                await _responder_json(send, 413, _erro(mensagem, "CORPO_GRANDE_DEMAIS", 413))


CSP_PADRAO = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; "
              "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; "
              "form-action 'self'; frame-ancestors 'none'")


class CabecalhosSegurancaMiddleware:
    """Adiciona cabeçalhos de segurança; a CSP estrita vale para tudo exceto /docs e /redoc."""

    def __init__(self, app: ASGIApp, rotas_sem_csp: Iterable[str] = ()) -> None:
        self.app = app
        self.rotas_sem_csp = tuple(rotas_sem_csp)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        caminho = scope.get("path", "")
        aplicar_csp = not any(caminho == r or caminho.startswith(r + "/") for r in self.rotas_sem_csp)

        async def send_com_cabecalhos(msg: Message) -> None:
            if msg["type"] == "http.response.start":
                cabecalhos = list(msg.get("headers", []))
                existentes = {nome.lower() for nome, _ in cabecalhos}
                novos = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                    (b"x-frame-options", b"DENY"),
                    (b"cross-origin-opener-policy", b"same-origin"),
                ]
                if aplicar_csp:
                    novos.append((b"content-security-policy", CSP_PADRAO.encode()))
                cabecalhos.extend(item for item in novos if item[0] not in existentes)
                msg = {**msg, "headers": cabecalhos}
            await send(msg)

        await self.app(scope, receive, send_com_cabecalhos)


class RateLimitMiddleware:
    """Limite simples por IP em memória (desligado por padrão).

    Corrige o crescimento sem limite da v1.0 (BE-09): baldes vazios são
    removidos e o número de clientes rastreados é limitado (LRU). Atrás de proxy,
    rode o uvicorn com ``--proxy-headers --forwarded-allow-ips=<ip do proxy>``
    para que o IP real seja usado. Em produção, prefira limitar no proxy reverso.
    """

    def __init__(self, app: ASGIApp, *, enabled: bool, requests: int, window_seconds: int,
                 max_clients: int = 10_000) -> None:
        self.app = app
        self.enabled = enabled
        self.requests = requests
        self.window = window_seconds
        self.max_clients = max_clients
        self._buckets: OrderedDict[str, Deque[float]] = OrderedDict()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self.enabled or scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        cliente = (scope.get("client") or ("desconhecido", 0))[0]
        agora = time.monotonic()
        balde = self._buckets.pop(cliente, None) or deque()
        while balde and agora - balde[0] > self.window:
            balde.popleft()
        if len(balde) >= self.requests:
            self._buckets[cliente] = balde
            await _responder_json(send, 429, _erro("Limite de requisições excedido.",
                                                   "LIMITE_DE_REQUISICOES", 429),
                                  extras=[(b"retry-after", str(self.window).encode())])
            return
        balde.append(agora)
        self._buckets[cliente] = balde
        while len(self._buckets) > self.max_clients:
            self._buckets.popitem(last=False)
        await self.app(scope, receive, send)


def json_para_script(dados: Any) -> str:
    """Serializa JSON para dentro de <script type="application/json"> sem quebrar a página (SE-03)."""
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    return (texto.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
