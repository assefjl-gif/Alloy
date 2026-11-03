/**
 * Conta e sessão (/api/v1/auth, /api/v1/me — ADR-008). O token de sessão fica SÓ no cookie
 * HttpOnly (o front nunca o vê); o token anti-CSRF vem no corpo do login e do /auth/me, fica só
 * em memória e é enviado por http.ts em toda escrita.
 */
import { z } from 'zod';
import { config } from '../../config.ts';
import { ApiError, requestJson, setCsrfToken } from './http.ts';

export const UserInfo = z.object({ id: z.string(), nome: z.string(), email: z.string(), admin_geral: z.boolean(), email_verificado: z.boolean() });
export type UserInfo = z.infer<typeof UserInfo>;
const SessionInfo = z.object({ usuario: UserInfo, csrf: z.string(), expira_em: z.string() });
export const HistoryItem = z.object({
  id: z.string(), operacao: z.string(), motor: z.string(), versao_motor: z.string(), versao_dados: z.string(),
  classe: z.string(), parametros: z.record(z.string(), z.unknown()), criado_em: z.string(),
});
export type HistoryItem = z.infer<typeof HistoryItem>;
const HistoryPage = z.object({ total: z.number(), pagina: z.number(), limite: z.number(), itens: z.array(HistoryItem) });
export type HistoryPage = z.infer<typeof HistoryPage>;
const Count = z.object({ encerradas: z.number() });

const api = (path: string): string => `${config.apiBase}/api/v1${path}`;

/** Usuário da sessão atual; `null` se anônimo (401). Renova o CSRF guardado em memória. */
export async function currentUser(signal?: AbortSignal): Promise<UserInfo | null> {
  try {
    const s = await requestJson(api('/auth/me'), { signal, schema: SessionInfo, timeoutMs: 5000 });
    setCsrfToken(s.csrf);
    return s.usuario;
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) { setCsrfToken(null); return null; }
    throw err;
  }
}

export async function login(email: string, senha: string): Promise<UserInfo> {
  const s = await requestJson(api('/auth/login'), { body: { email, senha }, schema: SessionInfo });
  setCsrfToken(s.csrf);
  return s.usuario;
}

export async function register(nome: string, email: string, senha: string): Promise<UserInfo> {
  return requestJson(api('/auth/register'), { body: { nome, email, senha }, schema: UserInfo });
}

export async function logout(all = false): Promise<number> {
  const r = await requestJson(api(all ? '/auth/logout-all' : '/auth/logout'), { body: {}, schema: Count });
  setCsrfToken(null);
  return r.encerradas;
}

export async function history(page = 1, signal?: AbortSignal): Promise<HistoryPage> {
  return requestJson(api(`/me/history?pagina=${page}&limite=20`), { signal, schema: HistoryPage });
}
