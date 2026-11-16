/**
 * Adaptadores de serviço contra o BACKEND REAL da plataforma (FastAPI, sem simulação):
 * detecção pela /api/v1/meta/version, validação de contrato (zod), célula, Miller, exportação
 * CIF/XYZ, erros tipados, cancelamento e descarte de respostas obsoletas.
 * O backend é iniciado por scripts/backend.mjs (venv ../.venv ou ALLOY_PYTHON).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import type { ChildProcess } from 'node:child_process';
// @ts-expect-error — script .mjs sem tipos
import { startBackend } from '../../scripts/backend.mjs';

const PORT = 8031;
let proc: ChildProcess | undefined;

async function waitFor(url: string, ms = 30000): Promise<void> {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    try { const r = await fetch(url); if (r.status < 500) return; } catch { /* ainda subindo */ }
    await new Promise((res) => setTimeout(res, 200));
  }
  throw new Error(`servidor não respondeu: ${url}`);
}

before(async () => {
  proc = startBackend({ port: PORT, stdio: 'ignore' }) as ChildProcess;
  await waitFor(`http://127.0.0.1:${PORT}/health`);
});

after(() => { proc?.kill(); });

async function loadApi(base: string) {
  const { config } = await import('../../src/config.ts');
  config.apiBase = base;
  return import('../../src/services/api/crystalab.ts');
}

test('API unificada: detecção, célula, Miller e erro de domínio validados pelo contrato', async () => {
  const api = await loadApi(`http://127.0.0.1:${PORT}`);
  const caps = await api.detectCrystalab();
  assert.equal(caps.api, 'v1');
  assert.deepEqual(caps.exportFormats, ['cif', 'xyz']);
  assert.match(caps.engineVersion ?? '', /motor 2\./);
  const fe = await api.crystalabApi.structure({ nome: 'Fe' });
  assert.equal(fe.estrutura, 'CCC');
  assert.equal(Number(fe.densidade?.toFixed(2)), 7.88);
  const plane = await api.crystalabApi.miller({ estrutura: fe.estrutura, tipo: 'plano', indices: [1, 1, 0], a_nm: fe.a_nm, c_a: fe.c_a });
  assert.equal(plane.tipo, 'plano');
  await assert.rejects(api.crystalabApi.structure({ nome: 'Xx' }), (e: Error & { kind?: string }) => e.kind === 'domain' && /Xx|reconhec|desconhec|encontr/i.test(e.message));
});

test('API unificada: exportação CIF/XYZ gerada no servidor', async () => {
  const api = await loadApi(`http://127.0.0.1:${PORT}`);
  await api.detectCrystalab();
  const cu = await api.crystalabApi.structure({ nome: 'Cu' });
  assert.equal(cu.estrutura, 'CFC');
  assert.equal(Number(cu.a_nm?.toFixed(5)), 0.36147);
  const cif = await api.crystalabApi.exportFile('cif', { nome: 'Cu' });
  assert.match(cif.content, /_cell_length_a/);
  const xyz = await api.crystalabApi.exportFile('xyz', { nome: 'Mg' });
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


/**
 * Política de demonstração do SERVIDOR (`demo_permitido` de GET /api/v1/meta/capabilities).
 * Em produção a demonstração é PROIBIDA (princípio 3 do projeto): com o serviço indisponível, o
 * modo efetivo tem de ser `disabled`, NUNCA `demo`, mesmo que a preferência local peça demonstração.
 */
test('demo_permitido: servidor proibindo demonstração ⇒ HEA indisponível fica "disabled", nunca "demo"', async () => {
  const { serviceMode, serverDemoAllowed, effectivePolicy } = await import('../../src/stores/capabilities.ts');
  const caps = (demoAllowed: boolean | null, available: boolean) => ({
    crystalab: null,
    hea: { available, checkedAt: '2026-11-15T00:00:00Z', error: available ? null : 'sem serviço', demoAllowed },
    online: true,
    ready: true,
    set: () => undefined,
  });

  // produção: o servidor proíbe a demonstração e o serviço não está disponível
  assert.equal(serviceMode('hea', caps(false, false), 'on'), 'disabled');
  assert.equal(serviceMode('hea', caps(false, false), 'auto'), 'disabled');
  assert.equal(serviceMode('hea', caps(false, true), 'on'), 'live', 'com serviço real, usa o serviço real');
  assert.equal(serverDemoAllowed('hea', caps(false, true)), false);
  assert.equal(effectivePolicy('hea', caps(false, true), 'on'), 'off');

  // ambiente não produtivo: o servidor permite, a política local decide (demonstração rotulada)
  assert.equal(serviceMode('hea', caps(true, false), 'on'), 'demo');
  assert.equal(serviceMode('hea', caps(true, false), 'auto'), 'demo');
  assert.equal(serviceMode('hea', caps(true, false), 'off'), 'disabled');

  // servidor não respondeu: não há decisão dele a respeitar, vale a política local
  assert.equal(serverDemoAllowed('hea', caps(null, false)), null);
  assert.equal(serviceMode('hea', caps(null, false), 'auto'), 'demo');
  assert.equal(serviceMode('hea', caps(null, false), 'off'), 'disabled');
});

test('demo_permitido: o campo é lido do servidor REAL e guardado nas capacidades', async () => {
  const { config } = await import('../../src/config.ts');
  config.apiBase = `http://127.0.0.1:${PORT}`;
  const hea = await import('../../src/services/api/hea.ts');
  const allowed = await hea.detectDemoPolicy();
  assert.equal(typeof allowed, 'boolean', 'o servidor informa a política por serviço');
  const { caps } = await hea.detectHea();
  assert.equal(caps.demoAllowed, allowed, 'a detecção guarda a política do servidor');

  // servidor fora do ar: política desconhecida (null), nunca "permitido" por omissão
  config.apiBase = 'http://127.0.0.1:1';
  assert.equal(await hea.detectDemoPolicy(), null);
  const off = await hea.detectHea();
  assert.equal(off.caps.available, false);
  assert.equal(off.caps.demoAllowed, null);
});
