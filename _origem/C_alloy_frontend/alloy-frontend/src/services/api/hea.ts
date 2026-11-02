/**
 * Adaptador do motor HEA (matriz pesquisa_front1.17 + hea_engine).
 * Detecta /api/bootstrap e /api/analyze reais; sem motor, o store usa heaDemo (rotulado).
 */
import { config } from '../../config.ts';
import { ApiError, requestJson } from './http.ts';
import { HeaBootstrap, HeaResult } from './contracts.ts';

export interface HeaCapabilities {
  available: boolean;
  checkedAt: string;
  error: string | null;
}

export async function detectHea(signal?: AbortSignal): Promise<{ caps: HeaCapabilities; bootstrap: HeaBootstrap | null }> {
  const checkedAt = new Date().toISOString();
  try {
    const bootstrap = await requestJson(`${config.heaBase}/api/bootstrap`, { signal, envelope: 'raw', schema: HeaBootstrap, timeoutMs: 5000 });
    return { caps: { available: true, checkedAt, error: null }, bootstrap };
  } catch (err) {
    if (err instanceof ApiError && err.kind === 'aborted') throw err;
    return { caps: { available: false, checkedAt, error: err instanceof Error ? err.message : String(err) }, bootstrap: null };
  }
}

export async function analyzeHea(name: string, composition: Record<string, number>, signal?: AbortSignal): Promise<HeaResult> {
  return requestJson(`${config.heaBase}/api/analyze`, { body: { name, composition }, signal, schema: HeaResult });
}
