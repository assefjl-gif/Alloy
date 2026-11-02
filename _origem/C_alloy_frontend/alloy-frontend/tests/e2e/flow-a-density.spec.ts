/**
 * Fluxo A — Densidade do cobre: cálculo guiado completo SEM digitar comandos (Etapas 3, 4 e 6).
 * Todos os números esperados vêm de uma chamada direta ao motor real, nunca de cálculo no teste.
 */
import { test, expect, openCrystalab } from './fixtures.ts';

async function engineCu(request: import('playwright/test').APIRequestContext) {
  const res = await request.post('http://127.0.0.1:8010/api/estrutura', { data: { nome: 'Cu' } });
  return (await res.json()).result as { n: number; a_nm: number; volume_cm3: number; densidade: number; estrutura: string };
}

const pt = (v: number, d: number) => v.toFixed(d).replace('.', ',');

test('A1 · laboratório: modo guiado carrega Cu e mostra a densidade do motor, com comando equivalente', async ({ app: page, request }) => {
  const cu = await engineCu(request);
  await openCrystalab(page);
  const guided = page.getByTestId('guided-mode');
  await guided.getByRole('combobox', { name: 'Metal do catálogo' }).selectOption('Cu');
  await expect(guided.getByTestId('equivalent-command').first()).toHaveText('usar Cu');
  await guided.getByTestId('guided-load').click();
  await expect(page.getByTestId('metric-structure')).toContainText('CFC');
  await expect(page.locator('#resultTitle')).toContainText('Cobre');
  await guided.getByTestId('guided-density').click();
  const panel = page.getByTestId('density-panel');
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(`ρ = ${pt(cu.densidade, 3)} g/cm³`);
  await expect(page.getByTestId('metric-density')).toContainText(pt(cu.densidade, 3));
  const log = page.getByTestId('terminal-log');
  await expect(log).toContainText('> usar Cu');
  await expect(log).toContainText('via formulário');
  await expect(log).toContainText('> calcular densidade');
});

test('A2 · exercício guiado: 7 passos, erro de unidade identificado, resultado do motor revelado e registro no caderno', async ({ app: page, request }) => {
  const cu = await engineCu(request);
  await page.goto('/#/aprender/densidade-cobre');
  const ex = page.getByTestId('density-exercise');
  await expect(ex).toHaveAttribute('data-step', 'dados');
  await expect(ex).toContainText('Cobre');
  await ex.getByTestId('exercise-next').click();

  // grandezas
  for (const id of ['n', 'A', 'Vc', 'NA']) await page.locator(`#q-${id}`).check();
  await ex.getByTestId('exercise-check').click();
  await expect(ex.getByTestId('exercise-feedback')).toContainText('Correto');
  await ex.getByTestId('exercise-next').click();

  // equação: primeiro uma errada (feedback), depois a certa
  await ex.getByTestId('eq-inv').check();
  await ex.getByTestId('exercise-check').click();
  await expect(ex.getByTestId('exercise-feedback')).toContainText('✗');
  await ex.getByTestId('eq-ok').check();
  await ex.getByTestId('exercise-check').click();
  await expect(ex.getByTestId('exercise-feedback')).toContainText('Correto');
  await ex.getByTestId('exercise-next').click();

  // substituição — valores do motor, digitados com vírgula decimal
  await ex.getByTestId('in-n').fill(String(cu.n));
  await ex.getByTestId('in-a').fill(pt(cu.a_nm, 4));
  await ex.getByTestId('in-vc').fill(cu.volume_cm3.toExponential(3).replace('.', ','));
  await ex.getByTestId('exercise-check').click();
  await expect(ex.getByTestId('exercise-feedback')).toContainText('Correto');
  await ex.getByTestId('exercise-next').click();

  // validação: erro de unidade (esqueceu 10⁻²¹) → classificado como unidade
  await ex.getByTestId('in-rho').fill(String(cu.densidade * 1e21));
  await ex.getByTestId('exercise-check').click();
  await expect(ex.getByTestId('exercise-feedback')).toContainText('Erro de unidade');
  await ex.getByTestId('in-rho').fill(pt(cu.densidade, 2));
  await ex.getByTestId('exercise-check').click();
  await expect(ex.getByTestId('exercise-feedback')).toContainText('Correto');
  await ex.getByTestId('exercise-next').click();

  // motor revelado depois da tentativa
  await expect(ex).toHaveAttribute('data-step', 'motor');
  await expect(ex.getByTestId('exercise-compare')).toContainText(pt(cu.densidade, 3));
  await ex.getByTestId('exercise-next').click();

  // revisão
  await expect(ex.getByTestId('exercise-review')).toContainText('tentativa');
  await ex.getByTestId('exercise-to-notebook').click();
  await ex.getByTestId('exercise-complete').click();
  await expect(page.getByTestId('progress-panel')).toContainText('1 de 9');

  await page.getByRole('link', { name: 'Caderno' }).click();
  const notes = page.getByTestId('notes');
  await expect(notes).toContainText('Densidade teórica do cobre');
  await expect(notes).toContainText(`Motor: ρ = ${pt(cu.densidade, 3)} g/cm³`);
});
