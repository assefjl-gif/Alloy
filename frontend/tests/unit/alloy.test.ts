/**
 * Ligas e temperatura (T-13): cena pura (sem WebGL) e adaptadores contra o BACKEND REAL.
 * O gabarito dos números é o do motor; aqui se confere que o front os repassa sem inventar nada.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import type { ChildProcess } from 'node:child_process';
import { ALLOY_PALETTE, alloyLegend, alloyLegendWith, displacement, displayAmplitude, sceneFromAlloy, unit } from '../../src/features/viewer3d/alloyScene.ts';
import { appearanceActive, DEFAULT_APPEARANCE, groupOf, normalizeColor, resolveAtomColor, type AppearanceSettings } from '../../src/features/viewer3d/appearance.ts';
import { axisRange, cutKeeps, EMPTY_FILTER } from '../../src/features/viewer3d/visibility.ts';
import type { AlloyResult } from '../../src/services/api/contracts.ts';
import { absentSolutes, alloyAtomViews, alloyDisplayCounts, alloyElementOptions, alloyOccupationOptions, alloySiteOptions, compositionPairs, drawnAtomCount, globalConclusion, hasPeriodicImages, pureElementOf, representedAtomsOf, uniqueAtomCount, uniqueAtoms } from '../../src/modules/crystalab/alloyDisplay.ts';
// @ts-expect-error — script .mjs sem tipos
import { startBackend } from '../../scripts/backend.mjs';

const PORT = 8034;
let proc: ChildProcess | undefined;

before(async () => {
  proc = startBackend({ port: PORT, stdio: 'ignore' }) as ChildProcess;
  const end = Date.now() + 30000;
  for (;;) {
    try { if ((await fetch(`http://127.0.0.1:${PORT}/health`)).ok) break; } catch { /* subindo */ }
    if (Date.now() > end) throw new Error('backend não subiu');
    await new Promise((r) => setTimeout(r, 200));
  }
});
after(() => { proc?.kill(); });

async function api() {
  const { config } = await import('../../src/config.ts');
  config.apiBase = `http://127.0.0.1:${PORT}`;
  const m = await import('../../src/services/api/crystalab.ts');
  await m.detectCrystalab();
  return m.crystalabApi;
}

test('liga substitucional Cu–Ni: contrato validado, contagens e regras vindas do motor', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Cu', soluto: 'Ni', x: 30, n: 2 });
  assert.equal(r.estrutura, 'CFC');
  assert.equal(r.intersticial, false);
  // V-8 do contrato R1: `n_soluto`/`n_solvente` contam átomos ÚNICOS; `atomos` traz as esferas
  // desenhadas (únicos + imagens periódicas de fronteira).
  assert.equal(r.n_soluto + r.n_solvente, r.composicao?.n_atomos_unicos);
  assert.equal(r.atomos.length, r.composicao?.n_desenhados);
  assert.equal(uniqueAtoms(r.atomos).length, r.composicao?.n_atomos_unicos);
  assert.equal(uniqueAtomCount(r), r.composicao?.n_atomos_unicos);
  assert.equal(drawnAtomCount(r), r.atomos.length);
  assert.equal(r.regras.length, 4);
  assert.ok(r.a_nm < r.a_base_nm, 'Ni é menor que Cu: a da liga diminui (Vegard)');
  assert.equal(r.procedencia.classe, 'estimativa_modelo');
});

test('liga intersticial Fe–C: soluto em sítio intersticial com distorção ilustrativa quando pedida', async () => {
  const cl = await api();
  // Supercélula 3×3×3 (54 átomos únicos): 2 at% dá ⌊54·x/(1−x) + ½⌋ = 1 intersticial.
  const r = await cl.alloy({ base: 'Fe', soluto: 'C', x: 2, n: 3, distorcer: true });
  assert.equal(r.intersticial, true);
  assert.ok(r.atomos.some((a) => a.tipo === 'intersticial' && a.elemento === 'C'));
  assert.equal(r.distorcao?.classe, 'simulacao_ilustrativa');
  assert.ok(r.sitio?.nome);
});

test('amostragem honesta: supercélula pequena demais para a composição não inventa um soluto (T-21)', async () => {
  const cl = await api();
  // 2 at% em 2×2×2 (16 átomos únicos) dá ⌊16·x/(1−x) + ½⌋ = 0. Antes havia um mínimo forçado de 1,
  // que falsificava a composição representada. Zero é o resultado correto da amostragem.
  const pequena = await cl.alloy({ base: 'Fe', soluto: 'C', x: 2, n: 2 });
  assert.equal(pequena.n_soluto, 0, '2 at% em 2×2×2 arredonda para 0 intersticiais');
  assert.equal(pequena.atomos.filter((a) => a.elemento === 'C').length, 0, 'sem soluto sorteado, nenhum C é desenhado');
  assert.equal(pequena.intersticial, true, 'o modo da liga continua intersticial, mesmo sem soluto na amostra');
  // A mesma composição numa supercélula maior passa a conter carbono: o problema é de amostragem, não de modelo.
  const maior = await cl.alloy({ base: 'Fe', soluto: 'C', x: 2, n: 3 });
  assert.ok(maior.n_soluto >= 1, 'em 3×3×3 a mesma composição já comporta um intersticial');
});

test('D-R2-3: soluto ausente é identificado pela contagem do motor, e o tamanho sugerido vem do motor', async () => {
  const cl = await api();
  // Caso 1 — supercélula pequena: 2 at% em 2×2×2 dá 0 átomos de C (amostragem honesta, T-21).
  const pequena = await cl.alloy({ base: 'Fe', soluto: 'C', x: 2, n: 2 });
  assert.equal(representedAtomsOf(pequena, 'C'), 0, 'a contagem do motor é zero, não nula');
  const ausentes = absentSolutes(pequena);
  assert.deepEqual(ausentes.map((a) => a.element), ['C']);
  assert.deepEqual(ausentes.map((a) => a.papel), ['intersticial']);
  assert.equal(ausentes[0]?.atRequested, 2, 'a composição pedida vem da resposta, não do formulário');
  // Caso 2 — a sugestão da interface é o primeiro tamanho em que o MOTOR traz ao menos um átomo.
  let sugerido: number | null = null;
  for (const n of [3, 4]) {
    const probe = await cl.alloy({ base: 'Fe', soluto: 'C', x: 2, n });
    if (sugerido === null && (representedAtomsOf(probe, 'C') ?? 0) >= 1) sugerido = n;
  }
  assert.equal(sugerido, 3, 'em 3×3×3 a mesma composição já comporta um intersticial');
  const maior = await cl.alloy({ base: 'Fe', soluto: 'C', x: 2, n: 3 });
  assert.ok((representedAtomsOf(maior, 'C') ?? 0) >= 1);
  assert.deepEqual(absentSolutes(maior), [], 'com soluto representado não há aviso de ausência');
  // Sem os campos novos (backend anterior) não se afirma ausência nenhuma.
  assert.deepEqual(absentSolutes({ composicao: undefined }), []);
  assert.equal(representedAtomsOf({ composicao: undefined }, 'C'), null);
});

test('mesma semente, mesma liga; entrada inválida vira erro de domínio, não valor inventado', async () => {
  const cl = await api();
  const a = await cl.alloy({ base: 'Cu', soluto: 'Ni', x: 25, n: 2, semente: 7 });
  const b = await cl.alloy({ base: 'Cu', soluto: 'Ni', x: 25, n: 2, semente: 7 });
  assert.deepEqual(a.atomos, b.atomos);
  await assert.rejects(cl.alloy({ base: 'Cu', soluto: 'Xx', x: 10 }), (e: Error & { kind?: string }) => e.kind === 'domain');
});

test('temperatura do metal e da liga: contrato, dilatação positiva e curva monotônica até a fusão', async () => {
  const cl = await api();
  const fe = await cl.thermal({ material: 'Fe', temperatura_c: 600 });
  // Dentro do dominio do modelo (abaixo da T_f) estes campos NAO podem ser nulos.
  assert.ok(fe.a_nm !== null && fe.delta_a_pct !== null && fe.delta_v_pct !== null, 'abaixo da T_f o motor deve entregar a rede e as dilatacoes');
  assert.ok(fe.a_nm > fe.a_ref_nm && fe.delta_a_pct > 0 && fe.delta_v_pct > 0);
  assert.ok(fe.homologa > 0 && fe.homologa < 1 && fe.fundido === false);
  assert.ok(fe.amplitude_rel > 0);
  for (let i = 1; i < fe.curva.length; i += 1) assert.ok((fe.curva[i] as [number, number])[1] >= (fe.curva[i - 1] as [number, number])[1]);
  const liga = await cl.thermal({ liga: { base: 'Cu', soluto: 'Ni', x: 30 }, temperatura_c: 500 });
  assert.ok(liga.a_nm !== null && liga.a_nm > liga.a_ref_nm);
  const quente = await cl.thermal({ material: 'Fe', temperatura_c: 2500 });
  assert.equal(quente.fundido, true);
});

test('acima da T_f: sem ordem cristalina, os campos voltam nulos COM causa, nunca zero', async () => {
  const cl = await api();
  // Achado T-1 do parecer de termodinamica: acima da T_f do modelo nao ha rede para informar.
  const quente = await cl.thermal({ material: 'Fe', temperatura_c: 2500 });
  assert.equal(quente.fundido, true);
  for (const campo of ['fator', 'a_nm', 'delta_a_pct', 'delta_v_pct'] as const) {
    assert.equal(quente[campo], null, `${campo} deveria ser nulo acima da T_f`);
    assert.ok(quente.indisponiveis?.[campo], `${campo} nulo tem de trazer a causa em indisponiveis`);
  }
  // A temperatura de referencia continua, porque e um dado tabelado a 20 C.
  assert.ok(quente.a_ref_nm > 0);
});

test('cena da liga: um átomo desenhado por átomo do motor, legenda por papel, amplitude só se informada', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Fe', soluto: 'C', x: 3, n: 2 }) as AlloyResult;
  const scene = sceneFromAlloy(r, 0.05);
  assert.equal(scene.atoms.length, r.atomos.length);
  assert.equal(scene.edges.length, r.arestas.length);
  assert.equal(sceneFromAlloy(r).amplitude, 0);
  const legend = alloyLegend(r);
  assert.deepEqual(legend.map((l) => l.role), ['base', 'intersticial']);
  assert.deepEqual(legend.map((l) => l.color), [ALLOY_PALETTE[0], ALLOY_PALETTE[1]]);
  assert.equal(scene.colors.Fe, ALLOY_PALETTE[0]);
});

test('vibração: determinística, limitada pela amplitude e nula sem temperatura', () => {
  assert.deepEqual(displacement(5, 1234, 0.05), displacement(5, 1234, 0.05));
  assert.deepEqual(displacement(5, 1234, 0), [0, 0, 0]);
  let maximo = 0;
  for (let i = 0; i < 200; i += 1) for (const t of [0, 250, 777, 1500]) for (const c of displacement(i, t, 0.05)) maximo = Math.max(maximo, Math.abs(c));
  assert.ok(maximo <= 0.05 + 1e-12 && maximo > 0.04, `máximo ${maximo}`);
  assert.notDeepEqual(displacement(1, 100, 0.05), displacement(2, 100, 0.05), 'átomos diferentes oscilam diferente');
  for (let i = 0; i < 50; i += 1) { const u = unit(i, 3); assert.ok(u >= 0 && u < 1); }
  assert.equal(displayAmplitude(0.05, 1), 0.05);
  assert.equal(displayAmplitude(0.05, 4), 0.2);
  assert.equal(displayAmplitude(0.05, 0), 0.05, 'exagero nunca reduz abaixo da amplitude real');
});

// ------------------------------------------------------------------ R2-FE-01: campos novos
test('composição pedida × representada: uma linha por elemento, nas duas bases, com átomos únicos', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Fe', n: 3, semente: 7, solutos: [{ elemento: 'Cr', x: 12 }, { elemento: 'Ni', x: 8 }, { elemento: 'C', x: 1, modo: 'intersticial', sitio: 'octaedrico' }] });
  const rows = compositionPairs(r);
  assert.deepEqual(rows.map((row) => row.element), ['Fe', 'Cr', 'Ni', 'C'], 'ordem canônica do motor');
  assert.deepEqual(rows.map((row) => row.papel), ['solvente', 'substitucional', 'substitucional', 'intersticial']);
  for (const row of rows) {
    assert.equal(typeof row.atRequested, 'number');
    assert.equal(typeof row.atRepresented, 'number');
    assert.ok(row.atoms !== null && row.atoms >= 0, 'contagem de átomos únicos vem do motor');
  }
  // soma das contagens = átomos únicos; nada é recalculado, só conferido contra o motor
  const soma = rows.reduce((acc, row) => acc + (row.atoms ?? 0), 0);
  assert.equal(soma, r.composicao?.n_atomos_unicos);
  assert.equal(uniqueAtomCount(r) + 0, soma);
  assert.ok(drawnAtomCount(r) >= soma, 'esferas desenhadas incluem as imagens periódicas');
  assert.equal(hasPeriodicImages(r.atomos), drawnAtomCount(r) > soma);
  // com mais de um soluto não há conclusão única: vem o motivo da API
  const conclusion = globalConclusion(r);
  assert.equal(conclusion.text, null);
  assert.ok(conclusion.reason && conclusion.reason.length > 0);
  assert.equal(r.regras_por_soluto?.length, 3);
});

test('legenda da cena com mais de dois elementos: um item por elemento representado, cor distinta', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Fe', n: 3, solutos: [{ elemento: 'Cr', x: 10 }, { elemento: 'Ni', x: 8 }, { elemento: 'Al', x: 4 }, { elemento: 'C', x: 1, modo: 'intersticial' }] });
  const legend = alloyLegend(r);
  assert.deepEqual(legend.map((l) => l.element), ['Fe', 'Al', 'Cr', 'Ni', 'C']);
  assert.deepEqual(legend.map((l) => l.role), ['base', 'soluto', 'soluto', 'soluto', 'intersticial']);
  assert.equal(new Set(legend.map((l) => l.color)).size, legend.length, 'cores distintas para 5 elementos');
  for (const l of legend) assert.ok(l.atoms !== null && l.atoms >= 0);
  const scene = sceneFromAlloy(r);
  assert.equal(Object.keys(scene.colors).length, legend.length);
  // imagem periódica nunca entra na contagem da legenda
  const unicos = uniqueAtoms(r.atomos);
  const porElemento = legend.map((l) => unicos.filter((a) => a.elemento === l.element).length);
  assert.deepEqual(legend.map((l) => l.atoms), porElemento);
});

test('legenda sem os campos novos (backend anterior): recuo para a forma binária', () => {
  const legend = alloyLegend({ base: 'Cu', soluto: 'Ni', intersticial: false });
  assert.deepEqual(legend.map((l) => [l.element, l.role, l.atoms]), [['Cu', 'base', null], ['Ni', 'soluto', null]]);
});

// ---------------------------------------------- R2-FE-03: identidade, filtros e cortes (T-24/T-23)

test('cena de liga: cada átomo desenhado leva a identidade do motor e o rótulo de imagem periódica', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Cu', soluto: 'Ni', x: 30, n: 2 });
  const scene = sceneFromAlloy(r);
  assert.equal(scene.atoms.length, r.atomos.length, 'uma esfera por átomo do motor');
  // id vem do motor e é único entre as esferas desenhadas
  const ids = scene.atoms.map((a) => a.id);
  assert.equal(new Set(ids).size, ids.length, 'identificadores distintos');
  r.atomos.forEach((a, i) => {
    if (a.id) assert.equal(ids[i], a.id, 'o front não inventa identificador');
    assert.equal(scene.atoms[i]!.image, a.imagem === true);
    assert.deepEqual(scene.atoms[i]!.pos, a.pos, 'posição repassada sem recálculo');
  });
  // imagem periódica fora da contagem de únicos; esferas = únicos + imagens
  const views = alloyAtomViews(r.atomos, EMPTY_FILTER);
  const counts = alloyDisplayCounts(views);
  assert.equal(counts.drawn, r.atomos.length);
  assert.equal(counts.unique, uniqueAtomCount(r));
  assert.equal(counts.unique + counts.images, counts.drawn);
  // a imagem aponta para o átomo de origem, e a origem existe na resposta
  for (const v of views.filter((x) => x.image)) {
    assert.ok(v.atom.imagem_de, 'imagem periódica diz de qual átomo é réplica');
    assert.ok(views.some((x) => x.id === v.atom.imagem_de), 'o átomo de origem está na cena');
  }
  // ocupação e sítio são os rótulos do motor; wyckoff ausente fica nulo (não é inventado)
  for (const v of views) {
    assert.equal(v.occupancy, v.atom.ocupacao ?? v.atom.tipo ?? null);
    assert.equal(v.site, v.atom.sitio?.nome ?? null);
    if (v.atom.sitio) assert.ok(v.atom.sitio.wyckoff === null || typeof v.atom.sitio.wyckoff === 'string');
  }
});

test('filtro por elemento e por ocupação: só exibição, contagem do motor intacta', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Fe', n: 3, semente: 7, solutos: [{ elemento: 'Cr', x: 12 }, { elemento: 'C', x: 1, modo: 'intersticial', sitio: 'octaedrico' }] });
  const engineUnique = uniqueAtomCount(r);
  const engineDrawn = drawnAtomCount(r);
  const elements = alloyElementOptions(r);
  assert.deepEqual(elements, ['Fe', 'Cr', 'C']);
  const occupations = alloyOccupationOptions(r.atomos);
  assert.ok(occupations.includes('intersticial'), 'ocupações do motor incluem intersticial');
  const sites = alloySiteOptions(r.atomos);
  assert.ok(sites.length >= 1, 'o motor nomeia ao menos um tipo de sítio');

  // ocultar o solvente esconde só as esferas de Fe
  const hideFe = alloyAtomViews(r.atomos, { ...EMPTY_FILTER, hiddenElements: ['Fe'] });
  assert.ok(hideFe.some((v) => !v.visible));
  assert.ok(hideFe.filter((v) => v.visible).every((v) => v.atom.elemento !== 'Fe'));
  // isolar o intersticial: só átomos cuja ocupação é intersticial continuam visíveis
  const isolate = alloyAtomViews(r.atomos, { ...EMPTY_FILTER, hiddenOccupations: occupations.filter((k) => k !== 'intersticial') });
  const visible = isolate.filter((v) => v.visible);
  assert.ok(visible.length > 0, 'há átomo intersticial na realização do motor');
  assert.ok(visible.every((v) => v.occupancy === 'intersticial'));
  // isolar na dimensão SÍTIO não mexe na dimensão ocupação (dimensões independentes)
  const bySite = alloyAtomViews(r.atomos, { ...EMPTY_FILTER, hiddenSites: sites.slice(1) });
  assert.ok(bySite.filter((v) => v.visible).every((v) => v.site === null || v.site === sites[0]));
  // a contagem CIENTÍFICA do motor não muda com o filtro
  assert.equal(uniqueAtomCount(r), engineUnique);
  assert.equal(drawnAtomCount(r), engineDrawn);
  // a contagem de EXIBIÇÃO muda, e é menor
  assert.ok(alloyDisplayCounts(isolate).drawn < engineDrawn);
});

test('corte por eixo: três modos, faixa tirada das coordenadas do motor, revelando o interior', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Cu', soluto: 'Ni', x: 30, n: 2 });
  const positions = r.atomos.map((a) => a.pos);
  const range = axisRange(positions, 2);
  assert.ok(range.max > range.min);
  const middle = (range.min + range.max) / 2;

  const below = alloyAtomViews(r.atomos, { ...EMPTY_FILTER, cut: { axis: 2, mode: 'below', position: middle, thickness: 0 } });
  const above = alloyAtomViews(r.atomos, { ...EMPTY_FILTER, cut: { axis: 2, mode: 'above', position: middle, thickness: 0 } });
  assert.ok(below.some((v) => v.visible) && below.some((v) => !v.visible), 'o corte esconde parte da cena');
  assert.ok(below.filter((v) => v.visible).every((v) => (v.atom.pos[2] as number) <= middle + 1e-12));
  assert.ok(above.filter((v) => v.visible).every((v) => (v.atom.pos[2] as number) >= middle - 1e-12));
  // todo átomo está em um dos dois lados (nenhum desaparece dos dois)
  r.atomos.forEach((_, i) => assert.ok(below[i]!.visible || above[i]!.visible));

  // átomo mais próximo do meio: revelado pela fatia que o contém, com o resto escondido
  const interior = r.atomos.reduce((best, a, i) => (Math.abs((a.pos[2] as number) - middle) < Math.abs((r.atomos[best]!.pos[2] as number) - middle) ? i : best), 0);
  const z = r.atomos[interior]!.pos[2] as number;
  const slab = alloyAtomViews(r.atomos, { ...EMPTY_FILTER, cut: { axis: 2, mode: 'slab', position: z, thickness: 0.05 } });
  assert.equal(slab[interior]!.visible, true, 'o átomo da fatia continua visível (e selecionável)');
  assert.ok(slab.filter((v) => v.visible).length < r.atomos.length, 'a fatia esconde o resto');
  // cutKeeps é a única regra de corte: sem corte, nada é escondido
  assert.equal(cutKeeps([9, 9, 9], null), true);
});

test('vizinhança de exibição: só átomos a até R do selecionado, sem alterar valor científico', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Cu', soluto: 'Ni', x: 30, n: 2 });
  const target = r.atomos[0]!;
  const views = alloyAtomViews(r.atomos, { ...EMPTY_FILTER, neighbourhood: { center: target.pos, radius: 0.75 } });
  const visible = views.filter((v) => v.visible);
  assert.ok(visible.length >= 1 && visible.length < r.atomos.length);
  for (const v of visible) {
    const d = Math.hypot((v.atom.pos[0] as number) - (target.pos[0] as number), (v.atom.pos[1] as number) - (target.pos[1] as number), (v.atom.pos[2] as number) - (target.pos[2] as number));
    assert.ok(d <= 0.75 + 1e-12);
  }
  // o próprio átomo selecionado está no conjunto visível (distância zero)
  assert.equal(views[0]!.visible, true);
});

test('dado tabelado do elemento puro é do ELEMENTO, não do átomo na liga', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Cu', soluto: 'Ni', x: 30, n: 2 });
  const pure = pureElementOf(r, 'Ni');
  assert.ok(pure, 'o motor devolve o elemento puro em `elementos`');
  assert.equal(pure!.simbolo, 'Ni');
  assert.ok(pure!.estado_do_dado.length > 0, 'estado do dado declarado pelo motor');
  // o raio de DESENHO do átomo vem de raio_rel, e não é apresentado como propriedade do átomo
  const ni = r.atomos.find((a) => a.elemento === 'Ni');
  assert.ok(ni && typeof ni.raio_rel === 'number');
  assert.equal(pureElementOf(r, 'Xx'), null, 'elemento ausente devolve nulo, não um valor inventado');
});

test('store de filtros: isolar em uma dimensão não mexe nas outras, e limpar apaga tudo', async () => {
  const { useSceneFilter, filterActive, hiddenOf, DEFAULT_CUT } = await import('../../src/stores/sceneFilter.ts');
  const { toVisibilityFilter } = await import('../../src/features/viewer3d/sceneFilterState.ts');
  const s = () => useSceneFilter.getState();
  s().clear();
  assert.equal(filterActive(s()), false);

  s().isolate('elements', 'Ni', ['Fe', 'Cr', 'Ni']);
  assert.deepEqual(hiddenOf(s(), 'elements'), ['Fe', 'Cr']);
  assert.deepEqual(hiddenOf(s(), 'occupations'), []);
  assert.deepEqual(hiddenOf(s(), 'sites'), []);

  s().isolate('sites', 'octaedrico', ['octaedrico', 'tetraedrico']);
  assert.deepEqual(hiddenOf(s(), 'sites'), ['tetraedrico']);
  assert.deepEqual(hiddenOf(s(), 'elements'), ['Fe', 'Cr'], 'isolar sítio não mexeu no elemento');

  s().toggle('occupations', 'intersticial', true);
  s().setCut({ axis: 1, position: 0.4 });
  assert.equal(s().cut?.axis, 1);
  assert.equal(s().cut?.mode, DEFAULT_CUT.mode, 'o que não foi informado mantém o padrão');
  assert.equal(filterActive(s()), true);

  // a vizinhança só existe quando há um centro (átomo selecionado); sem centro, não filtra
  s().set({ neighbourhoodRadius: 0.5 });
  assert.equal(toVisibilityFilter(s(), null).neighbourhood, null);
  assert.deepEqual(toVisibilityFilter(s(), [0, 0, 0]).neighbourhood, { center: [0, 0, 0], radius: 0.5 });

  s().clear();
  assert.equal(filterActive(s()), false);
  assert.equal(s().cut, null);
  assert.equal(s().neighbourhoodRadius, null);
  assert.deepEqual([hiddenOf(s(), 'elements'), hiddenOf(s(), 'occupations'), hiddenOf(s(), 'sites')], [[], [], []]);
});


// ===================================================================== aparência (T-22)
/** Preferências de aparência montadas à mão (o que a pessoa escolheria na barra lateral). */
function appearance(patch: Partial<AppearanceSettings> = {}): AppearanceSettings {
  return { ...DEFAULT_APPEARANCE, overrides: { elements: {}, groups: {}, atoms: {} }, ...patch };
}

test('T-22 aparência: cor por elemento, por grupo e por átomo chegam à cena com a precedência certa', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Fe', n: 3, semente: 7, solutos: [{ elemento: 'Cr', x: 12 }, { elemento: 'Ni', x: 8 }, { elemento: 'C', x: 1, modo: 'intersticial', sitio: 'octaedrico' }] });

  // padrão: a cor codifica o ELEMENTO, com a paleta acessível do app
  const plain = sceneFromAlloy(r);
  const fe = plain.atoms.find((a) => a.element === 'Fe');
  assert.ok(fe);
  assert.equal(fe.color, plain.colors.Fe);
  assert.equal(fe.colorSource, 'default');

  // cor por ELEMENTO
  const byElement = sceneFromAlloy(r, 0, EMPTY_FILTER, appearance({ overrides: { elements: { Fe: '#123456' }, groups: {}, atoms: {} } }));
  const feColored = byElement.atoms.filter((a) => a.element === 'Fe');
  assert.ok(feColored.length > 0);
  assert.ok(feColored.every((a) => a.color === '#123456' && a.colorSource === 'element'));
  assert.equal(byElement.colors.Fe, '#123456', 'o mapa de cores da legenda acompanha a escolha');
  assert.ok(byElement.atoms.filter((a) => a.element === 'Cr').every((a) => a.color === plain.colors.Cr), 'outros elementos não mudam');

  // cor por GRUPO (ocupação do motor) vence a do elemento
  const group = byElement.atoms.find((a) => a.occupancy === 'intersticial')?.occupancy;
  assert.ok(group, 'a liga tem átomo intersticial, informado pelo motor');
  const byGroup = sceneFromAlloy(r, 0, EMPTY_FILTER, appearance({ overrides: { elements: { C: '#123456' }, groups: { [group]: '#abcdef' }, atoms: {} } }));
  const interstitials = byGroup.atoms.filter((a) => a.occupancy === group);
  assert.ok(interstitials.length > 0);
  assert.ok(interstitials.every((a) => a.color === '#abcdef' && a.colorSource === 'group'));

  // cor por ÁTOMO vence grupo e elemento
  const target = interstitials[0] as (typeof interstitials)[number];
  const byAtom = sceneFromAlloy(r, 0, EMPTY_FILTER, appearance({ overrides: { elements: { C: '#123456' }, groups: { [group]: '#abcdef' }, atoms: { [target.id]: '#00ff00' } } }));
  const picked = byAtom.atoms.find((a) => a.id === target.id);
  assert.equal(picked?.color, '#00ff00');
  assert.equal(picked?.colorSource, 'atom');
  assert.equal(byAtom.atoms.filter((a) => a.color === '#00ff00').length, 1, 'a cor por átomo vale para UM átomo');

  // nada científico muda com a aparência: mesmas posições, mesmos elementos, mesma contagem
  assert.equal(byAtom.atoms.length, plain.atoms.length);
  assert.deepEqual(byAtom.atoms.map((a) => a.element), plain.atoms.map((a) => a.element));
  assert.deepEqual(byAtom.atoms.map((a) => a.pos), plain.atoms.map((a) => a.pos));
  assert.deepEqual(byAtom.atoms.map((a) => a.radius), plain.atoms.map((a) => a.radius));
  assert.deepEqual(byAtom.edges, plain.edges);
  assert.equal(byAtom.amplitude, plain.amplitude);
});

test('T-22 aparência: a legenda da cena usa a MESMA resolução de cor, com mais de dois elementos e depois de filtrar', async () => {
  const cl = await api();
  const r = await cl.alloy({ base: 'Fe', n: 3, solutos: [{ elemento: 'Cr', x: 10 }, { elemento: 'Ni', x: 8 }, { elemento: 'Al', x: 4 }, { elemento: 'C', x: 1, modo: 'intersticial' }] });
  const overrides = { elements: { Ni: '#ff8800' }, groups: {}, atoms: {} };
  const legend = alloyLegendWith(r, overrides);
  assert.ok(legend.length >= 4, 'legenda com um item por elemento representado (mais de dois)');
  const base = alloyLegend(r);
  assert.deepEqual(legend.map((l) => l.element), base.map((l) => l.element), 'ordem canônica do motor preservada');
  const ni = legend.find((l) => l.element === 'Ni');
  assert.equal(ni?.color, '#ff8800');
  assert.equal(ni?.custom, true, 'a legenda diz, por palavra, que a cor foi escolhida');
  assert.equal(ni?.defaultColor, base.find((l) => l.element === 'Ni')?.color);
  for (const l of legend.filter((x) => x.element !== 'Ni')) assert.equal(l.custom, false);

  // com filtro de exibição ativo (elemento escondido), a cor dos que continuam desenhados é a mesma
  const filtered = sceneFromAlloy(r, 0, { ...EMPTY_FILTER, hiddenElements: ['Cr'] }, appearance({ overrides }));
  const drawn = filtered.atoms.filter((a) => a.visible);
  assert.ok(drawn.every((a) => a.element !== 'Cr'), 'elemento escondido sai do desenho');
  for (const a of drawn.filter((x) => x.element === 'Ni')) assert.equal(a.color, '#ff8800');
  assert.equal(filtered.colors.Ni, '#ff8800', 'a legenda continua coerente com o que está desenhado');
  assert.equal(filtered.atoms.length, r.atomos.length, 'filtrar e colorir não mudam a contagem do motor');
});

test('T-22 aparência: resolução pura, grupo do átomo, cor válida e "está no padrão?"', () => {
  const ov = { elements: { Fe: '#111111' }, groups: { intersticial: '#222222' }, atoms: { 'a#1': '#333333' } };
  assert.deepEqual(resolveAtomColor({ id: 'a#1', element: 'Fe', occupancy: 'intersticial' }, '#000000', ov), { color: '#333333', source: 'atom' });
  assert.deepEqual(resolveAtomColor({ id: 'outro', element: 'Fe', occupancy: 'intersticial' }, '#000000', ov), { color: '#222222', source: 'group' });
  assert.deepEqual(resolveAtomColor({ id: 'outro', element: 'Fe', occupancy: 'solvente' }, '#000000', ov), { color: '#111111', source: 'element' });
  assert.deepEqual(resolveAtomColor({ id: 'outro', element: 'Ni', occupancy: 'solvente' }, '#000000', ov), { color: '#000000', source: 'default' });

  // grupo = ocupação do motor; sem ocupação, o tipo de sítio (célula do metal puro)
  assert.equal(groupOf({ occupancy: 'substitucional', site: 'vertice' }), 'substitucional');
  assert.equal(groupOf({ occupancy: null, site: 'vertice' }), 'vertice');
  assert.equal(groupOf({ occupancy: null, site: null }), null);

  assert.equal(normalizeColor('#ABC'), '#aabbcc');
  assert.equal(normalizeColor('#0072B2'), '#0072b2');
  assert.equal(normalizeColor('red'), null, 'só o que o seletor de cor produz é aceito');
  assert.equal(normalizeColor('javascript:alert(1)'), null);

  assert.equal(appearanceActive(DEFAULT_APPEARANCE), false);
  assert.equal(appearanceActive({ ...DEFAULT_APPEARANCE, atomScale: 1.4 }), true);
  assert.equal(appearanceActive({ ...DEFAULT_APPEARANCE, opacity: 0.5 }), true);
  assert.equal(appearanceActive({ ...DEFAULT_APPEARANCE, vertices: true }), true);
  assert.equal(appearanceActive({ ...DEFAULT_APPEARANCE, edgeColor: '#123456' }), true);
  assert.equal(appearanceActive({ ...DEFAULT_APPEARANCE, overrides: { elements: { Fe: '#123456' }, groups: {}, atoms: {} } }), true);
});

test('T-22 aparência: o store guarda só exibição, valida a cor e restaura o padrão por seção e geral', async () => {
  const { useAppearance } = await import('../../src/stores/appearance.ts');
  const s = () => useAppearance.getState();
  s().resetAll();
  assert.equal(appearanceActive(s()), false);

  s().setColor('elements', 'Fe', '#ABCDEF');
  assert.equal(s().overrides.elements.Fe, '#abcdef', 'a cor é normalizada antes de ser guardada');
  s().setColor('groups', 'intersticial', 'nao-e-cor');
  assert.equal(s().overrides.groups.intersticial, undefined, 'valor inválido não entra no estado');
  s().setColor('atoms', 'a#1', '#001122');
  s().set({ atomScale: 99, opacity: -3, vertices: true, edgeColor: '#101010' });
  assert.equal(s().atomScale, 2.5, 'a escala fica dentro da faixa de exibição');
  assert.equal(s().opacity, 0.2);

  s().resetAtoms();
  assert.equal(s().atomScale, 1);
  assert.equal(s().opacity, 1);
  assert.equal(s().vertices, true, 'restaurar os átomos não mexe na célula');
  s().resetCell();
  assert.equal(s().vertices, false);
  assert.equal(s().edgeColor, null);
  assert.equal(s().overrides.elements.Fe, '#abcdef', 'restaurar a célula não mexe nas cores');
  s().resetColors('elements');
  assert.deepEqual(s().overrides.elements, {});
  assert.equal(s().overrides.atoms['a#1'], '#001122', 'restaurar um nível não mexe nos outros');
  s().resetAll();
  assert.equal(appearanceActive(s()), false);
  assert.deepEqual(s().overrides, { elements: {}, groups: {}, atoms: {} });
});
