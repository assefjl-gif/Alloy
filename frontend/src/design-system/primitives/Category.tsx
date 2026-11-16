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

/**
 * Selo de origem não-preditiva (2.6), em DUAS variantes de significado diferente (decisão D-R2-2):
 *  - `demo`         → o número é FICTÍCIO, não há dado nem motor por tras dele;
 *  - `illustrative` → representação sem pretensão preditiva FEITA SOBRE DADO REAL do motor.
 * As duas se distinguem por texto, ícone, cor e estilo de borda — nunca só por cor.
 * O `data-testid` continua `demo-seal` nas duas (testes do legado), e `data-seal` diz qual é.
 */
export function DemoSeal({ text, detail, variant = 'demo' }: { text: string; detail?: string; variant?: 'demo' | 'illustrative' }) {
  return (
    <span className={`ds-demo-seal ds-demo-seal--${variant}`} data-testid="demo-seal" data-seal={variant} title={detail}>
      <Icon name={variant === 'illustrative' ? 'eye' : 'demo'} size={13} />
      {text}
      {detail ? <span className="sr-only">{` — ${detail}`}</span> : null}
    </span>
  );
}
