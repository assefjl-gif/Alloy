/**
 * Três estados de disponibilidade (7.12): local (funciona offline após o primeiro acesso),
 * apenas online (precisa de rede, não do motor), exige servidor (precisa do motor/serviço).
 */
export type Availability = 'local' | 'online' | 'server';

export const FEATURE_AVAILABILITY: Array<{ id: string; availability: Availability }> = [
  { id: 'shell', availability: 'local' },
  { id: 'viewer', availability: 'local' },
  { id: 'notebook', availability: 'local' },
  { id: 'quiz', availability: 'local' },
  { id: 'catalog', availability: 'local' },
  { id: 'share', availability: 'online' },
  { id: 'ai', availability: 'online' },
  { id: 'calc', availability: 'server' },
  { id: 'miller', availability: 'server' },
  { id: 'export', availability: 'server' },
  { id: 'hea', availability: 'server' },
  { id: 'classroom', availability: 'server' },
];
