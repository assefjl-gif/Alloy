/**
 * Filtros, cortes e isolamento da cena (T-23 / R2-FE-03). Fica na seção APARÊNCIA porque muda só
 * o que aparece: nenhum valor científico depende destes controles (a seção Análise reúne o que
 * produz resultado do motor — Miller, medição, temperatura).
 *
 * Mecanismo de corte escolhido: PLANO DE CORTE AO LONGO DE UM EIXO, com posição em unidades de a,
 * em três modos (fica o lado de baixo, o de cima, ou só uma fatia de espessura escolhida). Ele é
 * aplicado como VISIBILIDADE de átomo (ver `features/viewer3d/visibility.ts`), não como
 * `clippingPlane` do Three.js: assim o átomo escondido sai da malha e deixa de ser selecionável,
 * e o átomo revelado pelo corte passa a ser selecionável, sem nenhum tratamento extra no
 * raycasting. A faixa do controle vem das coordenadas que o motor devolveu, não de limites fixos.
 *
 * Toda contagem mostrada aqui é de EXIBIÇÃO e é rotulada como tal, ao lado da contagem científica
 * do motor, que não muda com o filtro.
 */
import { useMemo } from 'react';
import { useI18n } from '../../i18n/index.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useViewer } from '../../stores/viewer.ts';
import { DEFAULT_CUT, filterActive, hiddenOf, useSceneFilter, type FilterDimension } from '../../stores/sceneFilter.ts';
import { axisRange, type AxisIndex, type CutMode } from '../../features/viewer3d/visibility.ts';
import { buildAtoms } from '../../features/viewer3d/geometry.ts';
import { alloyLegend } from '../../features/viewer3d/alloyScene.ts';
import { Button, ToggleButton } from '../../design-system/primitives/Button.tsx';
import { Checkbox, Segmented, Select, Slider } from '../../design-system/primitives/Field.tsx';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { CategoryBox } from '../../design-system/primitives/Category.tsx';
import { alloyDisplayCounts, alloyElementOptions, alloyOccupationOptions, alloySiteOptions, drawnAtomCount, uniqueAtomCount } from './alloyDisplay.ts';
import { useAlloyAtomViews } from './AlloyAtomInspector.tsx';

/** Rótulos que a interface sabe nomear. Qualquer outro valor é mostrado COMO O MOTOR o escreveu. */
const SITE_KEYS = { vertice: 'site.vertice', centro: 'site.centro', face: 'site.face', basal: 'site.basal', interior: 'site.interior' } as const;
const OCC_KEYS = { rede: 'alloyAtom.occ.rede', solvente: 'alloyAtom.occ.solvente', substitucional: 'alloyAtom.occ.substitucional', intersticial: 'alloyAtom.occ.intersticial' } as const;
const CUT_MODES: readonly CutMode[] = ['below', 'above', 'slab'];

/** Rótulo de uma ocupação/sítio do motor, reusado pelo menu de aparência (T-22). */
export function classLabel(t: (k: 'site.vertice') => string, value: string): string {
  const key = (OCC_KEYS as Record<string, string>)[value] ?? (SITE_KEYS as Record<string, string>)[value];
  return key ? t(key as 'site.vertice') : value;
}

/** Uma linha por valor filtrável: mostrar/ocultar e isolar (isolar = ocultar todos os outros). */
function FilterRow({ name, label, hidden, onToggle, onIsolate, swatch }: {
  name: string;
  label: string;
  hidden: boolean;
  onToggle: (hidden: boolean) => void;
  onIsolate: () => void;
  swatch?: string;
}) {
  const { t } = useI18n();
  return (
    <li className="filter-row" data-testid={`filter-row-${name}`}>
      <ToggleButton
        size="sm"
        pressed={!hidden}
        data-testid={`filter-toggle-${name}`}
        aria-label={hidden ? t('filter.show', { name: label }) : t('filter.hide', { name: label })}
        onPressedChange={(on) => onToggle(!on)}
      >
        {swatch ? <span className="legend-swatch" style={{ background: swatch }} aria-hidden="true" /> : null}
        {label}
      </ToggleButton>
      <Button size="sm" variant="ghost" data-testid={`filter-isolate-${name}`} aria-label={t('filter.isolateOf', { name: label })} onClick={onIsolate}>{t('filter.isolate')}</Button>
      {hidden ? <Badge tone="warning">{t('filter.hiddenTag')}</Badge> : null}
    </li>
  );
}

/** Uma dimensão filtrável (elemento, ocupação ou sítio), com mostrar/ocultar e isolar. */
function Dimension({ dim, title, values, label, swatch }: {
  dim: FilterDimension;
  title: string;
  values: string[];
  label: (value: string) => string;
  swatch?: (value: string) => string | undefined;
}) {
  const hidden = useSceneFilter((s) => hiddenOf(s, dim));
  const id = `filter-dim-${dim}`;
  return (
    <section aria-labelledby={`${id}-title`} data-testid={id}>
      <h4 id={`${id}-title`} className="ds-label">{title}</h4>
      <ul className="filter-list">
        {values.map((v) => (
          <FilterRow
            key={v}
            name={v}
            label={label(v)}
            swatch={swatch?.(v)}
            hidden={hidden.includes(v)}
            onToggle={(next) => useSceneFilter.getState().toggle(dim, v, next)}
            onIsolate={() => useSceneFilter.getState().isolate(dim, v, values)}
          />
        ))}
      </ul>
    </section>
  );
}

export function FilterPanel() {
  const { t, num } = useI18n();
  const f = useSceneFilter();
  const alloy = useAlloy((s) => s.alloy);
  const structure = useCrystalab((s) => s.structure);
  const supercell = useViewer((s) => s.supercell);
  const selection = useViewer((s) => s.selection);
  const alloySelection = useViewer((s) => s.alloySelection);
  const views = useAlloyAtomViews(alloy);

  const cellAtoms = useMemo(() => (!alloy && structure ? buildAtoms(structure, supercell) : []), [alloy, structure, supercell]);
  const positions = useMemo(() => (alloy ? alloy.atomos.map((a) => a.pos) : cellAtoms.map((a) => a.pos)), [alloy, cellAtoms]);
  const elements = useMemo(() => (alloy ? alloyElementOptions(alloy) : []), [alloy]);
  const occupations = useMemo(() => (alloy ? alloyOccupationOptions(alloy.atomos) : []), [alloy]);
  const sites = useMemo(() => {
    if (alloy) return alloySiteOptions(alloy.atomos);
    const out: string[] = [];
    for (const a of cellAtoms) if (!out.includes(a.tipo)) out.push(a.tipo);
    return out;
  }, [alloy, cellAtoms]);

  const cut = f.cut;
  const axis: AxisIndex = cut?.axis ?? DEFAULT_CUT.axis;
  const range = useMemo(() => axisRange(positions, axis), [positions, axis]);
  const step = Math.max(0.01, Number(((range.max - range.min) / 100).toFixed(3)));

  const counts = useMemo(() => alloyDisplayCounts(views), [views]);
  // cores da legenda da cena (as mesmas do viewer): a cor nunca é o único código — há rótulo
  const colors = useMemo(() => (alloy ? Object.fromEntries(alloyLegend(alloy).map((l) => [l.element, l.color])) : {}), [alloy]);

  const hasSelection = alloy ? Boolean(alloySelection) : Boolean(selection);

  return (
    <div className="filter-panel" data-testid="filter-panel">
      <CategoryBox category="note" as="section" role="note"><p>{t('filter.note')}</p></CategoryBox>

      {alloy ? (
        <Dimension dim="elements" title={t('filter.elements')} values={elements} label={(e) => e} swatch={(e) => colors[e]} />
      ) : <p className="ds-field__hint">{t('filter.pureElementOnly')}</p>}

      {occupations.length ? <Dimension dim="occupations" title={t('filter.occupancy')} values={occupations} label={(k) => classLabel(t, k)} /> : null}
      {sites.length ? <Dimension dim="sites" title={t('filter.sites')} values={sites} label={(k) => classLabel(t, k)} /> : null}

      <section aria-labelledby="filter-cut-title">
        <h4 id="filter-cut-title" className="ds-label">{t('filter.cut')}</h4>
        <Checkbox
          label={t('filter.cutEnable')}
          checked={cut !== null}
          onChange={(on) => useSceneFilter.getState().setCut(on ? { ...DEFAULT_CUT, axis, position: (range.min + range.max) / 2, thickness: Math.max(step * 10, 0.2) } : null)}
          hint={t('filter.cutNote')}
        />
        {cut ? (
          <div className="filter-cut" data-testid="filter-cut-controls">
            <Select
              label={t('filter.cutAxis')}
              value={String(cut.axis)}
              data-testid="filter-cut-axis"
              onChange={(e) => useSceneFilter.getState().setCut({ axis: Number(e.target.value) as AxisIndex })}
              options={[0, 1, 2].map((a) => ({ value: String(a), label: t(`filter.axis.${a}` as 'filter.axis.0') }))}
            />
            <Segmented
              name="filter-cut-mode"
              size="sm"
              label={t('filter.cutModeLabel')}
              value={cut.mode}
              onChange={(mode) => useSceneFilter.getState().setCut({ mode })}
              options={CUT_MODES.map((m) => ({ value: m, label: t(`filter.cutMode.${m}` as 'filter.cutMode.below') }))}
            />
            <Slider
              label={t('filter.cutPosition')}
              id="filter-cut-position"
              min={Number(range.min.toFixed(3))}
              max={Number(range.max.toFixed(3))}
              step={step}
              value={cut.position}
              valueText={`${num(cut.position, 3)} a`}
              onChange={(position) => useSceneFilter.getState().setCut({ position })}
            />
            {cut.mode === 'slab' ? (
              <Slider
                label={t('filter.cutThickness')}
                id="filter-cut-thickness"
                min={step}
                max={Number(Math.max(step * 2, range.max - range.min).toFixed(3))}
                step={step}
                value={cut.thickness}
                valueText={`${num(cut.thickness, 3)} a`}
                onChange={(thickness) => useSceneFilter.getState().setCut({ thickness })}
              />
            ) : null}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="filter-neighbourhood-title">
        <h4 id="filter-neighbourhood-title" className="ds-label">{t('filter.neighbourhood')}</h4>
        <Checkbox
          label={t('filter.neighbourhood')}
          checked={f.neighbourhoodRadius !== null}
          disabled={!hasSelection}
          onChange={(on) => useSceneFilter.getState().set({ neighbourhoodRadius: on ? Math.max(step * 20, 0.6) : null })}
          hint={t('filter.neighbourhoodNote')}
        />
        {!hasSelection ? <p className="ds-field__hint">{t('filter.neighbourhoodNeedsSelection')}</p> : null}
        {f.neighbourhoodRadius !== null ? (
          <Slider
            label={t('filter.neighbourhoodRadius')}
            id="filter-neighbourhood-radius"
            min={step}
            max={Number(Math.max(step * 2, range.max - range.min).toFixed(3))}
            step={step}
            value={f.neighbourhoodRadius}
            valueText={`${num(f.neighbourhoodRadius, 3)} a`}
            onChange={(radius) => useSceneFilter.getState().set({ neighbourhoodRadius: radius })}
          />
        ) : null}
      </section>

      {alloy ? (
        <p className="ds-field__hint" data-testid="filter-counts">
          {t('filter.counts', { drawn: counts.drawn, total: alloy.atomos.length, unique: counts.unique })}
          <br />
          {t('filter.countsEngine', { unique: uniqueAtomCount(alloy), drawn: drawnAtomCount(alloy) })}
        </p>
      ) : null}

      <div className="ds-row">
        <Button size="sm" data-testid="filter-clear" disabled={!filterActive(f)} onClick={() => useSceneFilter.getState().clear()}>{t('filter.clear')}</Button>
        {filterActive(f) ? <Badge tone="warning">{t('filter.active')}</Badge> : <span className="ds-field__hint">{t('filter.none')}</span>}
      </div>
    </div>
  );
}
