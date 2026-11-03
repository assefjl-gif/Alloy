/** Configuração de implantação, lida de public/config.js (globalThis.ALLOY_CONFIG). */
export type DemoPolicy = 'auto' | 'on' | 'off';

export interface AlloyConfig {
  /** Prefixo da API unificada; '.' = mesmo domínio e mesmo caminho do front (ADR-011). */
  apiBase: string;
  demo: DemoPolicy;
  version: string;
  buildId: string;
}

function trimSlash(s: string): string {
  return s.endsWith('/') ? s.slice(0, -1) : s;
}

function readQueryDemo(): DemoPolicy | null {
  try {
    const q = new URLSearchParams(window.location.search);
    const v = q.get('demo');
    if (v === '1' || v === 'on') return 'on';
    if (v === '0' || v === 'off') return 'off';
  } catch {
    /* fora do navegador */
  }
  return null;
}

const runtime: AlloyRuntimeConfig = (typeof ALLOY_CONFIG !== 'undefined' && ALLOY_CONFIG) || {};

export const config: AlloyConfig = {
  apiBase: trimSlash(runtime.apiBase ?? '.'),
  demo: readQueryDemo() ?? runtime.demo ?? 'auto',
  version: typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.0.0-test',
  buildId: typeof __BUILD_ID__ !== 'undefined' ? __BUILD_ID__ : 'test',
};
