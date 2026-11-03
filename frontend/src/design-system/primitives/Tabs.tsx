import { useRef, type ReactNode } from 'react';

export interface TabItem {
  id: string;
  label: string;
  badge?: ReactNode;
}

/** Abas (WAI-ARIA tabs, ativação automática): setas esquerda/direita, Home/End. */
export function Tabs({ label, items, value, onChange, idPrefix, size = 'md' }: { label: string; items: TabItem[]; value: string; onChange: (id: string) => void; idPrefix: string; size?: 'sm' | 'md' }) {
  const ref = useRef<HTMLDivElement>(null);
  const focusTab = (id: string) => ref.current?.querySelector<HTMLElement>(`#${idPrefix}-tab-${id}`)?.focus();
  const go = (delta: number) => {
    const idx = items.findIndex((i) => i.id === value);
    const next = items[(idx + delta + items.length) % items.length];
    if (next) { onChange(next.id); focusTab(next.id); }
  };
  return (
    <div
      ref={ref}
      role="tablist"
      aria-label={label}
      className={`ds-tabs ds-tabs--${size}`}
      onKeyDown={(e) => {
        if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
        else if (e.key === 'Home') { e.preventDefault(); const f = items[0]; if (f) { onChange(f.id); focusTab(f.id); } }
        else if (e.key === 'End') { e.preventDefault(); const l = items[items.length - 1]; if (l) { onChange(l.id); focusTab(l.id); } }
      }}
    >
      {items.map((item) => {
        const selected = item.id === value;
        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            id={`${idPrefix}-tab-${item.id}`}
            aria-selected={selected}
            aria-controls={`${idPrefix}-panel-${item.id}`}
            tabIndex={selected ? 0 : -1}
            className={`ds-tab ${selected ? 'is-selected' : ''}`}
            onClick={() => onChange(item.id)}
          >
            {item.label}
            {item.badge !== undefined ? <span className="ds-tab__badge">{item.badge}</span> : null}
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({ idPrefix, id, active, children }: { idPrefix: string; id: string; active: boolean; children: ReactNode }) {
  return (
    <div role="tabpanel" id={`${idPrefix}-panel-${id}`} aria-labelledby={`${idPrefix}-tab-${id}`} hidden={!active} tabIndex={0} className="ds-tabpanel">
      {active ? children : null}
    </div>
  );
}
