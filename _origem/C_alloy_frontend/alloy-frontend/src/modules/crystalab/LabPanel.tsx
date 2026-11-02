import { useMemo, useState } from 'react';
import { dispatch, submitLine } from '../../commands/bus.ts';
import { useI18n } from '../../i18n/index.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { Terminal } from '../../features/terminal/Terminal.tsx';
import { Disclosure } from '../../design-system/primitives/Disclosure.tsx';
import type { StructureRequest } from '../../services/api/contracts.ts';
import { plain } from '../../utils/text.ts';

interface BlockItem {
  key: string;
  name: string;
  tag: string;
  tagKey: string;
  formula: string;
  chips: string[];
  request: StructureRequest;
}

function useBlocks(): BlockItem[] {
  const metals = useCrystalab((s) => s.metals);
  const structures = useCrystalab((s) => s.structures);
  const { num, t } = useI18n();
  return useMemo(() => {
    const m = Object.entries(metals ?? {}).map(([symbol, metal]) => ({
      key: symbol,
      name: `${symbol} · ${metal.nome}`,
      tag: metal.estrutura,
      tagKey: metal.estrutura,
      formula: `R = ${num(metal.raio, 4)} nm · A = ${num(metal.peso, 2)} g/mol`,
      chips: [metal.estrutura, `NC ${metal.nc}`, `ρ ${num(metal.densidade_exp, 2)}`],
      request: { nome: symbol },
    }));
    const g = (structures ?? []).map((s) => ({
      key: `gen:${s.sigla}`,
      name: `${t('blocks.cell')} ${s.sigla}`,
      tag: t('blocks.generic'),
      tagKey: 'gen',
      formula: `${s.nome} · ${s.relacao}`,
      chips: [s.sigla, `NC ${s.nc}`, `n = ${s.n}`],
      request: { nome: s.sigla },
    }));
    return [...m, ...g];
  }, [metals, structures, num, t]);
}

function activeKey(): string {
  const r = useCrystalab.getState().structure;
  if (!r) return '';
  if (r.simbolo && !r.editado) return r.simbolo;
  if (r.generica && r.raio_nm === null) return `gen:${r.estrutura}`;
  return '';
}

export function BlockBank() {
  const { t } = useI18n();
  const blocks = useBlocks();
  const structure = useCrystalab((s) => s.structure);
  const status = useCrystalab((s) => s.catalogStatus);
  const [filter, setFilter] = useState('');
  const current = structure ? activeKey() : '';
  const shown = filter ? blocks.filter((b) => plain(`${b.name} ${b.tag} ${b.formula}`).includes(plain(filter))) : blocks;
  return (
    <div className="lab-section lab-blocks">
      <div className="lab-blocks__filter">
        <label htmlFor="block-filter" className="sr-only">{t('blocks.filter')}</label>
        <input id="block-filter" className="lab-input" type="search" placeholder={t('blocks.filterPlaceholder')} value={filter} onChange={(e) => setFilter(e.target.value)} />
      </div>
      <ul className="block-list" data-testid="block-list" aria-label={t('blocks.listLabel')} aria-busy={status === 'loading' || undefined}>
        {status === 'error' ? <li className="lab-empty">{t('blocks.unavailable')}</li> : null}
        {shown.map((b) => (
          <li key={b.key}>
            <button
              type="button"
              className={`alloy-block ${b.key === current ? 'is-active' : ''}`}
              data-key={b.key}
              aria-pressed={b.key === current}
              draggable
              onDragStart={(e) => { e.dataTransfer.setData('text/plain', b.key); e.dataTransfer.effectAllowed = 'copy'; }}
              onClick={() => void dispatch({ type: 'material.load', request: b.request }, 'block')}
            >
              <span className="block-head">
                <span className="block-name">{b.name}</span>
                <span className="block-tag" data-s={b.tagKey}>{b.tag}</span>
              </span>
              <span className="block-formula">{b.formula}</span>
              <span className="composition-strip">
                {b.chips.map((c) => <span key={c} className="element-chip">{c}</span>)}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function BlockCount() {
  const { t } = useI18n();
  const count = useBlocks().length;
  return <span className="count-pill" aria-label={t('blocks.count', { count })}>{count}</span>;
}

export function ParameterEditor() {
  const { t } = useI18n();
  const text = useCrystalab((s) => s.editorText);
  const structure = useCrystalab((s) => s.structure);
  const metals = useCrystalab((s) => s.metals);
  const [drop, setDrop] = useState(false);
  const label = structure ? (structure.simbolo ? `${structure.simbolo} · ${structure.estrutura}` : `${t('blocks.generic')} · ${structure.estrutura}`) : '—';
  return (
    <div className="lab-editor">
      <div className="lab-section__title">
        <h3 id="editor-title">{t('editor.title')}</h3>
        <span className="lab-current" aria-live="polite">{label}</span>
      </div>
      <label htmlFor="parameterEditor" className="sr-only">{t('editor.label')}</label>
      <textarea
        id="parameterEditor"
        className={`composition-editor ${drop ? 'is-drop-target' : ''}`}
        spellCheck={false}
        data-testid="parameter-editor"
        aria-describedby="editor-hint"
        value={text}
        onChange={(e) => useCrystalab.getState().set({ editorText: e.target.value })}
        onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void dispatch({ type: 'editor.apply' }, 'form'); } }}
        onDragOver={(e) => { e.preventDefault(); setDrop(true); }}
        onDragLeave={() => setDrop(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrop(false);
          const key = e.dataTransfer.getData('text/plain');
          if (!key) return;
          const request: StructureRequest = key.startsWith('gen:') ? { nome: key.slice(4) } : metals?.[key] ? { nome: key } : { nome: key };
          void dispatch({ type: 'material.load', request }, 'block');
        }}
      />
      <p id="editor-hint" className="lab-hint">{t('editor.hint')}</p>
    </div>
  );
}

export function LabPanel() {
  const { t } = useI18n();
  const shortcuts = [
    { label: t('shortcuts.density'), command: 'calcular densidade', tone: 'cyan' },
    { label: t('shortcuts.plane111'), command: 'plano 1 1 1', tone: 'green' },
    { label: t('shortcuts.direction110'), command: 'direcao 1 1 0', tone: 'amber' },
    { label: t('shortcuts.clear'), command: 'limpar', tone: 'gray' },
  ];
  return (
    <div className="lab">
      <header className="brand-row">
        <div>
          <p className="brand-row__title">{t('crystalab.brand')}</p>
          <p className="brand-row__sub">{t('crystalab.brandSub')}</p>
        </div>
        <span className="lab-badge">M1 · v2.0</span>
      </header>
      <Disclosure title={t('blocks.title')} className="lab-disclosure lab-disclosure--blocks" headingLevel={2} aside={<BlockCount />}>
        <BlockBank />
      </Disclosure>
      <Disclosure title={t('terminal.title')} className="lab-disclosure" headingLevel={2}>
        <section className="terminal-panel" aria-label={t('terminal.title')}>
          <ParameterEditor />
          <Terminal context="crystalab" placeholderKey="terminal.placeholder" shortcuts={shortcuts} />
        </section>
      </Disclosure>
    </div>
  );
}

export { submitLine };
