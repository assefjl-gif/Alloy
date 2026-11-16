/**
 * R1-FE-01 — layout do CrystaLab: palco 3D em área total, barra lateral única com seis seções
 * expansíveis, câmera (girar, aproximar, deslocar, centralizar, restaurar) e legenda coerente.
 * Os valores exibidos são comparados com o que o motor devolveu (nada é recalculado no front).
 */
import type { Page } from 'playwright/test';
import { test, expect, openCrystalab, viewerReady, reveal } from './fixtures.ts';

const SECTIONS = ['structure', 'composition', 'selection', 'properties', 'appearance', 'analysis'] as const;

interface Cam { position: [number, number, number]; target: [number, number, number] }
interface ViewerHooks { camera: () => Cam; size: () => { width: number; height: number }; atoms: () => unknown[] }

const camera = (page: Page): Promise<Cam> => page.evaluate(() => (window as unknown as { __alloy: { viewer: ViewerHooks } }).__alloy.viewer.camera());
const norm = (v: number[]): number => Math.hypot(...v);
const sub = (a: number[], b: number[]): number[] => a.map((x, i) => x - (b[i] ?? 0));
const direction = (c: Cam): number[] => { const d = sub(c.position, c.target); const n = norm(d); return d.map((x) => x / n); };
const dot = (a: number[], b: number[]): number => a.reduce((s, x, i) => s + x * (b[i] ?? 0), 0);

/** O palco vai do fim do cabeçalho até a base da janela, e de `left` até a borda direita; o desenho acompanha. */
async function expectStageFills(page: Page, left: number): Promise<void> {
  const view = page.viewportSize();
  if (!view) throw new Error('sem viewport');
  await expect.poll(async () => {
    const header = await page.locator('.ds-app__header').boundingBox();
    const stage = await page.getByTestId('viewer-stage').boundingBox();
    if (!header || !stage) return 'sem caixa';
    const size = await page.evaluate(() => (window as unknown as { __alloy: { viewer: ViewerHooks } }).__alloy.viewer.size());
    const ok = Math.abs(stage.y - (header.y + header.height)) <= 1
      && Math.abs(stage.x - left) <= 1
      && Math.abs(stage.x + stage.width - view.width) <= 1
      && Math.abs(stage.y + stage.height - view.height) <= 1
      && Math.abs(size.width - stage.width) <= 1
      && Math.abs(size.height - stage.height) <= 1;
    return ok ? 'ok' : JSON.stringify({ header, stage, size, left, view });
  }).toBe('ok');
  // nada rola por trás da cena
  expect(await page.evaluate(() => document.documentElement.scrollHeight <= window.innerHeight)).toBe(true);
}

test('L1 — o palco ocupa toda a área útil com a barra aberta e recolhida, e a cena redimensiona', async ({ app: page }) => {
  await page.setViewportSize({ width: 1366, height: 800 });
  await openCrystalab(page);
  await viewerReady(page);
  const toggle = page.getByTestId('sidebar-toggle');
  const bar = page.locator('#crystal-sidebar');
  await expect(toggle).toHaveAttribute('aria-controls', 'crystal-sidebar');
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  await expect(bar).toBeVisible();
  const barBox = await bar.boundingBox();
  expect(barBox?.x).toBe(0);
  await expectStageFills(page, (barBox?.x ?? 0) + (barBox?.width ?? 0));

  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await expect(bar).toBeHidden();
  await expectStageFills(page, 0);

  // janela redimensionada: o palco e o desenho acompanham
  await page.setViewportSize({ width: 1100, height: 700 });
  await expectStageFills(page, 0);

  // o estado da barra é lembrado
  await page.reload();
  await viewerReady(page);
  await expect(page.getByTestId('sidebar-toggle')).toHaveAttribute('aria-expanded', 'false');
  await expectStageFills(page, 0);

  // barra larga: o palco fica com todo o restante
  await page.getByTestId('sidebar-toggle').click();
  await page.getByTestId('sidebar-wide').click();
  const wide = await bar.boundingBox();
  expect(wide?.width ?? 0).toBeGreaterThan(500);
  await expectStageFills(page, wide?.width ?? 0);
});

test('L2 — seis seções expansíveis, operáveis por teclado; avançadas recolhidas por padrão', async ({ app: page }) => {
  await openCrystalab(page);
  await expect(page.locator('#crystal-sidebar').getByRole('heading', { level: 2 })).toHaveCount(SECTIONS.length);
  const initial: Record<string, string | null> = {};
  for (const id of SECTIONS) {
    const btn = page.getByTestId(`section-${id}`);
    await expect(btn).toBeVisible();
    await expect(btn).toHaveAttribute('aria-controls', `cl-sec-${id}`);
    initial[id] = await btn.getAttribute('aria-expanded');
  }
  expect(initial).toEqual({ structure: 'true', composition: 'false', selection: 'false', properties: 'true', appearance: 'false', analysis: 'false' });

  for (const id of SECTIONS) {
    const btn = page.getByTestId(`section-${id}`);
    const region = page.locator(`#cl-sec-${id}`);
    const wasOpen = initial[id] === 'true';
    await btn.focus();
    await page.keyboard.press('Enter');
    await expect(btn).toHaveAttribute('aria-expanded', String(!wasOpen));
    if (wasOpen) await expect(region).toBeHidden(); else await expect(region).toBeVisible();
    await expect(btn).toBeFocused();
    await page.keyboard.press('Space');
    await expect(btn).toHaveAttribute('aria-expanded', String(wasOpen));
    if (wasOpen) await expect(region).toBeVisible(); else await expect(region).toBeHidden();
  }

  // dentro de Análise, só Miller começa aberto; terminal, medições, temperatura e animações ficam recolhidos
  await reveal(page, 'analysis');
  await expect(page.getByTestId('sub-analysis-miller')).toHaveAttribute('aria-expanded', 'true');
  for (const sub of ['overlays', 'measure', 'thermal', 'anim', 'terminal', 'workspaces']) await expect(page.getByTestId(`sub-analysis-${sub}`)).toHaveAttribute('aria-expanded', 'false');
});

test('L3 — câmera: deslocar, centralizar (mantém a orientação) e restaurar a vista padrão', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  const stage = page.getByTestId('viewer-stage');
  const initial = await camera(page);
  expect(norm(initial.target)).toBeLessThan(1e-6);
  const distance = norm(sub(initial.position, initial.target));

  // teclado: seta gira, Ctrl+seta desloca
  await stage.focus();
  await page.keyboard.press('ArrowLeft');
  await page.keyboard.press('ArrowUp');
  for (let i = 0; i < 4; i += 1) await page.keyboard.press('Control+ArrowLeft');
  const moved = await camera(page);
  expect(dot(direction(moved), direction(initial))).toBeLessThan(0.999); // girou
  expect(norm(moved.target)).toBeGreaterThan(0.1 * distance); // deslocou
  expect(norm(sub(moved.position, moved.target))).toBeCloseTo(distance, 5); // sem aproximar

  // botões: aproximar e deslocar
  await page.getByTestId('camera-zoom-in').click();
  expect(norm(sub((await camera(page)).position, (await camera(page)).target))).toBeLessThan(distance);
  await page.getByTestId('camera-controls').getByRole('radio', { name: 'Deslocar' }).check();
  await expect(page.getByTestId('camera-right')).toHaveAccessibleName('Deslocar a cena para a direita');
  const beforePan = await camera(page);
  await page.getByTestId('camera-right').click();
  const afterPan = await camera(page);
  expect(norm(sub(afterPan.target, beforePan.target))).toBeGreaterThan(0.01 * distance);

  // centralizar: o alvo volta ao conteúdo, a orientação fica
  await page.getByTestId('camera-center').click();
  const centered = await camera(page);
  expect(norm(centered.target)).toBeLessThan(0.02 * distance);
  expect(dot(direction(centered), direction(afterPan))).toBeGreaterThan(0.9999);
  expect(dot(direction(centered), direction(initial))).toBeLessThan(0.999);

  // restaurar: volta exatamente à vista padrão
  await page.getByTestId('camera-reset').click();
  await expect.poll(async () => norm(sub((await camera(page)).position, initial.position))).toBeLessThan(1e-6);
  expect(norm((await camera(page)).target)).toBeLessThan(1e-6);

  // os mesmos dois comandos pelo teclado (F centraliza, R restaura)
  await stage.focus();
  await page.keyboard.press('Alt+ArrowUp');
  await page.keyboard.press('ArrowRight');
  expect(norm((await camera(page)).target)).toBeGreaterThan(0.01 * distance);
  await page.keyboard.press('f');
  expect(norm((await camera(page)).target)).toBeLessThan(0.02 * distance);
  await page.keyboard.press('r');
  await expect.poll(async () => norm(sub((await camera(page)).position, initial.position))).toBeLessThan(1e-6);
});

test('L4 — célula unitária × supercélula e legenda com os parâmetros de rede do motor', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  const legend = page.getByTestId('scene-legend');
  await expect(page.getByTestId('legend-cells')).toHaveText('Célula unitária');
  // a legenda repete o valor de a que o motor devolveu (o mesmo do cartão de resultado)
  const metricA = (await page.getByTestId('metric-a').innerText()).match(/\d,\d{4}/)?.[0];
  expect(metricA).toBeTruthy();
  await expect(page.getByTestId('legend-lattice')).toHaveText(`a = ${metricA} nm`);
  await expect(page.getByTestId('cell-lattice')).toHaveText(`a = ${metricA} nm`);

  const unitAtoms = await page.evaluate(() => (window as unknown as { __alloy: { viewer: ViewerHooks } }).__alloy.viewer.atoms().length);
  await page.getByTestId('cell-control').getByRole('radio', { name: 'Supercélula' }).check();
  await expect(page.getByTestId('legend-cells')).toHaveText('Supercélula 2×2×2');
  await expect(page.locator('#supercell-select')).toHaveValue('2x2x2');
  await expect.poll(() => page.evaluate(() => (window as unknown as { __alloy: { viewer: ViewerHooks } }).__alloy.viewer.atoms().length)).toBeGreaterThan(unitAtoms);
  await page.getByTestId('cell-control').getByRole('radio', { name: 'Célula unitária' }).check();
  await expect(page.getByTestId('legend-cells')).toHaveText('Célula unitária');

  // a legenda acompanha o que está desenhado
  await reveal(page, 'appearance');
  await expect(legend).toContainText('Eixos x y z');
  await page.getByTestId('toggle-axes').click();
  await expect(page.getByTestId('toggle-axes')).toHaveAttribute('aria-pressed', 'false');
  await expect(legend).not.toContainText('Eixos');
  await page.getByTestId('toggle-latticePoints').click();
  await expect(legend).toContainText('Pontos de rede');

  // HC: a, c e c/a vêm do resultado do motor
  await page.getByTestId('block-list').getByRole('button', { name: /Mg · Magnésio/ }).click();
  await expect(page.locator('#resultTitle')).toContainText('Magnésio');
  await expect(page.getByTestId('legend-lattice')).toHaveText(/^a = \d,\d{4} nm · c = \d,\d{4} nm · c\/a = \d,\d{3}$/);
  expect(await page.getByTestId('cell-lattice').innerText()).toBe(await page.getByTestId('legend-lattice').innerText());

  // legenda recolhível
  await page.getByTestId('legend-toggle').click();
  await expect(page.getByTestId('legend-toggle')).toHaveAttribute('aria-expanded', 'false');
  await expect(legend).toHaveCount(0);
});

test('L5 — tela estreita: a barra é gaveta sobreposta, a cena continua em área total, Esc fecha', async ({ app: page }) => {
  await page.setViewportSize({ width: 800, height: 700 });
  await openCrystalabNarrow(page);
  const toggle = page.getByTestId('sidebar-toggle');
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await expectStageFills(page, 0);
  await toggle.click();
  await expect(page.locator('#crystal-sidebar')).toBeVisible();
  await expect(page.getByTestId('sidebar-close')).toBeFocused();
  await expectStageFills(page, 0); // sobreposta: não empurra a cena
  await page.keyboard.press('Escape');
  await expect(page.locator('#crystal-sidebar')).toBeHidden();
  await expect(toggle).toBeFocused();
});

/** Em tela estreita a barra começa fechada: espera a cena, não os cartões. */
async function openCrystalabNarrow(page: Page): Promise<void> {
  await page.goto('/#/crystalab');
  await viewerReady(page);
  await expect(page.locator('#resultTitle')).toContainText('Ferro');
}
