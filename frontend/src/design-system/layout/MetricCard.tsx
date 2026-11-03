import type { ReactNode } from 'react';
import { CategoryTag, type InfoCategory } from '../primitives/Category.tsx';

/** Cartão de grandeza (resultado do motor, dado de referência ou valor demonstrativo). */
export function MetricCard({ label, value, unit, category, categoryLabel, hint, testId }: { label: string; value: ReactNode; unit?: ReactNode; category: InfoCategory; categoryLabel: string; hint?: ReactNode; testId?: string }) {
  return (
    <article className={`ds-metric ds-cat-box ds-cat-box--${category}`} data-category={category} data-testid={testId}>
      <header className="ds-metric__head">
        <span className="ds-label">{label}</span>
        <CategoryTag category={category} label={categoryLabel} compact />
      </header>
      <span className="ds-metric__value">{value}</span>
      {unit ? <span className="ds-metric__unit">{unit}</span> : null}
      {hint ? <span className="ds-metric__hint">{hint}</span> : null}
    </article>
  );
}
