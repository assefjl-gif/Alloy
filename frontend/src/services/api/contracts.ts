/**
 * Contratos de tempo de execução (zod) das respostas da API unificada. A fonte da verdade é
 * docs/openapi.json (gerado do backend); os tipos estáticos gerados dele ficam em
 * openapi.gen.ts (`npm run types:api`). O teste de contrato do backend
 * (backend/tests/contract) valida respostas REAIS contra estes esquemas a cada execução.
 * Campos extras são preservados (passthrough) para que adições aditivas não quebrem o front.
 */
import { z } from 'zod';

export const Vec3 = z.tuple([z.number(), z.number(), z.number()]);
export type Vec3 = z.infer<typeof Vec3>;

export const StructureCode = z.enum(['CS', 'CCC', 'CFC', 'HC']);
export type StructureCode = z.infer<typeof StructureCode>;
export const STRUCTURE_CODES: readonly StructureCode[] = ['CS', 'CCC', 'CFC', 'HC'];

export const SiteType = z.enum(['vertice', 'centro', 'face', 'basal', 'interior']);
export type SiteType = z.infer<typeof SiteType>;

export const Atom = z.object({
  pos: Vec3,
  tipo: SiteType,
  fracao: z.number(),
  fracao_txt: z.string(),
}).passthrough();
export type Atom = z.infer<typeof Atom>;

export const AtomGroup = z.object({
  tipo: SiteType,
  rotulo: z.string(),
  quantidade: z.number().int(),
  fracao: z.number(),
  fracao_txt: z.string(),
  contribuicao: z.number(),
});

export const DensityStep = z.object({ titulo: z.string(), formula: z.string(), detalhe: z.string().optional().nullable() });
export type DensityStep = z.infer<typeof DensityStep>;

/** Sítio da base cristalográfica (v1.1.0: coordenadas fracionárias reais). */
export const BaseSite = z.object({ frac: Vec3.optional(), pos: Vec3.optional(), tipo: z.string().optional(), wyckoff: z.string().optional() }).passthrough();

export const StructureResult = z.object({
  rotulo: z.string(),
  simbolo: z.string().nullable(),
  nome_metal: z.string().nullable(),
  editado: z.boolean(),
  generica: z.boolean(),
  estrutura: StructureCode,
  estrutura_nome: z.string(),
  relacao_a: z.string(),
  contato: z.string(),
  n: z.number().int(),
  nc: z.number().int(),
  fea: z.number(),
  vazios: z.number(),
  a_em_R: z.number(),
  c_a: z.number().nullable(),
  raio_nm: z.number().nullable(),
  peso: z.number().nullable(),
  a_nm: z.number().nullable(),
  c_nm: z.number().nullable(),
  volume_nm3: z.number().nullable(),
  volume_cm3: z.number().nullable(),
  densidade: z.number().nullable(),
  densidade_exp: z.number().nullable(),
  erro_percent: z.number().nullable(),
  raio_relativo: z.number(),
  atomos: z.array(Atom),
  arestas: z.array(z.tuple([Vec3, Vec3])),
  contagem: z.array(AtomGroup),
  passos_densidade: z.array(DensityStep),
  interpretacao: z.array(z.string()),
  // ---- campos aditivos da v1.1.0 (opcionais) ----
  base: z.array(BaseSite).optional(),
  z: z.number().optional(),
  grupo_espacial: z.unknown().optional(),
  a_fonte: z.string().optional().nullable(),
  avisos: z.array(z.string()).optional(),
  fonte: z.unknown().optional(),
  // ---- campos aditivos do motor de cristalografia 2.1.0 (contrato R1 §3) ----
  // O FEA é propriedade do MODELO de esferas rígidas, não empacotamento medido. Os campos de HC
  // são nulos nas estruturas cúbicas ("não se aplica", sem motivo em `indisponiveis`).
  fea_modelo: z.string().optional(),
  raio_contato_rel: z.number().nullable().optional(),
  contato_tipo: z.string().nullable().optional(),
  c_a_ideal: z.number().nullable().optional(),
  c_a_natureza: z.string().nullable().optional(),
  vizinhos: z.array(z.object({
    grupo: z.string(),
    n: z.number().int(),
    d_rel: z.number(),
    d_nm: z.number().nullable(),
  }).passthrough()).nullable().optional(),
  nc_txt: z.string().optional(),
}).passthrough();
export type StructureResult = z.infer<typeof StructureResult>;
export type NeighbourGroup = NonNullable<StructureResult['vizinhos']>[number];

export const MillerPlane = z.object({
  tipo: z.literal('plano'),
  estrutura: StructureCode,
  indices: z.array(z.number().int()),
  notacao: z.string(),
  notacao_alternativa: z.string().nullable().optional(),
  poligono: z.array(Vec3),
  centro: Vec3,
  normal: Vec3,
  area_rel: z.number(),
  area_nm2: z.number().nullable().optional(),
  d_rel: z.number(),
  d_nm: z.number().nullable().optional(),
  atomos: z.array(z.number().int()),
  ordem: z.number().optional(),
  indices_reduzidos: z.array(z.number()).optional(),
  avisos: z.array(z.string()).optional(),
}).passthrough();
export type MillerPlane = z.infer<typeof MillerPlane>;

export const MillerDirection = z.object({
  tipo: z.literal('direcao'),
  estrutura: StructureCode,
  indices: z.array(z.number().int()),
  notacao: z.string(),
  notacao_alternativa: z.string().nullable().optional(),
  inicio: Vec3,
  fim: Vec3,
  comprimento_rel: z.number(),
  comprimento_nm: z.number().nullable().optional(),
  atomos_contados: z.number().nullable().optional(),
  densidade_linear_rel: z.number().nullable().optional(),
  densidade_linear_nm: z.number().nullable().optional(),
  atomos: z.array(z.number().int()),
  ordem: z.number().optional(),
  indices_reduzidos: z.array(z.number()).optional(),
  avisos: z.array(z.string()).optional(),
}).passthrough();
export type MillerDirection = z.infer<typeof MillerDirection>;

export const MillerResult = z.discriminatedUnion('tipo', [MillerPlane, MillerDirection]);
export type MillerResult = z.infer<typeof MillerResult>;

export const StructureRow = z.object({ sigla: StructureCode, nome: z.string(), n: z.number(), nc: z.number(), a_em_R: z.number(), relacao: z.string(), fea: z.number() });
export type StructureRow = z.infer<typeof StructureRow>;
export const StructureTable = z.array(StructureRow);

export const MetalInfo = z.object({
  nome: z.string(),
  estrutura: StructureCode,
  raio: z.number(),
  peso: z.number(),
  densidade_exp: z.number(),
  c_a: z.number().nullable().optional(),
  nc: z.number(),
}).passthrough();
export type MetalInfo = z.infer<typeof MetalInfo>;
export const MetalTable = z.record(z.string(), MetalInfo);
export type MetalTable = z.infer<typeof MetalTable>;

export const ExportFile = z.object({ formato: z.enum(['cif', 'xyz']), filename: z.string(), content: z.string(), content_type: z.string() });
export type ExportFile = z.infer<typeof ExportFile>;

/** Requisição de estrutura — mesma forma aceita por /api/estrutura e /v1/crystals/structure. */
export interface StructureRequest {
  nome?: string;
  estrutura?: StructureCode;
  raio?: number;
  peso?: number;
  c_a?: number;
}

export interface MillerRequest {
  estrutura: StructureCode;
  tipo: 'plano' | 'direcao';
  indices: number[];
  a_nm?: number | null;
  c_a?: number | null;
}

// ------------------------------- Ligas e temperatura (T-13) -------------------------------
/** Bloco de procedência devolvido pela API em todo resultado científico (docs/API.md §1.5). */
export const Provenance = z.object({
  classe: z.string(),
  motor: z.string(),
  versao_motor: z.string(),
  versao_dados: z.string(),
  fontes_modelo: z.array(z.string()),
  fontes_dados: z.array(z.string()),
  avisos: z.array(z.string()),
  calculado_em: z.string().optional().nullable(),
}).passthrough();
export type Provenance = z.infer<typeof Provenance>;

// ------------------------------- HEA (Etapa 5) -------------------------------
/**
 * Contrato do resultado HEA da API unificada (POST /api/v1/hea/analyses). Grandezas sem base
 * citável (ΔH_mix, Ω; e, em produção, as que dependem de dados não validados) chegam como null,
 * com o motivo em `indisponiveis` — a UI mostra "—" e o motivo, nunca um valor estimado.
 */
export const GibbsPoint = z.object({ T: z.number(), G: z.number() });

/** Base em que a composição foi informada/devolvida (contrato R1 §0: vocabulário único). */
export const CompositionBasis = z.enum(['atomica', 'massica']);
export type CompositionBasis = z.infer<typeof CompositionBasis>;

/**
 * Dado que faltou para um elemento ou para um par (contrato R1 §1.2 `DadoFaltante`).
 * `codigo` e `situacao` ficam como texto livre: valor novo no motor não pode invalidar a resposta.
 */
export const MissingDatum = z.object({
  simbolo: z.string(),
  codigo: z.string(),
  situacao: z.string(),
}).passthrough();
export type MissingDatum = z.infer<typeof MissingDatum>;

/** Ponto da curva de temperatura (R1 §1.2 `PontoCurvaT`). `dG` nulo = depende de ΔH_mix indisponível. */
export const CurveTPoint = z.object({
  T: z.number(),
  menos_TdS: z.number(),
  dG: z.number().nullable(),
}).passthrough();
export type CurveTPoint = z.infer<typeof CurveTPoint>;

/**
 * Definição de critério empírico vinda do bootstrap (R1 §1.5 `CriterioDef`): limiar, unidade,
 * natureza e FONTE. `verificada` falsa = a fonte não foi conferida; a interface precisa dizê-lo.
 * Nenhum limiar científico é escrito no front: todos vêm daqui.
 */
export const CriterionDef = z.object({
  codigo: z.string(),
  grandeza: z.string(),
  operador: z.string(),
  limiar: z.number(),
  unidade: z.string(),
  natureza: z.string(),
  fonte: z.string(),
  verificada: z.boolean(),
}).passthrough();
export type CriterionDef = z.infer<typeof CriterionDef>;

/** Critério já avaliado para a liga analisada (R1 §1.2 `CriterioAvaliado`). */
export const EvaluatedCriterion = CriterionDef.extend({
  valor: z.number().nullable(),
  atende: z.boolean().nullable(),
  aplicavel: z.boolean(),
  proximo_do_limiar: z.boolean(),
  motivo: z.string().nullable(),
}).passthrough();
export type EvaluatedCriterion = z.infer<typeof EvaluatedCriterion>;

/**
 * Triagem empírica (R1 §1.2): `estado` ∈ favoravel | desfavoravel | inconclusiva. O estado é lido
 * SEMPRE daqui, nunca do texto (o motor 2.0.0 não emite mais a palavra "ESTÁVEL").
 * Fica como texto livre para que um estado novo não invalide a resposta: a interface trata o
 * desconhecido como "não classificado", sem afirmar estabilidade.
 */
export const Triage = z.object({ estado: z.string(), texto: z.string() }).passthrough();
export type Triage = z.infer<typeof Triage>;

export const HeaResult = z.object({
  nome: z.string(),
  veredito: z.string(),
  fase: z.string(),
  ductilidade: z.string().nullable(),
  dureza: z.string().nullable(),
  dureza_indice: z.number().nullable(),
  dS: z.number(),
  // null = grandeza sem base citável neste ambiente (o motivo vem em `indisponiveis`).
  dH: z.number().nullable(),
  delta: z.number().nullable(),
  omega: z.number().nullable(),
  VEC: z.number().nullable(),
  Tm: z.number().nullable(),
  comp_percent: z.record(z.string(), z.number()),
  interpretacao: z.array(z.string()),
  fragilidade: z.string().nullable().optional(),
  /** @deprecated motor HEA 2.0.0: substituído por `curva_T` (kJ/mol). Mantido por compatibilidade. */
  gibbs: z.array(GibbsPoint),
  estrutura_sugerida: StructureCode.nullable().optional(),
  indisponiveis: z.record(z.string(), z.string()).optional(),
  // ---- campos aditivos do motor HEA 2.0.0 (contrato R1 §1.2) ----
  // Opcionais só para o front continuar funcionando contra um backend anterior; ausência NUNCA
  // é lida como zero: a interface mostra "indisponível" (e o motivo, quando houver).
  base_entrada: CompositionBasis.optional(),
  soma_informada: z.number().optional(),
  fracoes: z.record(z.string(), z.number()).optional(),
  fracoes_massa: z.record(z.string(), z.number()).nullable().optional(),
  comp_massa_pct: z.record(z.string(), z.number()).nullable().optional(),
  massa_molar_media: z.number().nullable().optional(),
  dS_R: z.number().optional(),
  classe_entropia: z.string().optional(),
  raio_medio_nm: z.number().nullable().optional(),
  pares_faltantes: z.array(z.string()).optional(),
  dados_faltantes: z.array(MissingDatum).optional(),
  curva_T: z.array(CurveTPoint).optional(),
  T_sup_k: z.number().optional(),
  dG_Tm: z.number().nullable().optional(),
  T_cruzamento_k: z.number().nullable().optional(),
  /** Sempre nulo em R1: o sistema não calcula energia de formação (motivo em `indisponiveis`). */
  energia_formacao: z.number().nullable().optional(),
  criterios: z.array(EvaluatedCriterion).optional(),
  triagem: Triage.optional(),
  vec_aplicavel: z.boolean().optional(),
  classes: z.record(z.string(), z.string()).optional(),
  procedencia: Provenance.optional(),
}).passthrough();
export type HeaResult = z.infer<typeof HeaResult>;

export const HeaAlloy = z.object({ nome: z.string(), grupo: z.string(), composicao: z.record(z.string(), z.number()) }).passthrough();
export type HeaAlloy = z.infer<typeof HeaAlloy>;
export const HeaReference = z.object({ dS: z.number(), omega: z.number(), delta: z.number(), VEC: z.number(), dH: z.number().nullable(), T_padrao: z.union([z.string(), z.number()]), P_padrao: z.union([z.string(), z.number()]) }).passthrough();
export type HeaReference = z.infer<typeof HeaReference>;
/** Elemento aceito na entrada (R1 §1.5 `ElementoAceito`): identidade e que dados existem. */
export const AcceptedElement = z.object({
  simbolo: z.string(),
  nome: z.string(),
  numero_atomico: z.number().int(),
  categoria: z.string(),
  tem_raio: z.boolean(),
  tem_fusao: z.boolean(),
  tem_vec: z.boolean(),
  tem_massa: z.boolean(),
}).passthrough();
export type AcceptedElement = z.infer<typeof AcceptedElement>;

/** Verbete do glossário do HEA (R1 §1.5 `Definicao`). */
export const HeaDefinition = z.object({
  codigo: z.string(),
  nome: z.string(),
  simbolo: z.string(),
  unidade: z.string(),
  referencia: z.string(),
  condicoes: z.string(),
  significado: z.string(),
  nao_e: z.string(),
  natureza: z.string(),
  disponivel: z.boolean(),
}).passthrough();
export type HeaDefinition = z.infer<typeof HeaDefinition>;

/** Guia de ΔS_mix da liga equimolar de n elementos (R1 §1.5, G-A): nunca calculado no front. */
export const EntropyGuide = z.object({ n: z.number().int(), dS: z.number(), dS_R: z.number() }).passthrough();
export type EntropyGuide = z.infer<typeof EntropyGuide>;

/** `.passthrough()` em vez de objeto simples: campo novo do contrato não pode ser descartado. */
export const HeaBootstrap = z.object({
  elements: z.unknown(),
  alloys: z.record(z.string(), HeaAlloy),
  /** @deprecated R1 §1.5: deixa de ser exibido como "liga de referência"; use `criterios`. */
  reference: HeaReference,
  samples: z.array(HeaResult),
  // ---- campos aditivos do motor HEA 2.0.0 (contrato R1 §1.5) ----
  versao_motor: z.string().optional(),
  elementos_aceitos: z.array(AcceptedElement).optional(),
  criterios: z.array(CriterionDef).optional(),
  entalpias: z.object({
    disponivel: z.boolean(),
    n_pares: z.number().int(),
    fonte: z.string().nullable(),
    estado: z.string().nullable(),
  }).passthrough().optional(),
  guias_entropia: z.array(EntropyGuide).optional(),
  definicoes: z.array(HeaDefinition).optional(),
  avisos_fixos: z.array(z.string()).optional(),
}).passthrough();
export type HeaBootstrap = z.infer<typeof HeaBootstrap>;

/** Sítio ocupado por um átomo (R1 §2.3). `nc` é inteiro; o texto ("2 + 4") vai em `nc_txt`. */
export const AtomSite = z.object({
  nome: z.string(),
  wyckoff: z.string().nullable().optional(),
  nc: z.number().optional(),
  nc_txt: z.string().optional(),
}).passthrough();
export type AtomSite = z.infer<typeof AtomSite>;

/**
 * Átomo da liga (R1 §2.3). `.passthrough()` em vez de objeto simples: sem os campos novos o front
 * não distingue imagem periódica de átomo único. `imagem: true` NUNCA entra em contagem ou legenda.
 */
export const AlloyAtom = z.object({
  pos: Vec3,
  frac: Vec3,
  tipo: z.enum(['rede', 'intersticial']),
  elemento: z.string(),
  /** raio de DESENHO (raio tabelado do elemento puro / a), não raio do átomo em solução */
  raio_rel: z.number(),
  // ---- campos aditivos do motor de cristalografia 2.1.0 ----
  id: z.string().optional(),
  imagem: z.boolean().optional(),
  imagem_de: z.string().nullable().optional(),
  pos_nm: Vec3.optional(),
  celula: z.tuple([z.number(), z.number(), z.number()]).optional(),
  frac_celula: Vec3.optional(),
  ocupacao: z.string().optional(),
  sitio: AtomSite.optional(),
  fase: z.string().optional(),
  pos_ideal: Vec3.nullable().optional(),
}).passthrough();
export type AlloyAtom = z.infer<typeof AlloyAtom>;

/** Componente da composição solicitada ou representada (R1 §2.2). */
export const AlloyComponent = z.object({
  elemento: z.string(),
  papel: z.string(),
  at_pct: z.number(),
  massa_pct: z.number().nullable(),
  /** átomos ÚNICOS (só na composição representada; pode ser 0) */
  n_atomos: z.number().optional(),
}).passthrough();
export type AlloyComponent = z.infer<typeof AlloyComponent>;

/** Composição solicitada × efetivamente representada na supercélula (R1 §2.2 `ComposicaoLiga`). */
export const AlloyComposition = z.object({
  base_entrada: CompositionBasis,
  solicitada: z.array(AlloyComponent),
  representada: z.array(AlloyComponent),
  n_sitios_rede: z.number().int(),
  n_intersticiais: z.number().int(),
  n_atomos_unicos: z.number().int(),
  /** esferas em `atomos` (únicos + imagens periódicas) */
  n_desenhados: z.number().int(),
  resolucao_at_pct: z.number(),
  desvio_maximo_at_pct: z.number(),
}).passthrough();
export type AlloyComposition = z.infer<typeof AlloyComposition>;

/** Natureza estatística do arranjo desenhado (R1 §2.2 `Realizacao`). */
export const AlloyRealization = z.object({
  tipo: z.string(),
  semente: z.number(),
  algoritmo: z.string(),
  n: z.number().int(),
  aviso: z.string(),
}).passthrough();
export type AlloyRealization = z.infer<typeof AlloyRealization>;

/** Rótulos de natureza do modelo (R1 §2.2 `ModeloLiga`): idealizado × medido. */
export const AlloyModel = z.object({
  tipo_solucao: z.string(),
  ordenacao: z.string(),
  fases: z.string(),
  geometria: z.string(),
  parametro_rede: z.string(),
  parametro_rede_solvente: z.string(),
  c_a: z.string().nullable(),
  hipoteses: z.array(z.string()),
}).passthrough();
export type AlloyModel = z.infer<typeof AlloyModel>;

/** Fase desenhada (R1 §2.2 `FaseLiga`). `fracao` é sempre nula em R1: não há equilíbrio de fases. */
export const AlloyPhase = z.object({
  id: z.string(),
  nome: z.string(),
  estrutura: StructureCode,
  origem: z.string(),
  composicao: z.array(AlloyComponent),
  fracao: z.number().nullable(),
  fracao_motivo: z.string().nullable().optional(),
}).passthrough();
export type AlloyPhase = z.infer<typeof AlloyPhase>;

/** O que o motor NÃO verifica (R1 §2.2 `Verificacoes`). */
export const AlloyChecks = z.object({
  limite_solubilidade: z.object({ verificado: z.boolean(), valor: z.number().nullable(), motivo: z.string() }).passthrough(),
  fases_secundarias: z.object({ previstas: z.unknown().nullable(), motivo: z.string() }).passthrough(),
}).passthrough();
export type AlloyChecks = z.infer<typeof AlloyChecks>;

/** Propriedades TABELADAS do elemento puro (R1 §2.2 `ElementoPuro`) — não do átomo na liga. */
export const PureElement = z.object({
  simbolo: z.string(),
  papel: z.string(),
  raio_nm: z.number().nullable(),
  massa_g_mol: z.number().nullable(),
  estrutura_elemento_puro: z.string().nullable(),
  estado_do_dado: z.string(),
  fonte: z.string().nullable(),
}).passthrough();
export type PureElement = z.infer<typeof PureElement>;

/** Sítio intersticial usado (R1 §2.2 `SitioIntersticial`), com os campos novos. */
export const InterstitialSite = z.object({
  nome: z.string(),
  fator: z.number(),
  raio_nm: z.number(),
  nc: z.number(),
  elemento: z.string().optional(),
  tipo: z.string().optional(),
  nc_txt: z.string().optional(),
  sitios_por_celula: z.number().optional(),
  wyckoff: z.string().nullable().optional(),
  escolha: z.string().optional(),
  justificativa: z.string().optional(),
  padrao_verificado: z.boolean().optional(),
}).passthrough();
export type InterstitialSite = z.infer<typeof InterstitialSite>;

export const SolubilityRule = z.object({
  criterio: z.string(),
  valor: z.string().nullable().optional(),
  ok: z.boolean().nullable().optional(),
  detalhe: z.string(),
  indisponivel: z.string().nullable().optional(),
});
export type SolubilityRule = z.infer<typeof SolubilityRule>;

export const AlloyResult = z.object({
  rotulo: z.string(),
  base: z.string(),
  soluto: z.string(),
  intersticial: z.boolean(),
  estrutura: StructureCode,
  estrutura_nome: z.string(),
  nc: z.number(),
  supercelula: z.number(),
  semente: z.number(),
  x_pct: z.number(),
  pct_peso: z.number(),
  a_nm: z.number(),
  a_base_nm: z.number(),
  raio_relativo: z.number(),
  densidade: z.number(),
  densidade_base: z.number(),
  n_soluto: z.number(),
  n_solvente: z.number(),
  fase_ordenada: z.string().nullable().optional(),
  nota_arranjo: z.string().nullable().optional(),
  /** escalar legado: com mais de um soluto refere-se ao PRIMEIRO da ordem canônica (R1 §2.2) */
  sitio: InterstitialSite.nullable().optional(),
  regras: z.array(SolubilityRule),
  conclusao: z.string(),
  passos: z.array(DensityStep),
  distorcao: z.object({ classe: z.string(), descricao: z.string() }).nullable().optional(),
  atomos: z.array(AlloyAtom),
  arestas: z.array(z.array(Vec3)),
  procedencia: Provenance,
  // ---- campos aditivos do motor de cristalografia 2.1.0 (contrato R1 §2.2) ----
  composicao: AlloyComposition.optional(),
  realizacao: AlloyRealization.optional(),
  modelo: AlloyModel.optional(),
  prototipo: z.object({
    strukturbericht: z.string(),
    prototipo: z.string(),
    rede_ordenada: z.string(),
    observacao: z.string().nullable().optional(),
    composicao_ideal_at_pct: z.record(z.string(), z.number()),
  }).passthrough().nullable().optional(),
  fases: z.array(AlloyPhase).optional(),
  verificacoes: AlloyChecks.optional(),
  regras_por_soluto: z.array(z.object({
    soluto: z.string(),
    modo: z.string(),
    regras: z.array(SolubilityRule),
    conclusao: z.string(),
  }).passthrough()).optional(),
  /** nulo com mais de um soluto: as regras são binárias (motivo em `indisponiveis`) */
  conclusao_global: z.string().nullable().optional(),
  sitios: z.array(InterstitialSite).optional(),
  elementos: z.array(PureElement).optional(),
  convencoes: z.array(z.string()).optional(),
  indisponiveis: z.record(z.string(), z.string()).optional(),
}).passthrough();
export type AlloyResult = z.infer<typeof AlloyResult>;

/** Soluto do pedido multicomponente (R1 §2.1 `SolutoPedido`). */
export interface AlloySolute {
  elemento: string;
  x: number;
  modo?: 'auto' | 'substitucional' | 'intersticial';
  sitio?: 'auto' | 'octaedrico' | 'tetraedrico' | 'cubico';
}

/**
 * Resultado térmico (motor 2.0.0). Acima da T_f do modelo não há ordem cristalina de longo alcance,
 * então `fator`, `a_nm`, `delta_a_pct`, `delta_v_pct` e `densidade` voltam NULOS, com a causa em
 * `indisponiveis` (achado T-1 do parecer de termodinâmica). A tela deve mostrar a causa, nunca um zero.
 */
export const ThermalResult = z.object({
  temperatura_c: z.number(),
  temperatura_k: z.number(),
  fusao_c: z.number(),
  homologa: z.number(),
  alfa_1e6_k: z.number(),
  fator: z.number().nullable(),
  a_ref_nm: z.number(),
  a_nm: z.number().nullable(),
  delta_a_pct: z.number().nullable(),
  densidade: z.number().nullable().optional(),
  delta_v_pct: z.number().nullable(),
  u_nm: z.number(),
  razao_lindemann: z.number(),
  amplitude_rel: z.number(),
  lindemann: z.number(),
  fundido: z.boolean(),
  curva: z.array(z.tuple([z.number(), z.number()])),
  notas: z.array(z.object({
    tipo: z.enum(['info', 'alerta']),
    texto: z.string(),
    fonte: z.string().nullable().optional(),
  })),
  /** T >= T_f do modelo (nominal, quando há mistura). Distinto de `fundido` (achado T-6). */
  acima_da_tf_nominal: z.boolean().optional(),
  tf_natureza: z.enum(['tabelada_do_elemento', 'nominal_regra_das_misturas']).optional(),
  tf_rotulo: z.string().optional(),
  u_rotulo: z.string().optional(),
  dilatacao_isotropica: z.boolean().optional(),
  hipoteses: z.array(z.string()).optional(),
  /** Domínio do modelo para a curva: de 100 K até a T_f do modelo. */
  curva_dominio: z.object({
    de_c: z.number(),
    ate_c: z.number(),
    limite_inferior: z.string(),
    limite_superior: z.string(),
  }).optional(),
  /** campo -> motivo, para cada campo nulo por falta de dado ou de modelo. */
  indisponiveis: z.record(z.string(), z.string()).optional(),
  /** campo -> motivo, para valor devolvido fora do domínio do modelo. */
  extrapolacao: z.record(z.string(), z.string()).optional(),
  procedencia: Provenance,
}).passthrough();
export type ThermalResult = z.infer<typeof ThermalResult>;

/**
 * Pedido de solução sólida (R1 §2.1). Forma binária legada (`soluto` + `x`) OU multicomponente
 * (`solutos`, 1 a 6 itens) — exatamente uma das duas; as duas juntas são recusadas com 422.
 */
export interface AlloyRequest {
  base: string;
  soluto?: string;
  x?: number;
  solutos?: AlloySolute[];
  base_composicao?: CompositionBasis;
  estrutura_matriz?: StructureCode;
  n?: number;
  arranjo?: 'aleatorio' | 'ordenado';
  distorcer?: boolean;
  semente?: number;
}

export type ThermalRequest =
  | { material: string; temperatura_c: number }
  | { liga: AlloyRequest; temperatura_c: number };
