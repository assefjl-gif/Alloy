/**
 * i18n (2.9) e design system (2.11/7.3): catálogos completos nos três idiomas, marcadores
 * coerentes, nenhuma chave órfã, e contraste WCAG 2.2 AA dos pares de cor usados pelos
 * componentes nos temas claro e escuro.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { listKeys, referenceCatalog, allCatalogs, translate } from '../../src/i18n/index.ts';

const root = fileURLToPath(new URL('../../', import.meta.url));

test('en e es têm todas as chaves do pt-BR, com os mesmos marcadores', () => {
  const ref = listKeys(referenceCatalog);
  for (const loc of ['en', 'es'] as const) {
    const keys = new Set(listKeys(allCatalogs[loc]));
    const missing = ref.filter((k) => !keys.has(k));
    assert.deepEqual(missing, [], `${loc}: faltam ${missing.length} chaves`);
    for (const k of ref) {
      const vars = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(',');
      assert.equal(vars(translate(loc, k as never)), vars(translate('pt-BR', k as never)), `${loc}:${k}`);
    }
  }
});

test('interpolação e recuo para pt-BR', () => {
  assert.equal(translate('en', 'count.atoms', { n: 4 }), '4 atoms');
  assert.equal(translate('pt-BR', 'count.atoms', { n: 4 }), '4 átomos');
});

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => { const p = join(dir, n); return statSync(p).isDirectory() ? walk(p) : [p]; });
}

test('nenhuma chave do catálogo fica sem uso no código', () => {
  const src = walk(join(root, 'src')).filter((f) => /\.(ts|tsx)$/.test(f) && !f.split(sep).join('/').includes('/i18n/locales/')).map((f) => readFileSync(f, 'utf8')).join('\n');
  const unused = listKeys(referenceCatalog).filter((k) => {
    if (src.includes(`'${k}'`) || src.includes(`"${k}"`)) return false;
    const parts = k.split('.');
    // famílias usadas com chave dinâmica: `prefixo.${valor}`
    for (let i = parts.length - 1; i > 0; i -= 1) if (src.includes(`\`${parts.slice(0, i).join('.')}.\${`)) return false;
    return true;
  });
  assert.deepEqual(unused, []);
});

// ---------- Contraste ----------
function block(css: string, selector: string): Record<string, string> {
  const i = css.indexOf(`${selector} {`);
  assert.ok(i >= 0, selector);
  const body = css.slice(i, css.indexOf('\n}', i));
  return Object.fromEntries([...body.matchAll(/(--[\w-]+):\s*([^;]+);/g)].map((m) => [m[1]!, m[2]!.trim()]));
}

function rgb(value: string, vars: Record<string, string>): [number, number, number, number] {
  let v = value;
  for (let n = 0; n < 5 && v.startsWith('var('); n += 1) v = vars[v.slice(4, -1)] ?? v;
  const hex = v.match(/^#([0-9a-f]{6})$/i);
  if (hex) { const h = hex[1]!; return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16), 1]; }
  const m = v.match(/^rgba?\(([^)]+)\)$/);
  if (m) { const p = m[1]!.split(',').map((x) => Number(x.trim())); return [p[0]!, p[1]!, p[2]!, p[3] ?? 1]; }
  throw new Error(`cor não suportada: ${value} → ${v}`);
}

function over(fg: [number, number, number, number], bg: [number, number, number, number]): [number, number, number] {
  const a = fg[3];
  return [fg[0] * a + bg[0] * (1 - a), fg[1] * a + bg[1] * (1 - a), fg[2] * a + bg[2] * (1 - a)];
}

function lum([r, g, b]: [number, number, number]): number {
  const c = (x: number) => { const s = x / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b);
}

export function contrast(fg: string, bg: string, vars: Record<string, string>, base = '--color-bg'): number {
  const b0 = rgb(vars[base]!, vars);
  const bgc = over(rgb(vars[bg] ?? bg, vars), [...b0.slice(0, 3), 1] as [number, number, number, number]);
  const fgc = over(rgb(vars[fg] ?? fg, vars), [...bgc, 1]);
  const [l1, l2] = [lum(fgc), lum(bgc)].sort((a, b) => b - a) as [number, number];
  return (l1 + 0.05) / (l2 + 0.05);
}

const TEXT_PAIRS: Array<[string, string]> = [
  ['--color-ink', '--color-bg'], ['--color-ink', '--color-surface'], ['--color-ink-soft', '--color-surface'],
  ['--color-muted', '--color-bg'], ['--color-muted', '--color-surface'], ['--color-muted', '--color-surface-2'],
  ['--color-accent', '--color-bg'], ['--color-accent', '--color-surface'], ['--color-on-primary', '--color-primary'], ['--color-on-accent', '--color-accent-fill'],
  ['--color-success', '--color-success-bg'], ['--color-warning', '--color-warning-bg'], ['--color-danger', '--color-danger-bg'], ['--color-info', '--color-info-bg'],
  ['--color-danger', '--color-surface'], ['--color-success', '--color-surface'],
  ['--lab-ink', '--lab-bg'], ['--lab-ink', '--lab-surface'], ['--lab-muted', '--lab-bg'], ['--lab-muted', '--lab-surface'], ['--lab-accent', '--lab-bg'],
  ['--term-entry', '--lab-code-bg'], ['--term-ok', '--lab-code-bg'], ['--term-error', '--lab-code-bg'], ['--term-step', '--lab-code-bg'], ['--term-warn', '--lab-code-bg'], ['--term-info', '--lab-code-bg'],
  ['--tag-ink', '--tag-ccc'], ['--tag-ink', '--tag-cfc'], ['--tag-ink', '--tag-hc'], ['--tag-ink', '--tag-cs'], ['--tag-ink', '--tag-gen'],
  ['--cat-result-accent', '--cat-result-bg'], ['--cat-param-accent', '--cat-param-bg'], ['--cat-reference-accent', '--cat-reference-bg'],
  ['--cat-control-accent', '--cat-control-bg'], ['--cat-feedback-accent', '--cat-feedback-bg'], ['--cat-demo-accent', '--cat-demo-bg'], ['--cat-note-accent', '--cat-note-bg'],
  ['--chart-text', '--chart-bg'], ['--color-ink-soft', '--cat-feedback-bg'], ['--color-ink-soft', '--cat-demo-bg'],
];
const NON_TEXT: Array<[string, string]> = [
  ['--chart-axis', '--chart-bg'], ['--chart-series-1', '--chart-bg'], ['--chart-highlight', '--chart-bg'], ['--color-line-strong', '--color-surface'],
];

test('contraste AA (texto ≥ 4,5:1; elementos gráficos ≥ 3:1) nos dois temas', () => {
  const css = readFileSync(join(root, 'src/design-system/tokens.css'), 'utf8');
  const light = { ...block(css, ':root'), ...block(css, ':root[data-theme="light"]') };
  const dark = { ...light, ...block(css, ':root[data-theme="dark"]') };
  const failures: string[] = [];
  for (const [theme, vars] of [['claro', light], ['escuro', dark]] as const) {
    for (const [fg, bg] of TEXT_PAIRS) { const c = contrast(fg, bg, vars); if (c < 4.5) failures.push(`${theme}: ${fg} sobre ${bg} = ${c.toFixed(2)}`); }
    for (const [fg, bg] of NON_TEXT) { const c = contrast(fg, bg, vars); if (c < 3) failures.push(`${theme}: ${fg} sobre ${bg} = ${c.toFixed(2)} (não texto)`); }
  }
  assert.deepEqual(failures, []);
});
