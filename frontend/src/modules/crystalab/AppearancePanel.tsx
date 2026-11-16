/**
 * Menu de APARÊNCIA da cena (T-22 / R2-FE-04). Fica na seção Aparência da barra lateral, junto da
 * representação, dos interruptores de exibição e dos filtros — um lugar só, sem controle duplicado.
 *
 * O que ele permite: cor por ELEMENTO, por GRUPO e por ÁTOMO selecionado; cor das ARESTAS e dos
 * VÉRTICES da célula/supercélula; TAMANHO (escala de desenho) e OPACIDADE dos átomos; e
 * RESTAURAÇÃO do padrão, por seção e geral.
 *
 * Regras obedecidas aqui:
 *  - aparência é preferência de EXIBIÇÃO: nenhum valor, contagem ou composição muda. Nada é
 *    calculado neste arquivo; os elementos, as ocupações e os sítios listados vêm da resposta do
 *    motor (os mesmos campos que os filtros de exibição usam);
 *  - "GRUPO" é a ocupação que o motor devolve por átomo (solvente, substitucional, intersticial)
 *    e, na célula do metal puro, o tipo de sítio. Está dito na própria tela;
 *  - cor nunca é o único meio de distinguir: cada controle tem rótulo em texto, o valor
 *    hexadecimal aparece escrito e "personalizada" é dito por palavra;
 *  - marcadores geométricos (eixos, pontos de rede, vértices, marcador de seleção, planos e
 *    direções de Miller) são desenhados em seta, linha ou arame — nunca como a esfera sólida de um
 *    átomo, e nunca com a cor de um elemento. O painel explica isso em texto.
 */
import { useMemo } from 'react';
import { useI18n } from '../../i18n/index.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useViewer } from '../../stores/viewer.ts';
import { atomKey } from '../../stores/overlays.ts';
import { useAppearance, type ColorLevel } from '../../stores/appearance.ts';
import {
  atomsActive, cellActive, colorsActive, DEFAULT_APPEARANCE, OPACITY_RANGE, SCALE_RANGE,
} from '../../features/viewer3d/appearance.ts';
import { ALLOY_PALETTE, alloyLegendWith } from '../../features/viewer3d/alloyScene.ts';
import { buildAtoms } from '../../features/viewer3d/geometry.ts';
import { Button } from '../../design-system/primitives/Button.tsx';
import { Checkbox, ColorInput, Slider } from '../../design-system/primitives/Field.tsx';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { CategoryBox } from '../../design-system/primitives/Category.tsx';
import { alloyOccupationOptions } from './alloyDisplay.ts';
import { classLabel } from './FilterPanel.tsx';

/**
 * Cor padrão que o viewer usa, lida do MESMO token do tema (`src/design-system/tokens.css`), para
 * o seletor mostrar a cor de fato em vigor quando não há escolha pessoal. O recuo só vale quando
 * não há documento (teste em Node).
 */
function tokenColor(name: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback;
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

const siteTokenColor = (tipo: string): string => tokenColor(`--site-${tipo}`, '#1aa7d9');

/** Elementos da cena, na ordem do motor, com a cor em vigor e a cor padrão. */
function useElementRows(): Array<{ element: string; color: string | null; defaultColor: string; note: string | null }> {
  const alloy = useAlloy((s) => s.alloy);
  const structure = useCrystalab((s) => s.structure);
  const overrides = useAppearance((s) => s.overrides);
  const { t } = useI18n();
  return useMemo(() => {
    if (alloy) {
      return alloyLegendWith(alloy, overrides).map((l) => ({
        element: l.element,
        color: overrides.elements[l.element] ?? null,
        defaultColor: l.defaultColor,
        note: t(`alloy.role.${l.role}`),
      }));
    }
    if (!structure) return [];
    const element = structure.simbolo ?? structure.estrutura;
    return [{
      element,
      color: overrides.elements[element] ?? null,
      defaultColor: ALLOY_PALETTE[0] as string,
      note: null,
    }];
  }, [alloy, structure, overrides, t]);
}

/** Grupos da cena: ocupação do motor (liga) ou tipo de sítio (célula do metal puro). */
function useGroupRows(): Array<{ key: string; defaultColor: string; isSite: boolean }> {
  const alloy = useAlloy((s) => s.alloy);
  const structure = useCrystalab((s) => s.structure);
  const supercell = useViewer((s) => s.supercell);
  return useMemo(() => {
    if (alloy) return alloyOccupationOptions(alloy.atomos).map((k) => ({ key: k, defaultColor: ALLOY_PALETTE[0] as string, isSite: false }));
    if (!structure) return [];
    const out: string[] = [];
    for (const a of buildAtoms(structure, supercell)) if (!out.includes(a.tipo)) out.push(a.tipo);
    return out.map((k) => ({ key: k, defaultColor: siteTokenColor(k), isSite: true }));
  }, [alloy, structure, supercell]);
}

function ColorRow({ level, name, label, hint, color, defaultColor, testId }: {
  level: ColorLevel;
  name: string;
  label: string;
  hint?: string;
  color: string | null;
  defaultColor: string;
  testId: string;
}) {
  const { t } = useI18n();
  return (
    <ColorInput
      label={label}
      hint={hint}
      value={color}
      defaultValue={defaultColor}
      testId={testId}
      customText={t('appearance.custom')}
      resetLabel={t('appearance.resetOf', { name: label })}
      onChange={(c) => useAppearance.getState().setColor(level, name, c)}
      onReset={() => useAppearance.getState().setColor(level, name, null)}
    />
  );
}

/** Cores: por elemento, por grupo e para o átomo selecionado. */
export function AppearanceColors() {
  const { t } = useI18n();
  const app = useAppearance();
  const elements = useElementRows();
  const groups = useGroupRows();
  const alloy = useAlloy((s) => s.alloy);
  const alloySelection = useViewer((s) => s.alloySelection);
  const selection = useViewer((s) => s.selection);
  const atomId = alloy ? alloySelection : (selection ? atomKey(selection) : null);
  const atomColors = Object.entries(app.overrides.atoms);
  return (
    <div className="cl-appearance__block" data-testid="appearance-colors">
      <CategoryBox category="note" as="section" role="note"><p>{t('appearance.precedence')}</p></CategoryBox>

      <section aria-labelledby="appearance-elements-title">
        <h4 id="appearance-elements-title" className="ds-label">{t('appearance.byElement')}</h4>
        {elements.length ? elements.map((e) => (
          <ColorRow
            key={e.element}
            level="elements"
            name={e.element}
            label={e.note ? `${e.element} · ${e.note}` : e.element}
            color={e.color}
            defaultColor={e.defaultColor}
            testId={`appearance-element-${e.element}`}
          />
        )) : <p className="ds-field__hint">{t('appearance.noElements')}</p>}
      </section>

      <section aria-labelledby="appearance-groups-title">
        <h4 id="appearance-groups-title" className="ds-label">{t('appearance.byGroup')}</h4>
        <p className="ds-field__hint">{t('appearance.groupNote')}</p>
        {groups.map((g) => (
          <ColorRow
            key={g.key}
            level="groups"
            name={g.key}
            label={classLabel(t, g.key)}
            color={app.overrides.groups[g.key] ?? null}
            defaultColor={g.defaultColor}
            testId={`appearance-group-${g.key}`}
          />
        ))}
      </section>

      <section aria-labelledby="appearance-atom-title">
        <h4 id="appearance-atom-title" className="ds-label">{t('appearance.byAtom')}</h4>
        {atomId ? (
          <ColorRow
            level="atoms"
            name={atomId}
            label={t('appearance.atomLabel', { id: atomId })}
            color={app.overrides.atoms[atomId] ?? null}
            defaultColor={(elements[0]?.color ?? elements[0]?.defaultColor ?? ALLOY_PALETTE[0]) as string}
            testId="appearance-atom"
          />
        ) : <p className="ds-field__hint">{t('appearance.noAtomSelected')}</p>}
        {atomColors.length ? (
          <ul className="filter-list" aria-label={t('appearance.atomColorsList')} data-testid="appearance-atom-colors">
            {atomColors.map(([id, color]) => (
              <li key={id} className="filter-row">
                <span className="legend-swatch" style={{ background: color }} aria-hidden="true" />
                <span className="ds-mono">{t('appearance.atomLabel', { id })} · {color.toUpperCase()}</span>
                <Button size="sm" variant="ghost" aria-label={t('appearance.removeAtomColor', { id })} onClick={() => useAppearance.getState().setColor('atoms', id, null)}>{t('appearance.reset')}</Button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <div className="ds-row">
        <Button size="sm" data-testid="appearance-reset-colors" disabled={!colorsActive(app)} onClick={() => useAppearance.getState().resetColors()}>{t('appearance.resetSection')}</Button>
        {colorsActive(app) ? <Badge tone="info">{t('appearance.customCount', { n: Object.keys(app.overrides.elements).length + Object.keys(app.overrides.groups).length + atomColors.length })}</Badge> : null}
      </div>
    </div>
  );
}

/** Arestas e vértices da célula/supercélula. O vértice é marcador geométrico, não átomo. */
export function AppearanceCell() {
  const { t } = useI18n();
  const app = useAppearance();
  return (
    <div className="cl-appearance__block" data-testid="appearance-cell">
      <ColorInput
        label={t('appearance.edgeColor')}
        value={app.edgeColor}
        defaultValue={tokenColor('--viewer-edge', '#29313f')}
        testId="appearance-edge"
        customText={t('appearance.custom')}
        resetLabel={t('appearance.resetOf', { name: t('appearance.edgeColor') })}
        onChange={(c) => useAppearance.getState().set({ edgeColor: c })}
        onReset={() => useAppearance.getState().set({ edgeColor: null })}
      />
      <Checkbox
        id="appearance-vertices"
        label={t('appearance.vertices')}
        checked={app.vertices}
        hint={t('appearance.verticesNote')}
        onChange={(on) => useAppearance.getState().set({ vertices: on })}
      />
      <ColorInput
        label={t('appearance.vertexColor')}
        value={app.vertexColor}
        defaultValue={tokenColor('--color-ink', '#10131a')}
        hint={app.vertices ? undefined : t('appearance.verticesOff')}
        testId="appearance-vertex"
        customText={t('appearance.custom')}
        resetLabel={t('appearance.resetOf', { name: t('appearance.vertexColor') })}
        onChange={(c) => useAppearance.getState().set({ vertexColor: c })}
        onReset={() => useAppearance.getState().set({ vertexColor: null })}
      />
      <div className="ds-row">
        <Button size="sm" data-testid="appearance-reset-cell" disabled={!cellActive(app)} onClick={() => useAppearance.getState().resetCell()}>{t('appearance.resetSection')}</Button>
      </div>
    </div>
  );
}

/** Tamanho e opacidade dos átomos: escala de desenho, nunca o raio do motor. */
export function AppearanceAtoms() {
  const { t, num } = useI18n();
  const app = useAppearance();
  return (
    <div className="cl-appearance__block" data-testid="appearance-atoms">
      <Slider
        label={t('appearance.scale')}
        id="appearance-scale"
        min={SCALE_RANGE.min}
        max={SCALE_RANGE.max}
        step={SCALE_RANGE.step}
        value={app.atomScale}
        valueText={t('appearance.scaleValue', { x: num(app.atomScale, 2) })}
        onChange={(v) => useAppearance.getState().set({ atomScale: v })}
      />
      <p className="ds-field__hint">{t('appearance.scaleNote')}</p>
      <Slider
        label={t('appearance.opacity')}
        id="appearance-opacity"
        min={OPACITY_RANGE.min}
        max={OPACITY_RANGE.max}
        step={OPACITY_RANGE.step}
        value={app.opacity}
        valueText={t('appearance.opacityValue', { pct: Math.round(app.opacity * 100) })}
        onChange={(v) => useAppearance.getState().set({ opacity: v })}
      />
      <div className="ds-row">
        <Button size="sm" data-testid="appearance-reset-atoms" disabled={!atomsActive(app)} onClick={() => useAppearance.getState().resetAtoms()}>{t('appearance.resetSection')}</Button>
        <span className="ds-field__hint">{t('appearance.scaleValue', { x: num(DEFAULT_APPEARANCE.atomScale, 2) })}</span>
      </div>
    </div>
  );
}

/** Explicação da distinção entre marcador geométrico e átomo real (requisito explícito do T-22). */
export function AppearanceMarkers() {
  const { t } = useI18n();
  return (
    <CategoryBox category="reference" as="section" className="cl-appearance__block" data-testid="appearance-markers">
      <p>{t('appearance.markersNote')}</p>
      <ul className="cl-legend__items">
        <li className="legend-chip"><i className="cl-glyph cl-glyph--axes" aria-hidden="true" />{t('view.toggle.axes')}</li>
        <li className="legend-chip"><i className="cl-glyph cl-glyph--wire" aria-hidden="true" />{t('view.toggle.latticePoints')}</li>
        <li className="legend-chip"><i className="cl-glyph cl-glyph--vertex" aria-hidden="true" />{t('legend.marker.vertices')}</li>
        <li className="legend-chip"><i className="cl-glyph cl-glyph--wire" aria-hidden="true" />{t('legend.marker.selection')}</li>
        <li className="legend-chip"><i className="cl-glyph cl-glyph--edge" aria-hidden="true" />{t('view.toggle.edges')}</li>
      </ul>
    </CategoryBox>
  );
}

/** Restauração geral: devolve toda a aparência ao padrão de fábrica. */
export function AppearanceResetAll() {
  const { t } = useI18n();
  const app = useAppearance();
  const active = colorsActive(app) || cellActive(app) || atomsActive(app);
  return (
    <div className="ds-row cl-appearance__reset">
      <Button size="sm" icon="restart" data-testid="appearance-reset-all" disabled={!active} onClick={() => useAppearance.getState().resetAll()}>{t('appearance.resetAll')}</Button>
      {active ? <Badge tone="info">{t('appearance.active')}</Badge> : null}
    </div>
  );
}
