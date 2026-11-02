"""Rotas legadas ``/api/*`` — CONGELADAS e marcadas como obsoletas (achados BE-01, SE-05).

A UI da v1.1 não as usa mais. Elas continuam respondendo no formato da v1.0
para não quebrar clientes externos, mas agora validam a entrada com os mesmos
schemas da v1 e devolvem os cabeçalhos ``Deprecation``, ``Sunset`` e ``Link``.
Remoção prevista quando a v1 estiver consolidada (ranking BE-3).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Response

from ..core import bootstrap, calcular_estrutura, calcular_miller, metais_publicos, tabela_estruturas
from ..core.repositorio import RepositorioMateriais
from .dependencias import get_repositorio
from .schemas import LegadoMillerRequest, LegadoStructureRequest

SUNSET = "Wed, 30 Jun 2027 23:59:59 GMT"

router = APIRouter(prefix="/api", tags=["legacy"], include_in_schema=False)


def _marcar(response: Response, sucessora: str) -> None:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = SUNSET
    response.headers["Link"] = f'<{sucessora}>; rel="successor-version"'


@router.get("/bootstrap")
def legacy_bootstrap(response: Response, repo: RepositorioMateriais = Depends(get_repositorio)):
    _marcar(response, "/")
    return bootstrap(repo)


@router.get("/metais")
def legacy_metais(response: Response, repo: RepositorioMateriais = Depends(get_repositorio)):
    _marcar(response, "/v1/crystals/metals")
    return {"ok": True, "metais": metais_publicos(repo)}


@router.get("/estruturas")
def legacy_estruturas(response: Response):
    _marcar(response, "/v1/crystals/structures")
    return {"ok": True, "estruturas": tabela_estruturas()}


@router.get("/estrutura")
def legacy_estrutura_get(response: Response, nome: Optional[str] = None, estrutura: Optional[str] = None,
                         raio: Optional[str] = None, peso: Optional[str] = None, c_a: Optional[str] = None,
                         repo: RepositorioMateriais = Depends(get_repositorio)):
    _marcar(response, "/v1/crystals/structure")
    dados = LegadoStructureRequest.model_validate(
        {"nome": nome, "estrutura": estrutura, "raio": raio, "peso": peso, "c_a": c_a})
    return {"ok": True, "result": calcular_estrutura(dados.model_dump(exclude_none=True), repo)}


@router.post("/estrutura")
def legacy_estrutura_post(response: Response, payload: Dict[str, Any] = Body(...),
                          repo: RepositorioMateriais = Depends(get_repositorio)):
    _marcar(response, "/v1/crystals/structure")
    dados = LegadoStructureRequest.model_validate(payload)
    return {"ok": True, "result": calcular_estrutura(dados.model_dump(exclude_none=True), repo)}


@router.post("/miller")
def legacy_miller_post(response: Response, payload: Dict[str, Any] = Body(...)):
    _marcar(response, "/v1/crystallography/miller")
    dados = LegadoMillerRequest.model_validate(payload)
    return {"ok": True, "result": calcular_miller(dados.model_dump(exclude_none=True))}
