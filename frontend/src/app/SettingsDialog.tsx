import { useI18n, pick } from '../i18n/index.ts';
import { usePreferences, type MotionPref, type Role, type ThemePref } from '../stores/preferences.ts';
import type { DemoPolicy } from '../config.ts';
import type { Locale } from '../utils/format.ts';
import { Dialog } from '../design-system/primitives/Dialog.tsx';
import { Button } from '../design-system/primitives/Button.tsx';
import { Checkbox, Segmented, Select } from '../design-system/primitives/Field.tsx';
import { SettingsPanel } from '../design-system/layout/SettingsPanel.tsx';
import { PENDING } from '../services/adapters/pending.ts';

export function SettingsDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t, locale } = useI18n();
  const p = usePreferences();
  return (
    <Dialog open={open} onClose={onClose} title={t('settings.title')} closeLabel={t('common.close')} size="lg" footer={<Button variant="primary" onClick={onClose}>{t('common.done')}</Button>}>
      <SettingsPanel groups={[
        { id: 'appearance', title: t('settings.appearance'), content: (
          <>
            <Segmented<ThemePref> name="theme" label={t('settings.theme')} value={p.theme} onChange={(v) => p.set({ theme: v })} options={[{ value: 'light', label: t('settings.themeLight') }, { value: 'dark', label: t('settings.themeDark') }, { value: 'system', label: t('settings.themeSystem') }]} />
            <Segmented<MotionPref> name="motion" label={t('settings.motion')} value={p.motion} onChange={(v) => p.set({ motion: v })} options={[{ value: 'system', label: t('settings.themeSystem') }, { value: 'reduce', label: t('settings.motionReduce') }, { value: 'full', label: t('settings.motionFull') }]} />
          </>
        ) },
        { id: 'language', title: t('settings.language'), description: t('settings.languageHint'), content: (
          <Select label={t('settings.language')} hideLabel value={p.locale} onChange={(e) => p.set({ locale: e.target.value as Locale })} options={[{ value: 'pt-BR', label: 'Português (Brasil)' }, { value: 'en', label: 'English' }, { value: 'es', label: 'Español' }]} data-testid="locale-select" />
        ) },
        { id: 'demo', title: t('settings.demo'), description: t('settings.demoHint'), content: (
          <Segmented<DemoPolicy | 'config'> name="demo" label={t('settings.demo')} hideLabel value={p.demo} onChange={(v) => p.set({ demo: v })} options={[{ value: 'config', label: t('settings.demoConfig') }, { value: 'auto', label: t('settings.demoAuto') }, { value: 'on', label: t('settings.demoOn') }, { value: 'off', label: t('settings.demoOff') }]} />
        ) },
        { id: 'role', title: t('settings.role'), description: t('settings.roleHint'), content: (
          <Segmented<Role> name="role" label={t('settings.role')} hideLabel value={p.role} onChange={(v) => p.set({ role: v })} options={[{ value: 'student', label: t('settings.student') }, { value: 'instructor', label: t('settings.instructor') }]} />
        ) },
        { id: 'touch', title: t('settings.touch'), content: (
          <Checkbox label={t('settings.touchLock')} hint={t('settings.touchLockHint')} checked={p.touchSceneLock} onChange={(v) => p.set({ touchSceneLock: v })} />
        ) },
        { id: 'pending', title: t('settings.pending'), description: t('settings.pendingHint'), content: (
          <ul className="pending-list" data-testid="pending-list">
            {PENDING.map((d) => <li key={d.id}><strong>{d.id}</strong> {pick(d.title, locale)} — <span className="ds-muted">{pick(d.behavior, locale)}</span></li>)}
          </ul>
        ) },
      ]} />
    </Dialog>
  );
}
