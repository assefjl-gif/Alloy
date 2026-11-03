/**
 * Complementos dos gates das Etapas 5–7: transporte HEA pela URL (recarregar mantém a cópia
 * original; alteração é recusada), cores+formas por elemento só como ilustração com semente,
 * recomendações de revisão e selos, captura de cena no caderno, rascunhos do professor e
 * movimento reduzido.
 */
import { test, expect, openCrystalab, terminal } from './fixtures.ts';
import type { Page } from 'playwright/test';

const transferJson = (page: Page) => page.evaluate(() => JSON.stringify((window as unknown as { __alloy: { stores: { crystalab: { getState: () => { heaTransfer: unknown } } } } }).__alloy.stores.crystalab.getState().heaTransfer));

test('5.3 · resultado HEA atravessa por store + URL: recarregar mantém a cópia; adulteração é recusada', async ({ app: page }) => {
  await page.goto('/#/hea');
  await page.getByTestId('analyze-button').click();
  await page.getByTestId('open-in-crystalab').click();
  await expect(page.getByTestId('hea-banner')).toBeVisible();
  await expect.poll(() => new URL(page.url()).hash).toContain('h=');
  const before = await transferJson(page);
  // recarrega também um link que só traz a referência h= (sem estado de cena)
  const h = new URL(page.url().replace('#/', '')).searchParams.get('h');
  await page.goto(`/#/crystalab?h=${h}`);
  await expect(page.getByTestId('metric-structure')).toContainText('CFC');
  expect(await transferJson(page)).toBe(before);
  await page.reload();
  await expect(page.getByTestId('hea-banner')).toBeVisible();
  expect(await transferJson(page)).toBe(before);
  // adultera a cópia guardada: a impressão digital não confere e o transporte é descartado
  await page.evaluate(() => { for (const k of Object.keys(sessionStorage)) if (k.startsWith('alloy.hea.transfer.')) sessionStorage.setItem(k, sessionStorage.getItem(k)!.replace('"delta":', '"delta":9')); });
  await page.reload();
  await expect(page.getByTestId('terminal-log')).toContainText('foi alterado e foi descartado');
  await expect(page.getByTestId('hea-banner')).toHaveCount(0);
});

test('5.4/5.5 · cores e formas por elemento: só ilustração, com semente reproduzível e legenda textual', async ({ app: page }) => {
  await page.goto('/?demo=1#/hea');   // coloração aleatória por elemento só existe no modo demonstrativo
  await page.getByTestId('analyze-button').click();
  await page.getByTestId('open-in-crystalab').click();
  await page.getByRole('tab', { name: 'Procedência' }).click();
  await page.getByTestId('toggle-coloring').click();
  await expect(page.getByTestId('coloring-seed')).toContainText('Semente');
  const legend = page.getByRole('list', { name: /Legenda de elementos/ });
  // uma entrada por elemento da composição analisada (CoCrFeNi no motor real; 5 na liga demonstrativa)
  const elements = await page.evaluate(() => Object.keys((window as unknown as { __alloy: { stores: { hea: { getState: () => { result: { comp_percent: Record<string, number> } } } } } }).__alloy.stores.hea.getState().result.comp_percent).length);
  expect(elements).toBeGreaterThanOrEqual(2);
  await expect(legend.getByRole('listitem')).toHaveCount(elements);
  await expect(legend).toContainText('esfera');
  await expect(page.getByTestId('viewer-stage').getByTestId('demo-seal')).toContainText('Ilustrativo');
  const seed1 = await page.getByTestId('coloring-seed').innerText();
  await page.getByRole('button', { name: 'Nova semente' }).click();
  await expect(page.getByTestId('coloring-seed')).not.toHaveText(seed1);
});

test('6.11 · recomendações de revisão e selos de conclusão, sem ranking', async ({ app: page }) => {
  await page.goto('/#/aprender/atomos-por-celula');
  for (let i = 0; i < 2; i += 1) {
    await page.getByLabel('Total n').fill('99');
    await page.getByTestId('exercise-check').click();
    await page.waitForTimeout(150);
  }
  await page.goto('/#/aprender');
  await expect(page.getByTestId('review-recs')).toContainText('Átomos por célula unitária');
  await expect(page.getByTestId('progress-panel').getByRole('table')).not.toContainText(/posição|lugar|tempo/i);
});

test('6.13 · “Anotar cena”: nota com captura, valores do motor e link para reabrir', async ({ app: page }) => {
  await openCrystalab(page);
  await terminal(page, 'plano 1 1 0');
  await page.waitForFunction(() => Boolean((window as { __alloy?: { viewer?: unknown } }).__alloy?.viewer));
  await page.getByTestId('capture-note').click();
  await expect(page.getByTestId('toast').filter({ hasText: 'Cena anotada' })).toBeVisible();
  await page.goto('/#/diario');
  const note = page.getByTestId('notes').getByRole('listitem').first();
  await expect(note.getByRole('img', { name: /Captura da cena 3D/ })).toBeVisible();
  await expect(note).toContainText('densidade_motor');
  await expect(note).toContainText('(1 1 0)');
  await note.getByRole('link', { name: 'Reabrir cena' }).click();
  await expect(page.locator('#resultTitle')).toContainText('Ferro');
});

test('6.15/6.18 · professor: instruções, critérios e rascunho local; publicar nunca é confirmado', async ({ app: page }) => {
  await page.goto('/#/crystalab');
  await page.evaluate(() => (window as unknown as { __alloy: { stores: { preferences: { getState: () => { set: (p: object) => void } } } } }).__alloy.stores.preferences.getState().set({ role: 'instructor' }));
  await page.goto('/#/professor');
  const panel = page.getByTestId('assign-panel');
  await panel.getByTestId('assign-instructions').fill('Resolver antes da aula de quinta.');
  await panel.locator('summary', { hasText: 'Critérios de avaliação' }).click();
  await expect(panel).toContainText('desvio ≤ 1 %');
  await panel.getByTestId('save-draft').click();
  await expect(page.getByTestId('drafts')).toContainText('rascunho local, não publicado');
  await panel.getByTestId('publish-button').click();
  await expect(page.getByTestId('publish-result')).toContainText('Não publicado');
});

test('7.5 · movimento reduzido: animação não roda sozinha; avanço passo a passo continua disponível', async ({ app: page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await openCrystalab(page);
  await terminal(page, 'animacao empilhamento abab');
  const panel = page.getByTestId('animations-panel');
  await expect(panel).toContainText('Movimento reduzido ativo');
  await expect(panel.getByRole('button', { name: 'Reproduzir' })).toBeDisabled();
  await panel.getByRole('button', { name: 'Próximo passo' }).click();
  await expect(panel).toContainText('A · B');
});
