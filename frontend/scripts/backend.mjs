// Sobe o backend da plataforma (FastAPI) para desenvolvimento, testes unitários de adaptador e E2E.
// Uso: node scripts/backend.mjs [--port 8010] [--db caminho.db]   (ou `npm run engine`)
// Python: ALLOY_PYTHON, senão o venv do monorepo (../.venv), senão `python`/`python3` do PATH.
// Ambiente: ALLOY_ENV=dev (padrão aqui) — aceita dados ainda não validados, com aviso.
// --db (ou ALLOY_DEV_DB): SQLite local migrado e com seed (python -m app.cli preparar) → contas e
// histórico funcionam; sem ele o backend roda só com o seed JSON (sem contas).
import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const monorepo = resolve(root, '..');
const backendDir = join(monorepo, 'backend');

export function pythonExecutable() {
  if (process.env.ALLOY_PYTHON) return process.env.ALLOY_PYTHON;
  const venv = process.platform === 'win32' ? join(monorepo, '.venv', 'Scripts', 'python.exe') : join(monorepo, '.venv', 'bin', 'python');
  if (existsSync(venv)) return venv;
  return process.platform === 'win32' ? 'python' : 'python3';
}

/** Inicia o uvicorn com a fábrica create_app; devolve o processo filho. */
export function startBackend({ port = 8010, stdio = 'inherit', db = process.env.ALLOY_DEV_DB } = {}) {
  const env = { ALLOY_ENV: 'dev', ...process.env };
  if (db) {
    env.DATABASE_URL = `sqlite:///${resolve(db).replaceAll('\\', '/')}`;
    const prep = spawnSync(pythonExecutable(), ['-m', 'app.cli', 'preparar'], { cwd: backendDir, env, encoding: 'utf8' });
    if (prep.status !== 0) throw new Error(`falha ao preparar o banco: ${prep.stderr || prep.stdout}`);
  }
  return spawn(pythonExecutable(), ['-m', 'uvicorn', 'app.main:create_app', '--factory', '--host', '127.0.0.1', '--port', String(port)], {
    cwd: backendDir, stdio, env,
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const arg = (name) => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : undefined; };
  const child = startBackend({ port: Number(arg('--port') ?? process.env.PORT ?? 8010), db: arg('--db') ?? process.env.ALLOY_DEV_DB });
  for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => child.kill());
  child.on('exit', (code) => process.exit(code ?? 0));
}
