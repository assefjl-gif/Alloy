// Configuração de implantação do Alloy Virtual Lab (carregada antes do app; sem recompilar).
// crystalabBase / heaBase: prefixos onde cada motor responde (o servidor de desenvolvimento faz proxy).
// demo: 'auto' (demonstrativo só para serviços ausentes) | 'on' (força) | 'off' (nunca; recursos sem serviço ficam desativados).
globalThis.ALLOY_CONFIG = {
  crystalabBase: './engines/crystalab',
  heaBase: './engines/hea',
  demo: 'auto',
};
