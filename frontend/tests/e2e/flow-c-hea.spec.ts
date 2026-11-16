/**
 * Fluxo C — HEA → CrystaLab: a transição não cria dados nem altera o resultado original (Etapa 5).
 * C1–C3 rodam no modo demonstrativo FORÇADO (?demo=1): conferem que o selo acompanha o resultado
 * até o CrystaLab. C4 usa o motor HEA real da API (/api/v1/hea): grandezas sem base aparecem como
 * indisponíveis, com o motivo, e a ponte usa a estrutura sugerida pelo critério de VEC.
 */
import { test, expect, reveal } from './fixtures.ts';
import type { Page } from 'playwright/test';

const heaResult = (page: Page) => page.evaluate(() => JSON.stringify((window as unknown as { __alloy: { stores: { hea: { getState: () => { result: unknown } } } } }).__alloy.stores.hea.getState().result));
const transfer = (page: Page) => page.evaluate(() => {
  const t = (window as unknown as { __alloy: { stores: { crystalab: { getState: () => { heaTransfer: { result: unknown; structure: { code: string; basis: string }; origin: string } | null } } } } }).__alloy.stores.crystalab.getState().heaTransfer;
  return t ? { result: JSON.stringify(t.result), code: t.structure.code, basis: t.structure.basis, origin: t.origin, frozen: Object.isFrozen(t) && Object.isFrozen(t.result) } : null;
});

test('C1 · fase com estrutura única: abre direto, parâmetros idênticos antes e depois', async ({ app: page }) => {
  await page.goto('/?demo=1#/hea');
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
  await reveal(page, 'properties.provenance');
  await expect(page.getByTestId('prov-identical')).toContainText('idêntico');
  await expect(page.getByTestId('delta-limitation')).toBeVisible();
  // volta ao HEA: resultado intacto
  await page.getByRole('link', { name: 'HEA Virtual Lab' }).click();
  expect(await heaResult(page)).toBe(before);
});

/**
 * D-R2-2 (decisão do responsável: demonstração MANTIDA, com selo). Critérios (b), (c) e (e):
 * o selo acompanha cada valor, gráfico e tabela demonstrativos; é distinguível do selo
 * "Ilustrativo" (data-seal="demo"); e a demonstração não emite veredito de estabilidade (A-17).
 */
test('C1b · modo demonstrativo: selo junto de cada valor, gráfico e tabela, e nenhuma triagem de estabilidade', async ({ app: page }) => {
  await page.goto('/?demo=1#/hea');
  await page.getByTestId('analyze-button').click();
  await expect(page.getByTestId('hea-demo-banner')).toBeVisible();

  // (e) A-17: a triagem demonstrativa é inconclusiva e não contém a palavra ESTÁVEL
  const triage = page.getByTestId('hea-triage');
  await expect(triage).toContainText('TRIAGEM NÃO REALIZADA');
  await expect(triage).not.toContainText('ESTÁVEL');
  await expect(triage.getByTestId('demo-seal').first()).toBeVisible();
  const state = await page.evaluate(() => (window as unknown as { __alloy: { stores: { hea: { getState: () => { result: { triagem?: { estado: string } } | null } } } } }).__alloy.stores.hea.getState().result?.triagem?.estado);
  expect(state).toBe('inconclusiva');

  // (b) selo junto do VALOR (cartão de grandeza), do GRÁFICO e da TABELA
  await expect(page.getByTestId('hea-ds-r').getByTestId('demo-seal')).toBeVisible();
  await expect(page.getByTestId('delta-vec-chart').getByTestId('chart-demo-seal')).toBeVisible();
  // o gráfico G-A não existe no modo demonstrativo (a demo não tem `curva_T`): aparece como
  // indisponível, e também selado — nenhuma curva demonstrativa é desenhada no lugar.
  await expect(page.getByTestId('chart-unavailable').getByTestId('chart-demo-seal')).toBeVisible();
  await expect(page.getByTestId('hea-composition-demo-seal')).toBeVisible();
  await expect(page.getByTestId('hea-criteria-demo-seal')).toBeVisible();
  await expect(page.getByTestId('hea-blocks-demo-seal')).toBeVisible();
  await expect(page.getByTestId('hea-interpretation-demo-seal')).toBeVisible();

  // (c) o selo de demonstração é distinguível do "Ilustrativo": texto e data-seal diferentes
  const seal = page.getByTestId('hea-ds-r').getByTestId('demo-seal');
  await expect(seal).toHaveAttribute('data-seal', 'demo');
  await expect(seal).toContainText('Demonstrativo');
});

test('C2 · fase ambígua: exige escolha explícita, registrada como do usuário (não predição)', async ({ app: page }) => {
  await page.goto('/?demo=1#/hea');
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
  await page.goto('/?demo=1#/hea');
  await page.getByRole('button', { name: /Liga demonstrativa B/ }).click();
  const input = page.locator('#term-input-hea');
  await input.fill('analisar');
  await input.press('Enter');
  await input.fill('cristalab');
  await input.press('Enter');
  await expect(page.getByRole('group', { name: /cita mais de uma estrutura|não cita estrutura/ })).toBeVisible();
  await expect(page).toHaveURL(/#\/hea/);
});

test('C4 · motor HEA real: indisponíveis com motivo, estrutura pelo VEC e transporte sem alteração', async ({ app: page }) => {
  await page.goto('/#/hea');
  await page.getByTestId('analyze-button').click();
  await expect(page.getByTestId('hea-demo-banner')).toHaveCount(0);
  const unavailable = page.getByTestId('hea-unavailable');
  // O motor 2.0.0 deixou de citar o codigo interno de pendencia ("Q-01") no texto e passou a explicar a
  // causa cientifica. A assercao verifica GRANDEZA (chave dH e simbolo ΔH_mix) + CAUSA (entalpias de
  // mistura por par sem fonte cadastrada) e a dependencia de Ω, no lugar do codigo.
  await expect(unavailable).toContainText('dH');
  await expect(unavailable).toContainText('ΔH_mix indisponível');
  await expect(unavailable).toContainText(/entalpias de mistura/);
  await expect(unavailable).toContainText('Ω depende de ΔH_mix');
  // R2-FE-01: os gráficos passaram a usar os campos novos do motor 2.0.0. G-A desenha
  // −T·ΔS_mix (sempre disponível) e diz, com a CAUSA da API, que ΔG_mix não foi desenhado;
  // G-B desenha δ × VEC com os limiares vindos de `criterios` (nenhum fixo no front).
  await expect(page.getByTestId('temperature-chart')).toBeVisible();
  await expect(page.getByTestId('ga-gibbs-unavailable')).toContainText('ΔH_mix');
  await expect(page.getByTestId('delta-vec-chart')).toBeVisible();
  await expect(page.getByTestId('gb-unverified')).toContainText('não verificado');
  // triagem lida de `triagem.estado`, sem a palavra "ESTÁVEL" em lugar nenhum
  await expect(page.getByTestId('hea-triage')).toContainText('inconclusiva');
  await expect(page.getByTestId('result-root')).not.toContainText('ESTÁVEL');
  // critérios empíricos com limiar, fonte e marca de verificação vindos da API
  const criteria = page.getByTestId('hea-criteria');
  await expect(criteria).toContainText('6,60 %');
  await expect(criteria).toContainText('Yang');
  await expect(criteria).toContainText('limiar não verificado na fonte');
  // composição nas duas bases: em massa indisponível com o motivo, nunca zero
  await expect(page.getByTestId('hea-composition-table')).toContainText('% em massa');
  await expect(page.getByTestId('hea-missing-pairs')).toContainText('Co-Cr');
  const before = await heaResult(page);
  expect(JSON.parse(before)).toMatchObject({ nome: 'CoCrFeNi', dH: null, omega: null, estrutura_sugerida: 'CFC' });
  await page.getByTestId('open-in-crystalab').click();
  await expect(page.getByTestId('hea-banner')).toBeVisible();
  const tr = await transfer(page);
  expect(tr).toMatchObject({ code: 'CFC', basis: 'predictor-field', origin: 'engine', frozen: true });
  expect(tr!.result).toBe(before);
});
