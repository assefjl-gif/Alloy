/**
 * Barramento único de operações (tarefa 4.3). Terminal, formulários do modo guiado,
 * paleta de comandos, blocos e viewer chamam `dispatch`. Cada operação:
 *   1. é registrada no terminal com o COMANDO EQUIVALENTE (mesmo vindo de formulário — 4.8);
 *   2. ganha estado de execução (em execução → concluída | cancelada | falhou — 4.5);
 *   3. pode ser cancelada (AbortController) quando chama o motor;
 *   4. é executada por um único handler, garantindo resultado idêntico qualquer que seja a origem.
 */
import { translate, type MessageKey, type Vars } from '../i18n/index.ts';
import { ApiError, isAbort } from '../services/api/http.ts';
import { usePreferences } from '../stores/preferences.ts';
import { log, pushHistory, updateEntry, useTerminal } from '../stores/terminal.ts';
import { uid } from '../utils/id.ts';
import { toCommand } from './serialize.ts';
import { parseCommand } from './parser.ts';
import type { Context, Operation, OperationType, ParseError, Source } from './types.ts';
import { useCrystalab } from '../stores/crystalab.ts';
import { useHea } from '../modules/hea/store.ts';

export interface HandlerContext {
  signal: AbortSignal;
  opId: string;
  source: Source;
  tr: (key: MessageKey, vars?: Vars) => string;
  /** marca a operação como assíncrona (mostra "em execução" e habilita cancelar) */
  running: (labelKey: MessageKey, vars?: Vars) => void;
}

type Handler<T extends Operation = Operation> = (op: T, ctx: HandlerContext) => Promise<void> | void;

const handlers = new Map<OperationType, Handler>();

export function registerHandler<K extends OperationType>(type: K, handler: Handler<Extract<Operation, { type: K }>>): void {
  handlers.set(type, handler as Handler);
}

export const tr = (key: MessageKey, vars?: Vars): string => translate(usePreferences.getState().locale, key, vars);

export interface DispatchResult {
  status: 'done' | 'failed' | 'cancelled';
  error?: string;
}

const controllers = new Map<string, AbortController>();

/** Operações que não ecoam no terminal (ruído): alternâncias disparadas pela própria UI do terminal etc. */
const SILENT: OperationType[] = ['op.cancel'];

export async function dispatch(op: Operation, source: Source, raw?: string): Promise<DispatchResult> {
  const handler = handlers.get(op.type);
  const opId = uid('op');
  const equivalent = toCommand(op);
  if (!SILENT.includes(op.type)) {
    const text = raw ?? equivalent ?? op.type;
    log('input', `> ${text}`, { opId, source, ...(source !== 'terminal' && equivalent ? { equivalent } : {}) });
  }
  if (!handler) {
    log('error', tr('cmd.err.noHandler', { op: op.type }), { opId });
    return { status: 'failed', error: 'no handler' };
  }
  const ctrl = new AbortController();
  controllers.set(opId, ctrl);
  let statusLine: string | null = null;
  const ctx: HandlerContext = {
    signal: ctrl.signal,
    opId,
    source,
    tr,
    running: (labelKey, vars) => {
      const label = tr(labelKey, vars);
      statusLine = log('info', label, { opId, status: 'running' });
      useTerminal.getState().set({ running: { opId, label, cancel: () => ctrl.abort() } });
    },
  };
  try {
    await handler(op, ctx);
    if (statusLine) updateEntry(statusLine, { status: 'done' });
    return { status: 'done' };
  } catch (err) {
    if (isAbort(err) || ctrl.signal.aborted) {
      if (statusLine) updateEntry(statusLine, { status: 'cancelled' });
      log('warn', err instanceof ApiError && err.code === 'STALE' ? err.message : tr('cmd.cancelled'), { opId });
      return { status: 'cancelled' };
    }
    if (statusLine) updateEntry(statusLine, { status: 'failed' });
    const message = describeError(err);
    log('error', message, { opId });
    return { status: 'failed', error: message };
  } finally {
    controllers.delete(opId);
    const running = useTerminal.getState().running;
    if (running?.opId === opId) useTerminal.getState().set({ running: null });
  }
}

export function cancelRunning(): boolean {
  const running = useTerminal.getState().running;
  if (!running) return false;
  running.cancel();
  return true;
}

export function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.kind === 'unavailable' || err.kind === 'network') return tr('cmd.err.engineUnavailable', { detail: err.message });
    if (err.kind === 'timeout') return tr('cmd.err.timeout', { detail: err.message });
    if (err.kind === 'contract') return tr('cmd.err.contract', { detail: err.message });
    return err.message; // mensagens de domínio do motor (já dizem como corrigir)
  }
  return err instanceof Error ? err.message : String(err);
}

function logParseError(error: ParseError): void {
  log('error', tr(error.key, error.vars));
  if (error.hintKey) log('step', tr(error.hintKey, error.hintVars));
}

/** Entrada do terminal: analisa, trata ambiguidade e despacha. */
export async function submitLine(text: string, context: Context, source: Source = 'terminal'): Promise<DispatchResult | null> {
  const raw = text.trim();
  if (!raw) return null;
  pushHistory(raw);
  useTerminal.getState().set({ pendingChoice: null });
  const metals = useCrystalab.getState().metals;
  const alloys = useHea.getState().bootstrap?.alloys ?? null;
  const result = parseCommand(raw, { context, metals, alloys });
  if (result.ok === true) {
    for (const w of result.warnings ?? []) log('warn', tr(w.key, w.vars));
    return dispatch(result.op, source, raw);
  }
  log('input', `> ${raw}`, { source });
  if (result.ok === 'ambiguous') {
    const a = result.ambiguity;
    const prompt = tr(a.promptKey, a.promptVars);
    log('warn', prompt);
    useTerminal.getState().set({ pendingChoice: { prompt, choices: a.choices.map((c) => ({ label: tr(c.labelKey, c.labelVars), command: c.command })) } });
    return { status: 'failed', error: 'ambiguous' };
  }
  logParseError(result.error);
  return { status: 'failed', error: tr(result.error.key, result.error.vars) };
}
