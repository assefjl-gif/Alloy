/**
 * Paleta de comandos (4.6): Ctrl+K / ⌘K ou botão no cabeçalho. Busca aproximada em comandos,
 * materiais, estruturas, operações, exemplos, ações do viewer e recursos didáticos, agrupada por
 * categoria, com descrição e sintaxe. Tudo executa pelo MESMO barramento do terminal.
 */
import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { dispatch, submitLine } from '../../commands/bus.ts';
import { specsFor } from '../../commands/catalog.ts';
import type { Context, Operation } from '../../commands/types.ts';
import { Dialog } from '../../design-system/primitives/Dialog.tsx';
import { Icon, type IconName } from '../../design-system/Icon.tsx';
import { Kbd } from '../../design-system/primitives/misc.tsx';
import { useI18n, pick, type MessageKey } from '../../i18n/index.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useHea } from '../../modules/hea/store.ts';
import { fuzzyScore } from '../../utils/fuzzy.ts';
import { navigate, getRoute } from '../../app/router.ts';
import { ACTIVITIES } from '../../modules/didactics/bank.ts';

type Group = 'commands' | 'materials' | 'structures' | 'operations' | 'examples' | 'viewer' | 'didactic' | 'modules';

interface Entry {
  id: string;
  group: Group;
  title: string;
  detail: string;
  syntax?: string;
  icon: IconName;
  keywords: string;
  run: () => void;
}

const GROUP_ORDER: Group[] = ['operations', 'materials', 'structures', 'viewer', 'commands', 'examples', 'didactic', 'modules'];
const GROUP_KEYS: Record<Group, MessageKey> = { commands: 'palette.group.commands', materials: 'palette.group.materials', structures: 'palette.group.structures', operations: 'palette.group.operations', examples: 'palette.group.examples', viewer: 'palette.group.viewer', didactic: 'palette.group.didactic', modules: 'palette.group.modules' };

function useEntries(context: Context, close: () => void): Entry[] {
  const { t, locale } = useI18n();
  const metals = useCrystalab((s) => s.metals);
  const structures = useCrystalab((s) => s.structures);
  const alloys = useHea((s) => s.bootstrap?.alloys);
  return useMemo(() => {
    const runOp = (op: Operation) => () => { close(); void dispatch(op, 'palette'); };
    const runLine = (line: string) => () => { close(); void submitLine(line, context, 'palette'); };
    const out: Entry[] = [];
    const ops: Array<[string, MessageKey, IconName, Operation]> = [
      ['undo', 'history.undo', 'undo', { type: 'history.undo' }],
      ['redo', 'history.redo', 'redo', { type: 'history.redo' }],
      ['share', 'share.button', 'share', { type: 'share' }],
      ['density', 'density.show', 'calc', { type: 'density.show' }],
      ['png', 'export.format.png', 'camera', { type: 'export', format: 'png' }],
      ['pdf', 'export.format.pdf', 'print', { type: 'export', format: 'pdf' }],
      ['cif', 'export.format.cif', 'file', { type: 'export', format: 'cif' }],
      ['xyz', 'export.format.xyz', 'file', { type: 'export', format: 'xyz' }],
      ['save', 'workspace.save', 'download', { type: 'workspace.save' }],
      ['theme', 'palette.toggleTheme', 'moon', { type: 'theme.set' }],
      ['clear', 'cmd.desc.limpar', 'trash', { type: 'lab.clear' }],
    ];
    if (context === 'crystalab') for (const [id, key, icon, op] of ops) out.push({ id: `op-${id}`, group: 'operations', title: t(key), detail: '', icon, keywords: id, run: runOp(op) });
    if (context === 'hea') {
      out.push({ id: 'op-analyze', group: 'operations', title: t('hea.analyzeAlloy'), detail: '', icon: 'flask', keywords: 'analisar analyze', run: runOp({ type: 'hea.analyze' }) });
      out.push({ id: 'op-bridge', group: 'operations', title: t('bridge.title'), detail: '', icon: 'cube', keywords: 'crystalab cristalab abrir', run: runOp({ type: 'hea.toCrystalab' }) });
      for (const [key, a] of Object.entries(alloys ?? {})) out.push({ id: `alloy-${key}`, group: 'materials', title: a.nome, detail: Object.keys(a.composicao).join(' + '), syntax: `usar ${key}`, icon: 'flask', keywords: `${key} ${a.nome}`, run: runOp({ type: 'hea.load', key }) });
    }
    if (context === 'crystalab') {
      for (const [sym, m] of Object.entries(metals ?? {})) out.push({ id: `metal-${sym}`, group: 'materials', title: `${sym} · ${m.nome}`, detail: `${m.estrutura} · R = ${m.raio} nm`, syntax: `usar ${sym}`, icon: 'atom', keywords: `${sym} ${m.nome} ${m.estrutura}`, run: runOp({ type: 'material.load', request: { nome: sym } }) });
      for (const s of structures ?? []) out.push({ id: `struct-${s.sigla}`, group: 'structures', title: `${t('blocks.cell')} ${s.sigla}`, detail: `${s.nome} · ${s.relacao}`, syntax: `estrutura ${s.sigla}`, icon: 'cube', keywords: `${s.sigla} ${s.nome}`, run: runOp({ type: 'material.load', request: { nome: s.sigla } }) });
      const viewerOps: Array<[string, MessageKey, IconName, Operation]> = [
        ['rigid', 'view.atomMode.rigid', 'atom', { type: 'view.atoms', mode: 'rigid' }],
        ['reduced', 'view.atomMode.reduced', 'atom', { type: 'view.atoms', mode: 'reduced' }],
        ['ballstick', 'view.atomMode.ballstick', 'atom', { type: 'view.atoms', mode: 'ballstick' }],
        ['axes', 'view.toggle.axes', 'axes', { type: 'view.toggle', key: 'axes' }],
        ['edges', 'view.toggle.edges', 'cube', { type: 'view.toggle', key: 'edges' }],
        ['lattice', 'view.toggle.latticePoints', 'grid', { type: 'view.toggle', key: 'latticePoints' }],
        ['rotate', 'view.toggle.autoRotate', 'restart', { type: 'view.toggle', key: 'autoRotate' }],
        ['reset', 'view.reset', 'target', { type: 'view.reset' }],
        ['sc1', 'palette.supercell1', 'grid', { type: 'supercell.set', n: [1, 1, 1] }],
        ['sc2', 'palette.supercell2', 'grid', { type: 'supercell.set', n: [2, 2, 2] }],
        ['sc3', 'palette.supercell3', 'grid', { type: 'supercell.set', n: [3, 3, 3] }],
        ['dist', 'measure.distance', 'ruler', { type: 'measure.start', kind: 'distance' }],
        ['angle', 'measure.angle', 'angle', { type: 'measure.start', kind: 'angle' }],
      ];
      for (const [id, key, icon, op] of viewerOps) out.push({ id: `view-${id}`, group: 'viewer', title: t(key), detail: '', icon, keywords: id, run: runOp(op) });
      const anims: Array<[string, MessageKey, Operation]> = [
        ['abab', 'palette.animAbab', { type: 'animation.open', name: 'stacking', variant: 'abab' }],
        ['abcabc', 'palette.animAbcabc', { type: 'animation.open', name: 'stacking', variant: 'abcabc' }],
        ['ag', 'palette.animAlphaGamma', { type: 'animation.open', name: 'alpha-gamma' }],
        ['thermal', 'anim.thermal.title', { type: 'animation.open', name: 'thermal' }],
      ];
      for (const [id, key, op] of anims) out.push({ id: `anim-${id}`, group: 'didactic', title: t(key), detail: t('palette.animation'), icon: 'play', keywords: `${id} animacao empilhamento stacking apilamiento alfa gama ferro iron`, run: runOp(op) });
    }
    for (const a of ACTIVITIES) out.push({ id: `act-${a.id}`, group: 'didactic', title: pick(a.title, locale), detail: t(`didactic.format.${a.format}`), icon: 'book', keywords: `${a.id} ${a.topic}`, run: () => { close(); navigate('aprender', [a.id]); } });
    for (const spec of specsFor(context)) {
      out.push({ id: `cmd-${spec.verb}-${spec.category}`, group: 'commands', title: spec.verb, detail: t(spec.descriptionKey), syntax: spec.syntax, icon: 'terminal', keywords: `${spec.verb} ${spec.aliases.join(' ')}`, run: () => { close(); const el = document.getElementById(`term-input-${context}`) as HTMLInputElement | null; if (el) { el.focus(); const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set; setter?.call(el, `${spec.verb} `); el.dispatchEvent(new Event('input', { bubbles: true })); } } });
      for (const ex of spec.examples) out.push({ id: `ex-${ex}`, group: 'examples', title: ex, detail: t(spec.descriptionKey), syntax: spec.syntax, icon: 'arrowRight', keywords: ex, run: runLine(ex) });
    }
    const mods: Array<[Parameters<typeof navigate>[0], MessageKey, IconName]> = [['crystalab', 'nav.crystalab', 'cube'], ['hea', 'nav.hea', 'flask'], ['aprender', 'nav.learn', 'book'], ['diario', 'nav.notebook', 'notebook'], ['professor', 'nav.instructor', 'teacher'], ['catalogo', 'nav.catalog', 'grid'], ['sobre', 'nav.about', 'info'], ['conta', 'nav.account', 'lock']];
    for (const [m, key, icon] of mods) out.push({ id: `mod-${m}`, group: 'modules', title: t(key), detail: t('palette.openModule'), icon, keywords: m, run: () => { close(); navigate(m); } });
    return out;
  }, [context, metals, structures, alloys, t, locale, close]);
}

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useI18n();
  const route = getRoute();
  const context: Context = route.module === 'hea' ? 'hea' : 'crystalab';
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();
  const entries = useEntries(context, onClose);
  const results = useMemo(() => {
    const scored = entries
      .map((e) => ({ e, s: Math.max(fuzzyScore(query, e.title) * 1.6, fuzzyScore(query, `${e.keywords} ${e.syntax ?? ''} ${e.detail}`)) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s || GROUP_ORDER.indexOf(a.e.group) - GROUP_ORDER.indexOf(b.e.group))
      .slice(0, query ? 40 : 60)
      .map((x) => x.e);
    if (!query) scored.sort((a, b) => GROUP_ORDER.indexOf(a.group) - GROUP_ORDER.indexOf(b.group));
    return scored;
  }, [entries, query]);
  useEffect(() => { if (open) { setQuery(''); setActive(0); window.setTimeout(() => inputRef.current?.focus(), 20); } }, [open]);
  useEffect(() => setActive(0), [query]);
  useEffect(() => { document.getElementById(`${listId}-opt-${active}`)?.scrollIntoView({ block: 'nearest' }); }, [active, listId]);
  let lastGroup: Group | null = null;
  return (
    <Dialog open={open} onClose={onClose} title={t('palette.title')} closeLabel={t('common.close')} size="lg" className="palette">
      <div className="palette__search">
        <Icon name="search" size={18} />
        <label htmlFor="palette-input" className="sr-only">{t('palette.search')}</label>
        <input
          ref={inputRef}
          id="palette-input"
          data-testid="palette-input"
          className="palette__input"
          placeholder={t('palette.placeholder')}
          value={query}
          role="combobox"
          aria-expanded="true"
          aria-controls={listId}
          aria-activedescendant={results.length ? `${listId}-opt-${active}` : undefined}
          aria-autocomplete="list"
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => Math.min(results.length - 1, a + 1)); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => Math.max(0, a - 1)); }
            else if (e.key === 'Enter') { e.preventDefault(); results[active]?.run(); }
          }}
        />
        <Kbd>Esc</Kbd>
      </div>
      <p className="sr-only" aria-live="polite">{t('palette.count', { n: results.length })}</p>
      <ul id={listId} role="listbox" aria-label={t('palette.results')} className="palette__list">
        {results.map((e, i) => {
          const header = e.group !== lastGroup ? t(GROUP_KEYS[e.group]) : null;
          lastGroup = e.group;
          return (
            <li key={e.id} role="presentation">
              {header ? <div className="palette__group" role="presentation">{header}</div> : null}
              <div id={`${listId}-opt-${i}`} role="option" aria-selected={i === active} className={`palette__item ${i === active ? 'is-active' : ''}`} onMouseEnter={() => setActive(i)} onClick={() => e.run()} data-palette-id={e.id}>
                <Icon name={e.icon} size={16} />
                <span className="palette__text"><strong>{e.title}</strong>{e.detail ? <small>{e.detail}</small> : null}</span>
                {e.syntax ? <code>{e.syntax}</code> : null}
              </div>
            </li>
          );
        })}
      </ul>
      {!results.length ? <p className="ds-muted">{t('palette.none')}</p> : null}
      <p className="palette__foot"><Kbd>↑</Kbd> <Kbd>↓</Kbd> {t('palette.navigate')} · <Kbd>Enter</Kbd> {t('palette.run')} · <Kbd>Ctrl</Kbd>+<Kbd>K</Kbd> {t('palette.toggle')}</p>
    </Dialog>
  );
}
