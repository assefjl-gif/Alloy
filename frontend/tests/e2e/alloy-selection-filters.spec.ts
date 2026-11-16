/**
 * Seleção e inspeção de átomo na liga (T-24) e filtros, cortes e isolamento (T-23) — R2-FE-03.
 * Roda contra o BUILD e o MOTOR REAIS. O que se confere:
 *  - clique em átomo da cena de liga seleciona o átomo e o inspetor mostra os campos da API;
 *  - imagem periódica é identificada, aponta para a origem e fica fora da contagem de únicos;
 *  - campo que o motor não confirmou (Wyckoff) aparece como não disponível, nunca como zero;
 *  - propriedade de ELEMENTO PURO fica em bloco separado e rotulado;
 *  - a lista navegável por teclado funciona na liga;
 *  - filtro por elemento (liga) e por tipo de sítio (metal puro) escondem só a EXIBIÇÃO, com a
 *    contagem do motor intacta, e o átomo oculto deixa de ser selecionável;
 *  - a seleção continua funcionando depois de filtrar e de cortar, inclusive para um átomo que o
 *    clique não alcançava antes do corte (requisito duro do cartão).
 */
import { test, expect, openCrystalab, viewerReady, reveal } from './fixtures.ts';
import type { Page } from 'playwright/test';

type Viewer = {
  alloyAtoms: () => string[];
  alloyScreenPosition: (id: string) => { x: number; y: number } | null;
  thermalScene: () => Record<string, number> | null;
  atoms: () => Array<{ key: string; replica: boolean; tipo: string }>;
  hiddenKeys: () => string[];
};
const api = <T,>(page: Page, fn: (v: Viewer) => T) =>
  page.evaluate(`(${fn.toString()})(window.__alloy.viewer)`) as Promise<T>;

const drawnIds = (page: Page) => api(page, (v) => v.alloyAtoms());
const sceneCounts = (page: Page) => api(page, (v) => (v.thermalScene ? v.thermalScene() : null));
const screenPos = (page: Page, id: string) =>
  page.evaluate((atomId) => (window as unknown as { __alloy: { viewer: Viewer } }).__alloy.viewer.alloyScreenPosition(atomId), id);
/** Átomos da célula do metal puro que estão DESENHADOS agora (os escondidos saem da malha). */
const visibleCellAtoms = (page: Page) => api(page, (v) => { const h = new Set(v.hiddenKeys()); return v.atoms().filter((a) => !h.has(a.key)); });

const selectedId = async (page: Page) =>
  (await page.getByTestId('alloy-atom-id').count()) ? (await page.getByTestId('alloy-atom-id').innerText()).trim() : null;

/** pt-BR: "0,2500" → 0.25 (os números da tela vêm formatados no idioma). */
const parseNum = (s: string) => Number(s.replace(/\s/g, '').replace(',', '.'));

/** Coordenadas cartesianas (unidades de a) que o cartão do átomo selecionado mostra. */
async function cardPosition(page: Page): Promise<[number, number, number]> {
  const text = (await page.getByTestId('alloy-atom-card').locator('dd').nth(2).innerText()).replace(/[()]/g, '');
  const p = text.split(';').map((v) => parseNum(v));
  return [p[0] as number, p[1] as number, p[2] as number];
}

/** Move um controle de intervalo pelo TECLADO (interação real) até o valor pedido. */
async function slide(page: Page, selector: string, value: number): Promise<void> {
  const input = page.locator(selector);
  await input.focus();
  const [cur, step] = await input.evaluate((el) => [Number((el as HTMLInputElement).value), Number((el as HTMLInputElement).step)]);
  const key = cur < value ? 'ArrowRight' : 'ArrowLeft';
  const presses = Math.min(200, Math.round(Math.abs(value - cur) / Math.max(step, 1e-6)));
  for (let i = 0; i < presses; i += 1) await input.press(key);
}

async function formAlloy(page: Page, base: string, solute: string, percent: string) {
  await reveal(page, 'composition');
  await page.getByTestId('alloy-base').selectOption(base);
  await page.getByTestId('alloy-solute').selectOption(solute);
  await page.getByTestId('alloy-percent').fill(percent);
  await page.getByTestId('alloy-submit').click();
  await expect(page.getByTestId('alloy-results')).toBeVisible();
}

/** Clica no ponto da tela onde está o átomo `id` e devolve o identificador que ficou selecionado. */
async function clickAtom(page: Page, id: string): Promise<string | null> {
  const p = await screenPos(page, id);
  if (!p) return null;
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(80);
  return selectedId(page);
}

test('T-24 Liga: clique seleciona o átomo, o inspetor mostra os campos da API e a imagem periódica é identificada', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await formAlloy(page, 'Cu', 'Ni', '30');
  await reveal(page, 'selection');

  const inspector = page.getByTestId('alloy-atom-inspector');
  await expect(inspector).toBeVisible();
  await expect(inspector).toContainText('Clique em um átomo da liga');   // sem seleção, nada em branco

  // contagem de EXIBIÇÃO: separa únicos de imagens periódicas e diz que é de exibição
  const listTitle = page.getByTestId('alloy-atom-list-title');
  await expect(listTitle).toContainText('contagem de exibição');
  await expect(listTitle).toContainText('32 únicos');
  await expect(listTitle).toContainText('31 imagens periódicas');
  // ao lado, a contagem CIENTÍFICA do motor, que não depende do filtro
  await expect(page.getByTestId('alloy-atom-engine-counts')).toContainText('32 átomos únicos');
  await expect(page.getByTestId('alloy-atom-engine-counts')).toContainText('63 esferas desenhadas');

  // clique na cena: o átomo clicado é o átomo selecionado (identidade do motor)
  const ids = await drawnIds(page);
  expect(ids.length).toBe(63);
  const first = ids[0] as string;
  expect(await clickAtom(page, first)).toBe(first);

  const card = page.getByTestId('alloy-atom-card');
  for (const label of ['Elemento', 'Identificador do motor', 'Posição cartesiana (unidades de a)', 'Posição cartesiana (nm)',
    'Coordenadas fracionárias (supercélula)', 'Coordenadas fracionárias (na célula)', 'Célula da supercélula', 'Fase',
    'Sítio cristalográfico', 'Número de coordenação do sítio', 'Ocupação']) {
    await expect(card).toContainText(label);
  }
  await expect(page.getByTestId('alloy-atom-site')).not.toBeEmpty();
  await expect(page.getByTestId('alloy-atom-occupancy')).not.toBeEmpty();
  // Wyckoff não foi conferido em fonte pelo motor: aparece como não disponível, sem invenção
  await expect(page.getByTestId('alloy-atom-wyckoff')).toContainText('não disponível');
  // bloco SEPARADO do elemento puro, rotulado como dado tabelado do elemento
  const pure = page.getByTestId('alloy-atom-pure');
  await expect(pure).toContainText('ELEMENTO PURO');
  await expect(pure).toContainText('NÃO são propriedades calculadas deste átomo');
  await expect(pure).toContainText('g/mol');

  // navegação por teclado na lista da liga
  const list = page.getByTestId('alloy-atom-list');
  await list.focus();
  await list.press('Home');
  const home = await selectedId(page);
  expect(home).not.toBeNull();
  await list.press('ArrowDown');
  const next = await selectedId(page);
  expect(next).not.toBe(home);
  await list.press('ArrowUp');
  expect(await selectedId(page)).toBe(home);
  await list.press('End');
  expect(await selectedId(page)).not.toBe(home);
  await list.press('Escape');
  expect(await selectedId(page)).toBeNull();

  // imagem periódica: identificada na lista e no cartão, com ligação para o átomo de origem
  const imageOpt = list.locator('.atom-opt.is-replica').first();
  await expect(imageOpt).toContainText('imagem');
  await imageOpt.click();
  const imageId = await selectedId(page);
  await expect(page.getByTestId('alloy-atom-image')).toContainText('réplica de fronteira do átomo');
  await expect(card).toContainText('Não entra em contagem, composição nem legenda');
  await page.getByTestId('alloy-atom-source').click();
  const sourceId = await selectedId(page);
  expect(sourceId).not.toBe(imageId);
  expect(imageId).toContain(sourceId as string);                 // o id da imagem deriva da origem
  await expect(page.getByTestId('alloy-atom-image')).toHaveText('não');  // a origem não é imagem
});

test('T-23 Liga: filtro por elemento é só exibição; átomo oculto não é selecionável e o visível continua sendo', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await formAlloy(page, 'Cu', 'Ni', '30');

  // um átomo de Ni, identificado pela própria lista do inspetor (o id é do motor, opaco)
  await reveal(page, 'selection');
  const niOpt = page.getByTestId('alloy-atom-list').locator('.atom-opt', { hasText: 'Ni ·' }).first();
  await niOpt.click();
  const niId = (await selectedId(page)) as string;
  expect(niId).not.toBeNull();
  expect(await clickAtom(page, niId)).toBe(niId);                // antes do filtro: selecionável

  await reveal(page, 'appearance.filters');
  const panel = page.getByTestId('filter-panel');
  await expect(panel).toContainText('Filtrar e cortar muda só o que aparece na cena');
  await expect(page.getByTestId('filter-clear')).toBeDisabled();
  const engineCounts = await page.getByTestId('alloy-counts').innerText();
  expect(Object.keys((await sceneCounts(page)) ?? {}).sort()).toEqual(['Cu', 'Ni']);

  // ocultar Ni: a cena perde as esferas de Ni; a contagem do MOTOR não muda
  await page.getByTestId('filter-toggle-Ni').click();
  await expect.poll(async () => Object.keys((await sceneCounts(page)) ?? {})).toEqual(['Cu']);
  await expect(page.getByTestId('filter-row-Ni')).toContainText('oculto');
  expect(await page.getByTestId('alloy-counts').innerText()).toBe(engineCounts);
  await expect(page.getByTestId('filter-counts')).toContainText('contagem de exibição');
  await expect(page.getByTestId('filter-counts')).toContainText('não muda com o filtro');
  await expect(page.getByTestId('legend-filter')).toContainText('Filtro de exibição ativo');

  // átomo oculto NÃO é selecionável (saiu da malha) e a tela diz que ele está escondido
  expect(await drawnIds(page)).not.toContain(niId);
  expect(await screenPos(page, niId)).toBeNull();
  await reveal(page, 'selection');
  await expect(page.getByTestId('alloy-atom-card')).toContainText('escondido pelo filtro de exibição');
  await expect(page.getByTestId('alloy-atom-list').locator('.atom-opt', { hasText: 'Ni ·' })).toHaveCount(0);

  // isolar Ni (mostra só Ni): o Ni volta, o Cu sai, e o átomo de Ni volta a ser selecionável
  await reveal(page, 'appearance.filters');
  await page.getByTestId('filter-isolate-Ni').click();
  await expect.poll(async () => Object.keys((await sceneCounts(page)) ?? {})).toEqual(['Ni']);
  await reveal(page, 'selection');
  expect(await clickAtom(page, niId)).toBe(niId);
  await expect(page.getByTestId('alloy-atom-card')).toContainText('Ni');

  // limpar devolve a cena completa
  await reveal(page, 'appearance.filters');
  await page.getByTestId('filter-clear').click();
  await expect.poll(async () => Object.keys((await sceneCounts(page)) ?? {}).sort()).toEqual(['Cu', 'Ni']);
  await expect(page.getByTestId('filter-clear')).toBeDisabled();
  await expect(page.getByTestId('legend-filter')).toHaveCount(0);
});

test('T-23 Metal puro: isolar por tipo de sítio esconde o resto, encurta a lista do teclado e volta ao limpar', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await reveal(page, 'appearance.filters');
  await expect(page.getByTestId('filter-panel')).toContainText('O filtro por elemento vale para a liga');

  const all = await visibleCellAtoms(page);
  const kinds = [...new Set(all.map((a) => a.tipo))];
  expect(kinds.length).toBeGreaterThan(1);
  const keep = kinds[0] as string;

  await page.getByTestId(`filter-isolate-${keep}`).click();
  await expect.poll(async () => [...new Set((await visibleCellAtoms(page)).map((a) => a.tipo))]).toEqual([keep]);
  const visibleCount = (await visibleCellAtoms(page)).length;
  expect(visibleCount).toBeLessThan(all.length);

  // a lista navegável por teclado também encurta (átomo escondido não é alcançável) e avisa
  await reveal(page, 'selection');
  await expect(page.getByTestId('atom-list-filtered')).toBeVisible();
  await expect(page.locator('#atom-list-title')).toContainText(String(visibleCount));
  await expect(page.getByTestId('atom-inspector').locator('.atom-opt')).toHaveCount(visibleCount);

  await reveal(page, 'appearance.filters');
  await page.getByTestId('filter-clear').click();
  await expect.poll(async () => (await visibleCellAtoms(page)).length).toBe(all.length);
});

test('T-23 requisito duro: o corte geométrico revela um átomo que o clique não alcançava, e ele fica selecionável', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await formAlloy(page, 'Cu', 'Ni', '30');
  await reveal(page, 'selection');
  const ids = await drawnIds(page);

  // 1) um átomo DESENHADO que o clique não alcança, porque outro está na frente dele. Os
  //    candidatos saem de uma leitura só: os pares que mais se sobrepõem na tela, em ordem.
  const points = await page.evaluate(() => {
    const v = (window as unknown as { __alloy: { viewer: Viewer } }).__alloy.viewer;
    return v.alloyAtoms().map((id) => ({ id, p: v.alloyScreenPosition(id) })).filter((e) => e.p) as Array<{ id: string; p: { x: number; y: number } }>;
  });
  const pairs: Array<{ d: number; ids: [string, string] }> = [];
  for (let i = 0; i < points.length; i += 1) {
    for (let j = i + 1; j < points.length; j += 1) {
      const a = points[i] as { id: string; p: { x: number; y: number } };
      const b = points[j] as { id: string; p: { x: number; y: number } };
      const d = Math.hypot(a.p.x - b.p.x, a.p.y - b.p.y);
      if (d < 30) pairs.push({ d, ids: [a.id, b.id] });
    }
  }
  pairs.sort((x, y) => x.d - y.d);
  expect(pairs.length, 'há átomos que se sobrepõem na tela').toBeGreaterThan(0);

  let target: { id: string; pos: [number, number, number]; blocker: [number, number, number]; inFront: string } | null = null;
  for (const candidate of pairs.slice(0, 4).flatMap((pair) => pair.ids)) {
    const got = await clickAtom(page, candidate);
    if (!got || got === candidate) continue;                    // este é alcançável: não serve
    const blocker = await cardPosition(page);                   // o que está na frente, já selecionado
    await page.locator(`#alloy-atom-opt-${candidate.replace(/[^\w-]/g, '_')}`).click();
    if ((await selectedId(page)) !== candidate) continue;
    const pos = await cardPosition(page);
    if (Math.max(...[0, 1, 2].map((i) => Math.abs((pos[i] as number) - (blocker[i] as number)))) < 0.1) continue;
    target = { id: candidate, pos, blocker, inFront: got };
    break;
  }
  expect(target, 'há átomo desenhado que o clique não alcança (oclusão)').not.toBeNull();
  const t24 = target as NonNullable<typeof target>;
  // o clique no ponto dele devolve o átomo da frente: hoje ele é inalcançável pelo clique
  expect(await clickAtom(page, t24.id)).toBe(t24.inFront);

  // 2) corte no eixo em que ele e o átomo da frente mais diferem, mantendo o lado dele
  const diffs = [0, 1, 2].map((i) => Math.abs((t24.pos[i] as number) - (t24.blocker[i] as number)));
  const axis = diffs.indexOf(Math.max(...diffs));
  const mode = (t24.pos[axis] as number) < (t24.blocker[axis] as number) ? 'abaixo do plano' : 'acima do plano';
  const middle = ((t24.pos[axis] as number) + (t24.blocker[axis] as number)) / 2;

  await reveal(page, 'appearance.filters');
  await page.getByLabel('Cortar a cena').check();
  await expect(page.getByTestId('filter-cut-controls')).toBeVisible();
  await page.getByTestId('filter-cut-axis').selectOption(String(axis));
  await page.getByRole('radio', { name: mode }).check();
  await slide(page, '#filter-cut-position', middle);

  // 3) o átomo da frente saiu da cena; o nosso continua desenhado
  await expect.poll(async () => (await drawnIds(page)).includes(t24.id)).toBe(true);
  await expect.poll(async () => (await drawnIds(page)).length).toBeLessThan(ids.length);

  // 4) limpa a seleção e CLICA no mesmo ponto: agora o átomo revelado é o selecionado
  await reveal(page, 'selection');
  await page.getByTestId('alloy-atom-card').getByRole('button', { name: 'Limpar seleção' }).click();
  expect(await selectedId(page)).toBeNull();
  expect(await clickAtom(page, t24.id)).toBe(t24.id);

  // 5) a contagem CIENTÍFICA do motor continua a mesma com o corte ativo (cortar é só exibição)
  await expect(page.getByTestId('alloy-counts')).toContainText('32 átomos únicos');
  await expect(page.getByTestId('alloy-atom-engine-counts')).toContainText('63 esferas desenhadas');
});
