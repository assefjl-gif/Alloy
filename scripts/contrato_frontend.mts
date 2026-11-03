// Teste de contrato (RQ-API-03, ADR-007): respostas REAIS da API unificada validadas pelos schemas
// Zod do frontend. Evolução de _auditoria/contrato_b_c.mts (Fase 1).
// Uso: tsx scripts/contrato_frontend.mts <url-da-api> <pasta-do-frontend>
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const base = process.argv[2] ?? 'http://127.0.0.1:8130';
const frontend = process.argv[3] ?? '_origem/C_alloy_frontend/alloy-frontend';
const contratos = await import(pathToFileURL(resolve(frontend, 'src/services/api/contracts.ts')).href);
const { StructureResult, MillerResult, MetalTable, StructureTable, ExportFile } = contratos;

type Schema = { safeParse: (v: unknown) => { success: boolean; error?: { issues: unknown[] } } };
type Caso = { nome: string; metodo: 'GET' | 'POST'; rota: string; corpo?: unknown; schema: Schema };

// Mesmos casos nas rotas que o frontend usa hoje (/v1, depreciadas) e nas canônicas (/api/v1).
const pares: Array<[string, string, string, 'GET' | 'POST', Schema, unknown[]]> = [
  ['metais', '/v1/crystals/metals', '/api/v1/crystallography/metals', 'GET', MetalTable, [undefined]],
  ['estruturas', '/v1/crystals/structures', '/api/v1/crystallography/structures', 'GET', StructureTable, [undefined]],
  ['célula', '/v1/crystals/structure', '/api/v1/crystallography/cells', 'POST', StructureResult, [
    { nome: 'Fe' }, { nome: 'Cu' }, { nome: 'Mg' }, { nome: 'Ti' }, { nome: 'Po' }, { nome: 'CFC' }, { nome: 'HC' },
    { nome: 'Fe', estrutura: 'CFC' }, { nome: 'CFC', a: 0.4 },
  ]],
  ['Miller', '/v1/crystallography/miller', '/api/v1/crystallography/miller', 'POST', MillerResult, [
    { estrutura: 'CFC', tipo: 'plano', indices: [1, 1, 1], a_nm: 0.3615 },
    { estrutura: 'HC', tipo: 'plano', indices: [1, 0, -1, 1] },
    { estrutura: 'CCC', tipo: 'direcao', indices: [1, 1, 1], a_nm: 0.2866 },
    { estrutura: 'CFC', tipo: 'plano', indices: [1, 1, 1], supercelula: 3 },
  ]],
  ['CIF', '/v1/export/cif', '/api/v1/exports/cif', 'POST', ExportFile, [{ nome: 'Cu' }]],
  ['XYZ', '/v1/export/xyz', '/api/v1/exports/xyz', 'POST', ExportFile, [{ nome: 'Mg' }]],
];

const casos: Caso[] = [];
for (const [nome, antiga, nova, metodo, schema, corpos] of pares) {
  for (const corpo of corpos) {
    const rotulo = `${nome}${corpo ? ' ' + JSON.stringify(corpo) : ''}`;
    casos.push({ nome: `[v1]     ${rotulo}`, metodo, rota: antiga, corpo, schema });
    casos.push({ nome: `[api/v1] ${rotulo}`, metodo, rota: nova, corpo, schema });
  }
}

let falhas = 0;
const health = await (await fetch(`${base}/health`)).json() as { ok?: boolean; version?: string };
if (!health.ok) { console.log('FALHA /health não responde ok: o frontend não detectaria a API'); falhas++; }
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
  }
}
console.log(`${casos.length - falhas}/${casos.length} respostas aceitas pelos schemas do frontend (API ${health.version ?? '?'})`);
process.exit(falhas ? 1 : 0);
