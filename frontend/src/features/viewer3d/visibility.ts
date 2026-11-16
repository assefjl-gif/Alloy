/**
 * VISIBILIDADE da cena (T-23): filtros por elemento, por ocupação/sítio, corte geométrico por eixo
 * e vizinhança de exibição. Puro (sem Three.js), testável em Node.
 *
 * Regras que este módulo respeita e por que ele existe:
 *  - filtrar e cortar é SÓ EXIBIÇÃO: nenhuma grandeza científica é calculada, nenhum valor exibido
 *    muda. As contagens científicas continuam vindo do motor (`composicao.n_atomos_unicos` etc.);
 *    o que daqui sai é contagem de EXIBIÇÃO, rotulada como tal na interface.
 *  - o corte é implementado como VISIBILIDADE de átomo, não como `clippingPlane` do Three.js.
 *    Motivo (requisito duro do cartão R2-FE-03): o átomo escondido não pode ser selecionável e o
 *    átomo revelado tem de ser. Removendo a instância da malha, o raycasting passa a respeitar o
 *    corte por construção — não por um filtro posterior sobre o ponto de impacto. De lambuja, não
 *    aparecem meias-esferas (meia esfera não é meio átomo) e o filtro fica testável sem WebGL.
 *  - nenhum limiar científico fixo: o eixo, a posição e a espessura são escolhidos pela pessoa, em
 *    unidades de a, dentro da faixa das próprias coordenadas devolvidas pelo motor.
 */
import type { Vec3 } from '../../services/api/contracts.ts';

export type AxisIndex = 0 | 1 | 2;
export type CutMode = 'below' | 'above' | 'slab';

/** Corte geométrico ao longo de um eixo. `position` e `thickness` em unidades de a. */
export interface CutState {
  axis: AxisIndex;
  mode: CutMode;
  position: number;
  thickness: number;
}

/** Vizinhança de EXIBIÇÃO em torno de um ponto (não é medida científica). */
export interface Neighbourhood {
  center: Vec3;
  /** raio em unidades de a */
  radius: number;
}

/**
 * Entrada pronta para decidir visibilidade. As três dimensões são INDEPENDENTES, porque o motor
 * as informa em campos diferentes: elemento (`elemento`), ocupação (`ocupacao`: solvente,
 * substitucional, intersticial) e sítio (`sitio.nome`: vértice, centro do cubo, octaédrico…).
 * Isolar em uma dimensão não mexe nas outras.
 */
export interface VisibilityFilter {
  hiddenElements: readonly string[];
  hiddenOccupations: readonly string[];
  hiddenSites: readonly string[];
  cut: CutState | null;
  neighbourhood: Neighbourhood | null;
}

export const EMPTY_FILTER: VisibilityFilter = { hiddenElements: [], hiddenOccupations: [], hiddenSites: [], cut: null, neighbourhood: null };

export function isFilterActive(f: VisibilityFilter): boolean {
  return f.hiddenElements.length > 0 || f.hiddenOccupations.length > 0 || f.hiddenSites.length > 0 || f.cut !== null || f.neighbourhood !== null;
}

/** Verdadeiro quando o ponto permanece visível segundo o corte (sem corte, tudo permanece). */
export function cutKeeps(pos: Vec3, cut: CutState | null): boolean {
  if (!cut) return true;
  const v = pos[cut.axis] as number;
  if (cut.mode === 'below') return v <= cut.position;
  if (cut.mode === 'above') return v >= cut.position;
  const half = Math.max(0, cut.thickness) / 2;
  return v >= cut.position - half && v <= cut.position + half;
}

function inNeighbourhood(pos: Vec3, n: Neighbourhood | null): boolean {
  if (!n) return true;
  const d = Math.hypot(pos[0] - n.center[0], pos[1] - n.center[1], pos[2] - n.center[2]);
  return d <= n.radius;
}

/** Item mínimo que o filtro sabe avaliar; os rótulos são os que o motor devolveu. */
export interface FilterableAtom {
  pos: Vec3;
  element: string;
  occupancy: string | null;
  site: string | null;
}

export function isVisible(atom: FilterableAtom, f: VisibilityFilter): boolean {
  if (f.hiddenElements.includes(atom.element)) return false;
  if (atom.occupancy !== null && f.hiddenOccupations.includes(atom.occupancy)) return false;
  if (atom.site !== null && f.hiddenSites.includes(atom.site)) return false;
  if (!cutKeeps(atom.pos, f.cut)) return false;
  return inNeighbourhood(atom.pos, f.neighbourhood);
}

/** Ocupação e sítio de um átomo de liga, como o motor os nomeia (`ocupacao` e `sitio.nome`). */
export function alloyClasses(a: { tipo?: string; ocupacao?: string; sitio?: { nome?: string } | null }): { occupancy: string | null; site: string | null } {
  return { occupancy: a.ocupacao ?? a.tipo ?? null, site: a.sitio?.nome ?? null };
}

/** Faixa das coordenadas desenhadas em um eixo (limites do controle de corte, vindos dos dados). */
export function axisRange(positions: readonly Vec3[], axis: AxisIndex): { min: number; max: number } {
  if (!positions.length) return { min: 0, max: 1 };
  let min = Infinity;
  let max = -Infinity;
  for (const p of positions) {
    const v = p[axis] as number;
    if (v < min) min = v;
    if (v > max) max = v;
  }
  return { min, max };
}

/**
 * Contagem de EXIBIÇÃO (nunca científica): esferas visíveis, átomos únicos visíveis e imagens
 * periódicas visíveis. `imagem: true` não entra na contagem de únicos, como no contrato R1.
 */
export interface DisplayCounts {
  drawn: number;
  unique: number;
  images: number;
  byElement: Record<string, number>;
}

export function displayCounts(atoms: ReadonlyArray<{ element: string; image: boolean; visible: boolean }>): DisplayCounts {
  const out: DisplayCounts = { drawn: 0, unique: 0, images: 0, byElement: {} };
  for (const a of atoms) {
    if (!a.visible) continue;
    out.drawn += 1;
    if (a.image) out.images += 1;
    else {
      out.unique += 1;
      out.byElement[a.element] = (out.byElement[a.element] ?? 0) + 1;
    }
  }
  return out;
}
