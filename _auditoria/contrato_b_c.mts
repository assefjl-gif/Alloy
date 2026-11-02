// Auditoria (Fase 1): valida as respostas REAIS da API B (FastAPI /v1) contra os
// schemas Zod do frontend C, sem alterar nenhuma das duas bases.
// Uso: npx tsx _auditoria/contrato_b_c.mts http://127.0.0.1:8120
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const base = process.argv[2] ?? 'http://127.0.0.1:8120';
const contratos = await import(pathToFileURL(resolve('_origem/C_alloy_frontend/alloy-frontend/src/services/api/contracts.ts')).href);
const { StructureResult, MillerResult, MetalTable, StructureTable, ExportFile } = contratos;

type Caso = { nome: string; metodo: 'GET' | 'POST'; rota: string; corpo?: unknown; schema: { safeParse: (v: unknown) => { success: boolean; error?: { issues: unknown[] } } } };

const casos: Caso[] = [
  { nome: 'metais', metodo: 'GET', rota: '/v1/crystals/metals', schema: MetalTable },
  { nome: 'estruturas', metodo: 'GET', rota: '/v1/crystals/structures', schema: StructureTable },
  ...['Fe', 'Cu', 'Mg', 'Ti', 'Po', 'CFC', 'HC'].map((nome) => ({ nome: `estrutura ${nome}`, metodo: 'POST' as const, rota: '/v1/crystals/structure', corpo: { nome }, schema: StructureResult })),
  { nome: 'estrutura Fe→CFC (editada)', metodo: 'POST', rota: '/v1/crystals/structure', corpo: { nome: 'Fe', estrutura: 'CFC' }, schema: StructureResult },
  { nome: 'plano CFC (111)', metodo: 'POST', rota: '/v1/crystallography/miller', corpo: { estrutura: 'CFC', tipo: 'plano', indices: [1, 1, 1], a_nm: 0.3615 }, schema: MillerResult },
  { nome: 'plano HC (10-11)', metodo: 'POST', rota: '/v1/crystallography/miller', corpo: { estrutura: 'HC', tipo: 'plano', indices: [1, 0, -1, 1] }, schema: MillerResult },
  { nome: 'direção CCC [111]', metodo: 'POST', rota: '/v1/crystallography/miller', corpo: { estrutura: 'CCC', tipo: 'direcao', indices: [1, 1, 1], a_nm: 0.2866 }, schema: MillerResult },
  { nome: 'CIF Cu', metodo: 'POST', rota: '/v1/export/cif', corpo: { nome: 'Cu' }, schema: ExportFile },
  { nome: 'XYZ Mg', metodo: 'POST', rota: '/v1/export/xyz', corpo: { nome: 'Mg' }, schema: ExportFile },
];

let falhas = 0;
for (const caso of casos) {
  const resposta = await fetch(base + caso.rota, {
    method: caso.metodo,
    headers: caso.corpo ? { 'Content-Type': 'application/json' } : undefined,
    body: caso.corpo ? JSON.stringify(caso.corpo) : undefined,
  });
  const envelope = await resposta.json() as { ok?: boolean; result?: unknown; error?: string };
  if (!resposta.ok || !envelope.ok) {
    falhas++;
    console.log(`FALHA HTTP  ${caso.nome}: ${resposta.status} ${envelope.error ?? ''}`);
    continue;
  }
  const r = caso.schema.safeParse(envelope.result);
  if (!r.success) {
    falhas++;
    console.log(`FALHA ZOD   ${caso.nome}: ${JSON.stringify(r.error?.issues.slice(0, 3))}`);
  } else {
    console.log(`ok          ${caso.nome}`);
  }
}
console.log(`\n${casos.length - falhas}/${casos.length} respostas da API B aceitas pelos schemas do frontend C`);
process.exit(falhas ? 1 : 0);
