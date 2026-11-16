/**
 * Câmera do viewer para os controles da interface (botões sobre a cena e teclado).
 * O Viewer3D registra a implementação ao montar; sem viewer, as chamadas não fazem nada.
 * Módulo leve (sem Three.js), para poder ser importado fora do bloco carregado sob demanda.
 */
export interface CameraApi {
  /** gira em torno do alvo (radianos) */
  orbit: (dAzimuth: number, dPolar: number) => void;
  /** fator < 1 aproxima, > 1 afasta */
  zoom: (factor: number) => void;
  /** desloca a câmera e o alvo no plano da tela (frações da altura visível; +x direita, +y cima) */
  pan: (dx: number, dy: number) => void;
  /** centraliza: enquadra o conteúdo desenhado mantendo a orientação atual */
  frame: () => void;
}

let current: CameraApi | null = null;

export function setCameraApi(api: CameraApi | null): void {
  current = api;
}

export function getCameraApi(): CameraApi | null {
  return current;
}
