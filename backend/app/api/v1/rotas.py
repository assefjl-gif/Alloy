"""Rotas /api/v1 (API.md §2) e aliases /v1 depreciados (API.md §3).

Os aliases chamam os MESMOS handlers: não existe segunda implementação. Handlers são ``def``
(threadpool), como no B: os cálculos são síncronos e curtos (< 1,1 ms medidos).
Autenticação ainda não existe (Fase 8): todos os cálculos são anônimos e não gravam histórico.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request, Response

from app import __version__
from app.core.config import Settings
from app.services.calculo import ServicoCalculo, versoes_motores

from ..dependencias import get_servico, get_settings
from ..erros import envelope_erro
from .schemas import (
    Capabilities,
    DensityRequest,
    DensityResponse,
    ErroEnvelope,
    ExportRequest,
    ExportResponse,
    MetalInfo,
    MillerRequest,
    MillerResponse,
    OkEnvelope,
    ServicoCapacidade,
    SolidSolutionRequest,
    SolidSolutionResponse,
    StructureInfo,
    StructureRequest,
    StructureResponse,
    SupercellRequest,
    SupercellResponse,
    ThermalRequest,
    ThermalResponse,
    VersionInfo,
)

_ERROS = {400: {"model": ErroEnvelope}, 422: {"model": ErroEnvelope}, 500: {"model": ErroEnvelope}}
_CACHE_TABELAS = "public, max-age=300"

router = APIRouter(prefix="/api/v1", responses=_ERROS)


def _ok(resultado: Any) -> Dict[str, Any]:
    return {"ok": True, "result": resultado}


def _payload(modelo: Any) -> Dict[str, Any]:
    return modelo.model_dump(exclude_none=True)


# --------------------------------------------------------------------------- cristalografia
@router.get("/crystallography/metals", response_model=OkEnvelope[Dict[str, MetalInfo]], tags=["cristalografia"])
def listar_metais(response: Response, servico: ServicoCalculo = Depends(get_servico)):
    """Metais cadastrados com propriedades cristalinas."""
    response.headers["Cache-Control"] = _CACHE_TABELAS
    return _ok(servico.metais())


@router.get("/crystallography/structures", response_model=OkEnvelope[List[StructureInfo]], tags=["cristalografia"])
def listar_estruturas(response: Response):
    """Tabela comparativa CS, CCC, CFC e HC."""
    response.headers["Cache-Control"] = _CACHE_TABELAS
    return _ok(ServicoCalculo.estruturas())


@router.post("/crystallography/cells", response_model=OkEnvelope[StructureResponse], tags=["cristalografia"],
             summary="Calcula a célula unitária completa")
def calcular_celula(payload: StructureRequest, servico: ServicoCalculo = Depends(get_servico)):
    """Rede (medida, derivada ou informada), FEA, densidade, átomos, base, passos e procedência."""
    return _ok(servico.celula(_payload(payload)))


@router.post("/crystallography/density", response_model=OkEnvelope[DensityResponse], tags=["cristalografia"],
             summary="Densidade teórica passo a passo + FEA")
def calcular_densidade(payload: DensityRequest, servico: ServicoCalculo = Depends(get_servico)):
    return _ok(servico.densidade(_payload(payload)))


@router.post("/crystallography/miller", response_model=OkEnvelope[MillerResponse], tags=["cristalografia"],
             summary="Planos (hkl)/(hkil) e direções [uvw]/[uvtw]")
def calcular_miller(payload: MillerRequest, servico: ServicoCalculo = Depends(get_servico)):
    """Polígono, normal, área, espaçamento, densidade planar validada e família em supercélula."""
    return _ok(servico.miller(_payload(payload)))


@router.post("/crystallography/supercells", response_model=OkEnvelope[SupercellResponse], tags=["cristalografia"],
             summary="Supercélula n×n×n")
def calcular_supercelula(payload: SupercellRequest, servico: ServicoCalculo = Depends(get_servico)):
    return _ok(servico.supercelula(_payload(payload)))


@router.post("/crystallography/solid-solutions", response_model=OkEnvelope[SolidSolutionResponse],
             tags=["cristalografia"], summary="Solução sólida substitucional ou intersticial")
def calcular_solucao_solida(payload: SolidSolutionRequest, servico: ServicoCalculo = Depends(get_servico)):
    """Vegard, % em peso, Hume-Rothery e supercélula com o soluto (estimativa de modelo)."""
    return _ok(servico.solucao_solida(_payload(payload)))


@router.post("/thermodynamics/thermal", response_model=OkEnvelope[ThermalResponse], tags=["termodinamica"],
             summary="Dilatação, vibração (Lindemann) e alotropia")
def calcular_termico(payload: ThermalRequest, servico: ServicoCalculo = Depends(get_servico)):
    return _ok(servico.termico(_payload(payload)))


# --------------------------------------------------------------------------- exportação
@router.post("/exports/cif", response_model=OkEnvelope[ExportResponse], tags=["exportacao"],
             summary="CIF (Å, grupo espacial, Wyckoff)")
def exportar_cif(payload: ExportRequest, servico: ServicoCalculo = Depends(get_servico)):
    return _ok(servico.exportar("cif", _payload(payload)))


@router.post("/exports/xyz", response_model=OkEnvelope[ExportResponse], tags=["exportacao"],
             summary="XYZ estendido (base em Å + vetores de rede)")
def exportar_xyz(payload: ExportRequest, servico: ServicoCalculo = Depends(get_servico)):
    return _ok(servico.exportar("xyz", _payload(payload)))


# --------------------------------------------------------------------------- HEA (ADR-013)
@router.get("/hea/{caminho:path}", tags=["hea"], responses={503: {"model": ErroEnvelope}},
            operation_id="hea_indisponivel_get", summary="Motor HEA (indisponível até Q-01)")
@router.post("/hea/{caminho:path}", tags=["hea"], responses={503: {"model": ErroEnvelope}},
             operation_id="hea_indisponivel_post", summary="Motor HEA (indisponível até Q-01)")
def hea_indisponivel(caminho: str, request: Request):
    """Responde 503 explícito: nenhum valor HEA é inventado enquanto não houver modelo com fonte (PI-02)."""
    return envelope_erro("Motor HEA indisponível: falta a base de dados com fonte (questão Q-01). "
                         "Nenhum valor é simulado.", "CAPACIDADE_INDISPONIVEL", 503,
                         request_id=request.scope.get("state", {}).get("request_id"))


# --------------------------------------------------------------------------- plataforma
@router.get("/meta/capabilities", response_model=OkEnvelope[Capabilities], tags=["plataforma"])
def capacidades(settings: Settings = Depends(get_settings)):
    """Estado de cada serviço para o frontend (live/demo/disabled). Em produção, demonstração é proibida."""
    demo = settings.demo_permitido
    motores = versoes_motores()
    nao_validados = (None if settings.producao
                     else "Dados ainda não validados são aceitos com aviso (ambiente não produtivo).")
    return _ok({
        "ambiente": settings.env,
        "crystallography": ServicoCapacidade(disponivel=True, demo_permitido=False,
                                             versao=motores["crystallography"], motivo=nao_validados),
        "thermodynamics": ServicoCapacidade(
            disponivel=not settings.producao, demo_permitido=False, versao=motores["thermodynamics"],
            motivo=("α, T_f e alotropia ainda sem validação (Q-03)." if settings.producao else nao_validados)),
        "hea": ServicoCapacidade(disponivel=False, demo_permitido=demo,
                                 motivo="Sem modelo nem dados com fonte (Q-01)."),
        "ia": ServicoCapacidade(disponivel=settings.ia_enabled, demo_permitido=False,
                                motivo=None if settings.ia_enabled else "Desligada até decisão (RQ-EDU-05)."),
        "autenticacao": ServicoCapacidade(disponivel=False, demo_permitido=False,
                                          motivo="Implementada na Fase 8 (ADR-008)."),
    })


@router.get("/meta/version", response_model=OkEnvelope[VersionInfo], tags=["plataforma"])
def versao(servico: ServicoCalculo = Depends(get_servico)):
    return _ok({"api": __version__, "motores": versoes_motores(), "versao_dados": servico.versao_dados()})


# --------------------------------------------------------------------------- aliases /v1 (depreciados)
alias = APIRouter(prefix="/v1", responses=_ERROS, deprecated=True, tags=["compatibilidade /v1 (depreciado)"])

#: alias → (método, handler, modelo de resposta, rota sucessora)
_SUCESSORAS = {
    "/crystals/metals": ("GET", listar_metais, OkEnvelope[Dict[str, MetalInfo]], "/api/v1/crystallography/metals"),
    "/crystals/structures": ("GET", listar_estruturas, OkEnvelope[List[StructureInfo]],
                             "/api/v1/crystallography/structures"),
    "/crystals/structure": ("POST", calcular_celula, OkEnvelope[StructureResponse], "/api/v1/crystallography/cells"),
    "/crystallography/miller": ("POST", calcular_miller, OkEnvelope[MillerResponse], "/api/v1/crystallography/miller"),
    "/calculations/density": ("POST", calcular_densidade, OkEnvelope[DensityResponse],
                              "/api/v1/crystallography/density"),
    "/export/cif": ("POST", exportar_cif, OkEnvelope[ExportResponse], "/api/v1/exports/cif"),
    "/export/xyz": ("POST", exportar_xyz, OkEnvelope[ExportResponse], "/api/v1/exports/xyz"),
}


def _marcar_depreciado(sucessora: str):
    def marcar(response: Response) -> None:
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = f'<{sucessora}>; rel="successor-version"'
    return marcar


for _caminho, (_metodo, _handler, _modelo, _sucessora) in _SUCESSORAS.items():
    alias.add_api_route(_caminho, _handler, methods=[_metodo], response_model=_modelo,
                        dependencies=[Depends(_marcar_depreciado(_sucessora))],
                        name=f"alias_{_handler.__name__}", operation_id=f"alias_{_handler.__name__}")
