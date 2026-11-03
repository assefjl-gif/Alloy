/**
 * Histórico de estado para desfazer/refazer (tarefa 2.8, usado na 4.10).
 * Um instantâneo guarda as RESPOSTAS do motor já recebidas — desfazer restaura a cena
 * sem reexecutar cálculos. Instantâneos são imutáveis (estruturas compartilhadas, não copiadas).
 */
import { create } from 'zustand';
import type { StructureRequest, StructureResult } from '../services/api/contracts.ts';
import { useCrystalab } from './crystalab.ts';
import { useOverlays, type OverlayItem } from './overlays.ts';
import { useViewer, type DisplaySettings } from './viewer.ts';

export interface SceneSnapshot {
  label: string;
  request: StructureRequest | null;
  structure: StructureResult | null;
  editorText: string;
  overlays: OverlayItem[];
  display: DisplaySettings;
  supercell: [number, number, number];
  densityVisible: boolean;
}

interface HistoryState {
  past: SceneSnapshot[];
  present: SceneSnapshot | null;
  future: SceneSnapshot[];
  set: (patch: Partial<Omit<HistoryState, 'set'>>) => void;
}

const LIMIT = 60;

export const useHistory = create<HistoryState>()((set) => ({ past: [], present: null, future: [], set: (patch) => set(patch) }));

export function captureScene(label: string): SceneSnapshot {
  const c = useCrystalab.getState();
  const v = useViewer.getState();
  return {
    label,
    request: c.request,
    structure: c.structure,
    editorText: c.editorText,
    overlays: useOverlays.getState().items,
    display: v.display,
    supercell: v.supercell,
    densityVisible: c.densityVisible,
  };
}

function applyScene(s: SceneSnapshot): void {
  useCrystalab.getState().set({ request: s.request, structure: s.structure, editorText: s.editorText, densityVisible: s.densityVisible, status: s.structure ? 'ready' : 'idle', error: null });
  useOverlays.getState().set({ items: s.overlays, selectedId: null });
  useViewer.getState().set({ display: s.display, supercell: s.supercell, selection: null, tool: null });
}

/** Registra o estado ATUAL como novo ponto do histórico (chamar depois de cada operação que muda a cena). */
export function commit(label: string): void {
  const h = useHistory.getState();
  const snap = captureScene(label);
  const past = h.present ? [...h.past, h.present].slice(-LIMIT) : h.past;
  h.set({ past, present: snap, future: [] });
}

export function undo(): SceneSnapshot | null {
  const h = useHistory.getState();
  const prev = h.past[h.past.length - 1];
  if (!prev || !h.present) return null;
  h.set({ past: h.past.slice(0, -1), present: prev, future: [h.present, ...h.future] });
  applyScene(prev);
  return h.present;
}

export function redo(): SceneSnapshot | null {
  const h = useHistory.getState();
  const next = h.future[0];
  if (!next || !h.present) return null;
  h.set({ past: [...h.past, h.present].slice(-LIMIT), present: next, future: h.future.slice(1) });
  applyScene(next);
  return next;
}

export function resetHistory(): void {
  useHistory.getState().set({ past: [], present: null, future: [] });
}
