import type { ReactNode } from 'react';
import { Icon, type IconName } from '../Icon.tsx';

/**
 * Seis categorias de informação (2.11) + nota pessoal (6.14). Cada uma tem cor, ícone,
 * rótulo textual e estilo de borda próprios — a categoria nunca é comunicada só por cor.
 */
export type InfoCategory = 'result' | 'param' | 'reference' | 'control' | 'feedback' | 'demo' | 'note';

export const CATEGORY_ICON: Record<InfoCategory, IconName> = {
  result: 'calc',
  param: 'pencil',
  reference: 'book',
  control: 'eye',
  feedback: 'bulb',
  demo: 'demo',
  note: 'notebook',
};

export function CategoryTag({ category, label, compact = false }: { category: InfoCategory; label: string; compact?: boolean }) {
  return (
    <span className={`ds-cat-tag ds-cat-tag--${category} ${compact ? 'is-compact' : ''}`} data-category={category}>
      <Icon name={CATEGORY_ICON[category]} size={13} />
      <span className={compact ? 'sr-only' : undefined}>{label}</span>
    </span>
  );
}

export function CategoryBox({ category, children, className = '', as: Tag = 'div', ...rest }: { category: InfoCategory; children: ReactNode; className?: string; as?: 'div' | 'section' | 'article' | 'aside' } & Record<string, unknown>) {
  return (
    <Tag className={`ds-cat-box ds-cat-box--${category} ${className}`} data-category={category} {...rest}>
      {children}
    </Tag>
  );
}

/** Selo "DEMONSTRATIVO" (2.6): sempre visível onde houver dado de serviço ausente. */
export function DemoSeal({ text, detail }: { text: string; detail?: string }) {
  return (
    <span className="ds-demo-seal" data-testid="demo-seal" title={detail}>
      <Icon name="demo" size={13} />
      {text}
      {detail ? <span className="sr-only">{` — ${detail}`}</span> : null}
    </span>
  );
}
