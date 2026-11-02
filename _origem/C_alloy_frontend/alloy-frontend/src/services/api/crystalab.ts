/**
 * Adaptador do motor CrystaLab. Detecta qual contrato o servidor fala:
 *  - 'v1'     → versão FastAPI (rotas /v1/*, com exportação CIF/XYZ);
 *  - 'legacy' → servidor stdlib v1.0 (rotas /api/*, sem exportação);
 *  - 'none'   → motor inacessível (cálculos exigem servidor; nada é simulado).
 */
import { config } from '../../config.ts';
import { ApiError, requestJson } from './http.ts';
import {
  ExportFile, MetalTable, MillerResult, StructureResult, StructureTable,
  type MillerRequest, type StructureRequest,
} from './contracts.ts';
import { z } from 'zod';

export type CrystalabApi = 'v1' | 'legacy' | 'none';

export interface CrystalabCapabilities {
  api: CrystalabApi;
  exportFormats: Array<'cif' | 'xyz'>;
  checkedAt: string;
  engineVersion: string | null;
  error: string | null;
}

let active: CrystalabApi = 'none';

const base = (): string => config.crystalabBase;

export async function detectCrystalab(signal?: AbortSignal): Promise<CrystalabCapabilities> {
  const checkedAt = new Date().toISOString();
  try {
    const health = await requestJson<{ ok?: boolean; version?: string }>(`${base()}/health`, { signal, envelope: 'raw', timeoutMs: 4000 });
    if (health && health.ok) {
      active = 'v1';
      return { api: 'v1', exportFormats: ['cif', 'xyz'], checkedAt, engineVersion: health.version ?? null, error: null };
    }
  } catch (err) {
    if (err instanceof ApiError && err.kind === 'aborted') throw err;
  }
  try {
    await requestJson(`${base()}/api/estruturas`, { signal, resultKey: 'estruturas', schema: StructureTable, timeoutMs: 5000 });
    active = 'legacy';
    return { api: 'legacy', exportFormats: [], checkedAt, engineVersion: 'v1.0 (stdlib)', error: null };
  } catch (err) {
    if (err instanceof ApiError && err.kind === 'aborted') throw err;
    active = 'none';
    return { api: 'none', exportFormats: [], checkedAt, engineVersion: null, error: err instanceof Error ? err.message : String(err) };
  }
}

export function setActiveApi(api: CrystalabApi): void {
  active = api;
}

function ensure(): CrystalabApi {
  if (active === 'none') throw new ApiError('unavailable', 'Motor CrystaLab indisponível: este cálculo exige o servidor.', base(), undefined, 'ENGINE_UNREACHABLE');
  return active;
}

function clean<T extends object>(req: T): Partial<T> {
  return Object.fromEntries(Object.entries(req).filter(([, v]) => v !== undefined && v !== null && v !== '')) as Partial<T>;
}

export const crystalabApi = {
  async metals(signal?: AbortSignal): Promise<MetalTable> {
    return ensure() === 'v1'
      ? requestJson(`${base()}/v1/crystals/metals`, { signal, schema: MetalTable })
      : requestJson(`${base()}/api/metais`, { signal, schema: MetalTable, resultKey: 'metais' });
  },
  async structures(signal?: AbortSignal): Promise<z.infer<typeof StructureTable>> {
    return ensure() === 'v1'
      ? requestJson(`${base()}/v1/crystals/structures`, { signal, schema: StructureTable })
      : requestJson(`${base()}/api/estruturas`, { signal, schema: StructureTable, resultKey: 'estruturas' });
  },
  async structure(req: StructureRequest, signal?: AbortSignal): Promise<StructureResult> {
    const url = ensure() === 'v1' ? `${base()}/v1/crystals/structure` : `${base()}/api/estrutura`;
    return requestJson(url, { body: clean(req), signal, schema: StructureResult });
  },
  async miller(req: MillerRequest, signal?: AbortSignal): Promise<MillerResult> {
    const url = ensure() === 'v1' ? `${base()}/v1/crystallography/miller` : `${base()}/api/miller`;
    return requestJson(url, { body: clean(req), signal, schema: MillerResult });
  },
  async exportFile(format: 'cif' | 'xyz', req: StructureRequest, signal?: AbortSignal): Promise<ExportFile> {
    if (ensure() !== 'v1') throw new ApiError('unavailable', 'Exportação CIF/XYZ só existe na versão /v1 do motor.', base(), undefined, 'EXPORT_UNAVAILABLE');
    return requestJson(`${base()}/v1/export/${format}`, { body: clean(req), signal, schema: ExportFile });
  },
};
