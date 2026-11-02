import { create } from 'zustand';
import { readJSON, writeJSON } from '../../utils/storage.ts';
import type { Attempt, Topic } from './model.ts';

const KEY = 'alloy.didactics.attempts';

interface DidacticsState {
  attempts: Attempt[];
  completed: string[];
  record: (a: Omit<Attempt, 'at'>) => void;
  complete: (activityId: string) => void;
  reset: () => void;
}

const saved = readJSON<{ attempts: Attempt[]; completed: string[] }>(KEY, { attempts: [], completed: [] });

export const useDidactics = create<DidacticsState>()((set, get) => ({
  attempts: saved.attempts ?? [],
  completed: saved.completed ?? [],
  record: (a) => {
    const attempts = [...get().attempts, { ...a, at: new Date().toISOString() }].slice(-2000);
    set({ attempts });
    writeJSON(KEY, { attempts, completed: get().completed });
  },
  complete: (id) => {
    const completed = Array.from(new Set([...get().completed, id]));
    set({ completed });
    writeJSON(KEY, { attempts: get().attempts, completed });
  },
  reset: () => { set({ attempts: [], completed: [] }); writeJSON(KEY, { attempts: [], completed: [] }); },
}));

export interface TopicProgress {
  topic: Topic;
  attempts: number;
  correct: number;
  errors: Record<string, number>;
}

export function progressByTopic(attempts: Attempt[]): TopicProgress[] {
  const map = new Map<Topic, TopicProgress>();
  for (const a of attempts) {
    const p = map.get(a.topic) ?? { topic: a.topic, attempts: 0, correct: 0, errors: {} };
    p.attempts += 1;
    if (a.correct) p.correct += 1;
    else if (a.errorType) p.errors[a.errorType] = (p.errors[a.errorType] ?? 0) + 1;
    map.set(a.topic, p);
  }
  return Array.from(map.values());
}

/**
 * Recomendações de revisão (6.11): tópicos com pelo menos 2 tentativas e menos de 60 % de acertos
 * apontam para uma atividade do mesmo tópico (de preferência ainda não concluída). Sem ranking.
 */
export function reviewRecommendations(attempts: Attempt[], completed: string[], activities: Array<{ id: string; topic: Topic }>): Array<{ topic: Topic; activityId: string; rate: number }> {
  return progressByTopic(attempts)
    .filter((p) => p.attempts >= 2 && p.correct / p.attempts < 0.6)
    .map((p) => {
      const pool = activities.filter((a) => a.topic === p.topic);
      const act = pool.find((a) => !completed.includes(a.id)) ?? pool[0];
      return act ? { topic: p.topic, activityId: act.id, rate: p.correct / p.attempts } : null;
    })
    .filter((r): r is { topic: Topic; activityId: string; rate: number } => r !== null);
}
