/**
 * Roteador por hash (sem recarga, sem exigir reescrita no servidor Python).
 * Rotas: #/crystalab, #/hea, #/aprender[/<atividade>], #/professor, #/diario, #/catalogo, #/sobre, #/conta.
 * Estado de cena serializável vai em ?s=<v1.base64url> (ver features/url/sceneUrl.ts).
 */
import { useSyncExternalStore } from 'react';
import type { ModuleId } from '../commands/types.ts';

export interface Route {
  module: ModuleId;
  rest: string[];
  query: URLSearchParams;
}

const MODULES: ModuleId[] = ['crystalab', 'hea', 'aprender', 'professor', 'diario', 'catalogo', 'sobre', 'conta'];

export function parseHash(hash: string): Route {
  const clean = hash.replace(/^#\/?/, '');
  const [path = '', qs = ''] = clean.split('?');
  const parts = path.split('/').filter(Boolean).map((p) => decodeURIComponent(p));
  const first = parts[0] as ModuleId | undefined;
  const module = first && MODULES.includes(first) ? first : 'crystalab';
  return { module, rest: first && MODULES.includes(first) ? parts.slice(1) : [], query: new URLSearchParams(qs) };
}

let current = parseHash(typeof window !== 'undefined' ? window.location.hash : '');
let cachedHash = typeof window !== 'undefined' ? window.location.hash : '';
const listeners = new Set<() => void>();

function onHash(): void {
  if (window.location.hash === cachedHash) return;
  cachedHash = window.location.hash;
  current = parseHash(cachedHash);
  listeners.forEach((l) => l());
}

if (typeof window !== 'undefined') window.addEventListener('hashchange', onHash);

export function useRoute(): Route {
  return useSyncExternalStore(
    (l) => { listeners.add(l); return () => listeners.delete(l); },
    () => current,
    () => current,
  );
}

export function getRoute(): Route {
  return current;
}

export function hrefFor(module: ModuleId, rest: string[] = [], query?: Record<string, string>): string {
  const qs = query && Object.keys(query).length ? `?${new URLSearchParams(query).toString()}` : '';
  return `#/${[module, ...rest].map(encodeURIComponent).join('/')}${qs}`;
}

export function navigate(module: ModuleId, rest: string[] = [], query?: Record<string, string>, replace = false): void {
  const target = hrefFor(module, rest, query);
  if (replace) window.history.replaceState(null, '', target);
  else window.location.hash = target;
  onHash();
}

/** Atualiza só a query do hash atual sem criar entrada de histórico (estado de cena). */
export function replaceQuery(query: Record<string, string | null>): void {
  const r = getRoute();
  const q = new URLSearchParams(r.query);
  for (const [k, v] of Object.entries(query)) {
    if (v === null) q.delete(k);
    else q.set(k, v);
  }
  const obj: Record<string, string> = {};
  q.forEach((v, k) => { obj[k] = v; });
  navigate(r.module, r.rest, obj, true);
}
