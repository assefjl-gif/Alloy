// Gera src/i18n/locales/{pt-BR,en,es}.ts a partir das tabelas src/i18n/source/*.tsv
// (chave<TAB>pt-BR<TAB>en<TAB>es). Uma linha por mensagem mantém as três línguas lado a lado.
// Verificações: chave duplicada, chave que é folha e ramo ao mesmo tempo, tradução vazia e
// marcadores {var} diferentes entre as línguas. Falha com código 1 em qualquer problema.
import { readFileSync, readdirSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = join(root, 'src/i18n/source');
const outDir = join(root, 'src/i18n/locales');
const LOCALES = ['pt-BR', 'en', 'es'];
// --check: não escreve; falha se os arquivos gerados estiverem desatualizados (usado pelo lint).
const CHECK = process.argv.includes('--check');
const problems = [];
const rows = new Map();

for (const file of readdirSync(srcDir).filter((f) => f.endsWith('.tsv')).sort()) {
  readFileSync(join(srcDir, file), 'utf8').split('\n').forEach((line, i) => {
    if (!line.trim() || line.startsWith('#')) return;
    const cols = line.split('\t');
    const where = `${file}:${i + 1}`;
    if (cols.length !== 4) { problems.push(`${where}: esperava 4 colunas, achou ${cols.length}`); return; }
    const [key, ...texts] = cols;
    if (!/^[a-zA-Z][\w-]*(\.[\w-]+)+$/.test(key)) problems.push(`${where}: chave inválida "${key}"`);
    if (rows.has(key)) problems.push(`${where}: chave duplicada "${key}" (já em ${rows.get(key).where})`);
    texts.forEach((t, j) => { if (!t.trim()) problems.push(`${where}: texto vazio para ${LOCALES[j]} em "${key}"`); });
    const vars = texts.map((t) => [...t.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(','));
    if (vars[1] !== vars[0] || vars[2] !== vars[0]) problems.push(`${where}: marcadores diferentes em "${key}": ${vars.join(' | ')}`);
    rows.set(key, { texts, where });
  });
}

const keys = [...rows.keys()].sort();
for (const k of keys) if (keys.some((o) => o.startsWith(`${k}.`))) problems.push(`"${k}" é folha e ramo ao mesmo tempo`);

if (problems.length) {
  console.error(`i18n: ${problems.length} problema(s)\n  ${problems.join('\n  ')}`);
  process.exit(1);
}

function tree(index) {
  const out = {};
  for (const k of keys) {
    const parts = k.split('.');
    let node = out;
    parts.slice(0, -1).forEach((p) => { node = node[p] ??= {}; });
    node[parts[parts.length - 1]] = rows.get(k).texts[index];
  }
  return out;
}

function emit(obj, indent = 1) {
  const pad = '  '.repeat(indent);
  return `{\n${Object.entries(obj).map(([k, v]) => `${pad}${/^[A-Za-z_$][\w$]*$/.test(k) ? k : JSON.stringify(k)}: ${typeof v === 'string' ? JSON.stringify(v) : emit(v, indent + 1)},`).join('\n')}\n${'  '.repeat(indent - 1)}}`;
}

const outputs = { 'pt-BR.ts': `${header()}const ptBR = ${emit(tree(0))} as const;\n\nexport default ptBR;\n` };
for (const [i, loc] of [[1, 'en'], [2, 'es']]) {
  const name = loc.replace('-', '');
  outputs[`${loc}.ts`] = `${header()}import type ptBR from './pt-BR.ts';\nimport type { DeepPartialMessages } from '../index.ts';\n\nconst ${name}: DeepPartialMessages<typeof ptBR> = ${emit(tree(i))};\n\nexport default ${name};\n`;
}
function header() { return '// ARQUIVO GERADO por scripts/i18n-build.mjs a partir de src/i18n/source/*.tsv — não edite à mão.\n'; }
if (CHECK) {
  const stale = Object.entries(outputs).filter(([f, c]) => !existsSync(join(outDir, f)) || readFileSync(join(outDir, f), 'utf8') !== c).map(([f]) => f);
  if (stale.length) { console.error(`i18n: catálogos desatualizados (${stale.join(', ')}). Rode: node scripts/i18n-build.mjs`); process.exit(1); }
  console.log(`i18n: ${keys.length} chaves × ${LOCALES.length} idiomas — catálogos em dia`);
} else {
  mkdirSync(outDir, { recursive: true });
  for (const [f, c] of Object.entries(outputs)) writeFileSync(join(outDir, f), c);
  console.log(`i18n: ${keys.length} chaves × ${LOCALES.length} idiomas gerados em src/i18n/locales/`);
}
