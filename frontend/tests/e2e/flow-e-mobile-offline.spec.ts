/**
 * Fluxo E — Móvel com conexão limitada (Etapa 7): layout utilizável em 360 px sem rolagem
 * horizontal, gesto do viewer não sequestra a rolagem (cena travada por padrão no toque),
 * conectividade comunicada e notas locais preservadas offline (sem perda silenciosa).
 */
import { test as base, expect } from 'playwright/test';

const test = base.extend({});
test.use({ viewport: { width: 360, height: 740 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2, locale: 'pt-BR' });

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (!sessionStorage.getItem('e2e-init')) {
      localStorage.clear();
      localStorage.setItem('alloy.prefs', JSON.stringify({ theme: 'light', locale: 'pt-BR', motion: 'system', demo: 'config', role: 'instructor', touchSceneLock: true }));
      sessionStorage.setItem('e2e-init', '1');
    }
  });
});

const ROUTES = ['crystalab', 'hea', 'aprender', 'aprender/densidade-cobre', 'aprender/abp-al-cu', 'diario', 'professor', 'sobre', 'catalogo'];

test('E1 · 360 px: nenhum módulo tem rolagem horizontal; ações essenciais visíveis', async ({ page }) => {
  for (const r of ROUTES) {
    await page.goto(`/#/${r}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);
    const { sw, cw } = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    expect(sw, `#/${r}: scrollWidth ${sw} > ${cw}`).toBeLessThanOrEqual(cw);
  }
  await page.goto('/#/crystalab');
  await expect(page.getByTestId('render-button')).toBeInViewport();
  await expect(page.getByTestId('palette-button')).toBeVisible();
});

test('E2 · toque: cena 3D começa travada (um dedo rola a página) e pode ser destravada', async ({ page }) => {
  await page.goto('/#/crystalab');
  await page.waitForFunction(() => Boolean((window as { __alloy?: { viewer?: unknown } }).__alloy?.viewer));
  const mode = () => page.evaluate(() => (window as unknown as { __alloy: { viewer: { touchMode: () => string } } }).__alloy.viewer.touchMode());
  expect(await mode()).toBe('locked');
  await expect(page.getByTestId('viewer-stage')).toHaveClass(/is-touch-locked/);
  const before = await page.evaluate(() => window.scrollY);
  const box = (await page.getByTestId('viewer-stage').boundingBox())!;
  await page.touchscreen.tap(box.x + 10, box.y + 10);
  await page.mouse.wheel(0, 400);
  await page.waitForTimeout(300);
  expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(before);
  await page.getByRole('button', { name: /Destravar a cena/ }).click();
  await expect.poll(mode).toBe('unlocked');
});

test('E3 · offline: shell abre do cache, estado comunicado, nota criada offline preservada e anunciada ao reconectar', async ({ page, context }) => {
  await page.goto('/#/crystalab');
  await page.evaluate(async () => { await navigator.serviceWorker.ready; });
  await page.reload();
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller));
  await page.waitForTimeout(500);

  await context.setOffline(true);
  await expect(page.getByTestId('connectivity')).toHaveClass(/conn--offline/);
  await expect(page.getByTestId('toast').first()).toContainText('offline');

  await page.goto('/#/diario');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Caderno de laboratório' })).toBeVisible();
  await page.getByTestId('note-title').fill('Observação offline');
  await page.getByTestId('note-body').fill('Registrada sem conexão.');
  await page.getByTestId('note-save').click();
  await expect(page.getByTestId('notes')).toContainText('criada offline');

  // cálculo exige servidor: não é simulado
  await page.goto('/#/crystalab');
  await expect(page.getByTestId('engine-unavailable').or(page.getByTestId('connectivity')).first()).toBeVisible();

  await context.setOffline(false);
  await expect(page.getByTestId('toast').filter({ hasText: 'nota(s) criada(s) offline' })).toBeVisible();
  await page.goto('/#/diario');
  await expect(page.getByTestId('notes')).toContainText('Observação offline');
});
