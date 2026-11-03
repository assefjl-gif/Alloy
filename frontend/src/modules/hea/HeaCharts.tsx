/**
 * Gráficos do HEA (carregados sob demanda — tarefa 2.16). SVG desenhado à mão, legível nos dois
 * temas (tokens --chart-*), com descrição textual e tabela de dados para leitores de tela.
 * Os pontos são exatamente os valores recebidos (δ, ΔH, curva G×T) — nada é recalculado.
 * Limites do mapa (δ < 6,6 %; −15 < ΔH < 5 kJ/mol) são os mesmos do HEA Virtual Lab v1.17.
 */
import type { HeaResult } from '../../services/api/contracts.ts';
import { useI18n } from '../../i18n/index.ts';

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

export function StabilityMap({ samples, selected }: { samples: HeaResult[]; selected: HeaResult }) {
  const { t, num } = useI18n();
  const pts = [...samples.filter((s) => s.nome !== selected.nome), selected];
  const xTicks = niceTicks(0, Math.max(8, ...pts.map((p) => p.delta + 1)), 5);
  const yTicks = niceTicks(Math.min(-20, ...pts.map((p) => p.dH - 4)), Math.max(10, ...pts.map((p) => p.dH + 4)), 6);
  const xMax = xTicks[xTicks.length - 1]!;
  const yMin = yTicks[0]!;
  const yMax = yTicks[yTicks.length - 1]!;
  const x = (v: number) => P.l + (v / xMax) * (W - P.l - P.r);
  const y = (v: number) => H - P.b - ((v - yMin) / (yMax - yMin)) * (H - P.t - P.b);
  const labelYs = spreadLabels(pts.map((p) => y(p.dH) - 8));
  const desc = t('hea.chart.stabilityDesc', { name: selected.nome, delta: num(selected.delta, 2), dh: num(selected.dH, 2) });
  return (
    <figure className="chart" data-testid="stability-chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={desc} className="chart__svg">
        <rect x={P.l} y={y(5)} width={x(6.6) - P.l} height={y(-15) - y(5)} className="chart__zone" />
        {xTicks.map((v) => <g key={`x${v}`}><line x1={x(v)} x2={x(v)} y1={P.t} y2={H - P.b} className="chart__grid" /><text x={x(v)} y={H - P.b + 18} className="chart__tick" textAnchor="middle">{num(v, 1)}</text></g>)}
        {yTicks.map((v) => <g key={`y${v}`}><line x1={P.l} x2={W - P.r} y1={y(v)} y2={y(v)} className="chart__grid" /><text x={P.l - 8} y={y(v) + 4} className="chart__tick" textAnchor="end">{num(v, 0)}</text></g>)}
        <line x1={x(6.6)} x2={x(6.6)} y1={P.t} y2={H - P.b} className="chart__limit" />
        <line x1={P.l} x2={P.l} y1={P.t} y2={H - P.b} className="chart__axis" />
        <line x1={P.l} x2={W - P.r} y1={H - P.b} y2={H - P.b} className="chart__axis" />
        <text x={(P.l + W - P.r) / 2} y={H - 8} className="chart__label" textAnchor="middle">{t('hea.chart.deltaAxis')}</text>
        <text transform={`translate(16 ${(P.t + H - P.b) / 2}) rotate(-90)`} className="chart__label" textAnchor="middle">{t('hea.chart.dhAxis')}</text>
        <text x={P.l + 8} y={y(4) + 16} className="chart__zone-label">{t('hea.chart.stableZone')}</text>
        {pts.map((p, i) => {
          const sel = p === selected;
          const ly = labelYs[i] ?? y(p.dH) - 8;
          return (
            <g key={p.nome + i}>
              {sel ? <rect x={x(p.delta) - 7} y={y(p.dH) - 7} width={14} height={14} className="chart__pt chart__pt--sel" transform={`rotate(45 ${x(p.delta)} ${y(p.dH)})`} /> : <circle cx={x(p.delta)} cy={y(p.dH)} r={5} className={`chart__pt chart__pt--s${(i % 4) + 1}`} />}
              <text x={x(p.delta) + 10} y={ly} className={`chart__pt-label ${sel ? 'is-sel' : ''}`}>{p.nome}</text>
            </g>
          );
        })}
      </svg>
      <figcaption>{t('hea.chart.stabilityCaption')}</figcaption>
      <details className="chart__data">
        <summary>{t('hea.chart.data')}</summary>
        <table className="ds-table"><thead><tr><th scope="col">{t('hea.alloy')}</th><th scope="col">δ (%)</th><th scope="col">ΔH (kJ/mol)</th></tr></thead>
          <tbody>{pts.map((p) => <tr key={p.nome}><th scope="row">{p.nome}</th><td>{num(p.delta, 2)}</td><td>{num(p.dH, 2)}</td></tr>)}</tbody></table>
      </details>
    </figure>
  );
}

export function GibbsChart({ samples, selected }: { samples: HeaResult[]; selected: HeaResult }) {
  const { t, num } = useI18n();
  const series = [...samples.filter((s) => s.nome !== selected.nome).slice(0, 3), selected];
  const all = series.flatMap((s) => s.gibbs.map((g) => g.G));
  const yTicks = niceTicks(Math.min(...all, -10000) / 1000, Math.max(...all, 0) / 1000, 5).map((v) => v * 1000);
  const yMin = yTicks[0]!;
  const yMax = yTicks[yTicks.length - 1]!;
  const xTicks = niceTicks(Math.min(...series.flatMap((s) => s.gibbs.map((g) => g.T)), 300), Math.max(...series.flatMap((s) => s.gibbs.map((g) => g.T)), 1000), 6);
  const xMin = xTicks[0]!;
  const xMax = xTicks[xTicks.length - 1]!;
  const x = (v: number) => P.l + ((v - xMin) / (xMax - xMin)) * (W - P.l - P.r);
  const y = (v: number) => H - P.b - ((v - yMin) / (yMax - yMin)) * (H - P.t - P.b);
  const path = (s: HeaResult) => s.gibbs.map((g, i) => `${i ? 'L' : 'M'}${x(g.T).toFixed(1)},${y(g.G).toFixed(1)}`).join(' ');
  const last = selected.gibbs[selected.gibbs.length - 1];
  const endLabelYs = spreadLabels(series.map((s) => { const e = s.gibbs[s.gibbs.length - 1]; return e ? y(e.G) - 5 : 0; }));
  return (
    <figure className="chart" data-testid="gibbs-chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={t('hea.chart.gibbsDesc', { name: selected.nome, g: last ? num(last.G / 1000, 1) : '—', T: last ? num(last.T, 0) : '—' })} className="chart__svg">
        {xTicks.map((v) => <g key={`x${v}`}><line x1={x(v)} x2={x(v)} y1={P.t} y2={H - P.b} className="chart__grid" /><text x={x(v)} y={H - P.b + 18} className="chart__tick" textAnchor="middle">{num(v, 0)}</text></g>)}
        {yTicks.map((v) => <g key={`y${v}`}><line x1={P.l} x2={W - P.r} y1={y(v)} y2={y(v)} className="chart__grid" /><text x={P.l - 8} y={y(v) + 4} className="chart__tick" textAnchor="end">{num(v / 1000, 0)}</text></g>)}
        <line x1={P.l} x2={W - P.r} y1={y(0)} y2={y(0)} className="chart__zero" />
        <line x1={P.l} x2={P.l} y1={P.t} y2={H - P.b} className="chart__axis" />
        <line x1={P.l} x2={W - P.r} y1={H - P.b} y2={H - P.b} className="chart__axis" />
        <text x={(P.l + W - P.r) / 2} y={H - 8} className="chart__label" textAnchor="middle">{t('hea.chart.tAxis')}</text>
        <text transform={`translate(16 ${(P.t + H - P.b) / 2}) rotate(-90)`} className="chart__label" textAnchor="middle">{t('hea.chart.gAxis')}</text>
        {series.map((s, i) => {
          const sel = s === selected;
          const end = s.gibbs[s.gibbs.length - 1];
          const ly = endLabelYs[i] ?? 0;
          return (
            <g key={s.nome + i}>
              <path d={path(s)} className={`chart__line ${sel ? 'chart__line--sel' : `chart__line--s${(i % 4) + 1}`}`} />
              {end ? <text x={W - P.r - 4} y={ly} textAnchor="end" className={`chart__pt-label ${sel ? 'is-sel' : ''}`}>{s.nome}</text> : null}
            </g>
          );
        })}
      </svg>
      <figcaption>{t('hea.chart.gibbsCaption')}</figcaption>
      <details className="chart__data">
        <summary>{t('hea.chart.data')}</summary>
        <table className="ds-table"><thead><tr><th scope="col">T (K)</th>{series.map((s) => <th key={s.nome} scope="col">{s.nome} — ΔG (J/mol)</th>)}</tr></thead>
          <tbody>{(selected.gibbs).filter((_, i) => i % 3 === 0).map((g, gi) => <tr key={g.T}><th scope="row">{num(g.T, 0)}</th>{series.map((s) => <td key={s.nome}>{num(s.gibbs[gi * 3]?.G ?? null, 0)}</td>)}</tr>)}</tbody></table>
      </details>
    </figure>
  );
}

export default function HeaCharts({ samples, selected }: { samples: HeaResult[]; selected: HeaResult }) {
  return (
    <div className="visual-grid">
      <StabilityMap samples={samples} selected={selected} />
      <GibbsChart samples={samples} selected={selected} />
    </div>
  );
}
