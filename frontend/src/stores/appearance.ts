/**
 * Estado da APARÊNCIA da cena (T-22 / R2-FE-04). Só preferência de exibição: cor, tamanho e
 * transparência NÃO alteram valor, contagem nem composição — as grandezas continuam vindo do
 * motor (API) e nenhuma delas é guardada aqui.
 *
 * É lembrado entre sessões, como o resto do estado de interface (`stores/crystalUi.ts`), porque
 * é escolha de exibição. O que a cor significa é dito pela legenda (ver `SceneHud.tsx`).
 */
import { create } from 'zustand';
import { readJSON, writeJSON } from '../utils/storage.ts';
import {
  clamp, DEFAULT_APPEARANCE, normalizeColor, OPACITY_RANGE, SCALE_RANGE,
  type AppearanceOverrides, type AppearanceSettings,
} from '../features/viewer3d/appearance.ts';

/** Nível da cor: átomo > grupo > elemento (ver `features/viewer3d/appearance.ts`). */
export type ColorLevel = 'elements' | 'groups' | 'atoms';

export interface AppearanceState extends AppearanceSettings {
  set: (patch: Partial<AppearanceSettings>) => void;
  /** define (ou remove, com `null`) a cor de um elemento, grupo ou átomo */
  setColor: (level: ColorLevel, key: string, color: string | null) => void;
  /** volta ao padrão só as cores (de um nível, ou de todos) */
  resetColors: (level?: ColorLevel) => void;
  /** volta ao padrão a aparência da célula (vértices e arestas) */
  resetCell: () => void;
  /** volta ao padrão tamanho e transparência dos átomos */
  resetAtoms: () => void;
  /** volta TUDO ao padrão */
  resetAll: () => void;
}

const KEY = 'alloy.appearance';

function sanitizeMap(raw: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  if (!raw || typeof raw !== 'object') return out;
  for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
    const color = typeof v === 'string' ? normalizeColor(v) : null;
    if (color && k) out[k] = color;
  }
  return out;
}

function initial(): AppearanceSettings {
  const saved = readJSON<Partial<AppearanceSettings>>(KEY, {});
  const ov = (saved.overrides ?? {}) as Partial<AppearanceOverrides>;
  return {
    overrides: { elements: sanitizeMap(ov.elements), groups: sanitizeMap(ov.groups), atoms: sanitizeMap(ov.atoms) },
    vertexColor: typeof saved.vertexColor === 'string' ? normalizeColor(saved.vertexColor) : null,
    edgeColor: typeof saved.edgeColor === 'string' ? normalizeColor(saved.edgeColor) : null,
    vertices: typeof saved.vertices === 'boolean' ? saved.vertices : DEFAULT_APPEARANCE.vertices,
    atomScale: clamp(Number(saved.atomScale ?? DEFAULT_APPEARANCE.atomScale), SCALE_RANGE.min, SCALE_RANGE.max),
    opacity: clamp(Number(saved.opacity ?? DEFAULT_APPEARANCE.opacity), OPACITY_RANGE.min, OPACITY_RANGE.max),
  };
}

function withColor(overrides: AppearanceOverrides, level: ColorLevel, key: string, color: string | null): AppearanceOverrides {
  const next = { ...overrides[level] };
  const parsed = color === null ? null : normalizeColor(color);
  if (parsed === null) delete next[key];
  else next[key] = parsed;
  return { ...overrides, [level]: next };
}

export const useAppearance = create<AppearanceState>()((set) => ({
  ...initial(),
  set: (patch) => set((s) => ({
    ...patch,
    ...(patch.atomScale === undefined ? {} : { atomScale: clamp(patch.atomScale, SCALE_RANGE.min, SCALE_RANGE.max) }),
    ...(patch.opacity === undefined ? {} : { opacity: clamp(patch.opacity, OPACITY_RANGE.min, OPACITY_RANGE.max) }),
    overrides: patch.overrides ?? s.overrides,
  })),
  setColor: (level, key, color) => set((s) => ({ overrides: withColor(s.overrides, level, key, color) })),
  resetColors: (level) => set((s) => ({
    overrides: level ? { ...s.overrides, [level]: {} } : { elements: {}, groups: {}, atoms: {} },
  })),
  resetCell: () => set({ vertexColor: null, edgeColor: null, vertices: DEFAULT_APPEARANCE.vertices }),
  resetAtoms: () => set({ atomScale: DEFAULT_APPEARANCE.atomScale, opacity: DEFAULT_APPEARANCE.opacity }),
  resetAll: () => set({ ...DEFAULT_APPEARANCE, overrides: { elements: {}, groups: {}, atoms: {} } }),
}));

useAppearance.subscribe((s) => writeJSON(KEY, {
  overrides: s.overrides, vertexColor: s.vertexColor, edgeColor: s.edgeColor,
  vertices: s.vertices, atomScale: s.atomScale, opacity: s.opacity,
}));

/** Instantâneo das preferências de aparência (para o viewer, que não usa React). */
export function appearanceSnapshot(s: AppearanceState = useAppearance.getState()): AppearanceSettings {
  return { overrides: s.overrides, vertexColor: s.vertexColor, edgeColor: s.edgeColor, vertices: s.vertices, atomScale: s.atomScale, opacity: s.opacity };
}
