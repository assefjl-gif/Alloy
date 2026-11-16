import { useEffect } from 'react';
import { dispatch, describeError, tr } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { StageLayout } from '../../design-system/layout/StageLayout.tsx';
import { CategoryBox } from '../../design-system/primitives/Category.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useCapabilities, useServiceMode } from '../../stores/capabilities.ts';
import { useOverlays } from '../../stores/overlays.ts';
import { useViewer } from '../../stores/viewer.ts';
import { useBarOpen, useCrystalUi, useNarrowViewport } from '../../stores/crystalUi.ts';
import { log } from '../../stores/terminal.ts';
import { toast } from '../../stores/toast.ts';
import { getRoute, replaceQuery, useRoute } from '../../app/router.ts';
import { applyStructure, loadStructure } from '../../commands/handlers.ts';
import { persistTransfer as persistTransferId, restoreTransfer } from '../hea/transferUrl.ts';
import { captureSceneState, decodeScene, encodeScene } from '../../features/url/sceneUrl.ts';
import { restoreScene } from '../../features/url/restore.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { SceneStage } from './ViewerPanel.tsx';
import { BAR_ID, SceneHud, SceneNotices } from './SceneHud.tsx';
import { Sidebar } from './Sidebar.tsx';

function EngineUnavailable() {
  const { t } = useI18n();
  const caps = useCapabilities((s) => s.crystalab);
  return (
    <CategoryBox category="feedback" as="section" className="engine-off" role="status" data-testid="engine-unavailable">
      <h2>{t('engine.offTitle')}</h2>
      <p>{t('engine.offBody')}</p>
      {caps?.error ? <p className="ds-mono ds-field__hint">{caps.error}</p> : null}
      <p className="ds-field__hint">{t('engine.offHow')}</p>
    </CategoryBox>
  );
}

let lastWritten: string | null = null;
let lastRestored: string | null = null;

/** Mantém ?s= da URL em sincronia com a cena (sem criar histórico) e restaura links abertos. */
function useSceneUrlSync(): void {
  const route = useRoute();
  const param = route.query.get('s');
  // a restauração só começa depois da detecção do motor (antes disso nenhum cálculo é possível)
  const ready = useCapabilities((c) => c.ready);
  const mode = useServiceMode('crystalab');
  useEffect(() => {
    if (!ready || !param || param === lastWritten || param === lastRestored) return;
    lastRestored = param;
    const decoded = decodeScene(param);
    if (!decoded.ok) {
      toast({ tone: 'error', title: tr('share.invalidTitle'), body: tr(`share.invalid.${decoded.reason}`) });
      log('error', `${tr('share.invalidTitle')}: ${tr(`share.invalid.${decoded.reason}`)}`);
      replaceQuery({ s: null });
      if (mode === 'live' && !useCrystalab.getState().structure) void dispatch({ type: 'material.load', request: { nome: 'Fe' } }, 'system');
      return;
    }
    if (mode !== 'live') return;
    const ctrl = new AbortController();
    restoreScene(decoded.scene, ctrl.signal, 'link', { keepHea: Boolean(getRoute().query.get('h')) }).catch((err) => log('error', describeError(err)));
  }, [param, ready, mode]);
  // resultado HEA transportado (5.3): restaura da referência h= e a remove quando a cena deixa de ser HEA
  const heaRef = route.query.get('h');
  useEffect(() => {
    if (!heaRef || !ready) return;
    const current = useCrystalab.getState().heaTransfer;
    if (current && persistTransferId(current) === heaRef) return;
    const res = restoreTransfer(heaRef);
    if (res.ok) {
      useCrystalab.getState().set({ heaTransfer: res.transfer });
      // link só com h= (sem estado de cena): abre a célula idealizada da estrutura transportada
      if (!getRoute().query.get('s') && !useCrystalab.getState().structure) {
        const request = { nome: res.transfer.structure.code };
        void loadStructure(request, new AbortController().signal).then((st) => { if (st) applyStructure(st, request, { keepHea: true }); }).catch((err) => log('error', describeError(err)));
      }
    }
    else { log('warn', tr(`bridge.restore.${res.reason}`)); replaceQuery({ h: null }); }
  }, [heaRef, ready]);
  useEffect(() => useCrystalab.subscribe((st, prev) => { if (prev.heaTransfer && !st.heaTransfer) replaceQuery({ h: null }); }), []);
  useEffect(() => {
    let timer = 0;
    const write = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        const scene = captureSceneState(true);
        if (!scene) return;
        const enc = encodeScene(scene);
        if (enc.length > 1800 || enc === lastWritten) return;
        lastWritten = enc;
        replaceQuery({ s: enc });
      }, 700);
    };
    const u1 = useCrystalab.subscribe((s, p) => { if (s.structure !== p.structure || s.densityVisible !== p.densityVisible) write(); });
    const u2 = useOverlays.subscribe((s, p) => { if (s.items !== p.items) write(); });
    const u3 = useViewer.subscribe((s, p) => { if (s.camera !== p.camera || s.display !== p.display || s.supercell !== p.supercell) write(); });
    return () => { u1(); u2(); u3(); window.clearTimeout(timer); };
  }, []);
}

export default function CrystaLabModule() {
  const { t } = useI18n();
  // carregar outro metal/estrutura invalida a liga e a temperatura calculadas para o anterior
  // (recarregar o MESMO metal, p.ex. ao restaurar a cena, não apaga a liga)
  useEffect(() => useCrystalab.subscribe((st, prev) => {
    const before = prev.structure;
    if (before && st.structure && (st.structure.rotulo !== before.rotulo || st.structure.estrutura !== before.estrutura)) useAlloy.getState().reset();
  }), []);
  const structure = useCrystalab((s) => s.structure);
  const status = useCrystalab((s) => s.status);
  const ready = useCapabilities((s) => s.ready);
  const mode = useServiceMode('crystalab');
  const route = useRoute();
  useSceneUrlSync();
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
      const el = e.target as HTMLElement | null;
      if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) return; // desfazer de texto continua nativo
      const k = e.key.toLowerCase();
      if (k === 'z' && !e.shiftKey) { e.preventDefault(); void dispatch({ type: 'history.undo' }, 'shortcut'); }
      else if ((k === 'z' && e.shiftKey) || k === 'y') { e.preventDefault(); void dispatch({ type: 'history.redo' }, 'shortcut'); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    if (!ready || mode !== 'live') return;
    const c = useCrystalab.getState();
    if (!c.structure && c.status !== 'loading' && !route.query.get('s') && !route.query.get('h')) void dispatch({ type: 'material.load', request: { nome: 'Fe' } }, 'system');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, mode]);

  const barOpen = useBarOpen();
  const wide = useCrystalUi((u) => u.wide);
  const narrow = useNarrowViewport();

  return (
    <StageLayout
      className="cl-layout"
      bar={<Sidebar />}
      barId={BAR_ID}
      barLabel={t('side.label')}
      open={barOpen}
      wide={wide}
      {...(narrow ? { onDismiss: () => useCrystalUi.getState().setBar(false), dismissLabel: t('bar.collapse') } : {})}
    >
      <main className="cl-main" id="main-content" data-testid="result-root" tabIndex={-1} aria-busy={status === 'loading' || undefined}>
        <SceneStage overlay={<SceneNotices />}>
          <SceneHud />
          {!ready ? <div className="cl-state"><Spinner size={22} label={t('engine.checking')} /></div> : null}
          {ready && mode !== 'live' ? <div className="cl-state"><EngineUnavailable /></div> : null}
          {ready && mode === 'live' && !structure ? <div className="cl-state"><Spinner size={22} label={t('common.loading')} /></div> : null}
        </SceneStage>
      </main>
    </StageLayout>
  );
}
