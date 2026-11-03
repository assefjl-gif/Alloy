/**
 * Escolha reproduzível do material de uma atividade (6.3): a semente decide entre os materiais
 * elegíveis que existem no catálogo do motor. Mesma semente → mesmo material, em qualquer máquina.
 */
import { createRng, hashSeed } from '../../utils/rng.ts';
import type { Activity } from './model.ts';

/** Material escolhido pela semente entre os elegíveis que o catálogo do motor contém. */
export function chooseMaterial(activity: Activity, seed: number, catalog: string[] | null): string {
  if (activity.fixedMaterial) return activity.fixedMaterial;
  const pool = catalog ? activity.pool.filter((p) => catalog.includes(p)) : activity.pool;
  if (!pool.length) return activity.pool[0] ?? 'Fe';
  return createRng(seed + hashSeed(activity.id)).pick(pool);
}

export function defaultSeed(activityId: string): number {
  return 1000 + (hashSeed(activityId) % 9000);
}

