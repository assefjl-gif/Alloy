/**
 * Modelo de atividade (6.1). Uma atividade declara objetivo, instruções, dados, critérios de
 * avaliação, explicação conceitual, módulo, tema e nível. Os DADOS numéricos sempre vêm do motor
 * no momento da resolução (nenhum valor fica gravado aqui); a semente só escolhe o material.
 */
import type { Localized } from '../../i18n/index.ts';

export type Topic = 'estruturas' | 'celulas' | 'fea' | 'densidade' | 'miller-planos' | 'miller-direcoes' | 'hea-parametros';
export type Level = 'introdutorio' | 'intermediario' | 'avancado';
export type Format = 'guided' | 'pbl' | 'quiz';
export type ErrorType = 'conceptual' | 'algebraic' | 'unit' | 'input';

export interface Criterion {
  id: string;
  text: Localized;
  /** tolerância relativa aceita na comparação com o motor */
  tolerance?: number;
}

export interface Activity {
  id: string;
  module: 'crystalab' | 'hea';
  topic: Topic;
  level: Level;
  format: Format;
  title: Localized;
  objective: Localized;
  instructions: Localized;
  /** materiais elegíveis (símbolos do catálogo do motor); vazio = fixo ou não se aplica */
  pool: string[];
  fixedMaterial?: string;
  criteria: Criterion[];
  explanation: Localized;
  references: string[];
  /** validação das faixas pelo especialista em materiais (D-17) */
  validation: 'catalog-only' | 'awaiting-specialist';
  /** só com resultados que o preditor HEA efetivamente fornece (6.4) */
  requiresHea?: boolean;
}

export interface Attempt {
  activityId: string;
  topic: Topic;
  step: string;
  correct: boolean;
  errorType?: ErrorType;
  seed: number;
  material?: string;
  at: string;
  demo?: boolean;
}

/**
 * Classifica a resposta do estudante comparando-a com o valor do MOTOR (6.7).
 *  - input: não é número;
 *  - correct: dentro da tolerância;
 *  - unit: difere por potência de 10 (ex.: esqueceu nm → cm);
 *  - conceptual: coincide com uma alternativa conceitualmente errada conhecida (fornecida pelo chamador,
 *    obtida do motor — ex.: mesma densidade calculada com outra estrutura);
 *  - algebraic: caso contrário.
 */
export function classifyAnswer(value: number | null, expected: number, tolerance = 0.01, conceptualAlternatives: number[] = []): { correct: boolean; type?: ErrorType; power?: number } {
  if (value === null || !Number.isFinite(value)) return { correct: false, type: 'input' };
  const close = (a: number, b: number) => b !== 0 && Math.abs(a / b - 1) <= tolerance;
  if (close(value, expected)) return { correct: true };
  for (const alt of conceptualAlternatives) if (close(value, alt)) return { correct: false, type: 'conceptual' };
  if (value !== 0 && expected !== 0) {
    const ratio = value / expected;
    const power = Math.round(Math.log10(Math.abs(ratio)));
    if (power !== 0 && Math.abs(Math.abs(ratio) / 10 ** power - 1) <= tolerance * 2) return { correct: false, type: 'unit', power };
  }
  return { correct: false, type: 'algebraic' };
}
