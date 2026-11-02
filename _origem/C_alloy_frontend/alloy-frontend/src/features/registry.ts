/**
 * Registro de capacidades imperativas expostas por componentes montados (ex.: o viewer
 * registra a captura PNG e os comandos de câmera). Evita acoplamento entre módulos.
 */
export interface ViewerHandle {
  capturePng: () => string | null;
  resetView: () => void;
  describe: () => string;
  orbit: (dAzimuth: number, dPolar: number) => void;
  zoom: (factor: number) => void;
}

let viewer: ViewerHandle | null = null;
const listeners = new Set<() => void>();

export function registerViewer(handle: ViewerHandle | null): void {
  viewer = handle;
  listeners.forEach((l) => l());
}

export function getViewer(): ViewerHandle | null {
  return viewer;
}

export function onViewerChange(l: () => void): () => void {
  listeners.add(l);
  return () => listeners.delete(l);
}
