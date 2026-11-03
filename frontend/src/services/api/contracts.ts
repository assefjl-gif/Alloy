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
}).passthrough();
export type StructureResult = z.infer<typeof StructureResult>;

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

// ------------------------------- HEA (Etapa 5) -------------------------------
/**
 * Contrato do resultado HEA conforme o que a UI v1.17 lê de /api/analyze (o motor
 * hea_engine não está no projeto; ver matriz de dados). Não existe campo de estrutura
 * sugerida; `estrutura_sugerida` é aceito se um dia o motor passar a enviá-lo.
 */
export const GibbsPoint = z.object({ T: z.number(), G: z.number() });
export const HeaResult = z.object({
  nome: z.string(),
  veredito: z.string(),
  fase: z.string(),
  ductilidade: z.string(),
  dureza: z.string(),
  dureza_indice: z.number(),
  dS: z.number(),
  dH: z.number(),
  delta: z.number(),
  omega: z.number(),
  VEC: z.number(),
  Tm: z.number(),
  comp_percent: z.record(z.string(), z.number()),
  interpretacao: z.array(z.string()),
  fragilidade: z.string().nullable().optional(),
  gibbs: z.array(GibbsPoint),
  estrutura_sugerida: StructureCode.optional(),
}).passthrough();
export type HeaResult = z.infer<typeof HeaResult>;

export const HeaAlloy = z.object({ nome: z.string(), grupo: z.string(), composicao: z.record(z.string(), z.number()) }).passthrough();
export type HeaAlloy = z.infer<typeof HeaAlloy>;
export const HeaReference = z.object({ dS: z.number(), omega: z.number(), delta: z.number(), VEC: z.number(), dH: z.number(), T_padrao: z.union([z.string(), z.number()]), P_padrao: z.union([z.string(), z.number()]) }).passthrough();
export type HeaReference = z.infer<typeof HeaReference>;
export const HeaBootstrap = z.object({
  elements: z.unknown(),
  alloys: z.record(z.string(), HeaAlloy),
  reference: HeaReference,
  samples: z.array(HeaResult),
});
export type HeaBootstrap = z.infer<typeof HeaBootstrap>;
