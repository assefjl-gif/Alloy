/**
 * Catálogo do design system alloy-ui (2.10–2.12): tokens, as seis categorias de informação
 * (+ nota), primitivos e estados. Serve de referência viva e de alvo dos testes de contraste.
 */
import { useState } from 'react';
import { useI18n } from '../../i18n/index.ts';
import { Button, IconButton, ToggleButton } from '../../design-system/primitives/Button.tsx';
import { Checkbox, Segmented, Select, Slider, TextArea, TextInput } from '../../design-system/primitives/Field.tsx';
import { CategoryBox, CategoryTag, DemoSeal, type InfoCategory } from '../../design-system/primitives/Category.tsx';
import { Badge, Kbd, Spinner } from '../../design-system/primitives/misc.tsx';
import { Tabs, TabPanel } from '../../design-system/primitives/Tabs.tsx';
import { Disclosure } from '../../design-system/primitives/Disclosure.tsx';
import { Menu } from '../../design-system/primitives/Menu.tsx';
import { Dialog } from '../../design-system/primitives/Dialog.tsx';
import { MetricCard } from '../../design-system/layout/MetricCard.tsx';
import { StepPanel } from '../../design-system/layout/StepPanel.tsx';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { toast } from '../../stores/toast.ts';
import { Formula } from '../../features/formula/Formula.tsx';

const CATEGORIES: InfoCategory[] = ['result', 'param', 'reference', 'control', 'feedback', 'demo', 'note'];
const SWATCHES = ['--color-bg', '--color-surface', '--color-surface-2', '--color-ink', '--color-muted', '--color-primary', '--color-accent', '--color-success', '--color-warning', '--color-danger', '--color-info', '--lab-bg', '--lab-accent', '--viewer-bg', '--site-vertice', '--site-centro', '--site-face'];

export default function CatalogModule() {
  const { t } = useI18n();
  const [tab, setTab] = useState('a');
  const [on, setOn] = useState(false);
  const [seg, setSeg] = useState<'x' | 'y' | 'z'>('x');
  const [slider, setSlider] = useState(2);
  const [check, setCheck] = useState(true);
  const [dialog, setDialog] = useState(false);
  return (
    <Workbench center={
      <main id="main-content" tabIndex={-1} className="module-main catalog" data-testid="catalog">
        <header className="module-head"><h1>{t('catalog.title')}</h1><p className="module-head__lead">{t('catalog.lead')}</p></header>

        <section aria-labelledby="cat-tokens" className="ds-stack">
          <h2 id="cat-tokens">{t('catalog.tokens')}</h2>
          <ul className="swatches">{SWATCHES.map((v) => <li key={v}><span className="swatch" style={{ background: `var(${v})` }} aria-hidden="true" /><code>{v}</code></li>)}</ul>
        </section>

        <section aria-labelledby="cat-categories" className="ds-stack">
          <h2 id="cat-categories">{t('catalog.categories')}</h2>
          <p className="ds-field__hint">{t('catalog.categoriesHint')}</p>
          <div className="catalog__cats">
            {CATEGORIES.map((c) => <CategoryBox key={c} category={c}><CategoryTag category={c} label={t(`category.${c}`)} /><p>{t(`catalog.cat.${c}`)}</p></CategoryBox>)}
          </div>
          <DemoSeal text={t('common.demo')} detail={t('catalog.demoSeal')} />
        </section>

        <section aria-labelledby="cat-buttons" className="ds-stack">
          <h2 id="cat-buttons">{t('catalog.buttons')}</h2>
          <div className="ds-row">
            <Button variant="primary">Primary</Button><Button>Secondary</Button><Button variant="ghost">Ghost</Button><Button variant="accent">Accent</Button><Button variant="danger">Danger</Button><Button variant="lab">Lab</Button><Button disabled>{t('catalog.disabled')}</Button>
            <IconButton icon="settings" label={t('settings.title')} />
            <ToggleButton pressed={on} onPressedChange={setOn}>{t('catalog.toggle')}</ToggleButton>
            <Menu label={t('catalog.menu')} items={[{ id: 'a', label: 'Item A', onSelect: () => toast({ tone: 'info', title: 'Item A' }) }, { id: 'b', label: 'Item B', disabled: true, disabledReason: t('catalog.disabledReason'), onSelect: () => undefined }]} />
          </div>
          <div className="ds-row"><Badge>neutral</Badge><Badge tone="info">info</Badge><Badge tone="success">success</Badge><Badge tone="warning">warning</Badge><Badge tone="danger">danger</Badge><Badge tone="accent">accent</Badge> <Kbd>Ctrl</Kbd>+<Kbd>K</Kbd> <Spinner label={t('common.loading')} /></div>
        </section>

        <section aria-labelledby="cat-fields" className="ds-stack">
          <h2 id="cat-fields">{t('catalog.fields')}</h2>
          <div className="catalog__fields">
            <TextInput label={t('catalog.text')} hint={t('catalog.hint')} defaultValue="0,1278" />
            <TextInput label={t('catalog.error')} error={t('catalog.errorText')} defaultValue="abc" />
            <Select label={t('catalog.select')} options={[{ value: 'cfc', label: 'CFC' }, { value: 'ccc', label: 'CCC' }]} />
            <TextArea label={t('catalog.textarea')} rows={2} />
            <Segmented name="cat-seg" label={t('catalog.segmented')} value={seg} onChange={setSeg} options={[{ value: 'x', label: 'X' }, { value: 'y', label: 'Y' }, { value: 'z', label: 'Z' }]} />
            <Slider label={t('catalog.slider')} min={1} max={4} value={slider} onChange={setSlider} valueText={`${slider}×${slider}×${slider}`} />
            <Checkbox label={t('catalog.checkbox')} checked={check} onChange={setCheck} />
          </div>
        </section>

        <section aria-labelledby="cat-layout" className="ds-stack">
          <h2 id="cat-layout">{t('catalog.layout')}</h2>
          <div className="metrics-row">
            <MetricCard label="ρ" value="8,89" unit="g/cm³" category="result" categoryLabel={t('category.result')} />
            <MetricCard label="R" value="0,1278" unit="nm" category="param" categoryLabel={t('category.param')} />
          </div>
          <StepPanel label={t('catalog.steps')} steps={[{ title: 'A', status: 'done' }, { title: 'B', status: 'current' }, { title: 'C', status: 'todo' }]} />
          <Tabs label={t('catalog.tabs')} idPrefix="cat-tabs" value={tab} onChange={setTab} items={[{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }]} />
          <TabPanel idPrefix="cat-tabs" id="a" active={tab === 'a'}><Formula tex="\rho = \dfrac{n\,A}{V_C\,N_A}" display label={t('density.formulaLabel')} /></TabPanel>
          <TabPanel idPrefix="cat-tabs" id="b" active={tab === 'b'}><p>B</p></TabPanel>
          <Disclosure title={t('catalog.disclosure')} headingLevel={3} defaultOpen={false}><p>{t('catalog.disclosureBody')}</p></Disclosure>
          <div className="ds-row">
            <Button onClick={() => setDialog(true)}>{t('catalog.openDialog')}</Button>
            <Button onClick={() => toast({ tone: 'success', title: t('catalog.toast') })}>{t('catalog.showToast')}</Button>
          </div>
          <Dialog open={dialog} onClose={() => setDialog(false)} title={t('catalog.dialog')} closeLabel={t('common.close')}><p>{t('catalog.dialogBody')}</p></Dialog>
        </section>
      </main>
    } />
  );
}
