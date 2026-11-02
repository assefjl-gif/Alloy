import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Icon, type IconName } from '../Icon.tsx';
import { Spinner } from './misc.tsx';
import { Tooltip } from './Tooltip.tsx';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'accent' | 'lab';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: 'sm' | 'md';
  icon?: IconName;
  iconRight?: IconName;
  loading?: boolean;
  children?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'secondary', size = 'md', icon, iconRight, loading = false, className = '', children, disabled, type = 'button', ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={`ds-btn ds-btn--${variant} ds-btn--${size} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner size={14} /> : icon ? <Icon name={icon} size={size === 'sm' ? 15 : 17} /> : null}
      {children !== undefined && children !== null ? <span className="ds-btn__label">{children}</span> : null}
      {iconRight ? <Icon name={iconRight} size={15} /> : null}
    </button>
  );
});

export interface IconButtonProps extends Omit<ButtonProps, 'children' | 'icon'> {
  icon: IconName;
  /** nome acessível obrigatório (também vira tooltip) */
  label: string;
  showTooltip?: boolean;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton({ icon, label, showTooltip = true, className = '', ...rest }, ref) {
  const btn = <Button ref={ref} icon={icon} aria-label={label} className={`ds-btn--icon ${className}`} {...rest} />;
  return showTooltip ? <Tooltip content={label}>{btn}</Tooltip> : btn;
});

export interface ToggleButtonProps extends Omit<ButtonProps, 'onChange'> {
  pressed: boolean;
  onPressedChange: (next: boolean) => void;
}

/** Botão de alternância com aria-pressed (7.2). O estado também é indicado por ícone/marca, não só por cor. */
export const ToggleButton = forwardRef<HTMLButtonElement, ToggleButtonProps>(function ToggleButton(
  { pressed, onPressedChange, className = '', children, ...rest },
  ref,
) {
  return (
    <Button
      ref={ref}
      aria-pressed={pressed}
      className={`ds-toggle ${pressed ? 'is-on' : ''} ${className}`}
      onClick={() => onPressedChange(!pressed)}
      {...rest}
    >
      <span className="ds-toggle__mark" aria-hidden="true">{pressed ? '●' : '○'}</span>
      {children}
    </Button>
  );
});
