/**
 * Exercícios guiados curtos (átomos por célula, FEA, planos e direções). Mesmo princípio do
 * ExerciseWorkspace: dados e respostas esperadas vêm do motor; o estudante resolve; o motor revela.
 */
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useI18n, pick } from '../../i18n/index.ts';
import { crystalabApi } from '../../services/api/crystalab.ts';
import type { MillerDirection, MillerPlane, StructureResult } from '../../services/api/contracts.ts';
import { Button } from '../../design-system/primitives/Button.tsx';
import { TextInput } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, CategoryTag } from '../../design-system/primitives/Category.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { parseUserNumber } from '../../utils/format.ts';
import { createRng } from '../../utils/rng.ts';
import { announce } from '../../design-system/announce.ts';
import { encodeScene } from '../../features/url/sceneUrl.ts';
import { classifyAnswer, type Activity, type ErrorType } from './model.ts';
import { useDidactics } from './store.ts';
import { ReviewTable } from './DensityExercise.tsx';

const SITE_KEYS = { vertice: 'site.vertice', centro: 'site.centro', face: 'site.face', basal: 'site.basal', interior: 'site.interior' } as const;

function OpenInLab({ symbol, overlay }: { symbol: string; overlay?: { t: 'p' | 'd'; i: number[] } }) {
  const { t } = useI18n();
  const param = encodeScene({ v: 1, m: { nome: symbol }, ...(overlay ? { o: [overlay] } : {}) });
  return <a className="ds-btn ds-btn--secondary ds-btn--sm" href={`#/crystalab?s=${param}`}>{t('exercise.openLab')}</a>;
}

function useStructure(symbol: string) {
  const [r, setR] = useState<StructureResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const ctrl = new AbortController();
    setR(null);
    crystalabApi.structure({ nome: symbol }, ctrl.signal).then(setR).catch((e: unknown) => { if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : String(e)); });
    return () => ctrl.abort();
  }, [symbol]);
  return { r, error };
}

function Shell({ activity, children, log, done }: { activity: Activity; children: ReactNode; log: Array<{ step: string; correct: boolean; type?: ErrorType }>; done: boolean }) {
  const { t, locale } = useI18n();
  const complete = useDidactics((s) => s.complete);
  return (
    <div className="exercise exercise--short">
      <section className="exercise__body">
        {children}
        {done ? (
          <>
            <CategoryBox category="feedback"><p>{pick(activity.explanation, locale)}</p><cite>{activity.references.join(' · ')}</cite></CategoryBox>
            <ReviewTable log={log} />
            <Button variant="primary" icon="check" data-testid="exercise-complete" onClick={() => { complete(activity.id); announce(t('exercise.completed')); }}>{t('exercise.complete')}</Button>
          </>
        ) : null}
      </section>
    </div>
  );
}

function useAttempts(activity: Activity, seed: number, material: string) {
  const record = useDidactics((s) => s.record);
  const [log, setLog] = useState<Array<{ step: string; correct: boolean; type?: ErrorType }>>([]);
  const attempt = (step: string, res: { correct: boolean; type?: ErrorType }) => {
    setLog((l) => [...l, { step, ...res }]);
    record({ activityId: activity.id, topic: activity.topic, step, correct: res.correct, ...(res.type ? { errorType: res.type } : {}), seed, material });
  };
  return { log, attempt };
}

function Feedback({ res }: { res: { correct: boolean; type?: ErrorType; power?: number } | null }) {
  const { t } = useI18n();
  if (!res) return null;
  return <CategoryBox category="feedback" role="status" className={`feedback ${res.correct ? 'is-correct' : 'is-wrong'}`} data-testid="exercise-feedback"><strong>{res.correct ? `✓ ${t('exercise.correct')}` : `✗ ${t(`exercise.error.${res.type ?? 'algebraic'}`)}`}</strong>{!res.correct ? <p>{t(`exercise.errorHelp.${res.type ?? 'algebraic'}`, { power: res.power ?? 0 })}</p> : null}</CategoryBox>;
}

export function AtomsPerCellExercise({ activity, symbol, seed }: { activity: Activity; symbol: string; seed: number }) {
  const { t, compact } = useI18n();
  const { r, error } = useStructure(symbol);
  const { log, attempt } = useAttempts(activity, seed, symbol);
  const [fractions, setFractions] = useState<Record<string, string>>({});
  const [nIn, setN] = useState('');
  const [res, setRes] = useState<{ correct: boolean; type?: ErrorType } | null>(null);
  if (error) return <p role="alert">{t('exercise.engineNeeded')}</p>;
  if (!r) return <Spinner size={22} label={t('common.loading')} />;
  return (
    <Shell activity={activity} log={log} done={Boolean(res?.correct)}>
      <p>{t('exercise.atoms.statement', { name: r.rotulo, structure: r.estrutura })} <OpenInLab symbol={symbol} /></p>
      <CategoryBox category="reference"><CategoryTag category="reference" label={t('exercise.dataFromEngine')} />
        <table className="ds-table"><thead><tr><th scope="col">{t('exercise.atoms.position')}</th><th scope="col">{t('exercise.atoms.quantity')}</th><th scope="col">{t('exercise.atoms.fraction')}</th></tr></thead>
          <tbody>{r.contagem.map((g) => (
            <tr key={g.tipo}><th scope="row">{t(SITE_KEYS[g.tipo])}</th><td>{g.quantidade}</td>
              <td><TextInput label={t('exercise.atoms.fractionOf', { site: t(SITE_KEYS[g.tipo]) })} hideLabel value={fractions[g.tipo] ?? ''} onChange={(e) => setFractions((f) => ({ ...f, [g.tipo]: e.target.value }))} placeholder="1/8" data-testid={`frac-${g.tipo}`} /></td></tr>
          ))}</tbody></table>
      </CategoryBox>
      <TextInput label={t('exercise.atoms.total')} inputMode="numeric" value={nIn} onChange={(e) => setN(e.target.value)} data-testid="in-n" />
      <Button variant="primary" data-testid="exercise-check" onClick={() => {
        const fracOk = r.contagem.every((g) => (fractions[g.tipo] ?? '').replace(/\s/g, '') === g.fracao_txt);
        const nv = parseUserNumber(nIn);
        const out: { correct: boolean; type?: ErrorType } = nv === null || Number.isNaN(nv) ? { correct: false, type: 'input' } : !fracOk ? { correct: false, type: 'conceptual' } : nv === r.n ? { correct: true } : { correct: false, type: 'algebraic' };
        setRes(out); attempt('n', out); announce(out.correct ? t('exercise.correct') : t(`exercise.error.${out.type ?? 'algebraic'}`));
      }}>{t('exercise.check')}</Button>
      <Feedback res={res} />
      {res?.correct ? <p>{r.contagem.map((g) => `${g.quantidade} × ${g.fracao_txt} = ${compact(g.contribuicao)}`).join(' + ')} = {r.n}</p> : null}
    </Shell>
  );
}

export function ApfExercise({ activity, symbol, seed }: { activity: Activity; symbol: string; seed: number }) {
  const { t, num } = useI18n();
  const { r, error } = useStructure(symbol);
  const { log, attempt } = useAttempts(activity, seed, symbol);
  const [fea, setFea] = useState('');
  const [res, setRes] = useState<{ correct: boolean; type?: ErrorType; power?: number } | null>(null);
  const [others, setOthers] = useState<number[]>([]);
  useEffect(() => { crystalabApi.structures().then((rows) => setOthers(rows.map((x) => x.fea))).catch(() => undefined); }, []);
  if (error) return <p role="alert">{t('exercise.engineNeeded')}</p>;
  if (!r) return <Spinner size={22} label={t('common.loading')} />;
  return (
    <Shell activity={activity} log={log} done={Boolean(res?.correct)}>
      <p>{t('exercise.apf.statement', { name: r.rotulo, structure: r.estrutura })} <OpenInLab symbol={symbol} /></p>
      <CategoryBox category="reference"><CategoryTag category="reference" label={t('exercise.dataFromEngine')} />
        <dl className="guided__dl"><dt>n</dt><dd>{r.n}</dd><dt>{t('comparison.relation')}</dt><dd>{r.relacao_a}</dd><dt>V_C</dt><dd>a³</dd></dl></CategoryBox>
      <p className="ds-field__hint">{t('exercise.apf.noSteps')}</p>
      <TextInput label={t('metrics.apf')} inputMode="decimal" value={fea} onChange={(e) => setFea(e.target.value)} data-testid="in-fea" />
      <Button variant="primary" data-testid="exercise-check" onClick={() => {
        const out = classifyAnswer(parseUserNumber(fea), r.fea, 0.01, others.filter((v) => Math.abs(v - r.fea) > 1e-6));
        setRes(out); attempt('fea', out); announce(out.correct ? t('exercise.correct') : t(`exercise.error.${out.type ?? 'algebraic'}`));
      }}>{t('exercise.check')}</Button>
      <Feedback res={res} />
      {res?.correct ? <p>{t('exercise.apf.engineValue', { value: num(r.fea, 4) })}</p> : null}
    </Shell>
  );
}

const PLANE_POOL = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]];
const DIR_POOL = [[1, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 1], [1, 1, 1], [0, 1, 1], [1, -1, 0]];

function sameIndices(a: number[], b: number[], allowSign: boolean): boolean {
  if (a.length !== b.length) return false;
  if (a.every((v, i) => v === b[i])) return true;
  return allowSign && a.every((v, i) => v === -(b[i] as number));
}

export function MillerExercise({ activity, symbol, seed, kind }: { activity: Activity; symbol: string; seed: number; kind: 'plano' | 'direcao' }) {
  const { t, num } = useI18n();
  const [r, setR] = useState<StructureResult | null>(null);
  const [m, setM] = useState<MillerPlane | MillerDirection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const target = useMemo(() => createRng(seed).pick(kind === 'plano' ? PLANE_POOL : DIR_POOL) as number[], [seed, kind]);
  const { log, attempt } = useAttempts(activity, seed, symbol);
  const [idx, setIdx] = useState(['', '', '']);
  const [res, setRes] = useState<{ correct: boolean; type?: ErrorType } | null>(null);
  useEffect(() => {
    const ctrl = new AbortController();
    (async () => {
      const s = await crystalabApi.structure({ nome: symbol }, ctrl.signal);
      const mm = await crystalabApi.miller({ estrutura: s.estrutura, tipo: kind, indices: target, a_nm: s.a_nm, c_a: s.c_a }, ctrl.signal);
      setR(s); setM(mm);
    })().catch((e: unknown) => { if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : String(e)); });
    return () => ctrl.abort();
  }, [symbol, kind, target]);
  if (error) return <p role="alert">{t('exercise.engineNeeded')}</p>;
  if (!r || !m) return <Spinner size={22} label={t('common.loading')} />;
  const fmtP = (p: number[]) => `(${p.map((v) => num(v, 2)).join('; ')})`;
  return (
    <Shell activity={activity} log={log} done={Boolean(res?.correct)}>
      <p>{t(kind === 'plano' ? 'exercise.miller.planeStatement' : 'exercise.miller.dirStatement', { name: r.rotulo })} <OpenInLab symbol={symbol} overlay={{ t: kind === 'plano' ? 'p' : 'd', i: target }} /></p>
      <CategoryBox category="reference"><CategoryTag category="reference" label={t('exercise.dataFromEngine')} />
        {m.tipo === 'plano' ? (
          <><p>{t('exercise.miller.vertices')}</p><ul className="ds-mono">{m.poligono.map((p, i) => <li key={i}>{fmtP(p)}</li>)}</ul></>
        ) : (
          <dl className="guided__dl"><dt>{t('exercise.miller.tail')}</dt><dd className="ds-mono">{fmtP(m.inicio)}</dd><dt>{t('exercise.miller.head')}</dt><dd className="ds-mono">{fmtP(m.fim)}</dd></dl>
        )}
        <p className="ds-field__hint">{t('exercise.miller.units')}</p>
      </CategoryBox>
      <div className="guided__indices" role="group" aria-label={t('miller.indices')}>
        {(kind === 'plano' ? ['h', 'k', 'l'] : ['u', 'v', 'w']).map((l, i) => (
          <TextInput key={l} label={l} inputMode="numeric" className="guided__index" value={idx[i] ?? ''} onChange={(e) => setIdx((c) => c.map((v, j) => (j === i ? e.target.value : v)))} data-testid={`in-${l}`} />
        ))}
      </div>
      <Button variant="primary" data-testid="exercise-check" onClick={() => {
        const vals = idx.map((v) => parseUserNumber(v));
        let out: { correct: boolean; type?: ErrorType };
        if (vals.some((v) => v === null || Number.isNaN(v) || !Number.isInteger(v))) out = { correct: false, type: 'input' };
        else {
          const ints = vals as number[];
          const engine = m.indices;
          if (sameIndices(ints, engine, kind === 'plano')) out = { correct: true };
          else if (ints.length === 3 && engine.length === 3 && ints.every((v, i) => Math.abs(v) === Math.abs(engine[i] as number))) out = { correct: false, type: 'algebraic' };
          else out = { correct: false, type: 'conceptual' };
        }
        setRes(out); attempt(kind, out); announce(out.correct ? t('exercise.correct') : t(`exercise.error.${out.type ?? 'algebraic'}`));
      }}>{t('exercise.check')}</Button>
      <Feedback res={res} />
      {res?.correct ? <p lang="pt-BR">{m.notacao} — {m.tipo === 'plano' ? `d = ${num(m.d_nm ?? m.d_rel, 4)} ${m.d_nm ? 'nm' : 'a'}` : `|v| = ${num(m.comprimento_nm ?? m.comprimento_rel, 4)} ${m.comprimento_nm ? 'nm' : 'a'}`}</p> : null}
    </Shell>
  );
}
