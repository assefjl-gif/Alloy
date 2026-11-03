/** α-Fe (CCC) e γ-Fe (CFC) vêm ambos do motor — nada é interpolado como dado científico. */
import { crystalabApi } from '../../services/api/crystalab.ts';
import type { StructureResult } from '../../services/api/contracts.ts';

const cache: { from: StructureResult | null; to: StructureResult | null; loading: Promise<void> | null } = { from: null, to: null, loading: null };

export function loadAlphaGamma(): Promise<void> {
  if (cache.from && cache.to) return Promise.resolve();
  if (!cache.loading) {
    cache.loading = Promise.all([crystalabApi.structure({ nome: 'Fe' }), crystalabApi.structure({ nome: 'Fe', estrutura: 'CFC' })])
      .then(([a, g]) => { cache.from = a; cache.to = g; })
      .finally(() => { cache.loading = null; });
  }
  return cache.loading;
}

export function alphaGammaData(): { from: StructureResult | null; to: StructureResult | null } {
  return { from: cache.from, to: cache.to };
}
