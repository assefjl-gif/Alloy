import { dispatch } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { MetricCard } from '../../design-system/layout/MetricCard.tsx';
import { Panel } from '../../design-system/layout/Panel.tsx';
import { CategoryTag } from '../../design-system/primitives/Category.tsx';
import { Button } from '../../design-system/primitives/Button.tsx';
import { Formula } from '../../features/formula/Formula.tsx';
import type { StructureResult } from '../../services/api/contracts.ts';

/** Texto vindo do motor (sempre em pt-BR): marcado com lang para leitores de tela. */
export function EngineText({ children }: { children: string }) {
  return <span lang="pt-BR">{children}</span>;
}

export function EngineLanguageNote() {
  const { t, locale } = useI18n();
  if (locale === 'pt-BR') return null;
  return <p className="engine-lang-note">{t('results.engineLanguage')}</p>;
}

export function StatusBand({ r }: { r: StructureResult }) {
  const { t, num } = useI18n();
  return (
    <section className="status-band" aria-label={t('results.statusLabel')}>
      <div className="verdict-box ds-cat-box ds-cat-box--result">
        <span className="ds-label">{t('results.crystalStructure')}</span>
        <p className="verdict-text" id="structureVerdict"><EngineText>{`${r.estrutura_nome} (${r.estrutura})`}</EngineText></p>
        <p className="verdict-sub">{t('results.touchAlong')} <EngineText>{r.contato}</EngineText> · {r.relacao_a}</p>
      </div>
      <div className="phase-box ds-cat-box ds-cat-box--result">
        <span className="ds-label">{t('results.geometry')}</span>
        <strong>{`NC = ${r.nc} · n = ${r.n} ${t('results.atomsPerCell')}`}</strong>
        <span>{r.estrutura === 'HC' ? t('results.caIdeal', { ca: num(r.c_a, 3) }) : t('results.voids', { pct: num(r.vazios * 100, 1) })}</span>
      </div>
    </section>
  );
}

export function MetricsGrid({ r }: { r: StructureResult }) {
  const { t, num } = useI18n();
  const resultLabel = t('category.result');
  const lattice = r.a_nm !== null
    ? <MetricCard testId="metric-a" label={t('metrics.latticeA')} value={num(r.a_nm, 4)} unit={r.c_nm !== null ? `nm · c = ${num(r.c_nm, 4)} nm` : 'nm'} category="result" categoryLabel={resultLabel} />
    : <MetricCard testId="metric-a" label={t('metrics.latticeA')} value={`${num(r.a_em_R, 3)} R`} unit={r.relacao_a} category="result" categoryLabel={resultLabel} />;
  return (
    <section className="metrics-grid" aria-label={t('metrics.label')} id="metricsGrid">
      <MetricCard testId="metric-structure" label={t('metrics.structure')} value={r.estrutura} unit={<EngineText>{r.estrutura_nome}</EngineText>} category="result" categoryLabel={resultLabel} />
      {lattice}
      <MetricCard testId="metric-fea" label={t('metrics.apf')} value={num(r.fea, 3)} unit={t('metrics.voidsUnit', { pct: num(r.vazios * 100, 1) })} category="result" categoryLabel={resultLabel} />
      <MetricCard
        testId="metric-density"
        label={t('metrics.density')}
        value={r.densidade !== null ? num(r.densidade, 3) : t('common.na')}
        unit={<>g/cm³{r.densidade_exp !== null ? <> · <span className="ref-inline"><CategoryTag category="reference" label={t('category.reference')} compact /> {t('metrics.exp', { value: num(r.densidade_exp, 2) })}</span></> : null}</>}
        category="result"
        categoryLabel={resultLabel}
      />
      <MetricCard testId="metric-nc" label={t('metrics.coordination')} value={r.nc} unit={t('metrics.neighbors')} category="result" categoryLabel={resultLabel} />
      <MetricCard testId="metric-n" label={t('metrics.atomsPerCell')} value={r.n} unit={t('metrics.effective')} category="result" categoryLabel={resultLabel} />
    </section>
  );
}

export function ComparisonTable({ r }: { r: StructureResult }) {
  const { t, num } = useI18n();
  const rows = useCrystalab((s) => s.structures) ?? [];
  const hcNote = r.estrutura === 'HC' && r.c_a !== null && Math.abs(r.c_a - 1.633) > 0.002;
  return (
    <Panel title={t('comparison.title')} aside={t('comparison.aside')} id="comparison" headingLevel={2}>
      <div className="ds-table-wrap" id="comparisonTable">
        <table className="ds-table">
          <caption className="sr-only">{t('comparison.caption')}</caption>
          <thead>
            <tr><th scope="col">{t('comparison.structure')}</th><th scope="col">n</th><th scope="col">NC</th><th scope="col">{t('comparison.relation')}</th><th scope="col">{t('metrics.apf')}</th></tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.sigla} className={s.sigla === r.estrutura ? 'is-current' : ''} aria-current={s.sigla === r.estrutura ? 'true' : undefined}>
                <th scope="row"><EngineText>{`${s.sigla} · ${s.nome}`}</EngineText>{s.sigla === r.estrutura ? <span className="sr-only"> ({t('comparison.current')})</span> : null}</th>
                <td>{s.n}</td><td>{s.nc}</td><td>{s.relacao}</td><td>{num(s.fea, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hcNote ? <p className="table-note">{t('comparison.hcNote', { ca: num(r.c_a, 3), fea: num(r.fea, 4) })}</p> : null}
    </Panel>
  );
}

export function AtomCount({ r }: { r: StructureResult }) {
  const { t, compact } = useI18n();
  return (
    <Panel title={t('count.title')} aside={t('count.aside')} id="atom-count" headingLevel={2}>
      <div className="composition-body" id="countBody">
        {r.contagem.map((g) => (
          <div key={g.tipo} className="count-row">
            <strong><EngineText>{g.rotulo}</EngineText></strong>
            <span className="bar-track" aria-hidden="true"><span className="bar-fill" style={{ width: `${Math.min(100, (g.contribuicao / r.n) * 100)}%` }} /></span>
            <span>{`${g.quantidade} × ${g.fracao_txt} = ${compact(g.contribuicao)}`}</span>
          </div>
        ))}
        <div className="count-row count-total">
          <strong>{t('count.total')}</strong>
          <span />
          <span>{t('count.atoms', { n: r.n })}</span>
        </div>
      </div>
    </Panel>
  );
}

/** Referência bibliográfica abreviada para cada parágrafo de interpretação (convenção do registro de referências §6). */
function referenceFor(line: string, structure: string): string {
  if (/Densidade teórica|densidade não pode/i.test(line)) return 'CAL9 §3.5, p. 54';
  if (/empilham|ABAB|ABCABC/.test(line)) return 'CAL9 §3.12, p. 75';
  if (/Miller-Bravais/.test(line)) return 'CAL9 §3.8–3.10, p. 58–74';
  if (/c\/a usado/.test(line)) return 'CAL9 §3.4, p. 48–54';
  if (structure === 'CS' && /Po-α|rara/.test(line)) return 'CAL9 §3.4, p. 51';
  return 'CAL9 §3.4, p. 48';
}

export function Interpretation({ r }: { r: StructureResult }) {
  const { t } = useI18n();
  return (
    <Panel title={t('interpretation.title')} aside={r.estrutura} id="interpretation" headingLevel={2}>
      <div className="interpretation-body" id="interpretationBody">
        {r.interpretacao.map((line, i) => (
          <div key={i} className="interp-line">
            <p><EngineText>{line}</EngineText></p>
            <cite className="interp-ref">{referenceFor(line, r.estrutura)}</cite>
          </div>
        ))}
        {(r.avisos ?? []).map((a, i) => <p key={`w${i}`} className="interp-warn" role="note"><EngineText>{a}</EngineText></p>)}
        <EngineLanguageNote />
      </div>
    </Panel>
  );
}

/** Fórmula simbólica de cada passo (conteúdo estático; os números vêm do motor). */
function symbolicFor(step: { titulo: string }, r: StructureResult): string | null {
  const title = step.titulo.toLowerCase();
  if (title.includes('parâmetro de rede')) {
    const rel = { CS: 'a = 2R', CCC: 'a = \\dfrac{4R}{\\sqrt{3}}', CFC: 'a = 2R\\sqrt{2}', HC: 'a = 2R,\\quad c = \\left(\\tfrac{c}{a}\\right) a' }[r.estrutura];
    return rel;
  }
  if (title.includes('volume')) return r.estrutura === 'HC' ? 'V_C = \\dfrac{3\\sqrt{3}}{2}\\,a^{2}c' : 'V_C = a^{3}';
  if (title.includes('densidade teórica')) return '\\rho = \\dfrac{n\\,A}{V_C\\,N_A}';
  if (title.includes('comparação')) return '\\text{desvio} = \\left(\\dfrac{\\rho}{\\rho_{\\text{exp}}} - 1\\right)\\times 100\\,\\%';
  if (title.includes('insuficientes')) return '\\rho = \\dfrac{n\\,A}{V_C\\,N_A}';
  return null;
}

export function DensityPanel({ r }: { r: StructureResult }) {
  const { t, num } = useI18n();
  return (
    <section className="ds-panel density-panel" id="density-panel" aria-labelledby="density-title" data-testid="density-panel">
      <header className="ds-panel__title">
        <h2 id="density-title">{t('density.title')}</h2>
        <Button size="sm" variant="ghost" onClick={() => useCrystalab.getState().set({ densityVisible: false })}>{t('common.hide')}</Button>
      </header>
      <div className="density-legend ds-cat-box ds-cat-box--reference">
        <strong>{t('density.variables')}</strong>
        <ul>
          <li><Formula tex="n" />: {t('density.var.n')}</li>
          <li><Formula tex="A" />: {t('density.var.A')} (g/mol)</li>
          <li><Formula tex="V_C" />: {t('density.var.Vc')} (cm³)</li>
          <li><Formula tex="N_A" />: {t('density.var.NA')} (6,022 × 10²³ {t('density.atomsPerMol')})</li>
          <li><Formula tex="R" />, <Formula tex="a" />: {t('density.var.Ra')} (nm; 1 nm = 10⁻⁷ cm)</li>
        </ul>
      </div>
      <ol className="ds-steps density-steps" id="densitySteps" aria-label={t('density.stepsLabel')}>
        {r.passos_densidade.map((step, i) => {
          const tex = symbolicFor(step, r);
          return (
            <li key={i} className="ds-step ds-step--done density-step">
              <span className="ds-step__index" aria-hidden="true">{i + 1}</span>
              <div className="ds-step__content">
                <strong className="ds-step__title"><EngineText>{step.titulo}</EngineText></strong>
                {tex ? (
                  <div className="density-step__row"><span className="ds-label">{t('density.formula')}</span><Formula tex={tex} display label={step.titulo} /></div>
                ) : null}
                <div className="density-step__row">
                  <span className="ds-label">{t(i === 0 ? 'density.data' : 'density.substitution')}</span>
                  <pre className="ds-pre"><EngineText>{step.formula}</EngineText></pre>
                </div>
                {step.detalhe ? <p className="density-step__detail"><EngineText>{step.detalhe}</EngineText></p> : null}
              </div>
            </li>
          );
        })}
      </ol>
      {r.densidade !== null ? (
        <div className="density-result ds-cat-box ds-cat-box--result" role="status">
          <span className="ds-label">{t('density.result')}</span>
          <strong>ρ = {num(r.densidade, 3)} g/cm³</strong>
          {r.densidade_exp !== null && r.erro_percent !== null ? <span>{t('density.vsExp', { exp: num(r.densidade_exp, 2), err: `${r.erro_percent >= 0 ? '+' : ''}${num(r.erro_percent, 2)}` })}</span> : null}
        </div>
      ) : null}
      <p className="density-note">{t('density.noInvention')}</p>
      <EngineLanguageNote />
    </section>
  );
}

export function DensityButton() {
  const { t } = useI18n();
  return <Button icon="calc" onClick={() => void dispatch({ type: 'density.show' }, 'form')}>{t('density.show')}</Button>;
}
