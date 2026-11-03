/** Legenda elemento → cor + forma (5.4). Mesma regra usada pelo viewer, sem depender do Three.js. */
export const ELEMENT_COLORS = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9', '#7A5195', '#4D4D4D'] as const;
export const SHAPES = ['sphere', 'cube', 'octahedron', 'tetrahedron', 'icosahedron', 'dodecahedron', 'cylinder'] as const;
export type Shape = (typeof SHAPES)[number];

export function elementLegendFor(composition: Record<string, number>): Array<{ element: string; color: string; shape: Shape }> {
  return Object.keys(composition).sort().map((element, i) => ({
    element,
    color: ELEMENT_COLORS[i % ELEMENT_COLORS.length] as string,
    shape: SHAPES[i % SHAPES.length] as Shape,
  }));
}
