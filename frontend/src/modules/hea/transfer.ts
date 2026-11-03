/**
 * Ponte HEA → CrystaLab (Etapa 5). O resultado do preditor atravessa a fronteira como
 * DADO IMUTÁVEL: cópia profunda congelada, nunca recalculada nem completada.
 *
 * Regra de correspondência (5.2):
 *  1. se o resultado tiver `estrutura_sugerida` → abertura direta (basis = 'predictor-field');
 *  2. senão, se o texto de `fase` citar exatamente UMA estrutura reconhecível (CFC/FCC, CCC/BCC,
 *     HC/HCP, CS/SC) → abertura direta (basis = 'predictor-phase');
 *  3. senão (nenhuma ou várias) → o usuário escolhe; a interface marca "escolha do usuário",
 *     nunca "predição" (basis = 'user-choice').
 */
import type { HeaResult, StructureCode } from '../../services/api/contracts.ts';
import { deepFreeze } from '../../utils/freeze.ts';

export type StructureBasis = 'predictor-field' | 'predictor-phase' | 'user-choice';

export interface HeaTransfer {
  readonly version: 1;
  readonly origin: 'engine' | 'demo';
  readonly seed: number | null;
  readonly receivedAt: string;
  readonly result: Readonly<HeaResult>;
  readonly structure: { readonly code: StructureCode; readonly basis: StructureBasis; readonly phaseText: string };
}

const PATTERNS: Array<[StructureCode, RegExp]> = [
  ['CFC', /\b(CFC|FCC)\b/i],
  ['CCC', /\b(CCC|BCC)\b/i],
  ['HC', /\b(HC|HCP|HEX)\b/i],
  ['CS', /\b(CS|SC)\b/i],
];

export interface StructureMatch {
  code: StructureCode | null;
  candidates: StructureCode[];
  basis: StructureBasis;
}

export function matchStructure(result: Pick<HeaResult, 'fase'> & { estrutura_sugerida?: StructureCode | null | undefined }): StructureMatch {
  if (result.estrutura_sugerida) return { code: result.estrutura_sugerida, candidates: [result.estrutura_sugerida], basis: 'predictor-field' };
  const found = PATTERNS.filter(([, re]) => re.test(result.fase)).map(([code]) => code);
  if (found.length === 1) return { code: found[0] ?? null, candidates: found, basis: 'predictor-phase' };
  return { code: null, candidates: found, basis: 'user-choice' };
}

export function createTransfer(result: HeaResult, origin: 'engine' | 'demo', seed: number | null, userChoice?: StructureCode): HeaTransfer {
  const match = matchStructure(result);
  const code = match.code ?? userChoice;
  if (!code) throw new Error('Estrutura não definida: o preditor não indicou uma estrutura única e o usuário não escolheu.');
  const basis: StructureBasis = match.code ? match.basis : 'user-choice';
  const copy = structuredClone(result) as HeaResult;
  return deepFreeze({
    version: 1 as const,
    origin,
    seed,
    receivedAt: new Date().toISOString(),
    result: copy,
    structure: { code, basis, phaseText: result.fase },
  });
}
