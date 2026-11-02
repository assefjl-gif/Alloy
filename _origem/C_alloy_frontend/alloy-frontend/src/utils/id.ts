let counter = 0;
/** Identificador local único por sessão (não usa aleatoriedade). */
export function uid(prefix = 'id'): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter.toString(36)}`;
}
