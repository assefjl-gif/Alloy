declare const __APP_VERSION__: string;
declare const __BUILD_ID__: string;

declare module '*.svg' {
  const content: string;
  export default content;
}

interface AlloyRuntimeConfig {
  crystalabBase?: string;
  heaBase?: string;
  demo?: 'auto' | 'on' | 'off';
}

// eslint-disable-next-line no-var
declare var ALLOY_CONFIG: AlloyRuntimeConfig | undefined;

interface Window {
  /** Ganchos de teste e medição (somente leitura de estado; ver docs/testes.md). */
  __alloy?: Record<string, unknown>;
}

declare module '*.css';
