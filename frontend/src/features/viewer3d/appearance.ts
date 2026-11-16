/**
 * APARÊNCIA da cena (T-22 / R2-FE-04). Puro (sem Three.js e sem React), testável em Node.
 *
 * Regras que este módulo respeita, e por que ele existe:
 *  - aparência é PREFERÊNCIA DE EXIBIÇÃO: cor, tamanho e transparência não alteram valor,
 *    contagem nem composição. Nenhuma grandeza científica passa por aqui;
 *  - a cor pode CODIFICAR informação (elemento, grupo, átomo escolhido). Quando codifica, a
 *    legenda diz o que ela significa — e sempre junto de rótulo em texto, porque cor nunca é o
 *    único meio de distinguir (acessibilidade);
 *  - a precedência é ÁTOMO > GRUPO > ELEMENTO > padrão da cena. A mais específica ganha, e a
 *    legenda informa qual nível está ativo;
 *  - "GRUPO" é a OCUPAÇÃO que o motor devolve por átomo (`ocupacao`: solvente, substitucional,
 *    intersticial…) e, quando o motor não a informa (célula do metal puro), o TIPO DE SÍTIO
 *    (`sitio`/`tipo`: vértice, centro, face…). Os dois são campos do próprio motor, já usados
 *    pelos filtros de exibição (T-23) e pela legenda da célula — ou seja, o agrupamento é
 *    sustentado pelos dados e usa o mesmo vocabulário que o resto da tela. O front não inventa
 *    nenhuma categoria nova nem deduz papel a partir de número.
 */

/** Sobreposições escolhidas pela pessoa. Chave ausente = cor padrão da cena. */
export interface AppearanceOverrides {
  /** elemento (símbolo como o motor o escreve) → cor */
  elements: Record<string, string>;
  /** grupo (ocupação do motor; ou tipo de sítio na célula do metal puro) → cor */
  groups: Record<string, string>;
  /** átomo individual (identidade estável `id` do motor) → cor */
  atoms: Record<string, string>;
}

export interface AppearanceSettings {
  overrides: AppearanceOverrides;
  /** cor dos marcadores de vértice da célula/supercélula (null = cor do tema) */
  vertexColor: string | null;
  /** cor das arestas da célula/supercélula (null = cor do tema) */
  edgeColor: string | null;
  /** desenhar os marcadores geométricos de vértice (desligado por padrão) */
  vertices: boolean;
  /** escala de exibição dos átomos (1 = padrão da representação escolhida) */
  atomScale: number;
  /** opacidade dos átomos (1 = opaco) */
  opacity: number;
}

export const DEFAULT_APPEARANCE: AppearanceSettings = {
  overrides: { elements: {}, groups: {}, atoms: {} },
  vertexColor: null,
  edgeColor: null,
  vertices: false,
  atomScale: 1,
  opacity: 1,
};

export const SCALE_RANGE = { min: 0.3, max: 2.5, step: 0.05 } as const;
export const OPACITY_RANGE = { min: 0.2, max: 1, step: 0.05 } as const;

/** Nível que decidiu a cor de um átomo (a legenda usa isto para explicar o que a cor codifica). */
export type ColorSource = 'atom' | 'group' | 'element' | 'default';

export interface AtomIdentity {
  id: string;
  element: string;
  /** ocupação do motor, quando houver */
  occupancy?: string | null;
  /** tipo de sítio do motor */
  site?: string | null;
}

/**
 * Grupo do átomo: ocupação do motor quando existe, senão o tipo de sítio. Sem nenhum dos dois,
 * o átomo não pertence a grupo algum (e a cor por grupo simplesmente não se aplica a ele).
 */
export function groupOf(a: Pick<AtomIdentity, 'occupancy' | 'site'>): string | null {
  return a.occupancy ?? a.site ?? null;
}

/** Cor efetiva do átomo e o nível que a decidiu. `base` é a cor padrão da cena para ele. */
export function resolveAtomColor(a: AtomIdentity, base: string, ov: AppearanceOverrides): { color: string; source: ColorSource } {
  const byAtom = ov.atoms[a.id];
  if (byAtom) return { color: byAtom, source: 'atom' };
  const group = groupOf(a);
  const byGroup = group === null ? undefined : ov.groups[group];
  if (byGroup) return { color: byGroup, source: 'group' };
  const byElement = ov.elements[a.element];
  if (byElement) return { color: byElement, source: 'element' };
  return { color: base, source: 'default' };
}

/** Cor efetiva de um ELEMENTO para a legenda (sem considerar grupo nem átomo). */
export function elementColor(element: string, base: string, ov: AppearanceOverrides): string {
  return ov.elements[element] ?? base;
}

export function clamp(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, value));
}

/** Aceita só `#rgb`/`#rrggbb` (o que o seletor de cor do navegador produz); senão devolve null. */
export function normalizeColor(value: string): string | null {
  const v = value.trim().toLowerCase();
  if (/^#[0-9a-f]{3}$/.test(v)) return `#${v[1]}${v[1]}${v[2]}${v[2]}${v[3]}${v[3]}`;
  return /^#[0-9a-f]{6}$/.test(v) ? v : null;
}

/** Alguma escolha de aparência está diferente do padrão? (a interface precisa dizer isso.) */
export function appearanceActive(s: AppearanceSettings): boolean {
  return colorsActive(s) || cellActive(s) || atomsActive(s);
}

export function colorsActive(s: AppearanceSettings): boolean {
  const o = s.overrides;
  return Object.keys(o.elements).length > 0 || Object.keys(o.groups).length > 0 || Object.keys(o.atoms).length > 0;
}

export function cellActive(s: AppearanceSettings): boolean {
  return s.vertexColor !== null || s.edgeColor !== null || s.vertices !== DEFAULT_APPEARANCE.vertices;
}

export function atomsActive(s: AppearanceSettings): boolean {
  return s.atomScale !== DEFAULT_APPEARANCE.atomScale || s.opacity !== DEFAULT_APPEARANCE.opacity;
}

/**
 * MARCADORES GEOMÉTRICOS da cena. Eles não são átomos e não podem ser confundidos com átomos:
 * cada um é desenhado com GEOMETRIA e ACABAMENTO próprios (arame/linha/seta, sem iluminação de
 * esfera sólida), nunca com a cor de elemento, e aparece na legenda com glifo e a frase
 * "não é átomo". A distinção, portanto, não depende de cor.
 */
export const GEOMETRIC_MARKERS = ['axes', 'latticePoints', 'vertices', 'selection', 'overlay'] as const;
export type GeometricMarker = (typeof GEOMETRIC_MARKERS)[number];

/** Um átomo real é sempre esfera sólida iluminada; marcador geométrico, nunca. */
export const ATOM_LOOK = 'solid-sphere' as const;
export const MARKER_LOOK: Record<GeometricMarker, 'arrow' | 'wireframe-octahedron' | 'wireframe-box' | 'wireframe-sphere' | 'dashed-outline'> = {
  axes: 'arrow',
  latticePoints: 'wireframe-octahedron',
  vertices: 'wireframe-box',
  selection: 'wireframe-sphere',
  overlay: 'dashed-outline',
};
