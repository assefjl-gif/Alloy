/**
 * Lógica de EXIBIÇÃO do módulo HEA (R2-FE-01). Nenhuma grandeza científica é calculada aqui:
 * tudo vem do motor (POST /api/v1/hea/analyses e GET /api/v1/hea/bootstrap).
 * Este arquivo só escolhe o que mostrar, em que ordem, e separa o que está indisponível.
 */
import type { CriterionDef, EvaluatedCriterion, HeaResult } from '../../services/api/contracts.ts';

/** Estados de triagem do motor 2.0.0 (contrato R1 §1.2). */
export type TriageTone = 'favoravel' | 'desfavoravel' | 'inconclusiva' | 'desconhecido';

/**
 * Estado da triagem lido SEMPRE de `triagem.estado` — nunca do texto do veredito.
 * Resposta sem `triagem` (backend anterior) ou com estado fora da enumeração vira
 * `desconhecido`: a interface não afirma nem nega estabilidade.
 */
export function triageTone(r: Pick<HeaResult, 'triagem'>): TriageTone {
  const estado = r.triagem?.estado;
  if (estado === 'favoravel' || estado === 'desfavoravel' || estado === 'inconclusiva') return estado;
  return 'desconhecido';
}

/** Texto da triagem; recua para `veredito` (que o contrato manda repetir `triagem.texto`). */
export function triageText(r: Pick<HeaResult, 'triagem' | 'veredito'>): string {
  return r.triagem?.texto ?? r.veredito;
}

export interface CompositionRow {
  element: string;
  /** % atômica (sempre disponível) */
  atPct: number;
  /** % em massa; null quando o motor não pôde converter (motivo em `indisponiveis`) */
  massPct: number | null;
}

/**
 * Composição nas DUAS bases, uma linha por elemento, em ordem decrescente de % atômica.
 * Ausência de `comp_massa_pct` vira `null` (indisponível), nunca 0.
 */
export function compositionRows(r: Pick<HeaResult, 'comp_percent' | 'comp_massa_pct'>): CompositionRow[] {
  const mass = r.comp_massa_pct ?? null;
  return Object.entries(r.comp_percent)
    .map(([element, atPct]) => ({ element, atPct, massPct: mass && element in mass ? (mass[element] as number) : null }))
    .sort((a, b) => b.atPct - a.atPct || a.element.localeCompare(b.element));
}

/** Verdadeiro quando alguma linha tem % em massa: só então a coluna de massa é mostrada. */
export function hasMassBasis(rows: CompositionRow[]): boolean {
  return rows.some((row) => row.massPct !== null);
}

/** Rótulo do critério como o motor o define: "δ ≤ 6,6 %" (limiar e unidade vêm da API). */
export function criterionLabel(c: Pick<CriterionDef, 'grandeza' | 'operador' | 'limiar' | 'unidade'>, fmt: (v: number) => string): string {
  const op = c.operador === '<=' ? '≤' : c.operador === '>=' ? '≥' : c.operador;
  const unit = c.unidade === 'adimensional' ? '' : ` ${c.unidade}`;
  return `${c.grandeza} ${op} ${fmt(c.limiar)}${unit}`;
}

export type CriterionStatus = 'atende' | 'nao_atende' | 'nao_avaliado' | 'fora_do_dominio';

/** Situação de um critério avaliado. Sem valor → não avaliado (o motivo vem da API). */
export function criterionStatus(c: Pick<EvaluatedCriterion, 'atende' | 'aplicavel' | 'valor'>): CriterionStatus {
  if (c.aplicavel === false) return 'fora_do_dominio';
  if (c.atende === null || c.valor === null) return 'nao_avaliado';
  return c.atende ? 'atende' : 'nao_atende';
}

/** Critérios avaliados, se houver; a lista do bootstrap não substitui a avaliação da liga. */
export function evaluatedCriteria(r: Pick<HeaResult, 'criterios'>): EvaluatedCriterion[] {
  return r.criterios ?? [];
}

export interface CurvePoint { T: number; value: number }

export interface CurveSeries {
  /** −T·ΔS_mix (kJ/mol): termo analítico, sempre disponível quando há `curva_T` */
  entropyTerm: CurvePoint[];
  /** ΔG_mix do modelo (kJ/mol): só quando TODOS os pontos têm valor */
  gibbs: CurvePoint[];
  /** motivo de `gibbs` estar vazia, quando o motor o informou */
  gibbsUnavailable: string | null;
  tMax: number | null;
}

/**
 * Séries do gráfico G-A a partir de `curva_T`. A curva de ΔG só entra quando o motor devolveu
 * valor em TODOS os pontos: curva parcial ou ausente aparece como indisponível com a causa,
 * nunca como curva demonstrativa.
 */
export function curveSeries(r: Pick<HeaResult, 'curva_T' | 'T_sup_k' | 'indisponiveis'>): CurveSeries {
  const points = r.curva_T ?? [];
  const entropyTerm = points.map((p) => ({ T: p.T, value: p.menos_TdS }));
  const complete = points.length > 0 && points.every((p) => p.dG !== null);
  const gibbs = complete ? points.map((p) => ({ T: p.T, value: p.dG as number })) : [];
  const motivo = r.indisponiveis?.['dG_Tm'] ?? r.indisponiveis?.['dH'] ?? r.indisponiveis?.['gibbs'] ?? null;
  return {
    entropyTerm,
    gibbs,
    gibbsUnavailable: complete ? null : motivo,
    tMax: r.T_sup_k ?? (points.length ? (points[points.length - 1] as { T: number }).T : null),
  };
}

export interface DeltaVecPoint { name: string; delta: number; vec: number; selected: boolean }

/**
 * Pontos do gráfico G-B (δ × VEC): só ligas com os DOIS valores disponíveis. A liga analisada
 * entra por último (desenhada em destaque) e não é duplicada quando também está nas amostras.
 */
export function deltaVecPoints(samples: HeaResult[], selected: HeaResult): DeltaVecPoint[] {
  const usable = (s: HeaResult): boolean => s.delta !== null && s.VEC !== null;
  const others = samples
    .filter((s) => s.nome !== selected.nome && usable(s))
    .map((s) => ({ name: s.nome, delta: s.delta as number, vec: s.VEC as number, selected: false }));
  if (!usable(selected)) return others;
  return [...others, { name: selected.nome, delta: selected.delta as number, vec: selected.VEC as number, selected: true }];
}

/** Faixas de critério para desenhar nos eixos do gráfico, pela grandeza. Nunca fixas no front. */
export function criteriaFor(criteria: CriterionDef[], grandeza: string): CriterionDef[] {
  return criteria.filter((c) => c.grandeza === grandeza);
}
