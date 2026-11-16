import { forwardRef, useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react';
import { IconButton } from './Button.tsx';

interface FieldShell {
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  /** rótulo visualmente oculto (continua acessível) */
  hideLabel?: boolean;
  className?: string;
}

function useFieldIds(id?: string) {
  const auto = useId();
  const base = id ?? auto;
  return { id: base, hint: `${base}-hint`, error: `${base}-error` };
}

function Shell({ ids, label, hint, error, hideLabel, className = '', children }: FieldShell & { ids: ReturnType<typeof useFieldIds>; children: ReactNode }) {
  return (
    <div className={`ds-field ${error ? 'has-error' : ''} ${className}`}>
      <label htmlFor={ids.id} className={hideLabel ? 'sr-only' : 'ds-field__label'}>{label}</label>
      {children}
      {hint ? <span id={ids.hint} className="ds-field__hint">{hint}</span> : null}
      {error ? <span id={ids.error} className="ds-field__error" role="alert">{error}</span> : null}
    </div>
  );
}

function described(ids: ReturnType<typeof useFieldIds>, hint: unknown, error: unknown): string | undefined {
  return [hint ? ids.hint : '', error ? ids.error : ''].filter(Boolean).join(' ') || undefined;
}

export const TextInput = forwardRef<HTMLInputElement, FieldShell & InputHTMLAttributes<HTMLInputElement>>(function TextInput({ label, hint, error, hideLabel, className, id, ...rest }, ref) {
  const ids = useFieldIds(id);
  return (
    <Shell ids={ids} label={label} hint={hint} error={error} hideLabel={hideLabel} className={className}>
      <input ref={ref} id={ids.id} className="ds-input" aria-invalid={error ? true : undefined} aria-describedby={described(ids, hint, error)} {...rest} />
    </Shell>
  );
});

export const TextArea = forwardRef<HTMLTextAreaElement, FieldShell & TextareaHTMLAttributes<HTMLTextAreaElement>>(function TextArea({ label, hint, error, hideLabel, className, id, ...rest }, ref) {
  const ids = useFieldIds(id);
  return (
    <Shell ids={ids} label={label} hint={hint} error={error} hideLabel={hideLabel} className={className}>
      <textarea ref={ref} id={ids.id} className="ds-input ds-textarea" aria-invalid={error ? true : undefined} aria-describedby={described(ids, hint, error)} {...rest} />
    </Shell>
  );
});

export const Select = forwardRef<HTMLSelectElement, FieldShell & SelectHTMLAttributes<HTMLSelectElement> & { options: Array<{ value: string; label: string; disabled?: boolean }> }>(function Select({ label, hint, error, hideLabel, className, id, options, ...rest }, ref) {
  const ids = useFieldIds(id);
  return (
    <Shell ids={ids} label={label} hint={hint} error={error} hideLabel={hideLabel} className={className}>
      <select ref={ref} id={ids.id} className="ds-input ds-select" aria-invalid={error ? true : undefined} aria-describedby={described(ids, hint, error)} {...rest}>
        {options.map((o) => <option key={o.value} value={o.value} disabled={o.disabled}>{o.label}</option>)}
      </select>
    </Shell>
  );
});

export function Checkbox({ label, checked, onChange, hint, disabled, id }: { label: ReactNode; checked: boolean; onChange: (v: boolean) => void; hint?: ReactNode; disabled?: boolean; id?: string }) {
  const ids = useFieldIds(id);
  return (
    <div className="ds-check">
      <input type="checkbox" id={ids.id} checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} aria-describedby={hint ? ids.hint : undefined} />
      <label htmlFor={ids.id}>{label}</label>
      {hint ? <span id={ids.hint} className="ds-field__hint">{hint}</span> : null}
    </div>
  );
}

/** Grupo de opções exclusivas (radiogroup nativo, navegável por setas). */
export function Segmented<T extends string>({ label, value, options, onChange, name, hideLabel = false, size = 'md' }: { label: string; value: T; options: Array<{ value: T; label: string; disabled?: boolean }>; onChange: (v: T) => void; name: string; hideLabel?: boolean; size?: 'sm' | 'md' }) {
  return (
    <fieldset className={`ds-segmented ds-segmented--${size}`}>
      <legend className={hideLabel ? 'sr-only' : 'ds-field__label'}>{label}</legend>
      <div className="ds-segmented__track">
        {options.map((o) => (
          <label key={o.value} className={`ds-segmented__opt ${o.value === value ? 'is-on' : ''} ${o.disabled ? 'is-disabled' : ''}`}>
            <input type="radio" name={name} value={o.value} checked={o.value === value} disabled={o.disabled} onChange={() => onChange(o.value)} />
            <span>{o.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function Slider({ label, value, min, max, step = 1, onChange, valueText, id }: { label: ReactNode; value: number; min: number; max: number; step?: number; onChange: (v: number) => void; valueText?: string; id?: string }) {
  const ids = useFieldIds(id);
  return (
    <div className="ds-field ds-slider">
      <label htmlFor={ids.id} className="ds-field__label">{label} <output htmlFor={ids.id}>{valueText ?? value}</output></label>
      <input id={ids.id} type="range" min={min} max={max} step={step} value={value} aria-valuetext={valueText} onChange={(e) => onChange(Number(e.target.value))} />
    </div>
  );
}

/**
 * Seletor de cor (T-22). Acessibilidade: a escolha NUNCA é comunicada só pela cor — há rótulo em
 * texto, o valor hexadecimal aparece escrito, e o estado "personalizada" é dito por palavra.
 * `value = null` significa "cor padrão da cena"; nesse caso o seletor mostra `defaultValue`.
 */
export function ColorInput({ label, value, defaultValue, onChange, onReset, hint, id, customText, resetLabel, disabled, testId }: {
  label: ReactNode;
  value: string | null;
  defaultValue: string;
  onChange: (color: string) => void;
  onReset: () => void;
  hint?: ReactNode;
  id?: string;
  /** palavra que diz que a cor foi escolhida pela pessoa (não é só a cor que informa isso) */
  customText: string;
  resetLabel: string;
  disabled?: boolean;
  testId?: string;
}) {
  const ids = useFieldIds(id);
  const shown = (value ?? defaultValue).toUpperCase();
  return (
    <div className="ds-field ds-color">
      <label htmlFor={ids.id} className="ds-field__label">{label}</label>
      <div className="ds-color__row">
        <input
          id={ids.id}
          type="color"
          className="ds-color__input"
          value={value ?? defaultValue}
          disabled={disabled}
          data-testid={testId}
          aria-describedby={described(ids, hint, undefined)}
          onChange={(e) => onChange(e.target.value)}
        />
        <span className="ds-color__hex ds-mono" data-testid={testId ? `${testId}-hex` : undefined}>{shown}</span>
        {value !== null ? <span className="ds-color__tag">{customText}</span> : null}
        {value !== null ? (
          <IconButton size="sm" variant="ghost" icon="restart" label={resetLabel} data-testid={testId ? `${testId}-reset` : undefined} onClick={onReset} />
        ) : null}
      </div>
      {hint ? <span id={ids.hint} className="ds-field__hint">{hint}</span> : null}
    </div>
  );
}
