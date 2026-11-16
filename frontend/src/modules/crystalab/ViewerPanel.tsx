import { lazy, Suspense, useCallback, useEffect, useState, type ReactNode } from 'react';
import { dispatch, submitLine } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useOverlays } from '../../stores/overlays.ts';
import { useViewer } from '../../stores/viewer.ts';
import { usePreferences } from '../../stores/preferences.ts';
import { Button } from '../../design-system/primitives/Button.tsx';
import { Segmented } from '../../design-system/primitives/Field.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { getCameraApi } from '../../features/viewer3d/cameraApi.ts';
import { millerDetail } from '../../commands/handlers.ts';
import { spokenNotation } from '../../utils/text.ts';

const Viewer3D = lazy(() => import('../../features/viewer3d/Viewer3D.tsx'));

const SITE_LABEL_KEYS = { vertice: 'site.vertice', centro: 'site.centro', face: 'site.face', basal: 'site.basal', interior: 'site.interior' } as const;

export function MillerForm() {
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

/**
 * Palco da cena 3D: ocupa todo o contêiner. Os controles flutuantes (título, ações, câmera,
 * legenda) entram como `children`, irmãos do palco, para que o teclado da cena não os capture.
 * `overlay` entra DENTRO do palco: são os avisos sobre o que a cena mostra (inclusive o selo
 * "Ilustrativo"), que devem permanecer verificáveis como descendentes da área da cena.
 */
export function SceneStage({ children, overlay }: { children?: ReactNode; overlay?: ReactNode }) {
  const { t } = useI18n();
  const [stage, setStage] = useState<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState(false);
  const engine = useViewer((s) => s.engine);
  const structure = useCrystalab((s) => s.structure);
  const tool = useViewer((s) => s.tool);
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
    // só o próprio palco controla a câmera pelo teclado; teclas digitadas nos avisos sobrepostos
    // (botões, selos) seguem o comportamento nativo do controle focado
    if (e.target !== e.currentTarget) return;
    const cam = getCameraApi();
    if (!cam) return;
    const modifier = e.ctrlKey || e.altKey || e.metaKey;
    const arrows: Record<string, [number, number]> = { ArrowLeft: [1, 0], ArrowRight: [-1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
    const arrow = arrows[e.key];
    if (arrow) {
      e.preventDefault();
      // Ctrl/Alt + seta desloca a cena no sentido da seta; seta sozinha gira (Shift = passo maior)
      if (modifier) { const step = e.shiftKey ? 0.15 : 0.06; cam.pan(arrow[0] * step, arrow[1] * step); }
      else { const step = e.shiftKey ? 0.2 : 0.08; cam.orbit(arrow[0] * step, arrow[1] * step); }
      return;
    }
    if (modifier) return; // Ctrl + / Ctrl − / Ctrl 0 continuam sendo o zoom do navegador
    const reset = () => void dispatch({ type: 'view.reset' }, 'shortcut');
    const map: Record<string, () => void> = {
      '+': () => cam.zoom(0.9), '=': () => cam.zoom(0.9), '-': () => cam.zoom(1.1), _: () => cam.zoom(1.1),
      '0': reset, Home: reset, r: reset, R: reset, f: () => cam.frame(), F: () => cam.frame(),
      Escape: () => useViewer.getState().set({ selection: null }),
    };
    const fn = map[e.key];
    if (fn) { e.preventDefault(); fn(); }
  };

  return (
    <div className="cl-scene">
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
        {failed || engine === 'unsupported' ? <div className="viewer-fallback" role="note">{t('viewer.unsupported')}</div> : null}
        {overlay}
      </div>
      {children}
      <p id="viewer-keys" className="sr-only">{t('viewer.keys')}</p>
    </div>
  );
}
