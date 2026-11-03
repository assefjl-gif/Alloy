/**
 * Gate da Etapa 3 — Viewer 3D científico: estruturas carregam com dados do motor; seleção
 * mostra dados válidos; réplicas não alteram contagens; cena parada não consome GPU;
 * recursos liberados ao sair; métricas registradas (perf-metrics.spec.ts).
 */
import { test, expect, openCrystalab, terminal, viewerReady } from './fixtures.ts';
import type { Page } from 'playwright/test';

type V = { atoms: () => Array<{ key: string; replica: boolean; tipo: string }>; stats: { renders: number }; camera: () => unknown; screenPosition: (k: string) => { x: number; y: number } | null };
const viewer = <T>(page: Page, fn: (v: V) => T) => page.evaluate(fn as never, undefined) as Promise<T>;
const engine = async (request: import('playwright/test').APIRequestContext, nome: string) => (await (await request.post('http://127.0.0.1:8010/api/v1/crystallography/cells', { data: { nome } })).json()).result;

for (const [nome, code] of [['Po', 'CS'], ['Fe', 'CCC'], ['Cu', 'CFC'], ['Mg', 'HC']] as const) {
  test(`3.5 · ${code} (${nome}): átomos desenhados = átomos enviados pelo motor`, async ({ app: page, request }) => {
    const r = await engine(request, nome);
    await openCrystalab(page);
    await viewerReady(page);
    await terminal(page, `usar ${nome}`);
    await expect(page.getByTestId('metric-structure')).toContainText(code);
    await expect.poll(() => page.evaluate(() => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.atoms().length)).toBe(r.atomos.length);
    const drawn = await page.evaluate(() => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.atoms().map((a) => a.tipo).sort());
    expect(drawn).toEqual((r.atomos as Array<{ tipo: string }>).map((a) => a.tipo).sort());
    await expect(page.getByTestId('metric-n')).toContainText(String(r.n));
  });
}

test('3.7/3.8 · seleção por clique mostra posição e contribuição do motor; Esc limpa', async ({ app: page, request }) => {
  const fe = await engine(request, 'Fe');
  await openCrystalab(page);
  await viewerReady(page);
  const center = (fe.atomos as Array<{ tipo: string }>).findIndex((a) => a.tipo === 'centro');
  const pos = await page.evaluate((k) => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.screenPosition(k), `${center}@0,0,0`);
  await page.mouse.click(pos!.x, pos!.y);
  await page.getByRole('tab', { name: 'Átomo' }).click();
  const card = page.getByTestId('atom-inspector');
  await expect(card).toContainText(`Átomo ${center + 1}`);
  await expect(card).toContainText('centro do corpo');
  await expect(card).toContainText('0,5; 0,5; 0,5');
  await expect(card).toContainText(fe.atomos[center].fracao_txt);
  await page.getByTestId('viewer-stage').focus();
  await page.keyboard.press('Escape');
  await expect(card).toContainText('Clique em um átomo');
});

test('3.9/3.10 · supercélula: réplicas marcadas e excluídas das contagens; volta à célula unitária', async ({ app: page, request }) => {
  const cu = await engine(request, 'Cu');
  await openCrystalab(page);
  await terminal(page, 'usar Cu');
  await expect(page.getByTestId('metric-structure')).toContainText('CFC');
  await terminal(page, 'supercelula 2');
  await expect.poll(() => page.evaluate(() => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.atoms().length)).toBe(63);
  const own = await page.evaluate(() => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.atoms().filter((a) => !a.replica).length);
  expect(own).toBe(cu.atomos.length);
  await expect(page.getByTestId('metric-n')).toContainText(String(cu.n));
  await expect(page.getByTestId('terminal-log')).toContainText('réplicas são gráficas');
  await terminal(page, 'supercelula 4');
  await expect(page.getByTestId('terminal-log')).toContainText('mais lenta');
  await page.locator('#supercell-select').selectOption('1x1x1');
  await expect.poll(() => page.evaluate(() => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.atoms().length)).toBe(cu.atomos.length);
});

test('3.2 · cena parada não renderiza; interação renderiza; recursos liberados ao sair do módulo', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await page.waitForTimeout(800);
  const r0 = await viewer(page, () => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.stats.renders);
  await page.waitForTimeout(1500);
  const r1 = await viewer(page, () => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.stats.renders);
  expect(r1 - r0, 'quadros desenhados com a cena parada').toBe(0);
  await page.getByTestId('viewer-stage').focus();
  await page.keyboard.press('ArrowLeft');
  await expect.poll(() => viewer(page, () => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.stats.renders)).toBeGreaterThan(r1);
  await page.getByRole('navigation', { name: 'Módulos' }).getByRole('link', { name: 'HEA Virtual Lab', exact: true }).click();
  await expect(page.locator('[data-testid="viewer-stage"] canvas')).toHaveCount(0);
  expect(await page.evaluate(() => Boolean((window as { __alloy?: { viewer?: unknown } }).__alloy?.viewer))).toBe(false);
});

test('3.4 · câmera serializável: o estado salvo na URL reabre o mesmo ponto de vista', async ({ app: page, browser }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await page.getByTestId('viewer-stage').focus();
  for (let i = 0; i < 4; i += 1) await page.keyboard.press('ArrowLeft');
  await page.waitForTimeout(1200);
  const cam = await page.evaluate(() => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.camera() as { position: number[] });
  await expect.poll(() => new URL(page.url()).hash).toContain('?s=v1.');
  const ctx = await browser.newContext({ locale: 'pt-BR' });
  const other = await ctx.newPage();
  await other.goto(page.url());
  await other.waitForFunction(() => Boolean((window as { __alloy?: { viewer?: unknown } }).__alloy?.viewer));
  await expect.poll(async () => {
    const c = await other.evaluate(() => (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer.camera() as { position: number[] });
    return c.position.map((v, i) => Math.abs(v - cam.position[i]!) < 0.01).every(Boolean);
  }).toBe(true);
  await ctx.close();
});

test('3.13 · medição por clique: distância com unidade, mantida na lista; medição inválida explicada', async ({ app: page }) => {
  await openCrystalab(page);
  await viewerReady(page);
  await terminal(page, 'medir distancia');
  await expect(page.locator('.viewer-tool-banner')).toContainText('0/2');
  // átomos cujo ponto na tela está realmente sobre o canvas (não sob a faixa da ferramenta)
  const points = await page.evaluate(() => {
    const v = (window as unknown as { __alloy: { viewer: V } }).__alloy.viewer;
    return v.atoms().map((a) => v.screenPosition(a.key)).filter((p): p is { x: number; y: number } => Boolean(p && document.elementFromPoint(p.x, p.y)?.tagName === 'CANVAS'));
  });
  expect(points.length).toBeGreaterThan(1);
  for (const p of points.slice(0, 2)) { await page.mouse.click(p.x, p.y); await page.waitForTimeout(150); }
  await expect(page.getByTestId('terminal-log')).toContainText(/Distância .* nm entre os átomos/);
  await page.getByRole('tab', { name: 'Medir' }).click();
  await expect(page.getByTestId('measure-panel')).toContainText('nm');
  await terminal(page, 'medir distancia 1 1');
  await expect(page.getByTestId('terminal-log')).toContainText('Escolha átomos diferentes');
});

test('3.14/3.17 · empilhamento: passo a passo para frente e para trás, com texto explicativo', async ({ app: page }) => {
  await openCrystalab(page);
  await terminal(page, 'animacao empilhamento abcabc');
  const panel = page.getByTestId('animations-panel');
  await expect(panel).toContainText('O que muda');
  await expect(panel).toContainText('O que permanece');
  await expect(panel).toContainText('O que observar');
  await panel.getByRole('button', { name: 'Próximo passo' }).click();
  await panel.getByRole('button', { name: 'Próximo passo' }).click();
  await expect(panel).toContainText('A · B · C');
  await panel.getByRole('button', { name: 'Passo anterior' }).click();
  await expect(panel).not.toContainText('A · B · C');
  await expect(page.getByTestId('viewer-stage').getByTestId('demo-seal')).toBeVisible();
});
