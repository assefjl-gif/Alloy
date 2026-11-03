/**
 * Sobre / estado do sistema: capacidades detectadas dos motores, matriz de disponibilidade
 * offline (7.12), registro de pendências e créditos/bibliografia do projeto.
 */
import { useI18n, pick } from '../../i18n/index.ts';
import { useCapabilities, useServiceMode } from '../../stores/capabilities.ts';
import { config } from '../../config.ts';
import { PENDING } from '../../services/adapters/pending.ts';
import { FEATURE_AVAILABILITY } from '../../features/pwa/availability.ts';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { Button } from '../../design-system/primitives/Button.tsx';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { detectEngines } from '../../app/boot.ts';

export default function AboutModule() {
  const { t, locale } = useI18n();
  const caps = useCapabilities();
  const clMode = useServiceMode('crystalab');
  const heaMode = useServiceMode('hea');
  const tone = (m: string) => (m === 'live' ? 'success' : m === 'demo' ? 'warning' : 'danger') as 'success' | 'warning' | 'danger';
  return (
    <Workbench center={
      <main id="main-content" tabIndex={-1} className="module-main about" data-testid="about">
        <header className="module-head"><h1>{t('about.title')}</h1><p className="module-head__lead">{t('about.lead')}</p></header>
        <section aria-labelledby="about-engines" className="ds-stack">
          <h2 id="about-engines">{t('about.engines')}</h2>
          <div className="ds-table-wrap"><table className="ds-table">
            <thead><tr><th scope="col">{t('about.service')}</th><th scope="col">{t('about.mode')}</th><th scope="col">{t('about.detail')}</th></tr></thead>
            <tbody>
              <tr><th scope="row">CrystaLab</th><td><Badge tone={tone(clMode)}>{t(`mode.${clMode}`)}</Badge></td><td>{caps.crystalab ? `${t(`about.api.${caps.crystalab.api}`)}${caps.crystalab.engineVersion ? ` · ${caps.crystalab.engineVersion}` : ''} · ${config.apiBase}` : t('engine.checking')}</td></tr>
              <tr><th scope="row">HEA</th><td><Badge tone={tone(heaMode)}>{t(`mode.${heaMode}`)}</Badge></td><td>{caps.hea?.available ? config.apiBase : t('about.heaMissing')}</td></tr>
              <tr><th scope="row">{t('about.exportCif')}</th><td>{caps.crystalab?.exportFormats.length ? <Badge tone="success">{caps.crystalab.exportFormats.join(', ').toUpperCase()}</Badge> : <Badge tone="danger">{t('mode.disabled')}</Badge>}</td><td>D-05</td></tr>
              <tr><th scope="row">{t('about.classroom')}</th><td><Badge tone="warning">{t('mode.demo')}</Badge></td><td>D-03</td></tr>
              <tr><th scope="row">{t('ai.title')}</th><td><Badge tone="danger">{t('mode.disabled')}</Badge></td><td>D-08</td></tr>
            </tbody>
          </table></div>
          <Button size="sm" icon="restart" onClick={() => void detectEngines()}>{t('about.recheck')}</Button>
        </section>
        <section aria-labelledby="about-offline" className="ds-stack">
          <h2 id="about-offline">{t('about.offline')}</h2>
          <ul className="avail-grid">
            {FEATURE_AVAILABILITY.map((f) => <li key={f.id}><span>{t(`feature.${f.id as 'shell'}`)}</span> <Badge tone={f.availability === 'local' ? 'success' : f.availability === 'online' ? 'info' : 'warning'}>{t(`availability.${f.availability}`)}</Badge></li>)}
          </ul>
        </section>
        <section aria-labelledby="about-pending" className="ds-stack">
          <h2 id="about-pending">{t('settings.pending')}</h2>
          <div className="ds-table-wrap"><table className="ds-table">
            <thead><tr><th scope="col">ID</th><th scope="col">{t('about.item')}</th><th scope="col">{t('about.behavior')}</th></tr></thead>
            <tbody>{PENDING.map((d) => <tr key={d.id}><th scope="row">{d.id}</th><td>{pick(d.title, locale)}</td><td>{pick(d.behavior, locale)}</td></tr>)}</tbody>
          </table></div>
        </section>
        <section aria-labelledby="about-refs" className="ds-stack">
          <h2 id="about-refs">{t('about.references')}</h2>
          <ul>
            <li>CAL9 — CALLISTER JR., W. D.; RETHWISCH, D. G. <cite>Ciência e Engenharia de Materiais: Uma Introdução</cite>. 9. ed. Rio de Janeiro: LTC, 2016.</li>
            <li>ASK6 — ASKELAND, D. R.; FULAY, P. P.; WRIGHT, W. J. <cite>The Science and Engineering of Materials</cite>. 6th ed. Stamford: Cengage Learning, 2011.</li>
          </ul>
          <p className="ds-field__hint">{t('about.refsNote')}</p>
        </section>
        <p className="ds-field__hint">{t('about.version', { version: config.version, build: config.buildId })}</p>
      </main>
    } />
  );
}
