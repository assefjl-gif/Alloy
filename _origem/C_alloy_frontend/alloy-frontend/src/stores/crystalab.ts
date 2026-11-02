import { create } from 'zustand';
import type { MetalTable, StructureRequest, StructureResult, StructureRow } from '../services/api/contracts.ts';
import type { HeaTransfer } from '../modules/hea/transfer.ts';

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error';

export interface CrystalabState {
  metals: MetalTable | null;
  structures: StructureRow[] | null;
  catalogStatus: LoadStatus;
  request: StructureRequest | null;
  structure: StructureResult | null;
  status: LoadStatus;
  error: string | null;
  densityVisible: boolean;
  editorText: string;
  /** Resultado HEA transportado para esta cena (imutável, Etapa 5). */
  heaTransfer: HeaTransfer | null;
  set: (patch: Partial<Omit<CrystalabState, 'set'>>) => void;
}

export const useCrystalab = create<CrystalabState>()((set) => ({
  metals: null,
  structures: null,
  catalogStatus: 'idle',
  request: null,
  structure: null,
  status: 'idle',
  error: null,
  densityVisible: false,
  editorText: '',
  heaTransfer: null,
  set: (patch) => set(patch),
}));

/** Texto do editor de parâmetros no mesmo formato do CrystaLab v1.0. */
export function structureToEditor(r: StructureResult): string {
  const lines = [
    `elemento = ${r.simbolo ?? '(genérico)'}`,
    `estrutura = ${r.estrutura}`,
    `${`raio = ${r.raio_nm ?? ''}`.padEnd(18)}# nm`,
    `${`peso = ${r.peso ?? ''}`.padEnd(18)}# g/mol`,
  ];
  if (r.estrutura === 'HC' && r.c_a !== null) lines.push(`c/a = ${Number(r.c_a.toFixed(4))}`);
  return lines.join('\n');
}
