/**
 * Conta pelo cliente do front contra o BACKEND REAL com SQLite migrado (scripts/backend.mjs --db):
 * cadastro, login, CSRF enviado automaticamente nas escritas, histórico pessoal, /auth/me e logout.
 * Node não tem cookie jar: o teste repassa o Set-Cookie como faria o navegador no mesmo domínio.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { ChildProcess } from 'node:child_process';
// @ts-expect-error — script .mjs sem tipos
import { startBackend } from '../../scripts/backend.mjs';

const PORT = 8033;
const dir = mkdtempSync(join(tmpdir(), 'alloy-conta-'));
let proc: ChildProcess | undefined;
let cookie = '';
const nativeFetch = globalThis.fetch;

before(async () => {
  proc = startBackend({ port: PORT, stdio: 'ignore', db: join(dir, 'alloy.db') }) as ChildProcess;
  const end = Date.now() + 30000;
  for (;;) {
    try { if ((await nativeFetch(`http://127.0.0.1:${PORT}/health`)).ok) break; } catch { /* subindo */ }
    if (Date.now() > end) throw new Error('backend não subiu');
    await new Promise((r) => setTimeout(r, 200));
  }
  // "Navegador" mínimo: guarda o cookie de sessão e o reenvia (ambiente dev → cookie sem Secure).
  globalThis.fetch = async (input, init = {}) => {
    const headers = new Headers(init.headers);
    if (cookie) headers.set('Cookie', cookie);
    const res = await nativeFetch(input, { ...init, headers });
    const set = res.headers.get('set-cookie') ?? '';
    const value = /alloy_sessao=([^;]*)/.exec(set)?.[1];
    if (value !== undefined) cookie = /Max-Age=0/i.test(set) ? '' : `alloy_sessao=${value}`;
    return res;
  };
});

after(() => {
  globalThis.fetch = nativeFetch;
  proc?.kill();
  try { rmSync(dir, { recursive: true, force: true }); } catch { /* arquivo ainda aberto no Windows */ }
});

test('cadastro, login, escrita com CSRF automático, histórico e logout', async () => {
  const { config } = await import('../../src/config.ts');
  config.apiBase = `http://127.0.0.1:${PORT}`;
  const auth = await import('../../src/services/api/auth.ts');
  const cl = await import('../../src/services/api/crystalab.ts');

  assert.equal(await auth.currentUser(), null);
  await assert.rejects(auth.register('Ana', 'ana@exemplo.test', '1234567890'), (e: Error & { kind?: string }) => e.kind === 'domain');
  await auth.register('Ana Lima', 'ana@exemplo.test', 'cristal-cubico-2026');
  const user = await auth.login('ana@exemplo.test', 'cristal-cubico-2026');
  assert.equal(user.nome, 'Ana Lima');
  assert.ok(cookie, 'cookie de sessão recebido');

  await cl.detectCrystalab();
  await cl.crystalabApi.structure({ nome: 'Fe' });   // POST com cookie: só passa com o X-Alloy-CSRF
  const h = await auth.history();
  assert.equal(h.total, 1);
  assert.equal(h.itens[0]?.operacao, 'celula');

  assert.equal((await auth.currentUser())?.email, 'ana@exemplo.test');   // renova o CSRF
  await cl.crystalabApi.structure({ nome: 'Cu' });                       // e o novo continua valendo
  assert.equal((await auth.history()).total, 2);

  assert.equal(await auth.logout(), 1);
  assert.equal(await auth.currentUser(), null);
});
