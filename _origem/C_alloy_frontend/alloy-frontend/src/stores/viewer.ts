import { create } from 'zustand';
import type { Vec3 } from '../services/api/contracts.ts';
import type { AtomRef } from './overlays.ts';

export type AtomMode = 'reduced' | 'rigid' | 'ballstick' | 'points';
export type AnimationName = 'stacking' | 'alpha-gamma' | 'thermal';

export interface DisplaySettings {
  atoms: AtomMode;
  edges: boolean;
  axes: boolean;
  latticePoints: boolean;
  labels: boolean;
  autoRotate: boolean;
}

export interface CameraState {
  position: Vec3;
  target: Vec3;
}

export interface ViewerState {
  display: DisplaySettings;
  supercell: [number, number, number];
  camera: CameraState | null;
  /** incrementa quando a câmera é definida por código (URL, reset) para o viewer aplicar */
  cameraRevision: number;
  selection: AtomRef | null;
  tool: { kind: 'distance' | 'angle'; picks: AtomRef[] } | null;
  animation: { name: AnimationName; variant: string; step: number; playing: boolean } | null;
  /** toque: cena destravada aceita arrastar com um dedo */
  sceneUnlocked: boolean;
  /** coloração ilustrativa por elemento (Etapa 5, só em modo demonstrativo/ilustrativo) */
  elementColoring: { enabled: boolean; seed: number } | null;
  /** estado do motor gráfico (para mensagens e testes) */
  engine: 'idle' | 'loading' | 'ready' | 'unsupported' | 'error';
  set: (patch: Partial<Omit<ViewerState, 'set'>>) => void;
}

export const DEFAULT_DISPLAY: DisplaySettings = { atoms: 'reduced', edges: true, axes: true, latticePoints: false, labels: true, autoRotate: false };

export const useViewer = create<ViewerState>()((set) => ({
  display: { ...DEFAULT_DISPLAY },
  supercell: [1, 1, 1],
  camera: null,
  cameraRevision: 0,
  selection: null,
  tool: null,
  animation: null,
  sceneUnlocked: false,
  elementColoring: null,
  engine: 'idle',
  set: (patch) => set(patch),
}));
