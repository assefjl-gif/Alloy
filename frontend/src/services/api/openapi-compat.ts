/**
 * Verificação ESTÁTICA (só tipos, sem código em tempo de execução) de que as requisições que o
 * front monta cabem no contrato publicado pelo backend (docs/openapi.json → openapi.gen.ts).
 * Se o backend mudar um campo de forma incompatível, `npm run typecheck` falha aqui.
 * As respostas são verificadas em tempo de execução pelos esquemas zod (contracts.ts) e pelo
 * teste de contrato do backend com respostas reais.
 */
import type { components } from './openapi.gen.ts';
import type { MillerRequest, StructureRequest } from './contracts.ts';

type Schemas = components['schemas'];
type Cabe<A, B> = A extends B ? true : false;
type Exige<T extends true> = T;

export type ContratoRequisicoes = [
  Exige<Cabe<StructureRequest, Schemas['StructureRequest']>>,
  Exige<Cabe<StructureRequest, Schemas['ExportRequest']>>,
  Exige<Cabe<MillerRequest, Schemas['MillerRequest']>>,
];
