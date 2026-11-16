/**
 * Filtros, cortes e isolamento da CENA (T-23). Só exibição: nenhuma grandeza científica é guardada
 * nem calculada aqui, e filtrar não altera nenhum valor que a tela mostra — apenas o que aparece.
 * As contagens científicas continuam sendo as do motor; o que depende deste store é rotulado como
 * contagem de EXIBIÇÃO na interface.
 *
 * Três dimensões independentes, como o motor as informa: elemento (`elemento`), ocupação
 * (`ocupacao`) e sítio (`sitio.nome`; na célula do metal puro, o `tipo` do sítio). Nenhuma lista
 * de valores é fixada no código: os valores vêm da resposta da API.
 *
 * "Isolar X" é expresso como "ocultar todos os outros valores DAQUELA dimensão" — assim isolar e
 * ocultar usam o mesmo estado, as dimensões não interferem entre si, e `clear()` limpa tudo.
 */
import { create } from 'zustand';
import type { AxisIndex, CutMode, CutState } from '../features/viewer3d/visibility.ts';

/** Dimensões filtráveis. O nome é o do campo do motor que as origina. */
export type FilterDimension = 'elements' | 'occupations' | 'sites';

const FIELD: Record<FilterDimension, 'hiddenElements' | 'hiddenOccupations' | 'hiddenSites'> = {
  elements: 'hiddenElements',
  occupations: 'hiddenOccupations',
  sites: 'hiddenSites',
};

export interface SceneFilterState {
  hiddenElements: string[];
  hiddenOccupations: string[];
  hiddenSites: string[];
  cut: CutState | null;
  /** raio de EXIBIÇÃO em torno do átomo selecionado, em unidades de a (null = desligado) */
  neighbourhoodRadius: number | null;
  set: (patch: Partial<Pick<SceneFilterState, 'hiddenElements' | 'hiddenOccupations' | 'hiddenSites' | 'cut' | 'neighbourhoodRadius'>>) => void;
  /** oculta (ou mostra) um valor de uma dimensão */
  toggle: (dim: FilterDimension, value: string, hidden?: boolean) => void;
  /** mostra só `value` naquela dimensão, entre os `all` informados pela resposta do motor */
  isolate: (dim: FilterDimension, value: string, all: readonly string[]) => void;
  setCut: (patch: Partial<CutState> | null) => void;
  clear: () => void;
}

export const DEFAULT_CUT: CutState = { axis: 2, mode: 'below', position: 0.5, thickness: 0.3 };

export const useSceneFilter = create<SceneFilterState>()((set) => ({
  hiddenElements: [],
  hiddenOccupations: [],
  hiddenSites: [],
  cut: null,
  neighbourhoodRadius: null,
  set: (patch) => set(patch),
  toggle: (dim, value, hidden) => set((s) => {
    const field = FIELD[dim];
    const list = s[field];
    const next = (hidden ?? !list.includes(value)) ? (list.includes(value) ? list : [...list, value]) : list.filter((v) => v !== value);
    return { [field]: next } as Partial<SceneFilterState>;
  }),
  isolate: (dim, value, all) => set({ [FIELD[dim]]: all.filter((v) => v !== value) } as Partial<SceneFilterState>),
  setCut: (patch) => set((s) => (patch === null ? { cut: null } : { cut: { ...(s.cut ?? DEFAULT_CUT), ...patch } })),
  clear: () => set({ hiddenElements: [], hiddenOccupations: [], hiddenSites: [], cut: null, neighbourhoodRadius: null }),
}));

/** Eixos na ordem x, y, z (os rótulos vêm do i18n; aqui só a identidade do índice). */
export const AXES: readonly AxisIndex[] = [0, 1, 2];
export const CUT_MODES: readonly CutMode[] = ['below', 'above', 'slab'];

/** Verdadeiro quando algo está escondido ou cortado (a interface precisa avisar em voz alta). */
export function filterActive(s: Pick<SceneFilterState, 'hiddenElements' | 'hiddenOccupations' | 'hiddenSites' | 'cut' | 'neighbourhoodRadius'>): boolean {
  return s.hiddenElements.length > 0 || s.hiddenOccupations.length > 0 || s.hiddenSites.length > 0 || s.cut !== null || s.neighbourhoodRadius !== null;
}

export function hiddenOf(s: SceneFilterState, dim: FilterDimension): string[] {
  return s[FIELD[dim]];
}
