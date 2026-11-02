/**
 * Acesso seguro ao localStorage. Pode falhar (janela privada, dados bloqueados, cota):
 * toda leitura/escrita é protegida e o app funciona sem armazenamento.
 */
export function readJSON<T>(key: string, fallback: T): T {
  try {
    const raw = globalThis.localStorage?.getItem(key);
    if (raw == null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function writeJSON(key: string, value: unknown): boolean {
  try {
    globalThis.localStorage?.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function removeKey(key: string): void {
  try {
    globalThis.localStorage?.removeItem(key);
  } catch {
    /* ignora */
  }
}

export function readRaw(key: string): string | null {
  try {
    return globalThis.localStorage?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

export function storageAvailable(): boolean {
  try {
    const k = '__alloy_probe__';
    globalThis.localStorage.setItem(k, '1');
    globalThis.localStorage.removeItem(k);
    return true;
  } catch {
    return false;
  }
}

/** sessionStorage (dura só a sessão da aba): usado para dados transportados entre módulos. */
export function readSession(key: string): string | null {
  try {
    return globalThis.sessionStorage?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

export function writeSession(key: string, value: string): boolean {
  try {
    globalThis.sessionStorage?.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}
