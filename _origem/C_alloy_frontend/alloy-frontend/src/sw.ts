/// <reference lib="webworker" />
/**
 * Service worker do Alloy Virtual Lab (7.10/7.11). Estratégia por tipo de recurso:
 *  - ativos com hash (JS/CSS/fontes/Three.js/KaTeX) → pré-cache + cache-first (imutáveis);
 *  - index.html, config.js, manifest → network-first com recuo ao cache (atualizáveis);
 *  - tabelas do motor (GET /api/metais, /api/estruturas, /v1/crystals/*) → stale-while-revalidate;
 *  - cálculos (POST) e demais rotas do motor → só rede (exigem servidor; nunca servidos do cache).
 * A lista de pré-cache é gerada no build (scripts/build.mjs) a partir do metafile.
 */
declare const __PRECACHE__: Array<{ url: string; revision: string }>;
declare const __BUILD_ID__: string;
const sw = self as unknown as ServiceWorkerGlobalScope;

const STATIC = `alloy-static-${__BUILD_ID__}`;
const RUNTIME = 'alloy-runtime-v1';
const TABLES = 'alloy-engine-tables-v1';

const scopeUrl = new URL(sw.registration.scope);
const toAbs = (u: string) => new URL(u, scopeUrl).href;

sw.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC).then((cache) => cache.addAll(__PRECACHE__.map((e) => toAbs(e.url)))).then(() => sw.skipWaiting()),
  );
});

sw.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('alloy-static-') && k !== STATIC).map((k) => caches.delete(k))))
      .then(() => sw.clients.claim()),
  );
});

const TABLE_PATTERN = /\/engines\/crystalab\/(api\/(metais|estruturas)|v1\/crystals\/(metals|structures))$/;
const UPDATABLE = /\/(index\.html|config\.js|boot\.js|manifest\.webmanifest)?$/;

sw.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return; // cálculos: sempre rede
  const url = new URL(req.url);
  if (url.origin !== scopeUrl.origin) return;

  if (TABLE_PATTERN.test(url.pathname)) {
    event.respondWith(
      caches.open(TABLES).then(async (cache) => {
        const cached = await cache.match(req);
        const network = fetch(req).then((res) => { if (res.ok) void cache.put(req, res.clone()); return res; }).catch(() => cached ?? Response.error());
        return cached ?? network;
      }),
    );
    return;
  }
  if (url.pathname.includes('/engines/') || url.pathname.startsWith('/api/') || url.pathname.includes('/legacy/')) return;

  if (url.pathname.includes('/assets/') || url.pathname.includes('/vendor/') || url.pathname.includes('/icons/')) {
    event.respondWith(caches.match(req, { ignoreSearch: true }).then((hit) => hit ?? fetch(req).then((res) => {
      if (res.ok) void caches.open(RUNTIME).then((c) => c.put(req, res.clone()));
      return res;
    })));
    return;
  }

  if (req.mode === 'navigate' || UPDATABLE.test(url.pathname.slice(scopeUrl.pathname.length - 1))) {
    event.respondWith(
      fetch(req)
        .then((res) => { if (res.ok) void caches.open(RUNTIME).then((c) => c.put(req, res.clone())); return res; })
        .catch(async () => (await caches.match(req, { ignoreSearch: true })) ?? (await caches.match(toAbs('./index.html'))) ?? Response.error()),
    );
  }
});

sw.addEventListener('message', (event) => {
  if (event.data === 'skip-waiting') void sw.skipWaiting();
});
