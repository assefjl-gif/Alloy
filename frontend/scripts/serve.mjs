// Servidor estático do build + proxy para a API unificada (desenvolvimento e E2E).
// Em produção quem faz este papel é o Caddy (infra/caddy/Caddyfile — ADR-010, mesmo domínio).
//   /                 → dist/ (front)
//   /api/*, /health   → backend FastAPI (padrão http://127.0.0.1:8010)
//   /v1/*             → backend (aliases depreciados; o front não os usa — mantidos para clientes antigos)
// Variáveis: PORT, ALLOY_API, DIST.
import { createServer, request as httpRequest } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { extname, join, normalize, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.webmanifest': 'application/manifest+json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
  '.txt': 'text/plain; charset=utf-8', '.map': 'application/json', '.ico': 'image/x-icon',
};

export function startServer({ port = Number(process.env.PORT ?? 5173), dist = process.env.DIST ?? join(root, 'dist'),
  api = process.env.ALLOY_API ?? 'http://127.0.0.1:8010', quiet = false } = {}) {
  const routes = [
    { prefix: '/api/', target: api },
    { prefix: '/v1/', target: api },
    { prefix: '/health', target: api },
  ];

  function proxy(req, res, route) {
    const url = new URL(route.target);
    const upstream = httpRequest({ hostname: url.hostname, port: url.port, path: req.url, method: req.method,
      headers: { ...req.headers, host: url.host } }, (up) => {
      res.writeHead(up.statusCode ?? 502, up.headers);
      up.pipe(res);
    });
    upstream.on('error', (err) => {
      res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ ok: false, error: `API indisponível em ${route.target} (${err.code ?? err.message}).`, code: 'ENGINE_UNREACHABLE' }));
    });
    req.pipe(upstream);
  }

  const server = createServer((req, res) => {
    const route = routes.find((r) => req.url === r.prefix || req.url.startsWith(r.prefix.endsWith('/') ? r.prefix : r.prefix + '/'));
    if (route) return proxy(req, res, route);
    const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let file = normalize(join(dist, urlPath));
    if (!file.startsWith(dist)) { res.writeHead(403); return res.end(); }
    if (existsSync(file) && statSync(file).isDirectory()) file = join(file, 'index.html');
    if (!existsSync(file)) { res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('não encontrado'); }
    const ext = extname(file);
    const immutable = /\/assets\/.+-[A-Z0-9]{8}\.(js|css)$/i.test(urlPath) || urlPath.includes('/assets/chunks/') || urlPath.includes('/assets/media/');
    res.writeHead(200, {
      'Content-Type': MIME[ext] ?? 'application/octet-stream',
      'Cache-Control': immutable ? 'public, max-age=31536000, immutable' : 'no-cache',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer',
      // CSP estrita: nenhum script inline, nenhum host externo (Three.js e KaTeX são locais).
      'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; worker-src 'self'; manifest-src 'self'; frame-ancestors 'none'; base-uri 'self'",
    });
    createReadStream(file).pipe(res);
  });
  return new Promise((ok) => server.listen(port, '127.0.0.1', () => { if (!quiet) console.log(`Alloy em http://127.0.0.1:${port} (API → ${api})`); ok(server); }));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) startServer();
