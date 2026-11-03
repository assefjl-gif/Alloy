/**
 * Caderno de laboratório (6.13/6.14): registro de observações, hipóteses, cálculos e conclusões,
 * com a possibilidade de anexar a cena atual do CrystaLab (estrutura, parâmetros devolvidos pelo
 * motor, medições e link da cena). Rascunho salvo automaticamente; exportação em Markdown/JSON.
 */
import { useEffect, useMemo, useState } from 'react';
import { useI18n } from '../../i18n/index.ts';
import { useNotebook, readDraft, saveDraft, notesToMarkdown, type Note, type NoteKind } from './store.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useOverlays } from '../../stores/overlays.ts';
import { buildShareUrl } from '../../features/url/sceneUrl.ts';
import { downloadText } from '../../features/export/download.ts';
import { Button, IconButton } from '../../design-system/primitives/Button.tsx';
import { Select, TextArea, TextInput, Checkbox } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, CategoryTag } from '../../design-system/primitives/Category.tsx';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { Panel } from '../../design-system/layout/Panel.tsx';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { announce } from '../../design-system/announce.ts';
import { Dialog } from '../../design-system/primitives/Dialog.tsx';

const KINDS: NoteKind[] = ['observation', 'hypothesis', 'calculation', 'conclusion', 'free'];

export default function NotebookModule() {
  const { t, num, locale } = useI18n();
  const notes = useNotebook((s) => s.notes);
  const add = useNotebook((s) => s.add);
  const update = useNotebook((s) => s.update);
  const remove = useNotebook((s) => s.remove);
  const structure = useCrystalab((s) => s.structure);
  const request = useCrystalab((s) => s.request);
  const overlays = useOverlays((s) => s.items);
  const [draft, setDraft] = useState(readDraft);
  const [attach, setAttach] = useState(true);
  const [filter, setFilter] = useState<NoteKind | 'all'>('all');
  const [editing, setEditing] = useState<Note | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Note | null>(null);
  useEffect(() => { const h = setTimeout(() => saveDraft(draft), 400); return () => clearTimeout(h); }, [draft]);
  const labels = useMemo(() => Object.fromEntries(KINDS.map((k) => [k, t(`notebook.kind.${k}`)])) as Record<NoteKind, string>, [t]);
  const shown = filter === 'all' ? notes : notes.filter((n) => n.kind === filter);
  const dateFmt = useMemo(() => new Intl.DateTimeFormat(locale, { dateStyle: 'short', timeStyle: 'short' }), [locale]);

  const save = () => {
    if (!draft.body.trim() && !draft.title.trim()) return;
    const measurements = overlays.filter((o) => o.kind === 'measurement').map((o) => (o.kind === 'measurement' ? { label: o.label, value: o.data.type === 'distance' ? (o.data.valueNm != null ? `${num(o.data.valueNm, 4)} nm` : `${num(o.data.valueA ?? 0, 4)} a`) : `${num(o.data.degrees ?? 0, 2)}°` } : { label: '', value: '' }));
    const share = attach && structure ? buildShareUrl() : null;
    add({
      kind: draft.kind,
      title: draft.title.trim(),
      body: draft.body.trim(),
      ...(attach && structure && request ? {
        structure: { rotulo: structure.rotulo, estrutura: structure.estrutura, request: { ...request } },
        params: { R_nm: structure.raio_nm ?? '—', A_g_mol: structure.peso ?? '—', n: structure.n, a_nm: structure.a_nm, FEA: structure.fea, densidade_motor: structure.densidade ?? '—' },
        ...(measurements.length ? { measurements } : {}),
        ...(share && !share.truncated ? { sceneUrl: share.url } : {}),
      } : {}),
    });
    setDraft({ kind: draft.kind, title: '', body: '' });
    announce(t('notebook.saved'));
  };

  const editor = (
    <Panel title={t('notebook.new')} id="notebook-editor" testId="notebook-editor" className="ds-panel--padded">
      <form className="ds-stack" onSubmit={(e) => { e.preventDefault(); save(); }}>
        <Select label={t('notebook.type')} value={draft.kind} onChange={(e) => setDraft({ ...draft, kind: e.target.value as NoteKind })} options={KINDS.map((k) => ({ value: k, label: labels[k] }))} />
        <TextInput label={t('notebook.titleLabel')} value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} data-testid="note-title" />
        <TextArea label={t('notebook.body')} value={draft.body} rows={6} onChange={(e) => setDraft({ ...draft, body: e.target.value })} hint={t('notebook.draftHint')} data-testid="note-body" />
        <Checkbox label={structure ? t('notebook.attach', { name: structure.rotulo }) : t('notebook.attachNone')} checked={attach && Boolean(structure)} disabled={!structure} onChange={setAttach} />
        <Button type="submit" variant="primary" icon="check" data-testid="note-save">{t('notebook.save')}</Button>
      </form>
      <CategoryBox category="note"><p className="ds-field__hint">{t('notebook.localOnly')}</p></CategoryBox>
    </Panel>
  );

  return (
    <Workbench
      className="notebook"
      lab={editor}
      center={
        <main id="main-content" tabIndex={-1} className="module-main">
          <header className="module-head">
            <h1>{t('notebook.title')}</h1>
            <div className="ds-row">
              <Select hideLabel label={t('notebook.filter')} value={filter} onChange={(e) => setFilter(e.target.value as NoteKind | 'all')} options={[{ value: 'all', label: t('notebook.all') }, ...KINDS.map((k) => ({ value: k, label: labels[k] }))]} />
              <Button size="sm" icon="download" disabled={!notes.length} onClick={() => downloadText(notesToMarkdown(notes, labels), 'caderno-alloy.md', 'text/markdown')}>{t('notebook.exportMd')}</Button>
              <Button size="sm" icon="download" disabled={!notes.length} onClick={() => downloadText(JSON.stringify({ format: 'alloy-notebook', version: 1, notes }, null, 2), 'caderno-alloy.json', 'application/json')}>JSON</Button>
              <Button size="sm" icon="print" disabled={!notes.length} onClick={() => { document.documentElement.classList.add('print-report'); window.print(); document.documentElement.classList.remove('print-report'); }}>PDF</Button>
            </div>
          </header>
          {shown.length === 0 ? <p className="empty-state">{t('notebook.empty')}</p> : (
            <ol className="notes" data-testid="notes" aria-label={t('notebook.listLabel', { n: shown.length })}>
              {shown.map((n) => (
                <li key={n.id} className={`note note--${n.kind}`}>
                  <article aria-labelledby={`${n.id}-h`}>
                    <header className="note__head">
                      <CategoryTag category={n.kind === 'calculation' ? 'result' : n.kind === 'conclusion' ? 'feedback' : 'note'} label={labels[n.kind]} compact />
                      <h2 id={`${n.id}-h`} className="note__title">{n.title || labels[n.kind]}</h2>
                      <time dateTime={n.createdAt} className="note__time">{dateFmt.format(new Date(n.createdAt))}</time>
                      {n.createdOffline && !n.synced ? <Badge tone="warning">{t('notebook.offline')}</Badge> : null}
                      <IconButton size="sm" icon="pencil" label={t('notebook.edit')} onClick={() => setEditing(n)} />
                      <IconButton size="sm" icon="trash" label={t('notebook.delete')} onClick={() => setConfirmDelete(n)} />
                    </header>
                    <p className="note__body">{n.body}</p>
                    {n.image ? <img className="note__img" src={n.image} alt={t('notebook.imageAlt', { name: n.structure?.rotulo ?? n.title })} /> : null}
                    {n.structure ? (
                      <CategoryBox category="result" className="note__scene">
                        <p><strong lang="pt-BR">{n.structure.rotulo}</strong> · {n.structure.estrutura}</p>
                        {n.params ? <dl className="note__params">{Object.entries(n.params).map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{typeof v === 'number' ? num(v, 4) : (v ?? '—')}</dd></div>)}</dl> : null}
                        {n.measurements?.length ? <ul>{n.measurements.map((m, i) => <li key={i}>{m.label}: {m.value}</li>)}</ul> : null}
                        <p className="ds-field__hint">{t('notebook.engineValues')}</p>
                        {n.sceneUrl ? <a href={n.sceneUrl.slice(n.sceneUrl.indexOf('#'))} className="ds-btn ds-btn--ghost ds-btn--sm">{t('notebook.openScene')}</a> : null}
                      </CategoryBox>
                    ) : null}
                  </article>
                </li>
              ))}
            </ol>
          )}
          <Dialog open={Boolean(editing)} onClose={() => setEditing(null)} title={t('notebook.edit')} closeLabel={t('common.close')}
            footer={<><Button onClick={() => setEditing(null)}>{t('common.cancel')}</Button><Button variant="primary" onClick={() => { if (editing) update(editing.id, { title: editing.title, body: editing.body, kind: editing.kind }); setEditing(null); announce(t('notebook.saved')); }}>{t('notebook.save')}</Button></>}>
            {editing ? (
              <div className="ds-stack">
                <Select label={t('notebook.type')} value={editing.kind} onChange={(e) => setEditing({ ...editing, kind: e.target.value as NoteKind })} options={KINDS.map((k) => ({ value: k, label: labels[k] }))} />
                <TextInput label={t('notebook.titleLabel')} value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} />
                <TextArea label={t('notebook.body')} rows={6} value={editing.body} onChange={(e) => setEditing({ ...editing, body: e.target.value })} />
              </div>
            ) : null}
          </Dialog>
          <Dialog open={Boolean(confirmDelete)} onClose={() => setConfirmDelete(null)} title={t('notebook.deleteTitle')} closeLabel={t('common.close')} size="sm"
            footer={<><Button onClick={() => setConfirmDelete(null)}>{t('common.cancel')}</Button><Button variant="danger" onClick={() => { if (confirmDelete) remove(confirmDelete.id); setConfirmDelete(null); announce(t('notebook.deleted')); }} data-testid="note-confirm-delete">{t('notebook.delete')}</Button></>}>
            <p>{t('notebook.deleteBody')}</p>
          </Dialog>
        </main>
      }
    />
  );
}
