import type { ReactNode } from 'react';

/** Painel com título (equivalente aos .chart-panel/.table-panel do legado). */
export function Panel({ title, aside, children, className = '', id, headingLevel = 2, testId, actions }: { title: ReactNode; aside?: ReactNode; children: ReactNode; className?: string; id?: string; headingLevel?: 2 | 3; testId?: string; actions?: ReactNode }) {
  const H = headingLevel === 2 ? 'h2' : 'h3';
  return (
    <section className={`ds-panel ${className}`} id={id} data-testid={testId} aria-labelledby={id ? `${id}-title` : undefined}>
      <header className="ds-panel__title">
        <H id={id ? `${id}-title` : undefined}>{title}</H>
        {aside ? <span className="ds-panel__aside">{aside}</span> : null}
        {actions ? <span className="ds-panel__actions">{actions}</span> : null}
      </header>
      <div className="ds-panel__body">{children}</div>
    </section>
  );
}
