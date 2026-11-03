import { lazy, Suspense, useEffect } from 'react';
import { dispatch } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { MetricCard } from '../../design-system/layout/MetricCard.tsx';
import { Panel } from '../../design-system/layout/Panel.tsx';
import { Button } from '../../design-system/primitives/Button.tsx';
import { CategoryBox, DemoSeal } from '../../design-system/primitives/Category.tsx';
import { Disclosure } from '../../design-system/primitives/Disclosure.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { Terminal } from '../../features/terminal/Terminal.tsx';
import { useServiceMode } from '../../stores/capabilities.ts';
import { useTerminal } from '../../stores/terminal.ts';
import { compositionToText, useHea } from './store.ts';
import { matchStructure } from './transfer.ts';
import type { HeaResult } from '../../services/api/contracts.ts';

const HeaCharts = lazy(() => import('./HeaCharts.tsx'));

function HeaLab() {
  const { t } = useI18n();
  const bootstrap = useHea((s) => s.bootstrap);
  const selectedKey = useHea((s) => s.selectedKey);
  const editor = useHea((s) => s.editorText);
  const name = useHea((s) => s.name);
  const alloys = Object.entries(bootstrap?.alloys ?? {});
  const shortcuts = [
    { label: t('hea.analyze'), command: 'analisar', tone: 'cyan' },
    { label: t('hea.normalize'), command: 'normalizar', tone: 'green' },
    { label: t('hea.help'), command: 'ajuda', tone: 'amber' },
    { label: t('shortcuts.clear'), command: 'limpar', tone: 'gray' },
  ];
  return (
    <div className="lab">
      <header className="brand-row">
        <div>
          <p className="brand-row__title">{t('hea.brand')}</p>
          <p className="brand-row__sub">{t('hea.brandSub')}</p>
        </div>
        <span className="lab-badge">v1.17 · v2.0</span>
      </header>
      <Disclosure title={t('hea.blocks')} className="lab-disclosure lab-disclosure--blocks" aside={<span className="count-pill">{alloys.length}</span>}>
        <ul className="block-list" data-testid="block-list" aria-label={t('hea.blocks')}>
          {alloys.map(([key, alloy]) => (
            <li key={key}>
              <button type="button" className={`alloy-block ${key === selectedKey ? 'is-active' : ''}`} aria-pressed={key === selectedKey} draggable
                onDragStart={(e) => e.dataTransfer.setData('text/plain', key)}
                onClick={() => void dispatch({ type: 'hea.load', key }, 'block')}>
                <span className="block-head"><span className="block-name">{alloy.nome}</span><span className="block-tag">{alloy.grupo}</span></span>
                <span className="block-formula">{Object.keys(alloy.composicao).join(' + ')}</span>
                <span className="composition-strip composition-strip--5">{Object.keys(alloy.composicao).slice(0, 5).map((e) => <span key={e} className="element-chip">{e}</span>)}</span>
              </button>
            </li>
          ))}
        </ul>
      </Disclosure>
      <Disclosure title={t('terminal.title')} className="lab-disclosure">
        <section className="terminal-panel" aria-label={t('terminal.title')}>
          <div className="lab-editor">
            <div className="lab-section__title"><h3>{t('hea.composition')}</h3><span className="lab-current">{name || t('hea.userAlloy')}</span></div>
            <label htmlFor="compositionEditor" className="sr-only">{t('hea.compositionLabel')}</label>
            <textarea id="compositionEditor" className="composition-editor" data-testid="composition-editor" spellCheck={false} value={editor}
              onChange={(e) => useHea.getState().set({ editorText: e.target.value, selectedKey: '' })}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); const key = e.dataTransfer.getData('text/plain'); if (key) void dispatch({ type: 'hea.load', key }, 'block'); }} />
          </div>
          <Terminal context="hea" placeholderKey="terminal.placeholderHea" shortcuts={shortcuts} />
        </section>
      </Disclosure>
    </div>
  );
}

function ComparisonWithReference({ r }: { r: HeaResult }) {
  const { t, num } = useI18n();
  const ref = useHea((s) => s.bootstrap?.reference);
  if (!ref) return null;
  const rows: Array<[string, number | null, number | null, string]> = [
    [t('hea.row.entropy'), r.dS, ref.dS, 'J/mol·K'], [t('hea.row.omega'), r.omega, ref.omega, ''], [t('hea.row.delta'), r.delta, ref.delta, '%'], ['VEC', r.VEC, ref.VEC, ''], [t('hea.row.enthalpy'), r.dH, ref.dH, 'kJ/mol'],
  ];
  return (
    <Panel title={t('hea.comparisonTitle')} aside={`${ref.T_padrao} · ${ref.P_padrao}`} headingLevel={2}>
      <div className="ds-table-wrap">
        <table className="ds-table">
          <thead><tr><th scope="col">{t('hea.parameter')}</th><th scope="col">{t('hea.calculated')}</th><th scope="col">{t('hea.reference')}</th><th scope="col">{t('hea.difference')}</th></tr></thead>
          <tbody>{rows.map(([label, v, rv, unit]) => <tr key={label}><th scope="row">{label}</th><td>{v === null ? t('hea.unavailable') : `${num(v, 2)} ${unit}`}</td><td>{rv === null ? '—' : `${num(rv, 2)} ${unit}`}</td><td>{v === null || rv === null ? '—' : `${v - rv >= 0 ? '+' : ''}${num(v - rv, 2)}`}</td></tr>)}</tbody>
        </table>
      </div>
      <p className="table-note">{t('hea.differenceNote')}</p>
    </Panel>
  );
}

/** Grandezas que o servidor não calculou, com o motivo (nunca substituídas por estimativas no front). */
function Unavailable({ r }: { r: HeaResult }) {
  const { t } = useI18n();
  const items = Object.entries(r.indisponiveis ?? {});
  if (!items.length) return null;
  return (
    <CategoryBox category="feedback" as="section" aria-labelledby="hea-unavailable-title" data-testid="hea-unavailable">
      <h2 id="hea-unavailable-title">{t('hea.unavailableTitle')}</h2>
      <ul>{items.map(([k, motivo]) => <li key={k} lang="pt-BR"><strong>{k}</strong>: {motivo}</li>)}</ul>
    </CategoryBox>
  );
}

function BridgeCard({ r }: { r: HeaResult }) {
  const { t } = useI18n();
  const match = matchStructure(r);
  return (
    <CategoryBox category="control" as="section" className="bridge-card" aria-labelledby="bridge-title" data-testid="bridge-card">
      <h2 id="bridge-title">{t('bridge.title')}</h2>
      <p>{match.code ? t('bridge.direct', { code: match.code, phase: r.fase }) : t('bridge.needsChoice', { phase: r.fase })}</p>
      {match.code ? (
        <Button variant="primary" icon="cube" data-testid="open-in-crystalab" onClick={() => void dispatch({ type: 'hea.toCrystalab' }, 'form')}>{t('bridge.open', { code: match.code })}</Button>
      ) : (
        <div className="ds-row" role="group" aria-label={t('bridge.choose')}>
          {(match.candidates.length ? match.candidates : (['CFC', 'CCC', 'HC'] as const)).map((code) => (
            <Button key={code} data-testid={`open-in-crystalab-${code}`} onClick={() => void dispatch({ type: 'hea.toCrystalab', choice: code }, 'form')}>{t('bridge.openAsChoice', { code })}</Button>
          ))}
        </div>
      )}
      <p className="ds-field__hint">{t('bridge.noDataCreated')}</p>
    </CategoryBox>
  );
}

function HeaResults() {
  const { t, num } = useI18n();
  const r = useHea((s) => s.result);
  const origin = useHea((s) => s.resultOrigin);
  const status = useHea((s) => s.status);
  const samples = useHea((s) => s.bootstrap?.samples ?? []);
  const mode = useServiceMode('hea');
  if (!r) {
    return <div className="empty-state">{status === 'loading' ? <Spinner size={20} label={t('common.loading')} /> : mode === 'disabled' ? t('hea.disabled') : t('hea.empty')}</div>;
  }
  const demo = origin === 'demo';
  const cat = demo ? 'demo' : 'result';
  const catLabel = demo ? t('category.demo') : t('category.result');
  const stable = r.veredito.toUpperCase().startsWith('ESTÁVEL');
  return (
    <>
      {demo ? (
        <CategoryBox category="demo" className="demo-banner" role="note" data-testid="hea-demo-banner">
          <DemoSeal text={t('common.demo')} />
          <p>{t('hea.demoBanner')}</p>
        </CategoryBox>
      ) : null}
      <section className="status-band">
        <div className={`verdict-box ds-cat-box ds-cat-box--${cat}`}>
          <span className="ds-label">{t('hea.verdict')}</span>
          <p className={`verdict-text ${stable ? 'is-ok' : 'is-risk'}`} lang="pt-BR"><span aria-hidden="true">{stable ? '✓ ' : '⚠ '}</span>{r.veredito}</p>
        </div>
        <div className={`phase-box ds-cat-box ds-cat-box--${cat}`}>
          <span className="ds-label">{t('hea.properties')}</span>
          <strong lang="pt-BR">{r.fase}</strong>
          <span>{r.ductilidade && r.dureza ? t('hea.propertiesLine', { ductility: r.ductilidade.toLowerCase(), hardness: r.dureza.toLowerCase(), index: num(r.dureza_indice, 0) }) : t('hea.propertiesUnavailable')}</span>
        </div>
      </section>
      <section className="metrics-grid" aria-label={t('metrics.label')}>
        <MetricCard label="ΔS mix" value={num(r.dS, 2)} unit="J/mol·K" category={cat} categoryLabel={catLabel} />
        <MetricCard label="ΔH mix" value={num(r.dH, 2)} unit="kJ/mol" category={cat} categoryLabel={catLabel} />
        <MetricCard label="δ" value={num(r.delta, 2)} unit="%" category={cat} categoryLabel={catLabel} />
        <MetricCard label="Ω" value={num(r.omega, 2)} unit={t('hea.dimensionless')} category={cat} categoryLabel={catLabel} />
        <MetricCard label="VEC" value={num(r.VEC, 2)} unit={t('hea.electrons')} category={cat} categoryLabel={catLabel} />
        <MetricCard label={t('hea.tm')} value={num(r.Tm, 0)} unit="K" category={cat} categoryLabel={catLabel} />
      </section>
      <Unavailable r={r} />
      <BridgeCard r={r} />
      <Suspense fallback={<div className="empty-state"><Spinner size={20} label={t('common.loading')} /></div>}>
        <HeaCharts samples={samples} selected={r} />
      </Suspense>
      <div className="lower-grid">
        <ComparisonWithReference r={r} />
        <Panel title={t('hea.normalizedComposition')} aside={t('hea.atomicPct')} headingLevel={2}>
          <div className="composition-body">
            {Object.entries(r.comp_percent).sort((a, b) => b[1] - a[1]).map(([el, pct]) => (
              <div key={el} className="composition-row"><strong>{el}</strong><span className="bar-track" aria-hidden="true"><span className="bar-fill" style={{ width: `${Math.min(100, pct)}%` }} /></span><span>{num(pct, 1)}%</span></div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel title={t('interpretation.title')} aside={demo ? t('common.demo') : t('hea.engine')} headingLevel={2}>
        <div className="interpretation-body">
          {r.interpretacao.map((line, i) => <p key={i} lang="pt-BR">{line}</p>)}
          {r.fragilidade ? <p lang="pt-BR">{r.fragilidade}</p> : null}
        </div>
      </Panel>
    </>
  );
}

export default function HeaModule() {
  const { t } = useI18n();
  const r = useHea((s) => s.result);
  const bootstrap = useHea((s) => s.bootstrap);
  const status = useHea((s) => s.status);
  useEffect(() => {
    // primeira visita: carrega a primeira liga e analisa (como o v1.17 fazia com a liga de Cantor)
    const h = useHea.getState();
    if (bootstrap && !h.result && !h.editorText) {
      const first = Object.keys(bootstrap.alloys)[0];
      if (first) {
        const alloy = bootstrap.alloys[first];
        if (alloy) h.set({ selectedKey: first, name: alloy.nome, editorText: compositionToText(alloy.composicao) });
        if (!useTerminal.getState().entries.length) void dispatch({ type: 'hea.analyze' }, 'system');
      }
    }
  }, [bootstrap]);
  return (
    <Workbench
      lab={<HeaLab />}
      center={
        <div className="output-panel">
          <header className="topbar">
            <div>
              <h1 id="resultTitle">{r?.nome ?? t('hea.analysisTitle')}</h1>
              <p>{bootstrap ? t('hea.subtitle', { T: String(bootstrap.reference.T_padrao), P: String(bootstrap.reference.P_padrao) }) : t('common.loading')}</p>
            </div>
            <div className="topbar-actions">
              <Button variant="primary" data-testid="analyze-button" loading={status === 'loading'} onClick={() => void dispatch({ type: 'hea.analyze' }, 'form')}>{t('hea.analyzeAlloy')}</Button>
            </div>
          </header>
          <main className="result-scroll" id="main-content" data-testid="result-root" tabIndex={-1}>
            <HeaResults />
          </main>
        </div>
      }
    />
  );
}
