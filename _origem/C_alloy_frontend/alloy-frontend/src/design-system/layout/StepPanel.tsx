import type { ReactNode } from 'react';

export interface StepItem {
  title: ReactNode;
  body?: ReactNode;
  status?: 'todo' | 'current' | 'done' | 'error';
}

/** Lista ordenada de passos (passo a passo do motor, fluxo de exercício). */
export function StepPanel({ steps, label, start = 1 }: { steps: StepItem[]; label: string; start?: number }) {
  return (
    <ol className="ds-steps" aria-label={label} start={start}>
      {steps.map((s, i) => (
        <li key={i} className={`ds-step ds-step--${s.status ?? 'todo'}`} aria-current={s.status === 'current' ? 'step' : undefined}>
          <span className="ds-step__index" aria-hidden="true">{s.status === 'done' ? '✓' : i + start}</span>
          <div className="ds-step__content">
            <strong className="ds-step__title">{s.title}</strong>
            {s.body ? <div className="ds-step__body">{s.body}</div> : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
