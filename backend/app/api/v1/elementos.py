"""Tabela periódica (/api/v1/elements — ADR-018). Somente leitura; dados de referência com procedência."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Path, Query, Response
from pydantic import BaseModel, Field

from app.services.elementos import ServicoElementos

from ..dependencias import get_servico_elementos
from .schemas import ErroEnvelope, OkEnvelope

router = APIRouter(prefix="/api/v1", responses={404: {"model": ErroEnvelope}, 422: {"model": ErroEnvelope}},
                   tags=["tabela periódica"])
_CACHE = "public, max-age=3600"


class ElementProperty(BaseModel):
    codigo: str
    nome: str
    valor: float
    incerteza: Optional[float] = None
    intervalo: Optional[List[float]] = Field(None, description="[mín, máx] da variação natural (CIAAW)")
    unidade: str
    fonte: str
    estado: str
    nota: Optional[str] = None


class ElementMass(BaseModel):
    codigo: Literal["peso_atomico_padrao", "massa_isotopica_referencia"]
    valor: float
    unidade: str


class ElementSource(BaseModel):
    tipo: str
    citacao: str
    doi: Optional[str] = None
    url: Optional[str] = None
    licenca: Optional[str] = None
    versao_fonte: Optional[str] = None
    acessado_em: Optional[str] = None


class ElementProvenance(BaseModel):
    conjunto: str
    versao_dados: str
    fontes: Dict[str, ElementSource]
    avisos: List[str]


class ElementSummary(BaseModel):
    numero_atomico: int
    simbolo: str
    nome: str
    nome_en: str
    periodo: int
    grupo: Optional[int] = Field(None, description="nulo no bloco f (lantanídeos e actinídeos)")
    bloco: Literal["s", "p", "d", "f"]
    categoria: str
    estado_padrao: str
    massa: Optional[ElementMass] = None


class ElementDetail(BaseModel):
    numero_atomico: int
    simbolo: str
    nome: str
    nome_en: str
    periodo: int
    grupo: Optional[int] = None
    bloco: Literal["s", "p", "d", "f"]
    categoria: str
    configuracao_eletronica: Optional[str] = None
    estados_oxidacao: Optional[str] = None
    estado_padrao: str
    ano_descoberta: Optional[int] = None
    conhecido_antiguidade: bool
    propriedades: List[ElementProperty]
    procedencia: ElementProvenance


class ElementList(BaseModel):
    total: int
    itens: List[ElementSummary]
    procedencia: ElementProvenance


def _ok(resultado: Any) -> Dict[str, Any]:
    return {"ok": True, "result": resultado}


@router.get("/elements", response_model=OkEnvelope[ElementList], summary="Os 118 elementos (com filtros)")
def listar_elementos(response: Response,
                     periodo: Optional[int] = Query(None, ge=1, le=7),
                     grupo: Optional[int] = Query(None, ge=1, le=18),
                     bloco: Optional[Literal["s", "p", "d", "f"]] = None,
                     categoria: Optional[str] = Query(None, max_length=40),
                     estado_padrao: Optional[Literal["solido", "liquido", "gas", "solido_previsto",
                                                     "gas_previsto"]] = None,
                     servico: ServicoElementos = Depends(get_servico_elementos)):
    response.headers["Cache-Control"] = _CACHE
    return _ok(servico.listar({"periodo": periodo, "grupo": grupo, "bloco": bloco, "categoria": categoria,
                               "estado_padrao": estado_padrao}))


_REF = r"^[A-Za-z]{1,3}$|^\d{1,3}$"   # símbolo (1–3 letras) ou número atômico: recusa qualquer outro texto


@router.get("/elements/{ref}", response_model=OkEnvelope[ElementDetail],
            summary="Um elemento por símbolo (Fe) ou número atômico (26), com propriedades e fontes")
def obter_elemento(response: Response, ref: str = Path(..., min_length=1, max_length=3, pattern=_REF),
                   servico: ServicoElementos = Depends(get_servico_elementos)):
    response.headers["Cache-Control"] = _CACHE
    return _ok(servico.obter(ref))
