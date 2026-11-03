/**
 * Implementação DEMONSTRATIVA do motor HEA (pendência D-01: hea_engine.py ausente).
 * Todos os números são fictícios, gerados com semente fixa a partir do nome e da
 * composição, apenas para exercitar a interface. A UI rotula cada valor como demonstrativo.
 * Nada aqui usa fórmulas termodinâmicas: não há "cálculo" — há placeholders reproduzíveis.
 */
import { createRng, hashSeed } from '../../utils/rng.ts';
import type { HeaAlloy, HeaBootstrap, HeaReference, HeaResult } from '../api/contracts.ts';

export const HEA_DEMO_SEED = 20261021;

export const HEA_DEMO_ALLOYS: Record<string, HeaAlloy> = {
  demo_a: { nome: 'Liga demonstrativa A', grupo: 'demo', composicao: { Fe: 20, Ni: 20, Cr: 20, Co: 20, Mn: 20 } },
  demo_b: { nome: 'Liga demonstrativa B', grupo: 'demo', composicao: { Al: 15, Fe: 25, Ni: 25, Cr: 20, Co: 15 } },
  demo_c: { nome: 'Liga demonstrativa C', grupo: 'demo', composicao: { Ti: 25, Zn: 15, Mg: 20, Co: 40 } },
  demo_d: { nome: 'Liga demonstrativa D', grupo: 'demo', composicao: { Mo: 25, W: 25, Cr: 25, Fe: 25 } },
};

/** Fases fixas por liga demo para cobrir os dois ramos da regra de correspondência (Etapa 5). */
const DEMO_PHASES: Record<string, string> = {
  'Liga demonstrativa A': 'CFC',
  'Liga demonstrativa B': 'CFC + CCC',
  'Liga demonstrativa C': 'HC',
  'Liga demonstrativa D': 'CCC',
};

export const HEA_DEMO_REFERENCE: HeaReference = { dS: 10, omega: 5, delta: 3, VEC: 7, dH: -5, T_padrao: '298,15 K (demo)', P_padrao: '1 atm (demo)' };

function round(v: number, d = 3): number {
  const f = 10 ** d;
  return Math.round(v * f) / f;
}

export function analyzeDemo(name: string, composition: Record<string, number>): HeaResult {
  const elements = Object.keys(composition).sort();
  const seed = hashSeed(`${HEA_DEMO_SEED}|${name}|${elements.map((e) => `${e}:${composition[e]}`).join(',')}`);
  const rng = createRng(seed);
  const total = elements.reduce((s, e) => s + (composition[e] ?? 0), 0) || 1;
  const comp_percent = Object.fromEntries(elements.map((e) => [e, round(((composition[e] ?? 0) / total) * 100, 2)]));
  const fase = DEMO_PHASES[name] ?? rng.pick(['CFC', 'CCC', 'CFC + CCC', 'HC']);
  // Curva fictícia: passeio aleatório decrescente, SEM ΔG = ΔH − TΔS.
  let g = rng.range(-6000, 2000);
  const gibbs = Array.from({ length: 28 }, (_, i) => {
    g -= rng.range(400, 2600);
    return { T: 300 + i * 100, G: round(g, 0) };
  });
  const stable = rng.next() > 0.35;
  return {
    nome: name,
    veredito: stable ? 'ESTÁVEL (valor demonstrativo)' : 'RISCO DE INTERMETÁLICOS (valor demonstrativo)',
    fase,
    ductilidade: rng.pick(['Alta', 'Média', 'Baixa']),
    dureza: rng.pick(['Baixa', 'Média', 'Alta']),
    dureza_indice: rng.int(20, 90),
    dS: round(rng.range(6, 15)),
    dH: round(rng.range(-18, 4)),
    delta: round(rng.range(1, 8)),
    omega: round(rng.range(0.6, 12)),
    VEC: round(rng.range(4.5, 8.8)),
    Tm: round(rng.range(1200, 2600), 0),
    comp_percent,
    interpretacao: [
      'Resultado DEMONSTRATIVO: o motor HEA (hea_engine) não está disponível neste ambiente.',
      `Os valores acima são fictícios, gerados com a semente ${seed} para testar a interface. Não use para conclusões.`,
    ],
    fragilidade: null,
    gibbs,
    demo_seed: seed,
  } as HeaResult;
}

export function demoBootstrap(): HeaBootstrap {
  return {
    elements: Object.fromEntries(Array.from(new Set(Object.values(HEA_DEMO_ALLOYS).flatMap((a) => Object.keys(a.composicao)))).map((e) => [e, { simbolo: e }])),
    alloys: HEA_DEMO_ALLOYS,
    reference: HEA_DEMO_REFERENCE,
    samples: Object.values(HEA_DEMO_ALLOYS).map((a) => analyzeDemo(a.nome, a.composicao)),
  };
}
