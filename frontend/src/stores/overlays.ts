import { create } from 'zustand';
import type { MillerDirection, MillerPlane, Vec3 } from '../services/api/contracts.ts';

/** Paleta Okabe–Ito (segura para daltonismo). A cor nunca é o único código: cada item tem rótulo e forma. */
export const OVERLAY_PALETTE = ['#D55E00', '#0072B2', '#009E73', '#CC79A7', '#E69F00', '#56B4E9', '#7A5195'] as const;

export interface AtomRef {
  /** índice do átomo em `structure.atomos` (célula unitária do motor) */
  index: number;
  /** deslocamento de célula na supercélula (réplica gráfica) */
  cell: [number, number, number];
}

export const atomKey = (a: AtomRef): string => `${a.index}@${a.cell.join(',')}`;

export interface Measurement {
  type: 'distance' | 'angle';
  atoms: AtomRef[];
  /** distância em unidades de a (geometria do viewer sobre posições do motor) */
  valueA?: number;
  /** distância em nm (valueA × a_nm do motor), quando a_nm existe */
  valueNm?: number | null;
  degrees?: number;
  points: Vec3[];
}

interface Base {
  id: string;
  visible: boolean;
  color: string;
  label: string;
}
export interface PlaneOverlay extends Base { kind: 'plane'; data: MillerPlane; clip: boolean }
export interface DirectionOverlay extends Base { kind: 'direction'; data: MillerDirection }
export interface MeasurementOverlay extends Base { kind: 'measurement'; data: Measurement }
export interface AnnotationOverlay extends Base { kind: 'annotation'; text: string; anchor: Vec3 }
export type OverlayItem = PlaneOverlay | DirectionOverlay | MeasurementOverlay | AnnotationOverlay;

export interface OverlaysState {
  items: OverlayItem[];
  selectedId: string | null;
  set: (patch: Partial<Omit<OverlaysState, 'set'>>) => void;
}

export const useOverlays = create<OverlaysState>()((set) => ({
  items: [],
  selectedId: null,
  set: (patch) => set(patch),
}));

export function nextColor(items: OverlayItem[]): string {
  const used = new Set(items.map((i) => i.color));
  return OVERLAY_PALETTE.find((c) => !used.has(c)) ?? OVERLAY_PALETTE[items.length % OVERLAY_PALETTE.length] ?? '#D55E00';
}
