/**
 * Raiz da aplicação: AppShell com navegação por módulo (sem recarga), ações globais
 * (conectividade, selo demonstrativo, paleta Ctrl/⌘K, configurações) e módulos carregados
 * sob demanda (code splitting). O foco vai para o <main> do módulo ao trocar de rota.
 */
import { Suspense, lazy, useEffect, useRef, useState } from 'react';
import { useI18n } from '../i18n/index.ts';
import { useRoute } from './router.ts';
import type { ModuleId } from '../commands/types.ts';
import { AppShell } from '../design-system/layout/AppShell.tsx';
import { ModuleNavigation, type ModuleLink } from '../design-system/layout/ModuleNavigation.tsx';
import { IconButton } from '../design-system/primitives/Button.tsx';
import { ToastRegion } from '../design-system/primitives/Toast.tsx';
import { Badge, Spinner, Kbd } from '../design-system/primitives/misc.tsx';
import { Icon } from '../design-system/Icon.tsx';
import { useCapabilities, useServiceMode } from '../stores/capabilities.ts';
import { usePreferences } from '../stores/preferences.ts';
import { useAccount } from '../stores/account.ts';
import { CommandPalette } from '../features/palette/CommandPalette.tsx';
import { SettingsDialog } from './SettingsDialog.tsx';
import CrystaLabModule from '../modules/crystalab/CrystaLabModule.tsx';

const HeaModule = lazy(() => import('../modules/hea/HeaModule.tsx'));
const LearnModule = lazy(() => import('../modules/didactics/LearnModule.tsx'));
const NotebookModule = lazy(() => import('../modules/notebook/NotebookModule.tsx'));
const InstructorModule = lazy(() => import('../modules/instructor/InstructorModule.tsx'));
const CatalogModule = lazy(() => import('../modules/catalog/CatalogModule.tsx'));
const AboutModule = lazy(() => import('../modules/about/AboutModule.tsx'));
const AccountModule = lazy(() => import('../modules/account/AccountModule.tsx'));

function ConnectivityIndicator() {
  const { t } = useI18n();
  const online = useCapabilities((s) => s.online);
  const ready = useCapabilities((s) => s.ready);
  const cl = useServiceMode('crystalab');
  const state = !online ? 'offline' : !ready ? 'checking' : cl === 'live' ? 'online' : 'engineOff';
  return (
    <a href="#/sobre" className={`conn conn--${state}`} data-testid="connectivity" aria-label={t(`conn.${state}`)} title={t(`conn.${state}`)}>
      <Icon name={state === 'offline' ? 'wifiOff' : state === 'engineOff' ? 'server' : 'wifi'} size={16} />
      <span className="conn__text">{t(`conn.short.${state}`)}</span>
    </a>
  );
}

function AccountLink() {
  const { t } = useI18n();
  const user = useAccount((s) => s.user);
  const label = user ? t('account.signedInAs', { name: user.nome }) : t('nav.account');
  return <a className="ds-btn ds-btn--ghost ds-btn--icon" href="#/conta" aria-label={label} title={label} data-testid="account-link"><Icon name={user ? 'unlock' : 'lock'} size={18} /></a>;
}

function DemoIndicator() {
  const { t } = useI18n();
  const hea = useServiceMode('hea');
  if (hea !== 'demo') return null;
  return <a href="#/sobre" className="demo-pill" data-testid="demo-indicator" title={t('demo.indicatorTitle')}><Badge tone="warning">{t('common.demo')}</Badge></a>;
}

function ModuleView({ module }: { module: ModuleId }) {
  switch (module) {
    case 'hea': return <HeaModule />;
    case 'aprender': return <LearnModule />;
    case 'diario': return <NotebookModule />;
    case 'professor': return <InstructorModule />;
    case 'catalogo': return <CatalogModule />;
    case 'sobre': return <AboutModule />;
    case 'conta': return <AccountModule />;
    default: return <CrystaLabModule />;
  }
}

export function App() {
  const { t } = useI18n();
  const route = useRoute();
  const role = usePreferences((p) => p.role);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const firstRender = useRef(true);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen((o) => !o);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    const titles: Record<ModuleId, string> = { crystalab: t('nav.crystalab'), hea: t('nav.hea'), aprender: t('nav.learn'), diario: t('nav.notebook'), professor: t('nav.instructor'), catalogo: t('nav.catalog'), sobre: t('nav.about'), conta: t('nav.account') };
    document.title = `${titles[route.module]} · Alloy Virtual Lab`;
    if (firstRender.current) { firstRender.current = false; return; }
    const h = window.setTimeout(() => (document.getElementById('main-content') as HTMLElement | null)?.focus({ preventScroll: true }), 60);
    return () => window.clearTimeout(h);
  }, [route.module, t]);

  const links: ModuleLink[] = [
    { id: 'crystalab', href: '#/crystalab', label: t('nav.crystalab'), icon: 'cube' },
    { id: 'hea', href: '#/hea', label: t('nav.hea'), icon: 'flask' },
    { id: 'aprender', href: '#/aprender', label: t('nav.learn'), icon: 'book' },
    { id: 'diario', href: '#/diario', label: t('nav.notebook'), icon: 'notebook' },
    ...(role === 'instructor' ? [{ id: 'professor', href: '#/professor', label: t('nav.instructor'), icon: 'teacher' as const }] : []),
  ];

  return (
    <AppShell
      skipLabel={t('a11y.skip')}
      brand={<a href="#/crystalab" className="brand" aria-label="Alloy Virtual Lab — CrystaLab"><span className="brand__mark" aria-hidden="true">◆</span><span className="brand__name">Alloy</span><span className="brand__sub">Virtual Lab</span></a>}
      nav={<ModuleNavigation label={t('nav.modules')} links={links} current={route.module} />}
      actions={
        <>
          <DemoIndicator />
          <ConnectivityIndicator />
          <button type="button" className="palette-trigger" onClick={() => setPaletteOpen(true)} data-testid="palette-button" aria-keyshortcuts="Control+K Meta+K">
            <Icon name="search" size={16} /><span className="palette-trigger__text">{t('palette.open')}</span><span className="palette-trigger__kbd" aria-hidden="true"><Kbd>Ctrl</Kbd><Kbd>K</Kbd></span>
          </button>
          <IconButton icon="settings" label={t('settings.title')} onClick={() => setSettingsOpen(true)} data-testid="settings-button" />
          <AccountLink />
          <a className="ds-btn ds-btn--ghost ds-btn--icon" href="#/sobre" aria-label={t('nav.about')} title={t('nav.about')}><Icon name="info" size={18} /></a>
        </>
      }
      overlays={
        <>
          <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
          <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
          <ToastRegion closeLabel={t('common.close')} label={t('a11y.notifications')} />
        </>
      }
    >
      <Suspense fallback={<div className="empty-state" role="status"><Spinner size={22} label={t('common.loading')} /></div>}>
        <ModuleView module={route.module} />
      </Suspense>
    </AppShell>
  );
}
