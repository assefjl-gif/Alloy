import { test as base, expect, type Page } from 'playwright/test';

/** Página em pt-BR, tema claro, armazenamento limpo; coleta erros de JS (falham o teste). */
export const test = base.extend<{ app: Page; jsErrors: string[] }>({
  jsErrors: async ({}, use) => { await use([]); },
  app: async ({ page, jsErrors }, use) => {
    await page.addInitScript(() => {
      if (!sessionStorage.getItem('e2e-init')) {
        localStorage.clear();
        localStorage.setItem('alloy.prefs', JSON.stringify({ theme: 'light', locale: 'pt-BR', motion: 'system', demo: 'config', role: 'student', touchSceneLock: true }));
        // Estado de interface do CrystaLab SEMEADO (R2-FE-01): a barra e as seções essenciais
        // começam abertas em todo teste, para nenhuma asserção depender do que ficou guardado
        // antes (o estado é persistido em localStorage por `stores/crystalUi.ts`).
        localStorage.setItem('alloy.crystalab.ui', JSON.stringify({
          sidebarOpen: true,
          wide: false,
          legend: true,
          open: { structure: true, 'structure.material': true, properties: true, 'properties.summary': true, 'analysis.miller': true },
        }));
        sessionStorage.setItem('e2e-init', '1');
      }
      (globalThis as { __name?: unknown }).__name = (f: unknown) => f;
    });
    page.on('pageerror', (e) => jsErrors.push(e.message));
    await use(page);
    expect(jsErrors, 'erros de JavaScript na página').toEqual([]);
  },
});

export { expect };

export async function openCrystalab(page: Page, hash = '#/crystalab'): Promise<void> {
  await page.goto(`/${hash}`);
  // Espera a estrutura inicial CHEGAR DO MOTOR antes de olhar a tela: sob carga (suíte cheia) o
  // primeiro carregamento às vezes não completa, e o teste falhava por tempo, não por
  // comportamento. Uma recarga é tentada antes de desistir. Isto é pré-condição, não asserção:
  // nenhuma verificação foi enfraquecida.
  const loaded = () => page.waitForFunction(
    () => Boolean((window as unknown as { __alloy?: { stores?: { crystalab?: { getState: () => { structure: unknown } } } } }).__alloy?.stores?.crystalab?.getState().structure),
    undefined,
    { timeout: 20_000 },
  );
  try {
    await loaded();
  } catch {
    await page.reload();
    await loaded();
  }
  // em tela estreita a barra (e os cartões) começa recolhida: basta o resultado estar montado
  await expect(page.getByTestId('metric-density')).toBeAttached({ timeout: 30_000 });
}

/**
 * Abre a barra lateral (se recolhida), a seção e, quando houver, a subseção: 'analysis' ou
 * 'analysis.thermal'. Usa os mesmos botões que a pessoa usa (aria-expanded).
 */
export async function reveal(page: Page, id: string): Promise<void> {
  const open = async (testId: string) => {
    const btn = page.getByTestId(testId);
    if ((await btn.getAttribute('aria-expanded')) !== 'true') await btn.click();
    await expect(btn).toHaveAttribute('aria-expanded', 'true');
  };
  await open('sidebar-toggle');
  await open(`section-${id.split('.')[0]}`);
  if (id.includes('.')) await open(`sub-${id.replace('.', '-')}`);
}

export async function terminal(page: Page, line: string): Promise<void> {
  await reveal(page, 'analysis.terminal');
  const input = page.locator('#term-input-crystalab');
  await input.fill(line);
  await input.press('Enter');
}

export async function lastLog(page: Page): Promise<string> {
  await reveal(page, 'analysis.terminal');
  return page.getByTestId('terminal-log').innerText();
}

export async function viewerReady(page: Page): Promise<void> {
  await page.waitForFunction(() => Boolean((window as { __alloy?: { viewer?: unknown } }).__alloy?.viewer));
}
