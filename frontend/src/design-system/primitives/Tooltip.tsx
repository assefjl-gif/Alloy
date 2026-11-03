import { cloneElement, isValidElement, useEffect, useId, useRef, useState, type ReactElement, type ReactNode } from 'react';

/**
 * Tooltip acessível: aparece em foco e em hover, some com Esc, liga-se ao gatilho por
 * aria-describedby. Não carrega informação essencial que não esteja também visível ou no nome.
 */
export function Tooltip({ content, children, placement = 'top' }: { content: ReactNode; children: ReactElement; placement?: 'top' | 'bottom' }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  if (!isValidElement(children)) return children;
  const show = () => { window.clearTimeout(timer.current); timer.current = window.setTimeout(() => setOpen(true), 350); };
  const hide = () => { window.clearTimeout(timer.current); setOpen(false); };
  const child = children as ReactElement<Record<string, unknown>>;
  const props = child.props;
  const call = (name: string, e: unknown) => { const fn = props[name]; if (typeof fn === 'function') (fn as (ev: unknown) => void)(e); };
  return (
    <span className="ds-tooltip-anchor" onMouseEnter={show} onMouseLeave={hide}>
      {cloneElement(child, {
        'aria-describedby': open ? id : (props['aria-describedby'] as string | undefined),
        onFocus: (e: unknown) => { call('onFocus', e); setOpen(true); },
        onBlur: (e: unknown) => { call('onBlur', e); setOpen(false); },
      })}
      {open ? (
        <span role="tooltip" id={id} className={`ds-tooltip ds-tooltip--${placement}`}>{content}</span>
      ) : null}
    </span>
  );
}
