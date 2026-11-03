/**
 * Testes de fluxo. Rodam contra o build de produção (dist/) servido por scripts/serve.mjs, com o
 * BACKEND REAL da plataforma (backend/, FastAPI) atrás do proxy /api — o mesmo arranjo do Caddy
 * em produção (ADR-010). O módulo HEA usa o serviço /api/v1/hea quando disponível.
 *
 * Pré-requisitos: `npm run build`; venv do backend (../.venv) ou ALLOY_PYTHON; navegador
 * Chromium do Playwright (`npx playwright install chromium`).
 */
import { defineConfig, devices } from 'playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  outputDir: 'reports/e2e-artifacts',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['json', { outputFile: 'reports/e2e-results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    locale: 'pt-BR',
    timezoneId: 'America/Fortaleza',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    viewport: { width: 1366, height: 900 },
    launchOptions: { args: ['--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1366, height: 900 }, locale: 'pt-BR' } }],
  webServer: [
    { command: 'node scripts/backend.mjs', url: 'http://127.0.0.1:8010/health', reuseExistingServer: true, timeout: 60_000 },
    { command: 'node scripts/serve.mjs', url: 'http://127.0.0.1:5173/', reuseExistingServer: true, timeout: 30_000, env: { PORT: '5173', ALLOY_API: 'http://127.0.0.1:8010' } },
  ],
});
