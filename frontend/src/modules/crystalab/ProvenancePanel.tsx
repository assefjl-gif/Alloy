/**
 * Painel de procedência (5.7): separa DADO DO PREDITOR, DADO DE REFERÊNCIA (célula do motor
 * CrystaLab) e ILUSTRAÇÃO. A transição HEA → CrystaLab nunca cria dados (5.3, Fluxo C).
 */
import { useI18n } from '../../i18n/index.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useViewer } from '../../stores/viewer.ts';
import { useHea } from '../hea/store.ts';
import { demoPolicy } from '../../stores/capabilities.ts';
import { deepEqual } from '../../utils/freeze.ts';
import { CategoryBox, CategoryTag, DemoSeal } from '../../design-system/primitives/Category.tsx';
import { Button, ToggleButton } from '../../design-system/primitives/Button.tsx';
import { elementLegendFor } from './elementLegend.ts';
import { HEA_DEMO_SEED } from '../../services/adapters/heaDemo.ts';
import { navigate } from '../../app/router.ts';

const SHAPE_KEYS = { sphere: 'shape.sphere', cube: 'shape.cube', octahedron: 'shape.octahedron', tetrahedron: 'shape.tetrahedron', icosahedron: 'shape.icosahedron', dodecahedron: 'shape.dodecahedron', cylinder: 'shape.cylinder' } as const;

export function HeaTransferBanner() {
  const { t } = useI18n();
  const tr = useCrystalab((s) => s.heaTransfer);
  if (!tr) return null;
  const isUser = tr.structure.basis === 'user-choice';
  return (
    <CategoryBox category={tr.origin === 'demo' ? 'demo' : 'result'} as="section" className="hea-banner" aria-labelledby="hea-banner-title" data-testid="hea-banner">
      <div className="hea-banner__head">
        <h2 id="hea-banner-title">{t('bridge.bannerTitle', { name: tr.result.nome })}</h2>
        {tr.origin === 'demo' ? <DemoSeal text={t('common.demo')} detail={t('hea.demoDetail')} /> : <CategoryTag category="result" label={t('bridge.fromPredictor')} />}
      </div>
      <p>
        {isUser ? <strong className="basis-user" data-testid="basis-user">{t('bridge.basisUserLong', { code: tr.structure.code })}</strong> : <span data-testid="basis-predictor">{t('bridge.basisPredictorLong', { code: tr.structure.code, phase: tr.structure.phaseText })}</span>}
      </p>
      <p className="ds-field__hint">{t('bridge.idealized')}</p>
      <Button size="sm" icon="flask" onClick={() => navigate('hea')}>{t('bridge.backToHea')}</Button>
    </CategoryBox>
  );
}

export function ProvenancePanel() {
  const { t, num } = useI18n();
  const transfer = useCrystalab((s) => s.heaTransfer);
  const structure = useCrystalab((s) => s.structure);
  const coloring = useViewer((s) => s.elementColoring);
  const original = useHea((s) => s.result);
  if (!transfer || !structure) {
    return (
      <div className="prov" data-testid="provenance">
        <CategoryBox category="result" as="section" className="prov__col">
          <h3>{t('prov.engine')}</h3>
          <p>{structure ? t('prov.engineOnly', { label: structure.rotulo }) : t('viewer.empty')}</p>
        </CategoryBox>
        <p className="ds-muted">{t('prov.noTransfer')}</p>
      </div>
    );
  }
  const r = transfer.result;
  const identical = original ? deepEqual(original, r) : null;
  const demoAllowed = demoPolicy() === 'on' || transfer.origin === 'demo';
  const legend = elementLegendFor(r.comp_percent);
  return (
    <div className="prov" data-testid="provenance">
      <CategoryBox category={transfer.origin === 'demo' ? 'demo' : 'result'} as="section" className="prov__col" aria-labelledby="prov-pred">
        <h3 id="prov-pred">{t('prov.predictor')}</h3>
        {transfer.origin === 'demo' ? <DemoSeal text={t('common.demo')} detail={t('hea.demoDetail')} /> : null}
        <dl className="guided__dl" data-testid="prov-predictor">
          <dt>{t('hea.alloy')}</dt><dd>{r.nome}</dd>
          <dt>{t('hea.phase')}</dt><dd lang="pt-BR">{r.fase}</dd>
          <dt>{t('hea.verdict')}</dt><dd lang="pt-BR">{r.veredito}</dd>
          <dt>δ</dt><dd>{num(r.delta, 2)} %</dd>
          <dt>Ω</dt><dd>{num(r.omega, 2)}</dd>
          <dt>ΔH<sub>mix</sub></dt><dd>{num(r.dH, 2)} kJ/mol</dd>
          <dt>ΔS<sub>mix</sub></dt><dd>{num(r.dS, 2)} J/mol·K</dd>
          <dt>VEC</dt><dd>{num(r.VEC, 2)}</dd>
          <dt>{t('hea.composition')}</dt><dd>{Object.entries(r.comp_percent).map(([e, v]) => `${e} ${num(v, 1)}%`).join(' · ')}</dd>
        </dl>
        <p className="prov__check" data-testid="prov-identical">
          {identical === null ? t('prov.originalGone') : identical ? `✓ ${t('prov.identical')}` : `✗ ${t('prov.different')}`}
        </p>
        <p className="ds-field__hint">{t('prov.immutable', { at: new Date(transfer.receivedAt).toLocaleString() })}</p>
      </CategoryBox>

      <CategoryBox category="reference" as="section" className="prov__col" aria-labelledby="prov-ref">
        <h3 id="prov-ref">{t('prov.reference')}</h3>
        <dl className="guided__dl">
          <dt>{t('metrics.structure')}</dt><dd lang="pt-BR">{`${structure.estrutura_nome} (${structure.estrutura})`}</dd>
          <dt>{t('prov.basis')}</dt><dd>{t(`bridge.basis.${transfer.structure.basis}`)}</dd>
          <dt>n · NC</dt><dd>{`${structure.n} · ${structure.nc}`}</dd>
          <dt>{t('metrics.apf')}</dt><dd>{num(structure.fea, 3)}</dd>
          <dt>a</dt><dd>{structure.relacao_a} {t('prov.unitsOfR')}</dd>
        </dl>
        <p className="ds-field__hint">{t('prov.referenceNote')}</p>
        <p className="interp-warn" role="note" data-testid="delta-limitation">{t('prov.deltaLimitation', { delta: num(r.delta, 2) })}</p>
      </CategoryBox>

      <CategoryBox category="demo" as="section" className="prov__col" aria-labelledby="prov-ill">
        <h3 id="prov-ill">{t('prov.illustration')}</h3>
        <p>{t('prov.mixedSite')}</p>
        <ToggleButton
          size="sm"
          pressed={Boolean(coloring?.enabled)}
          disabled={!demoAllowed}
          data-testid="toggle-coloring"
          onPressedChange={(v) => useViewer.getState().set({ elementColoring: v ? { enabled: true, seed: coloring?.seed ?? transfer.seed ?? HEA_DEMO_SEED } : null })}
        >
          {t('prov.randomDistribution')}
        </ToggleButton>
        {!demoAllowed ? <p className="ds-field__hint">{t('prov.randomOnlyDemo')}</p> : null}
        {coloring?.enabled ? (
          <>
            <DemoSeal text={t('common.illustrative')} detail={t('bridge.coloringDetail')} />
            <p className="ds-field__hint" data-testid="coloring-seed">{t('prov.seed', { seed: coloring.seed })}</p>
            <Button size="sm" onClick={() => useViewer.getState().set({ elementColoring: { enabled: true, seed: coloring.seed + 1 } })}>{t('prov.newSeed')}</Button>
            <ul className="element-legend" aria-label={t('prov.legend')}>
              {legend.map((l) => (
                <li key={l.element}><i className={`shape-swatch shape-swatch--${l.shape}`} style={{ color: l.color }} aria-hidden="true" /> <strong>{l.element}</strong> — {t(SHAPE_KEYS[l.shape])}</li>
              ))}
            </ul>
          </>
        ) : null}
      </CategoryBox>
    </div>
  );
}
