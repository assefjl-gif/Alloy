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
import { analyzeDemo, HEA_DEMO_ALLOYS } from '../../src/services/adapters/heaDemo.ts';
import { chooseMaterial, defaultSeed } from '../../src/modules/didactics/seed.ts';
import { ACTIVITIES, activityById } from '../../src/modules/didactics/bank.ts';
import { niceTicks, spreadLabels } from '../../src/modules/hea/HeaCharts.tsx';
import { notesToMarkdown, type Note } from '../../src/modules/notebook/store.ts';
import { parseUserNumber, formatNumber } from '../../src/utils/format.ts';
import { StructureResult } from '../../src/services/api/contracts.ts';
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
