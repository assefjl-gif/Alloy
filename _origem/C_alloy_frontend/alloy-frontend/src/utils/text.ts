/** Remove acentos e normaliza para comparação (mesma regra do motor: NFD sem marcas combinantes). */
export function plain(text: string): string {
  return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
}

export function capitalize(text: string): string {
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
}

/** Converte índices com barra combinante do motor ("1̄") para texto legível por leitores de tela ("menos 1"). */
export function spokenNotation(notation: string, minusWord: string): string {
  return notation.replace(/(\d)̄/g, `${minusWord} $1`);
}
