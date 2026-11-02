/**
 * Rascunhos de tarefa do professor (6.15/6.18). Sem serviço de turmas (D-03) eles ficam neste
 * navegador e são rotulados como rascunho local; publicar continua exigindo resposta do serviço.
 */
import { readJSON, writeJSON } from '../../utils/storage.ts';
import { uid } from '../../utils/id.ts';

export interface AssignmentDraft { id: string; activityId: string; classId: string; due: string; instructions: string; savedAt: string }
const KEY = 'alloy.instructor.drafts';

export function listDrafts(): AssignmentDraft[] { return readJSON<AssignmentDraft[]>(KEY, []); }
export function saveDraft(d: Omit<AssignmentDraft, 'id' | 'savedAt'>): AssignmentDraft {
  const draft = { ...d, id: uid('draft'), savedAt: new Date().toISOString() };
  writeJSON(KEY, [draft, ...listDrafts()].slice(0, 50));
  return draft;
}
export function deleteDraft(id: string): void { writeJSON(KEY, listDrafts().filter((d) => d.id !== id)); }
