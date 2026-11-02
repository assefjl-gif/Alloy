"""Entrega da interface: index.html com bootstrap embutido + arquivos estáticos (FE-01, SE-01, SE-03).

O front-end deixou de ser uma string Python: vive em ``crystalab/web/`` e é
servido como arquivo. O HTML é montado UMA vez na criação da aplicação (BE-03).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..core import bootstrap
from ..core.repositorio import RepositorioMateriais
from .seguranca import json_para_script

DIRETORIO_WEB = Path(__file__).resolve().parent.parent / "web"
DIRETORIO_ESTATICO = DIRETORIO_WEB / "static"

router = APIRouter(include_in_schema=False)


def montar_index(repo: RepositorioMateriais) -> str:
    modelo = (DIRETORIO_WEB / "index.html").read_text(encoding="utf-8")
    return (modelo
            .replace("__CRYSTALAB_VERSAO__", __version__)
            .replace("__BOOTSTRAP_JSON__", json_para_script(bootstrap(repo))))


def arquivos_estaticos() -> StaticFiles:
    return StaticFiles(directory=str(DIRETORIO_ESTATICO))


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    html = request.app.state.index_html
    return HTMLResponse(content=html, headers={"Cache-Control": "no-cache"})
