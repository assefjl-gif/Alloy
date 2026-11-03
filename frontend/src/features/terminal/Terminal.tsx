import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { submitLine, cancelRunning } from '../../commands/bus.ts';
import { specsFor, type CommandSpec } from '../../commands/catalog.ts';
import { matchVerb } from '../../commands/parser.ts';
import { tokenize } from '../../commands/lexer.ts';
import type { Context } from '../../commands/types.ts';
import { Icon } from '../../design-system/Icon.tsx';
import { Spinner } from '../../design-system/primitives/misc.tsx';
import { useI18n } from '../../i18n/index.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useTerminal, type TerminalEntry } from '../../stores/terminal.ts';
import { useHea } from '../../modules/hea/store.ts';

interface Suggestion {
  value: string;
  label: string;
  detail: string;
}

function useSuggestions(input: string, context: Context): Suggestion[] {
  const metals = useCrystalab((s) => s.metals);
  const alloys = useHea((s) => s.bootstrap?.alloys ?? null);
  const { t } = useI18n();
  return useMemo(() => {
    const specs = specsFor(context);
    const trimmed = input.replace(/^\s+/, '');
    if (!trimmed) return specs.slice(0, 8).map((s) => ({ value: `${s.verb} `, label: s.verb, detail: t(s.descriptionKey) }));
    const tokens = tokenize(trimmed);
    const ctx = { context, metals, alloys, raw: trimmed };
    const match = matchVerb(tokens, ctx);
    const endsWithSpace = /\s$/.test(input);
    if (match && (tokens.length > match.consumed || endsWithSpace)) {
      const spec: CommandSpec = match.spec;
      const typedArgs = tokens.slice(match.consumed);
      const partial = endsWithSpace ? '' : (typedArgs[typedArgs.length - 1]?.raw ?? '');
      const prefix = trimmed.slice(0, trimmed.length - partial.length);
      const options = spec.complete?.(ctx) ?? [];
      const list = options
        .filter((o) => o.toLowerCase().startsWith(partial.toLowerCase()))
        .slice(0, 8)
        .map((o) => ({ value: `${prefix}${prefix.endsWith(' ') || !prefix ? '' : ' '}${o}`, label: o, detail: spec.syntax }));
      if (list.length) return list;
      return spec.examples.slice(0, 4).map((e) => ({ value: e, label: e, detail: t('terminal.example') }));
    }
    const lower = trimmed.toLowerCase();
    return specs
      .filter((s) => [s.verb, ...s.aliases].some((v) => v.startsWith(lower)))
      .slice(0, 8)
      .map((s) => ({ value: `${s.verb} `, label: s.verb, detail: `${s.syntax} — ${t(s.descriptionKey)}` }));
  }, [input, context, metals, alloys, t]);
}

const KIND_CLASS: Record<TerminalEntry['kind'], string> = { input: 'is-entry', ok: 'is-ok', error: 'is-error', step: 'is-step', info: 'is-info', warn: 'is-warn' };

/**
 * Terminal do laboratório (4.4/4.5). Mantém os comandos do legado; adiciona autocompletar
 * contextual (combobox ARIA), histórico com ↑/↓, estados de execução com cancelamento,
 * mensagens que dizem como corrigir e escolha explícita em caso de ambiguidade.
 */
export function Terminal({ context, placeholderKey, shortcuts }: { context: Context; placeholderKey: 'terminal.placeholder' | 'terminal.placeholderHea'; shortcuts?: Array<{ label: string; command: string; tone: string }> }) {
  const { t } = useI18n();
  const entries = useTerminal((s) => s.entries);
  const history = useTerminal((s) => s.history);
  const running = useTerminal((s) => s.running);
  const pendingChoice = useTerminal((s) => s.pendingChoice);
  const [input, setInput] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [histIdx, setHistIdx] = useState<number | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();
  const suggestions = useSuggestions(input, context);

  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [entries]);

  const run = async (text: string) => {
    setOpen(false);
    setActive(-1);
    setHistIdx(null);
    setInput('');
    await submitLine(text, context);
  };

  const accept = (s: Suggestion) => {
    setInput(s.value);
    setActive(-1);
    inputRef.current?.focus();
  };

  return (
    <div className="term">
      {shortcuts?.length ? (
        <div className="term__shortcuts" role="group" aria-label={t('terminal.shortcuts')}>
          {shortcuts.map((s) => (
            <button key={s.command} type="button" className={`term__shortcut term__shortcut--${s.tone}`} onClick={() => void submitLine(s.command, context, 'shortcut')}>
              {s.label}
            </button>
          ))}
        </div>
      ) : null}
      <div
        ref={logRef}
        id={`terminal-log-${context}`}
        className="term__log"
        data-testid="terminal-log"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-label={t('terminal.logLabel')}
        tabIndex={0}
      >
        {entries.map((e) => (
          <div key={e.id} className={`term__line ${KIND_CLASS[e.kind]}`} data-kind={e.kind} data-status={e.status}>
            {e.status === 'running' ? <Spinner size={11} /> : null}
            {e.status === 'cancelled' ? <span className="term__badge">{t('terminal.status.cancelled')}</span> : null}
            {e.status === 'failed' ? <span className="term__badge">{t('terminal.status.failed')}</span> : null}
            {e.status === 'done' ? <span className="sr-only">{t('terminal.status.done')}</span> : null}
            <span className="term__text">{e.text}</span>
            {e.equivalent && e.source ? <span className="term__source">{t(`terminal.source.${e.source as 'form'}`)}</span> : null}
          </div>
        ))}
      </div>
      {pendingChoice ? (
        <div className="term__choice" role="group" aria-label={pendingChoice.prompt}>
          <span>{pendingChoice.prompt}</span>
          <div className="term__choice-btns">
            {pendingChoice.choices.map((c) => (
              <button key={c.command + c.label} type="button" className="ds-btn ds-btn--lab ds-btn--sm" onClick={() => void run(c.command)}>{c.label}</button>
            ))}
            <button type="button" className="ds-btn ds-btn--ghost ds-btn--sm term__dismiss" onClick={() => useTerminal.getState().set({ pendingChoice: null })}>{t('common.cancel')}</button>
          </div>
        </div>
      ) : null}
      <form
        className="term__input-row"
        onSubmit={(e) => {
          e.preventDefault();
          if (open && active >= 0 && suggestions[active]) { accept(suggestions[active] as Suggestion); return; }
          void run(input);
        }}
      >
        <div className="term__combo">
          <label htmlFor={`term-input-${context}`} className="sr-only">{t('terminal.inputLabel')}</label>
          <input
            ref={inputRef}
            id={`term-input-${context}`}
            className="term__input"
            data-testid="terminal-input"
            value={input}
            autoComplete="off"
            spellCheck={false}
            placeholder={t(placeholderKey)}
            role="combobox"
            aria-expanded={open && suggestions.length > 0}
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={open && active >= 0 ? `${listId}-${active}` : undefined}
            onFocus={() => setOpen(true)}
            onBlur={() => window.setTimeout(() => setOpen(false), 120)}
            onChange={(e) => { setInput(e.target.value); setOpen(true); setActive(-1); setHistIdx(null); }}
            onKeyDown={(e) => {
              if (e.key === 'Tab' && open && suggestions.length && input.trim()) {
                e.preventDefault();
                accept(suggestions[Math.max(0, active)] as Suggestion);
              } else if (e.key === 'ArrowDown' && open && suggestions.length && histIdx === null) {
                e.preventDefault();
                setActive((a) => Math.min(suggestions.length - 1, a + 1));
              } else if (e.key === 'ArrowUp' && (histIdx !== null || active <= 0 || !open)) {
                if (!history.length) return;
                e.preventDefault();
                const next = histIdx === null ? history.length - 1 : Math.max(0, histIdx - 1);
                setHistIdx(next);
                setInput(history[next] ?? '');
                setOpen(false);
              } else if (e.key === 'ArrowUp' && open) {
                e.preventDefault();
                setActive((a) => Math.max(-1, a - 1));
              } else if (e.key === 'ArrowDown' && histIdx !== null) {
                e.preventDefault();
                const next = histIdx + 1;
                if (next >= history.length) { setHistIdx(null); setInput(''); }
                else { setHistIdx(next); setInput(history[next] ?? ''); }
              } else if (e.key === 'Escape') {
                if (running) cancelRunning();
                setOpen(false);
              }
            }}
          />
          {open && suggestions.length > 0 ? (
            <ul id={listId} role="listbox" className="term__suggest" aria-label={t('terminal.suggestions')}>
              {suggestions.map((s, i) => (
                <li
                  key={s.value + i}
                  id={`${listId}-${i}`}
                  role="option"
                  aria-selected={i === active}
                  className={i === active ? 'is-active' : ''}
                  onMouseDown={(e) => { e.preventDefault(); accept(s); }}
                >
                  <code>{s.label}</code>
                  <small>{s.detail}</small>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
        {running ? (
          <button type="button" className="term__submit term__submit--cancel" onClick={() => cancelRunning()} data-testid="terminal-cancel">
            <Icon name="close" size={14} /> {t('common.cancel')}
          </button>
        ) : (
          <button type="submit" className="term__submit">{t('terminal.send')}</button>
        )}
      </form>
    </div>
  );
}
