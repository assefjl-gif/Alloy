/**
 * Metas medidas (Etapa 8.2): FPS do viewer e latência de seleção na supercélula CFC 3×3×3.
 * O teste REGISTRA as medições em reports/metrics.json com o equipamento real; ele só falha se
 * a medição não puder ser feita. Atingir ou não a meta é declarado no relatório a partir destes
 * números — nunca presumido (neste contêiner o WebGL é por software, SwiftShader).
 */
import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'node:fs';
import os from 'node:os';
import { test, expect, openCrystalab, terminal, viewerReady } from './fixtures.ts';

const median = (xs: number[]) => { const s = [...xs].sort((a, b) => a - b); return s[Math.floor(s.length / 2)]!; };

test('viewer: FPS e latência de seleção — CFC 3×3×3', async ({ app: page, browserName, browser }) => {
  await openCrystalab(page);
  await terminal(page, 'usar Cu');
  await expect(page.getByTestId('metric-structure')).toContainText('CFC');
  await terminal(page, 'supercelula 3');
  await viewerReady(page);
  await page.waitForTimeout(800);

  const info = await page.evaluate(() => {
    const v = (window as unknown as { __alloy: { viewer: { atoms: () => Array<{ key: string; replica: boolean }>; stats: Record<string, number> } } }).__alloy.viewer;
    const gl = document.createElement('canvas').getContext('webgl2');
    const ext = gl?.getExtension('WEBGL_debug_renderer_info');
    return { atoms: v.atoms().length, renderer: ext && gl ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : 'desconhecido', instances: v.stats.instances };
  });
  expect(info.atoms).toBeGreaterThan(100);

  const bench = await page.evaluate(() => (window as unknown as { __alloy: { viewer: { benchmark: (ms: number) => Promise<{ fps: number; frames: number; ms: number }> } } }).__alloy.viewer.benchmark(4000));
  expect(bench.frames).toBeGreaterThan(0);
  await page.waitForTimeout(500);

  // seleção: clique real (pointerdown/up) sobre átomos não-réplica visíveis
  const keys = await page.evaluate(() => (window as unknown as { __alloy: { viewer: { atoms: () => Array<{ key: string; replica: boolean }> } } }).__alloy.viewer.atoms().filter((a) => !a.replica).map((a) => a.key));
  const work: number[] = []; const toFrame: number[] = []; const pick: number[] = [];
  const box = (await page.getByTestId('viewer-stage').boundingBox())!;
  for (let i = 0; i < 15; i += 1) {
    const key = keys[i % keys.length]!;
    const pos = await page.evaluate((k) => (window as unknown as { __alloy: { viewer: { screenPosition: (k: string) => { x: number; y: number } | null } } }).__alloy.viewer.screenPosition(k), key);
    if (!pos || pos.x < box.x || pos.y < box.y || pos.x > box.x + box.width || pos.y > box.y + box.height) continue;
    await page.mouse.click(pos.x, pos.y);
    await page.waitForTimeout(120);
    const s = await page.evaluate(() => ({ ...(window as unknown as { __alloy: { viewer: { stats: Record<string, number> } } }).__alloy.viewer.stats }));
    pick.push(s.lastPickMs!); work.push(s.lastSelectWorkMs!); toFrame.push(s.lastSelectToFrameMs!);
  }
  expect(work.length).toBeGreaterThan(3);
  const sel = await page.evaluate(() => (window as unknown as { __alloy: { stores: { viewer: { getState: () => { selection: unknown } } } } }).__alloy.stores.viewer.getState().selection);
  expect(sel).not.toBeNull();

  const metrics = {
    measuredAt: new Date().toISOString(),
    environment: {
      cpu: os.cpus()[0]?.model ?? 'desconhecido', cores: os.cpus().length, memoryGB: Math.round(os.totalmem() / 2 ** 30),
      browser: `${browserName} ${browser.version()} (headless)`, webglRenderer: info.renderer, viewport: '1366×900',
      note: 'Contêiner de CI sem GPU: WebGL por software (SwiftShader). Não representa o notebook intermediário do plano (D-20).',
    },
    scenario: { structure: 'Cu (CFC) do motor', supercell: '3×3×3', drawnAtoms: info.atoms, instances: info.instances },
    fps: { target: '≈ 60', value: Number(bench.fps.toFixed(1)), frames: bench.frames, windowMs: Math.round(bench.ms), met: bench.fps >= 55 },
    selection: {
      target: '< 16 ms',
      samples: work.length,
      pickMedianMs: Number(median(pick).toFixed(2)),
      workMedianMs: Number(median(work).toFixed(2)),
      workMaxMs: Number(Math.max(...work).toFixed(2)),
      clickToFrameMedianMs: Number(median(toFrame).toFixed(2)),
      definition: 'work = raycast + atualização de estado + quadro do destaque (CPU); clickToFrame inclui a espera do próximo quadro',
      met: median(work) < 16,
    },
  };
  mkdirSync('reports', { recursive: true });
  const prev = existsSync('reports/metrics.json') ? JSON.parse(readFileSync('reports/metrics.json', 'utf8')) : {};
  writeFileSync('reports/metrics.json', JSON.stringify({ ...prev, viewer: metrics }, null, 2));
});
