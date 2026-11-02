import { useMemo } from 'react';
import { usePreferences } from '../stores/preferences.ts';
import { formatCompact, formatNumber, formatScientific, type Locale } from '../utils/format.ts';
import ptBR from './locales/pt-BR.ts';
import en from './locales/en.ts';
import es from './locales/es.ts';

export type { Locale };
export const LOCALES: readonly Locale[] = ['pt-BR', 'en', 'es'] as const;

type Leaves<T, P extends string = ''> = {
  [K in keyof T & string]: T[K] extends string ? `${P}${K}` : Leaves<T[K], `${P}${K}.`>;
}[keyof T & string];

export type MessageKey = Leaves<typeof ptBR>;
export type Vars = Record<string, string | number>;

export type DeepPartialMessages<T> = { [K in keyof T]?: T[K] extends string ? string : DeepPartialMessages<T[K]> };

const catalogs: Record<Locale, DeepPartialMessages<typeof ptBR>> = { 'pt-BR': ptBR, en, es };

function lookup(catalog: unknown, key: string): string | undefined {
  let node: unknown = catalog;
  for (const part of key.split('.')) {
    if (node && typeof node === 'object' && part in (node as Record<string, unknown>)) node = (node as Record<string, unknown>)[part];
    else return undefined;
  }
  return typeof node === 'string' ? node : undefined;
}

function interpolate(text: string, vars?: Vars): string {
  if (!vars) return text;
  return text.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m));
}

/** Tradução com recuo para pt-BR (idioma de referência). A completude de en/es é verificada em teste. */
export function translate(locale: Locale, key: MessageKey, vars?: Vars): string {
  const text = lookup(catalogs[locale], key) ?? lookup(ptBR, key) ?? key;
  return interpolate(text, vars);
}

/** Lista as chaves folha de um catálogo (usado no teste de completude). */
export function listKeys(catalog: unknown, prefix = ''): string[] {
  if (!catalog || typeof catalog !== 'object') return [];
  return Object.entries(catalog as Record<string, unknown>).flatMap(([k, v]) =>
    typeof v === 'string' ? [`${prefix}${k}`] : listKeys(v, `${prefix}${k}.`),
  );
}

export const referenceCatalog = ptBR;
export const allCatalogs = catalogs;

export interface I18n {
  locale: Locale;
  t: (key: MessageKey, vars?: Vars) => string;
  num: (value: number | null | undefined, digits?: number) => string;
  sci: (value: number | null | undefined, digits?: number) => string;
  compact: (value: number, digits?: number) => string;
}

export function makeI18n(locale: Locale): I18n {
  return {
    locale,
    t: (key, vars) => translate(locale, key, vars),
    num: (value, digits = 2) => formatNumber(value, digits, locale),
    sci: (value, digits = 3) => formatScientific(value, digits, locale),
    compact: (value, digits = 2) => formatCompact(value, locale, digits),
  };
}

export function useI18n(): I18n {
  const locale = usePreferences((s) => s.locale);
  return useMemo(() => makeI18n(locale), [locale]);
}

/** Texto em três idiomas para conteúdo didático longo (enunciados, explicações). */
export interface Localized {
  'pt-BR': string;
  en: string;
  es: string;
}

export function pick(text: Localized | string, locale: Locale): string {
  return typeof text === 'string' ? text : text[locale] || text['pt-BR'];
}
