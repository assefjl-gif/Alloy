/**
 * Adaptador de cristalografia da API unificada (rotas canônicas /api/v1 — docs/API.md §2).
 *  - 'v1'   → API unificada respondendo (cálculo, Miller, exportação CIF/XYZ);
 *  - 'none' → API inacessível (cálculos exigem servidor; nada é simulado).
 * O servidor stdlib v1.0 e as rotas /v1/* depreciadas não são mais usados pelo front (Fase 5).
 */
import { config } from '../../config.ts';
import { ApiError, requestJson } from './http.ts';
import {
  ExportFile, MetalTable, MillerResult, StructureResult, StructureTable,
  type MillerRequest, type StructureRequest,
} from './contracts.ts';
import { z } from 'zod';

export type CrystalabApi = 'v1' | 'none';

export interface CrystalabCapabilities {
  api: CrystalabApi;
  exportFormats: Array<'cif' | 'xyz'>;
  checkedAt: string;
  engineVersion: string | null;
  error: string | null;
}

const VersionInfo = z.object({
  api: z.string(),
  motores: z.record(z.string(), z.string()),
  versao_dados: z.string(),
}).passthrough();

let active: CrystalabApi = 'none';

const api = (path: string): string => `${config.apiBase}/api/v1${path}`;

export async function detectCrystalab(signal?: AbortSignal): Promise<CrystalabCapabilities> {
  const checkedAt = new Date().toISOString();
  try {
    const v = await requestJson(api('/meta/version'), { signal, schema: VersionInfo, timeoutMs: 4000 });
    active = 'v1';
    const motor = v.motores.crystallography;
    return { api: 'v1', exportFormats: ['cif', 'xyz'], checkedAt,
      engineVersion: `API ${v.api}${motor ? ` · motor ${motor}` : ''} · dados ${v.versao_dados}`, error: null };
  } catch (err) {
    if (err instanceof ApiError && err.kind === 'aborted') throw err;
    active = 'none';
    return { api: 'none', exportFormats: [], checkedAt, engineVersion: null, error: err instanceof Error ? err.message : String(err) };
  }
}

function ensure(): void {
  if (active === 'none') throw new ApiError('unavailable', 'API indisponível: este cálculo exige o servidor.', api(''), undefined, 'ENGINE_UNREACHABLE');
}

function clean<T extends object>(req: T): Partial<T> {
  return Object.fromEntries(Object.entries(req).filter(([, v]) => v !== undefined && v !== null && v !== '')) as Partial<T>;
}

export const crystalabApi = {
  async metals(signal?: AbortSignal): Promise<MetalTable> {
    ensure();
    return requestJson(api('/crystallography/metals'), { signal, schema: MetalTable });
  },
  async structures(signal?: AbortSignal): Promise<z.infer<typeof StructureTable>> {
    ensure();
    return requestJson(api('/crystallography/structures'), { signal, schema: StructureTable });
  },
  async structure(req: StructureRequest, signal?: AbortSignal): Promise<StructureResult> {
    ensure();
    return requestJson(api('/crystallography/cells'), { body: clean(req), signal, schema: StructureResult });
  },
  async miller(req: MillerRequest, signal?: AbortSignal): Promise<MillerResult> {
    ensure();
    return requestJson(api('/crystallography/miller'), { body: clean(req), signal, schema: MillerResult });
  },
  async exportFile(format: 'cif' | 'xyz', req: StructureRequest, signal?: AbortSignal): Promise<ExportFile> {
    ensure();
    return requestJson(api(`/exports/${format}`), { body: clean(req), signal, schema: ExportFile });
  },
};
