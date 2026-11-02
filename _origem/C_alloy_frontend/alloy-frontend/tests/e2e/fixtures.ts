import { test as base, expect, type Page } from 'playwright/test';

/** Página em pt-BR, tema claro, armazenamento limpo; coleta erros de JS (falham o teste). */
export const test = base.extend<{ app: Page; jsErrors: string[] }>({
  jsErrors: async ({}, use) => { await use([]); },
  app: async ({ page, jsErrors }, use) => {
    await page.addInitScript(() => {
      if (!sessionStorage.getItem('e2e-init')) {
        localStorage.clear();
        localStorage.setItem('alloy.prefs', JSON.stringify({ theme: 'light', locale: 'pt-BR', motion: 'system', demo: 'config', role: 'student', touchSceneLock: true }));
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
  await expect(page.getByTestId('metric-density')).toBeVisible();
}

export async function terminal(page: Page, line: string): Promise<void> {
  const input = page.locator('#term-input-crystalab');
  await input.fill(line);
  await input.press('Enter');
}

export async function lastLog(page: Page): Promise<string> {
  return page.getByTestId('terminal-log').innerText();
}

export async function viewerReady(page: Page): Promise<void> {
  await page.waitForFunction(() => Boolean((window as { __alloy?: { viewer?: unknown } }).__alloy?.viewer));
}
