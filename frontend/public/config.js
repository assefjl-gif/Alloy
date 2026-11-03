// Configuração de implantação do Alloy Virtual Lab (carregada antes do app; sem recompilar).
// apiBase: prefixo da API unificada (/api/v1). Padrão '.': mesmo domínio do front (Caddy — ADR-010);
//          em desenvolvimento, scripts/serve.mjs faz o proxy para o backend.
// demo: 'auto' (demonstrativo só para serviços ausentes) | 'on' (força) | 'off' (nunca; recursos sem serviço ficam desativados).
globalThis.ALLOY_CONFIG = {
  apiBase: '.',
  demo: 'auto',
};
