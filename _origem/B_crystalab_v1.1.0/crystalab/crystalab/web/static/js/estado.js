// Estado único da interface e constantes visuais.
export const TYPE_COLORS = { vertice: "#1aa7d9", centro: "#d79319", face: "#19a56b", basal: "#19a56b", interior: "#7256d9" };
export const TYPE_LABELS = { vertice: "vértice", centro: "centro do cubo", face: "centro de face", basal: "centro basal", interior: "interior" };
export const OVERLAY_COLORS = ["#ce3f4f", "#f2a73b", "#7256d9", "#19a56b", "#ff6fa5", "#3f6ecf"];

// Chaves de armazenamento local com prefixo do módulo (sem choque com outros módulos do Alloy).
export const STORAGE_KEYS = Object.freeze({ theme: "crystalab-theme" });

export const state = {
  data: null,          // bootstrap: { metais, estruturas, inicial, versao_dados }
  current: null,       // último resultado de célula
  selectedKey: "",
  mode: "plano",
  overlays: [],
  rigid: false,
  autoRotate: false,
  showAxes: true,
  densityVisible: false,
  theme: "light",
};
