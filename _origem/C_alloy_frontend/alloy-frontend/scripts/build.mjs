// Build de produção do Alloy Virtual Lab.
// esbuild 0.28 (o mesmo bundler que o Vite usa em desenvolvimento) com:
//  - code splitting em ESM (Three.js, KaTeX, gráficos, docx e módulos pesados carregados sob demanda);
//  - nomes com hash para cache imutável;
//  - index.html gerado a partir de index.html (raiz) com os arquivos de entrada;
//  - service worker (src/sw.ts) com a lista de pré-cache gerada a partir do metafile;
//  - relatório de tamanho em reports/bundle.json (bruto e gzip, inicial × sob demanda).
import * as esbuild from 'esbuild';
import { createHash } from 'node:crypto';
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dist = join(root, 'dist');
const dev = process.argv.includes('--dev');
const watch = process.argv.includes('--watch');
const pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
const buildId = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);

export const buildOptions = {
  absWorkingDir: root,
  entryPoints: { main: 'src/main.tsx' },
  bundle: true,
  splitting: true,
  format: 'esm',
  platform: 'browser',
  target: ['es2022', 'chrome109', 'firefox115', 'safari16'],
  outdir: join(dist, 'assets'),
  entryNames: '[name]-[hash]',
  chunkNames: 'chunks/[name]-[hash]',
  assetNames: 'media/[name]-[hash]',
  metafile: true,
  minify: !dev,
  sourcemap: dev ? 'inline' : 'linked',
  legalComments: 'linked',
  jsx: 'automatic',
  loader: { '.woff2': 'file', '.woff': 'file', '.ttf': 'file', '.svg': 'text' },
  alias: { '@': join(root, 'src') },
  define: {
    'process.env.NODE_ENV': JSON.stringify(dev ? 'development' : 'production'),
    __APP_VERSION__: JSON.stringify(pkg.version),
    __BUILD_ID__: JSON.stringify(buildId),
  },
  logLevel: 'warning',
};

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

function hashFile(p) {
  return createHash('sha256').update(readFileSync(p)).digest('hex').slice(0, 12);
}

/** Copia KaTeX (CSS + fontes woff2) para dist/vendor/katex — carregado sob demanda e disponível offline. */
function copyKatex() {
  const src = join(root, 'node_modules/katex/dist');
  const out = join(dist, 'vendor/katex');
  mkdirSync(join(out, 'fonts'), { recursive: true });
  cpSync(join(src, 'katex.min.css'), join(out, 'katex.min.css'));
  for (const f of readdirSync(join(src, 'fonts'))) if (f.endsWith('.woff2')) cpSync(join(src, 'fonts', f), join(out, 'fonts', f));
  cpSync(join(root, 'node_modules/katex/LICENSE'), join(out, 'LICENSE'));
}

function analyse(metafile) {
  const outputs = metafile.outputs;
  const entry = Object.keys(outputs).find((k) => outputs[k].entryPoint === 'src/main.tsx');
  const initial = new Set();
  const visit = (file) => {
    if (initial.has(file)) return;
    initial.add(file);
    for (const imp of outputs[file]?.imports ?? []) if (imp.kind === 'import-statement') visit(imp.path);
  };
  visit(entry);
  const cssEntry = outputs[entry].cssBundle;
  if (cssEntry) initial.add(cssEntry);
  const rows = Object.entries(outputs)
    .filter(([file]) => !file.endsWith('.map') && !file.endsWith('.LEGAL.txt'))
    .map(([file, info]) => {
      const abs = join(root, file);
      const bytes = statSync(abs).size;
      const gzip = gzipSync(readFileSync(abs), { level: 9 }).length;
      const inputs = Object.keys(info.inputs ?? {});
      const containsThree = inputs.some((i) => i.includes('vendor/three/') || i.includes('node_modules/three/'));
      const containsKatex = inputs.some((i) => i.includes('katex'));
      return { file: relative(dist, abs), bytes, gzip, initial: initial.has(file), containsThree, containsKatex, entryPoint: info.entryPoint ?? null };
    })
    .sort((a, b) => b.gzip - a.gzip);
  const sum = (list, k) => list.reduce((s, r) => s + r[k], 0);
  const init = rows.filter((r) => r.initial);
  return {
    builtAt: new Date().toISOString(),
    buildId,
    mode: dev ? 'development' : 'production',
    budget: { initialGzipWithoutThreeMaxBytes: 300 * 1024 },
    initial: { files: init.map((r) => r.file), bytes: sum(init, 'bytes'), gzip: sum(init, 'gzip'), containsThree: init.some((r) => r.containsThree) },
    lazy: rows.filter((r) => !r.initial),
    all: rows,
  };
}

function writeIndex(metafile) {
  const outputs = metafile.outputs;
  const entry = Object.keys(outputs).find((k) => outputs[k].entryPoint === 'src/main.tsx');
  const js = './' + relative(dist, join(root, entry));
  const css = outputs[entry].cssBundle ? './' + relative(dist, join(root, outputs[entry].cssBundle)) : null;
  let html = readFileSync(join(root, 'index.html'), 'utf8');
  html = html
    .replace('<!--APP_CSS-->', css ? `<link rel="stylesheet" href="${css}" />` : '')
    .replace('<!--APP_JS-->', `<script type="module" src="${js}"></script>`)
    .replaceAll('%BUILD_ID%', buildId)
    .replaceAll('%APP_VERSION%', pkg.version);
  writeFileSync(join(dist, 'index.html'), html);
}

async function buildServiceWorker() {
  const files = walk(dist)
    .filter((p) => !p.endsWith('.map') && !p.endsWith('.LEGAL.txt') && !p.endsWith('sw.js'))
    .map((p) => ({ url: './' + relative(dist, p).split('\\').join('/'), revision: hashFile(p) }));
  await esbuild.build({
    absWorkingDir: root,
    entryPoints: ['src/sw.ts'],
    bundle: true,
    format: 'iife',
    outfile: join(dist, 'sw.js'),
    minify: !dev,
    target: ['es2022'],
    define: { __PRECACHE__: JSON.stringify(files), __BUILD_ID__: JSON.stringify(buildId) },
    logLevel: 'warning',
  });
  return files.length;
}

export async function buildAll() {
  rmSync(dist, { recursive: true, force: true });
  mkdirSync(dist, { recursive: true });
  const result = await esbuild.build(buildOptions);
  copyKatex();
  if (existsSync(join(root, 'public'))) cpSync(join(root, 'public'), dist, { recursive: true });
  writeIndex(result.metafile);
  const precached = await buildServiceWorker();
  const report = analyse(result.metafile);
  report.serviceWorker = { precachedFiles: precached };
  mkdirSync(join(root, 'reports'), { recursive: true });
  writeFileSync(join(root, 'reports/bundle.json'), JSON.stringify(report, null, 2));
  writeFileSync(join(root, 'reports/esbuild-meta.json'), JSON.stringify(result.metafile));
  const kb = (n) => (n / 1024).toFixed(1) + ' kB';
  console.log(`build ${report.mode} ${buildId}: inicial ${kb(report.initial.bytes)} (${kb(report.initial.gzip)} gzip, Three no inicial: ${report.initial.containsThree ? 'SIM' : 'não'}) · ${report.lazy.length} arquivos sob demanda · ${precached} no pré-cache`);
  return report;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (watch) {
    const ctx = await esbuild.context({ ...buildOptions, minify: false, sourcemap: 'inline', plugins: [{ name: 'after', setup(b) { b.onEnd(async (r) => { if (!r.errors.length) { copyKatex(); if (existsSync(join(root, 'public'))) cpSync(join(root, 'public'), dist, { recursive: true }); writeIndex(r.metafile); await buildServiceWorker(); console.log('recompilado', new Date().toLocaleTimeString()); } }); } }] });
    mkdirSync(dist, { recursive: true });
    await ctx.watch();
    console.log('esbuild em modo watch');
  } else {
    await buildAll();
  }
}
