"""Schemas Pydantic v2 do contrato /api/v1 (origem: CrystaLab v1.1.0 ``api/schemas.py``; API.md).

Consolidação: campos novos SEMPRE opcionais (regra de evolução abaixo); modelos ``Legado*`` removidos
junto com as rotas /api/* da v1.0 (API.md §3); contratos novos ao fim do arquivo.

Texto original:

Regras gerais:
* números aceitam vírgula decimal ("0,128") e rejeitam NaN/Infinito;
* requisições usam ``extra="forbid"``;
* campos NOVOS de resposta são sempre opcionais ou com valor padrão, para que
  clientes antigos continuem funcionando (regra de evolução do contrato).
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.engines.crystallography.constantes import (
    FAIXA_A_NM,
    FAIXA_C_A,
    FAIXA_PESO,
    FAIXA_RAIO_NM,
    INDICE_MAXIMO,
    MAX_SOLUTOS,
    SUPERCELULA_MAXIMA,
)
from app.engines.crystallography.miller import normalizar_tipo


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

#: Base em que os percentuais da rota de ligas foram informados (mesmo vocabulário do HEA).
BaseComposicaoLiga = Literal["atomica", "massica"]
#: Papel de um componente da liga.
PapelComponente = Literal["solvente", "substitucional", "intersticial"]

T = TypeVar("T")


class OkEnvelope(BaseModel, Generic[T]):
    ok: bool = True
    result: T


class ErroEnvelope(BaseModel):
    ok: bool = False
    error: str = Field(..., description="Mensagem legível (pt-BR)")
    code: str = Field(..., description="Código estável do erro, ex.: ENTRADA_INVALIDA")
    status: int
    request_id: Optional[str] = Field(None, description="Identificador da requisição (também em X-Request-ID)")
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
    a: NumeroBR = Field(None, ge=FAIXA_A_NM[0], le=FAIXA_A_NM[1], allow_inf_nan=False,
                        description="Parâmetro de rede a em nm; define R pela condição de contato (tem prioridade)")


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




class Atomo(BaseModel):
    pos: List[float] = Field(..., min_length=3, max_length=3)
    tipo: str
    fracao: float
    fracao_txt: str
    elemento: Optional[str] = None


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


class DadoUsado(BaseModel):
    simbolo: str
    codigo: str
    valor: float
    unidade: str
    estado: str
    fonte: Optional[str] = None


class Procedencia(BaseModel):
    """PI-06/07: de onde veio o resultado (ARQUITETURA_FINAL §6)."""

    classe: Literal["analitico", "estimativa_modelo", "experimental", "simulacao_ilustrativa", "demonstrativo"]
    motor: str
    versao_motor: str
    versao_dados: str
    fontes_modelo: List[str] = Field(default_factory=list)
    fontes_dados: List[str] = Field(default_factory=list)
    dados_usados: List[DadoUsado] = Field(default_factory=list)
    parametros_sha256: str
    avisos: List[str] = Field(default_factory=list)
    calculado_em: Optional[str] = None


class PlanarInfo(BaseModel):
    validado: bool
    motivo: Optional[str] = None
    atomos_no_plano: Optional[float] = None
    densidade_rel: Optional[float] = Field(None, description="Átomos por a²")
    densidade_nm2: Optional[float] = Field(None, description="Átomos por nm²")
    fracao_planar: Optional[float] = None
    fonte: Optional[str] = None


class FamiliaPlano(BaseModel):
    m: int = Field(..., description="h·x + k·y + l·z = m (coordenadas fracionárias)")
    poligono: List[List[float]]
    centro: List[float]


class AtomGroup(BaseModel):
    tipo: str
    rotulo: str
    quantidade: int
    fracao: float
    fracao_txt: str
    contribuicao: float


class GrupoVizinhos(BaseModel):
    """Grupo de primeiros vizinhos (contrato R1 §3). No HC fora do c/a ideal os 12 vizinhos são 6 + 6."""

    grupo: Literal["basal", "entre_planos"]
    n: int
    d_rel: float = Field(..., description="Distância em unidades de a")
    d_nm: Optional[float] = Field(None, description="Distância em nm; nulo quando a_nm é nulo")


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
    nc_txt: str = Field("", description='"6 + 6" no HC com c/a ≠ ideal; senão o próprio nc como texto')
    fea: float
    vazios: float
    fea_modelo: Literal["esferas_rigidas"] = Field(
        "esferas_rigidas", description="O FEA é propriedade do modelo de esferas rígidas, não empacotamento medido")
    raio_contato_rel: Optional[float] = Field(
        None, description="R_c/a = ½·mín(1, d_entre_planos/a); só HC (nulo nas cúbicas)")
    contato_tipo: Optional[Literal["basal", "entre_planos", "ambos"]] = Field(
        None, description="Onde ocorre o primeiro contato das esferas; só HC")
    c_a_ideal: Optional[float] = Field(None, description="√(8/3); só HC")
    c_a_natureza: Optional[Literal["ideal", "tabelado", "derivado_de_a_c_medidos", "informado"]] = Field(
        None, description="Origem do c/a usado; só HC")
    vizinhos: Optional[List[GrupoVizinhos]] = Field(
        None, description="Grupos de primeiros vizinhos; só HC em R1 (nulo nas cúbicas)")
    a_em_R: float
    c_a: Optional[float]
    raio_nm: Optional[float]
    peso: Optional[float]
    a_nm: Optional[float]
    c_nm: Optional[float]
    a_fonte: Literal["medido", "derivado_de_R", "informado", "relativo"] = "derivado_de_R"
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
    passos_parametro: List[DensityStep] = Field(default_factory=list)
    passos_fea: List[DensityStep] = Field(default_factory=list)
    procedencia: Optional[Procedencia] = None


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
    supercelula: int = Field(1, ge=1, le=SUPERCELULA_MAXIMA,
                             description="n > 1: desenha a família de planos paralelos na supercélula n×n×n")
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [
            {"estrutura": "CFC", "tipo": "plano", "indices": [1, 1, 1], "a_nm": 0.3615},
            {"estrutura": "HC", "tipo": "plano", "indices": [1, 0, -1, 1], "c_a": 1.624},
            {"estrutura": "CCC", "tipo": "direcao", "indices": [1, 1, 0]},
        ]},
    )




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
    planar: Optional[PlanarInfo] = None
    supercelula: int = 1
    familia: Optional[List[FamiliaPlano]] = None
    procedencia: Optional[Procedencia] = None


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
    procedencia: Optional[Procedencia] = Field(
        None, description="Rastreabilidade do cálculo: dados do repositório usados, estado e fonte (QA-R2-02)")


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


# --------------------------------------------------------------------------- supercélula (v1.4)
class SupercellRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"estrutura": "CFC", "n": 3}]})
    estrutura: str = Field(..., max_length=32, description="CS | CCC | CFC | HC")
    n: int = Field(2, ge=1, le=SUPERCELULA_MAXIMA)
    c_a: NumeroBR = Field(None, ge=FAIXA_C_A[0], le=FAIXA_C_A[1], allow_inf_nan=False)


class AtomoRede(BaseModel):
    pos: List[float] = Field(..., min_length=3, max_length=3, description="Cartesiano em unidades de a")
    frac: List[float] = Field(..., min_length=3, max_length=3)
    tipo: str


class SupercellResponse(BaseModel):
    estrutura: str
    n: int
    c_a: Optional[float] = None
    atomos: List[AtomoRede]
    arestas: List[List[List[float]]]
    vetores_rede: List[List[float]] = Field(..., description="a₁, a₂, a₃ (ou c) em unidades de a")


# --------------------------------------------------------------------------- solução sólida (v1.4)
class SolutoPedido(BaseModel):
    """Um soluto do pedido multicomponente (contrato R1 §2.1)."""

    model_config = ConfigDict(extra="forbid")
    elemento: str = Field(..., max_length=32, description="Símbolo, nome ou alias resolvido pelo repositório")
    x: NumeroBR = Field(..., ge=0, le=100, allow_inf_nan=False,
                        description="% do soluto na base de 'base_composicao'")
    modo: Literal["auto", "substitucional", "intersticial"] = Field(
        "auto", description="'auto': intersticial se o símbolo é C, H ou N; senão substitucional")
    sitio: Literal["auto", "octaedrico", "tetraedrico", "cubico"] = Field(
        "auto", description="Só para intersticial. 'auto': octaédrico em CCC, CFC e HC; cúbico em CS")


class SolidSolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [
        {"base": "Cu", "soluto": "Ni", "x": 30},
        {"base": "Fe", "soluto": "C", "x": 2, "distorcer": True},
        {"base": "Cu", "soluto": "Au", "x": 25, "arranjo": "ordenado", "n": 2},
        {"base": "Fe", "n": 3, "semente": 7,
         "solutos": [{"elemento": "Cr", "x": 12}, {"elemento": "Ni", "x": 8},
                     {"elemento": "C", "x": 1, "modo": "intersticial", "sitio": "octaedrico"}]},
    ]})
    base: str = Field(..., max_length=32, description="Metal solvente")
    soluto: Optional[str] = Field(
        None, max_length=32,
        description="Forma binária legada: metal (substitucional) ou C, N, H (intersticial). "
                    "Informe exatamente um entre 'soluto' e 'solutos'")
    solutos: Optional[List[SolutoPedido]] = Field(
        None, min_length=1, max_length=MAX_SOLUTOS,
        description="Lista de 1 a 6 solutos, substitucionais e/ou intersticiais; "
                    "a ordem do pedido não altera o resultado")
    x: NumeroBR = Field(None, ge=0, le=100, allow_inf_nan=False,
                        description="% do soluto legado (padrão 10); não use junto com 'solutos'")
    base_composicao: BaseComposicaoLiga = Field(
        "atomica", description="Base em que todos os x do pedido foram informados")
    estrutura_matriz: Optional[Literal["CS", "CCC", "CFC", "HC"]] = Field(
        None, description="Estrutura imposta à matriz; padrão: a do solvente no repositório")
    n: int = Field(3, ge=1, le=SUPERCELULA_MAXIMA)
    arranjo: Literal["aleatorio", "ordenado"] = "aleatorio"
    distorcer: bool = False
    semente: int = Field(1, ge=0, le=2**31 - 1, description="0 é semente válida e respeitada")

    @field_validator("x")
    @classmethod
    def _x_so_na_forma_legada(cls, valor: Optional[float], info: Any) -> Optional[float]:
        if info.data.get("solutos") is not None:
            raise PydanticCustomError("x_com_solutos",
                                      "Com 'solutos', informe o x de cada item, não o x do pedido.")
        return valor

    @model_validator(mode="after")
    def _soluto_ou_solutos(self) -> SolidSolutionRequest:
        if (self.soluto in (None, "")) == (self.solutos is None):
            raise PydanticCustomError("soluto_ou_solutos", "Informe 'soluto' ou 'solutos', não os dois.")
        return self


class RegraSolubilidade(BaseModel):
    criterio: str
    valor: Optional[str] = None
    ok: Optional[bool] = Field(None, description="None = indisponível (ver 'indisponivel')")
    detalhe: str
    indisponivel: Optional[str] = None


class SitioAtomo(BaseModel):
    """Sítio cristalográfico do átomo. ``wyckoff`` é nulo até a conferência bibliográfica (decisão D-e)."""

    nome: str
    wyckoff: Optional[str] = None
    nc: int
    nc_txt: str = ""


class AtomoLiga(BaseModel):
    pos: List[float] = Field(..., description="Cartesiana, em unidades de a da liga")
    frac: List[float] = Field(..., description="Fracionária na célula replicada (0 a n)")
    tipo: Literal["rede", "intersticial"]
    elemento: str
    raio_rel: float = Field(..., description="Raio de DESENHO (raio tabelado / a), não raio do átomo em solução")
    id: str = Field("", description="Identificador estável: depende só de estrutura, n e sítio")
    imagem: bool = Field(False, description="true = imagem periódica de fronteira; não entra em contagem")
    imagem_de: Optional[str] = Field(None, description="id do átomo único de origem")
    pos_nm: List[float] = Field(default_factory=list, description="pos × a_nm (herda a natureza de a_nm)")
    celula: List[int] = Field(default_factory=list,
                              description="(i, j, k); numa imagem a coordenada transladada vale n")
    frac_celula: List[float] = Field(default_factory=list, description="Fracionária em [0, 1)")
    ocupacao: Literal["solvente", "substitucional", "intersticial"] = "solvente"
    sitio: Optional[SitioAtomo] = None
    fase: str = Field("matriz", description="id da fase em 'fases'")
    pos_ideal: Optional[List[float]] = Field(None, description="Posição de rede antes da distorção ilustrativa")


class SitioIntersticial(BaseModel):
    nome: str
    fator: float = Field(..., description="r_livre/R")
    raio_nm: float = Field(..., description="Raio livre do sítio em nm")
    nc: int = Field(..., description="Total de vizinhos (inteiro)")
    elemento: str = Field("", description="Intersticial que usa o sítio")
    tipo: Literal["octaedrico", "tetraedrico", "cubico"] = "octaedrico"
    nc_txt: str = Field("", description='Ex.: "2 + 4" no octaédrico da CCC')
    sitios_por_celula: int = 0
    wyckoff: Optional[str] = None
    escolha: Literal["padrao", "informado"] = "padrao"
    justificativa: str = ""
    padrao_verificado: bool = Field(False, description="false enquanto o sítio padrão não tiver parecer com fonte")


class Distorcao(BaseModel):
    classe: Literal["simulacao_ilustrativa"]
    descricao: str


class ComponenteSolicitado(BaseModel):
    elemento: str
    papel: PapelComponente
    at_pct: float = Field(..., description="% atômica sobre todos os átomos (intersticiais incluídos)")
    massa_pct: float


class ComponenteRepresentado(ComponenteSolicitado):
    n_atomos: int = Field(..., description="Átomos ÚNICOS (pode ser 0)")


class ComposicaoLiga(BaseModel):
    """Composição SOLICITADA × REPRESENTADA na supercélula periódica (parecer R1-CRI-01 §3.2)."""

    base_entrada: BaseComposicaoLiga = "atomica"
    solicitada: List[ComponenteSolicitado] = Field(default_factory=list)
    representada: List[ComponenteRepresentado] = Field(default_factory=list)
    n_sitios_rede: int = Field(0, description="Z·n³")
    n_intersticiais: int = 0
    n_atomos_unicos: int = 0
    n_desenhados: int = Field(0, description="Esferas em 'atomos' (únicos + imagens)")
    resolucao_at_pct: float = Field(0.0, description="100 / n_atomos_unicos")
    desvio_maximo_at_pct: float = 0.0


class Realizacao(BaseModel):
    tipo: Literal["estatistica", "ordenada_prototipo", "sem_soluto"] = "estatistica"
    semente: int = 1
    algoritmo: str = "mt19937-chaves-v1"
    n: int = 1
    aviso: str = ""


class ModeloLiga(BaseModel):
    tipo_solucao: Literal["substitucional", "intersticial", "mista"] = "substitucional"
    ordenacao: Literal["desordenada", "ordenada_prototipo"] = "desordenada"
    fases: Literal["monofasica_imposta"] = "monofasica_imposta"
    geometria: Literal["idealizada"] = "idealizada"
    parametro_rede: Literal["estimativa_vegard_sobre_raios"] = "estimativa_vegard_sobre_raios"
    parametro_rede_solvente: Literal["derivado_de_R", "medido"] = "derivado_de_R"
    c_a: Optional[Literal["ideal", "tabelado", "derivado_de_a_c_medidos", "informado"]] = None
    hipoteses: List[str] = Field(default_factory=list)


class Prototipo(BaseModel):
    strukturbericht: str
    prototipo: str
    composicao_ideal_at_pct: Dict[str, float] = Field(default_factory=dict)
    rede_ordenada: str
    observacao: Optional[str] = None


class FaseLiga(BaseModel):
    id: str = "matriz"
    nome: str = ""
    estrutura: Literal["CS", "CCC", "CFC", "HC"] = "CFC"
    origem: Literal["imposta_pelo_modelo"] = "imposta_pelo_modelo"
    composicao: List[ComponenteRepresentado] = Field(default_factory=list)
    fracao: Optional[float] = Field(None, description="Sempre nulo em R1: o motor não calcula equilíbrio de fases")
    fracao_motivo: str = ""


class VerificacaoLimite(BaseModel):
    verificado: bool = False
    valor: Optional[float] = None
    motivo: str = ""


class VerificacaoFases(BaseModel):
    previstas: Optional[List[str]] = None
    motivo: str = ""


class Verificacoes(BaseModel):
    """O que o motor NÃO verifica (parecer R1-CRI-01 §3.7)."""

    limite_solubilidade: VerificacaoLimite = Field(default_factory=VerificacaoLimite)
    fases_secundarias: VerificacaoFases = Field(default_factory=VerificacaoFases)


class RegrasSoluto(BaseModel):
    soluto: str
    modo: Literal["substitucional", "intersticial"]
    regras: List[RegraSolubilidade] = Field(default_factory=list)
    conclusao: str = ""


class ElementoPuro(BaseModel):
    """Propriedade TABELADA do elemento puro — não é propriedade do átomo na liga (parecer §3.5)."""

    simbolo: str
    papel: PapelComponente
    raio_nm: Optional[float] = None
    massa_g_mol: Optional[float] = None
    estrutura_elemento_puro: Optional[str] = None
    estado_do_dado: str = ""
    fonte: Optional[str] = None


class SolidSolutionResponse(BaseModel):
    rotulo: str
    base: str
    soluto: str = Field(..., description="Com vários solutos: o primeiro da ordem canônica (campo legado)")
    intersticial: bool
    estrutura: str
    estrutura_nome: str
    nc: int
    c_a: Optional[float] = None
    supercelula: int
    semente: int
    x_pct: float
    pct_peso: float
    a_nm: float
    c_nm: Optional[float] = None
    a_base_nm: float
    raio_relativo: float
    densidade: float
    densidade_base: float
    n_soluto: int = Field(..., description="Átomos ÚNICOS de soluto (soma de todos os solutos)")
    n_solvente: int = Field(..., description="Átomos ÚNICOS de solvente")
    fase_ordenada: Optional[str] = None
    nota_arranjo: Optional[str] = None
    sitio: Optional[SitioIntersticial] = None
    regras: List[RegraSolubilidade]
    conclusao: str
    passos: List[DensityStep]
    distorcao: Optional[Distorcao] = None
    atomos: List[AtomoLiga]
    arestas: List[List[List[float]]]
    composicao: ComposicaoLiga = Field(default_factory=ComposicaoLiga)
    realizacao: Realizacao = Field(default_factory=Realizacao)
    modelo: ModeloLiga = Field(default_factory=ModeloLiga)
    prototipo: Optional[Prototipo] = None
    fases: List[FaseLiga] = Field(default_factory=list)
    verificacoes: Verificacoes = Field(default_factory=Verificacoes)
    regras_por_soluto: List[RegrasSoluto] = Field(default_factory=list)
    conclusao_global: Optional[str] = Field(
        None, description="Nulo com mais de um soluto: as regras são binárias (motivo em 'indisponiveis')")
    sitios: List[SitioIntersticial] = Field(default_factory=list)
    elementos: List[ElementoPuro] = Field(default_factory=list)
    convencoes: List[str] = Field(default_factory=list)
    indisponiveis: Dict[str, str] = Field(default_factory=dict)
    procedencia: Procedencia


# --------------------------------------------------------------------------- temperatura (v1.4)
class ThermalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [
        {"material": "Fe", "temperatura_c": 1000},
        {"liga": {"base": "Cu", "soluto": "Ni", "x": 30}, "temperatura_c": 500},
    ]})
    material: Optional[str] = Field(None, max_length=32)
    liga: Optional[SolidSolutionRequest] = None
    temperatura_c: NumeroBR = Field(20.0, ge=-273.15, le=5000, allow_inf_nan=False)

    @model_validator(mode="after")
    def _um_dos_dois(self) -> ThermalRequest:
        if (self.liga is None) == (not self.material):
            raise ValueError("informe 'material' OU 'liga'")
        return self


class NotaTermica(BaseModel):
    tipo: Literal["info", "alerta"]
    texto: str
    fonte: Optional[str] = Field(
        None, description="Fonte da afirmação ou o motivo de ela não ter fonte verificada (achado T-7). "
                          "Nulo quando a nota é uma consequência direta do modelo já citado em procedência.")


class FaixaAlotropica(BaseModel):
    """Faixa de estabilidade cadastrada, só quando o dado passa pela política (achados T-8 e T-9)."""

    simbolo: str
    fase: str
    estrutura: str
    de_c: float
    ate_c: float
    estado: Literal["rascunho", "aguardando_validacao", "validado", "rejeitado", "arquivado"]
    fonte: Optional[str] = None
    pressao: Literal["nao_modelada"] = Field(
        "nao_modelada", description="A pressão não entra no modelo; as faixas são de pressão ambiente")


class DominioCurva(BaseModel):
    de_c: float = Field(..., description="Limite inferior do domínio do modelo (100 K)")
    ate_c: float = Field(..., description="Limite superior: a T_f do modelo")
    limite_inferior: str
    limite_superior: str


class ThermalResponse(BaseModel):
    temperatura_c: float
    temperatura_k: float
    fusao_c: float
    homologa: float
    alfa_1e6_k: float
    fator: Optional[float] = Field(None, description="Nulo acima da T_f do modelo (achado T-1)")
    a_ref_nm: float
    a_nm: Optional[float] = Field(None, description="Nulo acima da T_f do modelo (achado T-1)")
    delta_a_pct: Optional[float] = Field(None, description="Nulo acima da T_f do modelo (achado T-1)")
    densidade: Optional[float] = None
    delta_v_pct: Optional[float] = Field(None, description="Nulo acima da T_f do modelo (achado T-1)")
    u_nm: float = Field(..., description="Deslocamento quadrático médio estimado (ver u_rotulo), não amplitude")
    razao_lindemann: float
    amplitude_rel: float
    lindemann: float
    fundido: bool = Field(
        ..., description="Estado líquido afirmado: só para elemento puro acima da T_f tabelada. Em mistura é "
                         "sempre falso, porque a T_f da regra das misturas não é solidus nem liquidus "
                         "(achado T-6); use acima_da_tf_nominal para a comparação numérica.")
    curva: List[List[float]] = Field(
        ..., description="[T (°C), u/d] no domínio do modelo: de 100 K até a T_f do modelo (achados T-1 e T-4). "
                         "Vazia quando não há domínio válido, com o motivo em indisponiveis.curva")
    notas: List[NotaTermica]
    acima_da_tf_nominal: bool = Field(..., description="T ≥ T_f do modelo (nominal, se houver mistura)")
    tf_natureza: Literal["tabelada_do_elemento", "nominal_regra_das_misturas"]
    tf_rotulo: str
    mistura_base: Optional[Literal["atomica"]] = Field(
        None, description="Base da regra das misturas de α e T_f; nulo quando não há mistura")
    dilatacao_isotropica: bool = Field(..., description="Hipótese imposta pelo modelo (achado T-2)")
    u_natureza: Literal["deslocamento_quadratico_medio_estimado"]
    u_rotulo: str
    lindemann_natureza: Literal["limite_inferior_da_faixa_0_10_a_0_15"]
    curva_dominio: DominioCurva
    alotropia: Optional[FaixaAlotropica] = Field(
        None, description="Nulo com motivo em indisponiveis.alotropia quando o dado não passa pela política")
    hipoteses: List[str] = Field(..., description="Hipóteses do modelo declaradas no resultado")
    indisponiveis: Dict[str, str] = Field(
        default_factory=dict, description="campo → motivo, para cada campo nulo por falta de dado ou de modelo")
    extrapolacao: Dict[str, str] = Field(
        default_factory=dict, description="campo → motivo, para valor devolvido fora do domínio do modelo")
    procedencia: Procedencia


# --------------------------------------------------------------------------- HEA (Fase 6; contrato R1)
BaseComposicao = Literal["atomica", "massica"]
#: Número JSON estrito: inteiro ou real. Texto ("1") e booleano (true) são recusados (contrato R1, V-2).
QuantidadeHea = Annotated[float, Field(strict=True)]


class HeaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [
        {"nome": "CoCrFeNi", "composicao": {"Co": 1, "Cr": 1, "Fe": 1, "Ni": 1}},
        {"nome": "Al0.5CoCrCuFeNi", "composicao": {"Al": 0.5, "Co": 1, "Cr": 1, "Cu": 1, "Fe": 1, "Ni": 1}},
        {"nome": "CoCrFeNi (massa)", "composicao": {"Co": 26.1, "Cr": 23.1, "Fe": 24.8, "Ni": 26.0},
         "base": "massica"},
    ]})
    nome: Optional[str] = Field(None, max_length=80)
    composicao: Dict[str, QuantidadeHea] = Field(
        ..., max_length=12,
        description="{símbolo: quantidade}; 1 a 12 CHAVES (inclui as de quantidade 0). Quantidades são partes "
                    "proporcionais (soma livre), 0 ≤ q ≤ 1e6, conferidas no domínio. Pelo menos 2 elementos com "
                    "quantidade maior que zero. Símbolo de 1 ou 2 letras, normalizado (fe → Fe) e conferido "
                    "contra a tabela periódica.")
    base: BaseComposicao = Field("atomica", description="Base em que as quantidades foram informadas")

    @field_validator("composicao")
    @classmethod
    def _pelo_menos_dois(cls, valor: Dict[str, float]) -> Dict[str, float]:
        # Conta o que não é zero: valores inválidos (negativo, NaN) seguem para o domínio, que devolve o erro próprio.
        if sum(1 for q in valor.values() if q != 0) < 2:
            raise PydanticCustomError("elementos_insuficientes",
                                      "Uma liga precisa de pelo menos 2 elementos com quantidade maior que zero.")
        return valor


class DadoFaltante(BaseModel):
    simbolo: str = Field(..., description='Elemento ("Mn") ou par ("Co-Mn")')
    codigo: Literal["raio_atomico", "temperatura_fusao", "vec", "massa_atomica", "entalpia_mistura_par"]
    situacao: Literal["ausente", "nao_validado"]


class PontoCurvaT(BaseModel):
    T: float = Field(..., description="K")
    menos_TdS: float = Field(..., description="−T·ΔS_mix (analítico), kJ/mol")
    dG: Optional[float] = Field(None, description="ΔH_mix − T·ΔS_mix, kJ/mol; nulo quando ΔH_mix é nulo")


class CriterioDef(BaseModel):
    codigo: str
    grandeza: str = Field(..., description="Nome do campo da resposta: delta, omega, VEC, dS_R")
    operador: Literal["<=", ">=", "<", ">"]
    limiar: float
    unidade: str
    natureza: Literal["empirico", "definicao"]
    fonte: str
    verificada: bool = Field(..., description="Fonte conferida pelo auditor bibliográfico (falso em R1)")


class CriterioAvaliado(CriterioDef):
    valor: Optional[float] = None
    atende: Optional[bool] = Field(None, description="Nulo quando o valor é nulo ou o critério não se aplica")
    aplicavel: bool
    proximo_do_limiar: bool
    motivo: Optional[str] = None


class Triagem(BaseModel):
    estado: Literal["favoravel", "desfavoravel", "inconclusiva"]
    texto: str


class HeaResponse(BaseModel):
    nome: str
    veredito: str = Field(..., description="Repete triagem.texto (compatibilidade); o estado é triagem.estado")
    fase: str
    estrutura_sugerida: Optional[Literal["CS", "CCC", "CFC", "HC"]] = Field(
        None, description="Sempre presente; nulo quando não há sugestão única (motivo em indisponiveis)")
    ductilidade: Optional[str] = None
    dureza: Optional[str] = None
    dureza_indice: Optional[float] = None
    dS: float = Field(..., description="ΔS_mix ideal, J/(mol·K)")
    dH: Optional[float] = Field(None, description="ΔH_mix, kJ/mol — só com todos os pares na matriz de entalpias")
    delta: Optional[float] = Field(None, description="δ, %")
    omega: Optional[float] = None
    VEC: Optional[float] = None
    Tm: Optional[float] = Field(None, description="T_m pela regra das misturas, K")
    comp_percent: Dict[str, float] = Field(..., description="% ATÔMICA, 4 casas; símbolos na forma canônica")
    fracoes: Dict[str, float] = Field(..., description="Fração atômica, sem arredondar")
    interpretacao: List[str]
    fragilidade: Optional[str] = None
    gibbs: List[Dict[str, float]] = Field(
        ..., description="OBSOLETO: [{T (K), G (J/mol)}]. Use curva_T (kJ/mol).",
        json_schema_extra={"deprecated": True})
    indisponiveis: Dict[str, str] = Field(..., description="campo → motivo de não ter sido calculado")
    procedencia: Procedencia
    # --- contrato R1 (seção 1.2) ---
    base_entrada: BaseComposicao
    soma_informada: float = Field(..., description="Soma das quantidades recebidas (> 0), na unidade da entrada")
    fracoes_massa: Optional[Dict[str, float]] = Field(None, description="Fração mássica, sem arredondar")
    comp_massa_pct: Optional[Dict[str, float]] = Field(None, description="% em massa, 4 casas")
    massa_molar_media: Optional[float] = Field(None, description="M̄ = Σ xᵢMᵢ, g/mol")
    dS_R: float = Field(..., description="ΔS_mix/R, adimensional")
    classe_entropia: Literal["baixa", "media", "alta"]
    raio_medio_nm: Optional[float] = Field(None, description="r̄ = Σ xᵢrᵢ, nm")
    pares_faltantes: List[str] = Field(..., description='Pares "A-B" sem entalpia de mistura utilizável')
    dados_faltantes: List[DadoFaltante]
    curva_T: List[PontoCurvaT] = Field(..., description="De 300 K a T_sup_k, passo 50 K")
    T_sup_k: float = Field(..., description="Limite superior da curva, K")
    dG_Tm: Optional[float] = Field(None, description="ΔG_mix do modelo em T_m, kJ/mol")
    T_cruzamento_k: Optional[float] = Field(None, description="T* = 1000·ΔH_mix/ΔS_mix, K; só com ΔH_mix > 0")
    energia_formacao: None = Field(None, description="Sempre nulo: o sistema não calcula energia de formação")
    criterios: List[CriterioAvaliado]
    triagem: Triagem
    vec_aplicavel: bool = Field(..., description="Critério de VEC dentro do domínio (regra conservadora, sem fonte)")
    classes: Dict[str, str] = Field(..., description="Natureza de cada grandeza (valores de procedencia.classe)")


class HeaAlloy(BaseModel):
    nome: str
    grupo: str
    composicao: Dict[str, float]


class HeaElement(BaseModel):
    simbolo: str
    nome: str
    raio_nm: float
    tem_fusao: bool
    tem_vec: bool
    tem_massa: bool = Field(..., description="Há massa utilizável no repositório de materiais neste ambiente")


class ElementoAceito(BaseModel):
    """Símbolo aceito na entrada e o que este ambiente consegue usar dele. Sem valores de propriedade."""

    simbolo: str
    nome: str
    numero_atomico: int
    categoria: str
    tem_raio: bool
    tem_fusao: bool
    tem_vec: bool
    tem_massa: bool


class HeaEntalpias(BaseModel):
    disponivel: bool
    n_pares: int = Field(..., ge=0)
    fonte: Optional[str] = None
    estado: Optional[str] = None


class GuiaEntropia(BaseModel):
    n: int
    dS: float = Field(..., description="R·ln n, J/(mol·K)")
    dS_R: float = Field(..., description="ln n")


class HeaDefinicao(BaseModel):
    codigo: str
    nome: str
    simbolo: str
    unidade: str
    referencia: str
    condicoes: str
    significado: str
    nao_e: str
    natureza: str
    disponivel: bool = Field(..., description="O sistema calcula esta grandeza?")


class HeaReference(BaseModel):
    dS: float
    omega: float
    delta: float
    VEC: float
    dH: Optional[float] = None
    T_padrao: str
    P_padrao: str


class HeaBootstrap(BaseModel):
    elements: Dict[str, HeaElement]
    alloys: Dict[str, HeaAlloy]
    reference: HeaReference = Field(
        ..., description="OBSOLETO: limiares dos critérios (não é liga de referência). Use criterios.",
        json_schema_extra={"deprecated": True})
    samples: List[HeaResponse]
    versao_motor: str
    # --- contrato R1 (seção 1.5) ---
    elementos_aceitos: List[ElementoAceito]
    criterios: List[CriterioDef]
    entalpias: HeaEntalpias
    guias_entropia: List[GuiaEntropia]
    definicoes: List[HeaDefinicao]
    avisos_fixos: List[str]


# --------------------------------------------------------------------------- conta (Fase 8)
_EMAIL = r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$"


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., max_length=254, pattern=_EMAIL)
    senha: str = Field(..., min_length=1, max_length=256, description="mínimo de 10 caracteres; não pode ser comum")


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(..., max_length=254)
    senha: str = Field(..., max_length=256)


class UserInfo(BaseModel):
    id: str
    nome: str
    email: str
    admin_geral: bool
    email_verificado: bool


class SessionInfo(BaseModel):
    usuario: UserInfo
    csrf: str = Field(..., description="Enviar no cabeçalho X-Alloy-CSRF em POST/PUT/PATCH/DELETE")
    expira_em: str


class HistoryItem(BaseModel):
    id: str
    operacao: str
    motor: str
    versao_motor: str
    versao_dados: str
    classe: str
    parametros: Dict[str, Any]
    criado_em: str


class HistoryPage(BaseModel):
    total: int
    pagina: int
    limite: int
    itens: List[HistoryItem]


# --------------------------------------------------------------------------- educacional (Fase 7)
class GeneratorInfo(BaseModel):
    codigo: str
    titulo: str
    topicos: List[str]


class QuestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gerador: str = Field(..., max_length=40)
    instituicao_id: Optional[str] = Field(None, description="vazio = questão pública (só administração geral)")
    titulo: Optional[str] = Field(None, max_length=120)
    enunciado: Optional[str] = Field(None, max_length=2000)
    topicos: Optional[List[str]] = Field(None, max_length=10)
    dificuldade: int = Field(2, ge=1, le=5)
    max_tentativas: int = Field(3, ge=1, le=10)
    publicada: bool = True


class QuestionInfo(BaseModel):
    id: str
    titulo: str
    enunciado: str
    tipo: str
    gerador: Optional[str] = None
    topicos: List[str]
    dificuldade: int
    instituicao_id: Optional[str] = None
    max_tentativas: int
    publicada: bool


class QuestionInstance(BaseModel):
    id: str
    questao_id: str
    titulo: str
    enunciado: str
    parametros: Dict[str, Any]
    unidade: str
    max_tentativas: int
    semente: int


class AttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resposta: NumeroBR = Field(..., allow_inf_nan=False)
    tempo_ms: Optional[int] = Field(None, ge=0, le=3_600_000)


class Gabarito(BaseModel):
    valor: float
    unidade: str
    resolucao: List[str]


class AttemptResult(BaseModel):
    correta: bool
    tentativa: int
    restantes: int
    tipo_erro: Optional[str] = None
    gabarito: Optional[Gabarito] = Field(None, description="só quando acerta ou esgota as tentativas")


class TopicProgress(BaseModel):
    topico: str
    instancias: int
    tentativas: int
    resolvidas: int


class Progress(BaseModel):
    topicos: List[TopicProgress]
    resolvidas: int
    instancias: int


# --------------------------------------------------------------------------- plataforma
class ServicoCapacidade(BaseModel):
    disponivel: bool
    demo_permitido: bool
    versao: Optional[str] = None
    motivo: Optional[str] = None


class Capabilities(BaseModel):
    ambiente: Literal["dev", "test", "prod"]
    crystallography: ServicoCapacidade
    thermodynamics: ServicoCapacidade
    hea: ServicoCapacidade
    ia: ServicoCapacidade
    autenticacao: ServicoCapacidade


class VersionInfo(BaseModel):
    api: str
    motores: Dict[str, str]
    versao_dados: str
