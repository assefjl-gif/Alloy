import { create } from 'zustand';
import { readJSON, writeJSON } from '../utils/storage.ts';
import { uid } from '../utils/id.ts';

export type EntryKind = 'input' | 'ok' | 'error' | 'step' | 'info' | 'warn';
export type RunStatus = 'running' | 'done' | 'cancelled' | 'failed';

export interface TerminalEntry {
  id: string;
  kind: EntryKind;
  text: string;
  /** operação à qual a linha pertence (para atualizar o estado de execução) */
  opId?: string;
  status?: RunStatus;
  /** comando equivalente, quando a operação veio de formulário/paleta/viewer */
  equivalent?: string;
  source?: string;
}

export interface Choice {
  label: string;
  command: string;
}

interface TerminalState {
  entries: TerminalEntry[];
  history: string[];
  running: { opId: string; label: string; cancel: () => void } | null;
  /** escolha explícita pedida ao usuário em caso de ambiguidade (tarefa 4.2) */
  pendingChoice: { prompt: string; choices: Choice[] } | null;
  set: (patch: Partial<Omit<TerminalState, 'set'>>) => void;
}

const HISTORY_KEY = 'alloy.terminal.history';

export const useTerminal = create<TerminalState>()((set) => ({
  entries: [],
  history: readJSON<string[]>(HISTORY_KEY, []),
  running: null,
  pendingChoice: null,
  set: (patch) => set(patch),
}));

const MAX_ENTRIES = 400;

export function log(kind: EntryKind, text: string, extra: Partial<TerminalEntry> = {}): string {
  const id = uid('log');
  const s = useTerminal.getState();
  s.set({ entries: [...s.entries, { id, kind, text, ...extra }].slice(-MAX_ENTRIES) });
  return id;
}

export function updateEntry(id: string, patch: Partial<TerminalEntry>): void {
  const s = useTerminal.getState();
  s.set({ entries: s.entries.map((e) => (e.id === id ? { ...e, ...patch } : e)) });
}

export function pushHistory(command: string): void {
  const s = useTerminal.getState();
  const history = [...s.history.filter((h) => h !== command), command].slice(-100);
  s.set({ history });
  writeJSON(HISTORY_KEY, history);
}

export function clearLog(): void {
  useTerminal.getState().set({ entries: [] });
}
