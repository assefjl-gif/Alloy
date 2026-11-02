/**
 * Viewer (Etapa 3) e didática (Etapa 6) — complementos dos fluxos: medição sobre posições do
 * motor, réplicas que não alteram n, animações rotuladas como ilustração e ABP completa.
 */
import { test, expect, openCrystalab, terminal, viewerReady } from './fixtures.ts';

test('medição de distância entre átomos usa posições do motor × a do motor', async ({ app: page, request }) => {
  const fe = (await (await request.post('http://127.0.0.1:8010/api/estrutura', { data: { nome: 'Fe' } })).json()).result;
  await openCrystalab(page);
  // átomo 1 (vértice 0,0,0) e o centro do corpo: a distância é a√3/2 = 2R no CCC
  const idxCenter = (fe.atomos as Array<{ tipo: string }>).findIndex((a) => a.tipo === 'centro') + 1;
  const idxOrigin = (fe.atomos as Array<{ pos: number[] }>).findIndex((a) => a.pos.every((v) => v === 0)) + 1;
  await terminal(page, `medir distancia ${idxOrigin} ${idxCenter}`);
  const expected = (fe.a_nm * Math.sqrt(3) / 2).toFixed(4).replace('.', ',');
  await expect(page.getByTestId('terminal-log')).toContainText(expected);
  expect(Number((2 * fe.raio_nm).toFixed(4))).toBeCloseTo(fe.a_nm * Math.sqrt(3) / 2, 3);
});

test('supercélula: réplicas gráficas não alteram n nem a densidade exibidos', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  const n = await page.getByTestId('metric-n').innerText();
  const rho = await page.getByTestId('metric-density').innerText();
  await terminal(page, 'supercelula 3');
  await expect.poll(() => page.evaluate(() => (window as unknown as { __alloy: { viewer: { atoms: () => Array<{ replica: boolean }> } } }).__alloy.viewer.atoms().filter((a) => a.replica).length)).toBeGreaterThan(0);
  expect(await page.getByTestId('metric-n').innerText()).toBe(n);
  expect(await page.getByTestId('metric-density').innerText()).toBe(rho);
});

test('animações: empilhamento rotulado como ilustração; α→γ usa os dois resultados do motor', async ({ app: page }) => {
  await openCrystalab(page);
  await terminal(page, 'animacao empilhamento abab');
  await expect(page.getByTestId('viewer-stage').getByTestId('demo-seal')).toContainText('Ilustrativo');
  await terminal(page, 'animacao alfa-gama');
  const panel = page.getByTestId('animations-panel');
  await expect(panel).toContainText('CCC');
  await expect(panel).toContainText('CFC');
});

test('ABP Al × Cu: hipóteses, evidências dos três tipos e conclusão registrada no caderno', async ({ app: page }) => {
  await page.goto('/#/aprender/abp-al-cu');
  const pbl = page.getByTestId('pbl');
  await expect(pbl).toContainText('Al');
  await expect(page.getByTestId('pbl-complete')).toBeDisabled();
  await pbl.getByTestId('pbl-hyp-input').fill('A massa atômica do Cu é maior');
  await pbl.getByRole('button', { name: 'Adicionar' }).first().click();
  for (const [kind, text] of [['observation', 'Os dois são CFC, n = 4'], ['calculation', 'A(Cu)/A(Al) ≈ 2,36'], ['interpretation', 'A massa pesa mais que o volume']] as const) {
    await pbl.getByTestId('pbl-evidence-input').fill(text);
    await pbl.getByTestId('pbl-evidence-kind').selectOption(kind);
    await pbl.getByRole('button', { name: 'Adicionar' }).nth(1).click();
  }
  await pbl.getByTestId('pbl-conclusion').fill('Com o mesmo n, a densidade cresce com A (massa) e cai com Vc (volume); A domina.');
  await expect(page.getByTestId('pbl-complete')).toBeEnabled();
  await page.getByTestId('pbl-complete').click();
  await page.goto('/#/diario');
  await expect(page.getByTestId('notes')).toContainText('A domina');
});
