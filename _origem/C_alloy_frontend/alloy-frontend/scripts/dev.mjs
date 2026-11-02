// Desenvolvimento: recompila em modo watch e serve com proxy para os motores.
// Uso: npm run engine (outro terminal) && npm run dev
import { spawn } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { startServer } from './serve.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
spawn(process.execPath, ['scripts/build.mjs', '--watch', '--dev'], { cwd: root, stdio: 'inherit' });
setTimeout(() => startServer(), 1200);
