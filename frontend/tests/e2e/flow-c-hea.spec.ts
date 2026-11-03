/**
 * Fluxo C — HEA → CrystaLab: a transição não cria dados nem altera o resultado original (Etapa 5).
 * O motor HEA não existe neste repositório (D-01): o preditor roda em modo demonstrativo,
 * e o teste também confere que o selo demonstrativo acompanha o resultado até o CrystaLab.
 */
import { test, expect } from './fixtures.ts';
import type { Page } from 'playwright/test';

const heaResult = (page: Page) => page.evaluate(() => JSON.stringify((window as unknown as { __alloy: { stores: { hea: { getState: () => { result: unknown } } } } }).__alloy.stores.hea.getState().result));
const transfer = (page: Page) => page.evaluate(() => {
  const t = (window as unknown as { __alloy: { stores: { crystalab: { getState: () => { heaTransfer: { result: unknown; structure: { code: string; basis: string }; origin: string } | null } } } } }).__alloy.stores.crystalab.getState().heaTransfer;
  return t ? { result: JSON.stringify(t.result), code: t.structure.code, basis: t.structure.basis, origin: t.origin, frozen: Object.isFrozen(t) && Object.isFrozen(t.result) } : null;
});

test('C1 · fase com estrutura única: abre direto, parâmetros idênticos antes e depois', async ({ app: page }) => {
  await page.goto('/#/hea');
  await page.getByTestId('analyze-button').click();
  await expect(page.getByTestId('hea-demo-banner')).toBeVisible();
  const before = await heaResult(page);
  expect(before).not.toBe('null');
  await page.getByTestId('open-in-crystalab').click();
  await expect(page).toHaveURL(/#\/crystalab/);
  await expect(page.getByTestId('hea-banner')).toBeVisible();
  await expect(page.getByTestId('basis-predictor')).toBeVisible();
  await expect(page.getByTestId('hea-banner').getByTestId('demo-seal')).toBeVisible();
  const tr = await transfer(page);
  expect(tr).not.toBeNull();
  expect(tr!.result).toBe(before);
  expect(tr!.frozen).toBe(true);
  expect(tr!.basis).toBe('predictor-phase');
  expect(await heaResult(page)).toBe(before);
  // a célula exibida é a idealizada genérica: o CrystaLab não inventa densidade para a liga
  await expect(page.getByTestId('metric-density')).toContainText('n/d');
  await page.getByRole('tab', { name: 'Procedência' }).click();
  await expect(page.getByTestId('prov-identical')).toContainText('idêntico');
  await expect(page.getByTestId('delta-limitation')).toBeVisible();
  // volta ao HEA: resultado intacto
  await page.getByRole('link', { name: 'HEA Virtual Lab' }).click();
  expect(await heaResult(page)).toBe(before);
});

test('C2 · fase ambígua: exige escolha explícita, registrada como do usuário (não predição)', async ({ app: page }) => {
  await page.goto('/#/hea');
  await page.getByRole('button', { name: /Liga demonstrativa B/ }).click();
  await page.getByTestId('analyze-button').click();
  const card = page.getByTestId('bridge-card');
  await expect(card).toContainText('não indica uma única estrutura');
  await expect(page.getByTestId('open-in-crystalab')).toHaveCount(0);
  const before = await heaResult(page);
  await page.getByTestId('open-in-crystalab-CCC').click();
  await expect(page.getByTestId('basis-user')).toContainText('escolhida por você');
  const tr = await transfer(page);
  expect(tr!.basis).toBe('user-choice');
  expect(tr!.code).toBe('CCC');
  expect(tr!.result).toBe(before);
});

test('C3 · terminal HEA: "cristalab" sem escolha em fase ambígua pede opção e não abre nada', async ({ app: page }) => {
  await page.goto('/#/hea');
  await page.getByRole('button', { name: /Liga demonstrativa B/ }).click();
  const input = page.locator('#term-input-hea');
  await input.fill('analisar');
  await input.press('Enter');
  await input.fill('cristalab');
  await input.press('Enter');
  await expect(page.getByRole('group', { name: /cita mais de uma estrutura|não cita estrutura/ })).toBeVisible();
  await expect(page).toHaveURL(/#\/hea/);
});
