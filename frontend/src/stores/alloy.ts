import { create } from 'zustand';
import type { AlloyRequest, AlloyResult, ThermalResult } from '../services/api/contracts.ts';

/**
 * Liga e temperatura no CrystaLab (T-13). Os resultados vêm da API; este store só os guarda.
 * `thermalTarget` diz a que o cálculo térmico se refere (material carregado ou liga formada),
 * para o viewer saber se a amplitude de vibração vale para os átomos exibidos.
 */
export type Status = 'idle' | 'loading' | 'error';

export interface AlloyState {
  alloy: AlloyResult | null;
  /** pedido que gerou `alloy` (o cálculo térmico da liga o reutiliza) */
  alloyRequest: AlloyRequest | null;
  alloyStatus: Status;
  alloyError: string | null;
  thermal: ThermalResult | null;
  thermalTarget: 'material' | 'alloy' | null;
  thermalStatus: Status;
  thermalError: string | null;
  vibration: { on: boolean; exaggeration: number };
  set: (patch: Partial<Omit<AlloyState, 'set'>>) => void;
  reset: () => void;
}

const INITIAL = {
  alloy: null,
  alloyRequest: null,
  alloyStatus: 'idle' as Status,
  alloyError: null,
  thermal: null,
  thermalTarget: null,
  thermalStatus: 'idle' as Status,
  thermalError: null,
  vibration: { on: false, exaggeration: 3 },
};

export const useAlloy = create<AlloyState>()((set) => ({
  ...INITIAL,
  set: (patch) => set(patch),
  reset: () => set({ ...INITIAL }),
}));
