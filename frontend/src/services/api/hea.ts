/**
 * Adaptador HEA da API unificada (/api/v1/hea — docs/API.md §2).
 * Sem o serviço (503 CAPACIDADE_INDISPONIVEL), o store usa heaDemo (rotulado) ou desativa o módulo.
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
    const bootstrap = await requestJson(`${config.apiBase}/api/v1/hea/bootstrap`, { signal, schema: HeaBootstrap, timeoutMs: 5000 });
    return { caps: { available: true, checkedAt, error: null }, bootstrap };
  } catch (err) {
    if (err instanceof ApiError && err.kind === 'aborted') throw err;
    return { caps: { available: false, checkedAt, error: err instanceof Error ? err.message : String(err) }, bootstrap: null };
  }
}

export async function analyzeHea(name: string, composition: Record<string, number>, signal?: AbortSignal): Promise<HeaResult> {
  return requestJson(`${config.apiBase}/api/v1/hea/analyses`, { body: { nome: name, composicao: composition }, signal, schema: HeaResult });
}
