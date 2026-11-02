import { useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { Button, type ButtonProps } from './Button.tsx';
import { Icon, type IconName } from '../Icon.tsx';

export interface MenuItem {
  id: string;
  label: string;
  description?: string;
  icon?: IconName;
  disabled?: boolean;
  /** motivo exibido quando desativado (ex.: pendência D-05) */
  disabledReason?: string;
  onSelect: () => void;
}

/** Menu de ações (padrão WAI-ARIA menu button): setas, Home/End, Esc fecha e devolve o foco. */
export function Menu({ label, icon, items, buttonProps, align = 'start', children }: { label: string; icon?: IconName; items: MenuItem[]; buttonProps?: Partial<ButtonProps>; align?: 'start' | 'end'; children?: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const btn = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const menuId = useId();
  useEffect(() => {
    if (!open) return undefined;
    const first = items.findIndex((i) => !i.disabled);
    setActive(first < 0 ? 0 : first);
    const onDoc = (e: MouseEvent) => {
      if (!list.current?.contains(e.target as Node) && !btn.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open, items]);
  useEffect(() => {
    if (open) (list.current?.querySelectorAll<HTMLElement>('[role="menuitem"]')[active])?.focus();
  }, [open, active]);
  const close = (focus = true) => { setOpen(false); if (focus) btn.current?.focus(); };
  const move = (delta: number) => {
    const n = items.length;
    setActive((cur) => (cur + delta + n) % n);
  };
  return (
    <div className={`ds-menu ds-menu--${align}`}>
      <Button
        ref={btn}
        icon={icon}
        iconRight="chevronDown"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => { if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); } }}
        {...buttonProps}
      >
        {children ?? label}
      </Button>
      {open ? (
        <ul
          ref={list}
          id={menuId}
          role="menu"
          aria-label={label}
          className="ds-menu__list"
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
            else if (e.key === 'Home') { e.preventDefault(); setActive(0); }
            else if (e.key === 'End') { e.preventDefault(); setActive(items.length - 1); }
            else if (e.key === 'Escape') { e.preventDefault(); close(); }
            else if (e.key === 'Tab') close(false);
          }}
        >
          {items.map((item, i) => (
            <li key={item.id} role="none">
              <button
                type="button"
                role="menuitem"
                tabIndex={i === active ? 0 : -1}
                aria-disabled={item.disabled || undefined}
                className="ds-menu__item"
                onClick={() => { if (item.disabled) return; close(); item.onSelect(); }}
              >
                {item.icon ? <Icon name={item.icon} size={16} /> : null}
                <span className="ds-menu__text">
                  <span>{item.label}</span>
                  {item.disabled && item.disabledReason ? <small>{item.disabledReason}</small> : item.description ? <small>{item.description}</small> : null}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
