/**
 * Ligas e temperatura (T-13; sugestões Miná 2, 3 e 6): do formulário ao viewer, com o MOTOR REAL.
 * O que se confere: os números exibidos são os do motor (contagens, regras, rede), o viewer desenha
 * um átomo por átomo da liga, a vibração usa a amplitude do motor e respeita movimento reduzido.
 */
import { test, expect, openCrystalab, viewerReady, reveal } from './fixtures.ts';
import type { Page } from 'playwright/test';

type Viewer = { thermalScene: () => Record<string, number> | null; stats: { renders: number } };
const scene = (page: Page) => page.evaluate(() => (window as unknown as { __alloy: { viewer: Viewer } }).__alloy.viewer.thermalScene?.() ?? null);
const renders = (page: Page) => page.evaluate(() => (window as unknown as { __alloy: { viewer: Viewer } }).__alloy.viewer.stats.renders);

async function formAlloy(page: Page, base: string, solute: string, percent: string) {
  await reveal(page, 'composition');
  await page.getByTestId('alloy-base').selectOption(base);
  await page.getByTestId('alloy-solute').selectOption(solute);
  await page.getByTestId('alloy-percent').fill(percent);
  await page.getByTestId('alloy-submit').click();
  await expect(page.getByTestId('alloy-results')).toBeVisible();
}

test('Liga substitucional Cu–Ni: resultado do motor, regras de Hume-Rothery e átomos no viewer', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  expect(await scene(page)).toBeNull();
  await formAlloy(page, 'Cu', 'Ni', '30');

  await expect(page.getByTestId('alloy-rules').locator('tbody tr')).toHaveCount(4);
  await expect(page.getByTestId('alloy-rules')).toContainText('atende');
  await expect(page.getByTestId('alloy-conclusion')).toContainText('solubilidade');
  await expect(page.getByTestId('alloy-lattice')).toContainText('0,358');
  await expect(page.getByTestId('alloy-provenance')).toContainText('estimativa_modelo');

  // o viewer desenha exatamente os átomos do motor (supercélula 2×2×2: 63 átomos, com Ni e Cu)
  const counts = await scene(page);
  expect(counts).not.toBeNull();
  expect(Object.keys(counts!).sort()).toEqual(['Cu', 'Ni']);
  expect(counts!.Cu! + counts!.Ni!).toBe(63);
  await expect(page.getByTestId('alloy-legend')).toContainText('Ni');
  await expect(page.getByTestId('alloy-legend')).toContainText('solvente');
  // R2-FE-01: contagem separa átomos ÚNICOS de esferas desenhadas (imagens periódicas)
  await expect(page.getByTestId('alloy-atoms')).toContainText('32');
  await expect(page.getByTestId('alloy-atoms')).toContainText('63');
  await expect(page.getByTestId('alloy-viewer-counts')).toContainText('32');
  await expect(page.getByTestId('alloy-counts')).toContainText('32 átomos únicos');
  await expect(page.getByTestId('alloy-counts')).toContainText('63 esferas');
  // composição pedida × representada, nas duas bases
  const composition = page.getByTestId('alloy-composition');
  await expect(composition).toContainText('70,00 %');
  await expect(composition).toContainText('68,75 %');
  await expect(composition).toContainText('massa% representada');
  // realização estatística e o que o motor não verifica
  await expect(page.getByTestId('alloy-realization')).toContainText('realização estatística');
  await expect(page.getByTestId('alloy-checks')).toContainText('não verificado');
  await expect(page.getByTestId('alloy-model')).toContainText('idealizada');

  // voltar ao metal puro remove a liga da cena
  await page.getByTestId('alloy-close').click();
  await expect(page.getByTestId('alloy-results')).toHaveCount(0);
  expect(await scene(page)).toBeNull();
});

/**
 * D-R2-3 (achado T-21): Fe–C a 2 at% em 2×2×2 dá ZERO átomos de carbono — a amostragem honesta do
 * motor arredonda ⌊16·x/(1−x) + ½⌋ para 0. Os DOIS casos são cobertos aqui: supercélula pequena
 * (nenhum C na cena, com aviso acionável e tamanho sugerido PELO MOTOR) e supercélula suficiente
 * (C presente em sítio intersticial). Nenhum átomo é inventado para a cena parecer completa.
 */
test('Liga intersticial Fe–C: supercélula pequena diz que não há soluto e oferece o tamanho do motor; aplicada, o C aparece', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await reveal(page, 'composition');
  await page.getByTestId('alloy-base').selectOption('Fe');
  await page.getByTestId('alloy-solute').selectOption('C');
  await page.getByTestId('alloy-percent').fill('2');
  await page.getByLabel('Mostrar distorção ilustrativa').check();
  await page.getByTestId('alloy-submit').click();
  await expect(page.getByTestId('alloy-results')).toBeVisible();

  // caso 1: nenhum átomo de C na realização — a tela DIZ isso, explica e indica a ação
  const notice = page.getByTestId('alloy-absent-solute');
  await expect(notice).toBeVisible();
  await expect(notice).toContainText('Nenhum átomo de C');
  await expect(notice).toContainText('menos de meio átomo');
  await expect(notice).toContainText('aumentar a supercélula');
  await expect(page.getByTestId('alloy-absent-banner')).toContainText('SEM C');
  const semC = await scene(page);
  expect(Object.keys(semC!)).toEqual(['Fe']);

  // o tamanho sugerido vem do motor (novo pedido ao mesmo endpoint), não de fórmula no cliente
  await expect(page.getByTestId('alloy-absent-suggestion')).toContainText('3×3×3');
  await page.getByTestId('alloy-absent-apply').click();

  // caso 2: na supercélula sugerida o carbono existe, em sítio intersticial
  await expect(page.getByTestId('alloy-absent-solute')).toHaveCount(0);
  await expect(page.getByTestId('alloy-size')).toHaveValue('3');
  await expect(page.getByTestId('alloy-distortion')).toContainText('Distorção ilustrativa');
  await expect(page.getByTestId('alloy-legend')).toContainText('soluto intersticial');
  await expect.poll(async () => Object.keys((await scene(page)) ?? {}).sort().join(',')).toBe('C,Fe');
  const counts = await scene(page);
  expect(counts!.C!).toBeGreaterThan(0);
});

test('Entrada inválida mostra o erro do servidor, sem resultado inventado', async ({ app: page }) => {
  await openCrystalab(page);
  await reveal(page, 'composition');
  await page.getByTestId('alloy-percent').fill('abc');
  await page.getByTestId('alloy-submit').click();
  await expect(page.getByTestId('alloy-error')).toBeVisible();
  await expect(page.getByTestId('alloy-results')).toHaveCount(0);
});

test('Temperatura do metal: dilatação, amplitude e curva do motor; vibração anima o viewer', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await reveal(page, 'analysis.thermal');
  await expect(page.getByTestId('thermal-vibrate')).toBeDisabled();   // sem cálculo não há amplitude
  await page.getByTestId('thermal-submit').click();
  await expect(page.getByTestId('thermal-results')).toBeVisible();
  await expect(page.getByTestId('thermal-homologous')).toBeVisible();
  await expect(page.getByTestId('thermal-amplitude')).toContainText('pm');
  await expect(page.getByTestId('thermal-curve').locator('path.chart__line')).toBeVisible();
  await expect(page.getByTestId('alloy-provenance').last()).toContainText('thermodynamics');

  expect(await scene(page)).toBeNull();                               // vibração desligada: viewer normal
  await page.getByTestId('thermal-vibrate').click();
  await expect.poll(() => scene(page)).not.toBeNull();
  const before = await renders(page);
  await page.waitForTimeout(600);
  expect(await renders(page)).toBeGreaterThan(before + 5);            // quadros contínuos = átomos em movimento
  await page.getByTestId('thermal-vibrate').click();
  await expect.poll(() => scene(page)).toBeNull();
});

test('Temperatura da liga: a vibração usa os átomos da liga; acima da fusão o resultado é sinalizado', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await formAlloy(page, 'Cu', 'Ni', '30');
  await reveal(page, 'analysis.thermal');
  await page.getByRole('radio', { name: 'Liga formada' }).check();
  await page.getByTestId('thermal-submit').click();
  await expect(page.getByTestId('thermal-results')).toBeVisible();
  await page.getByTestId('thermal-vibrate').click();
  const counts = await scene(page);
  expect(Object.keys(counts!).sort()).toEqual(['Cu', 'Ni']);
});

test('Movimento reduzido: a vibração fica congelada (sem quadros contínuos)', async ({ browser }) => {
  const ctx = await browser.newContext({ locale: 'pt-BR', reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  await page.addInitScript(() => { (globalThis as { __name?: unknown }).__name = (f: unknown) => f; });
  await openCrystalab(page);
  await viewerReady(page);
  await reveal(page, 'analysis.thermal');
  await page.getByTestId('thermal-submit').click();
  await expect(page.getByTestId('thermal-results')).toBeVisible();
  await page.getByTestId('thermal-vibrate').click();
  await expect.poll(() => scene(page)).not.toBeNull();
  await page.waitForTimeout(300);
  const before = await renders(page);
  await page.waitForTimeout(600);
  expect(await renders(page) - before).toBeLessThan(3);
  await ctx.close();
});
