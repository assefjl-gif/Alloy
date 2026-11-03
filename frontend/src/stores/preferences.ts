import { create } from 'zustand';
import type { DemoPolicy } from '../config.ts';
import { readJSON, readRaw, writeJSON } from '../utils/storage.ts';
import type { Locale } from '../utils/format.ts';

export type ThemePref = 'light' | 'dark' | 'system';
export type MotionPref = 'system' | 'reduce' | 'full';
export type Role = 'student' | 'instructor';

export interface PreferencesState {
  theme: ThemePref;
  locale: Locale;
  motion: MotionPref;
  /** 'config' = segue public/config.js; senão sobrescreve a política de demonstração. */
  demo: DemoPolicy | 'config';
  role: Role;
  /** Em telas de toque, a cena começa travada (um dedo rola a página; dois dedos giram). */
  touchSceneLock: boolean;
  set: (patch: Partial<Omit<PreferencesState, 'set'>>) => void;
}

const KEY = 'alloy.prefs';
const LOCALES: Locale[] = ['pt-BR', 'en', 'es'];

function detectLocale(): Locale {
  const nav = (globalThis.navigator?.language ?? 'pt-BR').toLowerCase();
  if (nav.startsWith('es')) return 'es';
  if (nav.startsWith('en')) return 'en';
  return 'pt-BR';
}

function initial(): Omit<PreferencesState, 'set'> {
  const saved = readJSON<Partial<PreferencesState>>(KEY, {});
  const legacyTheme = readRaw('crystalab-theme'); // chave do CrystaLab v1.0 (preservada)
  return {
    theme: saved.theme ?? (legacyTheme === 'dark' || legacyTheme === 'light' ? legacyTheme : 'system'),
    locale: saved.locale && LOCALES.includes(saved.locale) ? saved.locale : detectLocale(),
    motion: saved.motion ?? 'system',
    demo: saved.demo ?? 'config',
    role: saved.role ?? 'student',
    touchSceneLock: saved.touchSceneLock ?? true,
  };
}

export const usePreferences = create<PreferencesState>()((set) => ({
  ...initial(),
  set: (patch) => set(patch),
}));

usePreferences.subscribe((s) => {
  const { set: _ignored, ...data } = s;
  void _ignored;
  writeJSON(KEY, data);
});

export function effectiveTheme(pref: ThemePref): 'light' | 'dark' {
  if (pref !== 'system') return pref;
  return globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function prefersReducedMotion(pref: MotionPref): boolean {
  if (pref === 'reduce') return true;
  if (pref === 'full') return false;
  return Boolean(globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
}
