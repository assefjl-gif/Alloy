import type { ReactNode } from 'react';

/** Agrupador de preferências: cada grupo com título e descrição curta. */
export function SettingsPanel({ groups }: { groups: Array<{ id: string; title: string; description?: string; content: ReactNode }> }) {
  return (
    <div className="ds-settings">
      {groups.map((g) => (
        <section key={g.id} className="ds-settings__group" aria-labelledby={`settings-${g.id}`}>
          <h3 id={`settings-${g.id}`}>{g.title}</h3>
          {g.description ? <p className="ds-muted">{g.description}</p> : null}
          <div className="ds-settings__content">{g.content}</div>
        </section>
      ))}
    </div>
  );
}
