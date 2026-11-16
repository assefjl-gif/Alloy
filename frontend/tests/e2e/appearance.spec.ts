/**
 * Menu de APARÊNCIA da cena (T-22 / R2-FE-04). Roda contra o BUILD e o MOTOR reais.
 * O que se confere, com o que está DESENHADO na cena (não só no DOM):
 *  - cor por ELEMENTO, por GRUPO (ocupação/sítio do motor) e por ÁTOMO selecionado, com a
 *    precedência átomo > grupo > elemento, e a LEGENDA acompanhando a escolha;
 *  - cor das ARESTAS e dos VÉRTICES da célula;
 *  - TAMANHO (escala) e OPACIDADE dos átomos;
 *  - RESTAURAR O PADRÃO (por seção e geral);
 *  - MARCADOR GEOMÉTRICO desenhado em arame/seta, nunca como a esfera sólida de um átomo;
 *  - aparência NÃO altera nenhum valor científico (densidade e contagens ficam idênticas).
 */
import { test, expect, openCrystalab, viewerReady, reveal } from './fixtures.ts';
import type { Page } from 'playwright/test';

type AppearanceSummary = {
  cell: Array<{ color: string; opacity: number; count: number }>;
  alloy: Array<{ element: string; kind: string; color: string; opacity: number; count: number }>;
  edgeColor: string;
  vertexColor: string;
  vertices: number;
  atomScale: number;
  markerLooks: Record<string, string>;
};
type Viewer = {
  appearance: () => AppearanceSummary;
  alloyAtoms: () => string[];
  alloyScreenPosition: (id: string) => { x: number; y: number } | null;
  thermalScene: () => Record<string, number> | null;
};

const api = <T,>(page: Page, fn: (v: Viewer) => T) =>
  page.evaluate(`(${fn.toString()})(window.__alloy.viewer)`) as Promise<T>;
const look = (page: Page) => api(page, (v) => v.appearance());
const currentElement = (page: Page) =>
  page.evaluate(() => {
    const s = (window as unknown as { __alloy: { stores: { crystalab: { getState: () => { structure: { simbolo: string | null; estrutura: string } | null } } } } }).__alloy.stores.crystalab.getState().structure;
    return s?.simbolo ?? s?.estrutura ?? '';
  });

/** Move um controle de intervalo pelo TECLADO (interação real) até o valor pedido. */
async function slide(page: Page, selector: string, value: number): Promise<void> {
  const input = page.locator(selector);
  await input.focus();
  const [cur, step] = await input.evaluate((el) => [Number((el as HTMLInputElement).value), Number((el as HTMLInputElement).step)]);
  const key = cur < value ? 'ArrowRight' : 'ArrowLeft';
  const presses = Math.min(200, Math.round(Math.abs(value - cur) / Math.max(step, 1e-6)));
  for (let i = 0; i < presses; i += 1) await input.press(key);
}

async function formAlloy(page: Page, base: string, solute: string, percent: string) {
  await reveal(page, 'composition');
  await page.getByTestId('alloy-base').selectOption(base);
  await page.getByTestId('alloy-solute').selectOption(solute);
  await page.getByTestId('alloy-percent').fill(percent);
  await page.getByTestId('alloy-submit').click();
  await expect(page.getByTestId('alloy-results')).toBeVisible();
}

test('T-22 célula do metal puro: cor por elemento e por grupo, vértices, arestas, tamanho, opacidade e restauração', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  const density = await page.getByTestId('metric-density').innerText();
  const element = await currentElement(page);
  expect(element.length).toBeGreaterThan(0);

  await reveal(page, 'appearance.colors');
  // cor por ELEMENTO: todos os átomos desenhados passam a usá-la
  await page.getByTestId(`appearance-element-${element}`).fill('#ff00ff');
  await expect(page.getByTestId(`appearance-element-${element}-hex`)).toHaveText('#FF00FF');
  await expect.poll(async () => (await look(page)).cell.every((b) => b.color === '#ff00ff')).toBe(true);
  // a legenda da cena acompanha a cor escolhida e DIZ por palavra que ela é personalizada
  const chip = page.locator('[data-testid^="legend-site-"]').first();
  await expect(chip).toHaveAttribute('data-color', '#ff00ff');
  await expect(chip).toContainText('cor personalizada');
  await expect(page.getByTestId('legend-color-means')).toContainText('não altera dado');

  // cor por GRUPO (tipo de sítio que o motor devolve) vence a do elemento para aqueles átomos
  const group = page.locator('[data-testid^="appearance-group-"][type="color"]').first();
  await group.fill('#00ffff');
  await expect.poll(async () => {
    const cell = (await look(page)).cell;
    return cell.some((b) => b.color === '#00ffff') && cell.some((b) => b.color === '#ff00ff');
  }).toBe(true);

  // tamanho e opacidade (só desenho)
  await reveal(page, 'appearance.atoms');
  await slide(page, '#appearance-scale', 2);
  await expect.poll(async () => (await look(page)).atomScale).toBeGreaterThan(1.5);
  await slide(page, '#appearance-opacity', 0.5);
  await expect.poll(async () => (await look(page)).cell.every((b) => b.opacity < 1)).toBe(true);

  // arestas e marcadores de vértice
  await reveal(page, 'appearance.cell');
  await page.getByTestId('appearance-edge').fill('#008800');
  await expect.poll(async () => (await look(page)).edgeColor).toBe('#008800');
  await page.locator('#appearance-vertices').check();
  await page.getByTestId('appearance-vertex').fill('#aa0000');
  await expect.poll(async () => (await look(page)).vertices).toBeGreaterThan(0);
  await expect.poll(async () => (await look(page)).vertexColor).toBe('#aa0000');
  await expect(page.getByTestId('legend-vertices')).toBeVisible();
  await expect(page.getByTestId('legend-markers')).toContainText('Vértices da célula');

  // MARCADOR GEOMÉTRICO × ÁTOMO REAL: o átomo é esfera sólida; os marcadores, arame ou seta
  await expect.poll(async () => (await look(page)).markerLooks.vertices).toBe('wireframe');
  const looks = (await look(page)).markerLooks;
  expect(looks.atoms).toBe('solid-sphere');
  expect(looks.latticePoints).toBe('wireframe');
  expect(looks.axes).toBe('arrow');

  // nenhum valor científico mudou com a aparência
  expect(await page.getByTestId('metric-density').innerText()).toBe(density);

  // restauração: por seção e geral
  await page.getByTestId('appearance-reset-atoms').click();
  await expect.poll(async () => (await look(page)).atomScale).toBe(1);
  await page.getByTestId('appearance-reset-all').click();
  await expect.poll(async () => {
    const l = await look(page);
    return l.vertices === 0 && l.cell.every((b) => b.color !== '#ff00ff' && b.color !== '#00ffff') && l.edgeColor !== '#008800';
  }).toBe(true);
  await expect(page.getByTestId('appearance-reset-all')).toBeDisabled();
});

test('T-22 liga: cor por elemento, por grupo e por ÁTOMO selecionado, com legenda coerente e contagens intactas', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await formAlloy(page, 'Cu', 'Ni', '30');
  const counts = await api(page, (v) => (v.thermalScene ? v.thermalScene() : null));
  const results = await page.getByTestId('alloy-results').innerText();

  await reveal(page, 'appearance.colors');
  await page.getByTestId('appearance-element-Ni').fill('#ff00ff');
  await expect.poll(async () => (await look(page)).alloy.some((g) => g.element === 'Ni' && g.color === '#ff00ff')).toBe(true);
  await expect.poll(async () => (await look(page)).alloy.filter((g) => g.element === 'Cu').every((g) => g.color !== '#ff00ff')).toBe(true);
  await expect(page.getByTestId('legend-element-Ni')).toHaveAttribute('data-color', '#ff00ff');
  await expect(page.getByTestId('legend-element-Ni')).toContainText('cor personalizada');
  await expect(page.getByTestId('legend-element-Cu')).not.toContainText('cor personalizada');

  // cor por ÁTOMO: escolhe um átomo desenhado, pinta só ele
  const ids = await api(page, (v) => v.alloyAtoms());
  expect(ids.length).toBeGreaterThan(1);
  const pos = await api(page, (v) => v.alloyScreenPosition(v.alloyAtoms()[0] as string));
  expect(pos).not.toBeNull();
  await page.mouse.click((pos as { x: number; y: number }).x, (pos as { x: number; y: number }).y);
  await expect(page.getByTestId('appearance-atom')).toBeVisible();
  await page.getByTestId('appearance-atom').fill('#00ff00');
  await expect.poll(async () => {
    const groups = (await look(page)).alloy.filter((g) => g.color === '#00ff00');
    return groups.length === 1 && groups[0]?.count === 1;
  }).toBe(true);
  await expect(page.getByTestId('legend-color-means')).toContainText('átomo escolhido');

  // cor por GRUPO na liga: a ocupação que o motor devolve (solvente, substitucional…) ganha cor
  // própria e passa a valer para os átomos daquele grupo (acima do elemento, abaixo do átomo)
  const group = page.locator('[data-testid^="appearance-group-"][type="color"]').first();
  await group.fill('#0000ff');
  await expect.poll(async () => (await look(page)).alloy.some((g) => g.color === '#0000ff')).toBe(true);
  await expect(page.getByTestId('legend-color-means')).toContainText('grupo');

  // a cena desenhada continua com os mesmos átomos por elemento, e os resultados do motor não mudam
  expect(await api(page, (v) => (v.thermalScene ? v.thermalScene() : null))).toEqual(counts);
  expect(await page.getByTestId('alloy-results').innerText()).toBe(results);

  await page.getByTestId('appearance-reset-all').click();
  await expect.poll(async () => (await look(page)).alloy.every((g) => !['#ff00ff', '#00ff00', '#0000ff'].includes(g.color))).toBe(true);
  await expect(page.getByTestId('legend-element-Ni')).not.toContainText('cor personalizada');
});

/**
 * Selos de origem (decisão D-R2-2): o selo de DEMONSTRAÇÃO (número fictício) e o de ILUSTRAÇÃO
 * (representação sem pretensão preditiva sobre dado real) são distintos. As explicações de
 * animação são ilustrativas e precisam dizê-lo no selo, não só no texto.
 */
test('selos: as explicações de animação trazem o selo ILUSTRATIVO (data-seal="illustrative")', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await reveal(page, 'analysis.anim');
  const panel = page.getByTestId('animations-panel');
  await panel.getByRole('button', { name: 'ABAB', exact: true }).click();
  const seal = panel.locator('.anim-explainer [data-testid="demo-seal"]').first();
  await expect(seal).toBeVisible();
  await expect(seal).toHaveAttribute('data-seal', 'illustrative');

  // α→γ: a tabela é resultado real do motor; o passo intermediário é interpolação VISUAL e tem selo
  await panel.getByRole('button', { name: /α/ }).click();
  await panel.getByRole('button', { name: 'Próximo passo' }).click();
  const agSeal = panel.locator('.anim-explainer [data-testid="demo-seal"]').first();
  await expect(agSeal).toHaveAttribute('data-seal', 'illustrative');
});
