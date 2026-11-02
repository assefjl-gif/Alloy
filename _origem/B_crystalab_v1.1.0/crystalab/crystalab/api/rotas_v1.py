"""Rotas v1 — contrato oficial usado pela UI a partir da v1.1 (achados BE-01, BE-02, FE-02).

Handlers são ``def`` (não ``async def``): o FastAPI os executa no threadpool, de
modo que cálculos síncronos não bloqueiam o event loop.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Response

from ..core import (
    calcular_densidade,
    calcular_estrutura,
    calcular_miller,
    gerar_cif,
    gerar_xyz,
    metais_publicos,
    tabela_estruturas,
)
from ..core.repositorio import RepositorioMateriais
from .dependencias import get_repositorio
from .schemas import (
    DensityRequest,
    DensityResponse,
    ErroEnvelope,
    ExportRequest,
    ExportResponse,
    MetalInfo,
    MillerRequest,
    MillerResponse,
    OkEnvelope,
    StructureInfo,
    StructureRequest,
    StructureResponse,
)
from .seguranca import current_user

_ERROS = {400: {"model": ErroEnvelope}, 422: {"model": ErroEnvelope}, 500: {"model": ErroEnvelope}}
_CACHE_TABELAS = "public, max-age=300"

router = APIRouter(prefix="/v1", dependencies=[Depends(current_user)], responses=_ERROS)


def _ok(resultado: Any) -> Dict[str, Any]:
    return {"ok": True, "result": resultado}


@router.get("/crystals/metals", response_model=OkEnvelope[Dict[str, MetalInfo]], tags=["crystals"])
def v1_listar_metais(response: Response, repo: RepositorioMateriais = Depends(get_repositorio)):
    """Lista os metais cadastrados com suas propriedades cristalinas."""
    response.headers["Cache-Control"] = _CACHE_TABELAS
    return _ok(metais_publicos(repo))


@router.get("/crystals/structures", response_model=OkEnvelope[List[StructureInfo]], tags=["crystals"])
def v1_listar_estruturas(response: Response):
    """Tabela comparativa das estruturas cristalinas (CS, CCC, CFC, HC)."""
    response.headers["Cache-Control"] = _CACHE_TABELAS
    return _ok(tabela_estruturas())


@router.post("/crystals/structure", response_model=OkEnvelope[StructureResponse], tags=["crystals"],
             summary="Calcula a célula unitária completa")
def v1_calcular_celula(payload: StructureRequest, repo: RepositorioMateriais = Depends(get_repositorio)):
    """Parâmetro de rede, densidade teórica, posições atômicas (desenho e base) e passo a passo."""
    return _ok(calcular_estrutura(payload.model_dump(exclude_none=True), repo))


@router.post("/crystallography/miller", response_model=OkEnvelope[MillerResponse], tags=["crystallography"],
             summary="Calcula planos (hkl)/(hkil) e direções [uvw]/[uvtw]")
def v1_miller(payload: MillerRequest):
    """Polígono de corte, normal, área, espaçamento, átomos contidos e avisos (ordem n)."""
    return _ok(calcular_miller(payload.model_dump(exclude_none=True)))


@router.post("/calculations/density", response_model=OkEnvelope[DensityResponse], tags=["calculations"],
             summary="Densidade teórica passo a passo + FEA")
def v1_densidade(payload: DensityRequest, repo: RepositorioMateriais = Depends(get_repositorio)):
    return _ok(calcular_densidade(payload.model_dump(exclude_none=True), repo))


@router.post("/export/cif", response_model=OkEnvelope[ExportResponse], tags=["interoperability"],
             summary="Gera CIF (Å, grupo espacial, Wyckoff, base sem réplicas)")
def v1_exportar_cif(payload: ExportRequest, repo: RepositorioMateriais = Depends(get_repositorio)):
    return _ok(gerar_cif(payload.model_dump(exclude_none=True), repo))


@router.post("/export/xyz", response_model=OkEnvelope[ExportResponse], tags=["interoperability"],
             summary="Gera XYZ estendido (base em Å + vetores de rede)")
def v1_exportar_xyz(payload: ExportRequest, repo: RepositorioMateriais = Depends(get_repositorio)):
    return _ok(gerar_xyz(payload.model_dump(exclude_none=True), repo))
