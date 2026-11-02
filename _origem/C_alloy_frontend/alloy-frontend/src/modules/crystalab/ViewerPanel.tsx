import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { dispatch, submitLine } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useOverlays } from '../../stores/overlays.ts';
import { useViewer } from '../../stores/viewer.ts';
import { usePreferences } from '../../stores/preferences.ts';
import { Button, IconButton, ToggleButton } from '../../design-system/primitives/Button.tsx';
import { Menu } from '../../design-system/primitives/Menu.tsx';
import { Segmented } from '../../design-system/primitives/Field.tsx';
import { DemoSeal } from '../../design-system/primitives/Category.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { getViewer } from '../../features/registry.ts';
import { millerDetail } from '../../commands/handlers.ts';
import { spokenNotation } from '../../utils/text.ts';

const Viewer3D = lazy(() => import('../../features/viewer3d/Viewer3D.tsx'));

const SITE_LABEL_KEYS = { vertice: 'site.vertice', centro: 'site.centro', face: 'site.face', basal: 'site.basal', interior: 'site.interior' } as const;

function MillerForm() {
  const { t } = useI18n();
  const [mode, setMode] = useState<'plano' | 'direcao'>('plano');
  const [value, setValue] = useState('1 1 1');
  return (
    <form
      className="miller-form"
      id="millerForm"
      onSubmit={(e) => { e.preventDefault(); void submitLine(`${mode} ${value}`, 'crystalab', 'form'); }}
      aria-label={t('miller.formLabel')}
    >
      <Segmented
        label={t('miller.kind')}
        hideLabel
        name="miller-kind"
        size="sm"
        value={mode}
        onChange={(m) => { setMode(m); setValue(m === 'plano' ? '1 1 1' : '1 1 0'); }}
        options={[{ value: 'plano', label: t('miller.planeHkl') }, { value: 'direcao', label: t('miller.directionUvw') }]}
      />
      <label htmlFor="millerInput" className="sr-only">{t('miller.indices')}</label>
      <input id="millerInput" className="ds-input miller-input" value={value} autoComplete="off" placeholder="1 1 1 · 1 0 -1 1" aria-describedby="miller-hint" onChange={(e) => setValue(e.target.value)} />
      <span id="miller-hint" className="sr-only">{t('miller.hint')}</span>
      <Button type="submit" variant="accent" size="sm">{t('miller.draw')}</Button>
      <Button size="sm" onClick={() => void dispatch({ type: 'overlays.clear' }, 'form')}>{t('miller.clear')}</Button>
    </form>
  );
}

function ViewToggles() {
  const { t } = useI18n();
  const display = useViewer((s) => s.display);
  const supercell = useViewer((s) => s.supercell);
  return (
    <div className="toggle-row" role="group" aria-label={t('view.controls')}>
      <ToggleButton size="sm" pressed={display.atoms === 'rigid'} onPressedChange={(v) => void dispatch({ type: 'view.toggle', key: 'rigid', value: v }, 'form')}>{t('view.rigid')}</ToggleButton>
      <ToggleButton size="sm" pressed={display.autoRotate} onPressedChange={(v) => void dispatch({ type: 'view.toggle', key: 'autoRotate', value: v }, 'form')}>{t('view.autoRotate')}</ToggleButton>
      <ToggleButton size="sm" pressed={display.axes} onPressedChange={(v) => void dispatch({ type: 'view.toggle', key: 'axes', value: v }, 'form')}>{t('view.axes')}</ToggleButton>
      <Button size="sm" icon="target" onClick={() => void dispatch({ type: 'view.reset' }, 'form')}>{t('view.reset')}</Button>
      <label className="sr-only" htmlFor="supercell-select">{t('view.supercell')}</label>
      <select
        id="supercell-select"
        className="ds-input supercell-select"
        value={supercell.join('x')}
        onChange={(e) => { const n = e.target.value.split('x').map(Number) as [number, number, number]; void dispatch({ type: 'supercell.set', n }, 'form'); }}
      >
        {['1x1x1', '2x2x2', '3x3x3', '4x4x4', '2x2x1', '3x3x1', '2x1x1', '3x1x1', '4x1x1', '1x1x4'].map((v) => (
          <option key={v} value={v}>{`${t('view.supercell')} ${v.replace(/x/g, '×')}`}</option>
        ))}
        {!['1x1x1', '2x2x2', '3x3x3', '4x4x4', '2x2x1', '3x3x1', '2x1x1', '3x1x1', '4x1x1', '1x1x4'].includes(supercell.join('x')) ? <option value={supercell.join('x')}>{`${t('view.supercell')} ${supercell.join('×')}`}</option> : null}
      </select>
      <Menu
        label={t('view.more')}
        icon="eye"
        align="end"
        buttonProps={{ size: 'sm' }}
        items={[
          { id: 'reduced', label: `${display.atoms === 'reduced' ? '● ' : ''}${t('view.atomMode.reduced')}`, onSelect: () => void dispatch({ type: 'view.atoms', mode: 'reduced' }, 'form') },
          { id: 'rigid', label: `${display.atoms === 'rigid' ? '● ' : ''}${t('view.atomMode.rigid')}`, onSelect: () => void dispatch({ type: 'view.atoms', mode: 'rigid' }, 'form') },
          { id: 'ballstick', label: `${display.atoms === 'ballstick' ? '● ' : ''}${t('view.atomMode.ballstick')}`, onSelect: () => void dispatch({ type: 'view.atoms', mode: 'ballstick' }, 'form') },
          { id: 'points', label: `${display.atoms === 'points' ? '● ' : ''}${t('view.atomMode.points')}`, onSelect: () => void dispatch({ type: 'view.atoms', mode: 'points' }, 'form') },
          { id: 'edges', label: `${display.edges ? '☑' : '☐'} ${t('view.toggle.edges')}`, onSelect: () => void dispatch({ type: 'view.toggle', key: 'edges' }, 'form') },
          { id: 'lattice', label: `${display.latticePoints ? '☑' : '☐'} ${t('view.toggle.latticePoints')}`, onSelect: () => void dispatch({ type: 'view.toggle', key: 'latticePoints' }, 'form') },
          { id: 'labels', label: `${display.labels ? '☑' : '☐'} ${t('view.toggle.labels')}`, onSelect: () => void dispatch({ type: 'view.toggle', key: 'labels' }, 'form') },
          { id: 'poly', label: t('view.polyhedra'), disabled: true, disabledReason: t('view.polyhedraReason'), onSelect: () => undefined },
        ]}
      />
    </div>
  );
}

export function SiteLegend() {
  const { t } = useI18n();
  const r = useCrystalab((s) => s.structure);
  const coloring = useViewer((s) => s.elementColoring);
  const transfer = useCrystalab((s) => s.heaTransfer);
  if (!r) return null;
  if (coloring?.enabled && transfer) return null; // legenda por elemento fica no painel de procedência
  return (
    <div className="viewer-legend" aria-hidden="true">
      {r.contagem.map((g) => (
        <span key={g.tipo} className="legend-chip"><i className={`dot dot--${g.tipo}`} />{`${t(SITE_LABEL_KEYS[g.tipo])} (${g.fracao_txt})`}</span>
      ))}
    </div>
  );
}

export function OverlayChips() {
  const { t } = useI18n();
  const items = useOverlays((s) => s.items);
  const selectedId = useOverlays((s) => s.selectedId);
  const visible = items.filter((i) => i.kind === 'plane' || i.kind === 'direction');
  if (!visible.length) {
    return (
      <div className="overlay-list" id="overlayList">
        <span className="overlay-empty">{t('overlays.empty')} <code>plano 1 1 1</code> · <code>direcao 1 1 0</code> · {t('overlays.inHc')} <code>plano 1 0 -1 1</code></span>
      </div>
    );
  }
  return (
    <ul className="overlay-list" id="overlayList" aria-label={t('overlays.chipsLabel')}>
      {visible.map((o) => {
        if (o.kind !== 'plane' && o.kind !== 'direction') return null;
        return (
          <li key={o.id}>
            <button type="button" className={`overlay-chip ${o.id === selectedId ? 'is-selected' : ''} ${o.visible ? '' : 'is-hidden'}`} aria-pressed={o.id === selectedId} onClick={() => useOverlays.getState().set({ selectedId: o.id === selectedId ? null : o.id })}>
              <i className={o.kind === 'plane' ? 'chip-shape chip-shape--plane' : 'chip-shape chip-shape--dir'} style={{ color: o.color }} aria-hidden="true" />
              <strong aria-label={spokenNotation(o.data.notacao, t('a11y.minus'))}>{o.data.notacao}</strong>
              {o.data.notacao_alternativa ? <em lang="pt-BR">{o.data.notacao_alternativa}</em> : null}
              <span>· {millerDetail(o.data)}</span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export function SceneDescription() {
  const { t } = useI18n();
  const r = useCrystalab((s) => s.structure);
  const items = useOverlays((s) => s.items);
  const supercell = useViewer((s) => s.supercell);
  const selection = useViewer((s) => s.selection);
  const tool = useViewer((s) => s.tool);
  if (!r) return <p id="scene-desc" className="sr-only">{t('viewer.empty')}</p>;
  const planes = items.filter((i) => i.kind === 'plane').length;
  const dirs = items.filter((i) => i.kind === 'direction').length;
  const meas = items.filter((i) => i.kind === 'measurement').length;
  const sel = selection ? r.atomos[selection.index] : null;
  return (
    <p id="scene-desc" className="scene-desc">
      {t('viewer.description', { label: r.rotulo, structure: r.estrutura_nome, atoms: r.atomos.length, n: r.n, supercell: supercell.join('×'), planes, dirs, meas })}
      {sel && selection ? ` ${t('viewer.descSelection', { n: selection.index + 1, site: t(SITE_LABEL_KEYS[sel.tipo]) })}` : ''}
      {tool ? ` ${t(tool.kind === 'distance' ? 'measure.startDistance' : 'measure.startAngle')}` : ''}
    </p>
  );
}

export function ViewerPanel() {
  const { t } = useI18n();
  const [stage, setStage] = useState<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState(false);
  const engine = useViewer((s) => s.engine);
  const structure = useCrystalab((s) => s.structure);
  const tool = useViewer((s) => s.tool);
  const animation = useViewer((s) => s.animation);
  const coloring = useViewer((s) => s.elementColoring);
  const unlocked = useViewer((s) => s.sceneUnlocked);
  const touchLockPref = usePreferences((s) => s.touchSceneLock);
  const ref = useCallback((el: HTMLDivElement | null) => setStage(el), []);
  const coarse = typeof window !== 'undefined' && window.matchMedia?.('(pointer: coarse)').matches;

  useEffect(() => {
    if (!tool) return undefined;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') void dispatch({ type: 'measure.stop' }, 'shortcut'); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [tool]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const v = getViewer();
    if (!v) return;
    const step = e.shiftKey ? 0.2 : 0.08;
    const map: Record<string, () => void> = {
      ArrowLeft: () => v.orbit(step, 0), ArrowRight: () => v.orbit(-step, 0), ArrowUp: () => v.orbit(0, -step), ArrowDown: () => v.orbit(0, step),
      '+': () => v.zoom(0.9), '=': () => v.zoom(0.9), '-': () => v.zoom(1.1), _: () => v.zoom(1.1), '0': () => void dispatch({ type: 'view.reset' }, 'shortcut'), Home: () => void dispatch({ type: 'view.reset' }, 'shortcut'),
      Escape: () => useViewer.getState().set({ selection: null }),
    };
    const fn = map[e.key];
    if (fn) { e.preventDefault(); fn(); }
  };

  return (
    <section className="ds-panel viewer-panel" aria-labelledby="viewer-title">
      <header className="ds-panel__title">
        <h2 id="viewer-title">{t('viewer.title')}</h2>
        <span className="ds-panel__aside">{t('viewer.hint')}</span>
      </header>
      <div className="viewer-toolbar">
        <MillerForm />
        <ViewToggles />
      </div>
      <div
        ref={ref}
        className={`viewer-stage ${coarse && touchLockPref && !unlocked ? 'is-touch-locked' : ''}`}
        id="viewerStage"
        data-testid="viewer-stage"
        tabIndex={0}
        role="application"
        aria-roledescription={t('viewer.roleDescription')}
        aria-label={t('viewer.stageLabel')}
        aria-describedby="scene-desc viewer-keys"
        onKeyDown={onKeyDown}
      >
        {stage && structure && !failed ? (
          <Suspense fallback={<div className="viewer-fallback"><Spinner size={22} label={t('viewer.loading')} /></div>}>
            <Viewer3D stage={stage} onReady={(ok) => setFailed(!ok)} />
          </Suspense>
        ) : null}
        {!structure ? <div className="viewer-fallback">{t('viewer.empty')}</div> : null}
        {failed || engine === 'unsupported' ? <div className="viewer-fallback" role="note">{t('viewer.unsupported')}</div> : null}
        <SiteLegend />
        <div className="viewer-badges">
          {animation && animation.name !== 'alpha-gamma' ? <DemoSeal text={t('common.illustrative')} detail={t('anim.illustrativeDetail')} /> : null}
          {coloring?.enabled ? <DemoSeal text={t('common.illustrative')} detail={t('bridge.coloringDetail')} /> : null}
        </div>
        {tool ? (
          <div className="viewer-tool-banner" role="status">
            {t(tool.kind === 'distance' ? 'measure.bannerDistance' : 'measure.bannerAngle', { picked: tool.picks.length })}
            <button type="button" className="ds-btn ds-btn--sm" onClick={() => void dispatch({ type: 'measure.stop' }, 'form')}>{t('measure.finish')}</button>
          </div>
        ) : null}
        {coarse && touchLockPref ? (
          <div className="viewer-touch">
            <IconButton icon={unlocked ? 'unlock' : 'lock'} size="sm" label={unlocked ? t('viewer.lockScene') : t('viewer.unlockScene')} aria-pressed={unlocked} onClick={() => useViewer.getState().set({ sceneUnlocked: !unlocked })} showTooltip={false} />
          </div>
        ) : null}
      </div>
      <p id="viewer-keys" className="sr-only">{t('viewer.keys')}</p>
      <OverlayChips />
      <SceneDescription />
    </section>
  );
}
