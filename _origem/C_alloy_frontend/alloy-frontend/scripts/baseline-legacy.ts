/**
 * Etapa 1.7 / 1.8 — linha de base do front-end legado (CrystaLab v1.0, stdlib).
 * Uso: python3 legacy/crystalab_modulo1.py --port 8010 &  node --import tsx scripts/baseline-legacy.ts
 * Saída: reports/baseline/legacy-baseline.json + capturas de tela.
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { cpus, totalmem, release, platform } from 'node:os';
import { gzipSync } from 'node:zlib';
import { runA11yAudit } from '../tests/helpers/a11yAudit.ts';

const URL_LEGACY = process.env.LEGACY_URL ?? 'http://127.0.0.1:8010/';
const OUT = 'reports/baseline';
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1366, height: 900 } });
await context.addInitScript('globalThis.__name = (f) => f');
const page = await context.newPage();
const failed: Array<{ url: string; error: string }> = [];
const requests: Array<{ url: string; status?: number }> = [];
page.on('requestfailed', (r) => failed.push({ url: r.url(), error: r.failure()?.errorText ?? '?' }));
page.on('response', (r) => requests.push({ url: r.url(), status: r.status() }));
const consoleErrors: string[] = [];
page.on('pageerror', (e) => consoleErrors.push(String(e)));

const t0 = Date.now();
await page.goto(URL_LEGACY, { waitUntil: 'load', timeout: 60000 });
const loadMs = Date.now() - t0;
await page.waitForTimeout(1500);

const html = await (await fetch(URL_LEGACY)).text();
const nav = await page.evaluate(() => {
  const n = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  return { domContentLoaded: Math.round(n.domContentLoadedEventEnd), load: Math.round(n.loadEventEnd), transfer: n.transferSize, decoded: n.decodedBodySize };
});
const gpu = await page.evaluate(() => {
  const c = document.createElement('canvas');
  const gl = c.getContext('webgl');
  if (!gl) return { webgl: false };
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  return { webgl: true, renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER), vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR) };
});
const threeLoaded = await page.evaluate(() => typeof (window as unknown as { THREE?: unknown }).THREE !== 'undefined');
const fallbackShown = await page.locator('.viewer-fallback').count();
const testids = await page.evaluate(() => Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')));

// FPS do loop legado (requestAnimationFrame contínuo) — só faz sentido se o Three carregou.
const fps = await page.evaluate(async () => {
  let frames = 0;
  const start = performance.now();
  await new Promise<void>((resolve) => {
    const tick = () => { frames += 1; if (performance.now() - start < 5000) requestAnimationFrame(tick); else resolve(); };
    requestAnimationFrame(tick);
  });
  return Math.round((frames / ((performance.now() - start) / 1000)) * 10) / 10;
});
await page.screenshot({ path: `${OUT}/legacy-1366.png`, fullPage: false });

const a11y = await runA11yAudit(page, { focusSamples: 30 });

// Comportamento em 360 px
const mobile = await browser.newContext({ viewport: { width: 360, height: 740 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
await mobile.addInitScript('globalThis.__name = (f) => f');
const mp = await mobile.newPage();
await mp.goto(URL_LEGACY, { waitUntil: 'load', timeout: 60000 });
await mp.waitForTimeout(800);
const narrow = await mp.evaluate(() => {
  const doc = document.documentElement;
  const offenders: Array<{ el: string; right: number }> = [];
  document.querySelectorAll('body *').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.right > window.innerWidth + 1 && r.width > 0) offenders.push({ el: `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}.${(el.getAttribute('class') ?? '').split(' ')[0]}`, right: Math.round(r.right) });
  });
  const stage = document.querySelector('[data-testid=viewer-stage]') as HTMLElement | null;
  return {
    viewport: window.innerWidth,
    scrollWidth: doc.scrollWidth,
    horizontalOverflow: doc.scrollWidth > window.innerWidth,
    offenders: offenders.slice(0, 12),
    pageHeight: doc.scrollHeight,
    viewerTouchAction: stage ? getComputedStyle(stage).touchAction : null,
    viewerTop: stage ? Math.round(stage.getBoundingClientRect().top + window.scrollY) : null,
  };
});
await mp.screenshot({ path: `${OUT}/legacy-360.png`, fullPage: true });

const report = {
  measuredAt: new Date().toISOString(),
  target: URL_LEGACY,
  equipment: {
    note: 'Contêiner de nuvem, Chromium headless (Playwright) — NÃO é o "notebook intermediário" do plano. Valores de FPS não são comparáveis às metas.',
    os: `${platform()} ${release()}`,
    cpu: `${cpus()[0]?.model ?? '?'} × ${cpus().length}`,
    ramGB: Math.round(totalmem() / 1e9),
    browser: `Chromium ${browser.version()} (headless)`,
    gpu,
  },
  load: { wallClockMs: loadMs, ...nav, htmlBytes: Buffer.byteLength(html), htmlGzipBytes: gzipSync(html).length },
  externalDependencies: requests.filter((r) => !r.url.startsWith(URL_LEGACY)).map((r) => ({ url: r.url, status: r.status })),
  failedRequests: failed,
  pageErrors: consoleErrors,
  viewer: { threeLoaded, fallbackShown: fallbackShown > 0, rafFps5s: fps, fpsMeaningful: threeLoaded },
  narrow360: narrow,
  dataTestIds: testids,
  a11y: { counts: a11y.counts, total: a11y.violations.length, needsReview: a11y.needsReview.length, stats: a11y.stats, violations: a11y.violations },
  notMeasured: {
    lighthouse: 'Lighthouse indisponível (registro npm bloqueado). Substituído pela auditoria própria tests/helpers/a11yAudit.ts.',
    axeCore: 'axe-core indisponível (repositório git não contém build; build exige npm). Mesma substituição.',
    bundle: 'Legado não tem bundle: HTML/CSS/JS inline numa string Python (htmlBytes acima) + Three.js r128 via CDN.',
    heaLegacy: 'pesquisa_front1.17.py importa hea_engine, que não está no projeto — o front HEA legado não pôde ser executado.',
  },
};
writeFileSync(`${OUT}/legacy-baseline.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify({ load: report.load, viewer: report.viewer, narrow360: { ...narrow, offenders: narrow.offenders.length }, a11y: report.a11y.counts, failed: failed.length, testids }, null, 2));
await browser.close();
