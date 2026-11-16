/**
 * Cena de ligas e vibração térmica (T-13). Sem Three.js, testável em Node.
 * Regra de integridade: posições, raios, elementos e amplitude vêm da API (motor). Aqui só
 * se montam os dados de desenho e o movimento ILUSTRATIVO em torno das posições de rede.
 * O movimento NÃO é uma simulação de dinâmica molecular: cada átomo oscila de forma independente
 * (modelo de Einstein simplificado), com a amplitude do critério de Lindemann devolvida pelo motor
 * multiplicada pelo "exagero visual" escolhido pelo usuário (e rotulado como tal na interface).
 */
import type { AlloyAtom, AlloyResult, StructureResult, Vec3 } from '../../services/api/contracts.ts';
import type { DisplayAtom } from './geometry.ts';
import { alloyClasses, EMPTY_FILTER, isVisible, type VisibilityFilter } from './visibility.ts';
import { DEFAULT_APPEARANCE, elementColor, resolveAtomColor, type AppearanceOverrides, type AppearanceSettings, type ColorSource } from './appearance.ts';

export interface SceneAtom {
  pos: Vec3;
  element: string;
  /** raio relativo a `a` (o motor entrega; o viewer só escala para exibição) */
  radius: number;
  kind: 'rede' | 'intersticial';
  /**
   * Identidade ESTÁVEL do átomo, como o motor a devolve (`id`). É a chave da seleção na cena de
   * liga (T-24): o front não a inventa. Sem `id` na resposta (motor anterior), cai no índice da
   * lista desenhada, que é estável para a mesma resposta.
   */
  id: string;
  /** `imagem: true` do motor: réplica periódica de fronteira; nunca entra em contagem nem legenda */
  image: boolean;
  /** ocupação e sítio como o motor os nomeia, usados pelos filtros de exibição (T-23) */
  occupancy: string | null;
  site: string | null;
  /** falso = escondido por filtro ou corte de EXIBIÇÃO (não é desenhado nem selecionável) */
  visible: boolean;
  /**
   * Cor de EXIBIÇÃO já resolvida (T-22): átomo > grupo > elemento > padrão da cena. É só
   * aparência — não altera valor, contagem nem composição.
   */
  color: string;
  /** nível que decidiu a cor (a legenda informa o que a cor está codificando) */
  colorSource: ColorSource;
}

export interface ThermalScene {
  atoms: SceneAtom[];
  /** segmentos [início, fim] da caixa da supercélula */
  edges: Vec3[][];
  colors: Record<string, string>;
  /** amplitude de vibração u/a do motor (0 = sem temperatura calculada) */
  amplitude: number;
  title: string;
}

/**
 * Paleta acessível (a mesma do restante do app): 1º elemento azul, 2º laranja, 3º verde…
 * Sete cores porque a API aceita solvente + até 6 solutos (contrato R1 §2.1).
 */
export const ALLOY_PALETTE = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9', '#666666'] as const;
/** Fator de exibição: o raio "rígido" (contato) fica grande demais para ver o arranjo. */
export const ALLOY_RADIUS_SCALE = 0.42;

export interface LegendEntry {
  element: string;
  color: string;
  role: 'base' | 'soluto' | 'intersticial';
  /** átomos ÚNICOS deste elemento (imagens periódicas não contam); null = o motor não informou */
  atoms: number | null;
}

/** Papel devolvido pela API (`papel`) → rótulo de legenda já existente na interface. */
const ROLE_BY_PAPEL: Record<string, LegendEntry['role']> = {
  solvente: 'base',
  substitucional: 'soluto',
  intersticial: 'intersticial',
};

/**
 * Legenda da cena com UM item por elemento representado, na ordem canônica do motor
 * (solvente, substitucionais, intersticiais) — a API aceita até 6 solutos (contrato R1 §2.1).
 * Recuo para a forma binária legada quando a resposta não traz `composicao` (backend anterior).
 * Imagens periódicas (`imagem: true`) nunca entram na contagem: ela vem de `n_atomos`.
 */
export function alloyLegend(r: Pick<AlloyResult, 'base' | 'soluto' | 'intersticial' | 'composicao'>): LegendEntry[] {
  const components = r.composicao?.representada ?? [];
  if (components.length) {
    return components.map((c, i) => ({
      element: c.elemento,
      color: ALLOY_PALETTE[i % ALLOY_PALETTE.length] as string,
      role: ROLE_BY_PAPEL[c.papel] ?? 'soluto',
      atoms: c.n_atomos ?? null,
    }));
  }
  return [
    { element: r.base, color: ALLOY_PALETTE[0], role: 'base', atoms: null },
    { element: r.soluto, color: ALLOY_PALETTE[1], role: r.intersticial ? 'intersticial' : 'soluto', atoms: null },
  ];
}

/** Identidade do átomo da liga: `id` do motor quando existe; senão a posição na lista desenhada. */
export function alloyAtomId(a: AlloyAtom, index: number): string {
  return a.id ?? `#${index}`;
}

export function sceneFromAlloy(r: AlloyResult, amplitude = 0, filter: VisibilityFilter = EMPTY_FILTER, appearance: AppearanceSettings = DEFAULT_APPEARANCE): ThermalScene {
  const legend = alloyLegend(r);
  const palette = Object.fromEntries(legend.map((l) => [l.element, l.color]));
  const ov = appearance.overrides;
  return {
    atoms: r.atomos.map((a, index) => {
      const cls = alloyClasses(a);
      const id = alloyAtomId(a, index);
      const base = palette[a.elemento] ?? (ALLOY_PALETTE[0] as string);
      const { color, source } = resolveAtomColor({ id, element: a.elemento, ...cls }, base, ov);
      return {
        pos: a.pos,
        element: a.elemento,
        radius: a.raio_rel,
        kind: a.tipo,
        id,
        image: a.imagem === true,
        ...cls,
        visible: isVisible({ pos: a.pos, element: a.elemento, ...cls }, filter),
        color,
        colorSource: source,
      };
    }),
    edges: r.arestas,
    colors: Object.fromEntries(legend.map((l) => [l.element, elementColor(l.element, l.color, ov)])),
    amplitude,
    title: r.rotulo,
  };
}

/**
 * Legenda da cena com a cor EFETIVA de cada elemento (T-22) e a marca de quem a escolheu.
 * A legenda é montada da mesma resolução que desenha a cena, por isso nunca divergem.
 */
export interface AppearanceLegendEntry extends LegendEntry {
  /** cor padrão da paleta, para o botão "restaurar" e para explicar a mudança */
  defaultColor: string;
  /** true quando a pessoa escolheu a cor deste elemento */
  custom: boolean;
}

export function alloyLegendWith(r: Pick<AlloyResult, 'base' | 'soluto' | 'intersticial' | 'composicao'>, ov: AppearanceOverrides): AppearanceLegendEntry[] {
  return alloyLegend(r).map((l) => ({ ...l, color: elementColor(l.element, l.color, ov), defaultColor: l.color, custom: ov.elements[l.element] !== undefined }));
}

/** Material puro: os átomos exibidos hoje (supercélula atual), sem réplicas gráficas duplicadas na contagem. */
export function sceneFromStructure(structure: StructureResult, atoms: DisplayAtom[], edges: Vec3[][], amplitude: number, filter: VisibilityFilter = EMPTY_FILTER, appearance: AppearanceSettings = DEFAULT_APPEARANCE): ThermalScene {
  const element = structure.simbolo ?? structure.estrutura;
  const ov = appearance.overrides;
  const base = ALLOY_PALETTE[0] as string;
  return {
    atoms: atoms.map((a) => {
      const { color, source } = resolveAtomColor({ id: a.key, element, occupancy: null, site: a.tipo }, base, ov);
      return {
        pos: a.pos,
        element,
        radius: structure.raio_relativo,
        kind: 'rede' as const,
        id: a.key,
        image: a.replica,
        occupancy: null,
        site: a.tipo,
        visible: isVisible({ pos: a.pos, element, occupancy: null, site: a.tipo }, filter),
        color,
        colorSource: source,
      };
    }),
    edges,
    colors: { [element]: elementColor(element, base, ov) },
    amplitude,
    title: structure.rotulo,
  };
}

/** Hash inteiro determinístico → [0,1). Mesma cena, mesmos movimentos (testes e relato reproduzíveis). */
export function unit(index: number, salt: number): number {
  let h = (Math.imul(index + 1, 0x9e3779b1) ^ Math.imul(salt + 1, 0x85ebca6b)) >>> 0;
  h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d) >>> 0;
  h = Math.imul(h ^ (h >>> 12), 0x297a2d39) >>> 0;
  return ((h ^ (h >>> 15)) >>> 0) / 4294967296;
}

/** Deslocamento do átomo `index` no instante `tMs` (ms). |componente| ≤ amplitude. */
export function displacement(index: number, tMs: number, amplitude: number): Vec3 {
  if (amplitude <= 0) return [0, 0, 0];
  const out: Vec3 = [0, 0, 0];
  for (let k = 0; k < 3; k += 1) {
    const freq = 0.9 + unit(index, 10 + k) * 0.8; // 0,9–1,7 Hz: lento o bastante para enxergar
    const phase = unit(index, 20 + k) * Math.PI * 2;
    out[k] = amplitude * Math.sin(2 * Math.PI * freq * (tMs / 1000) + phase);
  }
  return out;
}

/** Amplitude exibida = amplitude real do motor × exagero visual (1× = real). */
export function displayAmplitude(real: number, exaggeration: number): number {
  return real * Math.max(1, exaggeration);
}
