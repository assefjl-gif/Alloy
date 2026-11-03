import { Icon, type IconName } from '../Icon.tsx';

export interface ModuleLink {
  id: string;
  href: string;
  label: string;
  icon: IconName;
  badge?: string;
}

/** Navegação entre módulos sem recarga (links de hash; aria-current na página ativa). */
export function ModuleNavigation({ label, links, current }: { label: string; links: ModuleLink[]; current: string }) {
  return (
    <nav aria-label={label} className="ds-modnav">
      <ul>
        {links.map((l) => (
          <li key={l.id}>
            <a href={l.href} className={`ds-modnav__link ${l.id === current ? 'is-current' : ''}`} aria-current={l.id === current ? 'page' : undefined} data-module={l.id}>
              <Icon name={l.icon} size={17} />
              <span>{l.label}</span>
              {l.badge ? <span className="ds-modnav__badge">{l.badge}</span> : null}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
