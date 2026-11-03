import { useEffect, useMemo, useState } from 'react';
import { dispatch, submitLine } from '../../commands/bus.ts';
import { toCommand } from '../../commands/serialize.ts';
import type { Operation } from '../../commands/types.ts';
import { useI18n } from '../../i18n/index.ts';
import type { StructureCode, StructureRequest } from '../../services/api/contracts.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { commit } from '../../stores/history.ts';
import { atomKey, OVERLAY_PALETTE, useOverlays, type OverlayItem } from '../../stores/overlays.ts';
import { useViewer } from '../../stores/viewer.ts';
import { prefersReducedMotion, usePreferences } from '../../stores/preferences.ts';
import { Button, IconButton, ToggleButton } from '../../design-system/primitives/Button.tsx';
import { Select, TextInput, Segmented, Slider } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, CategoryTag, DemoSeal } from '../../design-system/primitives/Category.tsx';
import { Icon } from '../../design-system/Icon.tsx';
import { parseUserNumber } from '../../utils/format.ts';
import { spokenNotation } from '../../utils/text.ts';
import { buildAtoms } from '../../features/viewer3d/geometry.ts';
import { millerDetail } from '../../commands/handlers.ts';
import { alphaGammaData, loadAlphaGamma } from '../../features/viewer3d/alphaGamma.ts';
import type { StructureResult } from '../../services/api/contracts.ts';

const SITE_KEYS = { vertice: 'site.vertice', centro: 'site.centro', face: 'site.face', basal: 'site.basal', interior: 'site.interior' } as const;

/** Mostra o comando equivalente de um formulário (4.8), com botão para levá-lo ao terminal. */
function Equivalent({ op }: { op: Operation | null }) {
  const { t } = useI18n();
  const cmd = op ? toCommand(op) : null;
  return (
    <div className="equivalent" aria-live="polite">
      <span className="ds-label">{t('guided.equivalent')}</span>
      {cmd ? <code data-testid="equivalent-command">{cmd}</code> : <span className="ds-muted">{t('guided.noEquivalent')}</span>}
      {cmd ? (
        <button type="button" className="ds-link-btn" onClick={() => { const el = document.getElementById('term-input-crystalab') as HTMLInputElement | null; if (el) { el.focus(); const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set; setter?.call(el, cmd); el.dispatchEvent(new Event('input', { bubbles: true })); } }}>
          {t('guided.toTerminal')}
        </button>
      ) : null}
    </div>
  );
}

function num(text: string): number | undefined {
  const v = parseUserNumber(text);
  return v === null || Number.isNaN(v) ? undefined : v;
}

/** Modo guiado (4.7): as operações principais sem digitar comandos. */
export function GuidedMode() {
  const { t } = useI18n();
  const metals = useCrystalab((s) => s.metals);
  const structure = useCrystalab((s) => s.structure);
  const [kind, setKind] = useState<'metal' | 'generic'>('metal');
  const [metal, setMetal] = useState('Cu');
  const [override, setOverride] = useState<'' | StructureCode>('');
  const [code, setCode] = useState<StructureCode>('CFC');
  const [r, setR] = useState('');
  const [a, setA] = useState('');
  const [ca, setCa] = useState('');
  const [tipo, setTipo] = useState<'plano' | 'direcao'>('plano');
  const [idx, setIdx] = useState(['1', '1', '1', '']);

  const loadOp = useMemo<Operation>(() => {
    const req: StructureRequest = kind === 'metal' ? { nome: metal } : { nome: code };
    if (kind === 'metal' && override) req.estrutura = override;
    const rv = num(r); const av = num(a); const cav = num(ca);
    if (rv !== undefined) req.raio = rv;
    if (av !== undefined) req.peso = av;
    if (cav !== undefined && (kind === 'generic' ? code === 'HC' : true)) req.c_a = cav;
    return { type: 'material.load', request: req };
  }, [kind, metal, override, code, r, a, ca]);

  const indices = idx.filter((v, i) => i < 3 || v.trim() !== '').map((v) => Number(v.trim()));
  const millerValid = indices.length >= 3 && indices.every((v) => Number.isInteger(v));
  const millerOp: Operation | null = millerValid ? { type: 'miller.draw', tipo, indices } : null;

  return (
    <div className="guided" data-testid="guided-mode">
      <CategoryBox category="param" as="section" className="guided__card" aria-labelledby="g-material">
        <h3 id="g-material"><span className="guided__num">1</span>{t('guided.chooseMaterial')}</h3>
        <Segmented label={t('guided.source')} name="g-kind" value={kind} onChange={setKind} options={[{ value: 'metal', label: t('guided.metal') }, { value: 'generic', label: t('guided.genericCell') }]} size="sm" />
        {kind === 'metal' ? (
          <>
            <Select label={t('guided.metal')} value={metal} onChange={(e) => setMetal(e.target.value)} options={Object.entries(metals ?? {}).map(([s, m]) => ({ value: s, label: `${s} · ${m.nome} (${m.estrutura})` }))} />
            <Select label={t('guided.structureOverride')} hint={t('guided.structureOverrideHint')} value={override} onChange={(e) => setOverride(e.target.value as '' | StructureCode)} options={[{ value: '', label: t('guided.keepStructure') }, { value: 'CS', label: 'CS' }, { value: 'CCC', label: 'CCC' }, { value: 'CFC', label: 'CFC' }, { value: 'HC', label: 'HC' }]} />
          </>
        ) : (
          <Select label={t('guided.structure')} value={code} onChange={(e) => setCode(e.target.value as StructureCode)} options={[{ value: 'CS', label: 'CS' }, { value: 'CCC', label: 'CCC' }, { value: 'CFC', label: 'CFC' }, { value: 'HC', label: 'HC' }]} />
        )}
        <div className="guided__grid">
          <TextInput label={t('guided.radius')} hint="0,02–0,5 nm" inputMode="decimal" value={r} onChange={(e) => setR(e.target.value)} placeholder={kind === 'metal' ? t('guided.fromTable') : '0,128'} />
          <TextInput label={t('guided.mass')} hint="1–300 g/mol" inputMode="decimal" value={a} onChange={(e) => setA(e.target.value)} placeholder={kind === 'metal' ? t('guided.fromTable') : '63,55'} />
          {(kind === 'generic' && code === 'HC') || (kind === 'metal' && (override === 'HC' || (!override && metals?.[metal]?.estrutura === 'HC'))) ? (
            <TextInput label="c/a" hint="1,0–2,5" inputMode="decimal" value={ca} onChange={(e) => setCa(e.target.value)} placeholder="1,633" />
          ) : null}
        </div>
        <Equivalent op={loadOp} />
        <Button variant="primary" icon="cube" data-testid="guided-load" onClick={() => void dispatch(loadOp, 'form')}>{t('guided.load')}</Button>
      </CategoryBox>

      <CategoryBox category="result" as="section" className="guided__card" aria-labelledby="g-review">
        <h3 id="g-review"><span className="guided__num">2</span>{t('guided.review')}</h3>
        {structure ? (
          <dl className="guided__dl">
            <dt>{t('metrics.structure')}</dt><dd lang="pt-BR">{`${structure.estrutura_nome} (${structure.estrutura})`}</dd>
            <dt>{t('guided.material')}</dt><dd lang="pt-BR">{structure.rotulo}</dd>
            <dt>n · NC</dt><dd>{`${structure.n} · ${structure.nc}`}</dd>
            <dt>R</dt><dd>{structure.raio_nm !== null ? `${structure.raio_nm} nm` : t('guided.inUnitsOfR')}</dd>
          </dl>
        ) : <p className="ds-muted">{t('guided.noStructureYet')}</p>}
      </CategoryBox>

      <CategoryBox category="result" as="section" className="guided__card" aria-labelledby="g-density">
        <h3 id="g-density"><span className="guided__num">3</span>{t('guided.density')}</h3>
        <p className="ds-muted">{t('guided.densityHelp')}</p>
        <Equivalent op={{ type: 'density.show' }} />
        <Button icon="calc" data-testid="guided-density" disabled={!structure} onClick={() => void dispatch({ type: 'density.show' }, 'form')}>{t('density.show')}</Button>
      </CategoryBox>

      <CategoryBox category="param" as="section" className="guided__card" aria-labelledby="g-miller">
        <h3 id="g-miller"><span className="guided__num">4</span>{t('guided.miller')}</h3>
        <Segmented label={t('miller.kind')} name="g-tipo" value={tipo} onChange={setTipo} size="sm" options={[{ value: 'plano', label: t('miller.planeHkl') }, { value: 'direcao', label: t('miller.directionUvw') }]} />
        <div className="guided__indices" role="group" aria-label={t('miller.indices')}>
          {(structure?.estrutura === 'HC' ? [0, 1, 2, 3] : [0, 1, 2]).map((i) => (
            <TextInput
              key={i}
              label={(tipo === 'plano' ? (structure?.estrutura === 'HC' ? ['h', 'k', 'i', 'l'] : ['h', 'k', 'l']) : (structure?.estrutura === 'HC' ? ['u', 'v', 't', 'w'] : ['u', 'v', 'w']))[i] ?? ''}
              inputMode="numeric"
              value={idx[i] ?? ''}
              onChange={(e) => setIdx((cur) => cur.map((v, j) => (j === i ? e.target.value : v)))}
              className="guided__index"
            />
          ))}
        </div>
        {structure?.estrutura === 'HC' ? <p className="ds-field__hint">{t('guided.hcHint')}</p> : null}
        <Equivalent op={millerOp} />
        <Button icon="plane" data-testid="guided-miller" disabled={!structure || !millerOp} onClick={() => { if (millerOp) void dispatch(millerOp, 'form'); }}>{tipo === 'plano' ? t('guided.drawPlane') : t('guided.drawDirection')}</Button>
      </CategoryBox>
    </div>
  );
}

function overlayTitle(o: OverlayItem, t: ReturnType<typeof useI18n>['t']): string {
  if (o.kind === 'plane') return `${t('miller.plane')} ${o.data.notacao}`;
  if (o.kind === 'direction') return `${t('miller.direction')} ${o.data.notacao}`;
  if (o.kind === 'measurement') return `${t(o.data.type === 'distance' ? 'measure.distance' : 'measure.angle')} ${o.label}`;
  return o.text;
}

/** Gerenciador de overlays (4.9): visibilidade, cor acessível, seleção/destaque, corte, remoção individual. */
export function OverlayManager() {
  const { t } = useI18n();
  const items = useOverlays((s) => s.items);
  const selectedId = useOverlays((s) => s.selectedId);
  const display = useViewer((s) => s.display);
  const update = (id: string, patch: Partial<OverlayItem>, label: string) => {
    const s = useOverlays.getState();
    s.set({ items: s.items.map((i) => (i.id === id ? ({ ...i, ...patch } as OverlayItem) : i)) });
    commit(label);
  };
  return (
    <div className="ovm" data-testid="overlay-manager">
      <ul className="ovm__list" aria-label={t('overlays.managerLabel')}>
        <li className="ovm__item ovm__item--axes">
          <span className="ovm__shape" aria-hidden="true"><Icon name="axes" size={16} /></span>
          <span className="ovm__title">{t('view.axes')}</span>
          <ToggleButton size="sm" pressed={display.axes} onPressedChange={(v) => void dispatch({ type: 'view.toggle', key: 'axes', value: v }, 'form')} aria-label={t('overlays.visibility', { name: t('view.axes') })}>{display.axes ? t('common.visible') : t('common.hidden')}</ToggleButton>
        </li>
        {items.map((o) => {
          const title = overlayTitle(o, t);
          const spoken = o.kind === 'plane' || o.kind === 'direction' ? spokenNotation(title, t('a11y.minus')) : title;
          return (
            <li key={o.id} className={`ovm__item ${o.id === selectedId ? 'is-selected' : ''}`} data-overlay-kind={o.kind}>
              <span className={`ovm__shape ovm__shape--${o.kind}`} style={{ color: o.color }} aria-hidden="true" />
              <button type="button" className="ovm__title ds-link-btn" aria-pressed={o.id === selectedId} aria-label={t('overlays.select', { name: spoken })} onClick={() => useOverlays.getState().set({ selectedId: o.id === selectedId ? null : o.id })}>
                {title}
              </button>
              {o.kind === 'plane' || o.kind === 'direction' ? <span className="ovm__detail">{millerDetail(o.data)}</span> : null}
              <div className="ovm__actions">
                <IconButton size="sm" icon={o.visible ? 'eye' : 'eyeOff'} label={t(o.visible ? 'overlays.hide' : 'overlays.show', { name: spoken })} aria-pressed={o.visible} onClick={() => update(o.id, { visible: !o.visible }, o.visible ? 'ocultar' : 'mostrar')} />
                {o.kind === 'plane' ? (
                  <IconButton size="sm" icon="scissors" label={t(o.clip ? 'overlays.unclip' : 'overlays.clip', { name: spoken })} aria-pressed={o.clip} onClick={() => update(o.id, { clip: !o.clip }, o.clip ? 'sem corte' : 'corte')} />
                ) : null}
                <IconButton size="sm" icon="trash" label={t('overlays.remove', { name: spoken })} onClick={() => { const s = useOverlays.getState(); s.set({ items: s.items.filter((i) => i.id !== o.id), selectedId: s.selectedId === o.id ? null : s.selectedId }); commit(`remover ${o.label}`); }} />
              </div>
              <fieldset className="ovm__colors">
                <legend className="sr-only">{t('overlays.color', { name: spoken })}</legend>
                {OVERLAY_PALETTE.map((c, i) => (
                  <label key={c} className={`ovm__swatch ${o.color === c ? 'is-on' : ''}`} style={{ background: c }}>
                    <input type="radio" name={`color-${o.id}`} checked={o.color === c} onChange={() => update(o.id, { color: c }, 'cor')} />
                    <span className="sr-only">{t('overlays.colorN', { n: i + 1 })}</span>
                  </label>
                ))}
              </fieldset>
            </li>
          );
        })}
      </ul>
      {!items.length ? <p className="ds-muted">{t('overlays.emptyManager')}</p> : null}
      <p className="ds-field__hint">{t('overlays.familiesDisabled')}</p>
    </div>
  );
}

/** Painel do átomo (3.8) + lista navegável por teclado de todos os átomos desenhados (7.3). */
export function AtomInspector() {
  const { t, num, locale } = useI18n();
  const r = useCrystalab((s) => s.structure);
  const supercell = useViewer((s) => s.supercell);
  const selection = useViewer((s) => s.selection);
  const atoms = useMemo(() => (r ? buildAtoms(r, supercell) : []), [r, supercell]);
  if (!r) return <p className="ds-muted">{t('viewer.empty')}</p>;
  const atom = selection ? r.atomos[selection.index] : null;
  const isReplica = selection ? selection.cell.some((c) => c !== 0) : false;
  const base = selection && r.base ? r.base[selection.index] : null;
  const pos = atom ? atom.pos : null;
  return (
    <div className="atom-inspector" data-testid="atom-inspector">
      {atom && selection && pos ? (
        <CategoryBox category="result" as="section" className="atom-card" aria-live="polite">
          <h3>{t('atom.title', { n: selection.index + 1 })}</h3>
          <dl className="guided__dl">
            <dt>{t('atom.element')}</dt><dd>{r.simbolo ?? t('atom.generic')}</dd>
            <dt>{t('atom.site')}</dt><dd>{t(SITE_KEYS[atom.tipo])}</dd>
            <dt>{t('atom.positionA')}</dt><dd className="ds-mono">({pos.map((v) => num(v, 3)).join('; ')})</dd>
            <dt>{t('atom.fractional')}</dt>
            <dd className="ds-mono">{r.estrutura === 'HC' ? (base?.frac ? `(${base.frac.map((v) => num(v, 3)).join('; ')})` : <span className="ds-muted">{t('atom.fracUnavailable')}</span>) : `(${pos.map((v) => num(v, 3)).join('; ')})`}</dd>
            <dt>{t('atom.cartesianNm')}</dt><dd className="ds-mono">{r.a_nm !== null ? `(${pos.map((v) => num(v * (r.a_nm as number), 4)).join('; ')}) nm` : t('atom.needsRadius')}</dd>
            <dt>{t('atom.contribution')}</dt><dd>{isReplica ? t('atom.replica') : `${atom.fracao_txt} ${t('atom.ofAtom')}`}</dd>
            <dt>{t('atom.material')}</dt><dd lang="pt-BR">{`${r.rotulo} · ${r.estrutura}`}</dd>
            {isReplica ? <><dt>{t('atom.cell')}</dt><dd>{selection.cell.join(', ')}</dd></> : null}
          </dl>
          <p className="ds-field__hint">{r.estrutura === 'HC' ? t('atom.noteHc') : t('atom.noteCubic')}</p>
          <Button size="sm" onClick={() => useViewer.getState().set({ selection: null })}>{t('atom.clear')}</Button>
        </CategoryBox>
      ) : <p className="ds-muted">{t('atom.none')}</p>}
      <h3 className="atom-list__title" id="atom-list-title">{t('atom.listTitle', { count: atoms.length })}</h3>
      <ul className="atom-list" role="listbox" aria-labelledby="atom-list-title" tabIndex={0} aria-activedescendant={selection ? `atom-opt-${atomKey(selection).replace(/[@,]/g, '_')}` : undefined}
        onKeyDown={(e) => {
          if (!atoms.length) return;
          const cur = selection ? atoms.findIndex((a) => a.key === atomKey(selection)) : -1;
          let next = cur;
          if (e.key === 'ArrowDown') next = Math.min(atoms.length - 1, cur + 1);
          else if (e.key === 'ArrowUp') next = Math.max(0, cur - 1);
          else if (e.key === 'Home') next = 0;
          else if (e.key === 'End') next = atoms.length - 1;
          else if (e.key === 'Escape') { useViewer.getState().set({ selection: null }); return; }
          else return;
          e.preventDefault();
          const a = atoms[next];
          if (a) useViewer.getState().set({ selection: a.ref });
          document.getElementById(`atom-opt-${(a?.key ?? '').replace(/[@,]/g, '_')}`)?.scrollIntoView({ block: 'nearest' });
        }}
      >
        {atoms.map((a) => (
          <li key={a.key} id={`atom-opt-${a.key.replace(/[@,]/g, '_')}`} role="option" aria-selected={selection ? atomKey(selection) === a.key : false} className={`atom-opt ${a.replica ? 'is-replica' : ''}`} onClick={() => useViewer.getState().set({ selection: a.ref })}>
            <i className={`dot dot--${a.tipo}`} aria-hidden="true" />
            <span>{`#${a.ref.index + 1}${a.replica ? ` @${a.ref.cell.join('')}` : ''} · ${t(SITE_KEYS[a.tipo])}`}</span>
            <span className="ds-mono">({a.pos.map((v) => new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(v)).join('; ')})</span>
            {a.replica ? <span className="atom-opt__tag">{t('atom.replicaShort')}</span> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function MeasurementsPanel() {
  const { t } = useI18n();
  const tool = useViewer((s) => s.tool);
  const r = useCrystalab((s) => s.structure);
  const items = useOverlays((s) => s.items).filter((i) => i.kind === 'measurement');
  return (
    <div className="measure-panel" data-testid="measure-panel">
      <div className="ds-row">
        <Button icon="ruler" disabled={!r} aria-pressed={tool?.kind === 'distance'} onClick={() => void dispatch({ type: 'measure.start', kind: 'distance' }, 'form')}>{t('measure.distance')}</Button>
        <Button icon="angle" disabled={!r} aria-pressed={tool?.kind === 'angle'} onClick={() => void dispatch({ type: 'measure.start', kind: 'angle' }, 'form')}>{t('measure.angle')}</Button>
        {tool ? <Button variant="ghost" onClick={() => void dispatch({ type: 'measure.stop' }, 'form')}>{t('measure.finish')}</Button> : null}
      </div>
      <p className="ds-field__hint">{t('measure.howTo')}</p>
      <form className="measure-form" onSubmit={(e) => { e.preventDefault(); const f = new FormData(e.currentTarget); void submitLine(`medir ${String(f.get('kind'))} ${String(f.get('atoms'))}`, 'crystalab', 'form'); }}>
        <label className="sr-only" htmlFor="measure-kind">{t('measure.kind')}</label>
        <select id="measure-kind" name="kind" className="ds-input"><option value="distancia">{t('measure.distance')}</option><option value="angulo">{t('measure.angle')}</option></select>
        <label className="sr-only" htmlFor="measure-atoms">{t('measure.atomsField')}</label>
        <input id="measure-atoms" name="atoms" className="ds-input" placeholder="1 9" />
        <Button type="submit" size="sm">{t('measure.byNumber')}</Button>
      </form>
      <ul className="ovm__list">
        {items.map((m) => m.kind === 'measurement' ? (
          <li key={m.id} className="ovm__item">
            <span className="ovm__shape ovm__shape--measurement" style={{ color: m.color }} aria-hidden="true" />
            <span className="ovm__title">{`${t(m.data.type === 'distance' ? 'measure.distance' : 'measure.angle')} ${m.data.atoms.map((a) => `#${a.index + 1}`).join('–')}: ${m.label}`}</span>
            <IconButton size="sm" icon="trash" label={t('overlays.remove', { name: m.label })} onClick={() => { const s = useOverlays.getState(); s.set({ items: s.items.filter((i) => i.id !== m.id) }); commit('remover medição'); }} />
          </li>
        ) : null)}
      </ul>
      <p className="ds-field__hint">{t('measure.geometryNote')}</p>
    </div>
  );
}

/** Animações didáticas (3.14–3.17) com reproduzir/pausar/reiniciar/passo e texto explicativo. */
export function AnimationsPanel() {
  const { t } = useI18n();
  const animation = useViewer((s) => s.animation);
  const motion = usePreferences((s) => s.motion);
  const reduce = prefersReducedMotion(motion);
  const set = (patch: Partial<NonNullable<typeof animation>>) => { const a = useViewer.getState().animation; if (a) useViewer.getState().set({ animation: { ...a, ...patch } }); };
  const max = animation?.name === 'stacking' ? 5 : 10;
  return (
    <div className="anim-panel" data-testid="animations-panel">
      <div className="ds-row">
        <Button size="sm" icon="stack" aria-pressed={animation?.name === 'stacking' && animation.variant === 'abab'} onClick={() => void dispatch({ type: 'animation.open', name: 'stacking', variant: 'abab' }, 'form')}>ABAB</Button>
        <Button size="sm" icon="stack" aria-pressed={animation?.name === 'stacking' && animation.variant === 'abcabc'} onClick={() => void dispatch({ type: 'animation.open', name: 'stacking', variant: 'abcabc' }, 'form')}>ABCABC</Button>
        <Button size="sm" icon="swap" aria-pressed={animation?.name === 'alpha-gamma'} onClick={() => void dispatch({ type: 'animation.open', name: 'alpha-gamma' }, 'form')}>α → γ (Fe)</Button>
        <Button size="sm" icon="thermometer" aria-pressed={animation?.name === 'thermal'} onClick={() => void dispatch({ type: 'animation.open', name: 'thermal' }, 'form')}>{t('anim.thermal.title')}</Button>
      </div>
      {animation ? (
        <>
          <div className="anim-controls" role="group" aria-label={t('anim.controls')}>
            <IconButton icon={animation.playing ? 'pause' : 'play'} label={animation.playing ? t('anim.pause') : t('anim.play')} disabled={reduce} onClick={() => set({ playing: !animation.playing, ...(animation.step >= max ? { step: 0 } : {}) })} />
            <IconButton icon="stepBack" label={t('anim.stepBack')} onClick={() => set({ step: Math.max(0, animation.step - 1), playing: false })} />
            <IconButton icon="step" label={t('anim.stepForward')} onClick={() => set({ step: Math.min(max, animation.step + 1), playing: false })} />
            <IconButton icon="restart" label={t('anim.restart')} onClick={() => set({ step: 0, playing: false })} />
            <IconButton icon="close" label={t('anim.close')} onClick={() => useViewer.getState().set({ animation: null })} />
          </div>
          {reduce ? <p className="ds-field__hint">{t('anim.reducedMotion')}</p> : null}
          <Slider label={t('anim.step')} min={0} max={max} value={animation.step} onChange={(v) => set({ step: v, playing: false })} valueText={`${animation.step} / ${max}`} />
          <AnimationExplainer name={animation.name} variant={animation.variant} step={animation.step} />
        </>
      ) : <p className="ds-muted">{t('anim.choose')}</p>}
    </div>
  );
}

function AnimationExplainer({ name, variant, step }: { name: string; variant: string; step: number }) {
  const { t } = useI18n();
  if (name === 'stacking') {
    const seq = variant === 'abab' ? 'ABABAB' : 'ABCABC';
    return (
      <CategoryBox category="demo" as="section" className="anim-explainer" aria-live="polite">
        <DemoSeal text={t('common.illustrative')} detail={t('anim.illustrativeDetail')} />
        <p><strong>{t('anim.layers', { shown: seq.slice(0, step + 1).split('').join(' · '), total: seq.length })}</strong></p>
        <dl>
          <dt>{t('anim.changes')}</dt><dd>{t('anim.stacking.changes')}</dd>
          <dt>{t('anim.stays')}</dt><dd>{t('anim.stacking.stays')}</dd>
          <dt>{t('anim.observe')}</dt><dd>{t(variant === 'abab' ? 'anim.stacking.observeAbab' : 'anim.stacking.observeAbcabc')}</dd>
        </dl>
        <cite>CAL9 §3.12, p. 75 · {t('anim.pending', { id: 'D-13' })}</cite>
      </CategoryBox>
    );
  }
  if (name === 'alpha-gamma') return <AlphaGammaExplainer step={step} />;
  return (
    <CategoryBox category="demo" as="section" className="anim-explainer">
      <DemoSeal text={t('common.illustrative')} detail={t('anim.thermal.detail')} />
      <dl>
        <dt>{t('anim.changes')}</dt><dd>{t('anim.thermal.changes')}</dd>
        <dt>{t('anim.stays')}</dt><dd>{t('anim.thermal.stays')}</dd>
        <dt>{t('anim.observe')}</dt><dd>{t('anim.thermal.observe')}</dd>
      </dl>
      <cite>{t('anim.pending', { id: 'D-07' })}</cite>
    </CategoryBox>
  );
}

function AlphaGammaExplainer({ step }: { step: number }) {
  const { t, num } = useI18n();
  const [data, setData] = useState(alphaGammaData());
  useEffect(() => {
    let alive = true;
    loadAlphaGamma().then(() => { if (alive) setData(alphaGammaData()); }).catch(() => undefined);
    return () => { alive = false; };
  }, []);
  const row = (r: StructureResult | null, label: string) => r ? (
    <tr><th scope="row">{label}</th><td>{r.estrutura}</td><td>{r.a_nm !== null ? num(r.a_nm, 4) : '—'}</td><td>{r.n}</td><td>{num(r.fea, 3)}</td><td>{r.densidade !== null ? num(r.densidade, 3) : '—'}</td></tr>
  ) : null;
  return (
    <CategoryBox category="result" as="section" className="anim-explainer" aria-live="polite">
      <p><strong>{step === 0 ? t('anim.ag.alpha') : step >= 10 ? t('anim.ag.gamma') : t('anim.ag.mixing', { pct: step * 10 })}</strong></p>
      <div className="ds-table-wrap">
        <table className="ds-table">
          <caption className="sr-only">{t('anim.ag.caption')}</caption>
          <thead><tr><th scope="col">{t('anim.ag.phase')}</th><th scope="col">{t('metrics.structure')}</th><th scope="col">a (nm)</th><th scope="col">n</th><th scope="col">{t('metrics.apf')}</th><th scope="col">ρ (g/cm³)</th></tr></thead>
          <tbody>{row(data.from, 'α-Fe')}{row(data.to, 'γ-Fe')}</tbody>
        </table>
      </div>
      <dl>
        <dt>{t('anim.changes')}</dt><dd>{t('anim.ag.changes')}</dd>
        <dt>{t('anim.stays')}</dt><dd>{t('anim.ag.stays')}</dd>
        <dt>{t('anim.observe')}</dt><dd>{t('anim.ag.observe')}</dd>
      </dl>
      <p className="interp-warn" role="note">{t('anim.ag.warning')}</p>
      <cite>CAL9 §3.6, p. 55 · ASK6 §3-4, p. 72 · CR-02</cite>
      <CategoryTag category="result" label={t('category.result')} />
    </CategoryBox>
  );
}
