"""Schemas Pydantic v2 do contrato v1 (achados BE-07, SE-05).

Regras gerais:
* números aceitam vírgula decimal ("0,128") e rejeitam NaN/Infinito;
* requisições v1 usam ``extra="forbid"``; as rotas legadas reutilizam os mesmos
  modelos com ``extra="ignore"`` (ver ``Legado*``);
* campos NOVOS de resposta são sempre opcionais ou com valor padrão, para que
  clientes antigos continuem funcionando (regra de evolução do contrato).
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from ..core.constantes import FAIXA_A_NM, FAIXA_C_A, FAIXA_PESO, FAIXA_RAIO_NM, INDICE_MAXIMO
from ..core.miller import normalizar_tipo


def _aceitar_virgula(valor: Any) -> Any:
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        return texto.replace(",", ".")
    return valor


def _tipo_miller(valor: Any) -> Any:
    try:
        return normalizar_tipo(valor)
    except ValueError:
        return valor  # deixa o Literal produzir o erro de validação


NumeroBR = Annotated[Optional[float], BeforeValidator(_aceitar_virgula)]

T = TypeVar("T")


class OkEnvelope(BaseModel, Generic[T]):
    ok: bool = True
    result: T


class ErroEnvelope(BaseModel):
    ok: bool = False
    error: str = Field(..., description="Mensagem legível (pt-BR)")
    code: str = Field(..., description="Código estável do erro, ex.: ENTRADA_INVALIDA")
    status: int
    correlation_id: Optional[str] = None
    details: Optional[List[Dict[str, Any]]] = None


# --------------------------------------------------------------------------- tabelas
class MetalInfo(BaseModel):
    nome: str
    estrutura: str
    raio: float = Field(..., description="Raio atômico em nm")
    peso: float = Field(..., description="Peso atômico em g/mol")
    densidade_exp: Optional[float] = Field(None, description="Densidade experimental em g/cm³")
    c_a: Optional[float] = None
    nc: int
    a_nm: Optional[float] = Field(None, description="Parâmetro de rede medido (nm), quando disponível")
    c_nm: Optional[float] = None
    fonte: Optional[str] = Field(None, description="Chave da fonte bibliográfica do dado")


class StructureInfo(BaseModel):
    sigla: str
    nome: str
    n: int
    nc: int
    a_em_R: float
    relacao: str
    fea: float


# --------------------------------------------------------------------------- célula
class _BaseCelula(BaseModel):
    nome: Optional[str] = Field(None, max_length=64,
                                description="Metal (Fe, Cu, Al, ...) ou estrutura (CS/CCC/CFC/HC)")
    estrutura: Optional[str] = Field(None, max_length=32, description="Sobrescreve a estrutura do metal")
    raio: NumeroBR = Field(None, ge=FAIXA_RAIO_NM[0], le=FAIXA_RAIO_NM[1], allow_inf_nan=False,
                           description="Raio atômico em nm")
    peso: NumeroBR = Field(None, ge=FAIXA_PESO[0], le=FAIXA_PESO[1], allow_inf_nan=False,
                           description="Peso atômico em g/mol")
    c_a: NumeroBR = Field(None, ge=FAIXA_C_A[0], le=FAIXA_C_A[1], allow_inf_nan=False,
                          description="Razão c/a (apenas HC)")


class StructureRequest(_BaseCelula):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [
            {"nome": "Fe"},
            {"nome": "Cu", "estrutura": "CFC"},
            {"nome": "HC", "raio": 0.16, "peso": 24.31, "c_a": 1.624},
        ]},
    )


class DensityRequest(StructureRequest):
    pass


class ExportRequest(_BaseCelula):
    model_config = ConfigDict(extra="forbid")
    formula: Optional[str] = Field(None, max_length=64, description="Fórmula química para o cabeçalho CIF")
    comentario: Optional[str] = Field(None, max_length=200, description="Comentário (XYZ)")


class LegadoStructureRequest(_BaseCelula):
    model_config = ConfigDict(extra="ignore")


class Atomo(BaseModel):
    pos: List[float] = Field(..., min_length=3, max_length=3)
    tipo: str
    fracao: float
    fracao_txt: str


class SitioBase(BaseModel):
    frac: List[float] = Field(..., min_length=3, max_length=3, description="Coordenadas fracionárias em [0,1)")
    tipo: str


class GrupoEspacial(BaseModel):
    hm: str = Field(..., description="Símbolo Hermann-Mauguin")
    numero: int = Field(..., description="Número nas International Tables")


class DensityStep(BaseModel):
    titulo: str
    formula: str
    detalhe: Optional[str] = ""


class AtomGroup(BaseModel):
    tipo: str
    rotulo: str
    quantidade: int
    fracao: float
    fracao_txt: str
    contribuicao: float


class StructureResponse(BaseModel):
    rotulo: str
    simbolo: Optional[str]
    nome_metal: Optional[str]
    editado: bool
    generica: bool
    estrutura: str
    estrutura_nome: str
    relacao_a: str
    contato: str
    n: int
    nc: int
    fea: float
    vazios: float
    a_em_R: float
    c_a: Optional[float]
    raio_nm: Optional[float]
    peso: Optional[float]
    a_nm: Optional[float]
    c_nm: Optional[float]
    a_fonte: Literal["medido", "derivado_de_R", "relativo"] = "derivado_de_R"
    volume_nm3: Optional[float]
    volume_cm3: Optional[float]
    densidade: Optional[float]
    densidade_exp: Optional[float]
    erro_percent: Optional[float]
    raio_relativo: float
    atomos: List[Atomo] = Field(..., description="Átomos de DESENHO (inclui réplicas de fronteira)")
    arestas: List[List[List[float]]]
    contagem: List[AtomGroup]
    base: List[SitioBase] = Field(default_factory=list, description="Base cristalográfica (sítios únicos)")
    z: Optional[int] = Field(None, description="Átomos na célula cristalográfica (Z)")
    grupo_espacial: Optional[GrupoEspacial] = None
    passos_densidade: List[DensityStep]
    interpretacao: List[str]
    avisos: List[str] = Field(default_factory=list)
    fonte: Optional[str] = None


# --------------------------------------------------------------------------- Miller
class _BaseMiller(BaseModel):
    estrutura: str = Field(..., max_length=32, description="CS | CCC | CFC | HC")
    tipo: Annotated[Literal["plano", "direcao"], BeforeValidator(_tipo_miller)] = "plano"
    indices: List[int] = Field(..., min_length=3, max_length=4)
    a_nm: NumeroBR = Field(None, ge=FAIXA_A_NM[0], le=FAIXA_A_NM[1], allow_inf_nan=False,
                           description="Parâmetro de rede em nm")
    c_a: NumeroBR = Field(None, ge=FAIXA_C_A[0], le=FAIXA_C_A[1], allow_inf_nan=False,
                          description="Razão c/a (apenas HC)")

    @field_validator("indices")
    @classmethod
    def _faixa(cls, v: List[int]) -> List[int]:
        if all(x == 0 for x in v):
            raise ValueError("os índices não podem ser todos nulos")
        if any(abs(x) > INDICE_MAXIMO for x in v):
            raise ValueError(f"use índices entre -{INDICE_MAXIMO} e {INDICE_MAXIMO}")
        return v


class MillerRequest(_BaseMiller):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [
            {"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1], "a_nm": 0.3615},
            {"estrutura": "HC", "tipo": "plano", "indices": [1, 0, -1, 1], "c_a": 1.624},
            {"estrutura": "CCC", "tipo": "direcao", "indices": [1, 1, 0]},
        ]},
    )


class LegadoMillerRequest(_BaseMiller):
    model_config = ConfigDict(extra="ignore")


class MillerResponse(BaseModel):
    tipo: Literal["plano", "direcao"]
    estrutura: str
    indices: List[int]
    notacao: str
    notacao_alternativa: Optional[str] = None
    poligono: Optional[List[List[float]]] = None
    centro: Optional[List[float]] = None
    normal: Optional[List[float]] = None
    area_rel: Optional[float] = None
    area_nm2: Optional[float] = None
    d_rel: Optional[float] = None
    d_nm: Optional[float] = None
    inicio: Optional[List[float]] = None
    fim: Optional[List[float]] = None
    comprimento_rel: Optional[float] = None
    comprimento_nm: Optional[float] = None
    atomos_contados: Optional[float] = None
    densidade_linear_rel: Optional[float] = None
    densidade_linear_nm: Optional[float] = None
    atomos: List[int]
    ordem: int = Field(1, description="MDC dos índices; > 1 indica plano/direção não reduzido")
    indices_reduzidos: Optional[List[int]] = None
    avisos: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- densidade / export
class DensityResponse(BaseModel):
    rotulo: str
    estrutura: str
    n: int
    nc: int
    fea: float
    vazios: float
    densidade: Optional[float]
    densidade_exp: Optional[float]
    erro_percent: Optional[float]
    volume_cm3: Optional[float]
    raio_nm: Optional[float]
    peso: Optional[float]
    a_nm: Optional[float] = None
    c_nm: Optional[float] = None
    a_fonte: Optional[str] = None
    passos: List[DensityStep]
    avisos: List[str] = Field(default_factory=list)


class ExportResponse(BaseModel):
    formato: Literal["cif", "xyz"]
    filename: str
    content: str
    content_type: str


class HealthResponse(BaseModel):
    ok: bool = True
    status: str
    version: str
    data_version: Optional[str] = None
    checks: Optional[Dict[str, bool]] = None
