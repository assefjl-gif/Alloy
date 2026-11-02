import type { ReactNode } from 'react';

/**
 * Estrutura da aplicação (2.13): cabeçalho fixo com navegação por módulo, área do módulo
 * e regiões globais (anúncios aria-live, notificações). O conteúdo do módulo usa Workbench.
 */
export function AppShell({ brand, nav, actions, children, skipLabel, overlays }: { brand: ReactNode; nav: ReactNode; actions: ReactNode; children: ReactNode; skipLabel: string; overlays?: ReactNode }) {
  return (
    <div className="ds-app">
      <a href="#main-content" className="ds-skip-link">{skipLabel}</a>
      <header className="ds-app__header">
        <div className="ds-app__brand">{brand}</div>
        <div className="ds-app__nav">{nav}</div>
        <div className="ds-app__actions">{actions}</div>
      </header>
      <div className="ds-app__body">{children}</div>
      <div id="alloy-live-polite" className="sr-only" aria-live="polite" aria-atomic="true" />
      <div id="alloy-live-assertive" className="sr-only" aria-live="assertive" aria-atomic="true" />
      {overlays}
    </div>
  );
}

/**
 * Layout do laboratório: painel do laboratório (esquerda), área central (viewer/atividade +
 * resultados) e painel lateral (direita). Abaixo de 1180 px o painel lateral vira gaveta;
 * abaixo de 860 px tudo empilha e os painéis viram seções recolhíveis (7.7).
 */
export function Workbench({ lab, center, side, sideOpen, sideLabel, sideInline = false, className = '' }: { lab?: ReactNode; center: ReactNode; side?: ReactNode; sideOpen?: boolean; sideLabel?: string; /** em telas estreitas o painel lateral vai para baixo do conteúdo em vez de virar gaveta */ sideInline?: boolean; className?: string }) {
  return (
    <div className={`ds-workbench ${side ? 'has-side' : ''} ${lab ? 'has-lab' : ''} ${sideOpen ? 'side-open' : ''} ${sideInline ? 'side-inline' : ''} ${className}`}>
      {lab ? <aside className="ds-workbench__lab">{lab}</aside> : null}
      <div className="ds-workbench__center">{center}</div>
      {side ? <aside className="ds-workbench__side" aria-label={sideLabel}>{side}</aside> : null}
    </div>
  );
}
