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

/**
 * Política de demonstração do SERVIDOR (`demo_permitido` de GET /api/v1/meta/capabilities).
 * Em produção a demonstração é PROIBIDA (princípio 3 do projeto) e o servidor devolve `false`;
 * a interface obedece, ainda que a preferência local ou `public/config.js` peçam demonstração.
 * `null` (servidor não respondeu) não é tratado como autorização nem como proibição: a política
 * local continua valendo, porque não há decisão do servidor a respeitar.
 */
export function serverDemoAllowed(name: ServiceName, s: CapabilitiesState = useCapabilities.getState()): boolean | null {
  return name === 'hea' ? (s.hea?.demoAllowed ?? null) : null;
}

/** Política efetiva: a proibição do servidor desliga a demonstração (nunca o contrário). */
export function effectivePolicy(name: ServiceName, s: CapabilitiesState, policy: typeof config.demo): typeof config.demo {
  return serverDemoAllowed(name, s) === false ? 'off' : policy;
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
      // servidor proibindo demonstração ⇒ 'off': sem dado o serviço fica `disabled`, nunca `demo`
      return resolveMode(effectivePolicy('hea', s, policy), Boolean(s.hea?.available), true);
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
