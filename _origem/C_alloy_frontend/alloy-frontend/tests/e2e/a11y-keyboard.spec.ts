/**
 * Acessibilidade (Etapa 7, 7.1–7.5 e 7.14 — ver D-19): auditoria própria por regras WCAG 2.2
 * em todos os módulos, nos temas claro e escuro, mais navegação só por teclado.
 * Resultado gravado em reports/a11y.json. NÃO é nota Lighthouse.
 */
import { writeFileSync, mkdirSync } from 'node:fs';
import { test, expect, openCrystalab, terminal } from './fixtures.ts';
import { runA11yAudit, type A11yReport } from '../helpers/a11yAudit.ts';

const ROUTES = ['crystalab', 'hea', 'aprender', 'aprender/densidade-cobre', 'aprender/abp-al-cu', 'aprender/quiz-estruturas', 'diario', 'professor', 'sobre', 'catalogo'];
const reports: Array<A11yReport & { theme: string; route: string }> = [];

for (const theme of ['light', 'dark'] as const) {
  test(`auditoria WCAG — tema ${theme}`, async ({ app: page }) => {
    await page.goto('/#/crystalab');
    await page.evaluate((th) => (window as unknown as { __alloy: { stores: { preferences: { getState: () => { set: (p: object) => void } } } } }).__alloy.stores.preferences.getState().set({ theme: th, role: 'instructor' }), theme);
    const serious: string[] = [];
    for (const route of ROUTES) {
      await page.goto(`/#/${route}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(600);
      if (route === 'hea') await page.getByTestId('analyze-button').click().then(() => page.waitForTimeout(500));
      const rep = await runA11yAudit(page, { focusSamples: 25 });
      reports.push({ ...rep, theme, route });
      for (const v of rep.violations) if (v.impact === 'critical' || v.impact === 'serious') serious.push(`${theme} #/${route} [${v.rule}] ${v.target} — ${v.detail}`);
    }
    mkdirSync('reports', { recursive: true });
    writeFileSync('reports/a11y.json', JSON.stringify({ tool: 'auditoria própria (tests/helpers/a11yAudit.ts) — não é axe-core nem Lighthouse (D-19)', generatedAt: new Date().toISOString(), reports }, null, 1));
    expect(serious, serious.join('\n')).toEqual([]);
  });
}

test('teclado: pular para o conteúdo, paleta Ctrl+K com retorno de foco, terminal com histórico e Tab', async ({ app: page }) => {
  await openCrystalab(page);
  await page.keyboard.press('Tab');
  await expect(page.locator('.ds-skip-link')).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();

  await page.getByTestId('render-button').focus();
  await page.keyboard.press('Control+k');
  await expect(page.getByTestId('palette-input')).toBeFocused();
  await page.keyboard.type('supercélula 2');
  await page.keyboard.press('Enter');
  await expect.poll(() => page.evaluate(() => (window as unknown as { __alloy: { stores: { viewer: { getState: () => { supercell: number[] } } } } }).__alloy.stores.viewer.getState().supercell)).toEqual([2, 2, 2]);

  await page.keyboard.press('Control+k');
  await page.keyboard.press('Escape');
  await expect(page.getByTestId('palette-input')).toBeHidden();

  await terminal(page, 'plano 1 1 1');
  const input = page.locator('#term-input-crystalab');
  await input.focus();
  await page.keyboard.press('ArrowUp');
  await expect(input).toHaveValue('plano 1 1 1');
  await input.fill('calc');
  await page.keyboard.press('Tab');
  await expect(input).toHaveValue(/calcular densidade/);
});

test('viewer por teclado: foco na cena, setas giram, Tab percorre átomos na lista, Enter seleciona', async ({ app: page }) => {
  await openCrystalab(page);
  await page.waitForFunction(() => Boolean((window as { __alloy?: { viewer?: unknown } }).__alloy?.viewer));
  const cam = () => page.evaluate(() => JSON.stringify((window as unknown as { __alloy: { viewer: { camera: () => unknown } } }).__alloy.viewer.camera()));
  await page.getByTestId('viewer-stage').focus();
  const c0 = await cam();
  await page.keyboard.press('ArrowLeft');
  await page.waitForTimeout(150);
  expect(await cam()).not.toBe(c0);
  await page.getByRole('tab', { name: 'Átomo' }).click();
  const list = page.getByRole('listbox');
  await list.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(page.getByTestId('atom-inspector')).toContainText('Átomo');
  await expect(page.locator('#scene-desc')).toContainText('Selecionado');
});
