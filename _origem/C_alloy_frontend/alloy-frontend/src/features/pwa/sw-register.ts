/** Registro do service worker (7.10). Só em produção servida por http(s); falhas não quebram o app. */
import { toast } from '../../stores/toast.ts';
import { tr } from '../../commands/bus.ts';

export function registerServiceWorker(): void {
  if (!('serviceWorker' in navigator) || location.protocol === 'file:') return;
  if (new URLSearchParams(location.search).get('sw') === '0') return;
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('./sw.js', { scope: './' })
      .then((reg) => {
        reg.addEventListener('updatefound', () => {
          const w = reg.installing;
          w?.addEventListener('statechange', () => {
            if (w.state === 'installed' && navigator.serviceWorker.controller) {
              toast({ tone: 'info', title: tr('pwa.updateTitle'), body: tr('pwa.updateBody'), action: { label: tr('pwa.reload'), run: () => location.reload() }, timeout: 0 });
            }
          });
        });
      })
      .catch(() => undefined);
  });
}
