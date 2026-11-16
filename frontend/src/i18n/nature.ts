/**
 * Vocabulário de NATUREZA do resultado (`procedencia.classe` e `classes` da API): rótulo legível
 * para cada valor que o motor emite. Nenhuma tradução é inventada para valor desconhecido: o
 * próprio texto do motor é exibido, para a interface nunca afirmar mais do que a API diz.
 */
import type { MessageKey } from './index.ts';

export const NATURE_CODES = ['analitico', 'estimativa_modelo', 'experimental', 'simulacao_ilustrativa', 'demonstrativo', 'empirico', 'definicao'] as const;

/** Rótulo da natureza; valor fora do vocabulário conhecido volta como veio do motor. */
export function natureLabel(t: (key: MessageKey) => string, code: string | null | undefined): string {
  if (!code) return '—';
  return (NATURE_CODES as readonly string[]).includes(code) ? t(`nature.${code}` as MessageKey) : code;
}
