/**
 * Viewer 3D (Etapa 3) — módulo carregado sob demanda junto com o Three.js local.
 * Recebe o palco (div com data-testid="viewer-stage") do ViewerPanel e desenha nele.
 */
import { useEffect, useRef } from 'react';
import { dispatch } from '../../commands/bus.ts';
import { alphaGammaData, loadAlphaGamma } from './alphaGamma.ts';
import type { StructureResult } from '../../services/api/contracts.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useOverlays, atomKey, type AtomRef } from '../../stores/overlays.ts';
import { effectiveTheme, prefersReducedMotion, usePreferences } from '../../stores/preferences.ts';
import { useViewer } from '../../stores/viewer.ts';
import { registerViewer } from '../registry.ts';
import { createRng } from '../../utils/rng.ts';
import { illustrativeElements } from './geometry.ts';
import { SceneController, type AnimationFrame, type ElementColoring } from './SceneController.ts';
import { elementLegendFor } from '../../modules/crystalab/elementLegend.ts';
import { announce } from '../../design-system/announce.ts';
import { translate } from '../../i18n/index.ts';

export const LAYER_COLORS: Record<string, string> = { A: '#0072B2', B: '#E69F00', C: '#009E73' };

export default function Viewer3D({ stage, onReady }: { stage: HTMLDivElement; onReady?: (ok: boolean) => void }) {
  const ctrlRef = useRef<SceneController | null>(null);

  // montagem / desmontagem
  useEffect(() => {
    let ctrl: SceneController;
    try {
      ctrl = new SceneController(stage, {
        onCamera: (cam) => useViewer.getState().set({ camera: cam }),
        onPick: (ref) => handlePick(ref),
      });
    } catch {
      useViewer.getState().set({ engine: 'unsupported' });
      onReady?.(false);
      return undefined;
    }
    ctrlRef.current = ctrl;
    useViewer.getState().set({ engine: 'ready' });
    onReady?.(true);
    registerViewer({
      capturePng: () => ctrl.capturePng(),
      resetView: () => ctrl.resetView(),
      describe: () => `${ctrl.getAtoms().length} esferas`,
      orbit: (a, b) => ctrl.orbit(a, b),
      zoom: (f) => ctrl.zoom(f),
    });
    window.__alloy = {
      ...(window.__alloy ?? {}),
      viewer: {
        stats: ctrl.stats,
        benchmark: (ms: number) => ctrl.benchmark(ms),
        screenPosition: (key: string) => {
          const [index, cell] = key.split('@');
          return ctrl.screenPosition({ index: Number(index), cell: (cell ?? '0,0,0').split(',').map(Number) as [number, number, number] });
        },
        atoms: () => ctrl.getAtoms().map((a) => ({ key: a.key, replica: a.replica, tipo: a.tipo })),
        touchMode: () => ctrl.touchMode,
        camera: () => ctrl.getCamera(),
      },
    };
    return () => {
      registerViewer(null);
      if (window.__alloy) delete window.__alloy.viewer;
      ctrl.dispose();
      ctrlRef.current = null;
      useViewer.getState().set({ engine: 'idle' });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  // assinaturas dos stores → atualizações incrementais
  useEffect(() => {
    const apply = () => {
      const ctrl = ctrlRef.current;
      if (!ctrl) return;
      const { structure, heaTransfer } = useCrystalab.getState();
      const v = useViewer.getState();
      if (!structure) return;
      ctrl.setStructure(structure, v.supercell, v.display, v.camera !== null);
      ctrl.setDisplay(v.display);
      if (v.elementColoring?.enabled && heaTransfer) {
        const composition = heaTransfer.result.comp_percent;
        const legend = elementLegendFor(composition);
        const rng = createRng(v.elementColoring.seed);
        const coloring: ElementColoring = {
          elements: illustrativeElements(ctrl.getAtoms(), composition, rng),
          colors: Object.fromEntries(legend.map((l) => [l.element, l.color])),
          shapes: Object.fromEntries(legend.map((l) => [l.element, l.shape])),
        };
        ctrl.setElementColoring(coloring);
      }
    };
    apply();
    let last = { s: useCrystalab.getState().structure, sc: useViewer.getState().supercell, ec: useViewer.getState().elementColoring, d: useViewer.getState().display };
    const check = () => {
      const s = useCrystalab.getState().structure;
      const v = useViewer.getState();
      if (s !== last.s || v.supercell !== last.sc || v.elementColoring !== last.ec) {
        const ctrl = ctrlRef.current;
        if (ctrl && s && (v.elementColoring !== last.ec && !v.elementColoring?.enabled)) ctrl.setElementColoring(null);
        last = { s, sc: v.supercell, ec: v.elementColoring, d: v.display };
        apply();
      } else if (v.display !== last.d) {
        last = { ...last, d: v.display };
        ctrlRef.current?.setDisplay(v.display);
      }
    };
    const u1 = useCrystalab.subscribe(check);
    const u2 = useViewer.subscribe(check);
    return () => { u1(); u2(); };
  }, []);

  useEffect(() => {
    const apply = () => {
      const { items, selectedId } = useOverlays.getState();
      ctrlRef.current?.setOverlays(items, selectedId);
    };
    apply();
    return useOverlays.subscribe(apply);
  }, []);

  useEffect(() => {
    let rev = useViewer.getState().cameraRevision;
    ctrlRef.current?.setCamera(useViewer.getState().camera);
    let sel = useViewer.getState().selection;
    let tool = useViewer.getState().tool;
    let unlocked = useViewer.getState().sceneUnlocked;
    ctrlRef.current?.setSelection(sel, tool?.picks ?? []);
    const touchLock = () => usePreferences.getState().touchSceneLock && !useViewer.getState().sceneUnlocked && matchMedia('(pointer: coarse)').matches;
    ctrlRef.current?.setTouchLocked(touchLock());
    return useViewer.subscribe((s) => {
      const ctrl = ctrlRef.current;
      if (!ctrl) return;
      if (s.cameraRevision !== rev) { rev = s.cameraRevision; ctrl.setCamera(s.camera); }
      if (s.selection !== sel || s.tool !== tool) { sel = s.selection; tool = s.tool; ctrl.setSelection(sel, tool?.picks ?? []); }
      if (s.sceneUnlocked !== unlocked) { unlocked = s.sceneUnlocked; ctrl.setTouchLocked(touchLock()); }
    });
  }, []);

  // tema
  useEffect(() => {
    let theme = effectiveTheme(usePreferences.getState().theme);
    const mq = matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => {
      const next = effectiveTheme(usePreferences.getState().theme);
      if (next !== theme) { theme = next; window.setTimeout(() => ctrlRef.current?.setTheme(), 0); }
    };
    mq.addEventListener('change', onChange);
    const u = usePreferences.subscribe(onChange);
    return () => { mq.removeEventListener('change', onChange); u(); };
  }, []);

  // animações didáticas
  useEffect(() => {
    let timer = 0;
    const render = () => {
      const ctrl = ctrlRef.current;
      if (!ctrl) return;
      const a = useViewer.getState().animation;
      window.clearInterval(timer);
      if (!a) { ctrl.setAnimationFrame(null); return; }
      const frame = frameFor(a.name, a.variant, a.step, useCrystalab.getState().structure);
      if (frame === 'loading') {
        void loadAlphaGamma().then(render);
        return;
      }
      ctrl.setAnimationFrame(frame);
      const reduce = prefersReducedMotion(usePreferences.getState().motion);
      if (a.playing && !reduce) {
        timer = window.setInterval(() => {
          const cur = useViewer.getState().animation;
          if (!cur) return;
          const max = maxStep(cur.name);
          if (cur.step >= max) { useViewer.getState().set({ animation: { ...cur, playing: false } }); return; }
          useViewer.getState().set({ animation: { ...cur, step: cur.step + 1 } });
        }, a.name === 'stacking' ? 900 : 250);
      }
    };
    render();
    let prev = useViewer.getState().animation;
    const u = useViewer.subscribe((s) => { if (s.animation !== prev) { prev = s.animation; render(); } });
    return () => { u(); window.clearInterval(timer); };
  }, []);

  return null;
}

export function maxStep(name: string): number {
  return name === 'stacking' ? 5 : 10;
}

function frameFor(name: string, variant: string, step: number, current: StructureResult | null): AnimationFrame | 'loading' | null {
  if (name === 'stacking') {
    const seq = variant === 'abab' ? ['A', 'B', 'A', 'B', 'A', 'B'] : ['A', 'B', 'C', 'A', 'B', 'C'];
    return { kind: 'stacking', sequence: seq, visibleLayers: step + 1, layerColors: LAYER_COLORS };
  }
  if (name === 'alpha-gamma') {
    const d = alphaGammaData();
    if (!d.from || !d.to) return 'loading';
    return { kind: 'alpha-gamma', from: d.from, to: d.to, mix: step / 10 };
  }
  if (name === 'thermal' && current) return { kind: 'thermal', scale: 1 + (step / 10) * 0.06 };
  return null;
}

function handlePick(ref: AtomRef | null): void {
  const v = useViewer.getState();
  const tr = (k: Parameters<typeof translate>[1], vars?: Record<string, string | number>) => translate(usePreferences.getState().locale, k, vars);
  if (v.tool) {
    if (!ref) return;
    const picks = [...v.tool.picks, ref];
    const needed = v.tool.kind === 'distance' ? 2 : 3;
    if (picks.length < needed) {
      v.set({ tool: { ...v.tool, picks } });
      announce(tr('measure.picked', { n: picks.length, total: needed, atom: ref.index + 1 }));
      return;
    }
    v.set({ tool: { ...v.tool, picks } });
    void dispatch({ type: 'measure.add', kind: v.tool.kind, atoms: picks }, 'viewer').then((res) => {
      if (res.status !== 'done') { const cur = useViewer.getState(); if (cur.tool) cur.set({ tool: { ...cur.tool, picks: [] } }); }
    });
    return;
  }
  v.set({ selection: ref });
  if (ref) announce(tr('viewer.selected', { n: ref.index + 1, key: atomKey(ref) }));
}
