/** Reconstrói uma cena a partir do estado validado (link compartilhado ou workspace). */
import { applyStructure, computeMiller, loadStructure, structureSummary } from '../../commands/handlers.ts';
import { tr } from '../../commands/bus.ts';
import { commit } from '../../stores/history.ts';
import { nextColor, useOverlays, type OverlayItem } from '../../stores/overlays.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useViewer, DEFAULT_DISPLAY } from '../../stores/viewer.ts';
import { log } from '../../stores/terminal.ts';
import { safeColor, type SceneV1 } from './sceneUrl.ts';

/** keepHea: o link também referencia um resultado HEA (h=), que deve permanecer associado à cena. */
export async function restoreScene(scene: SceneV1, signal: AbortSignal, label = 'link', options: { keepHea?: boolean } = {}): Promise<void> {
  const structure = await loadStructure(scene.m, signal);
  if (!structure) return;
  applyStructure(structure, scene.m, { keepHea: Boolean(options.keepHea) });
  const items: OverlayItem[] = [];
  for (const o of scene.o ?? []) {
    const ov = await computeMiller(o.t === 'p' ? 'plano' : 'direcao', o.i, signal);
    ov.color = safeColor(o.c, nextColor(items));
    ov.visible = o.h !== 1;
    if (ov.kind === 'plane') ov.clip = o.k === 1;
    items.push(ov);
  }
  useOverlays.getState().set({ items, selectedId: null });
  const v = useViewer.getState();
  v.set({
    display: { ...DEFAULT_DISPLAY, ...(scene.d?.a ? { atoms: scene.d.a } : {}), ...(scene.d?.e !== undefined ? { edges: scene.d.e } : {}), ...(scene.d?.x !== undefined ? { axes: scene.d.x } : {}), ...(scene.d?.l !== undefined ? { latticePoints: scene.d.l } : {}), ...(scene.d?.r !== undefined ? { labels: scene.d.r } : {}) },
    supercell: scene.s ?? [1, 1, 1],
    camera: scene.c ? { position: scene.c.p, target: scene.c.t } : null,
    cameraRevision: v.cameraRevision + 1,
  });
  useCrystalab.getState().set({ densityVisible: scene.dn === 1 });
  commit(`${label}: ${structure.rotulo}`);
  log('ok', tr('share.restored', { label: structureSummary(structure) }));
}
