/**
 * Estado de interface do CrystaLab (R1-FE-01): barra lateral única, seções expansíveis,
 * legenda da cena e modo dos botões de câmera. Só apresentação: nenhuma grandeza científica.
 */
import { useSyncExternalStore } from 'react';
import { create } from 'zustand';
import { readJSON, writeJSON } from '../utils/storage.ts';

export const SECTION_IDS = ['structure', 'composition', 'selection', 'properties', 'appearance', 'analysis'] as const;
export type SectionId = (typeof SECTION_IDS)[number];

/** Seção (`analysis`) ou subseção (`analysis.thermal`). */
export type PanelId = SectionId | `${SectionId}.${string}`;

/** Abaixo desta largura a barra vira gaveta sobreposta à cena (mesmo valor em components.css). */
export const NARROW_QUERY = '(max-width: 960px)';

export interface CrystalUiState {
  /** barra aberta em tela larga (lembrado) */
  sidebarOpen: boolean;
  /** gaveta aberta em tela estreita (não é lembrado: a cena aparece primeiro) */
  drawerOpen: boolean;
  /** barra larga, para tabelas e passo a passo */
  wide: boolean;
  /** legenda sobre a cena */
  legend: boolean;
  /** os botões de seta sobre a cena giram ou deslocam a câmera */
  cameraMode: 'rotate' | 'pan';
  open: Record<string, boolean>;
  set: (patch: Partial<Omit<CrystalUiState, 'set' | 'toggle' | 'reveal' | 'setBar'>>) => void;
  toggle: (id: PanelId, value?: boolean) => void;
  /** Expande a seção (e a subseção). Com `showBar`, também abre a barra/gaveta. */
  reveal: (id: PanelId, showBar?: boolean) => void;
  setBar: (open: boolean) => void;
}

const KEY = 'alloy.crystalab.ui';

/** O essencial fica aberto; controles avançados começam recolhidos. */
export const DEFAULT_OPEN: Record<string, boolean> = {
  structure: true,
  'structure.material': true,
  properties: true,
  'properties.summary': true,
  'analysis.miller': true,
};

function isNarrow(): boolean {
  return Boolean(globalThis.matchMedia?.(NARROW_QUERY).matches);
}

const saved = readJSON<Partial<Pick<CrystalUiState, 'sidebarOpen' | 'wide' | 'legend' | 'open'>>>(KEY, {});

export const useCrystalUi = create<CrystalUiState>()((set) => ({
  sidebarOpen: saved.sidebarOpen ?? true,
  drawerOpen: false,
  wide: saved.wide ?? false,
  legend: saved.legend ?? true,
  cameraMode: 'rotate',
  open: { ...DEFAULT_OPEN, ...(saved.open ?? {}) },
  set: (patch) => set(patch),
  toggle: (id, value) => set((s) => ({ open: { ...s.open, [id]: value ?? !s.open[id] } })),
  reveal: (id, showBar = false) => set((s) => {
    const section = id.split('.')[0] as SectionId;
    const open = { ...s.open, [section]: true, [id]: true };
    if (!showBar) return { open };
    return isNarrow() ? { open, drawerOpen: true } : { open, sidebarOpen: true };
  }),
  setBar: (open) => set(isNarrow() ? { drawerOpen: open } : { sidebarOpen: open }),
}));

useCrystalUi.subscribe((s) => writeJSON(KEY, { sidebarOpen: s.sidebarOpen, wide: s.wide, legend: s.legend, open: s.open }));

function subscribeNarrow(cb: () => void): () => void {
  const mq = globalThis.matchMedia?.(NARROW_QUERY);
  mq?.addEventListener('change', cb);
  return () => mq?.removeEventListener('change', cb);
}

/** Verdadeiro quando a barra é gaveta sobreposta (tela estreita). */
export function useNarrowViewport(): boolean {
  return useSyncExternalStore(subscribeNarrow, isNarrow, () => false);
}

/** Barra visível agora, considerando a largura da janela. */
export function useBarOpen(): boolean {
  const narrow = useNarrowViewport();
  const sidebar = useCrystalUi((s) => s.sidebarOpen);
  const drawer = useCrystalUi((s) => s.drawerOpen);
  return narrow ? drawer : sidebar;
}
