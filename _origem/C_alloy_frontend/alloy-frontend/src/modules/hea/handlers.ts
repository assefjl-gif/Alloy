/**
 * Handlers do módulo HEA (sintaxe do HEA Virtual Lab v1.17) e da ponte para o CrystaLab.
 */
import { registerHandler, tr } from '../../commands/bus.ts';
import { applyStructure, loadStructure } from '../../commands/handlers.ts';
import { navigate } from '../../app/router.ts';
import { announce } from '../../design-system/announce.ts';
import { analyzeHea } from '../../services/api/hea.ts';
import { analyzeDemo } from '../../services/adapters/heaDemo.ts';
import { serviceMode } from '../../stores/capabilities.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { commit } from '../../stores/history.ts';
import { log, useTerminal } from '../../stores/terminal.ts';
import { useViewer } from '../../stores/viewer.ts';
import { compositionToText, parseComposition, useHea } from './store.ts';
import { createTransfer, matchStructure } from './transfer.ts';
import { persistTransfer } from './transferUrl.ts';

function markEdited(fallback: string): void {
  const h = useHea.getState();
  let name = h.name;
  if (!h.userNamed) {
    if (fallback === 'Liga modificada' && h.name && !h.name.includes('editada')) name = `${h.name} editada`;
    else name = fallback;
  }
  h.set({ selectedKey: '', name });
}

async function analyzeCurrent(signal: AbortSignal, opId: string, running: () => void): Promise<void> {
  const h = useHea.getState();
  const composition = parseComposition(h.editorText);
  if (Object.keys(composition).length < 2) throw new Error(tr('cmd.err.heaTwoElements'));
  const mode = serviceMode('hea');
  if (mode === 'disabled') throw new Error(tr('hea.disabled'));
  running();
  h.set({ status: 'loading', error: null });
  try {
    const name = h.name || tr('hea.userAlloy');
    const result = mode === 'live' ? await analyzeHea(name, composition, signal) : analyzeDemo(name, composition);
    useHea.getState().set({ result, resultOrigin: mode === 'live' ? 'engine' : 'demo', status: 'ready' });
    const stable = result.veredito.toUpperCase().startsWith('ESTÁVEL');
    log(stable ? 'ok' : 'error', `${tr('hea.analysisDone')}: ${result.veredito}${mode === 'demo' ? ` [${tr('common.demo')}]` : ''}`, { opId });
    announce(tr('hea.analysisAnnounce', { name: result.nome, verdict: result.veredito }));
  } catch (err) {
    useHea.getState().set({ status: 'error', error: err instanceof Error ? err.message : String(err) });
    throw err;
  }
}

export function registerHeaHandlers(): void {
  registerHandler('hea.load', async (op, ctx) => {
    const h = useHea.getState();
    const alloy = h.bootstrap?.alloys[op.key];
    if (!alloy) throw new Error(tr('cmd.err.unknownAlloy', { text: op.key }));
    h.set({ selectedKey: op.key, name: alloy.nome, userNamed: false, editorText: compositionToText(alloy.composicao) });
    log('ok', `${tr('hea.blockLoaded')}: ${alloy.nome}`, { opId: ctx.opId });
    await analyzeCurrent(ctx.signal, ctx.opId, () => ctx.running('cmd.run.hea'));
  });
  registerHandler('hea.set', async (op, ctx) => {
    useHea.getState().set({ editorText: compositionToText(op.composition) });
    markEdited(tr('hea.userAlloy'));
    await analyzeCurrent(ctx.signal, ctx.opId, () => ctx.running('cmd.run.hea'));
  });
  registerHandler('hea.add', async (op, ctx) => {
    const h = useHea.getState();
    const c = parseComposition(h.editorText);
    c[op.element] = (c[op.element] ?? 0) + op.amount;
    h.set({ editorText: compositionToText(c) });
    markEdited('Liga modificada');
    log('ok', tr('hea.elementUpdated', { el: op.element }), { opId: ctx.opId });
    await analyzeCurrent(ctx.signal, ctx.opId, () => ctx.running('cmd.run.hea'));
  });
  registerHandler('hea.remove', async (op, ctx) => {
    const h = useHea.getState();
    const c = parseComposition(h.editorText);
    delete c[op.element];
    h.set({ editorText: compositionToText(c) });
    markEdited('Liga modificada');
    log('ok', tr('hea.elementRemoved', { el: op.element }), { opId: ctx.opId });
    await analyzeCurrent(ctx.signal, ctx.opId, () => ctx.running('cmd.run.hea'));
  });
  registerHandler('hea.name', (op, ctx) => {
    useHea.getState().set({ name: op.name, userNamed: true });
    log('ok', tr('hea.nameSet', { name: op.name }), { opId: ctx.opId });
  });
  registerHandler('hea.analyze', (_op, ctx) => analyzeCurrent(ctx.signal, ctx.opId, () => ctx.running('cmd.run.hea')));
  registerHandler('hea.normalize', (_op, ctx) => {
    // Normalização da composição digitada (recurso do HEA v1.17, preservado): reescala as quantidades informadas pelo usuário.
    const h = useHea.getState();
    const c = parseComposition(h.editorText);
    const total = Object.values(c).reduce((s, v) => s + v, 0);
    if (total <= 0) throw new Error(tr('hea.nothingToNormalize'));
    const out = Object.fromEntries(Object.entries(c).map(([e, v]) => [e, (v / total) * 100]));
    h.set({ editorText: compositionToText(out) });
    log('ok', tr('hea.normalized'), { opId: ctx.opId });
  });
  registerHandler('hea.clear', (_op, ctx) => {
    useHea.getState().set({ editorText: '', name: tr('hea.userAlloy'), userNamed: false, selectedKey: '' });
    log('ok', tr('hea.editorCleared'), { opId: ctx.opId });
  });
  registerHandler('hea.toCrystalab', async (op, ctx) => {
    const h = useHea.getState();
    const result = h.result;
    if (!result || !h.resultOrigin) throw new Error(tr('bridge.noResult'));
    const match = matchStructure(result);
    if (!match.code && !op.choice) {
      const options = (match.candidates.length ? match.candidates : (['CFC', 'CCC', 'HC', 'CS'] as const)).map((code) => ({ label: tr('bridge.chooseOption', { code }), command: `cristalab ${code}` }));
      const prompt = tr(match.candidates.length ? 'bridge.ambiguousPhase' : 'bridge.noStructure', { phase: result.fase });
      log('warn', prompt, { opId: ctx.opId });
      useTerminal.getState().set({ pendingChoice: { prompt, choices: [...options] } });
      return;
    }
    const seed = (result as { demo_seed?: number }).demo_seed ?? null;
    const transfer = createTransfer(result, h.resultOrigin, seed, op.choice);
    ctx.running('cmd.run.structure');
    const request = { nome: transfer.structure.code };
    const structure = await loadStructure(request, ctx.signal);
    if (!structure) return;
    applyStructure(structure, request, { keepHea: true });
    useCrystalab.getState().set({ heaTransfer: transfer });
    useViewer.getState().set({ elementColoring: null });
    commit(`HEA → ${transfer.structure.code}`);
    log('ok', tr('bridge.opened', { name: result.nome, code: transfer.structure.code, basis: tr(`bridge.basis.${transfer.structure.basis}`) }), { opId: ctx.opId });
    navigate('crystalab', [], { h: persistTransfer(transfer) });
  });
}
