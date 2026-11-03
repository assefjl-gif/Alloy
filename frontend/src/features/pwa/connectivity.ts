/**
 * Conectividade (7.12/7.13): combina navigator.onLine com um ping leve ao motor.
 * Ao reconectar, informa quantas notas foram criadas offline (ficam neste navegador; D-18).
 */
import { useCapabilities } from '../../stores/capabilities.ts';
import { toast } from '../../stores/toast.ts';
import { tr } from '../../commands/bus.ts';
import { detectEngines } from '../../app/boot.ts';
import { countOfflineNotes, markNotesSynced } from '../../modules/notebook/store.ts';

let started = false;

export function startConnectivity(): void {
  if (started) return;
  started = true;
  const set = useCapabilities.getState().set;
  window.addEventListener('offline', () => {
    set({ online: false });
    toast({ tone: 'warning', title: tr('pwa.offlineTitle'), body: tr('pwa.offlineBody') });
  });
  window.addEventListener('online', () => {
    set({ online: true });
    void detectEngines();
    const n = countOfflineNotes();
    toast({
      tone: 'info',
      title: tr('pwa.onlineTitle'),
      body: n ? tr('pwa.onlineNotes', { n }) : tr('pwa.onlineBody'),
      ...(n ? { action: { label: tr('pwa.reviewNotes'), run: () => { window.location.hash = '#/diario'; markNotesSynced(); } } } : {}),
      timeout: n ? 0 : 6000,
    });
  });
}
