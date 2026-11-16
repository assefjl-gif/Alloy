/**
 * Controles flutuantes sobre a cena 3D (R1-FE-01): título e ações, câmera e legenda, irmãos
 * do palco; e os avisos de contexto (`SceneNotices`), que ficam dentro do palco. Todos são
 * discretos, sobrepostos, e não reduzem a área da cena.
 * Tudo o que aparece aqui vem do resultado do motor ou do estado de exibição; nada é calculado.
 */
import { dispatch } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { navigate } from '../../app/router.ts';
import { Button, IconButton } from '../../design-system/primitives/Button.tsx';
import { Menu } from '../../design-system/primitives/Menu.tsx';
import { Segmented } from '../../design-system/primitives/Field.tsx';
import { DemoSeal } from '../../design-system/primitives/Category.tsx';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { useHistory } from '../../stores/history.ts';
import { useCapabilities } from '../../stores/capabilities.ts';
import { useOverlays } from '../../stores/overlays.ts';
import { useViewer } from '../../stores/viewer.ts';
import { usePreferences } from '../../stores/preferences.ts';
import { useBarOpen, useCrystalUi } from '../../stores/crystalUi.ts';
import { toast } from '../../stores/toast.ts';
import { captureSceneNote } from '../notebook/captureNote.ts';
import { exportAvailability } from '../../features/export/exporters.ts';
import { getCameraApi } from '../../features/viewer3d/cameraApi.ts';
import { alloyLegendWith } from '../../features/viewer3d/alloyScene.ts';
import { useAppearance } from '../../stores/appearance.ts';
import { filterActive, useSceneFilter } from '../../stores/sceneFilter.ts';
import { useAlloyAtomViews } from './AlloyAtomInspector.tsx';
import { alloyDisplayCounts } from './alloyDisplay.ts';
import { elementLegendFor } from './elementLegend.ts';
import { spokenNotation } from '../../utils/text.ts';
import type { ExportFormat } from '../../commands/types.ts';

export const BAR_ID = 'crystal-sidebar';

const EXPORT_ICONS: Record<ExportFormat, 'file' | 'camera' | 'print' | 'download'> = { cif: 'file', xyz: 'file', png: 'camera', pdf: 'print', json: 'download' };
const SITE_LABEL_KEYS = { vertice: 'site.vertice', centro: 'site.centro', face: 'site.face', basal: 'site.basal', interior: 'site.interior' } as const;

/** Botão único que abre/recolhe a barra de ferramentas. */
export function BarToggle() {
  const { t } = useI18n();
  const open = useBarOpen();
  return (
    <Button
      className="cl-bar-toggle"
      icon={open ? 'close' : 'menu'}
      aria-expanded={open}
      aria-controls={BAR_ID}
      id="crystal-bar-toggle"
      data-testid="sidebar-toggle"
      onClick={() => {
        useCrystalUi.getState().setBar(!open);
        // ao abrir, o foco entra na barra (ela vem antes da cena na ordem de tabulação)
        if (!open) window.requestAnimationFrame(() => document.getElementById('crystal-sidebar-close')?.focus());
      }}
    >
      {t('bar.tools')}
    </Button>
  );
}

function SceneTitle() {
  const { t } = useI18n();
  const r = useCrystalab((s) => s.structure);
  return (
    <div className="cl-hud__title">
      <h1 id="resultTitle">{r?.rotulo ?? t('crystalab.unitCell')}</h1>
      <p id="resultSubtitle">{r && r.generica && r.raio_nm === null ? t('crystalab.subtitleGeneric') : t('crystalab.subtitle')}</p>
    </div>
  );
}

function SceneActions() {
  const { t, locale } = useI18n();
  const r = useCrystalab((s) => s.structure);
  const past = useHistory((s) => s.past.length);
  const future = useHistory((s) => s.future.length);
  useCapabilities((s) => s.crystalab);
  const exports = exportAvailability();
  return (
    <div className="cl-hud__actions" role="group" aria-label={t('hud.actions')}>
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
    </div>
  );
}

/**
 * Avisos de contexto: o que a cena mostra de diferente do metal carregado, e ferramentas ativas.
 * Renderizado DENTRO do palco (`SceneStage overlay=`), sobreposto à cena: o selo "Ilustrativo"
 * precisa ser, também no DOM, um descendente da área da cena a que ele se refere.
 */
export function SceneNotices() {
  const { t } = useI18n();
  const transfer = useCrystalab((s) => s.heaTransfer);
  const alloy = useAlloy((s) => s.alloy);
  const tool = useViewer((s) => s.tool);
  const animation = useViewer((s) => s.animation);
  const coloring = useViewer((s) => s.elementColoring);
  const reveal = useCrystalUi((s) => s.reveal);
  if (!transfer && !alloy && !tool && !animation && !coloring?.enabled) return null;
  return (
    <div className="cl-hud__notices">
      {tool ? (
        <div className="viewer-tool-banner" role="status">
          {t(tool.kind === 'distance' ? 'measure.bannerDistance' : 'measure.bannerAngle', { picked: tool.picks.length })}
          <button type="button" className="ds-btn ds-btn--sm" onClick={() => void dispatch({ type: 'measure.stop' }, 'form')}>{t('measure.finish')}</button>
        </div>
      ) : null}
      {transfer ? <Button size="sm" icon="flask" data-testid="hud-hea" onClick={() => reveal('composition', true)}>{t('hud.heaScene', { name: transfer.result.nome })}</Button> : null}
      {alloy ? <Button size="sm" icon="atom" data-testid="hud-alloy" onClick={() => reveal('composition', true)}>{t('hud.alloyScene', { label: alloy.rotulo })}</Button> : null}
      {/* D-R2-4: TODA animação tem selo, inclusive α→γ (achado T-15). A α→γ interpola entre dois
          resultados REAIS do motor, então o rótulo é "interpolação visual", não "demonstração". */}
      {animation ? (
        animation.name === 'alpha-gamma'
          ? <DemoSeal variant="illustrative" text={t('anim.ag.sealText')} detail={t('anim.ag.sealDetail')} />
          : <DemoSeal variant="illustrative" text={t('common.illustrative')} detail={t('anim.illustrativeDetail')} />
      ) : null}
      {coloring?.enabled ? <DemoSeal variant="illustrative" text={t('common.illustrative')} detail={t('bridge.coloringDetail')} /> : null}
    </div>
  );
}

/** Câmera por botões: girar/deslocar (setas), aproximar/afastar, centralizar e vista inicial. */
function CameraControls() {
  const { t } = useI18n();
  const mode = useCrystalUi((s) => s.cameraMode);
  const ready = useViewer((s) => s.engine) === 'ready';
  const unlocked = useViewer((s) => s.sceneUnlocked);
  const touchLockPref = usePreferences((s) => s.touchSceneLock);
  const coarse = typeof window !== 'undefined' && window.matchMedia?.('(pointer: coarse)').matches;
  // as setas movem a cena no sentido indicado: ao girar, a face visível vai para lá; ao deslocar, o conteúdo
  const move = (x: number, y: number) => {
    const cam = getCameraApi();
    if (!cam) return;
    if (mode === 'pan') cam.pan(-x * 0.08, -y * 0.08);
    else cam.orbit(-x * 0.12, -y * 0.12);
  };
  const dir = (key: 'left' | 'right' | 'up' | 'down') => t(mode === 'pan' ? `camera.pan.${key}` : `camera.rotate.${key}`);
  return (
    <div className="cl-camera" role="group" aria-label={t('camera.toolbar')} data-testid="camera-controls">
      {coarse && touchLockPref ? (
        <div className="viewer-touch">
          <IconButton icon={unlocked ? 'unlock' : 'lock'} size="sm" label={unlocked ? t('viewer.lockScene') : t('viewer.unlockScene')} aria-pressed={unlocked} onClick={() => useViewer.getState().set({ sceneUnlocked: !unlocked })} showTooltip={false} />
        </div>
      ) : null}
      <Segmented
        label={t('camera.modeLabel')}
        hideLabel
        name="camera-mode"
        size="sm"
        value={mode}
        onChange={(m) => useCrystalUi.getState().set({ cameraMode: m })}
        options={[{ value: 'rotate', label: t('camera.mode.rotate') }, { value: 'pan', label: t('camera.mode.pan') }]}
      />
      <div className="cl-camera__pad">
        <span className="cl-camera__up"><IconButton size="sm" icon="chevronDown" label={dir('up')} disabled={!ready} data-testid="camera-up" onClick={() => move(0, 1)} /></span>
        <span className="cl-camera__left"><IconButton size="sm" icon="chevronRight" label={dir('left')} disabled={!ready} data-testid="camera-left" onClick={() => move(-1, 0)} /></span>
        <span className="cl-camera__right"><IconButton size="sm" icon="chevronRight" label={dir('right')} disabled={!ready} data-testid="camera-right" onClick={() => move(1, 0)} /></span>
        <span className="cl-camera__down"><IconButton size="sm" icon="chevronDown" label={dir('down')} disabled={!ready} data-testid="camera-down" onClick={() => move(0, -1)} /></span>
      </div>
      <div className="cl-camera__row">
        <IconButton size="sm" icon="plus" label={t('camera.zoomIn')} disabled={!ready} data-testid="camera-zoom-in" onClick={() => getCameraApi()?.zoom(0.85)} />
        <IconButton size="sm" icon="minus" label={t('camera.zoomOut')} disabled={!ready} data-testid="camera-zoom-out" onClick={() => getCameraApi()?.zoom(1.18)} />
        <IconButton size="sm" icon="target" label={t('camera.center')} disabled={!ready} data-testid="camera-center" onClick={() => getCameraApi()?.frame()} />
        <IconButton size="sm" icon="restart" label={t('view.reset')} disabled={!ready} data-testid="camera-reset" onClick={() => void dispatch({ type: 'view.reset' }, 'form')} />
      </div>
    </div>
  );
}

/** Parâmetros de rede exatamente como o motor os devolveu (sem recálculo). */
export function useLatticeLines(): string[] {
  const { t, num } = useI18n();
  const r = useCrystalab((s) => s.structure);
  const alloy = useAlloy((s) => s.alloy);
  if (alloy) return [`a = ${num(alloy.a_nm, 4)} nm`];
  if (!r) return [];
  const lines = [r.a_nm !== null ? `a = ${num(r.a_nm, 4)} nm` : `a = ${num(r.a_em_R, 3)} R`];
  if (r.estrutura === 'HC') {
    if (r.c_nm !== null) lines.push(`c = ${num(r.c_nm, 4)} nm`);
    lines.push(r.c_a !== null ? `c/a = ${num(r.c_a, 3)}` : `c/a: ${t('common.na')}`);
  }
  return lines;
}

/** Legenda coerente com o que está desenhado: células, parâmetros de rede, átomos, linhas e overlays. */
function SceneLegend() {
  const { t } = useI18n();
  const show = useCrystalUi((s) => s.legend);
  const r = useCrystalab((s) => s.structure);
  const transfer = useCrystalab((s) => s.heaTransfer);
  const alloy = useAlloy((s) => s.alloy);
  const supercell = useViewer((s) => s.supercell);
  const display = useViewer((s) => s.display);
  const coloring = useViewer((s) => s.elementColoring);
  const animation = useViewer((s) => s.animation);
  const overlays = useOverlays((s) => s.items);
  const lattice = useLatticeLines();
  const vibrating = useAlloy((s) => s.vibration.on && Boolean(s.thermal));
  // filtro/corte de EXIBIÇÃO (T-23): a legenda precisa dizer em voz alta que a cena está incompleta
  const filtered = useSceneFilter(filterActive);
  const views = useAlloyAtomViews(alloy);
  const displayed = alloyDisplayCounts(views);
  // aparência (T-22): a legenda usa a MESMA resolução de cor que desenha a cena, por isso as duas
  // não podem divergir — inclusive depois de filtrar, isolar ou cortar
  const app = useAppearance();
  const selection = useViewer((s) => s.selection);
  const alloySelection = useViewer((s) => s.alloySelection);
  if (!r) return null;
  const drawn = overlays.filter((o) => o.visible && (o.kind === 'plane' || o.kind === 'direction'));
  const didactic = Boolean(animation && animation.name !== 'thermal');
  // com liga ou animação didática a célula do metal sai de cena, e com ela eixos, arestas e pontos de rede
  // (a vibração térmica também troca a célula pela cena do motor, sem eixos nem overlays)
  const cellVisible = !alloy && !didactic && !vibrating;
  const cells = alloy ? `${alloy.supercelula}×${alloy.supercelula}×${alloy.supercelula}` : supercell.join('×');
  const isUnit = cells === '1×1×1';
  // o que a cor está codificando agora (requisito T-22: se a cor codifica informação, a legenda diz)
  const colorLevels = [
    alloy ? t('legend.colorByElement') : t('legend.colorByGroup'),
    ...(Object.keys(app.overrides.elements).length && !alloy ? [t('legend.colorByElement')] : []),
    ...(Object.keys(app.overrides.groups).length && alloy ? [t('legend.colorByGroup')] : []),
    ...(Object.keys(app.overrides.atoms).length ? [t('legend.colorByAtom')] : []),
  ];
  // marcadores geométricos desenhados agora (nunca se confundem com átomo: seta, linha ou arame)
  const markers = [
    ...(cellVisible && display.axes ? [t('view.toggle.axes')] : []),
    ...(cellVisible && display.latticePoints ? [t('view.toggle.latticePoints')] : []),
    ...(app.vertices ? [t('legend.marker.vertices')] : []),
    ...(selection || alloySelection ? [t('legend.marker.selection')] : []),
  ];
  return (
    <div className="cl-legend-wrap">
      {show ? (
        <section className="cl-legend" id="scene-legend" aria-label={t('legend.title')} data-testid="scene-legend">
          <p className="cl-legend__what">
            <strong lang="pt-BR">{alloy ? alloy.rotulo : r.rotulo}</strong>
            <span data-testid="legend-cells">{isUnit ? t('crystalab.unitCell') : `${t('view.supercell')} ${cells}`}</span>
          </p>
          {filtered ? (
            <p className="cl-legend__note" data-testid="legend-filter">
              {t('filter.active')}
              {alloy ? ` · ${t('filter.counts', { drawn: displayed.drawn, total: alloy.atomos.length, unique: displayed.unique })}` : ''}
            </p>
          ) : null}
          {didactic ? <p className="cl-legend__note">{t('legend.animation')}</p> : (
            <>
              <p className="cl-legend__lattice ds-mono" data-testid="legend-lattice">{lattice.join(' · ')}</p>
              <ul className="cl-legend__items">
                {alloy ? alloyLegendWith(alloy, app.overrides).map((l) => (
                  <li key={l.element} className="legend-chip" data-testid={`legend-element-${l.element}`} data-color={l.color}>
                    <span className="legend-swatch" style={{ background: l.color }} aria-hidden="true" />
                    {`${l.element} · ${t(`alloy.role.${l.role}`)}${l.custom ? ` · ${t('legend.customColor')}` : ''}`}
                  </li>
                )) : coloring?.enabled && transfer ? elementLegendFor(transfer.result.comp_percent).map((l) => (
                  <li key={l.element} className="legend-chip"><span className="legend-swatch" style={{ background: l.color }} aria-hidden="true" />{`${l.element} · ${t(`shape.${l.shape}`)}`}</li>
                )) : r.contagem.map((g) => {
                  // célula do metal puro: a cor padrão codifica o SÍTIO; escolha pessoal (grupo ou
                  // elemento) vence e é dita por palavra, nunca só pela cor
                  const custom = app.overrides.groups[g.tipo] ?? app.overrides.elements[r.simbolo ?? r.estrutura] ?? null;
                  return (
                    <li key={g.tipo} className="legend-chip" data-testid={`legend-site-${g.tipo}`} data-color={custom ?? ''}>
                      {custom ? <span className="legend-swatch" style={{ background: custom }} aria-hidden="true" /> : <i className={`dot dot--${g.tipo}`} aria-hidden="true" />}
                      {`${t(SITE_LABEL_KEYS[g.tipo])} (${g.fracao_txt})${custom ? ` · ${t('legend.customColor')}` : ''}`}
                    </li>
                  );
                })}
                {cellVisible && display.edges ? <li className="legend-chip"><i className="cl-glyph cl-glyph--edge" aria-hidden="true" />{t('view.toggle.edges')}</li> : null}
                {cellVisible && display.axes ? <li className="legend-chip"><i className="cl-glyph cl-glyph--axes" aria-hidden="true" />{`${t('view.toggle.axes')} ${r.estrutura === 'HC' ? 'a₁ a₂ a₃ c' : 'x y z'}`}</li> : null}
                {cellVisible && display.latticePoints ? <li className="legend-chip"><i className="cl-glyph cl-glyph--wire" aria-hidden="true" />{t('view.toggle.latticePoints')}</li> : null}
                {app.vertices ? <li className="legend-chip" data-testid="legend-vertices" data-color={app.vertexColor ?? ''}><i className="cl-glyph cl-glyph--vertex" aria-hidden="true" />{t('legend.marker.vertices')}</li> : null}
                {cellVisible ? drawn.map((o) => (o.kind === 'plane' || o.kind === 'direction' ? (
                  <li key={o.id} className="legend-chip">
                    <i className={o.kind === 'plane' ? 'chip-shape chip-shape--plane' : 'chip-shape chip-shape--dir'} style={{ color: o.color }} aria-hidden="true" />
                    <span aria-label={spokenNotation(o.data.notacao, t('a11y.minus'))}>{o.data.notacao}</span>
                  </li>
                ) : null)) : null}
              </ul>
              <p className="cl-legend__note" data-testid="legend-color-means">
                {`${t('legend.colorMeans')}: ${[...new Set(colorLevels)].join(' · ')} — ${t('legend.colorChoice')}`}
              </p>
              {markers.length ? (
                <p className="cl-legend__note" data-testid="legend-markers">{`${t('legend.markers')}: ${markers.join(' · ')}`}</p>
              ) : null}
            </>
          )}
        </section>
      ) : null}
      <Button size="sm" icon={show ? 'eyeOff' : 'eye'} aria-expanded={show} aria-controls="scene-legend" data-testid="legend-toggle" onClick={() => useCrystalUi.getState().set({ legend: !show })}>{t('legend.title')}</Button>
    </div>
  );
}

export function SceneHud() {
  return (
    <>
      <div className="cl-hud">
        <div className="cl-hud__lead">
          <BarToggle />
          <SceneTitle />
        </div>
        <SceneActions />
      </div>
      <SceneLegend />
      <CameraControls />
    </>
  );
}
