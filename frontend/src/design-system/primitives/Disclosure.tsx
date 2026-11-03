import { useId, useState, type ReactNode } from 'react';
import { Icon } from '../Icon.tsx';

/** Seção recolhível (7.7): botão com aria-expanded controla a região. */
export function Disclosure({ title, defaultOpen = true, children, aside, headingLevel = 2, className = '', id, open: controlled, onOpenChange }: { title: ReactNode; defaultOpen?: boolean; children: ReactNode; aside?: ReactNode; headingLevel?: 2 | 3; className?: string; id?: string; open?: boolean; onOpenChange?: (open: boolean) => void }) {
  const [inner, setInner] = useState(defaultOpen);
  const open = controlled ?? inner;
  const auto = useId();
  const regionId = id ?? `disc-${auto}`;
  const H = headingLevel === 2 ? 'h2' : 'h3';
  const toggle = () => { const next = !open; setInner(next); onOpenChange?.(next); };
  return (
    <section className={`ds-disclosure ${open ? 'is-open' : ''} ${className}`}>
      <H className="ds-disclosure__heading">
        <button type="button" aria-expanded={open} aria-controls={regionId} onClick={toggle} className="ds-disclosure__btn">
          <Icon name={open ? 'chevronDown' : 'chevronRight'} size={16} />
          <span>{title}</span>
        </button>
        {aside ? <span className="ds-disclosure__aside">{aside}</span> : null}
      </H>
      <div id={regionId} className="ds-disclosure__body" hidden={!open}>{children}</div>
    </section>
  );
}
