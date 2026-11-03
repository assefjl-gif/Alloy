import { ApiError } from './http.ts';

/**
 * Coordena chamadas concorrentes por chave ("estrutura", "miller"...):
 *  - uma nova chamada cancela a anterior com a mesma chave (AbortController);
 *  - uma resposta que chega depois de uma chamada mais nova é marcada como obsoleta
 *    e descartada pelo chamador (nunca sobrescreve o estado atual);
 *  - `invalidate(chave)` torna obsoletas as chamadas em andamento quando o contexto muda
 *    (ex.: trocar de estrutura enquanto um plano de Miller ainda está sendo calculado).
 */
export interface LatestOutcome<T> {
  value: T;
  stale: boolean;
}

export class LatestRunner {
  private generation = new Map<string, number>();
  private controllers = new Map<string, AbortController>();

  async run<T>(key: string, task: (signal: AbortSignal) => Promise<T>, options: { cancelPrevious?: boolean } = {}): Promise<LatestOutcome<T>> {
    const gen = (this.generation.get(key) ?? 0) + 1;
    this.generation.set(key, gen);
    if (options.cancelPrevious !== false) this.controllers.get(key)?.abort();
    const ctrl = new AbortController();
    this.controllers.set(key, ctrl);
    try {
      const value = await task(ctrl.signal);
      return { value, stale: this.generation.get(key) !== gen };
    } finally {
      if (this.controllers.get(key) === ctrl) this.controllers.delete(key);
    }
  }

  cancel(key: string): boolean {
    const ctrl = this.controllers.get(key);
    if (!ctrl) return false;
    ctrl.abort();
    this.controllers.delete(key);
    this.generation.set(key, (this.generation.get(key) ?? 0) + 1);
    return true;
  }

  invalidate(key: string): void {
    this.generation.set(key, (this.generation.get(key) ?? 0) + 1);
    this.controllers.get(key)?.abort();
    this.controllers.delete(key);
  }

  isRunning(key: string): boolean {
    return this.controllers.has(key);
  }
}

export const latest = new LatestRunner();

export function staleError(url: string): ApiError {
  return new ApiError('aborted', 'Resultado descartado: o contexto mudou durante o cálculo.', url, undefined, 'STALE');
}
