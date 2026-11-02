/**
 * Testes de fluxo (Etapa 8). Rodam contra o build de produção (dist/) servido por scripts/serve.mjs,
 * com o MOTOR REAL do CrystaLab (legacy/crystalab_modulo1.py) e, para exportação CIF/XYZ, com o
 * servidor de contrato /v1 (engine-stub/). O motor HEA não existe neste repositório (D-01): o
 * módulo HEA roda em modo demonstrativo rotulado.
 *
 * Pré-requisito: `npm run build`. Navegador: Chromium em /opt/pw-browsers.
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
    { command: 'python3 legacy/crystalab_modulo1.py --port 8010', url: 'http://127.0.0.1:8010/api/estruturas', reuseExistingServer: true, timeout: 30_000 },
    { command: 'python3 engine-stub/v1_contract_server.py --port 8011', url: 'http://127.0.0.1:8011/health', reuseExistingServer: true, timeout: 30_000 },
    { command: 'node scripts/serve.mjs', url: 'http://127.0.0.1:5173/', reuseExistingServer: true, timeout: 30_000, env: { PORT: '5173', CRYSTALAB_ENGINE: 'http://127.0.0.1:8010' } },
    { command: 'node scripts/serve.mjs', url: 'http://127.0.0.1:5174/', reuseExistingServer: true, timeout: 30_000, env: { PORT: '5174', CRYSTALAB_ENGINE: 'http://127.0.0.1:8011' } },
  ],
});
