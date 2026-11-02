// Resolve as dependências deste projeto SEM acesso ao registro npm.
// Motivo: nesta máquina o registro npm/PyPI responde 403 (política de rede).
// O script cria node_modules/ com links simbólicos para:
//   1) pacotes já presentes no sistema (NPM_TOOLS, padrão /opt/npm-tools/node_modules);
//   2) pacotes vendorizados em vendor/ (three r160, zustand 5.0.1, tipos @types/*).
// Em um ambiente com registro disponível, use `npm install` normalmente: as versões
// declaradas em package.json são as mesmas.
import { existsSync, mkdirSync, rmSync, symlinkSync, lstatSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const system = process.env.NPM_TOOLS ?? '/opt/npm-tools/node_modules';
const nm = join(root, 'node_modules');
mkdirSync(join(nm, '@types'), { recursive: true });

const fromSystem = [
  'react', 'react-dom', 'scheduler', 'katex', 'zod', 'typescript', 'esbuild', 'playwright',
  'playwright-core', 'docx', 'tsx', '@types/node', '@types/katex',
];
const fromVendor = {
  three: 'vendor/three',
  zustand: 'vendor/zustand',
  csstype: 'vendor/types/csstype',
  '@types/three': 'vendor/types/three',
  '@types/react': 'vendor/types/react',
  '@types/react-dom': 'vendor/types/react-dom',
  '@types/webxr': 'vendor/types/webxr',
  '@types/stats.js': 'vendor/types/stats.js',
};

function link(target, name) {
  const dest = join(nm, name);
  try { if (lstatSync(dest)) rmSync(dest, { recursive: true, force: true }); } catch { /* inexistente */ }
  mkdirSync(dirname(dest), { recursive: true });
  symlinkSync(target, dest, 'dir');
}

const missing = [];
for (const pkg of fromSystem) {
  const src = join(system, pkg);
  if (!existsSync(src)) { missing.push(pkg); continue; }
  link(src, pkg);
}
for (const [name, rel] of Object.entries(fromVendor)) link(join(root, rel), name);

// bin/ para os executáveis usados pelos scripts
mkdirSync(join(nm, '.bin'), { recursive: true });
for (const [bin, rel] of Object.entries({ tsc: 'typescript/bin/tsc', esbuild: 'esbuild/bin/esbuild', playwright: 'playwright/cli.js', tsx: 'tsx/dist/cli.mjs' })) {
  const dest = join(nm, '.bin', bin);
  try { rmSync(dest, { force: true }); } catch { /* */ }
  symlinkSync(join(nm, rel), dest);
}
writeFileSync(join(nm, '.alloy-linked.json'), JSON.stringify({ system, linkedAt: new Date().toISOString(), missing }, null, 2));
if (missing.length) { console.error('Pacotes ausentes no sistema:', missing.join(', ')); process.exit(1); }
console.log(`node_modules pronto (${fromSystem.length} do sistema, ${Object.keys(fromVendor).length} vendorizados).`);
