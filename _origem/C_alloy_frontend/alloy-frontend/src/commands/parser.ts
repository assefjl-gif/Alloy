/**
 * Parser da linguagem de comandos. Procura o verbo mais longo que casa com o início
 * da linha (verbos podem ter duas palavras: "calcular densidade") e delega os argumentos
 * à regra do catálogo. Não usa expressões regulares sobre a linha inteira (4.1).
 */
import { tokenize, type Token } from './lexer.ts';
import { specsFor, type CommandSpec, type ParseContext } from './catalog.ts';
import type { ParseResult } from './types.ts';

interface VerbMatch {
  spec: CommandSpec;
  consumed: number;
}

function verbWords(v: string): string[] {
  return v.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().split(/\s+/);
}

export function matchVerb(tokens: Token[], ctx: ParseContext): VerbMatch | null {
  let best: VerbMatch | null = null;
  for (const spec of specsFor(ctx.context)) {
    for (const name of [spec.verb, ...spec.aliases]) {
      const words = verbWords(name);
      if (words.length > tokens.length) continue;
      const okMatch = words.every((w, i) => tokens[i]?.type === 'word' && tokens[i]?.value === w);
      if (okMatch && (!best || words.length > best.consumed)) best = { spec, consumed: words.length };
    }
  }
  return best;
}

export function parseCommand(input: string, ctx: Omit<ParseContext, 'raw'>): ParseResult {
  const raw = input.trim();
  const full: ParseContext = { ...ctx, raw };
  if (!raw) return { ok: false, error: { key: 'cmd.err.empty', hintKey: 'cmd.hint.typeHelp' } };
  const tokens = tokenize(raw);
  const match = matchVerb(tokens, full);
  if (!match) {
    // Atalho do HEA v1.17: uma linha só com pares (ex.: "Fe=20 Ni=20") equivale a "set".
    if (ctx.context === 'hea' && tokens.filter((t) => t.type === 'pair').length >= 2) {
      const set = specsFor('hea').find((s) => s.verb === 'set');
      if (set) return set.parse(tokens, full);
    }
    const first = tokens[0];
    return { ok: false, error: { key: 'cmd.err.unknownCommand', vars: { text: first?.raw ?? raw }, hintKey: 'cmd.hint.typeHelp', position: 0 } };
  }
  return match.spec.parse(tokens.slice(match.consumed), full);
}
