import { useEffect, useId, useRef, type ReactNode } from 'react';
import { IconButton } from './Button.tsx';

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
  closeLabel: string;
  className?: string;
}

/**
 * Diálogo modal sobre <dialog> nativo: foco preso, fundo inerte, Esc fecha e o foco volta
 * ao elemento que abriu o diálogo (7.2).
 */
export function Dialog({ open, onClose, title, description, children, footer, size = 'md', closeLabel, className = '' }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const opener = useRef<Element | null>(null);
  const titleId = useId();
  const descId = useId();
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) {
      opener.current = document.activeElement;
      try { el.showModal(); } catch { el.setAttribute('open', ''); }
    } else if (!open && el.open) {
      el.close();
      if (opener.current instanceof HTMLElement) opener.current.focus();
    }
  }, [open]);
  return (
    <dialog
      ref={ref}
      className={`ds-dialog ds-dialog--${size} ${className}`}
      aria-labelledby={titleId}
      aria-describedby={description ? descId : undefined}
      onCancel={(e) => { e.preventDefault(); onClose(); }}
      onClick={(e) => { if (e.target === ref.current) onClose(); }}
    >
      {open ? (
        <div className="ds-dialog__frame">
          <header className="ds-dialog__header">
            <h2 id={titleId} className="ds-dialog__title">{title}</h2>
            <IconButton icon="close" label={closeLabel} variant="ghost" size="sm" onClick={onClose} showTooltip={false} />
          </header>
          {description ? <div id={descId} className="ds-dialog__desc">{description}</div> : null}
          <div className="ds-dialog__body">{children}</div>
          {footer ? <footer className="ds-dialog__footer">{footer}</footer> : null}
        </div>
      ) : null}
    </dialog>
  );
}
