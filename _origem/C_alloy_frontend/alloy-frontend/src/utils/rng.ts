/**
 * Gerador pseudoaleatório reproduzível (mulberry32). Todo conteúdo aleatório do app
 * (dados demonstrativos, embaralhamento de quiz, distribuição ilustrativa de elementos)
 * passa por aqui com uma semente explícita. `Math.random` é proibido pelo lint do projeto.
 */
export interface Rng {
  readonly seed: number;
  next(): number;
  int(min: number, max: number): number;
  range(min: number, max: number): number;
  pick<T>(items: readonly T[]): T;
  shuffle<T>(items: readonly T[]): T[];
  weighted<T>(items: readonly T[], weights: readonly number[]): T;
}

export function hashSeed(text: string): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < text.length; i += 1) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

export function createRng(seed: number | string): Rng {
  const s0 = typeof seed === 'string' ? hashSeed(seed) : seed >>> 0;
  let state = s0 || 0x9e3779b9;
  const next = (): number => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const rng: Rng = {
    seed: s0,
    next,
    int: (min, max) => Math.floor(next() * (max - min + 1)) + min,
    range: (min, max) => next() * (max - min) + min,
    pick: (items) => {
      if (!items.length) throw new Error('pick em lista vazia');
      return items[Math.floor(next() * items.length)] as (typeof items)[number];
    },
    shuffle: (items) => {
      const out = items.slice();
      for (let i = out.length - 1; i > 0; i -= 1) {
        const j = Math.floor(next() * (i + 1));
        const tmp = out[i] as (typeof out)[number];
        out[i] = out[j] as (typeof out)[number];
        out[j] = tmp;
      }
      return out;
    },
    weighted: (items, weights) => {
      const total = weights.reduce((a, b) => a + b, 0);
      let r = next() * total;
      for (let i = 0; i < items.length; i += 1) {
        r -= weights[i] ?? 0;
        if (r <= 0) return items[i] as (typeof items)[number];
      }
      return items[items.length - 1] as (typeof items)[number];
    },
  };
  return rng;
}
