import { plain } from './text.ts';

/**
 * Busca aproximada simples para a paleta de comandos: subsequência com bônus para
 * início de palavra e sequência contígua. Retorna 0 quando não há correspondência.
 */
export function fuzzyScore(query: string, target: string): number {
  const q = plain(query).replace(/\s+/g, ' ');
  const t = plain(target);
  if (!q) return 1;
  if (t.includes(q)) return 100 + (t.startsWith(q) ? 50 : 0) - t.length * 0.01;
  let score = 0;
  let ti = 0;
  let streak = 0;
  for (const ch of q) {
    if (ch === ' ') continue;
    const found = t.indexOf(ch, ti);
    if (found < 0) return 0;
    streak = found === ti ? streak + 1 : 0;
    score += 1 + streak * 2 + (found === 0 || t[found - 1] === ' ' ? 3 : 0);
    ti = found + 1;
  }
  return score - t.length * 0.01;
}
