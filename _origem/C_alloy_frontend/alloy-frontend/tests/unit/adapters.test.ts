/**
 * Adaptadores de serviço contra servidores reais (sem simulação):
 *  - motor stdlib v1.0 (legacy/crystalab_modulo1.py) → API 'legacy';
 *  - servidor de contrato v1 (engine-stub/, rotas /v1/* reproduzindo o FastAPI) → API 'v1'.
 * Verifica detecção, validação de contrato (zod), Miller, exportação CIF/XYZ, erros tipados,
 * cancelamento e descarte de respostas obsoletas.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawn, type ChildProcess } from 'node:child_process';

const root = new URL('../../', import.meta.url).pathname;
const LEGACY_PORT = 8031;
const V1_PORT = 8032;
const procs: ChildProcess[] = [];

async function waitFor(url: string, ms = 15000): Promise<void> {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    try { const r = await fetch(url); if (r.status < 500) return; } catch { /* ainda subindo */ }
    await new Promise((res) => setTimeout(res, 150));
  }
  throw new Error(`servidor não respondeu: ${url}`);
}

before(async () => {
  procs.push(spawn('python3', ['legacy/crystalab_modulo1.py', '--port', String(LEGACY_PORT)], { cwd: root, stdio: 'ignore' }));
  procs.push(spawn('python3', ['engine-stub/v1_contract_server.py', '--port', String(V1_PORT)], { cwd: root, stdio: 'ignore' }));
  await Promise.all([waitFor(`http://127.0.0.1:${LEGACY_PORT}/api/estruturas`), waitFor(`http://127.0.0.1:${V1_PORT}/health`)]);
});

after(() => { for (const p of procs) p.kill(); });

async function loadApi(base: string) {
  const { config } = await import('../../src/config.ts');
  config.crystalabBase = base;
  return import('../../src/services/api/crystalab.ts');
}

test('motor stdlib v1.0: detecção legacy, estrutura e Miller validados pelo contrato', async () => {
  const api = await loadApi(`http://127.0.0.1:${LEGACY_PORT}`);
  const caps = await api.detectCrystalab();
  assert.equal(caps.api, 'legacy');
  assert.deepEqual(caps.exportFormats, []);
  const fe = await api.crystalabApi.structure({ nome: 'Fe' });
  assert.equal(fe.estrutura, 'CCC');
  assert.equal(Number(fe.densidade?.toFixed(2)), 7.88);
  const plane = await api.crystalabApi.miller({ estrutura: fe.estrutura, tipo: 'plano', indices: [1, 1, 0], a_nm: fe.a_nm, c_a: fe.c_a });
  assert.equal(plane.tipo, 'plano');
  await assert.rejects(api.crystalabApi.exportFile('cif', { nome: 'Fe' }), (e: Error & { kind?: string }) => e.kind === 'unavailable');
  await assert.rejects(api.crystalabApi.structure({ nome: 'Xx' }), (e: Error & { kind?: string }) => e.kind === 'domain' && /Xx|reconhec|desconhec|encontr/i.test(e.message));
});

test('contrato v1 (/v1/*): detecção, estrutura, exportação CIF/XYZ do servidor', async () => {
  const api = await loadApi(`http://127.0.0.1:${V1_PORT}`);
  const caps = await api.detectCrystalab();
  assert.equal(caps.api, 'v1');
  const cu = await api.crystalabApi.structure({ nome: 'Cu' });
  assert.equal(cu.estrutura, 'CFC');
  assert.equal(Number(cu.a_nm?.toFixed(5)), 0.36147);
  const cif = await api.crystalabApi.exportFile('cif', { nome: 'Cu' });
  assert.match(cif.content, /_cell_length_a/);
  const xyz = await api.crystalabApi.exportFile('xyz', { nome: 'Cu' });
  assert.match(xyz.filename, /\.xyz$/);
});

test('sem motor: erro tipado "unavailable", nunca valor simulado', async () => {
  const api = await loadApi('http://127.0.0.1:1');
  const caps = await api.detectCrystalab();
  assert.equal(caps.api, 'none');
  await assert.rejects(api.crystalabApi.structure({ nome: 'Fe' }), (e: Error & { kind?: string }) => e.kind === 'unavailable');
});

test('LatestRunner: chamada nova cancela a anterior e a resposta antiga é obsoleta', async () => {
  const { LatestRunner } = await import('../../src/services/api/latest.ts');
  const runner = new LatestRunner();
  let firstAborted = false;
  const slow = runner.run('k', (signal) => new Promise<string>((resolve) => {
    signal.addEventListener('abort', () => { firstAborted = true; });
    setTimeout(() => resolve('velho'), 60);
  }));
  const fast = runner.run('k', async () => 'novo');
  const [a, b] = await Promise.all([slow, fast]);
  assert.equal(firstAborted, true);
  assert.equal(a.stale, true);
  assert.equal(b.stale, false);
  assert.equal(b.value, 'novo');
});
