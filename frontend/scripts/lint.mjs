// Lint do projeto (ESLint não pôde ser instalado — registro D-19). Regras que protegem as
// garantias do plano, não só estilo:
//  R1  fetch só em src/services/api/http.ts (e no service worker)      — toda E/S passa pelos adaptadores
//  R2  Math.random proibido em src                                     — dados aleatórios só com semente
//  R3  dangerouslySetInnerHTML só em Formula.tsx (KaTeX, trust:false)   — sem HTML arbitrário
//  R4  console.log/debug, eval e new Function proibidos em src
//  R5  localStorage só em src/utils/storage.ts                         — leitura tolerante a falhas
//  R6  data-testid herdados do v1.0 presentes no código                — testes do legado continuam válidos
//  R7  cores literais (#hex, rgb()) em CSS só em tokens.css e print.css — tema único por tokens
//  R8  nenhum script/estilo de CDN em index.html ou src                — funciona offline e sob CSP
//  R9  catálogos i18n gerados em dia com as tabelas-fonte
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, resolve, dirname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const walk = (d) => readdirSync(d).flatMap((n) => { const p = join(d, n); return statSync(p).isDirectory() ? walk(p) : [p]; });
// Caminhos relativos sempre com '/', também no Windows (BUG-01 da auditoria).
const rel = (p) => relative(root, p).split(sep).join('/');
const files = walk(join(root, 'src'));
const code = files.filter((f) => /\.(ts|tsx)$/.test(f) && !rel(f).startsWith('src/i18n/locales/'));
const css = files.filter((f) => f.endsWith('.css'));
const problems = [];

function scan(list, re, rule, allow = () => false) {
  for (const f of list) {
    if (allow(rel(f))) continue;
    readFileSync(f, 'utf8').split('\n').forEach((line, i) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('//') || trimmed.startsWith('*') || trimmed.startsWith('/*')) return;
      if (re.test(line)) problems.push(`${rule} ${rel(f)}:${i + 1}: ${trimmed.slice(0, 120)}`);
    });
  }
}

scan(code, /\bfetch\s*\(/, 'R1', (p) => p === 'src/services/api/http.ts' || p === 'src/sw.ts');
scan(code, /Math\.random\s*\(/, 'R2');
scan(code, /dangerouslySetInnerHTML/, 'R3', (p) => p === 'src/features/formula/Formula.tsx');
scan(code, /\bconsole\.(log|debug)\s*\(|\beval\s*\(|new Function\s*\(/, 'R4');
scan(code, /\blocalStorage\b/, 'R5', (p) => p === 'src/utils/storage.ts');
scan(css, /#[0-9a-fA-F]{3,8}\b|\brgba?\(\s*\d/, 'R7', (p) => ['src/design-system/tokens.css', 'src/styles/print.css'].includes(p));

const all = code.map((f) => readFileSync(f, 'utf8')).join('\n');
for (const id of ['block-list', 'terminal-log', 'parameter-editor', 'render-button', 'result-root', 'viewer-stage']) {
  if (!all.includes(`data-testid="${id}"`)) problems.push(`R6 data-testid="${id}" não encontrado em src`);
}

for (const f of [join(root, 'index.html'), ...code]) {
  const text = readFileSync(f, 'utf8');
  if (/<(script|link)[^>]+(src|href)=["']https?:\/\//i.test(text) || /import\s*\(\s*['"]https?:/.test(text)) problems.push(`R8 ${rel(f)}: recurso externo (CDN)`);
}

const i18n = spawnSync(process.execPath, [join(root, 'scripts/i18n-build.mjs'), '--check'], { encoding: 'utf8' });
if (i18n.status !== 0) problems.push(`R9 ${i18n.stderr.trim() || i18n.stdout.trim()}`);

if (problems.length) {
  console.error(`lint: ${problems.length} problema(s)\n  ${problems.join('\n  ')}`);
  process.exit(1);
}
console.log(`lint: ok (${code.length} arquivos TS/TSX, ${css.length} CSS, 9 regras)`);
