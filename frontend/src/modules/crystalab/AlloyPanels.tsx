/**
 * Ligas e temperatura no CrystaLab (T-13, sugestões Miná 2, 3 e 6).
 * Formulários na barra lateral; resultados completos abaixo do viewer. Nenhuma fórmula aqui:
 * rede, densidade, regras de solubilidade, dilatação e vibração vêm da API (motor), e o viewer só desenha.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { useI18n } from '../../i18n/index.ts';
import { crystalabApi } from '../../services/api/crystalab.ts';
import { ApiError } from '../../services/api/http.ts';
import type { AlloyRequest, AlloyResult, ThermalResult } from '../../services/api/contracts.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { usePreferences, prefersReducedMotion } from '../../stores/preferences.ts';
import { alloyLegend } from '../../features/viewer3d/alloyScene.ts';
import { absentSolutes, drawnAtomCount, representedAtomsOf, uniqueAtomCount } from './alloyDisplay.ts';
import { AlloyChecksBox, AlloyCompositionPanel, AlloyConventions, AlloyModelBox, AlloyPhasesPanel, AlloyPureElementsPanel, AlloyRealizationBox, AlloyRulesPerSolute, AlloySitesPanel } from './AlloyDetails.tsx';
import { parseUserNumber } from '../../utils/format.ts';
import { Button, ToggleButton } from '../../design-system/primitives/Button.tsx';
import { Checkbox, Segmented, Select, Slider, TextInput } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, CategoryTag } from '../../design-system/primitives/Category.tsx';
import { Disclosure } from '../../design-system/primitives/Disclosure.tsx';
import { Badge, Spinner } from '../../design-system/primitives/misc.tsx';
import { MetricCard } from '../../design-system/layout/MetricCard.tsx';
import { Panel } from '../../design-system/layout/Panel.tsx';

const INTERSTITIALS = ['C', 'N', 'H'] as const;
/** Tamanhos de supercélula que o motor aceita (1 a 4 por aresta); a sugestão da T-21 usa a mesma lista. */
const SIZES = [1, 2, 3, 4] as const;
const message = (err: unknown): string => (err instanceof Error ? err.message : String(err));
const isAbort = (err: unknown): boolean => err instanceof ApiError && err.kind === 'aborted';

/** Cada pedido novo cancela o anterior: só a resposta mais recente atualiza a tela. */
function useLatest() {
  const ref = useRef<AbortController | null>(null);
  useEffect(() => () => ref.current?.abort(), []);
  return () => {
    ref.current?.abort();
    ref.current = new AbortController();
    return ref.current.signal;
  };
}

// ------------------------------------------------------------------------------ Liga
export function AlloyForm() {
  const { t } = useI18n();
  const metals = useCrystalab((s) => s.metals);
  const alloy = useAlloy((s) => s.alloy);
  const status = useAlloy((s) => s.alloyStatus);
  const error = useAlloy((s) => s.alloyError);
  const symbols = useMemo(() => Object.keys(metals ?? {}), [metals]);
  const [base, setBase] = useState('Cu');
  const [solute, setSolute] = useState('Ni');
  const [percent, setPercent] = useState('30');
  const [size, setSize] = useState('2');
  const [arrangement, setArrangement] = useState<'aleatorio' | 'ordenado'>('aleatorio');
  const [seed, setSeed] = useState('1');
  const [distort, setDistort] = useState(false);
  const next = useLatest();
  const loaded = useCrystalab((s) => s.structure?.simbolo ?? null);
  // a liga parte do metal que está na tela
  useEffect(() => {
    if (loaded && symbols.includes(loaded)) {
      setBase(loaded);
      setSolute((cur) => (cur === loaded ? (loaded === 'Ni' ? 'Cu' : 'Ni') : cur));
    }
  }, [loaded, symbols]);
  const interstitial = (INTERSTITIALS as readonly string[]).includes(solute);

  if (!metals) return <p className="ds-muted" data-testid="alloy-form">{t('alloy.noCatalog')}</p>;

  /** `nOverride` vem do aviso da T-21: refaz a liga com o tamanho que o MOTOR indicou. */
  async function form(nOverride?: number) {
    const x = parseUserNumber(percent);
    const s = useAlloy.getState();
    if (x === null || Number.isNaN(x)) { s.set({ alloyError: t('edu.invalidNumber') }); return; }
    const req: AlloyRequest = { base, soluto: solute, x, n: nOverride ?? Number(size), arranjo: arrangement, distorcer: distort, semente: Math.max(0, Math.floor(parseUserNumber(seed) ?? 1)) };
    const signal = next();
    s.set({ alloyStatus: 'loading', alloyError: null });
    try {
      const result = await crystalabApi.alloy(req, signal);
      // um cálculo térmico da liga anterior deixa de valer
      const keepThermal = useAlloy.getState().thermalTarget !== 'alloy';
      useAlloy.getState().set({ alloy: result, alloyRequest: req, alloyStatus: 'idle', ...(keepThermal ? {} : { thermal: null, thermalTarget: null, vibration: { ...useAlloy.getState().vibration, on: false } }) });
    } catch (err) {
      if (isAbort(err)) return;
      useAlloy.getState().set({ alloyStatus: 'error', alloyError: message(err) });
    }
  }

  const legend = alloy ? alloyLegend(alloy) : [];
  return (
    <div className="alloy-form" data-testid="alloy-form">
      <p className="ds-field__hint">{t('alloy.lead')}</p>
      <form className="ds-stack" onSubmit={(e) => { e.preventDefault(); void form(); }}>
        <Select label={t('alloy.base')} value={base} onChange={(e) => setBase(e.target.value)} options={symbols.map((k) => ({ value: k, label: `${k} · ${metals[k]?.nome ?? k}` }))} data-testid="alloy-base" />
        <Select label={t('alloy.solute')} value={solute} onChange={(e) => setSolute(e.target.value)} data-testid="alloy-solute"
          options={[
            ...symbols.filter((k) => k !== base).map((k) => ({ value: k, label: `${k} · ${metals[k]?.nome ?? k} — ${t('alloy.soluteMetals')}` })),
            ...INTERSTITIALS.map((k) => ({ value: k, label: `${k} — ${t('alloy.soluteInterstitial')}` })),
          ]} />
        <TextInput label={t('alloy.percent')} inputMode="decimal" value={percent} onChange={(e) => setPercent(e.target.value)} data-testid="alloy-percent" />
        <Select label={t('alloy.size')} value={size} onChange={(e) => setSize(e.target.value)} options={SIZES.map((n) => ({ value: String(n), label: `${n}×${n}×${n}` }))} data-testid="alloy-size" />
        {!interstitial ? (
          <Segmented name="alloy-arrangement" label={t('alloy.arrangement')} value={arrangement} onChange={setArrangement} options={[{ value: 'aleatorio', label: t('alloy.random') }, { value: 'ordenado', label: t('alloy.ordered') }]} />
        ) : null}
        {!interstitial && arrangement === 'aleatorio' ? <TextInput label={t('alloy.seed')} inputMode="numeric" value={seed} onChange={(e) => setSeed(e.target.value)} /> : null}
        <Checkbox label={t('alloy.distort')} checked={distort} onChange={setDistort} />
        <div className="ds-row">
          <Button type="submit" variant="primary" icon="flask" disabled={status === 'loading'} data-testid="alloy-submit">{status === 'loading' ? t('alloy.forming') : t('alloy.form')}</Button>
          {alloy ? <Button type="button" onClick={() => useAlloy.getState().reset()} data-testid="alloy-close">{t('alloy.close')}</Button> : null}
        </div>
        {error ? <p className="ds-field__error" role="alert" data-testid="alloy-error">{error}</p> : null}
      </form>
      {alloy ? (
        <section aria-label={t('alloy.elements')} className="alloy-legend" data-testid="alloy-legend">
          <h3 className="ds-label">{t('alloy.elements')}</h3>
          <ul className="ds-stack">
            {legend.map((l) => (
              <li key={l.element}>
                <span className="legend-swatch" style={{ background: l.color }} aria-hidden="true" /> <strong>{l.element}</strong> — {t(`alloy.role.${l.role}`)}
                {l.atoms !== null ? <span className="ds-field__hint"> · {t('alloy.legendAtoms', { n: l.atoms })}</span> : null}
              </li>
            ))}
          </ul>
          {/* contagem: átomos ÚNICOS × esferas desenhadas (imagens periódicas não contam) */}
          <p className="ds-field__hint" data-testid="alloy-viewer-counts">{t('alloy.viewerNote', { unique: uniqueAtomCount(alloy), drawn: drawnAtomCount(alloy), label: alloy.rotulo })}</p>
        </section>
      ) : null}
      {alloy ? <AbsentSoluteNotice alloy={alloy} onApply={(n) => { setSize(String(n)); void form(n); }} /> : null}
    </div>
  );
}

/**
 * D-R2-3 (achado T-21): a realização estatística não comportou nenhum átomo do soluto.
 * Zero é o resultado CORRETO do motor (⌊N·x/(1−x) + ½⌋); o problema era a tela anunciar a liga e
 * não mostrar o soluto, sem explicação. Aqui se diz o que houve, por quê, e qual a ação.
 *
 * O tamanho sugerido NÃO é calculado no cliente: a interface pergunta ao motor, pelo mesmo
 * endpoint, com a mesma composição e supercélulas maiores, e mostra o primeiro tamanho em que a
 * resposta do motor traz ao menos um átomo do soluto (`composicao.representada[].n_atomos`).
 */
function AbsentSoluteNotice({ alloy, onApply }: { alloy: AlloyResult; onApply: (n: number) => void }) {
  const { t, num } = useI18n();
  const absent = absentSolutes(alloy);
  const elements = absent.map((a) => a.element).join(', ');
  const key = `${alloy.rotulo}|${alloy.supercelula}|${alloy.x_pct}|${alloy.semente}`;
  const [probe, setProbe] = useState<{ state: 'asking' | 'found' | 'none' | 'error'; n?: number; atoms?: number; error?: string }>({ state: 'asking' });
  const biggest = SIZES[SIZES.length - 1] as number;
  useEffect(() => {
    const missing = absentSolutes(alloy).map((a) => a.element);
    const request = useAlloy.getState().alloyRequest;
    if (!missing.length || !request) return undefined;
    let alive = true;
    const controller = new AbortController();
    setProbe({ state: 'asking' });
    void (async () => {
      for (const n of SIZES.filter((candidate) => candidate > alloy.supercelula)) {
        try {
          const probed = await crystalabApi.alloy({ ...request, n }, controller.signal);
          const counts = missing.map((el) => representedAtomsOf(probed, el) ?? 0);
          if (counts.every((c) => c >= 1)) {
            if (alive) setProbe({ state: 'found', n, atoms: counts.reduce((a, b) => a + b, 0) });
            return;
          }
        } catch (err) {
          if (!isAbort(err) && alive) setProbe({ state: 'error', error: message(err) });
          return;
        }
      }
      if (alive) setProbe({ state: 'none' });
    })();
    return () => { alive = false; controller.abort(); };
    // a sondagem se refaz quando muda a liga, o tamanho, a composição ou a semente
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!absent.length) return null;
  return (
    <CategoryBox category="feedback" as="section" role="status" aria-labelledby="alloy-absent-title" data-testid="alloy-absent-solute">
      <h3 id="alloy-absent-title">{t('alloy.absent.title', { elements })}</h3>
      <p lang="pt-BR">{t('alloy.absent.why', { label: alloy.rotulo, n: alloy.supercelula, unique: uniqueAtomCount(alloy) })}</p>
      {alloy.composicao ? <p className="ds-field__hint">{t('alloy.absent.resolution', { pct: num(alloy.composicao.resolucao_at_pct, 3) })}</p> : null}
      <p>{t('alloy.absent.action')}</p>
      {probe.state === 'asking' ? <p className="ds-field__hint"><Spinner size={14} /> {t('alloy.absent.asking')}</p> : null}
      {probe.state === 'found' && probe.n ? (
        <>
          <p data-testid="alloy-absent-suggestion">{t('alloy.absent.suggestion', { n: probe.n, atoms: probe.atoms ?? 0, elements })}</p>
          <Button size="sm" icon="flask" data-testid="alloy-absent-apply" onClick={() => onApply(probe.n as number)}>{t('alloy.absent.apply', { n: probe.n })}</Button>
        </>
      ) : null}
      {probe.state === 'none' ? <p data-testid="alloy-absent-none">{t('alloy.absent.none', { n: biggest })}</p> : null}
      {probe.state === 'error' ? <p className="ds-field__error" role="alert" data-testid="alloy-absent-error">{t('alloy.absent.probeError', { error: probe.error ?? '' })}</p> : null}
    </CategoryBox>
  );
}

function RuleStatus({ ok }: { ok: boolean | null | undefined }) {
  const { t } = useI18n();
  if (ok === true) return <Badge tone="success">✓ {t('alloy.rule.ok')}</Badge>;
  if (ok === false) return <Badge tone="danger">✗ {t('alloy.rule.fail')}</Badge>;
  return <Badge tone="neutral">— {t('alloy.rule.na')}</Badge>;
}

export function ProvenanceLine({ p, estimate }: { p: AlloyResult['procedencia']; estimate?: boolean }) {
  const { t } = useI18n();
  return (
    <footer className="alloy-prov" data-testid="alloy-provenance">
      <span className="ds-label">{t('alloy.provenance')}</span>
      <span>{t('alloy.provLine', { class: p.classe, engine: p.motor, version: p.versao_motor, data: p.versao_dados })}</span>
      {estimate ? <span className="ds-field__hint">{t('alloy.estimateNote')}</span> : null}
      {p.avisos.map((a, i) => <span key={i} className="ds-field__hint" lang="pt-BR">{a}</span>)}
    </footer>
  );
}

export function AlloyResults() {
  const { t, num } = useI18n();
  const r = useAlloy((s) => s.alloy);
  if (!r) return null;
  const absent = absentSolutes(r);
  return (
    <Panel title={t('alloy.title', { label: r.rotulo })} aside={<CategoryTag category="result" label={r.procedencia.classe} />} headingLevel={2} testId="alloy-results" className="alloy-panel">
      {absent.length ? (
        <CategoryBox category="feedback" as="section" role="status" data-testid="alloy-absent-note">
          <p>{t('alloy.absent.banner', { elements: absent.map((a) => a.element).join(', ') })}</p>
          <p className="ds-field__hint">{t('alloy.absent.action')}</p>
        </CategoryBox>
      ) : null}
      <section className="metrics-grid" aria-label={t('metrics.label')}>
        <MetricCard label={t('alloy.composition')} value={`${num(r.x_pct, 1)} %`} unit={t('alloy.compositionValue', { x: num(r.x_pct, 1), solute: r.soluto, w: num(r.pct_peso, 1) })} category="param" categoryLabel={t('category.param')} />
        <MetricCard label={t('alloy.lattice')} value={num(r.a_nm, 4)} unit={t('alloy.latticeValue', { base: num(r.a_base_nm, 4) })} category="result" categoryLabel={t('category.result')} testId="alloy-lattice" />
        <MetricCard label={t('alloy.density')} value={num(r.densidade, 3)} unit={t('alloy.densityValue', { base: num(r.densidade_base, 3) })} category="result" categoryLabel={t('category.result')} testId="alloy-density" />
        <MetricCard label={t('alloy.atoms')} value={`${uniqueAtomCount(r)}`} unit={t('alloy.atomsUnit', { drawn: drawnAtomCount(r) })} category="result" categoryLabel={t('category.result')} testId="alloy-atoms" />
        {r.fase_ordenada ? <MetricCard label={t('alloy.phase')} value={r.fase_ordenada} category="result" categoryLabel={t('category.result')} hint={r.nota_arranjo ?? undefined} /> : null}
      </section>

      <AlloyCompositionPanel r={r} />
      <AlloyRealizationBox r={r} />
      <AlloyChecksBox r={r} />

      {r.regras_por_soluto?.length ? (
        <AlloyRulesPerSolute r={r} status={(ok) => <RuleStatus ok={ok} />} />
      ) : (
        <>
          <h3>{t('alloy.rules')}</h3>
          <div className="ds-table-wrap">
            <table className="ds-table" data-testid="alloy-rules">
              <thead><tr><th scope="col">{t('alloy.rule.criterion')}</th><th scope="col">{t('alloy.rule.value')}</th><th scope="col">{t('alloy.rule.status')}</th></tr></thead>
              <tbody>
                {r.regras.map((rule) => (
                  <tr key={rule.criterio}>
                    <th scope="row">{rule.criterio}</th>
                    <td lang="pt-BR">{rule.valor ?? '—'}<br /><span className="ds-field__hint">{rule.indisponivel ?? rule.detalhe}</span></td>
                    <td><RuleStatus ok={rule.ok} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!r.regras_por_soluto?.length || r.distorcao ? (
        <CategoryBox category="note" as="section" aria-label={t('alloy.conclusion')}>
          {/* sem `regras_por_soluto` (backend anterior) a conclusão legada continua sendo exibida */}
          {r.regras_por_soluto?.length ? null : <><h3>{t('alloy.conclusion')}</h3><p lang="pt-BR" data-testid="alloy-conclusion">{r.conclusao}</p></>}
          {r.distorcao ? <p lang="pt-BR" data-testid="alloy-distortion"><strong>{t('alloy.distortion')}:</strong> {r.distorcao.descricao}</p> : null}
        </CategoryBox>
      ) : null}

      <AlloySitesPanel r={r} />
      <AlloyPhasesPanel r={r} />
      <AlloyModelBox r={r} />
      <AlloyConventions r={r} />
      <AlloyPureElementsPanel r={r} />

      <Disclosure title={t('alloy.steps')} defaultOpen={false}>
        <ol className="steps">{r.passos.map((p, i) => <li key={i} lang="pt-BR"><strong>{p.titulo}</strong>: {p.formula}{p.detalhe ? <><br /><span className="ds-field__hint">{p.detalhe}</span></> : null}</li>)}</ol>
      </Disclosure>
      <ProvenanceLine p={r.procedencia} estimate />
    </Panel>
  );
}

// ------------------------------------------------------------------------------ Temperatura
export function ThermalForm() {
  const { t } = useI18n();
  const structure = useCrystalab((s) => s.structure);
  const alloy = useAlloy((s) => s.alloy);
  const thermal = useAlloy((s) => s.thermal);
  const target = useAlloy((s) => s.thermalTarget);
  const status = useAlloy((s) => s.thermalStatus);
  const error = useAlloy((s) => s.thermalError);
  const vibration = useAlloy((s) => s.vibration);
  const reduce = prefersReducedMotion(usePreferences((s) => s.motion));
  const [choice, setChoice] = useState<'material' | 'alloy'>('material');
  const [temperature, setTemperature] = useState(600);
  const next = useLatest();
  const timer = useRef(0);
  const symbol = structure?.simbolo ?? null;
  const effective: 'material' | 'alloy' = alloy ? choice : 'material';

  const canCompute = effective === 'alloy' ? Boolean(alloy) : Boolean(symbol);

  async function compute(valueC: number) {
    if (!canCompute) return;
    const signal = next();
    useAlloy.getState().set({ thermalStatus: 'loading', thermalError: null });
    try {
      const request = useAlloy.getState().alloyRequest;
      const result = effective === 'alloy' && request
        ? await crystalabApi.thermal({ liga: request, temperatura_c: valueC }, signal)
        : await crystalabApi.thermal({ material: symbol as string, temperatura_c: valueC }, signal);
      useAlloy.getState().set({ thermal: result, thermalTarget: effective, thermalStatus: 'idle' });
    } catch (err) {
      if (isAbort(err)) return;
      useAlloy.getState().set({ thermalStatus: 'error', thermalError: message(err), thermal: null, thermalTarget: null });
    }
  }

  // arrastar o controle recalcula depois de uma pausa curta (e cancela o pedido anterior)
  function onTemperature(v: number) {
    setTemperature(v);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => void compute(v), 350);
  }
  useEffect(() => () => window.clearTimeout(timer.current), []);

  const ready = Boolean(thermal) && target === effective;
  return (
    <div className="thermal-form ds-stack" data-testid="thermal-form">
      <p className="ds-field__hint">{t('thermal.lead')}</p>
      {alloy ? (
        <Segmented name="thermal-target" label={t('thermal.target')} value={choice} onChange={setChoice}
          options={[{ value: 'material', label: t('thermal.targetMaterial', { name: symbol ?? '—' }), disabled: !symbol }, { value: 'alloy', label: t('thermal.targetAlloy') }]} />
      ) : null}
      {!canCompute ? <p className="ds-field__hint" role="note">{t('thermal.noMaterial')}</p> : null}
      <Slider label={t('thermal.temperature')} min={-200} max={2500} step={10} value={temperature} onChange={onTemperature} valueText={`${temperature} °C`} />
      <div className="ds-row">
        <Button variant="primary" icon="thermometer" disabled={!canCompute || status === 'loading'} onClick={() => void compute(temperature)} data-testid="thermal-submit">{t('thermal.calc')}</Button>
        {status === 'loading' ? <Spinner size={14} /> : null}
      </div>
      {error ? <p className="ds-field__error" role="alert" data-testid="thermal-error">{error}</p> : null}
      <section aria-label={t('thermal.vibration')} className="ds-stack">
        <h3 className="ds-label">{t('thermal.vibration')}</h3>
        <ToggleButton size="sm" icon="thermometer" pressed={vibration.on && ready} disabled={!ready} data-testid="thermal-vibrate"
          onPressedChange={(on) => useAlloy.getState().set({ vibration: { ...useAlloy.getState().vibration, on } })}>{t('thermal.vibrationToggle')}</ToggleButton>
        {!ready ? <p className="ds-field__hint">{t('thermal.needsResult')}</p> : null}
        <Slider label={t('thermal.exaggeration')} min={1} max={10} step={1} value={vibration.exaggeration} valueText={`${vibration.exaggeration}×`}
          onChange={(v) => useAlloy.getState().set({ vibration: { ...useAlloy.getState().vibration, exaggeration: v } })} />
        <p className="ds-field__hint">{t('thermal.exaggerationHint')}</p>
        {reduce ? <p className="ds-field__hint">{t('thermal.reduced')}</p> : null}
      </section>
    </div>
  );
}

function VibrationCurve({ r }: { r: ThermalResult }) {
  const { t, num } = useI18n();
  const W = 520;
  const H = 220;
  const P = { l: 52, r: 16, t: 14, b: 40 };
  // Sem dominio valido o motor devolve a curva vazia, com a causa em `indisponiveis.curva` (achados T-1/T-4).
  // Desenhar um grafico vazio daria a entender que a grandeza vale zero.
  if (!r.curva.length) {
    const motivo = r.indisponiveis?.curva;
    return motivo ? (
      <CategoryBox category="feedback" role="status" data-testid="thermal-curve-unavailable">
        <p lang="pt-BR">{motivo}</p>
      </CategoryBox>
    ) : null;
  }
  const xs = r.curva.map((p) => p[0]);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMax = Math.max(r.lindemann * 1.15, ...r.curva.map((p) => p[1]));
  const x = (v: number) => P.l + ((v - xMin) / (xMax - xMin || 1)) * (W - P.l - P.r);
  const y = (v: number) => H - P.b - (v / yMax) * (H - P.t - P.b);
  const path = r.curva.map((p, i) => `${i ? 'L' : 'M'}${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join(' ');
  const xTicks = [0, 1, 2, 3, 4].map((i) => xMin + ((xMax - xMin) * i) / 4);
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * yMax);
  const desc = t('thermal.curveDesc', { t: num(r.temperatura_c, 0), r: num(r.razao_lindemann, 3), limit: num(r.lindemann, 2) });
  return (
    <figure className="chart" data-testid="thermal-curve">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={desc} className="chart__svg">
        {yTicks.map((v) => <g key={v}><line x1={P.l} x2={W - P.r} y1={y(v)} y2={y(v)} className="chart__grid" /><text x={P.l - 6} y={y(v) + 4} textAnchor="end" className="chart__tick">{num(v, 2)}</text></g>)}
        {xTicks.map((v) => <text key={v} x={x(v)} y={H - P.b + 16} textAnchor="middle" className="chart__tick">{num(v, 0)}</text>)}
        <line x1={P.l} x2={W - P.r} y1={y(r.lindemann)} y2={y(r.lindemann)} className="chart__ref" strokeDasharray="5 4" />
        <text x={W - P.r} y={y(r.lindemann) - 5} textAnchor="end" className="chart__label">{t('thermal.lindemannLine', { limit: num(r.lindemann, 2) })}</text>
        <path d={path} className="chart__line" fill="none" />
        <circle cx={x(Math.min(Math.max(r.temperatura_c, xMin), xMax))} cy={y(r.razao_lindemann)} r={5} className="chart__pt chart__pt--sel" />
        <text x={(P.l + W - P.r) / 2} y={H - 6} textAnchor="middle" className="chart__label">{t('thermal.curveX')}</text>
        <text x={14} y={(P.t + H - P.b) / 2} textAnchor="middle" className="chart__label" transform={`rotate(-90 14 ${(P.t + H - P.b) / 2})`}>{t('thermal.curveY')}</text>
      </svg>
      <figcaption>{desc}</figcaption>
    </figure>
  );
}

export function ThermalResults() {
  const { t, num } = useI18n();
  const r = useAlloy((s) => s.thermal);
  const target = useAlloy((s) => s.thermalTarget);
  const alloyLabel = useAlloy((s) => s.alloy?.rotulo);
  const structureLabel = useCrystalab((s) => s.structure?.rotulo);
  if (!r) return null;
  const subject = (target === 'alloy' ? alloyLabel : structureLabel) ?? '';
  // Acima da T_f do modelo o motor devolve estes campos nulos COM a causa; a causa tem de aparecer
  // junto do valor, nunca um zero silencioso (pedido secao 4; achado T-1).
  const semDado = r.indisponiveis ?? {};
  return (
    <Panel title={t('thermal.title')} aside={<CategoryTag category="result" label={r.procedencia.classe} />} headingLevel={2} testId="thermal-results" className="alloy-panel">
      {r.fundido ? <CategoryBox category="feedback" role="alert" data-testid="thermal-melted"><p>{t('thermal.melted')}</p></CategoryBox> : null}
      <section className="metrics-grid" aria-label={t('metrics.label')}>
        <MetricCard label={t('thermal.temperature')} value={`${num(r.temperatura_c, 0)} °C`} unit={`${num(r.temperatura_k, 2)} K · ${t('thermal.fusion', { t: num(r.fusao_c, 0) })}`} category="param" categoryLabel={t('category.param')} />
        <MetricCard label={t('thermal.homologous')} value={num(r.homologa, 3)} category="result" categoryLabel={t('category.result')} testId="thermal-homologous" />
        <MetricCard label={t('thermal.alpha')} value={num(r.alfa_1e6_k, 1)} unit={t('thermal.alphaUnit')} category="reference" categoryLabel={t('category.reference')} />
        <MetricCard label={t('thermal.lattice')} value={num(r.a_nm, 5)} unit={r.a_nm === null ? undefined : t('thermal.deltaA', { pct: num(r.delta_a_pct, 3) })} hint={r.a_nm === null ? <span lang="pt-BR">{semDado.a_nm}</span> : undefined} category="result" categoryLabel={t('category.result')} testId="thermal-lattice" />
        <MetricCard label={t('thermal.deltaV')} value={r.delta_v_pct === null ? num(null, 2) : `${num(r.delta_v_pct, 2)} %`} hint={r.delta_v_pct === null ? <span lang="pt-BR">{semDado.delta_v_pct}</span> : undefined} category="result" categoryLabel={t('category.result')} />
        {typeof r.densidade === 'number' ? <MetricCard label={t('thermal.density')} value={`${num(r.densidade, 3)}`} unit="g/cm³" category="result" categoryLabel={t('category.result')} /> : null}
        <MetricCard label={t('thermal.amplitude')} value={num(r.u_nm * 1000, 2)} unit={t('thermal.amplitudeHint', { ratio: `${num(r.razao_lindemann * 100, 1)} %` })} category="result" categoryLabel={t('category.result')} testId="thermal-amplitude" />
      </section>
      <h3>{t('thermal.curve')} <span className="ds-field__hint">({subject})</span></h3>
      <VibrationCurve r={r} />
      {r.notas.length ? (
        <section aria-label={t('thermal.notes')}>
          <h3>{t('thermal.notes')}</h3>
          <ul className="ds-stack">{r.notas.map((n, i) => <li key={i} lang="pt-BR"><Badge tone={n.tipo === 'alerta' ? 'warning' : 'info'}>{n.tipo === 'alerta' ? t('thermal.noteWarn') : t('thermal.noteInfo')}</Badge> {n.texto}</li>)}</ul>
        </section>
      ) : null}
      <ProvenanceLine p={r.procedencia} estimate />
    </Panel>
  );
}

/** Aviso acima do viewer: ele mostra a liga, mas o cabeçalho e os cartões continuam sendo do metal carregado. */
export function AlloyBanner() {
  const { t } = useI18n();
  const alloy = useAlloy((s) => s.alloy);
  const metal = useCrystalab((s) => s.structure?.rotulo);
  if (!alloy) return null;
  return (
    <CategoryBox category="note" as="section" className="alloy-banner" data-testid="alloy-banner" role="status">
      <p>{t('alloy.banner', { label: alloy.rotulo, unique: uniqueAtomCount(alloy), drawn: drawnAtomCount(alloy), metal: metal ?? '—' })}</p>
      {/* D-R2-3: a cena não pode anunciar a liga e esconder que o soluto não foi representado. */}
      {absentSolutes(alloy).length ? (
        <p lang="pt-BR" data-testid="alloy-absent-banner"><strong>{t('alloy.absent.banner', { elements: absentSolutes(alloy).map((a) => a.element).join(', ') })}</strong></p>
      ) : null}
      <Button size="sm" onClick={() => useAlloy.getState().reset()}>{t('alloy.close')}</Button>
    </CategoryBox>
  );
}
