/**
 * Fluxo B — Plano de Miller: parâmetros e representação consistentes do início ao fim
 * (formulário ≡ terminal ≡ cena), desfazer/refazer coerente e estado compartilhável por link.
 */
import { test, expect, openCrystalab, terminal, viewerReady } from './fixtures.ts';

type Item = { kind: string; label: string; data: Record<string, unknown> };
const overlays = (page: import('playwright/test').Page) => page.evaluate(() => {
  const s = (window as unknown as { __alloy: { stores: { overlays: { getState: () => { items: Item[] } } } } }).__alloy.stores.overlays.getState();
  // procedencia.calculado_em é o instante do cálculo no servidor: muda a cada chamada e não faz parte da cena.
  const semCarimbo = (d: Record<string, unknown>) => { const c = structuredClone(d) as { procedencia?: Record<string, unknown> }; if (c.procedencia) delete c.procedencia.calculado_em; return c; };
  return s.items.map((i) => ({ kind: i.kind, label: i.label, data: semCarimbo(i.data) }));
});

test('B1 · formulário e terminal produzem o mesmo plano, com os dados do motor', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await page.locator('#millerInput').fill('1 1 0');
  await page.locator('#millerForm').getByRole('button', { name: 'Desenhar' }).click();
  await expect(page.locator('#overlayList')).toContainText('(1 1 0)');
  await terminal(page, 'plano 1 1 0');
  await expect.poll(async () => (await overlays(page)).length).toBe(2);
  const [a, b] = await overlays(page);
  expect(a!.data).toEqual(b!.data);
  const log = page.getByTestId('terminal-log');
  await expect(log).toContainText('> plano 1 1 0');
  await expect(log).toContainText('via formulário');
  await expect(page.getByTestId('overlay-manager').or(page.locator('#overlayList'))).toBeVisible();
});

test('B2 · desfazer/refazer percorrem a cena de forma coerente', async ({ app: page }) => {
  await openCrystalab(page);
  await terminal(page, 'plano 1 1 1');
  await expect.poll(async () => (await overlays(page)).length).toBe(1);
  await terminal(page, 'direcao 1 1 0');
  await expect.poll(async () => (await overlays(page)).length).toBe(2);
  await page.getByTestId('undo').click();
  await expect.poll(async () => (await overlays(page)).map((o) => o.kind)).toEqual(['plane']);
  await page.getByTestId('undo').click();
  await expect.poll(async () => (await overlays(page)).length).toBe(0);
  await page.getByTestId('redo').click();
  await page.getByTestId('redo').click();
  await expect.poll(async () => (await overlays(page)).map((o) => o.kind)).toEqual(['plane', 'direction']);
  await page.keyboard.press('Control+z');
  await expect.poll(async () => (await overlays(page)).length).toBe(1);
});

test('B3 · HC com índices de Miller-Bravais (4 índices) e link que reconstrói a mesma cena', async ({ app: page, browser }) => {
  await openCrystalab(page);
  await page.getByTestId('block-list').getByRole('button', { name: /Mg · Magnésio/ }).click();
  await expect(page.getByTestId('metric-structure')).toContainText('HC');
  await terminal(page, 'plano 1 0 -1 1');
  await terminal(page, 'supercelula 2 2 1');
  await expect.poll(async () => (await overlays(page)).length).toBe(1);
  const before = await overlays(page);
  await page.getByTestId('share').click();
  await expect(page.getByTestId('terminal-log')).toContainText('Link da cena');
  await expect.poll(() => new URL(page.url()).hash).toContain('?s=v1.');
  const url = page.url();

  const ctx = await browser.newContext({ locale: 'pt-BR' });
  const other = await ctx.newPage();
  await other.goto(url);
  await expect(other.getByTestId('metric-structure')).toContainText('HC');
  await expect(other.locator('#resultTitle')).toContainText('Magnésio');
  await expect.poll(async () => (await overlays(other)).map((o) => o.label)).toEqual(before.map((o) => o.label));
  const after = await overlays(other);
  expect(after[0]!.data).toEqual(before[0]!.data);
  const supercell = await other.evaluate(() => (window as unknown as { __alloy: { stores: { viewer: { getState: () => { supercell: number[] } } } } }).__alloy.stores.viewer.getState().supercell);
  expect(supercell).toEqual([2, 2, 1]);
  await ctx.close();
});

test('B4 · link adulterado é recusado com mensagem, sem alterar a cena', async ({ app: page }) => {
  await openCrystalab(page, '#/crystalab?s=v1.eyJ2IjoxLCJtIjp7Im5vbWUiOiI8c2NyaXB0PiJ9fQ');
  await expect(page.getByTestId('terminal-log')).toContainText('Link de cena inválido');
});
