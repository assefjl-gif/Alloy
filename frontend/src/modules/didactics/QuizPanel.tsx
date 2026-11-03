/**
 * QuizPanel (6.10): múltipla escolha, resposta curta e flashcards de fórmulas e conceitos,
 * com embaralhamento controlado por semente e feedback explicativo. As respostas numéricas
 * são lidas das tabelas do motor; os enunciados conceituais citam a bibliografia do projeto.
 */
import { useEffect, useMemo, useState } from 'react';
import { useI18n, pick, type Localized } from '../../i18n/index.ts';
import { crystalabApi } from '../../services/api/crystalab.ts';
import type { MetalTable, StructureRow } from '../../services/api/contracts.ts';
import { Button } from '../../design-system/primitives/Button.tsx';
import { TextInput } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, DemoSeal } from '../../design-system/primitives/Category.tsx';
import { Tabs, TabPanel } from '../../design-system/primitives/Tabs.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { Formula } from '../../features/formula/Formula.tsx';
import { createRng } from '../../utils/rng.ts';
import { plain } from '../../utils/text.ts';
import { announce } from '../../design-system/announce.ts';
import type { Activity, Topic } from './model.ts';
import { useDidactics } from './store.ts';
import { useHea } from '../hea/store.ts';

interface McQuestion { id: string; kind: 'mc'; topic: Topic; prompt: Localized; options: string[]; answer: string; explanation: Localized; ref: string }
interface ShortQuestion { id: string; kind: 'short'; topic: Topic; prompt: Localized; accept: string[]; explanation: Localized; ref: string }
type Question = McQuestion | ShortQuestion;

function L(pt: string, en: string, es: string): Localized { return { 'pt-BR': pt, en, es }; }

export function buildQuestions(structures: StructureRow[], metals: MetalTable): Question[] {
  const by = (s: string) => structures.find((x) => x.sigla === s);
  const cfc = by('CFC'); const ccc = by('CCC'); const cs = by('CS');
  const qs: Question[] = [];
  if (cfc) qs.push({ id: 'n-cfc', kind: 'mc', topic: 'celulas', prompt: L('Quantos átomos equivalentes há em uma célula unitária CFC?', 'How many equivalent atoms are in an FCC unit cell?', '¿Cuántos átomos equivalentes hay en una celda unitaria FCC?'), options: ['1', '2', String(cfc.n), '6'], answer: String(cfc.n), explanation: L('8 vértices × 1/8 + 6 faces × 1/2 = 4.', '8 corners × 1/8 + 6 faces × 1/2 = 4.', '8 vértices × 1/8 + 6 caras × 1/2 = 4.'), ref: 'CAL9 §3.4, p. 48' });
  if (ccc) qs.push({ id: 'nc-ccc', kind: 'mc', topic: 'estruturas', prompt: L('Qual é o número de coordenação da estrutura CCC?', 'What is the coordination number of BCC?', '¿Cuál es el número de coordinación de la BCC?'), options: ['6', String(ccc.nc), '12', '4'], answer: String(ccc.nc), explanation: L('O átomo central toca os 8 átomos dos vértices.', 'The centre atom touches the 8 corner atoms.', 'El átomo central toca los 8 átomos de los vértices.'), ref: 'CAL9 §3.4, p. 48–54' });
  if (cs && ccc && cfc) qs.push({ id: 'fea-max', kind: 'mc', topic: 'fea', prompt: L('Entre as estruturas cúbicas, qual tem o maior FEA?', 'Among the cubic structures, which has the highest APF?', 'Entre las estructuras cúbicas, ¿cuál tiene el mayor FEA?'), options: ['CS', 'CCC', 'CFC'], answer: [cs, ccc, cfc].sort((a, b) => b.fea - a.fea)[0]?.sigla ?? 'CFC', explanation: L(`FEA (motor): CS ${cs.fea.toFixed(2)}, CCC ${ccc.fea.toFixed(2)}, CFC ${cfc.fea.toFixed(2)}.`, `APF (engine): SC ${cs.fea.toFixed(2)}, BCC ${ccc.fea.toFixed(2)}, FCC ${cfc.fea.toFixed(2)}.`, `FEA (motor): CS ${cs.fea.toFixed(2)}, BCC ${ccc.fea.toFixed(2)}, FCC ${cfc.fea.toFixed(2)}.`), ref: 'CAL9 §3.4, p. 48–54' });
  if (ccc) qs.push({ id: 'rel-ccc', kind: 'short', topic: 'estruturas', prompt: L('Escreva a relação entre a e R na CCC (ex.: a = 2R).', 'Write the a–R relation for BCC (e.g. a = 2R).', 'Escriba la relación entre a y R en la BCC (ej.: a = 2R).'), accept: [ccc.relacao, 'a=4r/√3', 'a=4r/raiz3', 'a=4r/sqrt3', 'a=4r/sqrt(3)'], explanation: L('Contato na diagonal do cubo: 4R = a√3.', 'Contact along the cube diagonal: 4R = a√3.', 'Contacto en la diagonal del cubo: 4R = a√3.'), ref: 'CAL9 §3.4, p. 48–54' });
  if (metals.Fe) qs.push({ id: 'fe-alpha', kind: 'mc', topic: 'estruturas', prompt: L('Qual é a estrutura cristalina do Fe-α à temperatura ambiente?', 'What is the crystal structure of α-Fe at room temperature?', '¿Cuál es la estructura cristalina del Fe-α a temperatura ambiente?'), options: ['CS', 'CCC', 'CFC', 'HC'], answer: metals.Fe.estrutura, explanation: L('O Fe-α é CCC (tabela do motor, CAL9 Tab. 3.1).', 'α-Fe is BCC (engine table, CAL9 Table 3.1).', 'El Fe-α es BCC (tabla del motor, CAL9 Tab. 3.1).'), ref: 'CAL9 Tab. 3.1, p. 49' });
  if (metals.Mg) qs.push({ id: 'mg', kind: 'mc', topic: 'estruturas', prompt: L('O magnésio cristaliza em qual estrutura?', 'Which structure does magnesium crystallise in?', '¿En qué estructura cristaliza el magnesio?'), options: ['CCC', 'CFC', 'HC', 'CS'], answer: metals.Mg.estrutura, explanation: L('Mg é hexagonal compacto.', 'Mg is hexagonal close-packed.', 'El Mg es hexagonal compacto.'), ref: 'CAL9 Tab. 3.1, p. 49' });
  qs.push({ id: 'stack-hc', kind: 'mc', topic: 'estruturas', prompt: L('Qual sequência de empilhamento de planos compactos gera a HC?', 'Which close-packed stacking sequence produces HCP?', '¿Qué secuencia de apilamiento de planos compactos genera la HC?'), options: ['ABAB…', 'ABCABC…', 'AAAA…', 'ABCBA…'], answer: 'ABAB…', explanation: L('Na HC a terceira camada repete a primeira (ABAB); na CFC, só a quarta (ABCABC).', 'In HCP the third layer repeats the first (ABAB); in FCC only the fourth does (ABCABC).', 'En la HC la tercera capa repite la primera (ABAB); en la FCC solo la cuarta (ABCABC).'), ref: 'CAL9 §3.12, p. 75' });
  qs.push({ id: 'bravais-i', kind: 'short', topic: 'miller-planos', prompt: L('Nos índices de Miller-Bravais (h k i l), quanto vale i para h = 1 e k = 0?', 'In Miller-Bravais indices (h k i l), what is i for h = 1 and k = 0?', 'En los índices de Miller-Bravais (h k i l), ¿cuánto vale i para h = 1 y k = 0?'), accept: ['-1', '−1'], explanation: L('i = −(h + k) = −1.', 'i = −(h + k) = −1.', 'i = −(h + k) = −1.'), ref: 'CAL9 §3.8–3.10, p. 58–74' });
  qs.push({ id: 'plane-parallel', kind: 'mc', topic: 'miller-planos', prompt: L('Um plano paralelo ao eixo z tem qual índice l?', 'A plane parallel to the z axis has which l index?', 'Un plano paralelo al eje z tiene qué índice l?'), options: ['0', '1', '∞', '−1'], answer: '0', explanation: L('Interseção no infinito → recíproco 0.', 'Intercept at infinity → reciprocal 0.', 'Intersección en el infinito → recíproco 0.'), ref: 'CAL9 §3.8–3.10, p. 58–74' });
  qs.push({ id: 'nm-cm', kind: 'short', topic: 'densidade', prompt: L('1 nm³ equivale a quantos cm³? (escreva como 1e-21)', 'How many cm³ is 1 nm³? (write as 1e-21)', '¿A cuántos cm³ equivale 1 nm³? (escriba 1e-21)'), accept: ['1e-21', '10^-21', '10⁻²¹', '1×10⁻²¹', '1x10^-21'], explanation: L('1 nm = 10⁻⁷ cm ⇒ 1 nm³ = 10⁻²¹ cm³.', '1 nm = 10⁻⁷ cm ⇒ 1 nm³ = 10⁻²¹ cm³.', '1 nm = 10⁻⁷ cm ⇒ 1 nm³ = 10⁻²¹ cm³.'), ref: 'CAL9 §3.5, p. 54' });
  return qs;
}

const FLASHCARDS: Array<{ id: string; front: Localized; tex?: string; back: Localized; ref: string }> = [
  { id: 'rho', front: L('Densidade teórica', 'Theoretical density', 'Densidad teórica'), tex: '\\rho = \\dfrac{n\\,A}{V_C\\,N_A}', back: L('n átomos por célula, A massa atômica, Vc volume da célula, N_A número de Avogadro.', 'n atoms per cell, A atomic mass, Vc cell volume, N_A Avogadro’s number.', 'n átomos por celda, A masa atómica, Vc volumen de la celda, N_A número de Avogadro.'), ref: 'CAL9 §3.5, p. 54' },
  { id: 'fea', front: L('Fator de empacotamento atômico', 'Atomic packing factor', 'Factor de empaquetamiento atómico'), tex: '\\text{FEA} = \\dfrac{V_S}{V_C} = \\dfrac{n\\cdot\\frac{4}{3}\\pi R^{3}}{V_C}', back: L('Fração do volume da célula ocupada por esferas rígidas.', 'Fraction of the cell volume occupied by hard spheres.', 'Fracción del volumen de la celda ocupada por esferas rígidas.'), ref: 'CAL9 §3.4, p. 48–54' },
  { id: 'cfc', front: L('Relação a–R na CFC', 'a–R relation in FCC', 'Relación a–R en la FCC'), tex: 'a = 2R\\sqrt{2}', back: L('Átomos se tocam na diagonal da face (4R = a√2).', 'Atoms touch along the face diagonal (4R = a√2).', 'Los átomos se tocan en la diagonal de la cara (4R = a√2).'), ref: 'CAL9 §3.4, p. 48–54' },
  { id: 'ccc', front: L('Relação a–R na CCC', 'a–R relation in BCC', 'Relación a–R en la BCC'), tex: 'a = \\dfrac{4R}{\\sqrt{3}}', back: L('Átomos se tocam na diagonal do cubo (4R = a√3).', 'Atoms touch along the cube diagonal (4R = a√3).', 'Los átomos se tocan en la diagonal del cubo (4R = a√3).'), ref: 'CAL9 §3.4, p. 48–54' },
  { id: 'hc', front: L('Volume da célula HC', 'HCP cell volume', 'Volumen de la celda HC'), tex: 'V_C = \\dfrac{3\\sqrt{3}}{2}\\,a^{2}c', back: L('Prisma hexagonal (3 células primitivas); c/a ideal ≈ 1,633.', 'Hexagonal prism (3 primitive cells); ideal c/a ≈ 1.633.', 'Prisma hexagonal (3 celdas primitivas); c/a ideal ≈ 1,633.'), ref: 'CAL9 §3.4, p. 48–54' },
  { id: 'bravais', front: L('Miller-Bravais', 'Miller-Bravais', 'Miller-Bravais'), tex: '(h\\,k\\,i\\,l),\\quad i = -(h+k)', back: L('Quarto índice redundante usado na HC.', 'Redundant fourth index used for HCP.', 'Cuarto índice redundante usado en la HC.'), ref: 'CAL9 §3.8–3.10, p. 58–74' },
  { id: 'ld', front: L('Densidade linear', 'Linear density', 'Densidad lineal'), tex: 'DL = \\dfrac{\\text{átomos centrados no vetor}}{\\text{comprimento do vetor}}', back: L('Átomos por unidade de comprimento ao longo de uma direção.', 'Atoms per unit length along a direction.', 'Átomos por unidad de longitud a lo largo de una dirección.'), ref: 'CAL9 §3.11, p. 74' },
];

function normalizeAnswer(s: string): string {
  return plain(s).replace(/\s+/g, '').replace(/[−–]/g, '-').replace('raizde3', '√3');
}

export function QuizPanel({ activity, seed }: { activity: Activity; seed: number }) {
  const { t, locale } = useI18n();
  const [data, setData] = useState<{ structures: StructureRow[]; metals: MetalTable } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'quiz' | 'cards'>('quiz');
  const [index, setIndex] = useState(0);
  const [chosen, setChosen] = useState<string>('');
  const [answered, setAnswered] = useState<{ correct: boolean } | null>(null);
  const [score, setScore] = useState({ ok: 0, total: 0 });
  const [flipped, setFlipped] = useState<Record<string, boolean>>({});
  const record = useDidactics((s) => s.record);
  const complete = useDidactics((s) => s.complete);
  useEffect(() => {
    if (activity.requiresHea) return;
    Promise.all([crystalabApi.structures(), crystalabApi.metals()]).then(([structures, metals]) => setData({ structures, metals })).catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, [activity.requiresHea]);
  const questions = useMemo(() => {
    if (!data) return [];
    const rng = createRng(seed);
    return rng.shuffle(buildQuestions(data.structures, data.metals)).map((q) => (q.kind === 'mc' ? { ...q, options: rng.shuffle(q.options) } : q));
  }, [data, seed]);
  const cards = useMemo(() => createRng(seed + 7).shuffle(FLASHCARDS), [seed]);

  if (activity.requiresHea) return <HeaMapQuiz activity={activity} />;
  if (error) return <p role="alert">{t('exercise.engineNeeded')}</p>;
  if (!data) return <Spinner size={22} label={t('common.loading')} />;
  const q = questions[index];
  const finished = index >= questions.length;
  const check = () => {
    if (!q) return;
    const correct = q.kind === 'mc' ? chosen === q.answer : q.accept.some((a) => normalizeAnswer(a) === normalizeAnswer(chosen));
    setAnswered({ correct });
    setScore((s) => ({ ok: s.ok + (correct ? 1 : 0), total: s.total + 1 }));
    record({ activityId: activity.id, topic: q.topic, step: q.id, correct, ...(correct ? {} : { errorType: q.kind === 'short' && !chosen.trim() ? 'input' as const : 'conceptual' as const }), seed });
    announce(correct ? t('exercise.correct') : t('quiz.wrong'));
  };
  return (
    <div className="quiz" data-testid="quiz">
      <Tabs label={t('quiz.modes')} idPrefix="quiz" value={tab} onChange={(v) => setTab(v as 'quiz' | 'cards')} items={[{ id: 'quiz', label: t('quiz.quiz') }, { id: 'cards', label: t('quiz.cards') }]} />
      <TabPanel idPrefix="quiz" id="quiz" active={tab === 'quiz'}>
        <p className="ds-field__hint">{t('quiz.seed', { seed })}</p>
        {finished ? (
          <CategoryBox category="feedback" role="status"><p>{t('quiz.finished', { ok: score.ok, total: score.total })}</p>
            <Button variant="primary" icon="check" onClick={() => { complete(activity.id); announce(t('exercise.completed')); }} data-testid="exercise-complete">{t('exercise.complete')}</Button></CategoryBox>
        ) : q ? (
          <section aria-labelledby="quiz-q">
            <p className="ds-label">{t('quiz.progress', { n: index + 1, total: questions.length })}</p>
            <h2 id="quiz-q">{pick(q.prompt, locale)}</h2>
            {q.kind === 'mc' ? (
              <fieldset className="exercise__radios"><legend className="sr-only">{pick(q.prompt, locale)}</legend>
                {q.options.map((o) => <label key={o} className={`exercise__radio ${chosen === o ? 'is-on' : ''}`}><input type="radio" name={`q-${q.id}`} value={o} checked={chosen === o} disabled={Boolean(answered)} onChange={() => setChosen(o)} /> {o}</label>)}
              </fieldset>
            ) : <TextInput label={t('quiz.answer')} value={chosen} disabled={Boolean(answered)} onChange={(e) => setChosen(e.target.value)} data-testid="quiz-short" />}
            {!answered ? <Button variant="primary" disabled={!chosen} onClick={check} data-testid="quiz-check">{t('exercise.check')}</Button> : (
              <>
                <CategoryBox category="feedback" role="status" className={`feedback ${answered.correct ? 'is-correct' : 'is-wrong'}`}>
                  <strong>{answered.correct ? `✓ ${t('exercise.correct')}` : `✗ ${t('quiz.wrong')}`}</strong>
                  <p>{pick(q.explanation, locale)}</p><cite>{q.ref}</cite>
                </CategoryBox>
                <Button onClick={() => { setIndex((i) => i + 1); setChosen(''); setAnswered(null); }} data-testid="quiz-next">{t('exercise.next')}</Button>
              </>
            )}
          </section>
        ) : null}
      </TabPanel>
      <TabPanel idPrefix="quiz" id="cards" active={tab === 'cards'}>
        <ul className="cards">
          {cards.map((c) => (
            <li key={c.id}>
              <button type="button" className={`flashcard ${flipped[c.id] ? 'is-flipped' : ''}`} aria-pressed={Boolean(flipped[c.id])} onClick={() => setFlipped((f) => ({ ...f, [c.id]: !f[c.id] }))}>
                <span className="flashcard__front"><strong>{pick(c.front, locale)}</strong>{c.tex && !flipped[c.id] ? <span className="sr-only">{t('quiz.flipHint')}</span> : null}</span>
                {flipped[c.id] ? <span className="flashcard__back">{c.tex ? <Formula tex={c.tex} display label={pick(c.front, locale)} /> : null}<span>{pick(c.back, locale)}</span><cite>{c.ref}</cite></span> : <span className="flashcard__hint" aria-hidden="true">{t('quiz.flip')}</span>}
              </button>
            </li>
          ))}
        </ul>
      </TabPanel>
    </div>
  );
}

/** Exercício HEA (6.4): só usa o que o preditor retornou para a liga atual. */
function HeaMapQuiz({ activity }: { activity: Activity }) {
  const { t, num } = useI18n();
  const r = useHea((s) => s.result);
  const origin = useHea((s) => s.resultOrigin);
  const record = useDidactics((s) => s.record);
  const [answer, setAnswer] = useState('');
  const [res, setRes] = useState<boolean | null>(null);
  if (!r) return <CategoryBox category="feedback"><p>{t('quiz.hea.needsResult')}</p><a className="ds-btn ds-btn--secondary" href="#/hea">{t('nav.hea')}</a></CategoryBox>;
  const inside = r.delta < 6.6 && r.dH > -15 && r.dH < 5;
  return (
    <div className="quiz" data-testid="hea-quiz">
      {origin === 'demo' ? <DemoSeal text={t('common.demo')} detail={t('hea.demoDetail')} /> : null}
      <h2>{t('quiz.hea.question', { name: r.nome, delta: num(r.delta, 2), dh: num(r.dH, 2) })}</h2>
      <fieldset className="exercise__radios"><legend className="sr-only">{t('quiz.hea.legend')}</legend>
        {[['in', t('quiz.hea.inside')], ['out', t('quiz.hea.outside')]].map(([v, l]) => <label key={v} className={`exercise__radio ${answer === v ? 'is-on' : ''}`}><input type="radio" name="hea-zone" value={v} checked={answer === v} onChange={() => setAnswer(v as string)} /> {l}</label>)}
      </fieldset>
      <Button variant="primary" disabled={!answer} onClick={() => { const ok = (answer === 'in') === inside; setRes(ok); record({ activityId: activity.id, topic: activity.topic, step: 'zona', correct: ok, ...(ok ? {} : { errorType: 'conceptual' as const }), seed: 0, demo: origin === 'demo' }); }}>{t('exercise.check')}</Button>
      {res !== null ? <CategoryBox category="feedback" role="status"><strong>{res ? `✓ ${t('exercise.correct')}` : `✗ ${t('quiz.wrong')}`}</strong><p>{t('quiz.hea.explain')}</p></CategoryBox> : null}
    </div>
  );
}
