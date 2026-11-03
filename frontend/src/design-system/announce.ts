/**
 * Anúncios para leitores de tela (aria-live). Duas regiões globais são montadas pelo AppShell:
 * #alloy-live-polite (resultados, carregamento) e #alloy-live-assertive (erros).
 * O texto é limpo e reescrito para que anúncios repetidos sejam lidos de novo.
 */
export function announce(text: string, politeness: 'polite' | 'assertive' = 'polite'): void {
  const el = typeof document !== 'undefined' ? document.getElementById(`alloy-live-${politeness}`) : null;
  if (!el) return;
  el.textContent = '';
  window.setTimeout(() => {
    el.textContent = text;
  }, 30);
}
