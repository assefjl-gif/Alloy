/**
 * Aprendizagem Baseada em Problemas (6.8/6.9): situação-problema, objetivo investigativo,
 * evidências disponíveis, questões orientadoras, hipóteses, exploração no laboratório,
 * registro, conclusão e reflexão. Evidências são classificadas como observação, cálculo ou
 * interpretação; hipóteses podem ser comparadas. Nada aqui é um formulário rígido: os campos
 * são livres e salvos no diário.
 */
import { useEffect, useState } from 'react';
import { useI18n, pick } from '../../i18n/index.ts';
import { crystalabApi } from '../../services/api/crystalab.ts';
import type { StructureResult } from '../../services/api/contracts.ts';
import { Button, IconButton } from '../../design-system/primitives/Button.tsx';
import { Select, TextArea } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, CategoryTag } from '../../design-system/primitives/Category.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { uid } from '../../utils/id.ts';
import { readJSON, writeJSON } from '../../utils/storage.ts';
import { announce } from '../../design-system/announce.ts';
import { encodeScene } from '../../features/url/sceneUrl.ts';
import type { Activity } from './model.ts';
import { useDidactics } from './store.ts';
import { addNote } from '../notebook/store.ts';

type EvidenceKind = 'observation' | 'calculation' | 'interpretation';
interface Evidence { id: string; kind: EvidenceKind; text: string; hypothesis: string | null; supports: boolean }
interface Hypothesis { id: string; text: string }
interface PblState { hypotheses: Hypothesis[]; evidence: Evidence[]; conclusion: string; reflection: string }

const KEY = (id: string) => `alloy.pbl.${id}`;

export function PblActivity({ activity }: { activity: Activity }) {
  const { t, num, locale } = useI18n();
  const complete = useDidactics((s) => s.complete);
  const record = useDidactics((s) => s.record);
  const [data, setData] = useState<{ al: StructureResult; cu: StructureResult } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [st, setSt] = useState<PblState>(() => readJSON<PblState>(KEY(activity.id), { hypotheses: [], evidence: [], conclusion: '', reflection: '' }));
  const [hText, setHText] = useState('');
  const [eText, setEText] = useState('');
  const [eKind, setEKind] = useState<EvidenceKind>('observation');
  const [eHyp, setEHyp] = useState('');
  const [eSupports, setESupports] = useState('true');
  useEffect(() => { writeJSON(KEY(activity.id), st); }, [st, activity.id]);
  useEffect(() => {
    const ctrl = new AbortController();
    Promise.all([crystalabApi.structure({ nome: 'Al' }, ctrl.signal), crystalabApi.structure({ nome: 'Cu' }, ctrl.signal)])
      .then(([al, cu]) => setData({ al, cu }))
      .catch((e: unknown) => { if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : String(e)); });
    return () => ctrl.abort();
  }, []);
  const kinds = new Set(st.evidence.map((e) => e.kind));
  const mentions = ['n', 'A', 'Vc'].every((k) => new RegExp(`\\b${k}\\b`, 'i').test(st.conclusion) || (k === 'Vc' && /volume/i.test(st.conclusion)) || (k === 'A' && /massa/i.test(st.conclusion)));
  const ready = kinds.size === 3 && st.conclusion.trim().length > 20;
  return (
    <div className="pbl" data-testid="pbl">
      <CategoryBox category="feedback" as="section" aria-labelledby="pbl-situation">
        <h2 id="pbl-situation">{t('pbl.situation')}</h2>
        <p>{t('pbl.alcu.situation')}</p>
        <p><strong>{t('pbl.objective')}:</strong> {pick(activity.objective, locale)}</p>
      </CategoryBox>

      <section aria-labelledby="pbl-evidence" className="pbl__section">
        <h2 id="pbl-evidence">{t('pbl.available')}</h2>
        {error ? <p role="alert">{t('exercise.engineNeeded')}</p> : !data ? <Spinner size={20} label={t('common.loading')} /> : (
          <CategoryBox category="reference">
            <CategoryTag category="reference" label={t('exercise.dataFromEngine')} />
            <div className="ds-table-wrap"><table className="ds-table">
              <thead><tr><th scope="col">{t('pbl.metal')}</th><th scope="col">{t('metrics.structure')}</th><th scope="col">R (nm)</th><th scope="col">A (g/mol)</th><th scope="col">n</th><th scope="col">a (nm)</th><th scope="col">ρ exp (g/cm³)</th></tr></thead>
              <tbody>{[data.al, data.cu].map((r) => <tr key={r.rotulo}><th scope="row" lang="pt-BR">{r.rotulo}</th><td>{r.estrutura}</td><td>{num(r.raio_nm, 4)}</td><td>{num(r.peso, 2)}</td><td>{r.n}</td><td>{num(r.a_nm, 4)}</td><td>{num(r.densidade_exp, 2)}</td></tr>)}</tbody>
            </table></div>
            <p className="ds-field__hint">{t('pbl.densityHidden')}</p>
          </CategoryBox>
        )}
        <div className="ds-row">
          <a className="ds-btn ds-btn--secondary ds-btn--sm" href={`#/crystalab?s=${encodeScene({ v: 1, m: { nome: 'Al' }, dn: 1 })}`}>{t('pbl.exploreAl')}</a>
          <a className="ds-btn ds-btn--secondary ds-btn--sm" href={`#/crystalab?s=${encodeScene({ v: 1, m: { nome: 'Cu' }, dn: 1 })}`}>{t('pbl.exploreCu')}</a>
        </div>
      </section>

      <section aria-labelledby="pbl-questions" className="pbl__section">
        <h2 id="pbl-questions">{t('pbl.guiding')}</h2>
        <ol><li>{t('pbl.alcu.q1')}</li><li>{t('pbl.alcu.q2')}</li><li>{t('pbl.alcu.q3')}</li></ol>
      </section>

      <section aria-labelledby="pbl-hyp" className="pbl__section">
        <h2 id="pbl-hyp">{t('pbl.hypotheses')}</h2>
        <form className="pbl__add" onSubmit={(e) => { e.preventDefault(); if (!hText.trim()) return; setSt((s) => ({ ...s, hypotheses: [...s.hypotheses, { id: uid('h'), text: hText.trim() }] })); setHText(''); announce(t('pbl.hypothesisAdded')); }}>
          <TextArea label={t('pbl.newHypothesis')} value={hText} onChange={(e) => setHText(e.target.value)} rows={2} data-testid="pbl-hyp-input" />
          <Button type="submit" size="sm" icon="plus">{t('pbl.add')}</Button>
        </form>
        <ul className="pbl__list">
          {st.hypotheses.map((h, i) => {
            const pro = st.evidence.filter((e) => e.hypothesis === h.id && e.supports).length;
            const con = st.evidence.filter((e) => e.hypothesis === h.id && !e.supports).length;
            return <li key={h.id} className="ds-cat-box ds-cat-box--note pbl__hyp"><strong>H{i + 1}</strong> {h.text} <span className="ds-badge ds-badge--success">+{pro}</span> <span className="ds-badge ds-badge--danger">−{con}</span>
              <IconButton size="sm" icon="trash" label={t('pbl.removeHypothesis', { n: i + 1 })} onClick={() => setSt((s) => ({ ...s, hypotheses: s.hypotheses.filter((x) => x.id !== h.id), evidence: s.evidence.map((e) => (e.hypothesis === h.id ? { ...e, hypothesis: null } : e)) }))} /></li>;
          })}
        </ul>
        {st.hypotheses.length > 1 ? <p className="ds-field__hint">{t('pbl.compareHint')}</p> : null}
      </section>

      <section aria-labelledby="pbl-record" className="pbl__section">
        <h2 id="pbl-record">{t('pbl.record')}</h2>
        <form className="pbl__evidence-form" onSubmit={(e) => { e.preventDefault(); if (!eText.trim()) return; setSt((s) => ({ ...s, evidence: [...s.evidence, { id: uid('e'), kind: eKind, text: eText.trim(), hypothesis: eHyp || null, supports: eSupports === 'true' }] })); setEText(''); announce(t('pbl.evidenceAdded')); }}>
          <TextArea label={t('pbl.evidenceText')} value={eText} onChange={(e) => setEText(e.target.value)} rows={2} data-testid="pbl-evidence-input" />
          <Select label={t('pbl.evidenceKind')} value={eKind} onChange={(e) => setEKind(e.target.value as EvidenceKind)} options={[{ value: 'observation', label: t('pbl.kind.observation') }, { value: 'calculation', label: t('pbl.kind.calculation') }, { value: 'interpretation', label: t('pbl.kind.interpretation') }]} data-testid="pbl-evidence-kind" />
          <Select label={t('pbl.relatesTo')} value={eHyp} onChange={(e) => setEHyp(e.target.value)} options={[{ value: '', label: t('pbl.noHypothesis') }, ...st.hypotheses.map((h, i) => ({ value: h.id, label: `H${i + 1}` }))]} />
          <Select label={t('pbl.effect')} value={eSupports} onChange={(e) => setESupports(e.target.value)} options={[{ value: 'true', label: t('pbl.supports') }, { value: 'false', label: t('pbl.contradicts') }]} />
          <Button type="submit" size="sm" icon="plus">{t('pbl.add')}</Button>
        </form>
        <ul className="pbl__list">
          {st.evidence.map((e) => <li key={e.id} className={`pbl__ev pbl__ev--${e.kind}`}><span className="ds-badge">{t(`pbl.kind.${e.kind}`)}</span> {e.text}</li>)}
        </ul>
        <p className="ds-field__hint">{t('pbl.kindsCount', { n: kinds.size })}</p>
      </section>

      <section aria-labelledby="pbl-concl" className="pbl__section">
        <h2 id="pbl-concl">{t('pbl.conclusion')}</h2>
        <TextArea label={t('pbl.conclusionLabel')} value={st.conclusion} onChange={(e) => setSt((s) => ({ ...s, conclusion: e.target.value }))} rows={4} hint={mentions ? t('pbl.mentionsOk') : t('pbl.mentionsHint')} data-testid="pbl-conclusion" />
        <TextArea label={t('pbl.reflectionLabel')} value={st.reflection} onChange={(e) => setSt((s) => ({ ...s, reflection: e.target.value }))} rows={3} />
      </section>

      <div className="ds-row">
        <Button variant="primary" icon="check" disabled={!ready} data-testid="pbl-complete" onClick={() => {
          complete(activity.id);
          record({ activityId: activity.id, topic: activity.topic, step: 'conclusao', correct: mentions, ...(mentions ? {} : { errorType: 'conceptual' as const }), seed: 0 });
          addNote({ kind: 'conclusion', title: pick(activity.title, locale), body: `${st.conclusion}\n\n${t('pbl.reflectionLabel')}: ${st.reflection}`, activityId: activity.id });
          announce(t('exercise.completed'));
        }}>{t('pbl.finish')}</Button>
        {!ready ? <p className="ds-field__hint">{t('pbl.finishHint')}</p> : null}
      </div>
      {ready ? <CategoryBox category="feedback"><p>{pick(activity.explanation, locale)}</p><cite>{activity.references.join(' · ')}</cite></CategoryBox> : null}
    </div>
  );
}
