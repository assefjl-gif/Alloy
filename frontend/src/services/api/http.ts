import type { ZodType } from 'zod';

/**
 * Cliente HTTP único. Toda chamada assíncrona aceita AbortSignal (cancelamento pelo usuário
 * ou por troca de contexto) e tem tempo-limite. Erros são normalizados em ApiError.
 * É o ÚNICO arquivo do front autorizado a chamar fetch() (regra verificada por scripts/lint.mjs).
 */
export type ApiErrorKind = 'network' | 'http' | 'domain' | 'aborted' | 'timeout' | 'contract' | 'unavailable';

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | undefined;
  readonly code: string | undefined;
  readonly url: string;

  constructor(kind: ApiErrorKind, message: string, url: string, status?: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
    this.code = code;
    this.url = url;
  }
}

/** Token anti-CSRF da sessão (ADR-008): só em memória; enviado em toda escrita. */
let csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export function isAbort(err: unknown): boolean {
  return err instanceof ApiError ? err.kind === 'aborted' : err instanceof DOMException && err.name === 'AbortError';
}

export interface RequestOptions<T> {
  method?: 'GET' | 'POST';
  body?: unknown;
  signal?: AbortSignal | undefined;
  timeoutMs?: number;
  /** Esquema de validação do conteúdo útil (após desembrulhar o envelope). */
  schema?: ZodType<T>;
  /** true: resposta tem envelope {ok, result|error}. 'raw': devolve o corpo inteiro. */
  envelope?: boolean | 'raw';
}

function combineSignals(signals: Array<AbortSignal | undefined>): AbortSignal {
  const list = signals.filter((s): s is AbortSignal => Boolean(s));
  if (typeof AbortSignal.any === 'function') return AbortSignal.any(list);
  const ctrl = new AbortController();
  for (const s of list) {
    if (s.aborted) ctrl.abort(s.reason);
    else s.addEventListener('abort', () => ctrl.abort(s.reason), { once: true });
  }
  return ctrl.signal;
}

export async function requestJson<T>(url: string, opts: RequestOptions<T> = {}): Promise<T> {
  const { method = opts.body === undefined ? 'GET' : 'POST', body, signal, timeoutMs = 15000, schema, envelope = true } = opts;
  const timeout = new AbortController();
  const timer = setTimeout(() => timeout.abort(new DOMException('timeout', 'TimeoutError')), timeoutMs);
  const combined = combineSignals([signal, timeout.signal]);
  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: {
        Accept: 'application/json',
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(method !== 'GET' && csrfToken ? { 'X-Alloy-CSRF': csrfToken } : {}),
      },
      credentials: 'same-origin',
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: combined,
      cache: 'no-store',
    });
  } catch (err) {
    clearTimeout(timer);
    if (signal?.aborted) throw new ApiError('aborted', 'Operação cancelada.', url);
    if (timeout.signal.aborted) throw new ApiError('timeout', `Sem resposta em ${Math.round(timeoutMs / 1000)} s.`, url);
    throw new ApiError('network', err instanceof Error ? err.message : 'Falha de rede.', url);
  }
  clearTimeout(timer);

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    if (response.status === 404) throw new ApiError('unavailable', 'Rota não encontrada.', url, 404);
    throw new ApiError('http', `Resposta não é JSON (HTTP ${response.status}).`, url, response.status);
  }
  const obj = (payload ?? {}) as Record<string, unknown>;
  if (response.status === 502 && obj.code === 'ENGINE_UNREACHABLE') {
    throw new ApiError('unavailable', String(obj.error ?? 'Motor indisponível.'), url, 502, 'ENGINE_UNREACHABLE');
  }
  if (envelope === true) {
    if (!response.ok || obj.ok === false) {
      const kind: ApiErrorKind = response.status === 404 ? 'unavailable' : response.status >= 500 ? 'http' : 'domain';
      throw new ApiError(kind, String(obj.error ?? `HTTP ${response.status}`), url, response.status, typeof obj.code === 'string' ? obj.code : undefined);
    }
  } else if (!response.ok) {
    throw new ApiError(response.status === 404 ? 'unavailable' : 'http', String(obj.error ?? `HTTP ${response.status}`), url, response.status);
  }
  const content = envelope === true ? obj.result : payload;
  if (!schema) return content as T;
  const parsed = schema.safeParse(content);
  if (!parsed.success) {
    const first = parsed.error.issues[0];
    throw new ApiError('contract', `Resposta fora do contrato em "${first?.path.join('.') || '(raiz)'}": ${first?.message ?? 'inválida'}.`, url, response.status, 'CONTRACT');
  }
  return parsed.data;
}
