import { create } from 'zustand';
import type { HeaBootstrap, HeaResult } from '../../services/api/contracts.ts';
import type { LoadStatus } from '../../stores/crystalab.ts';

export interface HeaState {
  bootstrap: HeaBootstrap | null;
  origin: 'engine' | 'demo' | null;
  selectedKey: string;
  editorText: string;
  name: string;
  userNamed: boolean;
  result: HeaResult | null;
  resultOrigin: 'engine' | 'demo' | null;
  status: LoadStatus;
  error: string | null;
  set: (patch: Partial<Omit<HeaState, 'set'>>) => void;
}

export const useHea = create<HeaState>()((set) => ({
  bootstrap: null,
  origin: null,
  selectedKey: '',
  editorText: '',
  name: '',
  userNamed: false,
  result: null,
  resultOrigin: null,
  status: 'idle',
  error: null,
  set: (patch) => set(patch),
}));

/** Mesmo formato do editor de composição do HEA v1.17 (`Fe=20` por linha). */
export function compositionToText(composition: Record<string, number>): string {
  return Object.entries(composition)
    .map(([el, v]) => `${el}=${Math.abs(v - Math.round(v)) < 1e-4 ? Math.round(v) : v.toFixed(2)}`)
    .join('\n');
}

/** Mesmo parser do HEA v1.17: pares elemento/valor separados por =, : ou espaço. */
export function parseComposition(text: string): Record<string, number> {
  const out: Record<string, number> = {};
  const re = /([A-Za-z][a-z]?)\s*(?:=|:|\s)\s*(-?\d+(?:[.,]\d+)?)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const raw = m[1] ?? '';
    const el = raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase();
    const v = Number((m[2] ?? '').replace(',', '.'));
    if (Number.isFinite(v) && v > 0) out[el] = v;
  }
  return out;
}
