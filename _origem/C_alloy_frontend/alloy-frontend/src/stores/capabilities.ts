import { create } from 'zustand';
import { config } from '../config.ts';
import type { CrystalabCapabilities } from '../services/api/crystalab.ts';
import type { HeaCapabilities } from '../services/api/hea.ts';
import { resolveMode, type ServiceMode } from '../services/adapters/mode.ts';
import { usePreferences } from './preferences.ts';

export interface CapabilitiesState {
  crystalab: CrystalabCapabilities | null;
  hea: HeaCapabilities | null;
  online: boolean;
  /** true depois da primeira detecção (evita piscar "indisponível" na carga). */
  ready: boolean;
  set: (patch: Partial<Omit<CapabilitiesState, 'set'>>) => void;
}

export const useCapabilities = create<CapabilitiesState>()((set) => ({
  crystalab: null,
  hea: null,
  online: globalThis.navigator?.onLine ?? true,
  ready: false,
  set: (patch) => set(patch),
}));

export function demoPolicy(): typeof config.demo {
  const pref = usePreferences.getState().demo;
  return pref === 'config' ? config.demo : pref;
}

export type ServiceName = 'crystalab' | 'hea' | 'classroom' | 'ai' | 'exportCif' | 'workspaceServer';

/** Modo efetivo de cada serviço, considerando disponibilidade e política de demonstração. */
export function serviceMode(name: ServiceName, s: CapabilitiesState = useCapabilities.getState(), policy = demoPolicy()): ServiceMode {
  switch (name) {
    case 'crystalab':
      return resolveMode(policy === 'on' ? 'auto' : policy, s.crystalab?.api !== undefined && s.crystalab.api !== 'none', false);
    case 'exportCif':
      return resolveMode('off', (s.crystalab?.exportFormats.length ?? 0) > 0, false);
    case 'hea':
      return resolveMode(policy, Boolean(s.hea?.available), true);
    case 'classroom':
      return resolveMode(policy, false, true);
    case 'ai':
    case 'workspaceServer':
      return resolveMode('off', false, false);
    default:
      return 'disabled';
  }
}

export function useServiceMode(name: ServiceName): ServiceMode {
  const caps = useCapabilities();
  const pref = usePreferences((p) => p.demo);
  return serviceMode(name, caps, pref === 'config' ? config.demo : pref);
}
