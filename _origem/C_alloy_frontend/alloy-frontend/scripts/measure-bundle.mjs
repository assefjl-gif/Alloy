// Verifica o orçamento do bundle a partir de reports/bundle.json (gerado por scripts/build.mjs)
// e acrescenta o resultado em reports/metrics.json. Falha se o inicial passar de 300 kB gzip
// ou se Three.js entrar no carregamento inicial.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';

const b = JSON.parse(readFileSync('reports/bundle.json', 'utf8'));
const kb = (n) => `${(n / 1024).toFixed(1)} kB`;
const limit = 300 * 1024;
const lazy = [...b.lazy].sort((x, y) => y.gzip - x.gzip).slice(0, 6).map((c) => `${c.file} ${kb(c.gzip)}`);
const ok = b.initial.gzip < limit && !b.initial.containsThree;
console.log(`bundle inicial: ${kb(b.initial.bytes)} (${kb(b.initial.gzip)} gzip) · Three no inicial: ${b.initial.containsThree ? 'sim' : 'não'} · meta < 300 kB gzip: ${ok ? 'ATINGIDA' : 'NÃO ATINGIDA'}`);
console.log(`maiores sob demanda: ${lazy.join(' · ')}`);
const prev = existsSync('reports/metrics.json') ? JSON.parse(readFileSync('reports/metrics.json', 'utf8')) : {};
writeFileSync('reports/metrics.json', JSON.stringify({ ...prev, bundle: { measuredAt: new Date().toISOString(), buildId: b.buildId, initialBytes: b.initial.bytes, initialGzip: b.initial.gzip, containsThree: b.initial.containsThree, target: '< 300 kB gzip (sem Three.js)', met: ok, largestLazy: lazy } }, null, 2));
process.exit(ok ? 0 : 1);
