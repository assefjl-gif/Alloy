/**
 * Adaptador de turmas/tarefas/avaliações (6.15–6.18). Não há endpoint (pendência D-03):
 *  - leitura: dados DEMONSTRATIVOS com semente fixa, rotulados, ou dados reais deste navegador;
 *  - escrita (publicar tarefa): sempre falha com 'unavailable' — a interface NUNCA confirma
 *    publicação sem resposta do serviço.
 */
import { createRng } from '../../utils/rng.ts';
import type { Topic } from '../../modules/didactics/model.ts';

export const CLASSROOM_DEMO_SEED = 4242;

export interface ClassGroup { id: string; name: string; students: number; demo: true }
export interface StepErrors { step: string; errors: number; attempts: number }
export interface TopicDifficulty { topic: Topic; errorRate: number; attempts: number }

export function demoClasses(): ClassGroup[] {
  return [
    { id: 't1', name: 'Turma demonstrativa A', students: 32, demo: true },
    { id: 't2', name: 'Turma demonstrativa B', students: 27, demo: true },
  ];
}

export function demoStepErrors(): StepErrors[] {
  const rng = createRng(CLASSROOM_DEMO_SEED);
  return ['grandezas', 'equacao', 'substituicao', 'validacao'].map((step) => {
    const attempts = rng.int(40, 70);
    return { step, attempts, errors: rng.int(3, Math.floor(attempts * 0.6)) };
  });
}

export function demoTopics(): TopicDifficulty[] {
  const rng = createRng(CLASSROOM_DEMO_SEED + 1);
  return (['estruturas', 'celulas', 'fea', 'densidade', 'miller-planos', 'miller-direcoes'] as Topic[]).map((topic) => ({ topic, attempts: rng.int(30, 90), errorRate: Math.round(rng.range(0.08, 0.55) * 100) / 100 }));
}

export function demoCompletion(): { completed: number; total: number } {
  const rng = createRng(CLASSROOM_DEMO_SEED + 2);
  return { completed: rng.int(20, 45), total: 59 };
}

export class ServiceUnavailableError extends Error {
  constructor() {
    super('Serviço de turmas indisponível (D-03): nada foi publicado.');
    this.name = 'ServiceUnavailableError';
  }
}

export async function publishAssignment(_assignment: unknown): Promise<never> {
  void _assignment;
  throw new ServiceUnavailableError();
}
