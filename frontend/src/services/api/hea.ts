/**
 * Adaptador HEA da API unificada (/api/v1/hea — docs/API.md §2).
 * Sem o serviço (503 CAPACIDADE_INDISPONIVEL), o store usa heaDemo (rotulado) ou desativa o módulo.
 */
import { z } from 'zod';
import { config } from '../../config.ts';
import { ApiError, requestJson } from './http.ts';
import { HeaBootstrap, HeaResult } from './contracts.ts';

export interface HeaCapabilities {
  available: boolean;
  checkedAt: string;
  error: string | null;
  /**
   * `demo_permitido` do SERVIDOR para o serviço HEA (GET /api/v1/meta/capabilities). Em produção
   * a demonstração é proibida (princípio 3 do projeto), e a interface tem de obedecer: `false`
   * desliga a política de demonstração, mesmo que a preferência local peça o contrário.
   * `null` = o servidor não respondeu, logo não há política dele a respeitar.
   */
  demoAllowed: boolean | null;
}

/** Só o que a interface precisa de /meta/capabilities (o resto do contrato é ignorado de propósito). */
const CapabilitiesInfo = z.object({
  ambiente: z.string(),
  hea: z.object({ disponivel: z.boolean(), demo_permitido: z.boolean() }).passthrough(),
}).passthrough();

/**
 * Política de demonstração do servidor para o HEA. Falha de rede devolve `null` (desconhecida):
 * nada é inventado e o front não finge que o servidor autorizou.
 */
export async function detectDemoPolicy(signal?: AbortSignal): Promise<boolean | null> {
  try {
    const caps = await requestJson(`${config.apiBase}/api/v1/meta/capabilities`, { signal, schema: CapabilitiesInfo, timeoutMs: 5000 });
    return caps.hea.demo_permitido;
  } catch (err) {
    if (err instanceof ApiError && err.kind === 'aborted') throw err;
    return null;
  }
}

export async function detectHea(signal?: AbortSignal): Promise<{ caps: HeaCapabilities; bootstrap: HeaBootstrap | null }> {
  const checkedAt = new Date().toISOString();
  // a política de demonstração é perguntada ao servidor JUNTO da disponibilidade: ela vale mesmo
  // quando o serviço responde (produção com demonstração proibida)
  const [bootstrap, demoAllowed] = await Promise.all([
    requestJson(`${config.apiBase}/api/v1/hea/bootstrap`, { signal, schema: HeaBootstrap, timeoutMs: 5000 })
      .then((b) => ({ ok: true as const, b }))
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.kind === 'aborted') throw err;
        return { ok: false as const, error: err instanceof Error ? err.message : String(err) };
      }),
    detectDemoPolicy(signal),
  ]);
  if (bootstrap.ok) return { caps: { available: true, checkedAt, error: null, demoAllowed }, bootstrap: bootstrap.b };
  return { caps: { available: false, checkedAt, error: bootstrap.error, demoAllowed }, bootstrap: null };
}

export async function analyzeHea(name: string, composition: Record<string, number>, signal?: AbortSignal): Promise<HeaResult> {
  return requestJson(`${config.apiBase}/api/v1/hea/analyses`, { body: { nome: name, composicao: composition }, signal, schema: HeaResult });
}
