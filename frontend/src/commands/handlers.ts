/**
 * Handlers das operações do CrystaLab e da aplicação. Cada handler é a ÚNICA implementação
 * da operação — por isso terminal, formulário, paleta e viewer produzem o mesmo resultado.
 */
import { announce } from '../design-system/announce.ts';
import { crystalabApi } from '../services/api/crystalab.ts';
import { latest, staleError } from '../services/api/latest.ts';
import type { MillerResult, StructureRequest, StructureResult, Vec3 } from '../services/api/contracts.ts';
import { structureToEditor, useCrystalab } from '../stores/crystalab.ts';
import { commit, redo, undo } from '../stores/history.ts';
import { nextColor, useOverlays, type Measurement, type OverlayItem } from '../stores/overlays.ts';
import { angleDeg, cellOffset, distance, measurementProblem, translations } from '../features/viewer3d/geometry.ts';
import { effectiveTheme, usePreferences } from '../stores/preferences.ts';
import { clearLog, log } from '../stores/terminal.ts';
import { toast } from '../stores/toast.ts';
import { useViewer } from '../stores/viewer.ts';
import { formatNumber } from '../utils/format.ts';
import { plain } from '../utils/text.ts';
import { uid } from '../utils/id.ts';
import { navigate } from '../app/router.ts';
import { cancelRunning, registerHandler, tr } from './bus.ts';
import { specsFor } from './catalog.ts';
import type { Context } from './types.ts';

const n = (v: number | null | undefined, d: number): string => formatNumber(v, d, usePreferences.getState().locale);

/** Época da cena: muda a cada nova estrutura; respostas de Miller de uma época anterior são descartadas (FE-07). */
let sceneEpoch = 0;
const millerControllers = new Set<AbortController>();

export function currentEpoch(): number {
  return sceneEpoch;
}

export function structureSummary(r: StructureResult): string {
  const density = r.densidade !== null ? ` · ρ = ${n(r.densidade, 3)} g/cm³` : '';
  return `${r.rotulo}: ${r.estrutura} · NC ${r.nc} · FEA ${n(r.fea, 3)}${density}`;
}

/** Aplica um resultado do motor como nova cena (usado também pela ponte HEA e pela URL). */
export function applyStructure(result: StructureResult, request: StructureRequest, options: { keepHea?: boolean; keepOverlays?: boolean } = {}): void {
  sceneEpoch += 1;
  millerControllers.forEach((c) => c.abort());
  millerControllers.clear();
  const c = useCrystalab.getState();
  c.set({ structure: result, request, status: 'ready', error: null, editorText: structureToEditor(result), ...(options.keepHea ? {} : { heaTransfer: null }) });
  if (!options.keepOverlays) useOverlays.getState().set({ items: [], selectedId: null });
  useViewer.getState().set({ selection: null, tool: null, ...(options.keepHea ? {} : { elementColoring: null }) });
}

export async function loadStructure(request: StructureRequest, signal: AbortSignal): Promise<StructureResult | null> {
  useCrystalab.getState().set({ status: 'loading', error: null });
  try {
    const outcome = await latest.run('structure', (s) => {
      signal.addEventListener('abort', () => latest.cancel('structure'), { once: true });
      return crystalabApi.structure(request, s);
    });
    if (outcome.stale) throw staleError('structure');
    return outcome.value;
  } catch (err) {
    const prev = useCrystalab.getState().structure;
    useCrystalab.getState().set({ status: prev ? 'ready' : 'error', error: err instanceof Error ? err.message : String(err) });
    throw err;
  }
}

export function millerDetail(o: MillerResult): string {
  if (o.tipo === 'plano') {
    const spacing = o.d_nm ? `${n(o.d_nm, 4)} nm` : `${n(o.d_rel, 3)} a`;
    return tr('cmd.ok.planeDetail', { spacing, count: o.atomos.length });
  }
  const length = o.comprimento_nm ? `${n(o.comprimento_nm, 4)} nm` : `${n(o.comprimento_rel, 3)} a`;
  let linear = '';
  if (o.densidade_linear_nm) linear = ` · DL = ${n(o.densidade_linear_nm, 2)} át/nm`;
  else if (o.densidade_linear_rel) linear = ` · DL = ${n(o.densidade_linear_rel, 3)} át/a`;
  return `|v| = ${length}${linear}`;
}

/** Calcula um plano/direção no motor e devolve o overlay pronto (sem adicioná-lo). */
export async function computeMiller(tipo: 'plano' | 'direcao', indices: number[], signal: AbortSignal): Promise<OverlayItem> {
  const structure = useCrystalab.getState().structure;
  if (!structure) throw new Error(tr('cmd.err.noStructure'));
  const epoch = sceneEpoch;
  const ctrl = new AbortController();
  millerControllers.add(ctrl);
  const abort = () => ctrl.abort();
  signal.addEventListener('abort', abort, { once: true });
  try {
    const result = await crystalabApi.miller({ estrutura: structure.estrutura, tipo, indices, a_nm: structure.a_nm, c_a: structure.c_a }, ctrl.signal);
    if (epoch !== sceneEpoch || useCrystalab.getState().structure !== structure) throw staleError('miller');
    const items = useOverlays.getState().items;
    const base = { id: uid('ov'), visible: true, color: nextColor(items), label: result.notacao };
    return result.tipo === 'plano' ? { ...base, kind: 'plane', data: result, clip: false } : { ...base, kind: 'direction', data: result };
  } catch (err) {
    if (ctrl.signal.aborted && epoch !== sceneEpoch) throw staleError('miller');
    throw err;
  } finally {
    millerControllers.delete(ctrl);
    signal.removeEventListener('abort', abort);
  }
}

/** Mesmo formato/regra do editor de parâmetros do CrystaLab v1.0. */
export function parseEditorText(text: string): StructureRequest {
  const payload: StructureRequest = {};
  const keys: Record<string, keyof StructureRequest> = { elemento: 'nome', metal: 'nome', nome: 'nome', estrutura: 'estrutura', raio: 'raio', r: 'raio', peso: 'peso', massa: 'peso', 'c/a': 'c_a', ca: 'c_a' };
  for (const rawLine of text.split('\n')) {
    const line = rawLine.split('#')[0] ?? '';
    const m = line.match(/^\s*([^=:]+?)\s*[=:]\s*(.*?)\s*$/);
    if (!m) continue;
    const key = keys[plain(m[1] ?? '')];
    if (!key) continue;
    const value = m[2] ?? '';
    if (key === 'nome') { if (value && !value.startsWith('(')) payload.nome = value; }
    else if (key === 'estrutura') { if (value) payload.estrutura = value.toUpperCase() as StructureRequest['estrutura']; }
    else if (value) {
      const v = Number(value.replace(',', '.'));
      if (Number.isFinite(v)) payload[key] = v;
    }
  }
  return payload;
}

function helpLines(context: Context, topic?: string): string {
  const specs = specsFor(context);
  if (topic) {
    const spec = specs.find((s) => plain(s.verb) === plain(topic) || s.aliases.some((a) => plain(a) === plain(topic)));
    if (!spec) return tr('cmd.err.unknownCommand', { text: topic });
    return `${spec.syntax}\n  ${tr(spec.descriptionKey)}\n  ${tr('terminal.examples')}: ${spec.examples.join(' · ')}`;
  }
  return [tr('terminal.helpTitle'), ...specs.map((s) => `  ${s.syntax.padEnd(44)} ${tr(s.descriptionKey)}`)].join('\n');
}

export function registerCrystalabHandlers(): void {
  registerHandler('material.load', async (op, ctx) => {
    ctx.running('cmd.run.structure');
    const result = await loadStructure(op.request, ctx.signal);
    if (!result) return;
    applyStructure(result, op.request);
    commit(`estrutura ${result.rotulo}`);
    log('ok', structureSummary(result), { opId: ctx.opId });
    for (const aviso of result.avisos ?? []) log('warn', aviso, { opId: ctx.opId });
    announce(tr('a11y.structureLoaded', { label: result.rotulo, structure: result.estrutura_nome }));
  });

  registerHandler('editor.apply', async (_op, ctx) => {
    const req = parseEditorText(useCrystalab.getState().editorText);
    if (!req.nome && !req.estrutura) throw new Error(tr('cmd.err.editorEmpty'));
    ctx.running('cmd.run.structure');
    const result = await loadStructure(req, ctx.signal);
    if (!result) return;
    applyStructure(result, req);
    commit(`aplicar ${result.rotulo}`);
    log('ok', structureSummary(result), { opId: ctx.opId });
    for (const aviso of result.avisos ?? []) log('warn', aviso, { opId: ctx.opId });
    announce(tr('a11y.structureLoaded', { label: result.rotulo, structure: result.estrutura_nome }));
  });

  registerHandler('miller.draw', async (op, ctx) => {
    if (!useCrystalab.getState().structure) throw new Error(tr('cmd.err.noStructure'));
    ctx.running('cmd.run.miller', { kind: op.tipo === 'plano' ? tr('miller.plane') : tr('miller.direction') });
    const overlay = await computeMiller(op.tipo, op.indices, ctx.signal);
    const s = useOverlays.getState();
    s.set({ items: [...s.items, overlay], selectedId: overlay.id });
    commit(`${op.tipo} ${overlay.label}`);
    const data = overlay.kind === 'plane' || overlay.kind === 'direction' ? overlay.data : null;
    if (data) {
      const name = data.tipo === 'plano' ? tr('miller.plane') : tr('miller.direction');
      const extra = data.notacao_alternativa ? ` = ${data.notacao_alternativa}` : '';
      log('ok', `${name} ${data.notacao}${extra}: ${millerDetail(data)}`, { opId: ctx.opId });
      if (data.tipo === 'direcao' && (data.densidade_linear_rel === null || data.densidade_linear_rel === undefined)) log('step', tr('cmd.ok.noLinearDensity'), { opId: ctx.opId });
      for (const aviso of data.avisos ?? []) log('warn', aviso, { opId: ctx.opId });
      announce(tr('a11y.overlayAdded', { name, notation: data.notacao }));
    }
  });

  registerHandler('density.show', (_op, ctx) => {
    const r = useCrystalab.getState().structure;
    if (!r) throw new Error(tr('cmd.err.noStructure'));
    useCrystalab.getState().set({ densityVisible: true });
    commit('densidade');
    if (r.densidade === null) {
      log('error', r.passos_densidade[0]?.detalhe ?? tr('density.insufficient'), { opId: ctx.opId });
      return;
    }
    log('ok', tr('cmd.ok.densityTitle', { label: r.rotulo }), { opId: ctx.opId });
    r.passos_densidade.forEach((step, i) => log('step', `${i + 1}. ${step.titulo}\n   ${step.formula.replace(/\n/g, '\n   ')}`, { opId: ctx.opId }));
    window.setTimeout(() => document.getElementById('density-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
  });

  registerHandler('overlays.clear', (_op, ctx) => {
    useOverlays.getState().set({ items: [], selectedId: null });
    commit('limpar índices');
    log('ok', tr('cmd.ok.overlaysCleared'), { opId: ctx.opId });
  });

  registerHandler('lab.clear', () => {
    useOverlays.getState().set({ items: [], selectedId: null });
    useViewer.getState().set({ selection: null, tool: null });
    commit('limpar');
    clearLog();
    log('ok', tr('cmd.ok.labCleared'));
  });

  registerHandler('view.atoms', (op, ctx) => {
    const v = useViewer.getState();
    v.set({ display: { ...v.display, atoms: op.mode } });
    commit(`esferas ${op.mode}`);
    log('ok', tr(`view.atomMode.${op.mode}`), { opId: ctx.opId });
  });

  registerHandler('view.toggle', (op, ctx) => {
    const v = useViewer.getState();
    if (op.key === 'rigid') {
      const next = op.value ?? v.display.atoms !== 'rigid';
      v.set({ display: { ...v.display, atoms: next ? 'rigid' : 'reduced' } });
      commit('esferas');
      log('ok', next ? tr('cmd.ok.rigidOn') : tr('cmd.ok.rigidOff'), { opId: ctx.opId });
      return;
    }
    const next = op.value ?? !v.display[op.key];
    v.set({ display: { ...v.display, [op.key]: next } });
    if (op.key !== 'autoRotate') commit(`${op.key}`);
    log('ok', tr(next ? 'cmd.ok.toggleOn' : 'cmd.ok.toggleOff', { what: tr(`view.toggle.${op.key}`) }), { opId: ctx.opId });
  });

  registerHandler('view.reset', (_op, ctx) => {
    const v = useViewer.getState();
    v.set({ camera: null, cameraRevision: v.cameraRevision + 1 });
    log('ok', tr('cmd.ok.viewReset'), { opId: ctx.opId });
  });

  registerHandler('supercell.set', (op, ctx) => {
    if (!useCrystalab.getState().structure) throw new Error(tr('cmd.err.noStructure'));
    useViewer.getState().set({ supercell: op.n, selection: null, tool: null });
    commit(`supercélula ${op.n.join('×')}`);
    const cells = op.n[0] * op.n[1] * op.n[2];
    log('ok', tr('cmd.ok.supercell', { n: op.n.join('×') }), { opId: ctx.opId });
    log('step', tr('cmd.ok.supercellCounts'), { opId: ctx.opId });
    if (cells > 27) log('warn', tr('cmd.ok.supercellCost', { cells }), { opId: ctx.opId });
  });

  registerHandler('measure.start', (op, ctx) => {
    if (!useCrystalab.getState().structure) throw new Error(tr('cmd.err.noStructure'));
    useViewer.getState().set({ tool: { kind: op.kind, picks: [] }, selection: null });
    log('info', tr(op.kind === 'distance' ? 'measure.startDistance' : 'measure.startAngle'), { opId: ctx.opId });
    announce(tr(op.kind === 'distance' ? 'measure.startDistance' : 'measure.startAngle'));
  });

  registerHandler('measure.add', (op, ctx) => {
    const r = useCrystalab.getState().structure;
    if (!r) throw new Error(tr('cmd.err.noStructure'));
    const problem = measurementProblem(op.kind, op.atoms);
    if (problem) throw new Error(tr(problem === 'duplicate' ? 'measure.invalidDuplicate' : 'measure.invalidVertex'));
    const t = translations(r.estrutura, r.c_a);
    const points = op.atoms.map((a) => {
      const atom = r.atomos[a.index];
      if (!atom) throw new Error(tr('measure.invalidAtom', { n: a.index + 1 }));
      const off = cellOffset(t, a.cell);
      return [atom.pos[0] + off[0], atom.pos[1] + off[1], atom.pos[2] + off[2]] as Vec3;
    });
    const items = useOverlays.getState().items;
    let label: string;
    let data: Measurement;
    if (op.kind === 'distance') {
      const valueA = distance(points[0] as Vec3, points[1] as Vec3);
      const valueNm = r.a_nm !== null ? valueA * r.a_nm : null;
      label = `${n(valueA, 3)} a${valueNm !== null ? ` = ${n(valueNm, 4)} nm` : ''}`;
      data = { type: 'distance', atoms: op.atoms, valueA, valueNm, points };
    } else {
      const degrees = angleDeg(points[0] as Vec3, points[1] as Vec3, points[2] as Vec3);
      if (!Number.isFinite(degrees)) throw new Error(tr('measure.invalidVertex'));
      label = `${n(degrees, 1)}°`;
      data = { type: 'angle', atoms: op.atoms, degrees, points };
    }
    const overlay: OverlayItem = { id: uid('ms'), kind: 'measurement', visible: true, color: nextColor(items), label, data };
    useOverlays.getState().set({ items: [...items, overlay] });
    const v = useViewer.getState();
    if (v.tool) v.set({ tool: { ...v.tool, picks: [] } });
    commit(`medição ${label}`);
    log('ok', tr(op.kind === 'distance' ? 'measure.doneDistance' : 'measure.doneAngle', { value: label, atoms: op.atoms.map((a) => a.index + 1).join('–') }), { opId: ctx.opId });
    log('step', tr('measure.geometryNote'), { opId: ctx.opId });
    announce(tr(op.kind === 'distance' ? 'measure.doneDistance' : 'measure.doneAngle', { value: label, atoms: op.atoms.map((a) => a.index + 1).join('–') }));
  });

  registerHandler('measure.stop', (_op, ctx) => {
    useViewer.getState().set({ tool: null });
    log('ok', tr('measure.stopped'), { opId: ctx.opId });
  });

  registerHandler('history.undo', (_op, ctx) => {
    const undone = undo();
    if (!undone) { log('warn', tr('cmd.ok.nothingToUndo'), { opId: ctx.opId }); return; }
    log('ok', tr('cmd.ok.undone', { label: undone.label }), { opId: ctx.opId });
    announce(tr('cmd.ok.undone', { label: undone.label }));
  });

  registerHandler('history.redo', (_op, ctx) => {
    const redone = redo();
    if (!redone) { log('warn', tr('cmd.ok.nothingToRedo'), { opId: ctx.opId }); return; }
    log('ok', tr('cmd.ok.redone', { label: redone.label }), { opId: ctx.opId });
    announce(tr('cmd.ok.redone', { label: redone.label }));
  });

  registerHandler('export', async (op, ctx) => {
    const { runExport } = await import('../features/export/exporters.ts');
    ctx.running('cmd.run.export', { format: op.format.toUpperCase() });
    const message = await runExport(op.format, ctx.signal);
    log('ok', message, { opId: ctx.opId });
  });

  registerHandler('share', async (_op, ctx) => {
    const { buildShareUrl } = await import('../features/url/sceneUrl.ts');
    const { url, length, truncated } = buildShareUrl();
    // A barra de endereço passa a mostrar exatamente o link compartilhado (a sincronização automática
    // da URL tem atraso de 700 ms e podia exibir o estado anterior, sem a última camada).
    if (new URL(url, window.location.href).origin === window.location.origin) window.history.replaceState(null, '', url);
    let copied = false;
    try { await navigator.clipboard.writeText(url); copied = true; } catch { /* sem permissão de área de transferência */ }
    log('ok', tr(copied ? 'share.copied' : 'share.ready', { length }), { opId: ctx.opId });
    log('info', url, { opId: ctx.opId });
    if (truncated) log('warn', tr('share.truncated'), { opId: ctx.opId });
    toast({ tone: 'success', title: tr(copied ? 'share.copied' : 'share.ready', { length }), body: url });
  });

  registerHandler('workspace.save', async (op, ctx) => {
    const { saveWorkspace } = await import('../features/workspace/workspaces.ts');
    const ws = saveWorkspace(op.name);
    log('ok', tr('workspace.saved', { name: ws.name }), { opId: ctx.opId });
    log('step', tr('workspace.localOnly'), { opId: ctx.opId });
  });

  registerHandler('animation.open', (op, ctx) => {
    if (!useCrystalab.getState().structure) throw new Error(tr('cmd.err.noStructure'));
    useViewer.getState().set({ animation: { name: op.name, variant: op.variant ?? (op.name === 'stacking' ? 'abcabc' : ''), step: 0, playing: false } });
    log('ok', tr(`anim.opened.${op.name}`), { opId: ctx.opId });
  });

  registerHandler('list', (_op, ctx) => {
    const { metals, structures } = useCrystalab.getState();
    const m = Object.entries(metals ?? {}).map(([s, x]) => `${s} (${x.estrutura})`).join(', ');
    log('info', `${tr('terminal.metals')}: ${m}\n${tr('terminal.structures')}: ${(structures ?? []).map((s) => s.sigla).join(', ')}`, { opId: ctx.opId });
  });
}

export function registerAppHandlers(): void {
  registerHandler('help', (op, ctx) => {
    const context: Context = window.location.hash.includes('/hea') ? 'hea' : 'crystalab';
    log('info', helpLines(context, op.topic), { opId: ctx.opId });
  });
  registerHandler('theme.set', (op, ctx) => {
    const prefs = usePreferences.getState();
    const next = op.theme ?? (effectiveTheme(prefs.theme) === 'dark' ? 'light' : 'dark');
    prefs.set({ theme: next });
    log('ok', tr(next === 'dark' ? 'cmd.ok.themeDark' : 'cmd.ok.themeLight'), { opId: ctx.opId });
  });
  registerHandler('locale.set', (op, ctx) => {
    usePreferences.getState().set({ locale: op.locale });
    log('ok', tr('cmd.ok.locale', { locale: op.locale }), { opId: ctx.opId });
  });
  registerHandler('module.open', (op) => {
    navigate(op.module);
  });
  registerHandler('op.cancel', () => {
    if (!cancelRunning()) log('warn', tr('cmd.ok.nothingRunning'));
  });
}
