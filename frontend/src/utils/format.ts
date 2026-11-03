/**
 * Formatação numérica por idioma. Só formata: casas decimais, separadores e notação
 * científica de exibição. Nenhum valor é recalculado aqui.
 */
export type Locale = 'pt-BR' | 'en' | 'es';

const cache = new Map<string, Intl.NumberFormat>();

function nf(locale: Locale, digits: number): Intl.NumberFormat {
  const key = `${locale}|${digits}`;
  let f = cache.get(key);
  if (!f) {
    f = new Intl.NumberFormat(locale, { minimumFractionDigits: digits, maximumFractionDigits: digits });
    cache.set(key, f);
  }
  return f;
}

export const NOT_AVAILABLE = '—';

export function formatNumber(value: number | null | undefined, digits: number, locale: Locale): string {
  if (value === null || value === undefined || Number.isNaN(value)) return NOT_AVAILABLE;
  if (!Number.isFinite(value)) return '∞';
  return nf(locale, digits).format(value);
}

/** Inteiro sem casas, ou até `digits` casas quando houver fração (ex.: contribuições 1/8 → 0,13). */
export function formatCompact(value: number, locale: Locale, digits = 2): string {
  if (Math.abs(value - Math.round(value)) < 1e-4) return nf(locale, 0).format(Math.round(value));
  return nf(locale, digits).format(value);
}

const SUPERSCRIPT: Record<string, string> = { '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻' };

/** Notação científica de exibição: 4,724 × 10⁻²³. */
export function formatScientific(value: number | null | undefined, digits: number, locale: Locale): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return NOT_AVAILABLE;
  if (value === 0) return '0';
  const exp = Math.floor(Math.log10(Math.abs(value)));
  const mantissa = value / 10 ** exp;
  const sup = String(exp).split('').map((c) => SUPERSCRIPT[c] ?? c).join('');
  return `${formatNumber(mantissa, digits, locale)} × 10${sup}`;
}

/** Converte texto digitado pelo usuário (aceita vírgula decimal) em número; NaN se inválido; null se vazio. */
export function parseUserNumber(text: string | null | undefined): number | null {
  if (text === null || text === undefined) return null;
  const clean = String(text).trim().replace(/\s/g, '').replace(',', '.');
  if (!clean) return null;
  const sci = clean.replace(/[x×]10\^?/i, 'e');
  const v = Number(sci);
  return Number.isFinite(v) ? v : Number.NaN;
}
