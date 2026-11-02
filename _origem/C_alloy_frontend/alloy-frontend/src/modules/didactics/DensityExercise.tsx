/**
 * ExerciseWorkspace da densidade teórica (6.5–6.7), fluxo de 7 passos:
 * problema e dados → grandezas → equação → substituição com unidades → validação →
 * resultado do motor e interpretação → revisão de erros.
 * Todos os valores esperados e as alternativas "conceitualmente erradas" vêm do motor
 * (ex.: mesma densidade calculada pelo motor com outra estrutura). Nada é inventado.
 */
import { useEffect, useMemo, useState } from 'react';
import { useI18n, pick, type Localized } from '../../i18n/index.ts';
import { crystalabApi } from '../../services/api/crystalab.ts';
import type { StructureCode, StructureResult } from '../../services/api/contracts.ts';
import { Button } from '../../design-system/primitives/Button.tsx';
import { Checkbox, TextInput } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, CategoryTag } from '../../design-system/primitives/Category.tsx';
import { StepPanel, type StepItem } from '../../design-system/layout/StepPanel.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { Formula } from '../../features/formula/Formula.tsx';
import { parseUserNumber } from '../../utils/format.ts';
import { announce } from '../../design-system/announce.ts';
import { classifyAnswer, type Activity, type ErrorType } from './model.ts';
import { useDidactics } from './store.ts';
import { addNote } from '../notebook/store.ts';
import { EngineText } from '../crystalab/Results.tsx';

const STEP_IDS = ['dados', 'grandezas', 'equacao', 'substituicao', 'validacao', 'motor', 'revisao'] as const;
type StepId = (typeof STEP_IDS)[number];

const HINTS: Record<'grandezas' | 'equacao' | 'substituicao' | 'validacao', [Localized, Localized]> = {
  grandezas: [
    { 'pt-BR': 'Densidade é massa por volume. Que grandezas dão a massa dos átomos de UMA célula? E o volume dessa célula?', en: 'Density is mass per volume. Which quantities give the mass of the atoms in ONE cell? And that cell volume?', es: 'Densidad es masa por volumen. ¿Qué magnitudes dan la masa de los átomos de UNA celda? ¿Y el volumen de esa celda?' },
    { 'pt-BR': 'A massa da célula usa n e A (convertida por N_A); o volume Vc vem do parâmetro a, que depende de R. NC, FEA e temperatura de fusão não entram.', en: 'Cell mass uses n and A (converted by N_A); volume Vc comes from a, which depends on R. CN, APF and melting point are not used.', es: 'La masa de la celda usa n y A (convertida por N_A); el volumen Vc viene de a, que depende de R. NC, FEA y temperatura de fusión no intervienen.' },
  ],
  equacao: [
    { 'pt-BR': 'O numerador deve ter unidade de massa (g) e o denominador, de volume (cm³).', en: 'The numerator must be a mass (g) and the denominator a volume (cm³).', es: 'El numerador debe tener unidad de masa (g) y el denominador, de volumen (cm³).' },
    { 'pt-BR': 'n·A/N_A é a massa (g) dos átomos de uma célula; divida pelo volume Vc.', en: 'n·A/N_A is the mass (g) of one cell’s atoms; divide by the volume Vc.', es: 'n·A/N_A es la masa (g) de los átomos de una celda; divida por el volumen Vc.' },
  ],
  substituicao: [
    { 'pt-BR': 'Verifique ao longo de qual linha da célula os átomos se tocam nesta estrutura; isso define a relação entre a e R.', en: 'Check along which cell line the atoms touch in this structure; that defines the a–R relation.', es: 'Verifique a lo largo de qué línea de la celda se tocan los átomos en esta estructura; eso define la relación entre a y R.' },
    { 'pt-BR': 'Converta antes de elevar ao cubo: 1 nm = 10⁻⁷ cm, logo 1 nm³ = 10⁻²¹ cm³.', en: 'Convert before cubing: 1 nm = 10⁻⁷ cm, so 1 nm³ = 10⁻²¹ cm³.', es: 'Convierta antes de elevar al cubo: 1 nm = 10⁻⁷ cm, así 1 nm³ = 10⁻²¹ cm³.' },
  ],
  validacao: [
    { 'pt-BR': 'Confira se o resultado tem ordem de grandeza de metais (alguns g/cm³ a ~20 g/cm³).', en: 'Check the order of magnitude: metals are a few g/cm³ up to ~20 g/cm³.', es: 'Revise el orden de magnitud: los metales van de unos g/cm³ a ~20 g/cm³.' },
    { 'pt-BR': 'Use N_A = 6,022 × 10²³ átomos/mol e o mesmo n do passo 4.', en: 'Use N_A = 6.022 × 10²³ atoms/mol and the same n as in step 4.', es: 'Use N_A = 6,022 × 10²³ átomos/mol y el mismo n del paso 4.' },
  ],
};

const QUANTITIES = [
  { id: 'n', tex: 'n', required: true }, { id: 'A', tex: 'A', required: true }, { id: 'Vc', tex: 'V_C', required: true }, { id: 'NA', tex: 'N_A', required: true },
  { id: 'R', tex: 'R', required: false, accepted: true }, { id: 'a', tex: 'a', required: false, accepted: true },
  { id: 'NC', tex: '\\text{NC}', required: false }, { id: 'FEA', tex: '\\text{FEA}', required: false }, { id: 'Tf', tex: 'T_f', required: false },
] as const;

const EQUATIONS = [
  { id: 'ok', tex: '\\rho = \\dfrac{n\\,A}{V_C\\,N_A}', correct: true },
  { id: 'inv', tex: '\\rho = \\dfrac{A}{n\\,V_C\\,N_A}', correct: false, type: 'algebraic' as ErrorType },
  { id: 'swap', tex: '\\rho = \\dfrac{n\\,V_C}{A\\,N_A}', correct: false, type: 'algebraic' as ErrorType },
  { id: 'nc', tex: '\\rho = \\dfrac{\\text{NC}\\,A}{V_C\\,N_A}', correct: false, type: 'conceptual' as ErrorType },
];

interface Data {
  r: StructureResult;
  /** mesmo metal calculado PELO MOTOR com as outras estruturas cúbicas (alternativas conceituais) */
  alternatives: StructureResult[];
}

export function useExerciseStructure(symbol: string): { data: Data | null; error: string | null } {
  const [state, setState] = useState<{ data: Data | null; error: string | null }>({ data: null, error: null });
  useEffect(() => {
    let alive = true;
    const ctrl = new AbortController();
    setState({ data: null, error: null });
    (async () => {
      const r = await crystalabApi.structure({ nome: symbol }, ctrl.signal);
      const others = (['CS', 'CCC', 'CFC'] as StructureCode[]).filter((c) => c !== r.estrutura);
      const alternatives = await Promise.all(others.map((c) => crystalabApi.structure({ nome: symbol, estrutura: c }, ctrl.signal).catch(() => null)));
      if (alive) setState({ data: { r, alternatives: alternatives.filter((x): x is StructureResult => Boolean(x)) }, error: null });
    })().catch((err: unknown) => { if (alive) setState({ data: null, error: err instanceof Error ? err.message : String(err) }); });
    return () => { alive = false; ctrl.abort(); };
  }, [symbol]);
  return state;
}

function FeedbackBox({ result }: { result: { correct: boolean; type?: ErrorType; power?: number } | null }) {
  const { t } = useI18n();
  if (!result) return null;
  return (
    <CategoryBox category="feedback" className={`feedback ${result.correct ? 'is-correct' : 'is-wrong'}`} role="status" data-testid="exercise-feedback">
      <strong>{result.correct ? `✓ ${t('exercise.correct')}` : `✗ ${t(`exercise.error.${result.type ?? 'algebraic'}`)}`}</strong>
      {!result.correct ? <p>{t(`exercise.errorHelp.${result.type ?? 'algebraic'}`, { power: result.power ?? 0 })}</p> : null}
    </CategoryBox>
  );
}

function Hints({ hints, level, onMore }: { hints: [Localized, Localized]; level: number; onMore: () => void }) {
  const { t, locale } = useI18n();
  return (
    <div className="hints">
      {hints.slice(0, level).map((h, i) => (
        <CategoryBox key={i} category="feedback" className="hint" role="note"><strong>{t(i === 0 ? 'exercise.hintConceptual' : 'exercise.hintSpecific')}</strong> {pick(h, locale)}</CategoryBox>
      ))}
      {level < hints.length ? <Button size="sm" variant="ghost" icon="bulb" onClick={onMore} data-testid="hint-button">{t('exercise.hint', { n: level + 1, total: hints.length })}</Button> : <p className="ds-field__hint">{t('exercise.noMoreHints')}</p>}
    </div>
  );
}

export function DensityExercise({ activity, symbol, seed }: { activity: Activity; symbol: string; seed: number }) {
  const { t, num, sci, locale } = useI18n();
  const { data, error } = useExerciseStructure(symbol);
  const record = useDidactics((s) => s.record);
  const complete = useDidactics((s) => s.complete);
  const [step, setStep] = useState(0);
  const [hint, setHint] = useState<Record<string, number>>({});
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [equation, setEquation] = useState('');
  const [nIn, setN] = useState('');
  const [aIn, setA] = useState('');
  const [vIn, setV] = useState('');
  const [rhoIn, setRho] = useState('');
  const [fb, setFb] = useState<Record<string, { correct: boolean; type?: ErrorType; power?: number } | null>>({});
  const [log, setLog] = useState<Array<{ step: StepId; correct: boolean; type?: ErrorType }>>([]);

  const r = data?.r;
  const tol = activity.criteria.find((c) => c.id === 'rho')?.tolerance ?? 0.01;
  const attempt = (s: StepId, res: { correct: boolean; type?: ErrorType }) => {
    setLog((l) => [...l, { step: s, correct: res.correct, ...(res.type ? { type: res.type } : {}) }]);
    record({ activityId: activity.id, topic: activity.topic, step: s, correct: res.correct, ...(res.type ? { errorType: res.type } : {}), seed, material: symbol });
    announce(res.correct ? t('exercise.correct') : t(`exercise.error.${res.type ?? 'algebraic'}`));
  };

  const steps = useMemo<StepItem[]>(() => STEP_IDS.map((id, i) => ({
    title: t(`exercise.step.${id}`),
    status: i < step ? 'done' : i === step ? 'current' : 'todo',
  })), [step, t]);

  if (error) return <CategoryBox category="feedback" role="alert"><p>{t('exercise.engineNeeded')}</p><p className="ds-mono">{error}</p></CategoryBox>;
  if (!r) return <Spinner size={22} label={t('common.loading')} />;

  const next = () => { setStep((s) => Math.min(6, s + 1)); window.setTimeout(() => document.getElementById('exercise-step')?.focus(), 30); };
  const altFor = (pickV: (x: StructureResult) => number | null) => data.alternatives.map(pickV).filter((v): v is number => v !== null);

  const stepId = STEP_IDS[step] as StepId;
  return (
    <div className="exercise" data-testid="density-exercise" data-step={stepId}>
      <div className="exercise__steps"><StepPanel steps={steps} label={t('exercise.stepsLabel')} /></div>
      <section className="exercise__body" id="exercise-step" tabIndex={-1} aria-labelledby="exercise-step-title">
        <h2 id="exercise-step-title">{`${step + 1}. ${t(`exercise.step.${stepId}`)}`}</h2>

        {stepId === 'dados' ? (
          <>
            <p>{t('exercise.density.statement', { name: r.rotulo, structure: r.estrutura })}</p>
            <CategoryBox category="reference" className="exercise__data">
              <CategoryTag category="reference" label={t('exercise.dataFromEngine')} />
              <dl className="guided__dl">
                <dt>R</dt><dd>{num(r.raio_nm, 4)} nm</dd>
                <dt>A</dt><dd>{num(r.peso, 2)} g/mol</dd>
                <dt>{t('metrics.structure')}</dt><dd lang="pt-BR">{`${r.estrutura_nome} (${r.estrutura})`}</dd>
                <dt>N_A</dt><dd>6,022 × 10²³ {t('density.atomsPerMol')}</dd>
              </dl>
            </CategoryBox>
            <p className="ds-field__hint">{pick(activity.instructions, locale)}</p>
            <Button variant="primary" onClick={next} data-testid="exercise-next">{t('exercise.start')}</Button>
          </>
        ) : null}

        {stepId === 'grandezas' ? (
          <>
            <p>{t('exercise.density.quantitiesQ')}</p>
            <fieldset className="exercise__checks"><legend className="sr-only">{t('exercise.density.quantitiesQ')}</legend>
              {QUANTITIES.map((q) => <Checkbox key={q.id} id={`q-${q.id}`} label={<Formula tex={q.tex} label={q.id} />} checked={Boolean(checked[q.id])} onChange={(v) => setChecked((c) => ({ ...c, [q.id]: v }))} />)}
            </fieldset>
            <Hints hints={HINTS.grandezas} level={hint.grandezas ?? 0} onMore={() => setHint((h) => ({ ...h, grandezas: (h.grandezas ?? 0) + 1 }))} />
            <Button variant="primary" data-testid="exercise-check" onClick={() => {
              const missing = QUANTITIES.filter((q) => q.required && !checked[q.id]);
              const wrong = QUANTITIES.filter((q) => !q.required && !('accepted' in q && q.accepted) && checked[q.id]);
              const res = missing.length || wrong.length ? { correct: false, type: 'conceptual' as ErrorType } : { correct: true };
              setFb((f) => ({ ...f, grandezas: res }));
              attempt('grandezas', res);
            }}>{t('exercise.check')}</Button>
            <FeedbackBox result={fb.grandezas ?? null} />
            {fb.grandezas?.correct ? <Button onClick={next} data-testid="exercise-next">{t('exercise.next')}</Button> : null}
          </>
        ) : null}

        {stepId === 'equacao' ? (
          <>
            <p>{t('exercise.density.equationQ')}</p>
            <fieldset className="exercise__radios"><legend className="sr-only">{t('exercise.density.equationQ')}</legend>
              {EQUATIONS.map((e) => (
                <label key={e.id} className={`exercise__radio ${equation === e.id ? 'is-on' : ''}`}>
                  <input type="radio" name="equation" value={e.id} checked={equation === e.id} onChange={() => setEquation(e.id)} data-testid={`eq-${e.id}`} />
                  <Formula tex={e.tex} display label={e.id} />
                </label>
              ))}
            </fieldset>
            <Hints hints={HINTS.equacao} level={hint.equacao ?? 0} onMore={() => setHint((h) => ({ ...h, equacao: (h.equacao ?? 0) + 1 }))} />
            <Button variant="primary" disabled={!equation} data-testid="exercise-check" onClick={() => {
              const e = EQUATIONS.find((x) => x.id === equation);
              const res = e?.correct ? { correct: true } : { correct: false, type: (e && 'type' in e ? e.type : 'algebraic') as ErrorType };
              setFb((f) => ({ ...f, equacao: res }));
              attempt('equacao', res);
            }}>{t('exercise.check')}</Button>
            <FeedbackBox result={fb.equacao ?? null} />
            {fb.equacao?.correct ? <Button onClick={next} data-testid="exercise-next">{t('exercise.next')}</Button> : null}
          </>
        ) : null}

        {stepId === 'substituicao' ? (
          <>
            <p>{t('exercise.density.substitutionQ')}</p>
            <div className="exercise__inputs">
              <TextInput label={t('exercise.density.nLabel')} inputMode="numeric" value={nIn} onChange={(e) => setN(e.target.value)} data-testid="in-n" />
              <TextInput label={t('exercise.density.aLabel')} hint={t('exercise.unitNm')} inputMode="decimal" value={aIn} onChange={(e) => setA(e.target.value)} data-testid="in-a" />
              <TextInput label={t('exercise.density.vcLabel')} hint={t('exercise.unitCm3')} inputMode="decimal" value={vIn} onChange={(e) => setV(e.target.value)} placeholder="4,72e-23" data-testid="in-vc" />
            </div>
            <Hints hints={HINTS.substituicao} level={hint.substituicao ?? 0} onMore={() => setHint((h) => ({ ...h, substituicao: (h.substituicao ?? 0) + 1 }))} />
            <Button variant="primary" data-testid="exercise-check" onClick={() => {
              const nv = parseUserNumber(nIn);
              const resN = nv === null || Number.isNaN(nv) ? { correct: false, type: 'input' as ErrorType } : nv === r.n ? { correct: true } : nv === r.nc ? { correct: false, type: 'conceptual' as ErrorType } : { correct: false, type: 'conceptual' as ErrorType };
              const resA = classifyAnswer(parseUserNumber(aIn), r.a_nm as number, 0.01, altFor((x) => x.a_nm));
              const resV = classifyAnswer(parseUserNumber(vIn), r.volume_cm3 as number, 0.015, altFor((x) => x.volume_cm3));
              const all = [resN, resA, resV];
              const res = all.every((x) => x.correct) ? { correct: true } : (all.find((x) => !x.correct) as { correct: boolean; type?: ErrorType; power?: number });
              setFb((f) => ({ ...f, substituicao: res, sn: resN, sa: resA, sv: resV }));
              attempt('substituicao', res);
            }}>{t('exercise.check')}</Button>
            {fb.substituicao ? (
              <ul className="exercise__partial" aria-label={t('exercise.partial')}>
                <li>n: {fb.sn?.correct ? '✓' : `✗ ${t(`exercise.error.${fb.sn?.type ?? 'algebraic'}`)}`}</li>
                <li>a: {fb.sa?.correct ? '✓' : `✗ ${t(`exercise.error.${fb.sa?.type ?? 'algebraic'}`)}`}</li>
                <li>Vc: {fb.sv?.correct ? '✓' : `✗ ${t(`exercise.error.${fb.sv?.type ?? 'algebraic'}`)}`}</li>
              </ul>
            ) : null}
            <FeedbackBox result={fb.substituicao ?? null} />
            {fb.substituicao?.correct ? <Button onClick={next} data-testid="exercise-next">{t('exercise.next')}</Button> : null}
          </>
        ) : null}

        {stepId === 'validacao' ? (
          <>
            <p>{t('exercise.density.rhoQ')}</p>
            <TextInput label={t('exercise.density.rhoLabel')} hint="g/cm³" inputMode="decimal" value={rhoIn} onChange={(e) => setRho(e.target.value)} data-testid="in-rho" />
            <Hints hints={HINTS.validacao} level={hint.validacao ?? 0} onMore={() => setHint((h) => ({ ...h, validacao: (h.validacao ?? 0) + 1 }))} />
            <Button variant="primary" data-testid="exercise-check" onClick={() => {
              // alternativas conceituais: densidades que o MOTOR calcula para o mesmo metal em outras estruturas
              const res = classifyAnswer(parseUserNumber(rhoIn), r.densidade as number, tol, altFor((x) => x.densidade));
              setFb((f) => ({ ...f, validacao: res }));
              attempt('validacao', res);
            }}>{t('exercise.check')}</Button>
            <FeedbackBox result={fb.validacao ?? null} />
            {fb.validacao ? <Button onClick={next} data-testid="exercise-next">{fb.validacao.correct ? t('exercise.next') : t('exercise.seeEngine')}</Button> : null}
          </>
        ) : null}

        {stepId === 'motor' ? (
          <>
            <CategoryBox category="result" className="exercise__engine">
              <CategoryTag category="result" label={t('category.result')} />
              <ol className="ds-steps">
                {r.passos_densidade.map((p, i) => (
                  <li key={i} className="ds-step ds-step--done"><span className="ds-step__index" aria-hidden="true">{i + 1}</span>
                    <div><strong lang="pt-BR">{p.titulo}</strong><pre className="ds-pre"><EngineText>{p.formula}</EngineText></pre>{p.detalhe ? <p className="ds-field__hint" lang="pt-BR">{p.detalhe}</p> : null}</div></li>
                ))}
              </ol>
            </CategoryBox>
            <div className="ds-table-wrap">
              <table className="ds-table" data-testid="exercise-compare">
                <caption>{t('exercise.compareCaption')}</caption>
                <thead><tr><th scope="col">{t('exercise.quantity')}</th><th scope="col">{t('exercise.yours')}</th><th scope="col">{t('exercise.engine')}</th></tr></thead>
                <tbody>
                  <tr><th scope="row">n</th><td>{nIn || '—'}</td><td>{r.n}</td></tr>
                  <tr><th scope="row">a (nm)</th><td>{aIn || '—'}</td><td>{num(r.a_nm, 4)}</td></tr>
                  <tr><th scope="row">Vc (cm³)</th><td>{vIn || '—'}</td><td>{sci(r.volume_cm3)}</td></tr>
                  <tr><th scope="row">ρ (g/cm³)</th><td>{rhoIn || '—'}</td><td>{num(r.densidade, 3)}</td></tr>
                </tbody>
              </table>
            </div>
            <CategoryBox category="feedback" className="exercise__interp"><p>{pick(activity.explanation, locale)}</p>
              {r.densidade_exp !== null && r.erro_percent !== null ? <p>{t('density.vsExp', { exp: num(r.densidade_exp, 2), err: `${r.erro_percent >= 0 ? '+' : ''}${num(r.erro_percent, 2)}` })}</p> : null}
              <cite>{activity.references.join(' · ')}</cite></CategoryBox>
            <Button variant="primary" onClick={next} data-testid="exercise-next">{t('exercise.next')}</Button>
          </>
        ) : null}

        {stepId === 'revisao' ? (
          <>
            <ReviewTable log={log} />
            <div className="ds-row">
              <Button variant="primary" icon="check" data-testid="exercise-complete" onClick={() => { complete(activity.id); announce(t('exercise.completed')); }}>{t('exercise.complete')}</Button>
              <Button icon="notebook" data-testid="exercise-to-notebook" onClick={() => {
                addNote({ kind: 'conclusion', title: `${pick(activity.title, locale)} — ${r.rotulo}`, body: t('exercise.noteBody', { rho: rhoIn || '—', engine: num(r.densidade, 3) }), activityId: activity.id, structure: { rotulo: r.rotulo, estrutura: r.estrutura, request: { nome: symbol } }, params: { R: r.raio_nm, A: r.peso, n: r.n, a_nm: r.a_nm, densidade_motor: r.densidade } });
                announce(t('notebook.saved'));
              }}>{t('exercise.toNotebook')}</Button>
            </div>
          </>
        ) : null}
      </section>
    </div>
  );
}

export function ReviewTable({ log }: { log: Array<{ step: string; correct: boolean; type?: ErrorType }> }) {
  const { t } = useI18n();
  const errors = log.filter((l) => !l.correct);
  const byType = errors.reduce<Record<string, number>>((m, e) => ({ ...m, [e.type ?? 'algebraic']: (m[e.type ?? 'algebraic'] ?? 0) + 1 }), {});
  return (
    <div data-testid="exercise-review">
      <p>{t('exercise.reviewSummary', { attempts: log.length, errors: errors.length })}</p>
      {errors.length ? (
        <ul className="exercise__review">
          {Object.entries(byType).map(([type, count]) => <li key={type}><strong>{t(`exercise.error.${type as ErrorType}`)}</strong> × {count} — {t(`exercise.errorHelp.${type as ErrorType}`, { power: 0 })}</li>)}
        </ul>
      ) : <p>{t('exercise.noErrors')}</p>}
    </div>
  );
}
