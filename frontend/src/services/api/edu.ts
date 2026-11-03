/**
 * Questões com correção no servidor (/api/v1/edu — RQ-EDU-01..04). O front nunca recebe o
 * gabarito antes da hora: ele só chega na resposta de uma tentativa, quando a política libera.
 */
import { z } from 'zod';
import { config } from '../../config.ts';
import { requestJson } from './http.ts';

export const QuestionInfo = z.object({
  id: z.string(), titulo: z.string(), enunciado: z.string(), gerador: z.string().nullable().optional(),
  topicos: z.array(z.string()), dificuldade: z.number(), max_tentativas: z.number(),
}).passthrough();
export type QuestionInfo = z.infer<typeof QuestionInfo>;
export const QuestionInstance = z.object({
  id: z.string(), questao_id: z.string(), titulo: z.string(), enunciado: z.string(),
  parametros: z.record(z.string(), z.unknown()), unidade: z.string(), max_tentativas: z.number(), semente: z.number(),
});
export type QuestionInstance = z.infer<typeof QuestionInstance>;
export const AttemptResult = z.object({
  correta: z.boolean(), tentativa: z.number(), restantes: z.number(), tipo_erro: z.string().nullable().optional(),
  gabarito: z.object({ valor: z.number(), unidade: z.string(), resolucao: z.array(z.string()) }).nullable().optional(),
});
export type AttemptResult = z.infer<typeof AttemptResult>;

const api = (path: string): string => `${config.apiBase}/api/v1${path}`;

export const eduApi = {
  questions: (signal?: AbortSignal) => requestJson(api('/edu/questions'), { signal, schema: z.array(QuestionInfo) }),
  start: (questionId: string) => requestJson(api(`/edu/questions/${encodeURIComponent(questionId)}/instances`), { body: {}, schema: QuestionInstance }),
  answer: (instanceId: string, resposta: number, tempoMs?: number) =>
    requestJson(api(`/edu/instances/${encodeURIComponent(instanceId)}/attempts`), { body: { resposta, ...(tempoMs !== undefined ? { tempo_ms: tempoMs } : {}) }, schema: AttemptResult }),
};
