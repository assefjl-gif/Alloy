/**
 * Fluxo D — Professor e turma: dados reais separados de demonstrativos; nenhuma publicação
 * sem confirmação do serviço (não há serviço de turmas — D-03).
 */
import { readFileSync } from 'node:fs';
import { inflateRawSync } from 'node:zlib';
import { test, expect } from './fixtures.ts';

/** Lê um arquivo de dentro de um .docx (zip) sem dependências. */
function zipEntry(buf: Buffer, name: string): string | null {
  let i = 0;
  while ((i = buf.indexOf(Buffer.from([0x50, 0x4b, 0x03, 0x04]), i)) >= 0) {
    const method = buf.readUInt16LE(i + 8);
    const size = buf.readUInt32LE(i + 18);
    const nameLen = buf.readUInt16LE(i + 26);
    const extra = buf.readUInt16LE(i + 28);
    const entry = buf.toString('utf8', i + 30, i + 30 + nameLen);
    const start = i + 30 + nameLen + extra;
    if (entry === name) {
      const data = buf.subarray(start, start + size);
      return (method === 8 ? inflateRawSync(data) : data).toString('utf8');
    }
    i = start + size;
  }
  return null;
}

test('D1 · perfil professor, turma demonstrativa selada e publicação nunca confirmada', async ({ app: page }) => {
  await page.goto('/#/crystalab');
  await expect(page.getByRole('link', { name: 'Professor' })).toHaveCount(0);
  await page.getByTestId('settings-button').click();
  await page.getByRole('radio', { name: 'Professor' }).check();
  await page.getByRole('button', { name: 'Concluir' }).click();
  await page.getByRole('link', { name: 'Professor' }).click();
  const panel = page.getByTestId('instructor');
  await expect(panel.getByTestId('demo-seal').first()).toBeVisible();
  await expect(panel).toContainText('semente 4242');
  await expect(panel).toContainText('nenhum estudante é comparado', { ignoreCase: true });

  await page.getByTestId('publish-button').click();
  await expect(page.getByTestId('publish-result')).toContainText('Não publicado');
  await expect(page.getByTestId('publish-result')).toContainText('nada foi publicado');

  const [download] = await Promise.all([page.waitForEvent('download'), page.getByTestId('instructor-docx').click()]);
  expect(download.suggestedFilename()).toContain('DEMONSTRATIVO');
  const xml = zipEntry(readFileSync((await download.path())!), 'word/document.xml');
  expect(xml).toContain('Dados fictícios com semente 4242');
});

test('D2 · dados deste navegador: vazios até haver tentativas reais; nunca misturados com a demo', async ({ app: page }) => {
  await page.goto('/#/crystalab');
  await page.evaluate(() => (window as unknown as { __alloy: { stores: { preferences: { getState: () => { set: (p: object) => void } } } } }).__alloy.stores.preferences.getState().set({ role: 'instructor' }));
  await page.goto('/#/professor');
  await page.getByRole('radio', { name: 'Dados deste navegador' }).check();
  await expect(page.getByTestId('instructor-empty')).toBeVisible();
  await expect(page.getByTestId('instructor-docx')).toBeDisabled();
  await expect(page.getByTestId('instructor').getByTestId('demo-seal')).toHaveCount(0);

  // uma tentativa real no quiz
  await page.goto('/#/aprender/quiz-estruturas');
  const quiz = page.getByTestId('quiz');
  await expect(quiz.getByTestId('quiz-check')).toBeVisible();
  if (await quiz.locator('input[type="radio"]').count()) await quiz.locator('input[type="radio"]').first().check();
  else await quiz.getByTestId('quiz-short').fill('0');
  await quiz.getByTestId('quiz-check').click();
  await page.goto('/#/professor');
  await page.getByRole('radio', { name: 'Dados deste navegador' }).check();
  await expect(page.getByTestId('instructor-empty')).toHaveCount(0);
  await expect(page.getByTestId('metric-completion')).toContainText('/9');
  await expect(page.getByTestId('instructor-docx')).toBeEnabled();
});
