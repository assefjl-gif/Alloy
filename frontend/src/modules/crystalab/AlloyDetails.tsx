/**
 * Painéis novos da liga (R2-FE-01), a partir dos campos do contrato R1 §2.2:
 * composição solicitada × representada, realização estatística, natureza do modelo,
 * o que o motor NÃO verifica, fases desenhadas, sítios intersticiais, elementos puros
 * (dados tabelados) e convenções do desenho.
 *
 * Nada é calculado aqui: todo número, texto e rótulo de natureza vem da API. Valor ausente é
 * exibido como indisponível, com o motivo quando a API o informa — nunca como zero.
 */
import type { ReactNode } from 'react';
import { useI18n } from '../../i18n/index.ts';
import { natureLabel } from '../../i18n/nature.ts';
import type { AlloyResult } from '../../services/api/contracts.ts';
import { CategoryBox } from '../../design-system/primitives/Category.tsx';
import { Disclosure } from '../../design-system/primitives/Disclosure.tsx';
import { Badge } from '../../design-system/primitives/misc.tsx';
import { compositionPairs, drawnAtomCount, globalConclusion, uniqueAtomCount } from './alloyDisplay.ts';

/** Rótulo de um papel da API (`solvente`, `substitucional`, `intersticial`). */
const ROLE_KEYS: Record<string, 'alloy.role.base' | 'alloy.role.soluto' | 'alloy.role.intersticial'> = {
  solvente: 'alloy.role.base',
  substitucional: 'alloy.role.soluto',
  intersticial: 'alloy.role.intersticial',
};

/** Valores de `modelo` que a interface sabe nomear; o resto é mostrado como veio do motor. */
const MODEL_VALUES: readonly string[] = [
  'substitucional', 'intersticial', 'mista', 'desordenada', 'ordenada_prototipo', 'monofasica_imposta',
  'idealizada', 'estimativa_vegard_sobre_raios', 'derivado_de_R', 'medido', 'ideal', 'tabelado',
  'derivado_de_a_c_medidos', 'informado', 'estatistica', 'sem_soluto', 'imposta_pelo_modelo',
];

function modelValue(t: (k: 'alloy.model.value.medido') => string, value: string | null): string {
  if (!value) return '—';
  return MODEL_VALUES.includes(value) ? t(`alloy.model.value.${value}` as 'alloy.model.value.medido') : value;
}

/** Composição pedida × efetivamente representada, nas duas bases, com a contagem de átomos. */
export function AlloyCompositionPanel({ r }: { r: AlloyResult }) {
  const { t, num } = useI18n();
  const rows = compositionPairs(r);
  const c = r.composicao;
  if (!rows.length || !c) return null;
  const pct = (v: number | null) => (v === null ? t('hea.unavailable') : `${num(v, 2)} %`);
  return (
    <section aria-labelledby="alloy-comp-title" data-testid="alloy-composition">
      <h3 id="alloy-comp-title">{t('alloy.comp.title')}</h3>
      <div className="ds-table-wrap">
        <table className="ds-table">
          <caption className="sr-only">{t('alloy.comp.caption')}</caption>
          <thead>
            <tr>
              <th scope="col">{t('alloy.comp.element')}</th>
              <th scope="col">{t('alloy.comp.requestedAt')}</th>
              <th scope="col">{t('alloy.comp.representedAt')}</th>
              <th scope="col">{t('alloy.comp.requestedMass')}</th>
              <th scope="col">{t('alloy.comp.representedMass')}</th>
              <th scope="col">{t('alloy.comp.atoms')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.element}>
                <th scope="row">{row.element}<br /><span className="ds-field__hint">{t(ROLE_KEYS[row.papel] ?? 'alloy.role.soluto')}</span></th>
                <td>{pct(row.atRequested)}</td>
                <td>{pct(row.atRepresented)}</td>
                <td>{pct(row.massRequested)}</td>
                <td>{pct(row.massRepresented)}</td>
                <td>{row.atoms === null ? t('hea.unavailable') : row.atoms}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <dl className="guided__dl">
        <dt>{t('alloy.comp.basis')}</dt><dd>{t(`hea.comp.basis.${c.base_entrada}`)}</dd>
        <dt>{t('alloy.comp.counts')}</dt>
        <dd data-testid="alloy-counts">{t('alloy.comp.countsValue', { unique: uniqueAtomCount(r), drawn: drawnAtomCount(r), sites: c.n_sitios_rede, interstitials: c.n_intersticiais })}</dd>
        <dt>{t('alloy.comp.resolution')}</dt>
        <dd>{t('alloy.comp.resolutionValue', { pct: num(c.resolucao_at_pct, 3), dev: num(c.desvio_maximo_at_pct, 3) })}</dd>
      </dl>
      <p className="ds-field__hint">{t('alloy.comp.imagesNote')}</p>
    </section>
  );
}

/** Uma realização estatística entre muitas: semente, algoritmo e o aviso do motor. */
export function AlloyRealizationBox({ r }: { r: AlloyResult }) {
  const { t } = useI18n();
  const real = r.realizacao;
  if (!real) return null;
  return (
    <CategoryBox category="note" as="section" aria-labelledby="alloy-real-title" data-testid="alloy-realization">
      <h3 id="alloy-real-title">{t('alloy.realization.title')}</h3>
      <p lang="pt-BR">{real.aviso}</p>
      <p className="ds-field__hint">{t('alloy.realization.line', { type: modelValue(t, real.tipo), seed: real.semente, algorithm: real.algoritmo, n: real.n })}</p>
    </CategoryBox>
  );
}

/** Natureza do modelo: o que é idealizado e o que é parâmetro medido. */
export function AlloyModelBox({ r }: { r: AlloyResult }) {
  const { t } = useI18n();
  const m = r.modelo;
  if (!m) return null;
  return (
    <section aria-labelledby="alloy-model-title" data-testid="alloy-model">
      <h3 id="alloy-model-title">{t('alloy.model.title')}</h3>
      <dl className="guided__dl">
        <dt>{t('alloy.model.solutionType')}</dt><dd>{modelValue(t, m.tipo_solucao)}</dd>
        <dt>{t('alloy.model.ordering')}</dt><dd>{modelValue(t, m.ordenacao)}</dd>
        <dt>{t('alloy.model.phases')}</dt><dd>{modelValue(t, m.fases)}</dd>
        <dt>{t('alloy.model.geometry')}</dt><dd>{modelValue(t, m.geometria)}</dd>
        <dt>{t('alloy.model.latticeParam')}</dt><dd>{modelValue(t, m.parametro_rede)}</dd>
        <dt>{t('alloy.model.solventParam')}</dt><dd>{modelValue(t, m.parametro_rede_solvente)}</dd>
        {m.c_a ? <><dt>c/a</dt><dd>{modelValue(t, m.c_a)}</dd></> : null}
      </dl>
      <ul className="ds-stack">{m.hipoteses.map((h, i) => <li key={i} lang="pt-BR">{h}</li>)}</ul>
      {r.prototipo ? (
        <p lang="pt-BR" data-testid="alloy-prototype">
          {t('alloy.model.prototype', { sb: r.prototipo.strukturbericht, proto: r.prototipo.prototipo, lattice: r.prototipo.rede_ordenada })}
          {r.prototipo.observacao ? ` ${r.prototipo.observacao}` : ''}
        </p>
      ) : null}
    </section>
  );
}

/** O que o motor NÃO verifica: limite de solubilidade e fases secundárias. */
export function AlloyChecksBox({ r }: { r: AlloyResult }) {
  const { t } = useI18n();
  const v = r.verificacoes;
  if (!v) return null;
  return (
    <CategoryBox category="feedback" as="section" aria-labelledby="alloy-checks-title" data-testid="alloy-checks">
      <h3 id="alloy-checks-title">{t('alloy.checks.title')}</h3>
      <ul className="ds-stack">
        <li>
          <strong>{t('alloy.checks.solubility')}</strong>{' '}
          <Badge tone="warning">{v.limite_solubilidade.verificado ? t('alloy.checks.verified') : t('alloy.checks.notVerified')}</Badge>
          <br /><span lang="pt-BR">{v.limite_solubilidade.motivo}</span>
        </li>
        <li>
          <strong>{t('alloy.checks.secondaryPhases')}</strong>{' '}
          <Badge tone="warning">{v.fases_secundarias.previstas === null ? t('alloy.checks.notPredicted') : t('alloy.checks.verified')}</Badge>
          <br /><span lang="pt-BR">{v.fases_secundarias.motivo}</span>
        </li>
      </ul>
    </CategoryBox>
  );
}

/** Fases desenhadas (sempre uma em R1: a matriz imposta), com a fração indisponível e o motivo. */
export function AlloyPhasesPanel({ r }: { r: AlloyResult }) {
  const { t } = useI18n();
  const phases = r.fases ?? [];
  if (!phases.length) return null;
  return (
    <section aria-labelledby="alloy-phases-title" data-testid="alloy-phases">
      <h3 id="alloy-phases-title">{t('alloy.phases.title')}</h3>
      <ul className="ds-stack">
        {phases.map((p) => (
          <li key={p.id}>
            <strong>{p.estrutura}</strong> — <span lang="pt-BR">{p.nome}</span> ({modelValue(t, p.origem)})
            <br />
            <span className="ds-field__hint" lang="pt-BR">
              {p.fracao === null ? t('alloy.phases.fractionUnavailable', { reason: p.fracao_motivo ?? t('hea.unavailable') }) : t('alloy.phases.fraction', { value: String(p.fracao) })}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Sítios intersticiais ocupados, um por soluto intersticial. */
export function AlloySitesPanel({ r }: { r: AlloyResult }) {
  const { t, num } = useI18n();
  const sites = r.sitios ?? (r.sitio ? [r.sitio] : []);
  if (!sites.length) return null;
  return (
    <section aria-labelledby="alloy-sites-title" data-testid="alloy-sites">
      <h3 id="alloy-sites-title">{t('alloy.sites.title')}</h3>
      <ul className="ds-stack">
        {sites.map((s, i) => (
          <li key={`${s.nome}-${i}`}>
            <strong>{s.elemento ? `${s.elemento} · ` : ''}{s.nome}</strong>
            <br />
            <span className="ds-field__hint">
              {t('alloy.sites.line', { r: num(s.raio_nm, 4), nc: s.nc_txt ?? String(s.nc), perCell: s.sitios_por_celula ?? t('hea.unavailable'), factor: num(s.fator, 4) })}
            </span>
            {s.justificativa ? <><br /><span className="ds-field__hint" lang="pt-BR">{s.justificativa}</span></> : null}
            {s.padrao_verificado === false ? <><br /><Badge tone="warning">{t('alloy.sites.unverified')}</Badge></> : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Propriedades TABELADAS dos elementos puros — não são propriedades do átomo na liga. */
export function AlloyPureElementsPanel({ r }: { r: AlloyResult }) {
  const { t, num } = useI18n();
  const elements = r.elementos ?? [];
  if (!elements.length) return null;
  return (
    <Disclosure title={t('alloy.pure.title')} defaultOpen={false} headingLevel={3}>
      <p className="ds-field__hint">{t('alloy.pure.note')}</p>
      <div className="ds-table-wrap">
        <table className="ds-table" data-testid="alloy-pure-elements">
          <thead>
            <tr>
              <th scope="col">{t('alloy.comp.element')}</th>
              <th scope="col">R (nm)</th>
              <th scope="col">M (g/mol)</th>
              <th scope="col">{t('alloy.pure.structure')}</th>
              <th scope="col">{t('alloy.pure.dataState')}</th>
            </tr>
          </thead>
          <tbody>
            {elements.map((e) => (
              <tr key={e.simbolo}>
                <th scope="row">{e.simbolo}<br /><span className="ds-field__hint">{t(ROLE_KEYS[e.papel] ?? 'alloy.role.soluto')}</span></th>
                <td>{e.raio_nm === null ? t('hea.unavailable') : num(e.raio_nm, 4)}</td>
                <td>{e.massa_g_mol === null ? t('hea.unavailable') : num(e.massa_g_mol, 3)}</td>
                <td>{e.estrutura_elemento_puro ?? t('hea.unavailable')}</td>
                <td>{e.estado_do_dado}{e.fonte ? <><br /><span className="ds-field__hint" lang="pt-BR">{e.fonte}</span></> : null}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Disclosure>
  );
}

/**
 * Convenções do desenho (referencial de `pos`/`frac`, célula replicada e, no HC, qual célula
 * está na tela). Em HC ficam visíveis sem precisar abrir nada, por serem decisivas na leitura.
 */
export function AlloyConventions({ r }: { r: AlloyResult }) {
  const { t } = useI18n();
  const items = r.convencoes ?? [];
  if (!items.length) return null;
  const body = <ul className="ds-stack" data-testid="alloy-conventions">{items.map((c, i) => <li key={i} lang="pt-BR">{c}</li>)}</ul>;
  if (r.estrutura === 'HC') {
    return (
      <CategoryBox category="note" as="section" aria-labelledby="alloy-conv-title">
        <h3 id="alloy-conv-title">{t('alloy.conventions.title')}</h3>
        {body}
      </CategoryBox>
    );
  }
  return <Disclosure title={t('alloy.conventions.title')} defaultOpen={false} headingLevel={3}>{body}</Disclosure>;
}

/** Regras de Hume-Rothery por soluto (uma avaliação por par solvente–soluto). */
export function AlloyRulesPerSolute({ r, status }: { r: AlloyResult; status: (ok: boolean | null | undefined) => ReactNode }) {
  const { t } = useI18n();
  const groups = r.regras_por_soluto ?? [];
  const conclusion = globalConclusion(r);
  if (!groups.length) return null;
  return (
    <section aria-labelledby="alloy-rules-title" data-testid="alloy-rules-per-solute">
      <h3 id="alloy-rules-title">{t('alloy.rules')}</h3>
      {groups.map((g) => (
        <div key={g.soluto} className="ds-stack">
          <h4>{t('alloy.rulesFor', { solute: g.soluto, mode: t(g.modo === 'intersticial' ? 'alloy.role.intersticial' : 'alloy.role.soluto') })}</h4>
          <div className="ds-table-wrap">
            {/* com um só soluto o data-testid legado continua valendo (testes do v1.0 e E2E) */}
            <table className="ds-table" data-testid={groups.length === 1 ? 'alloy-rules' : undefined}>
              <thead><tr><th scope="col">{t('alloy.rule.criterion')}</th><th scope="col">{t('alloy.rule.value')}</th><th scope="col">{t('alloy.rule.status')}</th></tr></thead>
              <tbody>
                {g.regras.map((rule) => (
                  <tr key={`${g.soluto}-${rule.criterio}`}>
                    <th scope="row">{rule.criterio}</th>
                    <td lang="pt-BR">{rule.valor ?? '—'}<br /><span className="ds-field__hint">{rule.indisponivel ?? rule.detalhe}</span></td>
                    <td>{status(rule.ok)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {groups.length > 1 ? <p lang="pt-BR" className="ds-field__hint">{g.conclusao}</p> : null}
        </div>
      ))}
      <CategoryBox category="note" as="section" aria-label={t('alloy.conclusion')}>
        <h4>{t('alloy.conclusionGlobal')}</h4>
        <p lang="pt-BR" data-testid="alloy-conclusion">{conclusion.text ?? t('alloy.conclusionGlobalUnavailable', { reason: conclusion.reason ?? t('hea.unavailable') })}</p>
      </CategoryBox>
    </section>
  );
}

/** Natureza do resultado da liga, com o rótulo do vocabulário da API. */
export function AlloyNature({ classe }: { classe: string }) {
  const { t } = useI18n();
  return <span>{natureLabel(t, classe)}</span>;
}
