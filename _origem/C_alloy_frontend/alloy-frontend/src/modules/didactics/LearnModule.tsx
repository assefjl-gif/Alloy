/**
 * Módulo "Aprender" (#/aprender[/<atividade>]?seed=N). Lista o banco de atividades com filtros,
 * abre cada uma com material escolhido por semente reproduzível e mostra o progresso do
 * estudante por tópico — sem ranking e sem comparação entre estudantes (6.11).
 */
import { useMemo, useState } from 'react';
import { useI18n, pick } from '../../i18n/index.ts';
import { useRoute, hrefFor, navigate } from '../../app/router.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useCapabilities } from '../../stores/capabilities.ts';
import { createRng } from '../../utils/rng.ts';
import { chooseMaterial, defaultSeed } from './seed.ts';
import { Button } from '../../design-system/primitives/Button.tsx';
import { Select } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, CategoryTag } from '../../design-system/primitives/Category.tsx';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { Panel } from '../../design-system/layout/Panel.tsx';
import { Icon } from '../../design-system/Icon.tsx';
import { aiAdapter } from '../../services/adapters/ai.ts';
import { ACTIVITIES, activityById } from './bank.ts';
import type { Activity, Format, Level, Topic } from './model.ts';
import { useDidactics, progressByTopic, reviewRecommendations } from './store.ts';
import { DensityExercise } from './DensityExercise.tsx';
import { AtomsPerCellExercise, ApfExercise, MillerExercise } from './GuidedExercises.tsx';
import { PblActivity } from './PblActivity.tsx';
import { QuizPanel } from './QuizPanel.tsx';

const TOPICS: Topic[] = ['estruturas', 'celulas', 'fea', 'densidade', 'miller-planos', 'miller-direcoes', 'hea-parametros'];

function ActivityBody({ activity, seed, symbol }: { activity: Activity; seed: number; symbol: string }) {
  switch (activity.id) {
    case 'densidade-cobre':
    case 'densidade-sorteada':
      return <DensityExercise activity={activity} symbol={symbol} seed={seed} key={`${symbol}-${seed}`} />;
    case 'atomos-por-celula':
      return <AtomsPerCellExercise activity={activity} symbol={symbol} seed={seed} key={`${symbol}-${seed}`} />;
    case 'fea':
      return <ApfExercise activity={activity} symbol={symbol} seed={seed} key={`${symbol}-${seed}`} />;
    case 'plano-miller':
      return <MillerExercise activity={activity} symbol={symbol} seed={seed} kind="plano" key={`${symbol}-${seed}`} />;
    case 'direcao-miller':
      return <MillerExercise activity={activity} symbol={symbol} seed={seed} kind="direcao" key={`${symbol}-${seed}`} />;
    default:
      if (activity.format === 'pbl') return <PblActivity activity={activity} />;
      return <QuizPanel activity={activity} seed={seed} key={seed} />;
  }
}

function AiAssist() {
  const { t } = useI18n();
  return (
    <CategoryBox category="feedback" className="ai-assist" data-testid="ai-assist">
      <p><Icon name="sparkles" size={16} /> <strong>{t('ai.title')}</strong> <Badge>{t('ai.off')}</Badge></p>
      <p className="ds-field__hint">{t('ai.reason')}</p>
      <Button size="sm" variant="ghost" disabled aria-describedby="ai-off-reason">{t('ai.ask')}</Button>
      <span id="ai-off-reason" className="sr-only">{aiAdapter.reason === 'not-configured' ? t('ai.reason') : ''}</span>
    </CategoryBox>
  );
}

export function ProgressPanel() {
  const { t, locale } = useI18n();
  const attempts = useDidactics((s) => s.attempts);
  const completed = useDidactics((s) => s.completed);
  const reset = useDidactics((s) => s.reset);
  const prog = useMemo(() => progressByTopic(attempts), [attempts]);
  const recs = useMemo(() => reviewRecommendations(attempts, completed, ACTIVITIES), [attempts, completed]);
  return (
    <Panel title={t('progress.title')} id="progress" testId="progress-panel" headingLevel={2} className="ds-panel--padded">
      <p className="ds-field__hint">{t('progress.private')}</p>
      <p>{t('progress.completed', { n: completed.length, total: ACTIVITIES.length })}</p>
      {prog.length === 0 ? <p className="empty-state">{t('progress.empty')}</p> : (
        <div className="ds-table-wrap"><table className="ds-table">
          <caption className="sr-only">{t('progress.caption')}</caption>
          <thead><tr><th scope="col">{t('progress.topic')}</th><th scope="col">{t('progress.attempts')}</th><th scope="col">{t('progress.correct')}</th><th scope="col">{t('progress.mainError')}</th></tr></thead>
          <tbody>{prog.map((p) => {
            const main = Object.entries(p.errors).sort((a, b) => b[1] - a[1])[0];
            return <tr key={p.topic}><th scope="row">{t(`topic.${p.topic}`)}</th><td>{p.attempts}</td><td>{p.correct}</td><td>{main ? `${t(`exercise.error.${main[0] as 'input'}`)} (${main[1]})` : '—'}</td></tr>;
          })}</tbody>
        </table></div>
      )}
      {recs.length ? (
        <CategoryBox category="feedback" data-testid="review-recs">
          <strong>{t('progress.review')}</strong>
          <ul>{recs.map((r) => { const a = activityById(r.activityId)!; return <li key={r.topic}><a href={hrefFor('aprender', [a.id])}>{pick(a.title, locale)}</a> — {t(`topic.${r.topic}`)} ({t('progress.rate', { pct: Math.round(r.rate * 100) })})</li>; })}</ul>
        </CategoryBox>
      ) : null}
      {completed.length ? <ul className="seals" aria-label={t('progress.seals')}>{completed.map((id) => { const a = activityById(id); return a ? <li key={id}><Badge tone="success">✓ {pick(a.title, locale)}</Badge></li> : null; })}</ul> : null}
      <Button size="sm" variant="ghost" icon="trash" onClick={reset} disabled={!attempts.length}>{t('progress.reset')}</Button>
    </Panel>
  );
}

function ActivityList() {
  const { t, locale } = useI18n();
  const completed = useDidactics((s) => s.completed);
  const [topic, setTopic] = useState<Topic | 'all'>('all');
  const [level, setLevel] = useState<Level | 'all'>('all');
  const [format, setFormat] = useState<Format | 'all'>('all');
  const list = ACTIVITIES.filter((a) => (topic === 'all' || a.topic === topic) && (level === 'all' || a.level === level) && (format === 'all' || a.format === format));
  return (
    <>
      <header className="module-head">
        <h1>{t('learn.title')}</h1>
        <p className="module-head__lead">{t('learn.lead')}</p>
      </header>
      <div className="learn__filters" role="group" aria-label={t('learn.filters')}>
        <Select label={t('progress.topic')} value={topic} onChange={(e) => setTopic(e.target.value as Topic | 'all')} options={[{ value: 'all', label: t('learn.all') }, ...TOPICS.map((x) => ({ value: x, label: t(`topic.${x}`) }))]} />
        <Select label={t('learn.level')} value={level} onChange={(e) => setLevel(e.target.value as Level | 'all')} options={[{ value: 'all', label: t('learn.all') }, ...(['introdutorio', 'intermediario', 'avancado'] as Level[]).map((x) => ({ value: x, label: t(`level.${x}`) }))]} />
        <Select label={t('learn.format')} value={format} onChange={(e) => setFormat(e.target.value as Format | 'all')} options={[{ value: 'all', label: t('learn.all') }, ...(['guided', 'pbl', 'quiz'] as Format[]).map((x) => ({ value: x, label: t(`didactic.format.${x}`) }))]} />
      </div>
      <p className="sr-only" role="status">{t('learn.count', { n: list.length })}</p>
      <ul className="activity-grid" data-testid="activity-list">
        {list.map((a) => (
          <li key={a.id}>
            <a className="activity-card" href={hrefFor('aprender', [a.id])} data-testid={`activity-${a.id}`}>
              <span className="activity-card__meta"><Badge tone="info">{t(`didactic.format.${a.format}`)}</Badge> <Badge>{t(`level.${a.level}`)}</Badge> {completed.includes(a.id) ? <Badge tone="success">✓ {t('learn.done')}</Badge> : null}</span>
              <strong className="activity-card__title">{pick(a.title, locale)}</strong>
              <span className="activity-card__obj">{pick(a.objective, locale)}</span>
              <span className="activity-card__topic">{t(`topic.${a.topic}`)}{a.module === 'hea' ? ` · ${t('nav.hea')}` : ''}</span>
            </a>
          </li>
        ))}
      </ul>
    </>
  );
}

function ActivityView({ activity }: { activity: Activity }) {
  const { t, locale } = useI18n();
  const route = useRoute();
  const metals = useCrystalab((s) => s.metals);
  const engine = useCapabilities((s) => s.crystalab);
  const seedParam = Number(route.query.get('seed'));
  const seed = Number.isInteger(seedParam) && seedParam > 0 ? seedParam : defaultSeed(activity.id);
  const symbol = chooseMaterial(activity, seed, metals ? Object.keys(metals) : null);
  const variable = !activity.fixedMaterial && (activity.pool.length > 1 || activity.format === 'quiz');
  const engineMissing = activity.module === 'crystalab' && engine?.api === 'none';
  return (
    <>
      <nav aria-label={t('learn.breadcrumb')} className="breadcrumb"><a href={hrefFor('aprender')}>{t('learn.title')}</a> <Icon name="chevronRight" size={14} /> <span aria-current="page">{pick(activity.title, locale)}</span></nav>
      <header className="module-head">
        <h1>{pick(activity.title, locale)}</h1>
        <p className="module-head__lead">{pick(activity.instructions, locale)}</p>
        <div className="ds-row">
          <CategoryTag category="param" label={t('learn.seed', { seed })} />
          {variable ? <Button size="sm" icon="restart" onClick={() => navigate('aprender', [activity.id], { seed: String(createRng(seed).int(1000, 9999)) })} data-testid="new-seed">{t('learn.newSeed')}</Button> : null}
          {activity.validation === 'awaiting-specialist' ? <Badge tone="warning">{t('learn.awaitingSpecialist')}</Badge> : null}
        </div>
      </header>
      <details className="criteria">
        <summary>{t('learn.criteria')}</summary>
        <ul>{activity.criteria.map((c) => <li key={c.id}>{pick(c.text, locale)}</li>)}</ul>
        <p className="ds-field__hint">{activity.references.join(' · ')}</p>
      </details>
      {engineMissing ? <CategoryBox category="feedback" role="alert"><p>{t('exercise.engineNeeded')}</p></CategoryBox> : <ActivityBody activity={activity} seed={seed} symbol={symbol} />}
    </>
  );
}

export default function LearnModule() {
  const route = useRoute();
  const { t } = useI18n();
  const activity = route.rest[0] ? activityById(route.rest[0]) : undefined;
  return (
    <Workbench
      className="learn"
      center={
        <main id="main-content" tabIndex={-1} className="module-main">
          {route.rest[0] && !activity ? <CategoryBox category="feedback" role="alert"><p>{t('learn.notFound')}</p><a href={hrefFor('aprender')}>{t('learn.title')}</a></CategoryBox> : activity ? <ActivityView activity={activity} /> : <ActivityList />}
        </main>
      }
      side={<div className="ds-stack"><ProgressPanel /><AiAssist /></div>}
      sideInline
      sideLabel={t('progress.title')}
    />
  );
}
