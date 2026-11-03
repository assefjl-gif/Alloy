/**
 * Geometria de VISUALIZAÇÃO (sem Three.js, testável em Node).
 * Regra: posições, arestas, raios relativos e índices de Miller vêm do motor. Aqui só:
 *  - transladamos a célula do motor para desenhar supercélulas (réplicas gráficas, 3.9/3.10);
 *  - removemos pontos coincidentes entre células vizinhas (mesmo ponto desenhado uma vez);
 *  - ligamos esferas em contato para o modo bola-e-bastão;
 *  - medimos distância/ângulo entre posições do motor (ferramenta de medição, 3.13).
 * Nenhuma grandeza científica exibida como resultado (n, FEA, ρ…) sai deste arquivo.
 *
 * Convenção de translação (pendência D-10: o motor não envia vetores de rede):
 *  - cúbicas: t1=(1,0,0), t2=(0,1,0), t3=(0,0,1) em unidades de a (a célula do motor é [0,1]³);
 *  - HC: o motor desenha o prisma hexagonal (3 células primitivas) de circunraio a, centrado na origem;
 *    prismas vizinhos estão em t1=(3/2, √3/2, 0), t2=(0, √3, 0), t3=(0, 0, c/a).
 */
import type { SiteType, StructureCode, StructureResult, Vec3 } from '../../services/api/contracts.ts';
import type { AtomRef } from '../../stores/overlays.ts';

export interface DisplayAtom {
  key: string;
  ref: AtomRef;
  pos: Vec3;
  tipo: SiteType;
  /** cópia transladada da célula do motor (não entra em nenhuma contagem) */
  replica: boolean;
  /** fração do sítio na célula do motor (1/8, 1/2, 1…), apenas para exibição */
  fracaoTxt: string;
}

const SQRT3 = Math.sqrt(3);

export function translations(estrutura: StructureCode, cA: number | null): [Vec3, Vec3, Vec3] {
  if (estrutura === 'HC') return [[1.5, SQRT3 / 2, 0], [0, SQRT3, 0], [0, 0, cA ?? Math.sqrt(8 / 3)]];
  return [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
}

const keyOf = (p: Vec3): string => p.map((v) => (Math.round(v * 1e4) / 1e4).toFixed(4)).join('|');

const add = (a: Vec3, b: Vec3, s = 1): Vec3 => [a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s];

export function cellOffset(t: [Vec3, Vec3, Vec3], cell: [number, number, number]): Vec3 {
  let o: Vec3 = [0, 0, 0];
  o = add(o, t[0], cell[0]);
  o = add(o, t[1], cell[1]);
  o = add(o, t[2], cell[2]);
  return o;
}

export function buildAtoms(r: Pick<StructureResult, 'atomos' | 'estrutura' | 'c_a'>, n: [number, number, number]): DisplayAtom[] {
  const t = translations(r.estrutura, r.c_a);
  const seen = new Set<string>();
  const out: DisplayAtom[] = [];
  for (let k = 0; k < n[2]; k += 1) {
    for (let j = 0; j < n[1]; j += 1) {
      for (let i = 0; i < n[0]; i += 1) {
        const cell: [number, number, number] = [i, j, k];
        const off = cellOffset(t, cell);
        r.atomos.forEach((a, index) => {
          const pos = add(a.pos as Vec3, off);
          const key = keyOf(pos);
          if (seen.has(key)) return;
          seen.add(key);
          out.push({ key: `${index}@${cell.join(',')}`, ref: { index, cell }, pos, tipo: a.tipo, replica: i + j + k > 0, fracaoTxt: a.fracao_txt });
        });
      }
    }
  }
  return out;
}

export function buildEdges(r: Pick<StructureResult, 'arestas' | 'estrutura' | 'c_a'>, n: [number, number, number]): Array<[Vec3, Vec3]> {
  const t = translations(r.estrutura, r.c_a);
  const seen = new Set<string>();
  const out: Array<[Vec3, Vec3]> = [];
  for (let k = 0; k < n[2]; k += 1) for (let j = 0; j < n[1]; j += 1) for (let i = 0; i < n[0]; i += 1) {
    const off = cellOffset(t, [i, j, k]);
    for (const [a, b] of r.arestas) {
      const p = add(a as Vec3, off);
      const q = add(b as Vec3, off);
      const ka = keyOf(p);
      const kb = keyOf(q);
      const key = ka < kb ? `${ka}#${kb}` : `${kb}#${ka}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push([p, q]);
    }
  }
  return out;
}

export function distance(a: Vec3, b: Vec3): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
}

/** Ângulo em graus no vértice `v` formado por a–v–b. */
export function angleDeg(a: Vec3, v: Vec3, b: Vec3): number {
  const u: Vec3 = [a[0] - v[0], a[1] - v[1], a[2] - v[2]];
  const w: Vec3 = [b[0] - v[0], b[1] - v[1], b[2] - v[2]];
  const nu = Math.hypot(...u);
  const nw = Math.hypot(...w);
  if (nu < 1e-9 || nw < 1e-9) return Number.NaN;
  const cos = Math.min(1, Math.max(-1, (u[0] * w[0] + u[1] * w[1] + u[2] * w[2]) / (nu * nw)));
  return (Math.acos(cos) * 180) / Math.PI;
}

/**
 * Pares de esferas em contato (bola-e-bastão): distância = 2R (R/a vem do motor como
 * `raio_relativo`) com tolerância relativa. Na HC com c/a ≠ ideal, só os contatos dentro
 * da tolerância aparecem — o que é fiel ao modelo de esferas rígidas.
 */
export function contactBonds(atoms: DisplayAtom[], raioRelativo: number, tolerance = 0.02): Array<[number, number]> {
  const target = 2 * raioRelativo;
  const out: Array<[number, number]> = [];
  for (let i = 0; i < atoms.length; i += 1) {
    for (let j = i + 1; j < atoms.length; j += 1) {
      const d = distance((atoms[i] as DisplayAtom).pos, (atoms[j] as DisplayAtom).pos);
      if (Math.abs(d - target) <= target * tolerance) out.push([i, j]);
    }
  }
  return out;
}

export function bounds(points: Vec3[]): { center: Vec3; radius: number; min: Vec3; max: Vec3 } {
  const min: Vec3 = [Infinity, Infinity, Infinity];
  const max: Vec3 = [-Infinity, -Infinity, -Infinity];
  for (const p of points) for (let i = 0; i < 3; i += 1) { min[i] = Math.min(min[i] as number, p[i] as number); max[i] = Math.max(max[i] as number, p[i] as number); }
  if (!points.length) return { center: [0, 0, 0], radius: 1, min: [0, 0, 0], max: [0, 0, 0] };
  const center: Vec3 = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2];
  return { center, radius: Math.max(0.5, distance(min, max) / 2), min, max };
}

/** Pontos de rede: nas cúbicas (base de 1 átomo) coincidem com os átomos; na HC, vértices e centros basais (base de 2 átomos). */
export function isLatticePoint(estrutura: StructureCode, tipo: SiteType): boolean {
  return estrutura !== 'HC' || tipo === 'vertice' || tipo === 'basal';
}

/** Validação da ferramenta de medição: devolve o motivo quando a medição não é válida (3.13). */
export function measurementProblem(kind: 'distance' | 'angle', refs: AtomRef[]): 'duplicate' | 'vertexRepeat' | null {
  const keys = refs.map((r) => `${r.index}@${r.cell.join(',')}`);
  if (kind === 'distance' && keys.length === 2 && keys[0] === keys[1]) return 'duplicate';
  if (kind === 'angle' && keys.length === 3 && (keys[0] === keys[1] || keys[1] === keys[2] || keys[0] === keys[2])) return 'vertexRepeat';
  return null;
}

/** Atribuição ILUSTRATIVA de elementos aos sítios (Etapa 5.5) — só em modo demonstrativo, com semente. */
export function illustrativeElements(atoms: DisplayAtom[], composition: Record<string, number>, rng: { weighted<T>(items: readonly T[], w: readonly number[]): T }): string[] {
  const els = Object.keys(composition);
  const w = els.map((e) => composition[e] ?? 0);
  return atoms.map(() => rng.weighted(els, w));
}

/** Camadas compactas esquemáticas para a animação de empilhamento (ilustração, sem medidas — D-13). */
export function stackingLayers(sequence: string[], size = 3): Array<{ letter: string; points: Vec3[] }> {
  const shift: Record<string, [number, number]> = { A: [0, 0], B: [0.5, SQRT3 / 6], C: [1, SQRT3 / 3] };
  const dz = Math.sqrt(2 / 3);
  return sequence.map((letter, layer) => {
    const [sx, sy] = shift[letter] ?? [0, 0];
    const points: Vec3[] = [];
    for (let j = -size; j <= size; j += 1) for (let i = -size; i <= size; i += 1) {
      const x = i + j / 2 + sx;
      const y = (j * SQRT3) / 2 + sy;
      if (Math.hypot(x - 0.5, y - SQRT3 / 6) <= size - 0.3) points.push([x, y, layer * dz]);
    }
    return { letter, points };
  });
}
