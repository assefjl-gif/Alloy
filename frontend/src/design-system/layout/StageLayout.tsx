import type { ReactNode } from 'react';

/**
 * Layout de palco: a área principal (uma cena, um canvas) ocupa todo o espaço abaixo do
 * cabeçalho da aplicação e uma única barra lateral recolhível reúne as ferramentas.
 * Recolhida, a barra sai do fluxo e o palco ocupa a largura inteira; em tela estreita
 * (≤ 960 px) ela vira gaveta sobreposta, com fundo clicável para fechar.
 * O estado (aberta, larga) pertence a quem usa o layout. Os demais módulos seguem no Workbench.
 */
export function StageLayout({ bar, barId, barLabel, open, wide = false, onDismiss, dismissLabel, children, className = '' }: {
  bar: ReactNode;
  barId: string;
  barLabel: string;
  open: boolean;
  wide?: boolean;
  /** fecha a gaveta ao tocar fora dela (tela estreita) */
  onDismiss?: () => void;
  dismissLabel?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`ds-stage-layout ${open ? 'is-open' : ''} ${wide ? 'is-wide' : ''} ${className}`}>
      <aside id={barId} className="ds-stage-layout__bar" aria-label={barLabel} hidden={!open}>{bar}</aside>
      {open && onDismiss ? <button type="button" className="ds-stage-layout__backdrop" aria-label={dismissLabel} tabIndex={-1} onClick={onDismiss} /> : null}
      <div className="ds-stage-layout__stage">{children}</div>
    </div>
  );
}
