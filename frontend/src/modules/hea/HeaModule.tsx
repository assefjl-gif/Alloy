import { lazy, Suspense, useEffect } from 'react';
import { dispatch } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { MetricCard } from '../../design-system/layout/MetricCard.tsx';
import { Panel } from '../../design-system/layout/Panel.tsx';
import { Button } from '../../design-system/primitives/Button.tsx';
import { CategoryBox, CategoryTag, DemoSeal } from '../../design-system/primitives/Category.tsx';
import { Disclosure } from '../../design-system/primitives/Disclosure.tsx';
import { Badge, Spinner } from '../../design-system/primitives/misc.tsx';
import { Terminal } from '../../features/terminal/Terminal.tsx';
import { useServiceMode } from '../../stores/capabilities.ts';
import { useTerminal } from '../../stores/terminal.ts';
import { compositionToText, useHea } from './store.ts';
import { compositionRows, criterionLabel, criterionStatus, evaluatedCriteria, hasMassBasis, triageText, triageTone } from './display.ts';
import { natureLabel } from '../../i18n/nature.ts';
import { matchStructure } from './transfer.ts';
import type { HeaResult } from '../../services/api/contracts.ts';

const HeaCharts = lazy(() => import('./HeaCharts.tsx'));

/** Códigos de dado faltante com rótulo traduzido (R1 §1.2 `DadoFaltante.codigo`). */
const MISSING_CODES: readonly string[] = ['raio_atomico', 'temperatura_fusao', 'vec', 'massa_atomica', 'entalpia_mistura_par'];

/** Selo reutilizavel de valor demonstrativo (D-R2-2 (b)): acompanha o proprio dado. */
function DemoValueSeal({ testId }: { testId?: string }) {
  const { t } = useI18n();
  return <span className="hea-demo-seal" data-testid={testId}><DemoSeal text={t('common.demo')} detail={t('hea.demoSealDetail')} /></span>;
}

function HeaLab() {
  const { t } = useI18n();
  const bootstrap = useHea((s) => s.bootstrap);
  const origin = useHea((s) => s.origin);
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
      <Disclosure title={t('hea.blocks')} className="lab-disclosure lab-disclosure--blocks" aside={origin === 'demo' ? <DemoValueSeal testId="hea-blocks-demo-seal" /> : <span className="count-pill">{alloys.length}</span>}>
        {origin === 'demo' ? <p className="ds-field__hint" data-testid="hea-blocks-demo-note">{t('hea.demoAlloysNote')}</p> : null}
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

/**
 * Critérios empíricos avaliados PELO MOTOR (R1 §1.2 `criterios`): limiar, unidade, valor da liga,
 * situação e FONTE vêm da API. Substitui a antiga "comparação com a liga de referência", que
 * subtraía limiares do valor calculado como se fossem medidas da mesma natureza.
 */
function CriteriaTable({ r, demo }: { r: HeaResult; demo: boolean }) {
  const { t, num } = useI18n();
  const rows = evaluatedCriteria(r);
  const fmt = (v: number) => num(v, 2);
  return (
    <Panel title={t('hea.criteria.title')} aside={demo ? <DemoValueSeal testId="hea-criteria-demo-seal" /> : <CategoryTag category="reference" label={t('category.reference')} />} headingLevel={2} testId="hea-criteria">
      {demo ? <p className="table-note" data-testid="hea-criteria-demo-note">{t('hea.demoTableNote')}</p> : null}
      {rows.length ? (
        <>
          <div className="ds-table-wrap">
            <table className="ds-table">
              <thead><tr><th scope="col">{t('hea.criteria.criterion')}</th><th scope="col">{t('hea.criteria.value')}</th><th scope="col">{t('hea.criteria.status')}</th><th scope="col">{t('hea.criteria.source')}</th></tr></thead>
              <tbody>
                {rows.map((c) => {
                  const status = criterionStatus(c);
                  return (
                    <tr key={c.codigo}>
                      <th scope="row">
                        {criterionLabel(c, fmt)}
                        <br /><span className="ds-field__hint">{natureLabel(t, c.natureza)}</span>
                      </th>
                      <td>{c.valor === null ? t('hea.unavailable') : `${num(c.valor, 4)}${c.unidade === 'adimensional' ? '' : ` ${c.unidade}`}`}
                        {c.proximo_do_limiar ? <><br /><Badge tone="warning">{t('hea.criteria.near')}</Badge></> : null}
                      </td>
                      <td>
                        <Badge tone={status === 'atende' ? 'success' : status === 'nao_atende' ? 'danger' : 'neutral'}>{t(`hea.criteria.${status}`)}</Badge>
                        {c.motivo ? <><br /><span className="ds-field__hint" lang="pt-BR">{c.motivo}</span></> : null}
                      </td>
                      <td lang="pt-BR"><span className="ds-field__hint">{c.fonte}</span>
                        {c.verificada ? null : <><br /><Badge tone="warning">{t('hea.criteria.unverified')}</Badge></>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="table-note">{t('hea.criteria.note')}</p>
        </>
      ) : <p className="ds-muted">{t('hea.criteria.empty')}</p>}
    </Panel>
  );
}

/**
 * Composição nas DUAS bases, como o motor as devolveu: % atômica sempre, % em massa quando há
 * massa utilizável. Ausência de base mássica é dita como indisponível, nunca convertida no front.
 */
function CompositionPanel({ r, demo }: { r: HeaResult; demo: boolean }) {
  const { t, num } = useI18n();
  const rows = compositionRows(r);
  const mass = hasMassBasis(rows);
  const basis = r.base_entrada ? t(`hea.comp.basis.${r.base_entrada}`) : t('hea.comp.basis.atomica');
  return (
    <Panel title={t('hea.comp.title')} aside={demo ? <DemoValueSeal testId="hea-composition-demo-seal" /> : basis} headingLevel={2} testId="hea-composition">
      {demo ? <p className="table-note" data-testid="hea-composition-demo-note">{t('hea.demoTableNote')}</p> : <p className="ds-field__hint">{basis}</p>}
      <div className="ds-table-wrap">
        <table className="ds-table" data-testid="hea-composition-table">
          <thead><tr><th scope="col">{t('hea.comp.element')}</th><th scope="col">{t('hea.comp.atPct')}</th><th scope="col">{t('hea.comp.massPct')}</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.element}>
                <th scope="row">{row.element}</th>
                <td><span className="bar-track" aria-hidden="true"><span className="bar-fill" style={{ width: `${Math.min(100, row.atPct)}%` }} /></span> {num(row.atPct, 2)} %</td>
                <td>{row.massPct === null ? t('hea.unavailable') : `${num(row.massPct, 2)} %`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <dl className="guided__dl">
        <dt>{t('hea.comp.molarMass')}</dt>
        <dd>{r.massa_molar_media === null || r.massa_molar_media === undefined ? t('hea.unavailable') : `${num(r.massa_molar_media, 4)} g/mol`}</dd>
        <dt>{t('hea.comp.sumLabel')}</dt>
        <dd>{r.soma_informada === undefined ? t('hea.unavailable') : num(r.soma_informada, 4)}</dd>
      </dl>
      {!mass ? <p className="ds-field__hint" lang="pt-BR" data-testid="hea-mass-unavailable">{r.indisponiveis?.['comp_massa_pct'] ?? t('hea.comp.massUnavailable')}</p> : null}
    </Panel>
  );
}

/** Grandezas que o servidor não calculou, com o motivo (nunca substituídas por estimativas no front). */
function Unavailable({ r }: { r: HeaResult }) {
  const { t } = useI18n();
  const items = Object.entries(r.indisponiveis ?? {});
  const missing = r.dados_faltantes ?? [];
  const pairs = r.pares_faltantes ?? [];
  if (!items.length && !missing.length && !pairs.length) return null;
  const codeLabel = (code: string): string => (MISSING_CODES.includes(code) ? t(`hea.missing.code.${code}` as 'hea.missing.code.vec') : code);
  const situationLabel = (s: string): string => (s === 'ausente' || s === 'nao_validado' ? t(`hea.missing.situation.${s}`) : s);
  return (
    <CategoryBox category="feedback" as="section" aria-labelledby="hea-unavailable-title" data-testid="hea-unavailable">
      <h2 id="hea-unavailable-title">{t('hea.unavailableTitle')}</h2>
      <ul>{items.map(([k, motivo]) => <li key={k} lang="pt-BR"><strong>{k}</strong>: {motivo}</li>)}</ul>
      {missing.length ? (
        <>
          <h3>{t('hea.missing.title')}</h3>
          <ul data-testid="hea-missing-data">
            {missing.map((m) => <li key={`${m.simbolo}-${m.codigo}`}>{t('hea.missing.item', { symbol: m.simbolo, datum: codeLabel(m.codigo), situation: situationLabel(m.situacao) })}</li>)}
          </ul>
        </>
      ) : null}
      {pairs.length ? (
        <>
          <h3>{t('hea.missing.pairsTitle')}</h3>
          <p data-testid="hea-missing-pairs">{pairs.join(' · ')}</p>
        </>
      ) : null}
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

/** Avisos obrigatórios do motor (`bootstrap.avisos_fixos`, auditoria 2.7.1): texto da API. */
function FixedWarnings() {
  const { t } = useI18n();
  // o seletor devolve a referência do store (nunca um array novo): array novo a cada render
  // reentraria em laço de atualização no zustand
  const warnings = useHea((s) => s.bootstrap?.avisos_fixos);
  if (!warnings?.length) return null;
  return (
    <Disclosure title={t('hea.warnings.title')} defaultOpen={false}>
      <ul data-testid="hea-fixed-warnings">{warnings.map((w, i) => <li key={i} lang="pt-BR">{w}</li>)}</ul>
    </Disclosure>
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
  // D-R2-2 (b): o selo acompanha CADA valor demonstrativo, visivel e permanente.
  const seal = demo ? <DemoValueSeal /> : undefined;
  // O estado vem de `triagem.estado` (R1 §1.2). O motor 2.0.0 não emite mais a palavra "ESTÁVEL":
  // nenhum texto é usado como prova de estabilidade.
  const tone = triageTone(r);
  const mark = tone === 'favoravel' ? '✓ ' : tone === 'desfavoravel' ? '⚠ ' : '— ';
  const toneClass = tone === 'favoravel' ? 'is-ok' : tone === 'desfavoravel' ? 'is-risk' : '';
  return (
    <>
      {demo ? (
        <CategoryBox category="demo" className="demo-banner" role="note" data-testid="hea-demo-banner">
          <DemoSeal text={t('common.demo')} />
          <p>{t('hea.demoBanner')}</p>
        </CategoryBox>
      ) : null}
      <section className="status-band">
        <div className={`verdict-box ds-cat-box ds-cat-box--${cat}`} data-testid="hea-triage">
          <span className="ds-label">{t('hea.triage.title')}</span>
          <Badge tone={tone === 'favoravel' ? 'success' : tone === 'desfavoravel' ? 'danger' : 'neutral'}>{t(`hea.triage.state.${tone}`)}</Badge>
          {demo ? <DemoValueSeal testId="hea-triage-demo-seal" /> : null}
          <p className={`verdict-text ${toneClass}`} lang="pt-BR"><span aria-hidden="true">{mark}</span>{triageText(r)}</p>
          <p className="ds-field__hint">{demo ? t('hea.demoTriageNote') : t('hea.triage.note')}</p>
        </div>
        <div className={`phase-box ds-cat-box ds-cat-box--${cat}`}>
          <span className="ds-label">{t('hea.properties')}</span>
          {demo ? <DemoValueSeal testId="hea-phase-demo-seal" /> : null}
          <strong lang="pt-BR">{r.fase}</strong>
          <span>{r.ductilidade && r.dureza ? t('hea.propertiesLine', { ductility: r.ductilidade.toLowerCase(), hardness: r.dureza.toLowerCase(), index: num(r.dureza_indice, 0) }) : t('hea.propertiesUnavailable')}</span>
          {r.vec_aplicavel === false ? <span className="ds-field__hint" data-testid="hea-vec-domain">{t('hea.vecNotApplicable')}</span> : null}
        </div>
      </section>
      <section className="metrics-grid" aria-label={t('metrics.label')}>
        <MetricCard label="ΔS mix" value={num(r.dS, 2)} unit="J/mol·K" category={cat} categoryLabel={catLabel} hint={seal} />
        <MetricCard label="ΔS/R" value={num(r.dS_R ?? null, 4)} unit={r.classe_entropia ? t(`hea.entropyClass.${r.classe_entropia}` as 'hea.entropyClass.alta') : t('hea.dimensionless')} category={cat} categoryLabel={catLabel} hint={seal} testId="hea-ds-r" />
        <MetricCard label="ΔH mix" value={num(r.dH, 2)} unit="kJ/mol" category={cat} categoryLabel={catLabel} hint={seal} />
        <MetricCard label="δ" value={num(r.delta, 2)} unit="%" category={cat} categoryLabel={catLabel} hint={seal} />
        <MetricCard label="Ω" value={num(r.omega, 2)} unit={t('hea.dimensionless')} category={cat} categoryLabel={catLabel} hint={seal} />
        <MetricCard label="VEC" value={num(r.VEC, 2)} unit={t('hea.electrons')} category={cat} categoryLabel={catLabel} hint={seal} />
        <MetricCard label={t('hea.tm')} value={num(r.Tm, 0)} unit="K" category={cat} categoryLabel={catLabel} hint={seal} />
        <MetricCard label={t('hea.meanRadius')} value={num(r.raio_medio_nm ?? null, 4)} unit="nm" category={cat} categoryLabel={catLabel} hint={seal} />
      </section>
      <Unavailable r={r} />
      <BridgeCard r={r} />
      <Suspense fallback={<div className="empty-state"><Spinner size={20} label={t('common.loading')} /></div>}>
        <HeaCharts samples={samples} selected={r} demo={demo} />
      </Suspense>
      <div className="lower-grid">
        <CriteriaTable r={r} demo={demo} />
        <CompositionPanel r={r} demo={demo} />
      </div>
      <Panel title={t('interpretation.title')} aside={demo ? <DemoValueSeal testId="hea-interpretation-demo-seal" /> : t('hea.engine')} headingLevel={2}>
        <div className="interpretation-body">
          {r.interpretacao.map((line, i) => <p key={i} lang="pt-BR">{line}</p>)}
          {r.fragilidade ? <p lang="pt-BR">{r.fragilidade}</p> : null}
        </div>
        <FixedWarnings />
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
          <header className="topbar ds-on-dark">
            <div>
              <h1 id="resultTitle">{r?.nome ?? t('hea.analysisTitle')}</h1>
              <p>{bootstrap ? t('hea.subtitle', { version: bootstrap.versao_motor ?? '—' }) : t('common.loading')}</p>
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
