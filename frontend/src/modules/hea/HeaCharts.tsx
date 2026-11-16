/**
 * Gráficos do HEA (carregados sob demanda), SVG desenhado à mão, legível nos dois temas
 * (tokens --chart-*), com descrição textual e tabela de dados para leitores de tela.
 *
 *  G-A  −T·ΔS_mix × T (e ΔG_mix = ΔH_mix − T·ΔS_mix quando o motor tem ΔH_mix), de `curva_T`.
 *  G-B  δ × VEC, com os limiares vindos de `criterios` da resposta.
 *
 * Regras (R2-FE-01): os pontos são exatamente os valores recebidos — nada é recalculado aqui;
 * NENHUM limiar ou faixa científica está fixo neste arquivo (todos vêm da API, com fonte e marca
 * de verificação); grandeza indisponível aparece como indisponível COM A CAUSA da API, nunca como
 * curva demonstrativa. A zona "estável" fixa (δ < 6,6 %, −15 < ΔH < 5 kJ/mol) e sem fonte, que
 * existia aqui até a rodada R1, foi REMOVIDA.
 *
 * R2-FE-02 (decisão D-R2-2): com `demo`, os valores vêm de `heaDemo.ts` e são FICTÍCIOS. Então o
 * selo "Demonstrativo" acompanha cada figura e cada tabela de dados, de forma visível e
 * persistente — não só no aviso do topo da tela.
 */
import type { CriterionDef, HeaResult } from '../../services/api/contracts.ts';
import { useI18n } from '../../i18n/index.ts';
import { DemoSeal } from '../../design-system/primitives/Category.tsx';
import { natureLabel } from '../../i18n/nature.ts';
import { criteriaFor, criterionLabel, curveSeries, deltaVecPoints } from './display.ts';

const W = 560;
const H = 330;
const P = { l: 58, r: 18, t: 18, b: 48 };

/** Marcas "redondas" (1, 2, 5 × 10ⁿ) que cobrem [min, max]; o domínio do eixo passa a ser o das marcas. */
export function niceTicks(min: number, max: number, target = 5): number[] {
  const span = Math.max(max - min, 1e-9);
  const raw = span / target;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = ([1, 2, 2.5, 5, 10].find((m) => m * mag >= raw) ?? 10) * mag;
  const start = Math.floor(min / step) * step;
  const out: number[] = [];
  for (let v = start; v <= max + step * 1e-6; v += step) out.push(Number(v.toFixed(10)));
  if (out[out.length - 1]! < max) out.push(Number((out[out.length - 1]! + step).toFixed(10)));
  return out;
}

/** Afasta rótulos verticalmente para não se sobreporem (mínimo de `gap` px). */
export function spreadLabels(ys: number[], gap = 12): number[] {
  const order = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
  for (let k = 1; k < order.length; k += 1) if (order[k]!.y - order[k - 1]!.y < gap) order[k]!.y = order[k - 1]!.y + gap;
  const out = new Array<number>(ys.length);
  order.forEach((o) => { out[o.i] = o.y; });
  return out;
}

/** Selo de origem demonstrativa junto do próprio gráfico (nunca só no topo da tela). */
function ChartDemoSeal({ note }: { note: 'chart' | 'table' }) {
  const { t } = useI18n();
  return (
    <p className="chart__meta hea-demo-seal" data-testid={note === 'chart' ? 'chart-demo-seal' : 'chart-data-demo-seal'}>
      <DemoSeal text={t('common.demo')} detail={t('hea.demoSealDetail')} />{' '}
      {t(note === 'chart' ? 'hea.demoChartNote' : 'hea.demoTableNote')}
    </p>
  );
}

/** Gráfico que não pode ser desenhado: diz o quê falta e a CAUSA que a API informou. */
function ChartUnavailable({ title, cause, demo = false }: { title: string; cause?: string | null; demo?: boolean }) {
  const { t } = useI18n();
  return (
    <figure className={`chart ${demo ? 'ds-cat-box ds-cat-box--demo' : ''}`} data-testid="chart-unavailable">
      <figcaption>{title}</figcaption>
      {demo ? <ChartDemoSeal note="chart" /> : null}
      <p className="empty-state">{t('hea.chart.unavailable')}</p>
      {cause ? <p className="chart__meta" lang="pt-BR" data-testid="chart-cause">{t('hea.chart.unavailableCause', { cause })}</p> : null}
    </figure>
  );
}

/** Rodapé comum: natureza do resultado, condições e FONTE (sempre os da API). */
function ChartMeta({ r, nature, conditions }: { r: HeaResult; nature: string | undefined; conditions: string }) {
  const { t } = useI18n();
  const p = r.procedencia;
  const sources = p ? [...p.fontes_modelo, ...p.fontes_dados] : [];
  const engine = p ? t('hea.chart.engineSource', { motor: p.motor, version: p.versao_motor }) : null;
  return (
    <div className="chart__meta">
      <p><strong>{t('hea.chart.natureLabel')}:</strong> {natureLabel(t, nature)}</p>
      <p><strong>{t('hea.chart.conditionsLabel')}:</strong> {conditions}</p>
      <p lang="pt-BR"><strong>{t('hea.chart.sourceLabel')}:</strong> {[engine, ...sources].filter(Boolean).join(' · ') || '—'}</p>
    </div>
  );
}

/** Marca de limiar sem fonte conferida (decisão D-h: a faixa é exibida, sempre rotulada). */
function unverifiedMark(c: Pick<CriterionDef, 'verificada'>, label: string): string {
  return c.verificada ? label : `${label} *`;
}

// --------------------------------------------------------------------- G-A
export function TemperatureChart({ selected, demo = false }: { selected: HeaResult; demo?: boolean }) {
  const { t, num } = useI18n();
  const series = curveSeries(selected);
  if (!series.entropyTerm.length) return <ChartUnavailable title={t('hea.chart.ga.caption')} cause={t('hea.chart.ga.noCurve')} demo={demo} />;
  const ts = series.entropyTerm.map((p) => p.T);
  const values = [...series.entropyTerm.map((p) => p.value), ...series.gibbs.map((p) => p.value), 0];
  const xTicks = niceTicks(Math.min(...ts), Math.max(...ts), 6);
  const yTicks = niceTicks(Math.min(...values), Math.max(...values), 5);
  const xMin = xTicks[0]!;
  const xMax = xTicks[xTicks.length - 1]!;
  const yMin = yTicks[0]!;
  const yMax = yTicks[yTicks.length - 1]!;
  const x = (v: number) => P.l + ((v - xMin) / (xMax - xMin)) * (W - P.l - P.r);
  const y = (v: number) => H - P.b - ((v - yMin) / (yMax - yMin)) * (H - P.t - P.b);
  const path = (pts: Array<{ T: number; value: number }>) => pts.map((p, i) => `${i ? 'L' : 'M'}${x(p.T).toFixed(1)},${y(p.value).toFixed(1)}`).join(' ');
  const last = series.entropyTerm[series.entropyTerm.length - 1]!;
  const desc = t('hea.chart.ga.desc', { name: selected.nome, tmin: num(ts[0] ?? null, 0), tmax: num(last.T, 0), value: num(last.value, 2) });
  const step = Math.max(1, Math.ceil(series.entropyTerm.length / 12));
  return (
    <figure className={`chart ${demo ? 'ds-cat-box ds-cat-box--demo' : ''}`} data-testid="temperature-chart">
      {demo ? <ChartDemoSeal note="chart" /> : null}
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={desc} className="chart__svg">
        {xTicks.map((v) => <g key={`x${v}`}><line x1={x(v)} x2={x(v)} y1={P.t} y2={H - P.b} className="chart__grid" /><text x={x(v)} y={H - P.b + 18} className="chart__tick" textAnchor="middle">{num(v, 0)}</text></g>)}
        {yTicks.map((v) => <g key={`y${v}`}><line x1={P.l} x2={W - P.r} y1={y(v)} y2={y(v)} className="chart__grid" /><text x={P.l - 8} y={y(v) + 4} className="chart__tick" textAnchor="end">{num(v, 0)}</text></g>)}
        {yMin < 0 && yMax > 0 ? <line x1={P.l} x2={W - P.r} y1={y(0)} y2={y(0)} className="chart__zero" /> : null}
        <line x1={P.l} x2={P.l} y1={P.t} y2={H - P.b} className="chart__axis" />
        <line x1={P.l} x2={W - P.r} y1={H - P.b} y2={H - P.b} className="chart__axis" />
        <text x={(P.l + W - P.r) / 2} y={H - 8} className="chart__label" textAnchor="middle">{t('hea.chart.tAxis')}</text>
        <text transform={`translate(16 ${(P.t + H - P.b) / 2}) rotate(-90)`} className="chart__label" textAnchor="middle">{t('hea.chart.ga.yAxis')}</text>
        <path d={path(series.entropyTerm)} className="chart__line chart__line--sel" />
        {series.gibbs.length ? <path d={path(series.gibbs)} className="chart__line chart__line--s2" /> : null}
      </svg>
      <figcaption>{t('hea.chart.ga.caption')}</figcaption>
      <ul className="chart__legend">
        <li><span className="legend-swatch legend-swatch--sel" aria-hidden="true" /> {t('hea.chart.ga.seriesEntropy')}</li>
        {series.gibbs.length
          ? <li><span className="legend-swatch legend-swatch--s2" aria-hidden="true" /> {t('hea.chart.ga.seriesGibbs')}</li>
          : <li lang="pt-BR" data-testid="ga-gibbs-unavailable">{t('hea.chart.ga.gibbsUnavailable', { cause: series.gibbsUnavailable ?? t('hea.unavailable') })}</li>}
      </ul>
      <ChartMeta r={selected} nature={selected.classes?.['curva_T.menos_TdS']} conditions={t('hea.chart.ga.conditions')} />
      <details className="chart__data">
        <summary>{t('hea.chart.data')}</summary>
        {demo ? <ChartDemoSeal note="table" /> : null}
        <table className="ds-table">
          <thead><tr><th scope="col">{t('hea.chart.tAxis')}</th><th scope="col">{t('hea.chart.ga.seriesEntropy')}</th><th scope="col">{t('hea.chart.ga.seriesGibbs')}</th></tr></thead>
          <tbody>
            {series.entropyTerm.filter((_, i) => i % step === 0).map((p, i) => (
              <tr key={p.T}><th scope="row">{num(p.T, 0)}</th><td>{num(p.value, 3)}</td><td>{series.gibbs.length ? num(series.gibbs[i * step]?.value ?? null, 3) : t('hea.unavailable')}</td></tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

// --------------------------------------------------------------------- G-B
export function DeltaVecChart({ samples, selected, demo = false }: { samples: HeaResult[]; selected: HeaResult; demo?: boolean }) {
  const { t, num } = useI18n();
  const pts = deltaVecPoints(samples, selected);
  const cause = selected.indisponiveis?.['delta'] ?? selected.indisponiveis?.['VEC'] ?? null;
  if (!pts.length) return <ChartUnavailable title={t('hea.chart.gb.caption')} cause={cause ?? t('hea.chart.gb.empty')} demo={demo} />;
  const criteria = selected.criterios ?? [];
  const deltaLimits = criteriaFor(criteria, 'delta');
  const vecLimits = criteriaFor(criteria, 'VEC');
  const xTicks = niceTicks(0, Math.max(...pts.map((p) => p.delta), ...deltaLimits.map((c) => c.limiar)) * 1.15, 5);
  const yTicks = niceTicks(Math.min(...pts.map((p) => p.vec), ...vecLimits.map((c) => c.limiar)) - 1, Math.max(...pts.map((p) => p.vec), ...vecLimits.map((c) => c.limiar)) + 1, 5);
  const xMin = xTicks[0]!;
  const xMax = xTicks[xTicks.length - 1]!;
  const yMin = yTicks[0]!;
  const yMax = yTicks[yTicks.length - 1]!;
  const x = (v: number) => P.l + ((v - xMin) / (xMax - xMin)) * (W - P.l - P.r);
  const y = (v: number) => H - P.b - ((v - yMin) / (yMax - yMin)) * (H - P.t - P.b);
  const labelYs = spreadLabels(pts.map((p) => y(p.vec) - 8));
  const sel = pts.find((p) => p.selected);
  const desc = sel
    ? t('hea.chart.gb.desc', { name: sel.name, delta: num(sel.delta, 2), vec: num(sel.vec, 2) })
    : t('hea.chart.gb.caption');
  const fmt = (v: number) => num(v, 2);
  return (
    <figure className={`chart ${demo ? 'ds-cat-box ds-cat-box--demo' : ''}`} data-testid="delta-vec-chart">
      {demo ? <ChartDemoSeal note="chart" /> : null}
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={desc} className="chart__svg">
        {xTicks.map((v) => <g key={`x${v}`}><line x1={x(v)} x2={x(v)} y1={P.t} y2={H - P.b} className="chart__grid" /><text x={x(v)} y={H - P.b + 18} className="chart__tick" textAnchor="middle">{num(v, 1)}</text></g>)}
        {yTicks.map((v) => <g key={`y${v}`}><line x1={P.l} x2={W - P.r} y1={y(v)} y2={y(v)} className="chart__grid" /><text x={P.l - 8} y={y(v) + 4} className="chart__tick" textAnchor="end">{num(v, 1)}</text></g>)}
        {deltaLimits.map((c) => (
          <g key={`dl-${c.codigo}`}>
            <line x1={x(c.limiar)} x2={x(c.limiar)} y1={P.t} y2={H - P.b} className="chart__limit" />
            <text x={x(c.limiar) + 4} y={P.t + 12} className="chart__zone-label">{unverifiedMark(c, criterionLabel(c, fmt))}</text>
          </g>
        ))}
        {vecLimits.map((c) => (
          <g key={`vl-${c.codigo}`}>
            <line x1={P.l} x2={W - P.r} y1={y(c.limiar)} y2={y(c.limiar)} className="chart__limit" />
            <text x={W - P.r - 4} y={y(c.limiar) - 4} textAnchor="end" className="chart__zone-label">{unverifiedMark(c, criterionLabel(c, fmt))}</text>
          </g>
        ))}
        <line x1={P.l} x2={P.l} y1={P.t} y2={H - P.b} className="chart__axis" />
        <line x1={P.l} x2={W - P.r} y1={H - P.b} y2={H - P.b} className="chart__axis" />
        <text x={(P.l + W - P.r) / 2} y={H - 8} className="chart__label" textAnchor="middle">{t('hea.chart.gb.xAxis')}</text>
        <text transform={`translate(16 ${(P.t + H - P.b) / 2}) rotate(-90)`} className="chart__label" textAnchor="middle">{t('hea.chart.gb.yAxis')}</text>
        {pts.map((p, i) => (
          <g key={`${p.name}-${i}`}>
            {p.selected
              ? <rect x={x(p.delta) - 7} y={y(p.vec) - 7} width={14} height={14} className="chart__pt chart__pt--sel" transform={`rotate(45 ${x(p.delta)} ${y(p.vec)})`} />
              : <circle cx={x(p.delta)} cy={y(p.vec)} r={5} className={`chart__pt chart__pt--s${(i % 4) + 1}`} />}
            <text x={x(p.delta) + 10} y={labelYs[i] ?? y(p.vec) - 8} className={`chart__pt-label ${p.selected ? 'is-sel' : ''}`}>{p.name}</text>
          </g>
        ))}
      </svg>
      <figcaption>{t('hea.chart.gb.caption')}</figcaption>
      {deltaLimits.concat(vecLimits).some((c) => !c.verificada) ? <p className="chart__meta" data-testid="gb-unverified">{t('hea.chart.unverifiedNote')}</p> : null}
      <ChartMeta r={selected} nature={selected.classes?.['delta']} conditions={t('hea.chart.gb.conditions')} />
      <details className="chart__data">
        <summary>{t('hea.chart.data')}</summary>
        {demo ? <ChartDemoSeal note="table" /> : null}
        <table className="ds-table">
          <thead><tr><th scope="col">{t('hea.alloy')}</th><th scope="col">{t('hea.chart.gb.xAxis')}</th><th scope="col">{t('hea.chart.gb.yAxis')}</th></tr></thead>
          <tbody>{pts.map((p) => <tr key={p.name}><th scope="row">{p.name}</th><td>{num(p.delta, 2)}</td><td>{num(p.vec, 2)}</td></tr>)}</tbody>
        </table>
        <table className="ds-table">
          <caption>{t('hea.chart.limitsCaption')}</caption>
          <thead><tr><th scope="col">{t('hea.criteria.criterion')}</th><th scope="col">{t('hea.criteria.source')}</th></tr></thead>
          <tbody>{deltaLimits.concat(vecLimits).map((c) => (
            <tr key={c.codigo}><th scope="row">{criterionLabel(c, fmt)}</th><td lang="pt-BR">{c.fonte}{c.verificada ? '' : ` — ${t('hea.criteria.unverified')}`}</td></tr>
          ))}</tbody>
        </table>
      </details>
    </figure>
  );
}

export default function HeaCharts({ samples, selected, demo = false }: { samples: HeaResult[]; selected: HeaResult; demo?: boolean }) {
  return (
    <div className="visual-grid">
      <TemperatureChart selected={selected} demo={demo} />
      <DeltaVecChart samples={samples} selected={selected} demo={demo} />
    </div>
  );
}
