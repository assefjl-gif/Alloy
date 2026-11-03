/**
 * Inicialização: registra handlers, detecta motores, carrega catálogos, liga conectividade
 * e o service worker. Nada aqui bloqueia a primeira pintura.
 */
import { registerAppHandlers, registerCrystalabHandlers } from '../commands/handlers.ts';
import { registerHeaHandlers } from '../modules/hea/handlers.ts';
import { crystalabApi, detectCrystalab } from '../services/api/crystalab.ts';
import { detectHea } from '../services/api/hea.ts';
import { demoBootstrap } from '../services/adapters/heaDemo.ts';
import { serviceMode, useCapabilities } from '../stores/capabilities.ts';
import { useCrystalab } from '../stores/crystalab.ts';
import { useHea } from '../modules/hea/store.ts';
import { effectiveTheme, prefersReducedMotion, usePreferences } from '../stores/preferences.ts';
import { log } from '../stores/terminal.ts';
import { useOverlays } from '../stores/overlays.ts';
import { useViewer } from '../stores/viewer.ts';
import { useHistory } from '../stores/history.ts';
import { refreshAccount } from '../stores/account.ts';
import { toast } from '../stores/toast.ts';
import { tr } from '../commands/bus.ts';
import { startConnectivity } from '../features/pwa/connectivity.ts';
import { registerServiceWorker } from '../features/pwa/sw-register.ts';

let booted = false;

export function applyDocumentPreferences(): void {
  const p = usePreferences.getState();
  const root = document.documentElement;
  root.dataset.theme = effectiveTheme(p.theme);
  root.lang = p.locale;
  if (p.motion === 'system') delete root.dataset.motion;
  else root.dataset.motion = p.motion === 'reduce' ? 'reduce' : 'full';
  root.dataset.reducedMotion = String(prefersReducedMotion(p.motion));
}

/**
 * Uma falha de detecção não é definitiva: na primeira carga a API pode demorar (cold start, ou o
 * navegador com as conexões ocupadas pela pré-carga do service worker). Tenta de novo com espera
 * crescente enquanto houver rede; a cena e o HEA reagem quando o modo passa a "live".
 */
const RETRY_MS = [1500, 4000, 10000];
let retries = 0;
let retryTimer = 0;

function scheduleRetry(apiDown: boolean): void {
  window.clearTimeout(retryTimer);
  if (!apiDown) { retries = 0; return; }
  if (retries >= RETRY_MS.length || !(globalThis.navigator?.onLine ?? true)) return;
  retryTimer = window.setTimeout(() => { retries += 1; void detectEngines(); }, RETRY_MS[retries]);
}

export async function detectEngines(): Promise<void> {
  const caps = useCapabilities.getState();
  const [cl, hea] = await Promise.all([detectCrystalab(), detectHea()]);
  caps.set({ crystalab: cl, hea: hea.caps, ready: true });
  scheduleRetry(cl.api === 'none');
  const heaMode = serviceMode('hea');
  if (heaMode === 'live' && hea.bootstrap) useHea.getState().set({ bootstrap: hea.bootstrap, origin: 'engine' });
  else if (heaMode === 'demo') useHea.getState().set({ bootstrap: demoBootstrap(), origin: 'demo' });
  else useHea.getState().set({ bootstrap: null, origin: null });
  if (cl.api !== 'none') {
    const c = useCrystalab.getState();
    if (!c.metals || !c.structures) {
      c.set({ catalogStatus: 'loading' });
      try {
        const [metals, structures] = await Promise.all([crystalabApi.metals(), crystalabApi.structures()]);
        useCrystalab.getState().set({ metals, structures, catalogStatus: 'ready' });
      } catch (err) {
        useCrystalab.getState().set({ catalogStatus: 'error' });
        log('error', err instanceof Error ? err.message : String(err));
      }
    }
  } else {
    useCrystalab.getState().set({ catalogStatus: useCrystalab.getState().metals ? 'ready' : 'error' });
  }
}

export function boot(): void {
  if (booted) return;
  booted = true;
  registerCrystalabHandlers();
  registerAppHandlers();
  registerHeaHandlers();
  applyDocumentPreferences();
  usePreferences.subscribe((s, prev) => {
    applyDocumentPreferences();
    if (s.demo !== prev.demo) void detectEngines();
  });
  window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener('change', applyDocumentPreferences);
  log('info', tr('terminal.ready'));
  void detectEngines().then(() => {
    const cl = useCapabilities.getState().crystalab;
    if (cl?.api === 'none') toast({ tone: 'warning', title: tr('engine.offTitle'), body: tr('engine.offBody') });
    void refreshAccount(cl?.api !== 'none');
  });
  startConnectivity();
  registerServiceWorker();
  window.__alloy = { ...(window.__alloy ?? {}), bootId: `${Date.now()}`, stores: { crystalab: useCrystalab, hea: useHea, capabilities: useCapabilities, preferences: usePreferences, overlays: useOverlays, viewer: useViewer, history: useHistory } };
}
