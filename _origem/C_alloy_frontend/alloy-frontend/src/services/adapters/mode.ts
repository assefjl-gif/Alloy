import type { DemoPolicy } from '../../config.ts';

/**
 * Modo efetivo de cada serviço:
 *  - live      → serviço real respondendo;
 *  - demo      → serviço ausente (ou demonstração forçada) e existe implementação demonstrativa;
 *  - disabled  → serviço ausente e não há demonstração (ou a política proíbe): recurso desativado com explicação.
 * Nunca há "simulação silenciosa": todo conteúdo em modo demo é rotulado na interface.
 */
export type ServiceMode = 'live' | 'demo' | 'disabled';

export function resolveMode(policy: DemoPolicy, available: boolean, hasDemo: boolean): ServiceMode {
  if (policy === 'on') return hasDemo ? 'demo' : available ? 'live' : 'disabled';
  if (available) return 'live';
  if (policy === 'off') return 'disabled';
  return hasDemo ? 'demo' : 'disabled';
}
