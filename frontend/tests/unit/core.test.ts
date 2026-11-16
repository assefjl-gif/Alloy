/**
 * Testes unitários de núcleo: semente reproduzível, URL de cena, classificação de erros,
 * geometria do viewer (sobre respostas reais do motor), transporte HEA imutável,
 * escolha de material por semente, eixos dos gráficos e exportação do caderno.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRng, hashSeed } from '../../src/utils/rng.ts';
import { encodeScene, decodeScene, SCENE_URL_MAX, safeColor } from '../../src/features/url/sceneUrl.ts';
import { classifyAnswer } from '../../src/modules/didactics/model.ts';
import { buildAtoms, distance, angleDeg, translations, cellOffset, measurementProblem } from '../../src/features/viewer3d/geometry.ts';
import { matchStructure, createTransfer } from '../../src/modules/hea/transfer.ts';
import { analyzeDemo, demoBootstrap, HEA_DEMO_ALLOYS } from '../../src/services/adapters/heaDemo.ts';
import { chooseMaterial, defaultSeed } from '../../src/modules/didactics/seed.ts';
import { ACTIVITIES, activityById } from '../../src/modules/didactics/bank.ts';
import { niceTicks, spreadLabels } from '../../src/modules/hea/HeaCharts.tsx';
import { notesToMarkdown, type Note } from '../../src/modules/notebook/store.ts';
import { parseUserNumber, formatNumber } from '../../src/utils/format.ts';
import { HeaResult, StructureResult } from '../../src/services/api/contracts.ts';
import { compositionRows, criteriaFor, criterionLabel, criterionStatus, curveSeries, deltaVecPoints, evaluatedCriteria, hasMassBasis, triageText, triageTone } from '../../src/modules/hea/display.ts';
import type { Vec3 } from '../../src/services/api/contracts.ts';

const fixture = (m: string) => StructureResult.parse(JSON.parse(readFileSync(new URL(`../fixtures/engine-${m}.json`, import.meta.url), 'utf8')).result);

test('rng: mesma semente, mesma sequência; Math.random não é usado', () => {
  const a = createRng(42); const b = createRng(42);
  assert.deepEqual([a.next(), a.next(), a.int(1, 9)], [b.next(), b.next(), b.int(1, 9)]);
  assert.notEqual(createRng(43).next(), createRng(42).next());
  assert.deepEqual(createRng(7).shuffle([1, 2, 3, 4, 5]), createRng(7).shuffle([1, 2, 3, 4, 5]));
  assert.equal(hashSeed('abc'), hashSeed('abc'));
});

test('URL de cena: ida e volta, versão, esquema e tamanho', () => {
  const scene = { v: 1 as const, m: { nome: 'Cu' }, o: [{ t: 'p' as const, i: [1, 1, 1], c: '#D55E00' }], s: [2, 2, 2] as [number, number, number], dn: 1 as const };
  const enc = encodeScene(scene);
  assert.ok(enc.startsWith('v1.'));
  const dec = decodeScene(enc);
  assert.equal(dec.ok, true);
  assert.deepEqual((dec as { scene: unknown }).scene, scene);
  assert.equal((decodeScene('v2.abc') as { reason: string }).reason, 'version');
  assert.equal((decodeScene('v1.%%%') as { reason: string }).reason, 'format');
  const bad = encodeScene({ v: 1, m: { nome: '<script>' } } as never);
  assert.equal((decodeScene(bad) as { reason: string }).reason, 'schema');
  const extra = encodeScene({ v: 1, m: {}, z: 1 } as never);
  assert.equal((decodeScene(extra) as { reason: string }).reason, 'schema', 'campos desconhecidos são recusados');
  assert.equal((decodeScene(`v1.${'a'.repeat(SCENE_URL_MAX)}`) as { reason: string }).reason, 'size');
  assert.equal(safeColor('red; background:url(x)', '#000000'), '#000000');
});

test('classificação de erros do estudante', () => {
  assert.deepEqual(classifyAnswer(8.93, 8.937), { correct: true });
  assert.equal(classifyAnswer(null, 8.937).type, 'input');
  assert.equal(classifyAnswer(8.937e-21, 8.937).type, 'unit');
  assert.equal(classifyAnswer(8.937e3, 8.937).power, 3);
  assert.equal(classifyAnswer(7.74, 8.937, 0.01, [7.74]).type, 'conceptual');
  assert.equal(classifyAnswer(5.1, 8.937).type, 'algebraic');
});

test('geometria: contagens exibidas vêm do motor; supercélula só replica', () => {
  const cu = fixture('Cu');
  assert.equal(cu.n, 4);
  assert.equal(buildAtoms(cu, [1, 1, 1]).length, cu.atomos.length);
  const sc = buildAtoms(cu, [2, 2, 2]);
  assert.equal(sc.length, 27 + 36, 'CFC 2×2×2: 27 vértices + 36 centros de face, sem duplicatas');
  assert.equal(sc.filter((a) => !a.replica).length, cu.atomos.length);
  const mg = fixture('Mg');
  assert.equal(mg.estrutura, 'HC');
  const t = translations('HC', mg.c_a);
  assert.deepEqual(cellOffset(t, [0, 0, 1]), [0, 0, mg.c_a]);
  const mg2 = buildAtoms(mg, [2, 1, 1]);
  assert.ok(mg2.length > mg.atomos.length && mg2.length < 2 * mg.atomos.length, 'prismas vizinhos compartilham átomos');
});

test('geometria: distância e ângulo (unidades de a)', () => {
  const o: Vec3 = [0, 0, 0];
  assert.equal(distance(o, [1, 0, 0]), 1);
  assert.ok(Math.abs(distance(o, [0.5, 0.5, 0]) - Math.SQRT1_2) < 1e-12);
  assert.ok(Math.abs(angleDeg([1, 0, 0], o, [0, 1, 0]) - 90) < 1e-9);
  assert.equal(measurementProblem('distance', [{ index: 1, cell: [0, 0, 0] }, { index: 1, cell: [0, 0, 0] }]), 'duplicate');
});

test('transporte HEA → CrystaLab: regra de correspondência e imutabilidade', () => {
  assert.deepEqual(matchStructure({ fase: 'Solução sólida CFC' }), { code: 'CFC', candidates: ['CFC'], basis: 'predictor-phase' });
  assert.equal(matchStructure({ fase: 'CFC + CCC' }).code, null);
  assert.equal(matchStructure({ fase: 'CFC + CCC' }).basis, 'user-choice');
  assert.equal(matchStructure({ fase: 'qualquer', estrutura_sugerida: 'HC' }).basis, 'predictor-field');
  const alloy = HEA_DEMO_ALLOYS[Object.keys(HEA_DEMO_ALLOYS)[0]!]!;
  const result = analyzeDemo(alloy.nome, alloy.composicao);
  const tr = createTransfer(result, 'demo', 1);
  assert.ok(Object.isFrozen(tr) && Object.isFrozen(tr.result) && Object.isFrozen(tr.result.comp_perc));
  assert.throws(() => { (tr.result as { delta: number }).delta = 0; });
  (result as { delta: number }).delta = -1;
  assert.notEqual(tr.result.delta, -1, 'a cópia não acompanha alterações do original');
  assert.throws(() => createTransfer({ ...result, fase: 'CFC + CCC' }, 'demo', 1), /Estrutura não definida/);
  assert.equal(createTransfer({ ...result, fase: 'CFC + CCC' }, 'demo', 1, 'CCC').structure.basis, 'user-choice');
});

test('HEA demonstrativo: determinístico e marcado', () => {
  const comp = { Fe: 1, Ni: 1, Cr: 1 };
  const a = analyzeDemo('X', comp); const b = analyzeDemo('X', comp);
  assert.deepEqual(a, b);
  assert.ok(typeof (a as { demo_seed?: number }).demo_seed === 'number');
});

test('HEA demonstrativo (A-17): nenhum veredito de estabilidade; triagem na forma do contrato', () => {
  const resultados = [analyzeDemo('X', { Fe: 1, Ni: 1, Cr: 1 }), ...demoBootstrap().samples];
  for (const r of resultados) {
    // a forma é a do motor (R1 §1.2), e o estado é sempre inconclusivo: não houve triagem
    assert.equal(r.triagem?.estado, 'inconclusiva');
    assert.equal(triageTone(r), 'inconclusiva');
    assert.equal(triageText(r), r.triagem?.texto);
    assert.equal(r.veredito, r.triagem?.texto, 'veredito repete triagem.texto');
    assert.doesNotMatch(`${r.veredito} ${r.triagem?.texto ?? ''}`, /EST[\u00c1A]VEL/i, 'a demo não pode sortear ESTÁVEL');
    // procedência declarada: sem motor, sem fontes
    assert.equal(r.procedencia?.classe, 'demonstrativo');
    assert.deepEqual(r.procedencia?.fontes_modelo, []);
    assert.deepEqual(r.procedencia?.fontes_dados, []);
    assert.ok(r.interpretacao.some((line) => /DEMONSTRATIVO/.test(line)));
  }
});

test('atividades: material por semente, sempre do catálogo', () => {
  const act = activityById('densidade-sorteada')!;
  const catalog = ['Fe', 'Cu', 'Al', 'Ni', 'Cr'];
  const m1 = chooseMaterial(act, 1234, catalog);
  assert.equal(m1, chooseMaterial(act, 1234, catalog));
  assert.ok(catalog.includes(m1));
  const seen = new Set(Array.from({ length: 40 }, (_, i) => chooseMaterial(act, 1000 + i, catalog)));
  assert.ok(seen.size > 1, 'sementes diferentes variam o material');
  assert.equal(chooseMaterial(activityById('densidade-cobre')!, 99, catalog), 'Cu');
  assert.equal(defaultSeed('fea'), defaultSeed('fea'));
  for (const a of ACTIVITIES) {
    assert.ok(a.references.length > 0 && a.references.every((r) => /^(CAL9|ASK6|HEA Virtual Lab v1\.17)\b/.test(r)), `${a.id}: referências do registro/fontes do projeto`);
    assert.ok(a.title['pt-BR'] && a.title.en && a.title.es, `${a.id}: título nos 3 idiomas`);
  }
});

test('gráficos: marcas redondas e rótulos sem sobreposição', () => {
  assert.deepEqual(niceTicks(0, 8, 5), [0, 2, 4, 6, 8]);
  const t = niceTicks(-21, 10, 6);
  assert.ok(t[0]! <= -21 && t[t.length - 1]! >= 10);
  assert.ok(t.every((v) => Number.isInteger(v / 5)));
  const ys = spreadLabels([100, 104, 300], 12);
  assert.ok(ys[1]! - ys[0]! >= 12 && ys[2] === 300);
});

test('caderno: exporta em Markdown sem recalcular valores', () => {
  const note: Note = { id: 'n1', kind: 'calculation', title: 'Cu', body: 'ρ calculada', createdAt: '2026-10-21T00:00:00Z', updatedAt: '2026-10-21T00:00:00Z', params: { densidade_motor: 8.937318868060766, R: null } };
  const md = notesToMarkdown([note], { observation: 'Obs', hypothesis: 'Hip', calculation: 'Cálculo', conclusion: 'Concl', free: 'Livre' });
  assert.match(md, /## Cu/);
  assert.match(md, /densidade_motor: 8\.937318868060766/);
  assert.match(md, /R: —/);
});

test('números: vírgula ou ponto na entrada, formato por idioma na saída', () => {
  assert.equal(parseUserNumber('0,128'), 0.128);
  assert.equal(parseUserNumber('4,7e-23'), 4.7e-23);
  assert.ok(Number.isNaN(parseUserNumber('abc')));
  assert.equal(parseUserNumber('  '), null);
  assert.equal(formatNumber(8.937, 2, 'pt-BR'), '8,94');
  assert.equal(formatNumber(8.937, 2, 'en'), '8.94');
});

// ------------------------------------------------- R2-FE-01: exibição do HEA (contrato R1 §1.2)
/** Resposta real do motor HEA 2.0.0, abreviada; os números são os devolvidos pela API. */
const heaBase = {
  nome: 'CoCrFeNi', veredito: 'TRIAGEM INCONCLUSIVA: (...)', fase: 'não avaliada: VEC indisponível',
  ductilidade: null, dureza: null, dureza_indice: null, fragilidade: null,
  dS: 11.5263, dS_R: 1.3863, classe_entropia: 'media',
  dH: null, delta: 0.3512, omega: null, VEC: 8.25, Tm: 1861.25, raio_medio_nm: 0.124725,
  base_entrada: 'atomica', soma_informada: 4,
  comp_percent: { Co: 25, Cr: 25, Fe: 30, Ni: 20 },
  comp_massa_pct: null, fracoes_massa: null, massa_molar_media: null,
  pares_faltantes: ['Co-Cr'], dados_faltantes: [{ simbolo: 'Co-Cr', codigo: 'entalpia_mistura_par', situacao: 'ausente' }],
  T_sup_k: 1900,
  curva_T: [{ T: 300, menos_TdS: -3.4579, dG: null }, { T: 350, menos_TdS: -4.0342, dG: null }],
  dG_Tm: null, T_cruzamento_k: null, energia_formacao: null, gibbs: [],
  criterios: [{
    codigo: 'delta_yang_zhang', grandeza: 'delta', operador: '<=', limiar: 6.6, unidade: '%',
    natureza: 'empirico', fonte: 'Yang & Zhang (2012)', verificada: false,
    valor: 0.3512, atende: true, aplicavel: true, proximo_do_limiar: false, motivo: null,
  }, {
    codigo: 'omega_yang_zhang', grandeza: 'omega', operador: '>=', limiar: 1.1, unidade: 'adimensional',
    natureza: 'empirico', fonte: 'Yang & Zhang (2012)', verificada: false,
    valor: null, atende: null, aplicavel: true, proximo_do_limiar: false,
    motivo: 'Ω depende de ΔH_mix, que está indisponível.',
  }, {
    codigo: 'vec_ccc_guo', grandeza: 'VEC', operador: '<', limiar: 6.87, unidade: 'e/átomo',
    natureza: 'empirico', fonte: 'Guo et al. (2011)', verificada: false,
    valor: 8.25, atende: false, aplicavel: false, proximo_do_limiar: false, motivo: null,
  }],
  triagem: { estado: 'inconclusiva', texto: 'TRIAGEM INCONCLUSIVA: (...)' },
  vec_aplicavel: true, classes: { dS: 'analitico', 'curva_T.menos_TdS': 'analitico' },
  interpretacao: ['(...)'],
  indisponiveis: { dH: 'ΔH_mix indisponível: a tabela de entalpias por par não foi cadastrada.', omega: 'Ω depende de ΔH_mix.' },
};
const hea = (patch: Record<string, unknown> = {}) => HeaResult.parse({ ...heaBase, ...patch });

test('HEA: estado da triagem vem de triagem.estado, nunca do texto do veredito', () => {
  assert.equal(triageTone(hea()), 'inconclusiva');
  assert.equal(triageTone(hea({ triagem: { estado: 'favoravel', texto: 'x' } })), 'favoravel');
  assert.equal(triageTone(hea({ triagem: { estado: 'desfavoravel', texto: 'x' } })), 'desfavoravel');
  // texto com "ESTÁVEL" e sem triagem NÃO é lido como estabilidade
  assert.equal(triageTone(hea({ triagem: undefined, veredito: 'ESTÁVEL (texto antigo)' })), 'desconhecido');
  assert.equal(triageTone(hea({ triagem: { estado: 'outro_estado_novo', texto: 'x' } })), 'desconhecido');
  assert.equal(triageText(hea()), 'TRIAGEM INCONCLUSIVA: (...)');
  assert.equal(triageText(hea({ triagem: undefined, veredito: 'V' })), 'V');
});

test('HEA: composição nas duas bases; ausência de % em massa não vira zero', () => {
  const rows = compositionRows(hea());
  assert.deepEqual(rows.map((r) => r.element), ['Fe', 'Co', 'Cr', 'Ni'], 'ordem decrescente de % atômica');
  assert.deepEqual(rows.map((r) => r.massPct), [null, null, null, null]);
  assert.equal(hasMassBasis(rows), false);
  const comMassa = compositionRows(hea({ comp_massa_pct: { Co: 26.1365, Cr: 23.0629, Fe: 30.1, Ni: 20.8 } }));
  assert.equal(hasMassBasis(comMassa), true);
  assert.equal(comMassa[0]?.element, 'Fe');
  assert.equal(comMassa[0]?.massPct, 30.1);
  // elemento sem valor na base mássica continua null (nunca 0)
  const parcial = compositionRows(hea({ comp_massa_pct: { Fe: 30.1 } }));
  assert.deepEqual(parcial.map((r) => r.massPct), [30.1, null, null, null]);
});

test('HEA: série do gráfico G-A só desenha ΔG quando o motor tem valor em todos os pontos', () => {
  const sem = curveSeries(hea());
  assert.equal(sem.entropyTerm.length, 2);
  assert.deepEqual(sem.entropyTerm[0], { T: 300, value: -3.4579 });
  assert.deepEqual(sem.gibbs, [], 'sem ΔH_mix não se desenha curva demonstrativa');
  assert.match(sem.gibbsUnavailable ?? '', /ΔH_mix indisponível/);
  assert.equal(sem.tMax, 1900);
  const parcial = curveSeries(hea({ curva_T: [{ T: 300, menos_TdS: -3.4579, dG: -1 }, { T: 350, menos_TdS: -4.0342, dG: null }] }));
  assert.deepEqual(parcial.gibbs, [], 'curva parcial não é desenhada');
  const completa = curveSeries(hea({ curva_T: [{ T: 300, menos_TdS: -3.4579, dG: -1.5 }, { T: 350, menos_TdS: -4.0342, dG: -2.5 }] }));
  assert.deepEqual(completa.gibbs, [{ T: 300, value: -1.5 }, { T: 350, value: -2.5 }]);
  assert.equal(completa.gibbsUnavailable, null);
  const vazia = curveSeries(hea({ curva_T: [] }));
  assert.deepEqual(vazia.entropyTerm, []);
});

test('HEA: pontos do gráfico G-B exigem δ e VEC; a liga analisada entra uma única vez', () => {
  const selected = hea();
  const samples = [hea({ nome: 'A', delta: 1, VEC: 7 }), hea({ nome: 'B', delta: null }), hea({ nome: 'C', VEC: null }), selected];
  const pts = deltaVecPoints(samples, selected);
  assert.deepEqual(pts.map((p) => p.name), ['A', 'CoCrFeNi']);
  assert.equal(pts[pts.length - 1]?.selected, true);
  assert.deepEqual(pts[0], { name: 'A', delta: 1, vec: 7, selected: false });
  const semSelecionada = deltaVecPoints(samples, hea({ delta: null }));
  assert.deepEqual(semSelecionada.map((p) => p.name), ['A']);
  assert.deepEqual(deltaVecPoints([], hea({ VEC: null })), []);
});

test('HEA: rótulo e situação do critério saem do motor (limiar, unidade, fonte e domínio)', () => {
  const [delta, omega, vecCcc] = evaluatedCriteria(hea());
  const fmt = (v: number) => String(v);
  assert.equal(criterionLabel(delta!, fmt), 'delta ≤ 6.6 %');
  assert.equal(criterionLabel(omega!, fmt), 'omega ≥ 1.1');
  assert.equal(criterionStatus(delta!), 'atende');
  assert.equal(criterionStatus(omega!), 'nao_avaliado');
  assert.equal(criterionStatus(vecCcc!), 'fora_do_dominio');
  assert.equal(criterionStatus({ atende: false, aplicavel: true, valor: 9 }), 'nao_atende');
  assert.deepEqual(criteriaFor(evaluatedCriteria(hea()), 'VEC').map((c) => c.codigo), ['vec_ccc_guo']);
  assert.deepEqual(evaluatedCriteria(hea({ criterios: undefined })), []);
});
