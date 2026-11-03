/**
 * Gate da Etapa 4 — Terminal, paleta e modo guiado: Fluxo B sem digitar comandos, ambiguidade
 * com escolha explícita, erros que dizem como corrigir, autocompletar, OverlayManager, descarte
 * de respostas obsoletas, KaTeX, workspaces e exportação com motivos de indisponibilidade.
 * (Fluxo A sem digitar: flow-a-density.spec.ts; equivalência e desfazer/refazer: flow-b-miller.spec.ts
 * e tests/unit/commands.test.ts.)
 */
import { readFileSync } from 'node:fs';
import { test, expect, openCrystalab, terminal } from './fixtures.ts';
import type { Page } from 'playwright/test';

type Item = { kind: string; label: string; visible: boolean; color: string; data: unknown };
const overlays = (page: Page) => page.evaluate(() => (window as unknown as { __alloy: { stores: { overlays: { getState: () => { items: Item[] } } } } }).__alloy.stores.overlays.getState().items.map((i) => ({ kind: i.kind, label: i.label, visible: i.visible, color: i.color, data: i.data })));

test('Fluxo B sem digitar: bloco HC → formulário Miller-Bravais → compartilhar → mesma cena', async ({ app: page, browser }) => {
  await openCrystalab(page);
  await page.getByTestId('block-list').getByRole('button', { name: /Mg · Magnésio/ }).click();
  await expect(page.getByTestId('metric-structure')).toContainText('HC');
  const guided = page.getByTestId('guided-mode');
  for (const [label, v] of [['h', '1'], ['k', '0'], ['i', '-1'], ['l', '1']] as const) await guided.getByLabel(label, { exact: true }).fill(v);
  await expect(guided.getByTestId('equivalent-command').last()).toHaveText('plano 1 0 -1 1');
  await guided.getByTestId('guided-miller').click();
  await expect.poll(async () => (await overlays(page)).length).toBe(1);
  await page.getByTestId('share').click();
  await expect.poll(() => new URL(page.url()).hash).toContain('?s=v1.');
  const before = await overlays(page);
  const ctx = await browser.newContext({ locale: 'pt-BR' });
  const other = await ctx.newPage();
  await other.goto(page.url());
  await expect(other.getByTestId('metric-structure')).toContainText('HC');
  await expect.poll(async () => (await overlays(other)).map((o) => o.data)).toEqual(before.map((o) => o.data));
  await ctx.close();
});

test('4.2 · ambiguidade "a=" exige escolha; a escolha executa o comando corrigido', async ({ app: page }) => {
  await openCrystalab(page);
  await terminal(page, 'estrutura CFC r=0.128 a=63.55');
  const group = page.getByRole('group', { name: /é ambíguo/ });
  await expect(group).toBeVisible();
  await group.getByRole('button', { name: /A = 63.55 g\/mol/ }).click();
  await expect(page.getByTestId('metric-structure')).toContainText('CFC');
  await expect(page.getByTestId('terminal-log')).toContainText('> estrutura CFC r=0.128 A=63.55');
});

test('4.4/4.5 · autocompletar, erros com dica de correção e estado de execução', async ({ app: page }) => {
  await openCrystalab(page);
  const input = page.locator('#term-input-crystalab');
  await input.fill('pla');
  await expect(page.getByRole('listbox', { name: 'Sugestões' })).toContainText('plano');
  await terminal(page, 'plano 1 1');
  const log = page.getByTestId('terminal-log');
  await expect(log).toContainText('São necessários 3 ou 4 índices');
  await expect(log).toContainText('Exemplo: plano 1 1 1');
  await terminal(page, 'voar');
  await expect(log).toContainText('Comando desconhecido');
  await expect(log).toContainText('Digite “ajuda”');
  await terminal(page, 'ajuda plano');
  await expect(log).toContainText('plano <h k l> | <h k i l>');
});

test('4.9 · OverlayManager: ocultar, cor acessível, seleção e remoção individual', async ({ app: page }) => {
  await openCrystalab(page);
  await terminal(page, 'plano 1 1 0');
  await terminal(page, 'direcao 1 1 1');
  await expect.poll(async () => (await overlays(page)).length).toBe(2);
  await page.getByRole('tab', { name: /Camadas/ }).click();
  const mgr = page.getByTestId('overlay-manager');
  await mgr.getByRole('button', { name: /Ocultar Plano/ }).click();
  await expect.poll(async () => (await overlays(page))[0]!.visible).toBe(false);
  await mgr.getByRole('radio', { name: 'Cor 3' }).first().check();
  await expect.poll(async () => (await overlays(page))[0]!.color).toBe('#009E73');
  await mgr.getByRole('button', { name: /Remover Direção/ }).click();
  await expect.poll(async () => (await overlays(page)).map((o) => o.kind)).toEqual(['plane']);
  await page.getByTestId('undo').click();
  await expect.poll(async () => (await overlays(page)).length).toBe(2);
});

test('4.11 · troca rápida de material: a resposta antiga é descartada e não sobrescreve a cena', async ({ app: page }) => {
  await openCrystalab(page);
  await page.evaluate(async () => {
    const input = document.getElementById('term-input-crystalab') as HTMLInputElement;
    const send = (v: string) => { const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!; set.call(input, v); input.dispatchEvent(new Event('input', { bubbles: true })); input.form!.requestSubmit(); };
    send('usar W'); send('usar Cu');
  });
  await expect(page.locator('#resultTitle')).toContainText('Cobre');
  await page.waitForTimeout(1200);
  await expect(page.locator('#resultTitle')).toContainText('Cobre');
  await expect(page.getByTestId('metric-structure')).toContainText('CFC');
});

test('4.12 · densidade com KaTeX: fórmula simbólica, variáveis, substituição e resultado do motor', async ({ app: page }) => {
  await openCrystalab(page);
  await page.getByRole('button', { name: 'Calcular densidade' }).first().click();
  const panel = page.getByTestId('density-panel');
  await expect(panel.locator('.katex').first()).toBeVisible();
  await expect(panel).toContainText('número de Avogadro');
  await expect(panel).toContainText('Substituição');
  await expect(panel).toContainText('Resultado do motor');
  await expect(panel).toContainText('todos os números vêm do motor');
});

test('4.14 · workspaces locais: salvar, reabrir, exportar e importar JSON', async ({ app: page }) => {
  await openCrystalab(page);
  await terminal(page, 'usar Cu');
  await terminal(page, 'plano 1 1 1');
  await terminal(page, 'salvar aula-3');
  await expect(page.getByTestId('terminal-log')).toContainText('Workspace “aula-3” salvo neste navegador');
  await terminal(page, 'usar Fe');
  await expect(page.locator('#resultTitle')).toContainText('Ferro');
  await page.getByRole('tab', { name: 'Workspaces' }).click();
  const ws = page.getByTestId('workspaces');
  await expect(ws).toContainText('neste navegador');
  const [download] = await Promise.all([page.waitForEvent('download'), ws.getByRole('button', { name: 'Exportar todos' }).click()]);
  const json = readFileSync((await download.path())!, 'utf8');
  expect(json).toContain('aula-3');
  await ws.getByRole('button', { name: 'Abrir' }).first().click();
  await expect(page.locator('#resultTitle')).toContainText('Cobre');
  await expect.poll(async () => (await overlays(page)).map((o) => o.label)).toEqual(['(1 1 1)']);
  await ws.getByRole('button', { name: /Excluir aula-3/ }).click();
  await expect(ws).toContainText('Nenhum workspace salvo');
  await ws.locator('input[type="file"]').setInputFiles({ name: 'ws.json', mimeType: 'application/json', buffer: Buffer.from(json) });
  await expect(ws).toContainText('aula-3');
});

test('4.15 · exportação: PNG e JSON locais; CIF/XYZ desabilitados com motivo no motor v1.0', async ({ app: page }) => {
  await openCrystalab(page);
  await page.getByRole('button', { name: 'Exportar' }).click();
  const cif = page.getByRole('menuitem', { name: /CIF/ });
  await expect(cif).toHaveAttribute('aria-disabled', 'true');
  await expect(cif).toContainText('API /v1');
  const [png] = await Promise.all([page.waitForEvent('download'), page.getByRole('menuitem', { name: /PNG/ }).click()]);
  expect(png.suggestedFilename()).toMatch(/\.png$/);
  const head = readFileSync((await png.path())!).subarray(0, 4).toString('hex');
  expect(head).toBe('89504e47');
  await terminal(page, 'exportar json');
  await expect(page.getByTestId('terminal-log')).toContainText('Arquivo gerado');
});

test('4.5/4.11 · operação lenta mostra carregamento e pode ser cancelada; a cena anterior fica intacta', async ({ app: page }) => {
  await openCrystalab(page);
  // atraso de rede real (a resposta continua sendo a do motor; nada é simulado)
  await page.route('**/api/v1/crystallography/cells', async (route) => { await new Promise((r) => setTimeout(r, 2500)); await route.continue(); });
  await terminal(page, 'usar Au');
  await expect(page.getByTestId('terminal-cancel')).toBeVisible();
  await expect(page.getByTestId('result-root')).toHaveAttribute('aria-busy', 'true');
  await page.getByTestId('terminal-cancel').click();
  await expect(page.getByTestId('terminal-log')).toContainText('cancelad');
  await page.waitForTimeout(3000);
  await expect(page.locator('#resultTitle')).toContainText('Ferro');
});
