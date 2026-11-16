/**
 * Viewer 3D (Etapa 3) — módulo carregado sob demanda junto com o Three.js local.
 * Recebe o palco (div com data-testid="viewer-stage") do ViewerPanel e desenha nele.
 */
import { useEffect, useRef } from 'react';
import { dispatch } from '../../commands/bus.ts';
import { alphaGammaData, loadAlphaGamma } from './alphaGamma.ts';
import type { StructureResult } from '../../services/api/contracts.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useOverlays, atomKey } from '../../stores/overlays.ts';
import { effectiveTheme, prefersReducedMotion, usePreferences } from '../../stores/preferences.ts';
import { useViewer } from '../../stores/viewer.ts';
import { registerViewer } from '../registry.ts';
import { setCameraApi } from './cameraApi.ts';
import { createRng } from '../../utils/rng.ts';
import { buildEdges, illustrativeElements } from './geometry.ts';
import { sceneFromAlloy, sceneFromStructure, type ThermalScene } from './alloyScene.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { useSceneFilter } from '../../stores/sceneFilter.ts';
import { appearanceSnapshot, useAppearance } from '../../stores/appearance.ts';
import { currentFilter } from './sceneFilterState.ts';
import { SceneController, type AnimationFrame, type ElementColoring, type PickTarget } from './SceneController.ts';
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
        onPickTarget: (target) => handlePick(target),
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
    setCameraApi({ orbit: (a, b) => ctrl.orbit(a, b), zoom: (f) => ctrl.zoom(f), pan: (x, y) => ctrl.pan(x, y), frame: () => ctrl.frameContent() });
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
        hiddenKeys: () => ctrl.hiddenKeys(),
        alloyAtoms: () => ctrl.alloyDrawnIds(),
        appearance: () => ctrl.appearanceSummary(),
        alloyScreenPosition: (id: string) => ctrl.alloyScreenPosition(id),
        camera: () => ctrl.getCamera(),
        orbit: (a: number, b: number) => ctrl.orbit(a, b),
        pan: (x: number, y: number) => ctrl.pan(x, y),
        frame: () => ctrl.frameContent(),
        reset: () => ctrl.resetView(),
        size: () => ctrl.viewportSize(),
      },
    };
    return () => {
      registerViewer(null);
      setCameraApi(null);
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

  // aparência (T-22): cores, tamanho, transparência, arestas e vértices da CÉLULA do metal puro
  // (a cena de liga é remontada no efeito da liga, que resolve a cor de cada átomo)
  useEffect(() => {
    const apply = () => ctrlRef.current?.setAppearance(appearanceSnapshot());
    apply();
    return useAppearance.subscribe(apply);
  }, []);

  // filtros/cortes de exibição (T-23) e seleção na cena de liga (T-24)
  useEffect(() => {
    const applyFilter = () => ctrlRef.current?.setFilter(currentFilter());
    const applyAlloySelection = () => ctrlRef.current?.setAlloySelection(useViewer.getState().alloySelection);
    applyFilter();
    applyAlloySelection();
    let f = useSceneFilter.getState();
    let sel = useViewer.getState().selection;
    let alloySel = useViewer.getState().alloySelection;
    let alloyResult = useAlloy.getState().alloy;
    // outra liga (ou volta ao metal puro) invalida a identidade do átomo selecionado
    const checkAlloy = () => {
      const next = useAlloy.getState().alloy;
      if (next === alloyResult) return;
      alloyResult = next;
      if (useViewer.getState().alloySelection) useViewer.getState().set({ alloySelection: null });
    };
    const check = () => {
      const next = useSceneFilter.getState();
      const v = useViewer.getState();
      const selectionChanged = v.selection !== sel || v.alloySelection !== alloySel;
      if (v.alloySelection !== alloySel) { alloySel = v.alloySelection; applyAlloySelection(); }
      if (v.selection !== sel) sel = v.selection;
      // a vizinhança de exibição depende do átomo selecionado; o resto, só do filtro
      if (next !== f || (selectionChanged && next.neighbourhoodRadius !== null)) { f = next; applyFilter(); }
    };
    const unsubs = [useSceneFilter.subscribe(check), useViewer.subscribe(check), useAlloy.subscribe(checkAlloy)];
    return () => unsubs.forEach((u) => u());
  }, []);

  // liga e vibração térmica (T-13): a cena vem do motor (API); o viewer só desenha
  useEffect(() => {
    let key = '';
    const apply = () => {
      const ctrl = ctrlRef.current;
      if (!ctrl) return;
      const a = useAlloy.getState();
      const structure = useCrystalab.getState().structure;
      const supercell = useViewer.getState().supercell;
      const reduce = prefersReducedMotion(usePreferences.getState().motion);
      const filter = currentFilter();
      const appearance = appearanceSnapshot();
      const next = [a.alloy, a.thermal, a.thermalTarget, a.vibration.on, a.vibration.exaggeration, structure, supercell, reduce, JSON.stringify(filter), JSON.stringify(appearance)].map((v) => (v && typeof v === 'object' ? (cache.get(v) ?? cache.set(v, ++ids).get(v)) : String(v))).join('|');
      if (next === key) return;
      key = next;
      // a amplitude só vale para os átomos a que o cálculo térmico se refere
      const matches = a.thermal && ((a.thermalTarget === 'alloy' && a.alloy) || (a.thermalTarget === 'material' && !a.alloy));
      const amplitude = a.vibration.on && matches && a.thermal ? a.thermal.amplitude_rel : 0;
      let scene: ThermalScene | null = null;
      if (a.alloy) scene = sceneFromAlloy(a.alloy, amplitude, filter, appearance);
      else if (a.vibration.on && structure && amplitude > 0) {
        scene = sceneFromStructure(structure, ctrl.getAtoms(), buildEdges(structure, supercell) as unknown as Array<[number, number, number]>[], amplitude, filter, appearance);
      }
      // a aparência vai JUNTO da cena: o mesmo instantâneo que resolveu a cor de cada átomo
      ctrl.setThermalScene(scene, {
        playing: a.vibration.on && !reduce,
        exaggeration: a.vibration.exaggeration,
        atomScale: appearance.atomScale,
        opacity: appearance.opacity,
        edgeColor: appearance.edgeColor,
        vertexColor: appearance.vertexColor,
        vertices: appearance.vertices,
      });
      const w = window as unknown as { __alloy?: { viewer?: Record<string, unknown> } };
      if (w.__alloy?.viewer) w.__alloy.viewer.thermalScene = () => ctrl.thermalSummary();
    };
    const cache = new WeakMap<object, number>();
    let ids = 0;
    apply();
    const unsubs = [useAlloy.subscribe(apply), useCrystalab.subscribe(apply), useViewer.subscribe(apply), usePreferences.subscribe(apply), useSceneFilter.subscribe(apply), useAppearance.subscribe(apply)];
    return () => unsubs.forEach((u) => u());
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

function handlePick(target: PickTarget | null): void {
  const v = useViewer.getState();
  const tr = (k: Parameters<typeof translate>[1], vars?: Record<string, string | number>) => translate(usePreferences.getState().locale, k, vars);
  // cena de liga (T-24): a identidade é o `id` do motor; a ferramenta de medição não a usa
  if (target?.kind === 'alloy' || (useAlloy.getState().alloy && !target)) {
    const id = target?.kind === 'alloy' ? target.id : null;
    v.set({ alloySelection: id });
    if (id) announce(tr('alloyAtom.selected', { id }));
    return;
  }
  const ref = target?.kind === 'cell' ? target.ref : null;
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
