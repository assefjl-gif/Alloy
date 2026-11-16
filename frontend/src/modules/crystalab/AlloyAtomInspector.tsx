/**
 * Inspetor do átomo da LIGA (T-24 / R2-FE-03): clique na cena ou navegação por teclado na lista,
 * com os campos que o motor devolve para cada átomo (contrato R1 §2.3): `id`, `elemento`, `pos`,
 * `pos_nm`, `frac`, `frac_celula`, `celula`, `ocupacao`, `sitio` (nome, Wyckoff, NC), `fase`,
 * `pos_ideal`, `imagem` e `imagem_de`.
 *
 * Regras obedecidas aqui:
 *  - nada é recalculado: toda coordenada, rótulo e número vem da resposta da API;
 *  - campo ausente aparece como INDISPONÍVEL (com a causa quando o motor a dá), nunca como zero
 *    nem em branco — `wyckoff` vem `null` de propósito e é dito assim;
 *  - imagem periódica é identificada como imagem, aponta para o átomo de origem e não entra em
 *    contagem nem em legenda;
 *  - propriedade do ELEMENTO PURO (raio, massa, estrutura) fica em bloco separado e rotulado como
 *    dado tabelado do elemento puro — nunca como propriedade calculada deste átomo na liga.
 */
import { useMemo } from 'react';
import { useI18n } from '../../i18n/index.ts';
import type { AlloyResult, Vec3 } from '../../services/api/contracts.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { useSceneFilter } from '../../stores/sceneFilter.ts';
import { useViewer } from '../../stores/viewer.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { Button } from '../../design-system/primitives/Button.tsx';
import { CategoryBox } from '../../design-system/primitives/Category.tsx';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { selectedPosition, toVisibilityFilter } from '../../features/viewer3d/sceneFilterState.ts';
import { ALLOY_PALETTE, alloyLegend } from '../../features/viewer3d/alloyScene.ts';
import { alloyAtomViewById, alloyAtomViews, alloyDisplayCounts, drawnAtomCount, pureElementOf, uniqueAtomCount, type AlloyAtomView } from './alloyDisplay.ts';

/** Ocupações que a interface sabe nomear; qualquer outro valor é mostrado como veio do motor. */
const OCCUPANCY_KEYS: Record<string, 'alloyAtom.occ.rede' | 'alloyAtom.occ.substitucional' | 'alloyAtom.occ.intersticial'> = {
  rede: 'alloyAtom.occ.rede',
  substitucional: 'alloyAtom.occ.substitucional',
  intersticial: 'alloyAtom.occ.intersticial',
};

const domId = (id: string): string => `alloy-atom-opt-${id.replace(/[^\w-]/g, '_')}`;

/** Visões dos átomos desenhados, já com a visibilidade do filtro de exibição. */
export function useAlloyAtomViews(r: AlloyResult | null): AlloyAtomView[] {
  const filterState = useSceneFilter();
  const alloySelection = useViewer((s) => s.alloySelection);
  const structure = useCrystalab((s) => s.structure);
  const selection = useViewer((s) => s.selection);
  const supercell = useViewer((s) => s.supercell);
  return useMemo(() => {
    if (!r) return [];
    const center = filterState.neighbourhoodRadius === null ? null : selectedPosition(r, alloySelection, structure, selection, supercell);
    return alloyAtomViews(r.atomos, toVisibilityFilter(filterState, center));
  }, [r, filterState, alloySelection, structure, selection, supercell]);
}

function Coord({ value, suffix }: { value: Vec3 | null | undefined; suffix?: string }) {
  const { t, num } = useI18n();
  if (!value) return <span className="ds-muted">{t('hea.unavailable')}</span>;
  return <span className="ds-mono">{`(${value.map((v) => num(v, 4)).join('; ')})${suffix ? ` ${suffix}` : ''}`}</span>;
}

/** Cartão do átomo selecionado: campos da API, com indisponível explícito. */
function SelectedAtomCard({ r, view }: { r: AlloyResult; view: AlloyAtomView }) {
  const { t } = useI18n();
  const a = view.atom;
  const site = a.sitio;
  const pure = pureElementOf(r, a.elemento);
  const unavailable = <span className="ds-muted">{t('hea.unavailable')}</span>;
  return (
    <CategoryBox category="result" as="section" className="atom-card" aria-live="polite" data-testid="alloy-atom-card">
      <h3>{t('alloyAtom.title')}</h3>
      <dl className="guided__dl">
        <dt>{t('alloyAtom.element')}</dt><dd><strong>{a.elemento}</strong></dd>
        <dt>{t('alloyAtom.id')}</dt><dd className="ds-mono" data-testid="alloy-atom-id">{a.id ?? view.id}</dd>
        <dt>{t('alloyAtom.positionA')}</dt><dd><Coord value={a.pos} /></dd>
        <dt>{t('alloyAtom.positionNm')}</dt><dd><Coord value={a.pos_nm} suffix="nm" /></dd>
        <dt>{t('alloyAtom.fractional')}</dt><dd><Coord value={a.frac} /></dd>
        <dt>{t('alloyAtom.fractionalCell')}</dt><dd><Coord value={a.frac_celula} /></dd>
        <dt>{t('alloyAtom.cell')}</dt><dd className="ds-mono">{a.celula ? a.celula.join(', ') : unavailable}</dd>
        <dt>{t('alloyAtom.phase')}</dt><dd lang="pt-BR">{a.fase ?? unavailable}</dd>
        <dt>{t('alloyAtom.site')}</dt><dd lang="pt-BR" data-testid="alloy-atom-site">{site?.nome ?? unavailable}</dd>
        <dt>{t('alloyAtom.wyckoff')}</dt>
        <dd data-testid="alloy-atom-wyckoff">{site?.wyckoff ?? <span className="ds-muted">{t('alloyAtom.wyckoffUnavailable')}</span>}</dd>
        <dt>{t('alloyAtom.nc')}</dt><dd>{site?.nc_txt ?? (site?.nc !== undefined ? String(site.nc) : unavailable)}</dd>
        <dt>{t('alloyAtom.occupancy')}</dt>
        <dd data-testid="alloy-atom-occupancy">{a.ocupacao ? t(OCCUPANCY_KEYS[a.ocupacao] ?? 'alloyAtom.occ.rede') : (a.tipo ?? unavailable)}</dd>
        <dt>{t('alloyAtom.idealPos')}</dt><dd><Coord value={a.pos_ideal} /></dd>
        <dt>{t('alloyAtom.image')}</dt>
        <dd data-testid="alloy-atom-image">
          {view.image ? (
            <>
              <Badge tone="warning">{t('alloyAtom.imageTag')}</Badge>{' '}
              {t('alloyAtom.imageYes', { of: a.imagem_de ?? t('hea.unavailable') })}
            </>
          ) : t('alloyAtom.imageNo')}
        </dd>
      </dl>
      {view.image ? (
        <>
          <p className="ds-field__hint">{t('alloyAtom.imageNote')}</p>
          {a.imagem_de ? (
            <Button size="sm" data-testid="alloy-atom-source" onClick={() => useViewer.getState().set({ alloySelection: a.imagem_de as string })}>{t('alloyAtom.goToSource')}</Button>
          ) : null}
        </>
      ) : null}
      {!view.visible ? <p className="ds-field__error" role="status">{t('alloyAtom.hiddenByFilter')}</p> : null}

      {/* bloco SEPARADO: dado tabelado do elemento puro, não propriedade deste átomo na liga */}
      <CategoryBox category="note" as="section" aria-labelledby="alloy-atom-pure-title" data-testid="alloy-atom-pure">
        <h4 id="alloy-atom-pure-title">{t('alloyAtom.pureTitle', { element: a.elemento })}</h4>
        <p className="ds-field__hint">{t('alloyAtom.pureNote')}</p>
        {pure ? (
          <dl className="guided__dl">
            <dt>R (nm)</dt><dd>{pure.raio_nm === null ? unavailable : <PureNumber value={pure.raio_nm} digits={4} />}</dd>
            <dt>M (g/mol)</dt><dd>{pure.massa_g_mol === null ? unavailable : <PureNumber value={pure.massa_g_mol} digits={3} />}</dd>
            <dt>{t('alloy.pure.structure')}</dt><dd>{pure.estrutura_elemento_puro ?? unavailable}</dd>
            <dt>{t('alloy.pure.dataState')}</dt>
            <dd>{pure.estado_do_dado}{pure.fonte ? <><br /><span className="ds-field__hint" lang="pt-BR">{pure.fonte}</span></> : null}</dd>
          </dl>
        ) : <p className="ds-muted">{t('alloyAtom.pureMissing')}</p>}
        <p className="ds-field__hint">{t('alloyAtom.drawRadiusNote')}</p>
      </CategoryBox>
      <Button size="sm" onClick={() => useViewer.getState().set({ alloySelection: null })}>{t('atom.clear')}</Button>
    </CategoryBox>
  );
}

function PureNumber({ value, digits }: { value: number; digits: number }) {
  const { num } = useI18n();
  return <>{num(value, digits)}</>;
}

/**
 * Inspetor + lista navegável por teclado dos átomos da liga. A lista mostra apenas o que está
 * VISÍVEL (filtro e corte de exibição), e o título separa átomos únicos de imagens periódicas,
 * dizendo que a contagem é de exibição.
 */
export function AlloyAtomInspector() {
  const { t, num } = useI18n();
  const r = useAlloy((s) => s.alloy);
  const selection = useViewer((s) => s.alloySelection);
  const views = useAlloyAtomViews(r);
  const visible = useMemo(() => views.filter((v) => v.visible), [views]);
  const counts = useMemo(() => alloyDisplayCounts(views), [views]);
  const colors = useMemo(() => (r ? Object.fromEntries(alloyLegend(r).map((l) => [l.element, l.color])) : {}), [r]);
  if (!r) return null;
  const selected = alloyAtomViewById(views, selection);
  const move = (next: number) => {
    const v = visible[next];
    if (!v) return;
    useViewer.getState().set({ alloySelection: v.id });
    document.getElementById(domId(v.id))?.scrollIntoView({ block: 'nearest' });
  };
  return (
    <div className="atom-inspector" data-testid="alloy-atom-inspector">
      {selected ? <SelectedAtomCard r={r} view={selected} /> : <p className="ds-muted">{t('alloyAtom.none')}</p>}
      <h3 className="atom-list__title" id="alloy-atom-list-title" data-testid="alloy-atom-list-title">
        {t('alloyAtom.listTitle', { unique: counts.unique, images: counts.images })}
      </h3>
      <p className="ds-field__hint">{t('alloyAtom.listHint')}</p>
      <p className="ds-field__hint" data-testid="alloy-atom-engine-counts">{t('filter.countsEngine', { unique: uniqueAtomCount(r), drawn: drawnAtomCount(r) })}</p>
      <ul
        className="atom-list"
        role="listbox"
        aria-labelledby="alloy-atom-list-title"
        tabIndex={0}
        data-testid="alloy-atom-list"
        aria-activedescendant={selected && selected.visible ? domId(selected.id) : undefined}
        onKeyDown={(e) => {
          if (!visible.length) return;
          const cur = selected ? visible.findIndex((v) => v.id === selected.id) : -1;
          if (e.key === 'ArrowDown') move(Math.min(visible.length - 1, cur + 1));
          else if (e.key === 'ArrowUp') move(Math.max(0, cur - 1));
          else if (e.key === 'Home') move(0);
          else if (e.key === 'End') move(visible.length - 1);
          else if (e.key === 'Escape') { useViewer.getState().set({ alloySelection: null }); return; }
          else return;
          e.preventDefault();
        }}
      >
        {visible.map((v) => (
          <li
            key={v.id}
            id={domId(v.id)}
            role="option"
            aria-selected={selection === v.id}
            className={`atom-opt ${v.image ? 'is-replica' : ''}`}
            onClick={() => useViewer.getState().set({ alloySelection: v.id })}
          >
            <span className="legend-swatch" style={{ background: colors[v.atom.elemento] ?? ALLOY_PALETTE[0] }} aria-hidden="true" />
            <span>{`${v.atom.elemento} · ${v.id}`}</span>
            <span className="ds-mono">({v.atom.pos.map((p) => num(p, 2)).join('; ')})</span>
            {v.image ? <span className="atom-opt__tag">{t('alloyAtom.imageTag')}</span> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
