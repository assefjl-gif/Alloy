/**
 * Transporte do resultado HEA pela URL (5.3). O resultado completo (com a curva G×T) não cabe
 * no limite de 1 800 caracteres da URL de cena; por isso a URL leva só uma referência
 * `h=<impressão digital>` e a cópia fica no sessionStorage da aba. Ao ler, a impressão digital
 * é recalculada: qualquer alteração do conteúdo invalida o transporte (dado imutável).
 */
import { HeaResult } from '../../services/api/contracts.ts';
import { hashSeed } from '../../utils/rng.ts';
import { deepFreeze } from '../../utils/freeze.ts';
import { readSession, writeSession } from '../../utils/storage.ts';
import type { HeaTransfer } from './transfer.ts';

const KEY = (id: string) => `alloy.hea.transfer.${id}`;

export function fingerprint(json: string): string {
  return `${hashSeed(json).toString(36)}${hashSeed(`${json.length}:${json}`).toString(36)}`;
}

export function persistTransfer(t: HeaTransfer): string {
  const json = JSON.stringify(t);
  const id = fingerprint(json);
  writeSession(KEY(id), json);
  return id;
}

export type RestoreResult = { ok: true; transfer: HeaTransfer } | { ok: false; reason: 'missing' | 'tampered' | 'schema' };

export function restoreTransfer(id: string): RestoreResult {
  if (!/^[a-z0-9]{4,32}$/.test(id)) return { ok: false, reason: 'schema' };
  const json = readSession(KEY(id));
  if (!json) return { ok: false, reason: 'missing' };
  if (fingerprint(json) !== id) return { ok: false, reason: 'tampered' };
  try {
    const raw = JSON.parse(json) as HeaTransfer;
    const result = HeaResult.safeParse(raw.result);
    if (raw.version !== 1 || !result.success || !['CS', 'CCC', 'CFC', 'HC'].includes(raw.structure?.code)) return { ok: false, reason: 'schema' };
    return { ok: true, transfer: deepFreeze(raw) };
  } catch {
    return { ok: false, reason: 'schema' };
  }
}
