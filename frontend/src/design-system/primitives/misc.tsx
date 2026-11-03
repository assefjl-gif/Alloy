import type { ReactNode } from 'react';

export function VisuallyHidden({ children, as: Tag = 'span', id }: { children: ReactNode; as?: 'span' | 'div' | 'h2' | 'h3'; id?: string }) {
  return <Tag className="sr-only" id={id}>{children}</Tag>;
}

export function Spinner({ size = 16, label }: { size?: number; label?: string }) {
  return (
    <span className="ds-spinner" style={{ width: size, height: size }} role={label ? 'status' : undefined} aria-label={label} aria-hidden={label ? undefined : true} />
  );
}

export function Kbd({ children }: { children: ReactNode }) {
  return <kbd className="ds-kbd">{children}</kbd>;
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'accent' }) {
  return <span className={`ds-badge ds-badge--${tone}`}>{children}</span>;
}
