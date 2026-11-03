/**
 * Analisador léxico da linguagem de comandos (docs/gramatica-comandos.md).
 * Tokens: palavra, número, par chave=valor, delimitadores de índices e separadores.
 * Cada token guarda a posição para mensagens de erro que apontam onde corrigir.
 */
export type TokenType = 'word' | 'number' | 'pair' | 'open' | 'close' | 'sep';

export interface Token {
  type: TokenType;
  /** texto original */
  raw: string;
  /** palavra normalizada (sem acentos, minúscula) ou chave do par */
  value: string;
  /** valor do par (texto) */
  pairValue?: string;
  num?: number;
  start: number;
  end: number;
}

const OPEN = '([{<';
const CLOSE = ')]}>';

function normalizeWord(w: string): string {
  return w.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

export function tokenize(input: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  const n = input.length;
  while (i < n) {
    const ch = input.charAt(i);
    if (/\s/.test(ch)) { i += 1; continue; }
    if (OPEN.includes(ch)) { tokens.push({ type: 'open', raw: ch, value: ch, start: i, end: i + 1 }); i += 1; continue; }
    if (CLOSE.includes(ch)) { tokens.push({ type: 'close', raw: ch, value: ch, start: i, end: i + 1 }); i += 1; continue; }
    if (ch === ',' || ch === ';') { tokens.push({ type: 'sep', raw: ch, value: ch, start: i, end: i + 1 }); i += 1; continue; }
    // trecho até espaço ou delimitador
    let j = i;
    while (j < n && !/\s/.test(input.charAt(j)) && !OPEN.includes(input.charAt(j)) && !CLOSE.includes(input.charAt(j)) && input.charAt(j) !== ';') {
      // vírgula dentro de número decimal (0,128) faz parte do número; fora dele é separador
      if (input.charAt(j) === ',' && !(/\d/.test(input.charAt(j - 1)) && /\d/.test(input.charAt(j + 1)) && /[=:]/.test(input.slice(i, j)))) break;
      j += 1;
    }
    const raw = input.slice(i, j);
    const eq = raw.search(/[=:]/);
    if (eq > 0) {
      const key = raw.slice(0, eq);
      const val = raw.slice(eq + 1);
      tokens.push({ type: 'pair', raw, value: key, pairValue: val, start: i, end: j });
    } else if (/^[+-]?\d+(?:[.,]\d+)?$/.test(raw)) {
      tokens.push({ type: 'number', raw, value: raw, num: Number(raw.replace(',', '.')), start: i, end: j });
    } else {
      tokens.push({ type: 'word', raw, value: normalizeWord(raw), start: i, end: j });
    }
    i = j;
  }
  return tokens;
}

/**
 * Índices de Miller a partir dos tokens restantes. Aceita "1 1 1", "(1 1 1)", "[1,1,0]",
 * "111", "1-10", "<110>", "1 0 -1 1". Retorna null se algo não for inteiro.
 */
export function readIndices(tokens: Token[]): { indices: number[]; badToken?: Token } | null {
  const inner = tokens.filter((t) => t.type !== 'open' && t.type !== 'close' && t.type !== 'sep');
  if (!inner.length) return null;
  const compact = /^(?:[+-]?\d){2,4}$/;
  // Sem separadores ("111", "1-10", "-110"): um dígito por índice, como no CrystaLab v1.0.
  if (inner.length === 1) {
    const only = inner[0] as Token;
    if (only.type !== 'pair' && compact.test(only.raw)) return { indices: (only.raw.match(/-?\d/g) ?? []).map(Number) };
  }
  const out: number[] = [];
  for (const t of inner) {
    if (t.type === 'number' && Number.isInteger(t.num)) { out.push(t.num as number); continue; }
    return { indices: out, badToken: t };
  }
  return { indices: out };
}
