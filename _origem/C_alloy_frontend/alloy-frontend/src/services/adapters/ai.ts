/**
 * Adaptador de IA generativa (6.12). Não há serviço conectado (pendência D-08): o recurso fica
 * desativado e identificado na interface. Quando houver, todo conteúdo gerado deve vir com
 * `origin` e ser exibido como APOIO (categoria feedback), nunca como resultado calculado.
 */
export interface AiSuggestion {
  text: string;
  origin: { service: string; model: string; generatedAt: string };
}

export interface AiAdapter {
  available: boolean;
  reason: 'not-configured' | 'offline' | null;
  suggestHint: (context: { activityId: string; step: string; locale: string }) => Promise<AiSuggestion>;
}

export const aiAdapter: AiAdapter = {
  available: false,
  reason: 'not-configured',
  suggestHint: async () => {
    throw new Error('Serviço de IA não configurado (D-08).');
  },
};
