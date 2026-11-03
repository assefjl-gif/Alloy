/**
 * Painel do professor (6.15–6.18) — DEMONSTRATIVO. Não há serviço de turmas (D-03):
 *  - "Dados demonstrativos": turma fictícia com semente fixa, selada em toda a tela;
 *  - "Dados deste navegador": tentativas reais registradas localmente (um único estudante);
 *  - Publicar tarefa: a chamada ao adaptador sempre falha e a interface diz que NADA foi publicado.
 * Exportação PDF/Word só é habilitada quando há dados válidos para o modo escolhido.
 */
import { useMemo, useState } from 'react';
import { useI18n, pick } from '../../i18n/index.ts';
import { Button, IconButton } from '../../design-system/primitives/Button.tsx';
import { Segmented, Select, TextArea, TextInput } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, DemoSeal } from '../../design-system/primitives/Category.tsx';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { Panel } from '../../design-system/layout/Panel.tsx';
import { MetricCard } from '../../design-system/layout/MetricCard.tsx';
import { announce } from '../../design-system/announce.ts';
import { toast } from '../../stores/toast.ts';
import { demoClasses, demoCompletion, demoStepErrors, demoTopics, publishAssignment, CLASSROOM_DEMO_SEED, type StepErrors, type TopicDifficulty } from '../../services/adapters/classroom.ts';
import { ACTIVITIES, activityById } from '../didactics/bank.ts';
import { deleteDraft, listDrafts, saveDraft } from './drafts.ts';
import { useDidactics, progressByTopic } from '../didactics/store.ts';
import { exportDocx, exportPdf, reportHasData, type ReportData } from './report.ts';

type Source = 'demo' | 'local';

function Bars({ items, label }: { items: Array<{ label: string; value: number; detail: string }>; label: string }) {
  const max = Math.max(1, ...items.map((i) => i.value));
  return (
    <figure className="bars" aria-label={label}>
      <ul>
        {items.map((i) => (
          <li key={i.label} className="bars__row">
            <span className="bars__label">{i.label}</span>
            <span className="bars__track" aria-hidden="true"><span className="bars__fill" style={{ width: `${(i.value / max) * 100}%` }} /></span>
            <span className="bars__value">{i.detail}</span>
          </li>
        ))}
      </ul>
    </figure>
  );
}

export default function InstructorModule() {
  const { t, num, locale } = useI18n();
  const [source, setSource] = useState<Source>('demo');
  const attempts = useDidactics((s) => s.attempts);
  const completed = useDidactics((s) => s.completed);
  const [assignActivity, setAssignActivity] = useState(ACTIVITIES[0]?.id ?? '');
  const [assignClass, setAssignClass] = useState('t1');
  const [due, setDue] = useState('');
  const [instructions, setInstructions] = useState('');
  const [drafts, setDrafts] = useState(listDrafts);
  const [publishState, setPublishState] = useState<'idle' | 'sending' | 'failed'>('idle');
  const [busy, setBusy] = useState(false);

  const local = useMemo(() => {
    const stepMap = new Map<string, StepErrors>();
    for (const a of attempts) {
      const s = stepMap.get(a.step) ?? { step: a.step, attempts: 0, errors: 0 };
      s.attempts += 1;
      if (!a.correct) s.errors += 1;
      stepMap.set(a.step, s);
    }
    const topics: TopicDifficulty[] = progressByTopic(attempts).map((p) => ({ topic: p.topic, attempts: p.attempts, errorRate: p.attempts ? (p.attempts - p.correct) / p.attempts : 0 }));
    return { steps: Array.from(stepMap.values()), topics, completion: { completed: completed.length, total: ACTIVITIES.length } };
  }, [attempts, completed]);

  const data = source === 'demo' ? { steps: demoStepErrors(), topics: demoTopics(), completion: demoCompletion() } : local;
  const hasData = data.steps.length > 0 || data.topics.length > 0;
  const stepLabel = (s: string) => (['dados', 'grandezas', 'equacao', 'substituicao', 'validacao', 'motor', 'revisao'].includes(s) ? t(`exercise.step.${s as 'dados'}`) : s);

  const report: ReportData = {
    title: t('instructor.reportTitle'),
    subtitle: source === 'demo' ? t('instructor.sourceDemo') : t('instructor.sourceLocal'),
    demo: source === 'demo',
    demoNotice: t('instructor.demoNotice', { seed: CLASSROOM_DEMO_SEED }),
    generatedAt: new Intl.DateTimeFormat(locale, { dateStyle: 'long', timeStyle: 'short' }).format(new Date()),
    sections: [
      { heading: t('instructor.stepErrors'), columns: [t('instructor.step'), t('progress.attempts'), t('instructor.errors')], rows: data.steps.map((s) => ({ label: stepLabel(s.step), values: [s.attempts, s.errors] })) },
      { heading: t('instructor.topics'), columns: [t('progress.topic'), t('progress.attempts'), t('instructor.errorRate')], rows: data.topics.map((tp) => ({ label: t(`topic.${tp.topic}`), values: [tp.attempts, `${num(tp.errorRate * 100, 0)} %`] })), note: t('instructor.noRanking') },
    ],
  };

  const publish = async () => {
    setPublishState('sending');
    try {
      await publishAssignment({ activity: assignActivity, class: assignClass, due, instructions });
    } catch {
      setPublishState('failed');
      announce(t('instructor.publishFailed'), 'assertive');
      toast({ tone: 'error', title: t('instructor.publishFailedTitle'), body: t('instructor.publishFailed') });
    }
  };

  return (
    <Workbench
      className="instructor"
      center={
        <main id="main-content" tabIndex={-1} className="module-main" data-testid="instructor">
          <header className="module-head">
            <h1>{t('instructor.title')}</h1>
            <p className="module-head__lead">{t('instructor.lead')}</p>
            <Segmented name="instructor-source" label={t('instructor.source')} value={source} onChange={setSource} options={[{ value: 'demo', label: t('instructor.sourceDemo') }, { value: 'local', label: t('instructor.sourceLocal') }]} />
          </header>
          {source === 'demo' ? <CategoryBox category="demo" className="demo-banner"><DemoSeal text={t('common.demo')} /><p>{t('instructor.demoNotice', { seed: CLASSROOM_DEMO_SEED })}</p></CategoryBox> : <CategoryBox category="note"><p>{t('instructor.localNotice')}</p></CategoryBox>}

          <div className="metrics-row">
            <MetricCard label={t('instructor.completion')} value={`${data.completion.completed}/${data.completion.total}`} category={source === 'demo' ? 'demo' : 'result'} categoryLabel={source === 'demo' ? t('common.demo') : t('instructor.local')} testId="metric-completion" />
            <MetricCard label={t('instructor.classes')} value={source === 'demo' ? String(demoClasses().length) : '—'} category={source === 'demo' ? 'demo' : 'note'} categoryLabel={source === 'demo' ? t('common.demo') : t('instructor.noService')} />
          </div>

          {!hasData ? <p className="empty-state" data-testid="instructor-empty">{t('instructor.empty')}</p> : (
            <>
              <section aria-labelledby="ins-steps" className="ds-stack">
                <h2 id="ins-steps">{t('instructor.stepErrors')}</h2>
                <Bars label={t('instructor.stepErrors')} items={data.steps.map((s) => ({ label: stepLabel(s.step), value: s.attempts ? s.errors / s.attempts : 0, detail: `${s.errors}/${s.attempts}` }))} />
                <details><summary>{t('common.dataTable')}</summary>
                  <div className="ds-table-wrap"><table className="ds-table"><thead><tr><th scope="col">{t('instructor.step')}</th><th scope="col">{t('progress.attempts')}</th><th scope="col">{t('instructor.errors')}</th></tr></thead>
                    <tbody>{data.steps.map((s) => <tr key={s.step}><th scope="row">{stepLabel(s.step)}</th><td>{s.attempts}</td><td>{s.errors}</td></tr>)}</tbody></table></div>
                </details>
              </section>
              <section aria-labelledby="ins-topics" className="ds-stack">
                <h2 id="ins-topics">{t('instructor.topics')}</h2>
                <Bars label={t('instructor.topics')} items={data.topics.map((tp) => ({ label: t(`topic.${tp.topic}`), value: tp.errorRate, detail: `${num(tp.errorRate * 100, 0)} %` }))} />
                <p className="ds-field__hint">{t('instructor.noRanking')}</p>
              </section>
            </>
          )}

          <div className="ds-row">
            <Button icon="print" disabled={!reportHasData(report)} onClick={exportPdf} data-testid="instructor-pdf">{t('instructor.exportPdf')}</Button>
            <Button icon="file" disabled={!reportHasData(report) || busy} data-testid="instructor-docx" onClick={async () => {
              setBusy(true);
              try { await exportDocx(report, source === 'demo' ? 'relatorio-turma-DEMONSTRATIVO.docx' : 'relatorio-local.docx'); announce(t('instructor.exported')); } catch (e) { toast({ tone: 'error', title: t('instructor.exportFailed'), body: e instanceof Error ? e.message : String(e) }); } finally { setBusy(false); }
            }}>{t('instructor.exportDocx')}</Button>
            {!reportHasData(report) ? <p className="ds-field__hint">{t('instructor.exportNeedsData')}</p> : null}
          </div>
        </main>
      }
      side={
        <Panel title={t('instructor.assign')} id="assign" testId="assign-panel" className="ds-panel--padded">
          <form className="ds-stack" onSubmit={(e) => { e.preventDefault(); void publish(); }}>
            <Select label={t('instructor.activity')} value={assignActivity} onChange={(e) => setAssignActivity(e.target.value)} options={ACTIVITIES.map((a) => ({ value: a.id, label: pick(a.title, locale) }))} />
            <Select label={t('instructor.class')} value={assignClass} onChange={(e) => setAssignClass(e.target.value)} options={demoClasses().map((c) => ({ value: c.id, label: c.name }))} hint={t('instructor.classesDemo')} />
            <TextInput type="date" label={t('instructor.due')} value={due} onChange={(e) => setDue(e.target.value)} />
            <TextArea label={t('instructor.instructions')} rows={3} value={instructions} onChange={(e) => setInstructions(e.target.value)} hint={t('instructor.instructionsHint')} data-testid="assign-instructions" />
            <details className="criteria"><summary>{t('learn.criteria')}</summary><ul>{(activityById(assignActivity)?.criteria ?? []).map((c) => <li key={c.id}>{pick(c.text, locale)}</li>)}</ul></details>
            <div className="ds-row">
              <Button icon="check" onClick={() => { const d = saveDraft({ activityId: assignActivity, classId: assignClass, due, instructions }); setDrafts(listDrafts()); announce(t('instructor.draftSaved', { id: d.id })); }} data-testid="save-draft">{t('instructor.saveDraft')}</Button>
              <Button type="submit" variant="primary" icon="share" disabled={publishState === 'sending'} data-testid="publish-button">{t('instructor.publish')}</Button>
            </div>
          </form>
          {drafts.length ? (
            <section aria-labelledby="drafts-h" data-testid="drafts">
              <h3 id="drafts-h">{t('instructor.drafts')}</h3>
              <ul className="ws-list">{drafts.map((d) => <li key={d.id} className="ws-item"><div><strong>{pick(activityById(d.activityId)?.title ?? d.activityId, locale)}</strong><small>{demoClasses().find((c) => c.id === d.classId)?.name ?? d.classId}{d.due ? ` · ${d.due}` : ''} · {t('instructor.draftLocal')}</small></div><IconButton size="sm" icon="trash" label={t('instructor.deleteDraft')} onClick={() => { deleteDraft(d.id); setDrafts(listDrafts()); }} /></li>)}</ul>
            </section>
          ) : null}
          {publishState === 'failed' ? (
            <CategoryBox category="feedback" role="alert" data-testid="publish-result">
              <p><Badge tone="danger">{t('instructor.notPublished')}</Badge> {t('instructor.publishFailed')}</p>
            </CategoryBox>
          ) : <p className="ds-field__hint">{t('instructor.publishHint')}</p>}
        </Panel>
      }
      sideInline
      sideLabel={t('instructor.assign')}
    />
  );
}
