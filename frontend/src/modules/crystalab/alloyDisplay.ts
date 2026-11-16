/**
 * Lógica de EXIBIÇÃO da liga (R2-FE-01). Nenhuma grandeza científica é calculada aqui: as
 * contagens, as porcentagens nas duas bases e os rótulos de natureza vêm da API
 * (POST /api/v1/crystallography/solid-solutions, contrato R1 §2.2 e §2.3).
 *
 * Regra de contagem (V-8 do contrato): `n_soluto` e `n_solvente` passaram a contar átomos
 * ÚNICOS; as esferas desenhadas (`atomos`) incluem imagens periódicas de fronteira
 * (`imagem: true`), que não entram em contagem, composição, massa nem legenda.
 */
import type { AlloyAtom, AlloyResult } from '../../services/api/contracts.ts';
import { alloyAtomId } from '../../features/viewer3d/alloyScene.ts';
import { alloyClasses, displayCounts, isVisible, type DisplayCounts, type VisibilityFilter } from '../../features/viewer3d/visibility.ts';

export interface CompositionPairRow {
  element: string;
  papel: string;
  /** % atômica pedida pelo usuário */
  atRequested: number | null;
  /** % atômica efetivamente representada na supercélula */
  atRepresented: number | null;
  massRequested: number | null;
  massRepresented: number | null;
  /** átomos ÚNICOS deste elemento (pode ser 0) */
  atoms: number | null;
}

/**
 * Uma linha por elemento, na ordem canônica do motor (solvente, substitucionais, intersticiais),
 * com a composição SOLICITADA ao lado da REPRESENTADA. Valor ausente fica `null` (nunca 0).
 */
export function compositionPairs(r: Pick<AlloyResult, 'composicao'>): CompositionPairRow[] {
  const c = r.composicao;
  if (!c) return [];
  const represented = new Map(c.representada.map((item) => [item.elemento, item]));
  const rows: CompositionPairRow[] = c.solicitada.map((req) => {
    const rep = represented.get(req.elemento);
    return {
      element: req.elemento,
      papel: req.papel,
      atRequested: req.at_pct,
      atRepresented: rep ? rep.at_pct : null,
      massRequested: req.massa_pct,
      massRepresented: rep ? rep.massa_pct : null,
      atoms: rep?.n_atomos ?? null,
    };
  });
  // elemento que só aparece na composição representada (não deve ocorrer, mas não se omite dado)
  for (const rep of c.representada) {
    if (!rows.some((row) => row.element === rep.elemento)) {
      rows.push({
        element: rep.elemento,
        papel: rep.papel,
        atRequested: null,
        atRepresented: rep.at_pct,
        massRequested: null,
        massRepresented: rep.massa_pct,
        atoms: rep.n_atomos ?? null,
      });
    }
  }
  return rows;
}

/** Átomos ÚNICOS: da API quando houver; senão, as esferas que não são imagem periódica. */
export function uniqueAtomCount(r: Pick<AlloyResult, 'composicao' | 'atomos'>): number {
  if (r.composicao) return r.composicao.n_atomos_unicos;
  return r.atomos.filter((a) => a.imagem !== true).length;
}

/** Esferas desenhadas (únicos + imagens periódicas). */
export function drawnAtomCount(r: Pick<AlloyResult, 'composicao' | 'atomos'>): number {
  return r.composicao?.n_desenhados ?? r.atomos.length;
}

/** Verdadeiro quando a resposta traz imagens periódicas (a legenda precisa avisar). */
export function hasPeriodicImages(atoms: AlloyAtom[]): boolean {
  return atoms.some((a) => a.imagem === true);
}

/** Átomos únicos (sem imagem periódica): base de qualquer contagem feita na interface. */
export function uniqueAtoms(atoms: AlloyAtom[]): AlloyAtom[] {
  return atoms.filter((a) => a.imagem !== true);
}

/** Conclusão de solubilidade do sistema: texto global, ou o motivo de não haver um. */
export function globalConclusion(r: Pick<AlloyResult, 'conclusao_global' | 'conclusao' | 'indisponiveis'>): { text: string | null; reason: string | null } {
  if (r.conclusao_global) return { text: r.conclusao_global, reason: null };
  if (r.conclusao_global === null || r.conclusao_global === undefined) {
    const reason = r.indisponiveis?.['conclusao_global'] ?? null;
    if (reason) return { text: null, reason };
  }
  return { text: r.conclusao, reason: null };
}

export interface AbsentSolute {
  element: string;
  papel: string;
  /** % atômica pedida pelo usuário (como a API a devolveu em `composicao.solicitada`) */
  atRequested: number | null;
}

/**
 * Solutos PEDIDOS que a realização estatística não representou: `n_atomos === 0` na composição
 * representada (D-R2-3 / achado T-21). Zero é o resultado correto da amostragem honesta do motor
 * — aqui só se identifica o caso para que a interface o diga em voz alta, com a ação possível.
 * Nada é calculado: a contagem vem de `composicao.representada[].n_atomos`.
 */
export function absentSolutes(r: Pick<AlloyResult, 'composicao'>): AbsentSolute[] {
  if (!r.composicao) return [];
  return compositionPairs(r)
    .filter((row) => row.papel !== 'solvente' && row.atoms === 0)
    .map((row) => ({ element: row.element, papel: row.papel, atRequested: row.atRequested }));
}

/** Átomos ÚNICOS de um elemento na composição representada (da API; `null` se ela não vier). */
export function representedAtomsOf(r: Pick<AlloyResult, 'composicao'>, element: string): number | null {
  const item = r.composicao?.representada.find((c) => c.elemento === element);
  return item?.n_atomos ?? null;
}

// --------------------------------------------------------------- exibição da cena (R2-FE-03)

/** Átomo da liga como a cena o vê: identidade do motor, classes de filtro e visibilidade. */
export interface AlloyAtomView {
  atom: AlloyAtom;
  /** `id` do motor (ou a posição na lista desenhada, se o motor não enviou `id`) */
  id: string;
  index: number;
  image: boolean;
  /** ocupação (`ocupacao`) e sítio (`sitio.nome`) do motor; `null` quando a resposta não os traz */
  occupancy: string | null;
  site: string | null;
  visible: boolean;
}

/**
 * Uma visão por esfera desenhada, na ordem em que o motor as devolveu, com a visibilidade do
 * filtro de EXIBIÇÃO (T-23). A ordem e a identidade são do motor: o front não reordena nem renomeia.
 */
export function alloyAtomViews(atoms: AlloyAtom[], filter: VisibilityFilter): AlloyAtomView[] {
  return atoms.map((atom, index) => {
    const classes = alloyClasses(atom);
    return {
      atom,
      index,
      id: alloyAtomId(atom, index),
      image: atom.imagem === true,
      ...classes,
      visible: isVisible({ pos: atom.pos, element: atom.elemento, ...classes }, filter),
    };
  });
}

/** Contagem de EXIBIÇÃO (nunca científica) do que está desenhado agora. */
export function alloyDisplayCounts(views: AlloyAtomView[]): DisplayCounts {
  return displayCounts(views.map((v) => ({ element: v.atom.elemento, image: v.image, visible: v.visible })));
}

/** Elementos na ordem canônica do motor (solvente, substitucionais, intersticiais). */
export function alloyElementOptions(r: Pick<AlloyResult, 'composicao' | 'atomos'>): string[] {
  const fromEngine = r.composicao?.representada.map((c) => c.elemento) ?? [];
  const out = [...fromEngine];
  for (const a of r.atomos) if (!out.includes(a.elemento)) out.push(a.elemento);
  return out;
}

/** Ocupações presentes, na ordem em que o motor as nomeou (sem lista fixa no front). */
export function alloyOccupationOptions(atoms: AlloyAtom[]): string[] {
  const out: string[] = [];
  for (const a of atoms) { const k = alloyClasses(a).occupancy; if (k && !out.includes(k)) out.push(k); }
  return out;
}

/** Sítios cristalográficos presentes, na ordem em que o motor os nomeou. */
export function alloySiteOptions(atoms: AlloyAtom[]): string[] {
  const out: string[] = [];
  for (const a of atoms) { const k = alloyClasses(a).site; if (k && !out.includes(k)) out.push(k); }
  return out;
}

/** Visão de um átomo pelo `id` do motor. */
export function alloyAtomViewById(views: AlloyAtomView[], id: string | null): AlloyAtomView | null {
  if (!id) return null;
  return views.find((v) => v.id === id) ?? null;
}

/** Dados TABELADOS do elemento puro devolvidos pelo motor (`elementos`), ou `null`. */
export function pureElementOf(r: Pick<AlloyResult, 'elementos'>, element: string): NonNullable<AlloyResult['elementos']>[number] | null {
  return r.elementos?.find((e) => e.simbolo === element) ?? null;
}
