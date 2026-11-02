/**
 * Fundação e regressão (Etapas 2 e 8.3): navegação sem recarga, temas, idiomas, data-testid
 * herdados do v1.0, interface legada preservada, orçamento do bundle e exportação CIF/XYZ
 * pelo servidor /v1 (porta 5174 → engine-stub).
 */
import { readFileSync } from 'node:fs';
import { test, expect, openCrystalab, terminal } from './fixtures.ts';

test('navegação entre módulos sem recarregar a página', async ({ app: page }) => {
  await openCrystalab(page);
  const bootId = await page.evaluate(() => (window as unknown as { __alloy: { bootId: string } }).__alloy.bootId);
  for (const name of ['HEA Virtual Lab', 'Aprender', 'Caderno', 'CrystaLab']) {
    await page.getByRole('navigation', { name: 'Módulos' }).getByRole('link', { name, exact: true }).click();
    await expect(page.getByRole('navigation', { name: 'Módulos' }).getByRole('link', { name, exact: true })).toHaveAttribute('aria-current', 'page');
  }
  expect(await page.evaluate(() => (window as unknown as { __alloy: { bootId: string } }).__alloy.bootId)).toBe(bootId);
});

test('data-testid do CrystaLab v1.0 preservados e funcionais', async ({ app: page }) => {
  await openCrystalab(page);
  for (const id of ['block-list', 'terminal-log', 'parameter-editor', 'render-button', 'result-root', 'viewer-stage']) await expect(page.getByTestId(id)).toBeVisible();
  // editor de parâmetros + Renderizar, como no v1.0
  await page.getByTestId('parameter-editor').fill('elemento = (genérico)\nestrutura = CFC\nraio = 0.128\npeso = 63.55');
  await page.getByTestId('render-button').click();
  await expect(page.getByTestId('metric-structure')).toContainText('CFC');
  await expect(page.getByTestId('terminal-log')).toContainText('> aplicar');
});

test('tema claro/escuro (inclusive chave do v1.0) e idiomas pt-BR/en/es', async ({ app: page }) => {
  await openCrystalab(page);
  await terminal(page, 'tema escuro');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await terminal(page, 'tema claro');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await terminal(page, 'idioma en');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByRole('link', { name: 'Learn' })).toBeVisible();
  await terminal(page, 'idioma es');
  await expect(page.getByRole('link', { name: 'Cuaderno' })).toBeVisible();
  await terminal(page, 'idioma pt');
  await expect(page.getByRole('link', { name: 'Caderno' })).toBeVisible();

  const legacy = await page.context().newPage();
  await legacy.addInitScript(() => localStorage.setItem('crystalab-theme', 'dark'));
  await legacy.addInitScript(() => localStorage.removeItem('alloy.prefs'));
  await legacy.goto('/#/crystalab');
  await expect(legacy.locator('html')).toHaveAttribute('data-theme', 'dark');
});

test('interface legada v1.0 continua acessível em /legacy/crystalab/', async ({ app: page }) => {
  const res = await page.request.get('/legacy/crystalab/');
  expect(res.status()).toBe(200);
  expect(await res.text()).toContain('CrystaLab');
});

test('orçamento: bundle inicial < 300 kB gzip e Three.js fora do carregamento inicial', async () => {
  const b = JSON.parse(readFileSync('reports/bundle.json', 'utf8')) as { initial: { gzip: number; files: string[]; containsThree: boolean } };
  expect(b.initial.gzip).toBeLessThan(300 * 1024);
  expect(b.initial.containsThree).toBe(false);
});

test('exportação CIF pelo servidor /v1 (sem gerar arquivo no front)', async ({ app: page }) => {
  await page.goto('http://127.0.0.1:5174/#/crystalab');
  await expect(page.getByTestId('metric-density')).toBeVisible();
  await page.getByRole('button', { name: 'Exportar' }).click();
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('menuitem', { name: /CIF/ }).click()]);
  const text = readFileSync((await download.path())!, 'utf8');
  expect(text).toContain('_cell_length_a');
  expect(download.suggestedFilename()).toMatch(/\.cif$/);
});
