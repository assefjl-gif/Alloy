import { useToasts } from '../../stores/toast.ts';
import { Icon } from '../Icon.tsx';
import { IconButton } from './Button.tsx';

/**
 * Região de notificações. Avisos comuns em região polite (role=status); erros em
 * role=alert (assertive). Erros não somem sozinhos (WCAG 2.2.1).
 */
export function ToastRegion({ closeLabel, label }: { closeLabel: string; label: string }) {
  const toasts = useToasts((s) => s.toasts);
  const dismiss = useToasts((s) => s.dismiss);
  const polite = toasts.filter((t) => t.tone !== 'error');
  const assertive = toasts.filter((t) => t.tone === 'error');
  const render = (list: typeof toasts) =>
    list.map((t) => (
      <div key={t.id} className={`ds-toast ds-toast--${t.tone}`} data-testid="toast">
        <Icon name={t.tone === 'error' ? 'alert' : t.tone === 'success' ? 'check' : t.tone === 'warning' ? 'alert' : 'info'} size={18} />
        <div className="ds-toast__text">
          <strong>{t.title}</strong>
          {t.body ? <p>{t.body}</p> : null}
          {t.action ? (
            <button type="button" className="ds-link-btn" onClick={() => { t.action?.run(); dismiss(t.id); }}>{t.action.label}</button>
          ) : null}
        </div>
        <IconButton icon="close" label={closeLabel} size="sm" variant="ghost" showTooltip={false} onClick={() => dismiss(t.id)} />
      </div>
    ));
  return (
    <div className="ds-toast-stack" aria-label={label}>
      <div role="status" aria-live="polite" aria-atomic="false">{render(polite)}</div>
      <div role="alert" aria-live="assertive" aria-atomic="false">{render(assertive)}</div>
    </div>
  );
}
