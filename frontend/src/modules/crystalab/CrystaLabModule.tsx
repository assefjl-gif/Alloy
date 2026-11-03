import { useEffect, useRef, useState } from 'react';
import { dispatch, describeError, tr } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { Button, IconButton } from '../../design-system/primitives/Button.tsx';
import { Menu } from '../../design-system/primitives/Menu.tsx';
import { Tabs, TabPanel } from '../../design-system/primitives/Tabs.tsx';
import { CategoryBox } from '../../design-system/primitives/Category.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useHistory } from '../../stores/history.ts';
import { useCapabilities, useServiceMode } from '../../stores/capabilities.ts';
import { useOverlays } from '../../stores/overlays.ts';
import { useViewer } from '../../stores/viewer.ts';
import { log } from '../../stores/terminal.ts';
import { toast } from '../../stores/toast.ts';
import { getRoute, navigate, replaceQuery, useRoute } from '../../app/router.ts';
import { applyStructure, loadStructure } from '../../commands/handlers.ts';
import { captureSceneNote } from '../notebook/captureNote.ts';
import { persistTransfer as persistTransferId, restoreTransfer } from '../hea/transferUrl.ts';
import { exportAvailability } from '../../features/export/exporters.ts';
import { captureSceneState, decodeScene, encodeScene } from '../../features/url/sceneUrl.ts';
import { restoreScene } from '../../features/url/restore.ts';
import { deleteWorkspace, exportWorkspacesJson, importWorkspacesJson, listWorkspaces, type Workspace } from '../../features/workspace/workspaces.ts';
import { downloadText } from '../../features/export/download.ts';
import { LabPanel } from './LabPanel.tsx';
import { AtomCount, ComparisonTable, DensityPanel, Interpretation, MetricsGrid, StatusBand } from './Results.tsx';
import { ViewerPanel } from './ViewerPanel.tsx';
import { AnimationsPanel, AtomInspector, GuidedMode, MeasurementsPanel, OverlayManager } from './SidePanels.tsx';
import { HeaTransferBanner, ProvenancePanel } from './ProvenancePanel.tsx';
import type { ExportFormat } from '../../commands/types.ts';

const EXPORT_ICONS: Record<ExportFormat, 'file' | 'camera' | 'print' | 'download'> = { cif: 'file', xyz: 'file', png: 'camera', pdf: 'print', json: 'download' };

function Topbar({ onToggleSide, sideOpen }: { onToggleSide: () => void; sideOpen: boolean }) {
  const { t, locale } = useI18n();
  const r = useCrystalab((s) => s.structure);
  const status = useCrystalab((s) => s.status);
  const past = useHistory((s) => s.past.length);
  const future = useHistory((s) => s.future.length);
  useCapabilities((s) => s.crystalab);
  const exports = exportAvailability();
  return (
    <header className="topbar">
      <div className="topbar__title">
        <h1 id="resultTitle">{r?.rotulo ?? t('crystalab.unitCell')}</h1>
        <p id="resultSubtitle">{r && r.generica && r.raio_nm === null ? t('crystalab.subtitleGeneric') : t('crystalab.subtitle')}</p>
      </div>
      <div className="topbar-actions">
        <IconButton icon="undo" label={t('history.undo')} disabled={!past} onClick={() => void dispatch({ type: 'history.undo' }, 'form')} data-testid="undo" />
        <IconButton icon="redo" label={t('history.redo')} disabled={!future} onClick={() => void dispatch({ type: 'history.redo' }, 'form')} data-testid="redo" />
        <IconButton icon="share" label={t('share.button')} disabled={!r} onClick={() => void dispatch({ type: 'share' }, 'form')} data-testid="share" />
        <IconButton icon="notebook" label={t('notebook.captureScene')} disabled={!r} data-testid="capture-note" onClick={async () => {
          const note = await captureSceneNote(r ? `${r.rotulo} — ${t('notebook.sceneTitle')}` : '', locale);
          if (note) toast({ tone: 'success', title: t('notebook.captured'), action: { label: t('nav.notebook'), run: () => navigate('diario') } });
        }} />
        <Menu
          label={t('export.menu')}
          icon="download"
          align="end"
          buttonProps={{ size: 'md', 'aria-label': t('export.menu') } as never}
          items={exports.map((e) => ({
            id: e.format,
            label: t(`export.format.${e.format}`),
            icon: EXPORT_ICONS[e.format],
            disabled: !e.enabled,
            ...(e.reasonKey ? { disabledReason: t(e.reasonKey) } : {}),
            onSelect: () => void dispatch({ type: 'export', format: e.format }, 'form'),
          }))}
        >
          {t('export.menu')}
        </Menu>
        <Button className="side-toggle" icon="layers" aria-expanded={sideOpen} aria-controls="side-panel" onClick={onToggleSide}>{t('crystalab.panel')}</Button>
        <Button variant="primary" data-testid="render-button" loading={status === 'loading'} onClick={() => void dispatch({ type: 'editor.apply' }, 'form')}>{t('crystalab.render')}</Button>
      </div>
    </header>
  );
}

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

function WorkspacesPanel() {
  const { t } = useI18n();
  const [items, setItems] = useState<Workspace[]>(() => listWorkspaces());
  const fileRef = useRef<HTMLInputElement>(null);
  const refresh = () => setItems(listWorkspaces());
  useEffect(() => {
    const onStorage = () => refresh();
    window.addEventListener('storage', onStorage);
    window.addEventListener('alloy:workspaces', onStorage);
    return () => { window.removeEventListener('storage', onStorage); window.removeEventListener('alloy:workspaces', onStorage); };
  }, []);
  return (
    <div className="ws-panel" data-testid="workspaces">
      <CategoryBox category="demo" className="ws-note" role="note"><p>{t('workspace.localOnly')}</p></CategoryBox>
      <div className="ds-row">
        <Button icon="download" onClick={async () => { await dispatch({ type: 'workspace.save' }, 'form'); refresh(); }}>{t('workspace.save')}</Button>
        <Button icon="upload" onClick={() => fileRef.current?.click()}>{t('workspace.import')}</Button>
        <Button icon="file" disabled={!items.length} onClick={() => downloadText(exportWorkspacesJson(), 'alloy-workspaces.json', 'application/json')}>{t('workspace.export')}</Button>
        <input ref={fileRef} type="file" accept="application/json,.json" hidden aria-hidden="true" tabIndex={-1} onChange={async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          try { const res = importWorkspacesJson(await file.text()); toast({ tone: 'success', title: t('workspace.imported', { n: res.added }) }); refresh(); }
          catch (err) { toast({ tone: 'error', title: t('workspace.importFailed'), body: err instanceof Error ? err.message : String(err) }); }
          e.target.value = '';
        }} />
      </div>
      <ul className="ws-list">
        {items.map((w) => (
          <li key={w.id} className="ws-item">
            <div><strong>{w.name}</strong><small>{new Date(w.savedAt).toLocaleString()} · {t('workspace.local')}</small></div>
            <div className="ds-row">
              <Button size="sm" onClick={async () => { const ctrl = new AbortController(); try { await restoreScene(w.scene, ctrl.signal, w.name); } catch (err) { log('error', describeError(err)); } }}>{t('workspace.open')}</Button>
              <IconButton size="sm" icon="trash" label={t('workspace.delete', { name: w.name })} onClick={() => { deleteWorkspace(w.id); refresh(); }} />
            </div>
          </li>
        ))}
      </ul>
      {!items.length ? <p className="ds-muted">{t('workspace.none')}</p> : null}
    </div>
  );
}

type SideTab = 'guided' | 'overlays' | 'atom' | 'measure' | 'anim' | 'prov' | 'ws';

function SidePanel() {
  const { t } = useI18n();
  const [tab, setTab] = useState<SideTab>('guided');
  const overlayCount = useOverlays((s) => s.items.length);
  const selection = useViewer((s) => s.selection);
  const animation = useViewer((s) => s.animation);
  const tool = useViewer((s) => s.tool);
  const transfer = useCrystalab((s) => s.heaTransfer);
  useEffect(() => { if (selection) setTab('atom'); }, [selection]);
  useEffect(() => { if (animation) setTab('anim'); }, [animation?.name]);
  useEffect(() => { if (tool) setTab('measure'); }, [tool?.kind]);
  useEffect(() => { if (transfer) setTab('prov'); }, [transfer]);
  const items: Array<{ id: SideTab; label: string; badge?: number }> = [
    { id: 'guided', label: t('side.guided') },
    { id: 'overlays', label: t('side.overlays'), badge: overlayCount },
    { id: 'atom', label: t('side.atom') },
    { id: 'measure', label: t('side.measure') },
    { id: 'anim', label: t('side.anim') },
    { id: 'prov', label: t('side.prov') },
    { id: 'ws', label: t('side.ws') },
  ];
  return (
    <div className="side" id="side-panel">
      <Tabs label={t('side.label')} items={items} value={tab} onChange={(v) => setTab(v as SideTab)} idPrefix="side" size="sm" />
      <TabPanel idPrefix="side" id="guided" active={tab === 'guided'}><GuidedMode /></TabPanel>
      <TabPanel idPrefix="side" id="overlays" active={tab === 'overlays'}><OverlayManager /></TabPanel>
      <TabPanel idPrefix="side" id="atom" active={tab === 'atom'}><AtomInspector /></TabPanel>
      <TabPanel idPrefix="side" id="measure" active={tab === 'measure'}><MeasurementsPanel /></TabPanel>
      <TabPanel idPrefix="side" id="anim" active={tab === 'anim'}><AnimationsPanel /></TabPanel>
      <TabPanel idPrefix="side" id="prov" active={tab === 'prov'}><ProvenancePanel /></TabPanel>
      <TabPanel idPrefix="side" id="ws" active={tab === 'ws'}><WorkspacesPanel /></TabPanel>
    </div>
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
  const structure = useCrystalab((s) => s.structure);
  const status = useCrystalab((s) => s.status);
  const densityVisible = useCrystalab((s) => s.densityVisible);
  const ready = useCapabilities((s) => s.ready);
  const mode = useServiceMode('crystalab');
  const route = useRoute();
  const [sideOpen, setSideOpen] = useState(false);
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

  return (
    <Workbench
      lab={<LabPanel />}
      sideOpen={sideOpen}
      sideLabel={t('side.label')}
      center={
        <div className="output-panel">
          <Topbar sideOpen={sideOpen} onToggleSide={() => setSideOpen((o) => !o)} />
          <main className="result-scroll" id="main-content" data-testid="result-root" tabIndex={-1} aria-busy={status === 'loading' || undefined}>
            {!ready ? <div className="empty-state"><Spinner size={22} label={t('engine.checking')} /></div> : null}
            {ready && mode !== 'live' ? <EngineUnavailable /> : null}
            <HeaTransferBanner />
            {structure ? (
              <>
                <StatusBand r={structure} />
                <MetricsGrid r={structure} />
                <ViewerPanel />
                {densityVisible ? <DensityPanel r={structure} /> : null}
                <div className="lower-grid">
                  <ComparisonTable r={structure} />
                  <AtomCount r={structure} />
                </div>
                <Interpretation r={structure} />
              </>
            ) : ready && mode === 'live' ? <div className="empty-state"><Spinner size={22} label={t('common.loading')} /></div> : null}
          </main>
        </div>
      }
      side={<SidePanel />}
    />
  );
}
