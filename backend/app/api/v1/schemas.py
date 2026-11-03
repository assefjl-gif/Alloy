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

from app.engines.crystallography.constantes import (
    FAIXA_A_NM,
    FAIXA_C_A,
    FAIXA_PESO,
    FAIXA_RAIO_NM,
    INDICE_MAXIMO,
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
class SolidSolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [
        {"base": "Cu", "soluto": "Ni", "x": 30},
        {"base": "Fe", "soluto": "C", "x": 2, "distorcer": True},
        {"base": "Cu", "soluto": "Au", "x": 25, "arranjo": "ordenado", "n": 2},
    ]})
    base: str = Field(..., max_length=32, description="Metal solvente")
    soluto: str = Field(..., max_length=32, description="Metal (substitucional) ou C, N, H (intersticial)")
    x: NumeroBR = Field(10.0, ge=0, le=100, allow_inf_nan=False, description="% atômica do soluto")
    n: int = Field(3, ge=1, le=SUPERCELULA_MAXIMA)
    arranjo: Literal["aleatorio", "ordenado"] = "aleatorio"
    distorcer: bool = False
    semente: int = Field(1, ge=0, le=2**31 - 1)


class RegraSolubilidade(BaseModel):
    criterio: str
    valor: Optional[str] = None
    ok: Optional[bool] = Field(None, description="None = indisponível (ver 'indisponivel')")
    detalhe: str
    indisponivel: Optional[str] = None


class AtomoLiga(BaseModel):
    pos: List[float]
    frac: List[float]
    tipo: Literal["rede", "intersticial"]
    elemento: str
    raio_rel: float


class SitioIntersticial(BaseModel):
    nome: str
    fator: float
    raio_nm: float
    nc: int


class Distorcao(BaseModel):
    classe: Literal["simulacao_ilustrativa"]
    descricao: str


class SolidSolutionResponse(BaseModel):
    rotulo: str
    base: str
    soluto: str
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
    n_soluto: int
    n_solvente: int
    fase_ordenada: Optional[str] = None
    nota_arranjo: Optional[str] = None
    sitio: Optional[SitioIntersticial] = None
    regras: List[RegraSolubilidade]
    conclusao: str
    passos: List[DensityStep]
    distorcao: Optional[Distorcao] = None
    atomos: List[AtomoLiga]
    arestas: List[List[List[float]]]
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


class ThermalResponse(BaseModel):
    temperatura_c: float
    temperatura_k: float
    fusao_c: float
    homologa: float
    alfa_1e6_k: float
    fator: float
    a_ref_nm: float
    a_nm: float
    delta_a_pct: float
    densidade: Optional[float] = None
    delta_v_pct: float
    u_nm: float
    razao_lindemann: float
    amplitude_rel: float
    lindemann: float
    fundido: bool
    curva: List[List[float]] = Field(..., description="[T (°C), u/d] de 0 K até T_f + 200 °C")
    notas: List[NotaTermica]
    procedencia: Procedencia


# --------------------------------------------------------------------------- HEA (Fase 6)
class HeaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [
        {"nome": "CoCrFeNi", "composicao": {"Co": 1, "Cr": 1, "Fe": 1, "Ni": 1}},
        {"nome": "Al0.5CoCrCuFeNi", "composicao": {"Al": 0.5, "Co": 1, "Cr": 1, "Cu": 1, "Fe": 1, "Ni": 1}},
    ]})
    nome: Optional[str] = Field(None, max_length=80)
    composicao: Dict[str, float] = Field(..., min_length=2, max_length=12,
                                          description="{elemento: quantidade}; normalizada para frações molares")


class HeaResponse(BaseModel):
    nome: str
    veredito: str
    fase: str
    estrutura_sugerida: Optional[Literal["CS", "CCC", "CFC", "HC"]] = None
    ductilidade: Optional[str] = None
    dureza: Optional[str] = None
    dureza_indice: Optional[float] = None
    dS: float = Field(..., description="ΔS_mix ideal, J/(mol·K)")
    dH: Optional[float] = Field(None, description="ΔH_mix, kJ/mol — indisponível até Q-01")
    delta: Optional[float] = Field(None, description="δ, %")
    omega: Optional[float] = None
    VEC: Optional[float] = None
    Tm: Optional[float] = Field(None, description="T_m pela regra das misturas, K")
    comp_percent: Dict[str, float]
    fracoes: Dict[str, float]
    interpretacao: List[str]
    fragilidade: Optional[str] = None
    gibbs: List[Dict[str, float]]
    indisponiveis: Dict[str, str] = Field(..., description="grandeza → motivo de não ter sido calculada")
    procedencia: Procedencia


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
    reference: HeaReference
    samples: List[HeaResponse]
    versao_motor: str


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
