/**
 * Linguagem de comandos (Etapa 4): gramática, ambiguidades e o teste de equivalência
 * parse(toCommand(op)) ≡ op — garante que formulário, paleta e terminal produzem a mesma operação.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseCommand } from '../../src/commands/parser.ts';
import { toCommand } from '../../src/commands/serialize.ts';
import { tokenize, readIndices } from '../../src/commands/lexer.ts';
import type { Operation } from '../../src/commands/types.ts';
import type { MetalTable } from '../../src/services/api/contracts.ts';

const metal = (nome: string, estrutura: 'CS' | 'CCC' | 'CFC' | 'HC') => ({ nome, estrutura, raio: 0.1, peso: 50, densidade_exp: 7 }) as unknown as MetalTable[string];
const METALS = { Fe: metal('Ferro', 'CCC'), Cu: metal('Cobre', 'CFC'), Mg: metal('Magnésio', 'HC'), Co: metal('Cobalto', 'HC') } as MetalTable;
const ALLOYS = { cantor: { nome: 'Cantor' } };
const cl = { context: 'crystalab' as const, metals: METALS, alloys: null };
const hea = { context: 'hea' as const, metals: null, alloys: ALLOYS };

function parseOk(line: string, ctx: typeof cl | typeof hea = cl): Operation {
  const r = parseCommand(line, ctx);
  assert.equal(r.ok, true, `"${line}" deveria ser válido: ${JSON.stringify(r)}`);
  return (r as { op: Operation }).op;
}

test('verbos de uma e de duas palavras', () => {
  assert.deepEqual(parseOk('calcular densidade'), { type: 'density.show' });
  assert.deepEqual(parseOk('encerrar medicao'), { type: 'measure.stop' });
  assert.deepEqual(parseOk('usar Fe'), { type: 'material.load', request: { nome: 'Fe' } });
});

test('acentos e maiúsculas no verbo são ignorados', () => {
  assert.deepEqual(parseOk('DIREÇÃO 1 1 0'), { type: 'miller.draw', tipo: 'direcao', indices: [1, 1, 0] });
});

test('índices compactos e negativos', () => {
  assert.deepEqual(parseOk('plano 111'), { type: 'miller.draw', tipo: 'plano', indices: [1, 1, 1] });
  assert.deepEqual(parseOk('plano 1-10'), { type: 'miller.draw', tipo: 'plano', indices: [1, -1, 0] });
  assert.deepEqual(parseOk('plano 1 0 -1 1'), { type: 'miller.draw', tipo: 'plano', indices: [1, 0, -1, 1] });
  assert.deepEqual(readIndices(tokenize('2 -1 -1 0'))?.indices, [2, -1, -1, 0]);
});

test('erros dizem o que corrigir', () => {
  const bad = parseCommand('plano 1 1', cl);
  assert.equal(bad.ok, false);
  assert.equal((bad as { error: { key: string } }).error.key, 'cmd.err.indexCount');
  const nonInt = parseCommand('plano 1 1.5 0', cl);
  assert.equal((nonInt as { error: { key: string } }).error.key, 'cmd.err.notInteger');
  const unknown = parseCommand('voar alto', cl);
  assert.equal((unknown as { error: { key: string; hintKey?: string } }).error.key, 'cmd.err.unknownCommand');
  assert.equal((unknown as { error: { hintKey?: string } }).error.hintKey, 'cmd.hint.typeHelp');
  assert.equal((parseCommand('supercelula 5', cl) as { error: { key: string } }).error.key, 'cmd.err.supercellRange');
  assert.equal((parseCommand('', cl) as { error: { key: string } }).error.key, 'cmd.err.empty');
});

test('vírgula decimal e chaves do v1.0', () => {
  assert.deepEqual(parseOk('estrutura CFC r=0,128 A=63,55'), { type: 'material.load', request: { nome: 'CFC', raio: 0.128, peso: 63.55 } });
  assert.deepEqual(parseOk('usar Cu estrutura=CCC'), { type: 'material.load', request: { nome: 'Cu', estrutura: 'CCC' } });
});

test('ambiguidade: "a=" minúsculo pede escolha explícita', () => {
  const r = parseCommand('estrutura CFC r=0.128 a=63.55', cl);
  assert.equal(r.ok, 'ambiguous');
  const amb = (r as { ambiguity: { promptKey: string; choices: Array<{ command: string }> } }).ambiguity;
  assert.equal(amb.promptKey, 'cmd.amb.lowercaseA');
  assert.equal(amb.choices[0]?.command, 'estrutura CFC r=0.128 A=63.55');
});

test('ambiguidade: texto que é metal e estrutura ao mesmo tempo', () => {
  const metals = { ...METALS, Cs: metal('Césio', 'CCC') } as MetalTable;
  const r = parseCommand('usar cs', { ...cl, metals });
  assert.equal(r.ok, 'ambiguous');
  const cmds = (r as { ambiguity: { choices: Array<{ command: string }> } }).ambiguity.choices.map((c) => c.command);
  assert.deepEqual(cmds, ['usar Cs', 'estrutura CS']);
});

test('HEA: pares soltos equivalem a "set"', () => {
  assert.deepEqual(parseOk('Fe=20 Ni=20', hea), { type: 'hea.set', composition: { Fe: 20, Ni: 20 } });
});

const EQUIVALENCE: Array<[Operation, 'crystalab' | 'hea']> = [
  [{ type: 'material.load', request: { nome: 'Fe' } }, 'crystalab'],
  [{ type: 'material.load', request: { nome: 'Cu', estrutura: 'CCC' } }, 'crystalab'],
  [{ type: 'material.load', request: { nome: 'CFC', raio: 0.128, peso: 63.55 } }, 'crystalab'],
  [{ type: 'material.load', request: { nome: 'HC', raio: 0.16, peso: 24.31, c_a: 1.624 } }, 'crystalab'],
  [{ type: 'miller.draw', tipo: 'plano', indices: [1, 1, 1] }, 'crystalab'],
  [{ type: 'miller.draw', tipo: 'plano', indices: [1, 0, -1, 1] }, 'crystalab'],
  [{ type: 'miller.draw', tipo: 'direcao', indices: [1, -1, 0] }, 'crystalab'],
  [{ type: 'density.show' }, 'crystalab'],
  [{ type: 'editor.apply' }, 'crystalab'],
  [{ type: 'lab.clear' }, 'crystalab'],
  [{ type: 'view.atoms', mode: 'ballstick' }, 'crystalab'],
  [{ type: 'view.atoms', mode: 'points' }, 'crystalab'],
  [{ type: 'view.toggle', key: 'axes' }, 'crystalab'],
  [{ type: 'view.toggle', key: 'edges' }, 'crystalab'],
  [{ type: 'view.toggle', key: 'latticePoints' }, 'crystalab'],
  [{ type: 'view.toggle', key: 'labels' }, 'crystalab'],
  [{ type: 'view.toggle', key: 'autoRotate' }, 'crystalab'],
  [{ type: 'view.reset' }, 'crystalab'],
  [{ type: 'supercell.set', n: [2, 2, 2] }, 'crystalab'],
  [{ type: 'supercell.set', n: [3, 2, 1] }, 'crystalab'],
  [{ type: 'measure.start', kind: 'distance' }, 'crystalab'],
  [{ type: 'measure.start', kind: 'angle' }, 'crystalab'],
  [{ type: 'measure.add', kind: 'distance', atoms: [{ index: 0, cell: [0, 0, 0] }, { index: 4, cell: [1, 0, 0] }] }, 'crystalab'],
  [{ type: 'measure.stop' }, 'crystalab'],
  [{ type: 'history.undo' }, 'crystalab'],
  [{ type: 'history.redo' }, 'crystalab'],
  [{ type: 'export', format: 'cif' }, 'crystalab'],
  [{ type: 'export', format: 'png' }, 'crystalab'],
  [{ type: 'theme.set', theme: 'dark' }, 'crystalab'],
  [{ type: 'locale.set', locale: 'es' }, 'crystalab'],
  [{ type: 'module.open', module: 'hea' }, 'crystalab'],
  [{ type: 'help' }, 'crystalab'],
  [{ type: 'list' }, 'crystalab'],
  [{ type: 'share' }, 'crystalab'],
  [{ type: 'animation.open', name: 'stacking', variant: 'abab' }, 'crystalab'],
  [{ type: 'animation.open', name: 'alpha-gamma' }, 'crystalab'],
  [{ type: 'animation.open', name: 'thermal' }, 'crystalab'],
  [{ type: 'workspace.save', name: 'aula 3' }, 'crystalab'],
  [{ type: 'op.cancel' }, 'crystalab'],
  [{ type: 'hea.load', key: 'cantor' }, 'hea'],
  [{ type: 'hea.set', composition: { Co: 1, Cr: 1, Fe: 1 } }, 'hea'],
  [{ type: 'hea.add', element: 'Al', amount: 0.5 }, 'hea'],
  [{ type: 'hea.remove', element: 'Mn' }, 'hea'],
  [{ type: 'hea.name', name: 'Minha liga' }, 'hea'],
  [{ type: 'hea.analyze' }, 'hea'],
  [{ type: 'hea.normalize' }, 'hea'],
  [{ type: 'hea.clear' }, 'hea'],
  [{ type: 'hea.toCrystalab' }, 'hea'],
  [{ type: 'hea.toCrystalab', choice: 'CCC' }, 'hea'],
];

for (const [op, context] of EQUIVALENCE) {
  test(`equivalência: ${JSON.stringify(op)}`, () => {
    const cmd = toCommand(op);
    assert.ok(cmd, 'operação sem comando equivalente');
    const parsed = parseCommand(cmd, context === 'hea' ? hea : cl);
    assert.equal(parsed.ok, true, `"${cmd}" → ${JSON.stringify(parsed)}`);
    assert.deepEqual((parsed as { op: Operation }).op, op, `"${cmd}"`);
  });
}
