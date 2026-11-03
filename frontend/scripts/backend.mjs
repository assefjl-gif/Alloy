// Sobe o backend da plataforma (FastAPI) para desenvolvimento, testes unitários de adaptador e E2E.
// Uso: node scripts/backend.mjs [--port 8010]   (ou `npm run engine`)
// Python: ALLOY_PYTHON, senão o venv do monorepo (../.venv), senão `python`/`python3` do PATH.
// Ambiente: ALLOY_ENV=dev (padrão aqui) — aceita dados ainda não validados, com aviso.
import { spawn } from 'node:child_process';
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
export function startBackend({ port = 8010, stdio = 'inherit' } = {}) {
  return spawn(pythonExecutable(), ['-m', 'uvicorn', 'app.main:create_app', '--factory', '--host', '127.0.0.1', '--port', String(port)], {
    cwd: backendDir, stdio, env: { ALLOY_ENV: 'dev', ...process.env },
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const i = process.argv.indexOf('--port');
  const child = startBackend({ port: i > 0 ? Number(process.argv[i + 1]) : Number(process.env.PORT ?? 8010) });
  for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => child.kill());
  child.on('exit', (code) => process.exit(code ?? 0));
}
