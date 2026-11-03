/**
 * Caderno de laboratório (6.13/6.14). As notas ficam NESTE navegador (pendência D-18: não há
 * serviço de sincronização). Cada nota pode guardar a estrutura, os parâmetros e as medições
 * que o motor devolveu no momento — nunca valores recalculados no front-end. Notas criadas
 * offline são marcadas para que a interface avise ao reconectar.
 */
import { create } from 'zustand';
import { readJSON, writeJSON } from '../../utils/storage.ts';
import { uid } from '../../utils/id.ts';

export type NoteKind = 'observation' | 'hypothesis' | 'calculation' | 'conclusion' | 'free';

export interface NoteStructureRef {
  rotulo: string;
  estrutura: string;
  request: Record<string, unknown>;
}

export interface Note {
  id: string;
  kind: NoteKind;
  title: string;
  body: string;
  createdAt: string;
  updatedAt: string;
  activityId?: string;
  structure?: NoteStructureRef;
  /** valores copiados da resposta do motor (rótulos de origem preservados) */
  params?: Record<string, number | string | null>;
  measurements?: Array<{ label: string; value: string }>;
  sceneUrl?: string;
  /** miniatura JPEG da cena (data URL) */
  image?: string;
  createdOffline?: boolean;
  synced?: boolean;
}

const KEY = 'alloy.notebook';
const DRAFT_KEY = 'alloy.notebook.draft';

interface NotebookState {
  notes: Note[];
  add: (n: NewNote) => Note;
  update: (id: string, patch: Partial<Omit<Note, 'id' | 'createdAt'>>) => void;
  remove: (id: string) => void;
  clear: () => void;
}

export type NewNote = Omit<Note, 'id' | 'createdAt' | 'updatedAt' | 'createdOffline' | 'synced'>;

function persist(notes: Note[]): void { writeJSON(KEY, notes); }

function isOffline(): boolean {
  return typeof navigator !== 'undefined' && navigator.onLine === false;
}

export const useNotebook = create<NotebookState>()((set, get) => ({
  notes: readJSON<Note[]>(KEY, []),
  add: (n) => {
    const now = new Date().toISOString();
    const note: Note = { ...n, id: uid('note'), createdAt: now, updatedAt: now, ...(isOffline() ? { createdOffline: true, synced: false } : {}) };
    const notes = [note, ...get().notes].slice(0, 500);
    set({ notes });
    persist(notes);
    return note;
  },
  update: (id, patch) => {
    const notes = get().notes.map((n) => (n.id === id ? { ...n, ...patch, updatedAt: new Date().toISOString() } : n));
    set({ notes });
    persist(notes);
  },
  remove: (id) => {
    const notes = get().notes.filter((n) => n.id !== id);
    set({ notes });
    persist(notes);
  },
  clear: () => { set({ notes: [] }); persist([]); },
}));

export function addNote(n: NewNote): Note { return useNotebook.getState().add(n); }

export function countOfflineNotes(): number {
  return useNotebook.getState().notes.filter((n) => n.createdOffline && !n.synced).length;
}

/** "Sincronizar" aqui significa apenas marcar como revisada; não há envio a servidor (D-18). */
export function markNotesSynced(): void {
  const notes = useNotebook.getState().notes.map((n) => (n.createdOffline ? { ...n, synced: true } : n));
  useNotebook.setState({ notes });
  persist(notes);
}

export interface Draft { kind: NoteKind; title: string; body: string }
export function readDraft(): Draft { return readJSON<Draft>(DRAFT_KEY, { kind: 'observation', title: '', body: '' }); }
export function saveDraft(d: Draft): void { writeJSON(DRAFT_KEY, d); }

export function notesToMarkdown(notes: Note[], labels: Record<NoteKind, string>): string {
  return notes.map((n) => {
    const lines = [`## ${n.title || labels[n.kind]}`, `*${labels[n.kind]} · ${n.createdAt}*`, '', n.body];
    if (n.structure) lines.push('', `- Estrutura: ${n.structure.rotulo} (${n.structure.estrutura})`);
    if (n.params) for (const [k, v] of Object.entries(n.params)) lines.push(`- ${k}: ${v ?? "—"}`);
    if (n.measurements) for (const m of n.measurements) lines.push(`- ${m.label}: ${m.value}`);
    if (n.sceneUrl) lines.push(`- Cena: ${n.sceneUrl}`);
    return lines.join('\n');
  }).join('\n\n---\n\n');
}
