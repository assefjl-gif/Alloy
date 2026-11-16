/**
 * Barra lateral única do CrystaLab (R1-FE-01): seis seções expansíveis reúnem tudo o que antes
 * ficava no painel esquerdo, na coluna central e nas nove abas da direita.
 *
 *   Estrutura · Composição · Seleção de átomos · Propriedades · Aparência · Análise
 *
 * Só reorganiza a exibição: os valores vêm do motor (API) e nada é calculado aqui.
 * Pontos de extensão (R1-FE-02): novas subseções entram com <Sub id="aparencia.xxx"> em
 * AppearanceSection (cores, tamanho, transparência) e em SelectionSection (filtros, isolamento).
 */
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { dispatch, describeError } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { Disclosure } from '../../design-system/primitives/Disclosure.tsx';
import { Button, IconButton, ToggleButton } from '../../design-system/primitives/Button.tsx';
import { Segmented } from '../../design-system/primitives/Field.tsx';
import { CategoryBox } from '../../design-system/primitives/Category.tsx';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { useOverlays } from '../../stores/overlays.ts';
import { useViewer, type AtomMode } from '../../stores/viewer.ts';
import { useCrystalUi, type PanelId, type SectionId } from '../../stores/crystalUi.ts';
import { filterActive, useSceneFilter } from '../../stores/sceneFilter.ts';
import { useAppearance } from '../../stores/appearance.ts';
import { appearanceActive, colorsActive } from '../../features/viewer3d/appearance.ts';
import { log } from '../../stores/terminal.ts';
import { toast } from '../../stores/toast.ts';
import { Terminal } from '../../features/terminal/Terminal.tsx';
import { restoreScene } from '../../features/url/restore.ts';
import { deleteWorkspace, exportWorkspacesJson, importWorkspacesJson, listWorkspaces, type Workspace } from '../../features/workspace/workspaces.ts';
import { downloadText } from '../../features/export/download.ts';
import type { ViewToggleKey } from '../../commands/types.ts';
import { BlockBank, BlockCount, ParameterEditor } from './LabPanel.tsx';
import { AtomCount, ComparisonTable, ContactPanel, DensityPanel, Interpretation, MetricsGrid, StatusBand } from './Results.tsx';
import { MillerForm, OverlayChips, SceneDescription } from './ViewerPanel.tsx';
import { AnimationsPanel, AtomInspector, GuidedDensity, GuidedMaterial, GuidedMiller, MeasurementsPanel, OverlayManager } from './SidePanels.tsx';
import { AlloyBanner, AlloyForm, AlloyResults, ThermalForm, ThermalResults } from './AlloyPanels.tsx';
import { AlloyAtomInspector } from './AlloyAtomInspector.tsx';
import { FilterPanel } from './FilterPanel.tsx';
import { AppearanceAtoms, AppearanceCell, AppearanceColors, AppearanceMarkers, AppearanceResetAll } from './AppearancePanel.tsx';
import { HeaTransferBanner, ProvenancePanel } from './ProvenancePanel.tsx';
import { BAR_ID, useLatticeLines } from './SceneHud.tsx';

const SUPERCELLS = ['1x1x1', '2x2x2', '3x3x3', '4x4x4', '2x2x1', '3x3x1', '2x1x1', '3x1x1', '4x1x1', '1x1x4'];
const ATOM_MODES: AtomMode[] = ['reduced', 'rigid', 'ballstick', 'points'];
const DISPLAY_TOGGLES = ['axes', 'edges', 'latticePoints', 'labels', 'autoRotate'] as const satisfies readonly ViewToggleKey[];

function domId(id: PanelId): string {
  return id.replace('.', '-');
}

/** Seção de primeiro nível da barra (h2 + botão com aria-expanded/aria-controls). */
function Section({ id, aside, children }: { id: SectionId; aside?: ReactNode; children: ReactNode }) {
  const { t } = useI18n();
  const open = useCrystalUi((s) => Boolean(s.open[id]));
  return (
    <Disclosure className="cl-section" headingLevel={2} id={`cl-sec-${id}`} testId={`section-${id}`} title={t(`section.${id}`)} aside={aside} open={open} onOpenChange={(v) => useCrystalUi.getState().toggle(id, v)}>
      {children}
    </Disclosure>
  );
}

/** Subseção (h3). As avançadas começam recolhidas (DEFAULT_OPEN em stores/crystalUi.ts). */
function Sub({ id, title, aside, children }: { id: PanelId; title: ReactNode; aside?: ReactNode; children: ReactNode }) {
  const open = useCrystalUi((s) => Boolean(s.open[id]));
  return (
    <Disclosure className="cl-sub" headingLevel={3} id={`cl-sub-${domId(id)}`} testId={`sub-${domId(id)}`} title={title} aside={aside} open={open} onOpenChange={(v) => useCrystalUi.getState().toggle(id, v)}>
      {children}
    </Disclosure>
  );
}

/** Célula unitária × supercélula: troca direta e escolha do número de células desenhadas. */
function CellControl() {
  const { t } = useI18n();
  const supercell = useViewer((s) => s.supercell);
  const current = supercell.join('x');
  const set = (value: string) => { const n = value.split('x').map(Number) as [number, number, number]; void dispatch({ type: 'supercell.set', n }, 'form'); };
  return (
    <div className="cl-cells" data-testid="cell-control">
      <Segmented
        label={t('cells.drawn')}
        name="cell-mode"
        size="sm"
        value={current === '1x1x1' ? 'unit' : 'super'}
        onChange={(m) => set(m === 'unit' ? '1x1x1' : '2x2x2')}
        options={[{ value: 'unit', label: t('crystalab.unitCell') }, { value: 'super', label: t('view.supercell') }]}
      />
      <label className="sr-only" htmlFor="supercell-select">{t('cells.size')}</label>
      <select id="supercell-select" className="ds-input supercell-select" value={current} onChange={(e) => set(e.target.value)}>
        {SUPERCELLS.map((v) => <option key={v} value={v}>{`${t('view.supercell')} ${v.replace(/x/g, '×')}`}</option>)}
        {!SUPERCELLS.includes(current) ? <option value={current}>{`${t('view.supercell')} ${supercell.join('×')}`}</option> : null}
      </select>
    </div>
  );
}

/** Resumo da célula carregada: valores do resultado do motor, com unidade. */
function CellSummary() {
  const { t } = useI18n();
  const r = useCrystalab((s) => s.structure);
  const lattice = useLatticeLines();
  const alloy = useAlloy((s) => s.alloy);
  return (
    <CategoryBox category="result" as="section" className="guided__card" aria-labelledby="cell-summary-title" data-testid="cell-summary">
      <h3 id="cell-summary-title">{t('guided.review')}</h3>
      {r ? (
        <dl className="guided__dl">
          <dt>{t('metrics.structure')}</dt><dd lang="pt-BR">{`${r.estrutura_nome} (${r.estrutura})`}</dd>
          <dt>{t('guided.material')}</dt><dd lang="pt-BR">{r.rotulo}</dd>
          <dt>n · NC</dt><dd>{`${r.n} · ${r.nc}`}</dd>
          <dt>R</dt><dd>{r.raio_nm !== null ? `${r.raio_nm} nm` : t('guided.inUnitsOfR')}</dd>
          <dt>{t('cells.lattice')}</dt>
          <dd className="ds-mono" data-testid="cell-lattice">{lattice.join(' · ')}{alloy ? ` (${alloy.rotulo})` : ''}</dd>
        </dl>
      ) : <p className="ds-muted">{t('guided.noStructureYet')}</p>}
    </CategoryBox>
  );
}

function StructureSection() {
  const { t } = useI18n();
  const status = useCrystalab((s) => s.status);
  return (
    <Section id="structure">
      <CellSummary />
      <CellControl />
      <SceneDescription />
      <Sub id="structure.material" title={t('blocks.title')} aside={<BlockCount />}>
        <div className="cl-well"><BlockBank /></div>
      </Sub>
      <Sub id="structure.guided" title={t('side.guided')}>
        <GuidedMaterial />
      </Sub>
      <Sub id="structure.editor" title={t('editor.title')}>
        <div className="cl-well"><ParameterEditor /></div>
        <Button variant="primary" data-testid="render-button" loading={status === 'loading'} onClick={() => void dispatch({ type: 'editor.apply' }, 'form')}>{t('crystalab.render')}</Button>
      </Sub>
    </Section>
  );
}

function CompositionSection() {
  const alloy = useAlloy((s) => s.alloy);
  const transfer = useCrystalab((s) => s.heaTransfer);
  return (
    <Section id="composition" aside={alloy || transfer ? <Badge tone="info">●</Badge> : undefined}>
      <HeaTransferBanner />
      <AlloyBanner />
      <AlloyForm />
    </Section>
  );
}

/**
 * Seleção de átomos. Com liga formada, a cena desenhada é a da liga (T-24): o inspetor da liga
 * usa a identidade do motor (`id`) e os campos por átomo da API. Sem liga, vale o inspetor da
 * célula do metal puro.
 */
function SelectionSection() {
  const selection = useViewer((s) => s.selection);
  const alloySelection = useViewer((s) => s.alloySelection);
  const alloy = useAlloy((s) => s.alloy);
  const badge = alloy ? (alloySelection ? <Badge tone="info">1</Badge> : undefined) : (selection ? <Badge tone="info">{selection.index + 1}</Badge> : undefined);
  return (
    <Section id="selection" aside={badge}>
      {alloy ? <AlloyAtomInspector /> : <AtomInspector />}
    </Section>
  );
}

function PropertiesSection() {
  const { t } = useI18n();
  const r = useCrystalab((s) => s.structure);
  const densityVisible = useCrystalab((s) => s.densityVisible);
  const alloy = useAlloy((s) => s.alloy);
  return (
    <Section id="properties">
      {r ? (
        <>
          <Sub id="properties.summary" title={t('sub.summary')}>
            <StatusBand r={r} />
            <MetricsGrid r={r} />
            <ContactPanel r={r} />
          </Sub>
          <Sub id="properties.density" title={t('density.title')}>
            <GuidedDensity />
            {densityVisible ? <DensityPanel r={r} /> : null}
          </Sub>
          {alloy ? (
            <Sub id="properties.alloy" title={t('sub.alloyResults')}>
              <AlloyResults />
            </Sub>
          ) : null}
          <Sub id="properties.compare" title={t('comparison.title')}><ComparisonTable r={r} /></Sub>
          <Sub id="properties.count" title={t('count.title')}><AtomCount r={r} /></Sub>
          <Sub id="properties.interpretation" title={t('interpretation.title')}><Interpretation r={r} /></Sub>
        </>
      ) : <p className="ds-muted">{t('guided.noStructureYet')}</p>}
      <Sub id="properties.provenance" title={t('side.prov')}><ProvenancePanel /></Sub>
    </Section>
  );
}

/**
 * Aparência (T-22): representação, interruptores de exibição, CORES (elemento, grupo, átomo),
 * aparência da CÉLULA (arestas e vértices), TAMANHO e OPACIDADE dos átomos, marcadores
 * geométricos, filtros de exibição e restauração do padrão. Tudo em um lugar, sem duplicar
 * controle: a representação e os interruptores continuam sendo os mesmos comandos de antes.
 */
function AppearanceSection() {
  const { t } = useI18n();
  const display = useViewer((s) => s.display);
  const legend = useCrystalUi((s) => s.legend);
  const active = useSceneFilter(filterActive);
  const appearance = useAppearance();
  return (
    <Section id="appearance" aside={appearanceActive(appearance) ? <Badge tone="info">{t('appearance.active')}</Badge> : undefined}>
      <div className="cl-appearance" data-testid="appearance-controls">
        <Segmented
          label={t('view.atoms')}
          name="atom-mode"
          size="sm"
          value={display.atoms}
          onChange={(mode) => void dispatch({ type: 'view.atoms', mode }, 'form')}
          options={ATOM_MODES.map((m) => ({ value: m, label: t(`view.atomMode.${m}`) }))}
        />
        <div className="toggle-row" role="group" aria-label={t('view.controls')}>
          {DISPLAY_TOGGLES.map((key) => (
            <ToggleButton key={key} size="sm" pressed={display[key]} data-testid={`toggle-${key}`} onPressedChange={(v) => void dispatch({ type: 'view.toggle', key, value: v }, 'form')}>{t(`view.toggle.${key}`)}</ToggleButton>
          ))}
          <ToggleButton size="sm" pressed={legend} data-testid="toggle-legend" onPressedChange={(v) => useCrystalUi.getState().set({ legend: v })}>{t('legend.title')}</ToggleButton>
        </div>
        <p className="ds-field__hint"><strong>{t('view.polyhedra')}:</strong> {t('view.polyhedraReason')}</p>
        <p className="ds-field__hint" data-testid="appearance-intro">{t('appearance.intro')}</p>
      </div>
      {/* Filtros e cortes ficam em APARÊNCIA porque só mudam o que aparece: nenhum valor
          científico depende deles (Análise reúne o que produz resultado do motor). */}
      <Sub id="appearance.colors" title={t('appearance.colors')} aside={colorsActive(appearance) ? <Badge tone="info">{t('appearance.custom')}</Badge> : undefined}>
        <AppearanceColors />
      </Sub>
      <Sub id="appearance.cell" title={t('appearance.cell')}>
        <AppearanceCell />
      </Sub>
      <Sub id="appearance.atoms" title={t('appearance.atomsTitle')}>
        <AppearanceAtoms />
      </Sub>
      <Sub id="appearance.markers" title={t('appearance.markers')}>
        <AppearanceMarkers />
      </Sub>
      <Sub id="appearance.filters" title={t('filter.title')} aside={active ? <Badge tone="warning">{t('filter.active')}</Badge> : undefined}>
        <FilterPanel />
      </Sub>
      <AppearanceResetAll />
    </Section>
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

function AnalysisSection() {
  const { t } = useI18n();
  const overlayCount = useOverlays((s) => s.items.length);
  const shortcuts = [
    { label: t('shortcuts.density'), command: 'calcular densidade', tone: 'cyan' },
    { label: t('shortcuts.plane111'), command: 'plano 1 1 1', tone: 'green' },
    { label: t('shortcuts.direction110'), command: 'direcao 1 1 0', tone: 'amber' },
    { label: t('shortcuts.clear'), command: 'limpar', tone: 'gray' },
  ];
  return (
    <Section id="analysis" aside={overlayCount ? <Badge tone="info">{overlayCount}</Badge> : undefined}>
      <Sub id="analysis.miller" title={t('sub.miller')}>
        <MillerForm />
        <OverlayChips />
        <GuidedMiller />
      </Sub>
      <Sub id="analysis.overlays" title={t('side.overlays')} aside={overlayCount ? <Badge tone="neutral">{overlayCount}</Badge> : undefined}><OverlayManager /></Sub>
      <Sub id="analysis.measure" title={t('side.measure')}><MeasurementsPanel /></Sub>
      <Sub id="analysis.thermal" title={t('side.temp')}>
        <ThermalForm />
        <ThermalResults />
      </Sub>
      <Sub id="analysis.anim" title={t('side.anim')}><AnimationsPanel /></Sub>
      <Sub id="analysis.terminal" title={t('terminal.title')}>
        <div className="cl-well">
          <section className="terminal-panel" aria-label={t('terminal.title')}>
            <Terminal context="crystalab" placeholderKey="terminal.placeholder" shortcuts={shortcuts} />
          </section>
        </div>
      </Sub>
      <Sub id="analysis.workspaces" title={t('side.ws')}><WorkspacesPanel /></Sub>
    </Section>
  );
}

/** Abre a seção certa quando o estado muda por outro caminho (clique na cena, terminal, paleta, HEA). */
function useAutoReveal(): void {
  const selection = useViewer((s) => s.selection);
  const alloySelection = useViewer((s) => s.alloySelection);
  const animation = useViewer((s) => s.animation?.name);
  const tool = useViewer((s) => s.tool?.kind);
  const transfer = useCrystalab((s) => s.heaTransfer);
  const densityVisible = useCrystalab((s) => s.densityVisible);
  const alloy = useAlloy((s) => s.alloy);
  const thermal = useAlloy((s) => s.thermal);
  const reveal = useCrystalUi((s) => s.reveal);
  useEffect(() => { if (selection) reveal('selection'); }, [selection, reveal]);
  useEffect(() => { if (alloySelection) reveal('selection'); }, [alloySelection, reveal]);
  useEffect(() => { if (animation) reveal('analysis.anim'); }, [animation, reveal]);
  useEffect(() => { if (tool) reveal('analysis.measure'); }, [tool, reveal]);
  useEffect(() => { if (transfer) { reveal('properties.provenance'); reveal('composition'); } }, [transfer, reveal]);
  // pedido explícito de resultado: além de expandir, traz a barra de volta se estiver recolhida
  useEffect(() => { if (densityVisible) reveal('properties.density', true); }, [densityVisible, reveal]);
  useEffect(() => { if (alloy) reveal('properties.alloy'); }, [alloy, reveal]);
  useEffect(() => { if (thermal) reveal('analysis.thermal'); }, [thermal, reveal]);
}

export function Sidebar() {
  const { t } = useI18n();
  const wide = useCrystalUi((s) => s.wide);
  useAutoReveal();
  const close = () => {
    useCrystalUi.getState().setBar(false);
    window.requestAnimationFrame(() => document.getElementById('crystal-bar-toggle')?.focus());
  };
  return (
    <div className="cl-bar" data-testid="crystal-sidebar" onKeyDown={(e) => { if (e.key === 'Escape' && useCrystalUi.getState().drawerOpen && !e.defaultPrevented) close(); }}>
      <header className="cl-bar__head">
        <div className="cl-bar__brand">
          <p className="cl-bar__title">{t('crystalab.brand')} <span className="lab-badge">M1 · v2.0</span></p>
          <p className="cl-bar__sub">{t('crystalab.brandSub')}</p>
        </div>
        <ToggleButton size="sm" className="cl-bar__wide" pressed={wide} data-testid="sidebar-wide" onPressedChange={(v) => useCrystalUi.getState().set({ wide: v })}>{t('bar.wide')}</ToggleButton>
        <IconButton id="crystal-sidebar-close" icon="close" size="sm" label={t('bar.collapse')} aria-expanded aria-controls={BAR_ID} data-testid="sidebar-close" onClick={close} />
      </header>
      <div className="cl-bar__body">
        <StructureSection />
        <CompositionSection />
        <SelectionSection />
        <PropertiesSection />
        <AppearanceSection />
        <AnalysisSection />
      </div>
    </div>
  );
}
