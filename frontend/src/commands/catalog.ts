/**
 * Catálogo de comandos: sintaxe, exemplos, categoria e regra de análise de cada verbo.
 * É a fonte única para o parser, o autocompletar, a ajuda e a paleta de comandos.
 * Todos os comandos do CrystaLab v1.0 e do HEA v1.17 continuam válidos.
 */
import type { MessageKey } from '../i18n/index.ts';
import type { MetalTable, StructureCode, StructureRequest } from '../services/api/contracts.ts';
import type { Token } from './lexer.ts';
import { readIndices } from './lexer.ts';
import type { Context, ExportFormat, ModuleId, Operation, ParseResult } from './types.ts';
import type { AtomRef } from '../stores/overlays.ts';

export type CommandCategory = 'material' | 'miller' | 'calc' | 'view' | 'history' | 'export' | 'app' | 'hea' | 'didactic';

export interface ParseContext {
  context: Context;
  metals: MetalTable | null;
  alloys: Record<string, { nome: string }> | null;
  /** texto original completo (para mensagens que citam a entrada) */
  raw: string;
}

export interface CommandSpec {
  verb: string;
  aliases: string[];
  contexts: Context[];
  category: CommandCategory;
  syntax: string;
  examples: string[];
  descriptionKey: MessageKey;
  parse: (args: Token[], ctx: ParseContext) => ParseResult;
  /** sugestões para o primeiro argumento (autocompletar contextual, 4.4) */
  complete?: (ctx: ParseContext) => string[];
}

const ok = (op: Operation): ParseResult => ({ ok: true, op });
const err = (key: MessageKey, vars?: Record<string, string | number>, hintKey?: MessageKey, hintVars?: Record<string, string | number>, position?: number): ParseResult => ({
  ok: false,
  error: { key, ...(vars ? { vars } : {}), ...(hintKey ? { hintKey } : {}), ...(hintVars ? { hintVars } : {}), ...(position !== undefined ? { position } : {}) },
});

const noArgs = (op: Operation) => (args: Token[]): ParseResult =>
  args.length ? err('cmd.err.noArgs', { arg: args[0]?.raw ?? '' }, 'cmd.hint.removeArgs', undefined, args[0]?.start) : ok(op);

export const STRUCTURE_ALIASES: Record<string, StructureCode> = {
  cs: 'CS', sc: 'CS', cubicasimples: 'CS',
  ccc: 'CCC', bcc: 'CCC', cubicadecorpocentrado: 'CCC',
  cfc: 'CFC', fcc: 'CFC', cubicadefacecentrada: 'CFC',
  hc: 'HC', hcp: 'HC', hexagonalcompacta: 'HC',
};

function parseDecimal(text: string | undefined): number | null {
  if (text === undefined) return null;
  const v = Number(text.replace(',', '.'));
  return Number.isFinite(v) ? v : null;
}

/**
 * Resolve `usar X [estrutura=… r=… A=… c/a=…]` com a mesma precedência do motor v1.1:
 * símbolo exato → sigla de estrutura → nome/apelido (resolvidos pelo motor). Os pares
 * opcionais sobrescrevem parâmetros do metal (equivalem ao editor de parâmetros).
 */
function parseUse(args: Token[], ctx: ParseContext): ParseResult {
  const nameTokens = args.filter((a) => a.type !== 'pair');
  const pairs = args.filter((a) => a.type === 'pair');
  if (!nameTokens.length) return err('cmd.err.missingMaterial', undefined, 'cmd.hint.useExample');
  const text = nameTokens.map((a) => a.raw).join(' ').trim();
  const lower = text.toLowerCase();
  const metals = ctx.metals ?? {};
  const exactSymbol = Object.keys(metals).find((s) => s === text);
  const ciSymbol = Object.keys(metals).find((s) => s.toLowerCase() === lower);
  const structure = STRUCTURE_ALIASES[lower.replace(/\s+/g, '')];
  let request: StructureRequest;
  if (exactSymbol) request = { nome: exactSymbol };
  else if (ciSymbol && structure) {
    return {
      ok: 'ambiguous',
      ambiguity: {
        promptKey: 'cmd.amb.metalOrStructure',
        promptVars: { text },
        choices: [
          { labelKey: 'cmd.amb.chooseMetal', labelVars: { symbol: ciSymbol, name: metals[ciSymbol]?.nome ?? ciSymbol }, command: `usar ${ciSymbol}` },
          { labelKey: 'cmd.amb.chooseStructure', labelVars: { code: structure }, command: `estrutura ${structure}` },
        ],
      },
    };
  } else if (ciSymbol) request = { nome: ciSymbol };
  else if (structure) request = { nome: structure };
  // Nomes e apelidos (ferro, copper…) são resolvidos pelo motor: o front não duplica a regra.
  else request = { nome: text };
  for (const t of pairs) {
    const key = t.value.toLowerCase();
    if (key === 'estrutura') {
      const code = STRUCTURE_ALIASES[(t.pairValue ?? '').toLowerCase()];
      if (!code) return err('cmd.err.unknownStructure', { text: t.pairValue ?? '' }, 'cmd.hint.structureExample', undefined, t.start);
      request.estrutura = code;
      continue;
    }
    const v = parseDecimal(t.pairValue);
    if (v === null) return err('cmd.err.badNumber', { text: t.raw }, 'cmd.hint.decimal', undefined, t.start);
    if (t.value === 'r' || t.value === 'R' || key === 'raio') request.raio = v;
    else if (t.value === 'A' || key === 'peso' || key === 'massa') request.peso = v;
    else if (key === 'c/a' || key === 'ca') request.c_a = v;
    else return err('cmd.err.unknownKey', { key: t.value }, 'cmd.hint.useKeys', undefined, t.start);
  }
  return ok({ type: 'material.load', request });
}

/** `estrutura CFC r=0.128 A=63.55 c/a=1.62` — mesma sintaxe do v1.0, com a ambiguidade de `a=` explicitada. */
function parseStructure(args: Token[]): ParseResult {
  const first = args[0];
  if (!first || first.type !== 'word') return err('cmd.err.missingStructure', undefined, 'cmd.hint.structureExample');
  const code = STRUCTURE_ALIASES[first.value];
  if (!code) return err('cmd.err.unknownStructure', { text: first.raw }, 'cmd.hint.structureExample', undefined, first.start);
  const request: StructureRequest = { nome: code };
  for (const t of args.slice(1)) {
    if (t.type !== 'pair') return err('cmd.err.expectedPair', { text: t.raw }, 'cmd.hint.structureExample', undefined, t.start);
    const v = parseDecimal(t.pairValue);
    if (v === null) return err('cmd.err.badNumber', { text: t.raw }, 'cmd.hint.decimal', undefined, t.start);
    const key = t.value;
    if (key === 'r' || key === 'R' || key.toLowerCase() === 'raio') request.raio = v;
    else if (key === 'A' || key.toLowerCase() === 'peso' || key.toLowerCase() === 'massa') request.peso = v;
    else if (key.toLowerCase() === 'c/a' || key.toLowerCase() === 'ca') request.c_a = v;
    else if (key === 'a') {
      // Ambíguo: no v1.0 `a=` (minúsculo) significava massa atômica A; aqui também pode ser lido como parâmetro de rede.
      const rest = args.slice(1).filter((x) => x !== t).map((x) => x.raw).join(' ');
      return {
        ok: 'ambiguous',
        ambiguity: {
          promptKey: 'cmd.amb.lowercaseA',
          promptVars: { value: t.pairValue ?? '' },
          choices: [
            { labelKey: 'cmd.amb.chooseAtomicMass', labelVars: { value: t.pairValue ?? '' }, command: `estrutura ${code} ${rest ? `${rest} ` : ''}A=${t.pairValue ?? ''}`.replace(/\s+/g, ' ').trim() },
            { labelKey: 'cmd.amb.chooseLattice', command: `ajuda estrutura` },
          ],
        },
      };
    } else return err('cmd.err.unknownKey', { key }, 'cmd.hint.structureKeys', undefined, t.start);
  }
  return ok({ type: 'material.load', request });
}

function parseMiller(tipo: 'plano' | 'direcao') {
  return (args: Token[]): ParseResult => {
    const read = readIndices(args);
    if (!read || !read.indices.length) return err('cmd.err.missingIndices', undefined, tipo === 'plano' ? 'cmd.hint.planeExample' : 'cmd.hint.directionExample');
    if (read.badToken) return err('cmd.err.notInteger', { text: read.badToken.raw }, 'cmd.hint.indicesIntegers', undefined, read.badToken.start);
    if (read.indices.length < 3 || read.indices.length > 4) return err('cmd.err.indexCount', { count: read.indices.length }, tipo === 'plano' ? 'cmd.hint.planeExample' : 'cmd.hint.directionExample');
    return ok({ type: 'miller.draw', tipo, indices: read.indices });
  };
}

function parseSupercell(args: Token[]): ParseResult {
  const nums = args.filter((a) => a.type === 'number').map((a) => a.num as number);
  const bad = args.find((a) => a.type !== 'number' && a.type !== 'sep' && !(a.type === 'word' && /^\d+x\d+x\d+$/i.test(a.raw)));
  const compact = args.find((a) => a.type === 'word' && /^\d+x\d+x\d+$/i.test(a.raw));
  const values = compact ? compact.raw.toLowerCase().split('x').map(Number) : nums;
  if (bad || !(values.length === 1 || values.length === 3)) return err('cmd.err.supercell', undefined, 'cmd.hint.supercellExample');
  const n = (values.length === 1 ? [values[0], values[0], values[0]] : values) as [number, number, number];
  if (n.some((v) => !Number.isInteger(v) || v < 1 || v > 4)) return err('cmd.err.supercellRange', undefined, 'cmd.hint.supercellExample');
  return ok({ type: 'supercell.set', n });
}

const ATOM_MODES: Record<string, 'reduced' | 'rigid' | 'ballstick' | 'points'> = {
  rigidas: 'rigid', rigida: 'rigid', reduzidas: 'reduced', reduzida: 'reduced', 'bola-bastao': 'ballstick', bolabastao: 'ballstick', bastao: 'ballstick', pontos: 'points',
};

function parseSpheres(args: Token[]): ParseResult {
  if (!args.length) return ok({ type: 'view.toggle', key: 'rigid' });
  const mode = ATOM_MODES[(args[0] as Token).value];
  if (!mode) return err('cmd.err.unknownOption', { text: (args[0] as Token).raw }, 'cmd.hint.spheresOptions');
  return ok({ type: 'view.atoms', mode });
}

const EXPORTS: ExportFormat[] = ['cif', 'xyz', 'png', 'pdf', 'json'];
const MODULES: Record<string, ModuleId> = { crystalab: 'crystalab', cristalab: 'crystalab', hea: 'hea', aprender: 'aprender', exercicios: 'aprender', professor: 'professor', diario: 'diario', catalogo: 'catalogo', sobre: 'sobre' };

function parseHeaPairs(args: Token[]): Record<string, number> {
  const out: Record<string, number> = {};
  const text = args.map((a) => a.raw).join(' ');
  const re = /([A-Za-z][a-z]?)\s*(?:=|:|\s)\s*(-?\d+(?:[.,]\d+)?)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const raw = m[1] ?? '';
    const el = raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase();
    const v = Number((m[2] ?? '').replace(',', '.'));
    if (Number.isFinite(v) && v > 0) out[el] = v;
  }
  return out;
}

export const COMMANDS: CommandSpec[] = [
  // ---------------- CrystaLab ----------------
  { verb: 'usar', aliases: ['use', 'carregar'], contexts: ['crystalab'], category: 'material', syntax: 'usar <metal | estrutura> [estrutura=…] [r=…] [A=…] [c/a=…]', examples: ['usar Cu', 'usar ferro', 'usar Fe estrutura=CFC'], descriptionKey: 'cmd.desc.usar', parse: parseUse,
    complete: (ctx) => Object.keys(ctx.metals ?? {}) },
  { verb: 'estrutura', aliases: ['structure'], contexts: ['crystalab'], category: 'material', syntax: 'estrutura <CS|CCC|CFC|HC> [r=<nm>] [A=<g/mol>] [c/a=<razão>]', examples: ['estrutura CFC', 'estrutura CFC r=0.128 A=63.55', 'estrutura HC r=0.16 A=24.31 c/a=1.624'], descriptionKey: 'cmd.desc.estrutura', parse: parseStructure,
    complete: () => ['CS', 'CCC', 'CFC', 'HC'] },
  { verb: 'plano', aliases: ['plane'], contexts: ['crystalab'], category: 'miller', syntax: 'plano <h k l> | <h k i l>', examples: ['plano 1 1 1', 'plano (110)', 'plano 1 0 -1 1'], descriptionKey: 'cmd.desc.plano', parse: parseMiller('plano'),
    complete: () => ['1 0 0', '1 1 0', '1 1 1', '0 0 0 1', '1 0 -1 0'] },
  { verb: 'direcao', aliases: ['dir', 'direction'], contexts: ['crystalab'], category: 'miller', syntax: 'direcao <u v w> | <u v t w>', examples: ['direcao 1 1 0', 'direcao [111]', 'direcao 1 1 -2 0'], descriptionKey: 'cmd.desc.direcao', parse: parseMiller('direcao'),
    complete: () => ['1 0 0', '1 1 0', '1 1 1', '1 1 -2 0'] },
  { verb: 'calcular densidade', aliases: ['densidade', 'density'], contexts: ['crystalab'], category: 'calc', syntax: 'calcular densidade', examples: ['calcular densidade'], descriptionKey: 'cmd.desc.densidade', parse: noArgs({ type: 'density.show' }) },
  { verb: 'aplicar', aliases: ['renderizar', 'render'], contexts: ['crystalab'], category: 'material', syntax: 'aplicar', examples: ['aplicar'], descriptionKey: 'cmd.desc.aplicar', parse: noArgs({ type: 'editor.apply' }) },
  { verb: 'listar', aliases: ['list'], contexts: ['crystalab'], category: 'material', syntax: 'listar', examples: ['listar'], descriptionKey: 'cmd.desc.listar', parse: noArgs({ type: 'list' }) },
  { verb: 'supercelula', aliases: ['supercell'], contexts: ['crystalab'], category: 'view', syntax: 'supercelula <n> | <nx ny nz>  (1 a 4)', examples: ['supercelula 2', 'supercelula 3 3 3', 'supercelula 1'], descriptionKey: 'cmd.desc.supercelula', parse: parseSupercell,
    complete: () => ['1', '2', '3', '2 2 1', '3 3 3'] },
  { verb: 'esferas', aliases: ['spheres'], contexts: ['crystalab'], category: 'view', syntax: 'esferas [rigidas|reduzidas|bola-bastao|pontos]', examples: ['esferas', 'esferas rigidas', 'esferas bola-bastao'], descriptionKey: 'cmd.desc.esferas', parse: parseSpheres,
    complete: () => ['rigidas', 'reduzidas', 'bola-bastao', 'pontos'] },
  { verb: 'girar', aliases: ['rotate'], contexts: ['crystalab'], category: 'view', syntax: 'girar', examples: ['girar'], descriptionKey: 'cmd.desc.girar', parse: noArgs({ type: 'view.toggle', key: 'autoRotate' }) },
  { verb: 'eixos', aliases: ['axes'], contexts: ['crystalab'], category: 'view', syntax: 'eixos', examples: ['eixos'], descriptionKey: 'cmd.desc.eixos', parse: noArgs({ type: 'view.toggle', key: 'axes' }) },
  { verb: 'arestas', aliases: ['edges'], contexts: ['crystalab'], category: 'view', syntax: 'arestas', examples: ['arestas'], descriptionKey: 'cmd.desc.arestas', parse: noArgs({ type: 'view.toggle', key: 'edges' }) },
  { verb: 'rede', aliases: ['pontos de rede', 'lattice'], contexts: ['crystalab'], category: 'view', syntax: 'rede', examples: ['rede'], descriptionKey: 'cmd.desc.rede', parse: noArgs({ type: 'view.toggle', key: 'latticePoints' }) },
  { verb: 'rotulos', aliases: ['labels'], contexts: ['crystalab'], category: 'view', syntax: 'rotulos', examples: ['rotulos'], descriptionKey: 'cmd.desc.rotulos', parse: noArgs({ type: 'view.toggle', key: 'labels' }) },
  { verb: 'vista', aliases: ['resetar vista', 'reset'], contexts: ['crystalab'], category: 'view', syntax: 'vista', examples: ['vista'], descriptionKey: 'cmd.desc.vista', parse: noArgs({ type: 'view.reset' }) },
  { verb: 'medir', aliases: ['measure'], contexts: ['crystalab'], category: 'view', syntax: 'medir <distancia|angulo> [átomos: 1 5 ou 1 5@100]', examples: ['medir distancia', 'medir distancia 1 9', 'medir angulo 1 9 2'], descriptionKey: 'cmd.desc.medir',
    parse: (args) => {
      const w = args[0]?.value;
      const kind = w === 'distancia' || w === 'distance' ? 'distance' : w === 'angulo' || w === 'angle' ? 'angle' : null;
      if (!kind) return err('cmd.err.unknownOption', { text: args[0]?.raw ?? '' }, 'cmd.hint.measureOptions');
      const refs = args.slice(1);
      if (!refs.length) return ok({ type: 'measure.start', kind });
      const atoms: AtomRef[] = [];
      for (const t of refs) {
        const m = t.raw.match(/^(\d+)(?:@([0-3])([0-3])([0-3]))?$/);
        if (!m) return err('cmd.err.atomRef', { text: t.raw }, 'cmd.hint.atomRef', undefined, t.start);
        atoms.push({ index: Number(m[1]) - 1, cell: [Number(m[2] ?? 0), Number(m[3] ?? 0), Number(m[4] ?? 0)] });
      }
      if (atoms.length !== (kind === 'distance' ? 2 : 3)) return err('cmd.err.atomCount', { count: kind === 'distance' ? 2 : 3 }, 'cmd.hint.atomRef');
      return ok({ type: 'measure.add', kind, atoms });
    },
    complete: () => ['distancia', 'angulo'] },
  { verb: 'encerrar medicao', aliases: ['parar medicao'], contexts: ['crystalab'], category: 'view', syntax: 'encerrar medicao', examples: ['encerrar medicao'], descriptionKey: 'cmd.desc.encerrarMedicao', parse: noArgs({ type: 'measure.stop' }) },
  { verb: 'animacao', aliases: ['animation'], contexts: ['crystalab'], category: 'didactic', syntax: 'animacao <empilhamento [abab|abcabc] | alfa-gama | termica>', examples: ['animacao empilhamento abcabc', 'animacao alfa-gama', 'animacao termica'], descriptionKey: 'cmd.desc.animacao',
    parse: (args) => {
      const w = args[0]?.value;
      if (w === 'empilhamento' || w === 'stacking') {
        const v = args[1]?.value ?? 'abcabc';
        if (v !== 'abab' && v !== 'abcabc') return err('cmd.err.unknownOption', { text: args[1]?.raw ?? '' }, 'cmd.hint.animationOptions');
        return ok({ type: 'animation.open', name: 'stacking', variant: v });
      }
      if (w === 'alfa-gama' || w === 'alfagama' || w === 'alpha-gamma') return ok({ type: 'animation.open', name: 'alpha-gamma' });
      if (w === 'termica' || w === 'thermal' || w === 'expansao') return ok({ type: 'animation.open', name: 'thermal' });
      return err('cmd.err.unknownOption', { text: args[0]?.raw ?? '' }, 'cmd.hint.animationOptions');
    },
    complete: () => ['empilhamento abab', 'empilhamento abcabc', 'alfa-gama', 'termica'] },
  { verb: 'exportar', aliases: ['export'], contexts: ['crystalab'], category: 'export', syntax: 'exportar <cif|xyz|png|pdf|json>', examples: ['exportar png', 'exportar cif'], descriptionKey: 'cmd.desc.exportar',
    parse: (args) => {
      const f = args[0]?.value as ExportFormat | undefined;
      if (!f || !EXPORTS.includes(f)) return err('cmd.err.unknownOption', { text: args[0]?.raw ?? '' }, 'cmd.hint.exportOptions');
      return ok({ type: 'export', format: f });
    },
    complete: () => EXPORTS.slice() },
  { verb: 'compartilhar', aliases: ['share', 'link'], contexts: ['crystalab'], category: 'export', syntax: 'compartilhar', examples: ['compartilhar'], descriptionKey: 'cmd.desc.compartilhar', parse: noArgs({ type: 'share' }) },
  { verb: 'salvar', aliases: ['save'], contexts: ['crystalab'], category: 'export', syntax: 'salvar [nome]', examples: ['salvar', 'salvar aula de CFC'], descriptionKey: 'cmd.desc.salvar',
    parse: (args) => ok(args.length ? { type: 'workspace.save', name: args.map((a) => a.raw).join(' ') } : { type: 'workspace.save' }) },
  { verb: 'limpar', aliases: ['clear'], contexts: ['crystalab'], category: 'view', syntax: 'limpar', examples: ['limpar'], descriptionKey: 'cmd.desc.limpar', parse: noArgs({ type: 'lab.clear' }) },
  { verb: 'desfazer', aliases: ['undo'], contexts: ['crystalab'], category: 'history', syntax: 'desfazer', examples: ['desfazer'], descriptionKey: 'cmd.desc.desfazer', parse: noArgs({ type: 'history.undo' }) },
  { verb: 'refazer', aliases: ['redo'], contexts: ['crystalab'], category: 'history', syntax: 'refazer', examples: ['refazer'], descriptionKey: 'cmd.desc.refazer', parse: noArgs({ type: 'history.redo' }) },
  // ---------------- HEA (sintaxe do v1.17) ----------------
  { verb: 'usar', aliases: [], contexts: ['hea'], category: 'hea', syntax: 'usar <liga>', examples: ['usar demo_a'], descriptionKey: 'cmd.desc.heaUsar',
    parse: (args, ctx) => {
      const alias = args.map((a) => a.raw).join(' ').trim().toLowerCase();
      if (!alias) return err('cmd.err.missingAlloy', undefined, 'cmd.hint.heaUseExample');
      const found = Object.entries(ctx.alloys ?? {}).find(([k, a]) => `${k} ${a.nome}`.toLowerCase().includes(alias));
      if (!found) return err('cmd.err.unknownAlloy', { text: alias }, 'cmd.hint.heaUseExample');
      return ok({ type: 'hea.load', key: found[0] });
    },
    complete: (ctx) => Object.keys(ctx.alloys ?? {}) },
  { verb: 'set', aliases: ['definir'], contexts: ['hea'], category: 'hea', syntax: 'set <El>=<qtd> <El>=<qtd> ...', examples: ['set Fe=20 Ni=20 Cr=20 Co=20 Mn=20'], descriptionKey: 'cmd.desc.heaSet',
    parse: (args) => {
      const c = parseHeaPairs(args);
      if (Object.keys(c).length < 2) return err('cmd.err.heaTwoElements', undefined, 'cmd.hint.heaSetExample');
      return ok({ type: 'hea.set', composition: c });
    } },
  { verb: 'add', aliases: ['somar'], contexts: ['hea'], category: 'hea', syntax: 'add <El>=<qtd>', examples: ['add Cu=5'], descriptionKey: 'cmd.desc.heaAdd',
    parse: (args) => {
      const c = parseHeaPairs(args);
      const [el, v] = Object.entries(c)[0] ?? [];
      if (!el || v === undefined) return err('cmd.err.heaPair', undefined, 'cmd.hint.heaAddExample');
      return ok({ type: 'hea.add', element: el, amount: v });
    } },
  { verb: 'rem', aliases: ['remove', 'remover'], contexts: ['hea'], category: 'hea', syntax: 'rem <El>', examples: ['rem Cu'], descriptionKey: 'cmd.desc.heaRem',
    parse: (args) => {
      const raw = args[0]?.raw ?? '';
      if (!/^[A-Za-z][a-z]?$/.test(raw)) return err('cmd.err.heaElement', { text: raw }, 'cmd.hint.heaRemExample');
      return ok({ type: 'hea.remove', element: raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase() });
    } },
  { verb: 'nome', aliases: ['name'], contexts: ['hea'], category: 'hea', syntax: 'nome <texto>', examples: ['nome Minha Liga'], descriptionKey: 'cmd.desc.heaNome',
    parse: (args) => (args.length ? ok({ type: 'hea.name', name: args.map((a) => a.raw).join(' ') }) : err('cmd.err.missingName', undefined, 'cmd.hint.heaNameExample')) },
  { verb: 'analisar', aliases: ['run'], contexts: ['hea'], category: 'hea', syntax: 'analisar', examples: ['analisar'], descriptionKey: 'cmd.desc.heaAnalisar', parse: noArgs({ type: 'hea.analyze' }) },
  { verb: 'normalizar', aliases: ['normalize'], contexts: ['hea'], category: 'hea', syntax: 'normalizar', examples: ['normalizar'], descriptionKey: 'cmd.desc.heaNormalizar', parse: noArgs({ type: 'hea.normalize' }) },
  { verb: 'limpar', aliases: ['clear'], contexts: ['hea'], category: 'hea', syntax: 'limpar', examples: ['limpar'], descriptionKey: 'cmd.desc.heaLimpar', parse: noArgs({ type: 'hea.clear' }) },
  { verb: 'cristalab', aliases: ['crystalab', 'abrir crystalab', 'abrir cristalab'], contexts: ['hea'], category: 'hea', syntax: 'cristalab [CS|CCC|CFC|HC]', examples: ['cristalab', 'cristalab CFC'], descriptionKey: 'cmd.desc.heaCrystalab',
    parse: (args) => {
      if (!args.length) return ok({ type: 'hea.toCrystalab' });
      const code = STRUCTURE_ALIASES[(args[0] as Token).value];
      if (!code) return err('cmd.err.unknownStructure', { text: (args[0] as Token).raw }, 'cmd.hint.structureExample');
      return ok({ type: 'hea.toCrystalab', choice: code });
    },
    complete: () => ['CFC', 'CCC', 'HC'] },
  // ---------------- Globais ----------------
  { verb: 'ajuda', aliases: ['help', '?'], contexts: ['crystalab', 'hea'], category: 'app', syntax: 'ajuda [comando]', examples: ['ajuda', 'ajuda plano'], descriptionKey: 'cmd.desc.ajuda',
    parse: (args) => ok(args.length ? { type: 'help', topic: args.map((a) => a.value).join(' ') } : { type: 'help' }) },
  { verb: 'tema', aliases: ['theme'], contexts: ['crystalab', 'hea'], category: 'app', syntax: 'tema [claro|escuro]', examples: ['tema', 'tema escuro'], descriptionKey: 'cmd.desc.tema',
    parse: (args) => {
      const w = args[0]?.value;
      if (!w) return ok({ type: 'theme.set' });
      if (w === 'claro' || w === 'light') return ok({ type: 'theme.set', theme: 'light' });
      if (w === 'escuro' || w === 'dark') return ok({ type: 'theme.set', theme: 'dark' });
      return err('cmd.err.unknownOption', { text: args[0]?.raw ?? '' }, 'cmd.hint.themeOptions');
    },
    complete: () => ['claro', 'escuro'] },
  { verb: 'idioma', aliases: ['language', 'lang'], contexts: ['crystalab', 'hea'], category: 'app', syntax: 'idioma <pt|en|es>', examples: ['idioma en'], descriptionKey: 'cmd.desc.idioma',
    parse: (args) => {
      const w = args[0]?.value;
      if (w === 'pt' || w === 'pt-br') return ok({ type: 'locale.set', locale: 'pt-BR' });
      if (w === 'en') return ok({ type: 'locale.set', locale: 'en' });
      if (w === 'es') return ok({ type: 'locale.set', locale: 'es' });
      return err('cmd.err.unknownOption', { text: args[0]?.raw ?? '' }, 'cmd.hint.localeOptions');
    },
    complete: () => ['pt', 'en', 'es'] },
  { verb: 'abrir', aliases: ['open', 'modulo'], contexts: ['crystalab', 'hea'], category: 'app', syntax: 'abrir <crystalab|hea|aprender|professor|diario>', examples: ['abrir hea', 'abrir aprender'], descriptionKey: 'cmd.desc.abrir',
    parse: (args) => {
      const m = MODULES[args[0]?.value ?? ''];
      return m ? ok({ type: 'module.open', module: m }) : err('cmd.err.unknownOption', { text: args[0]?.raw ?? '' }, 'cmd.hint.moduleOptions');
    },
    complete: () => ['crystalab', 'hea', 'aprender', 'professor', 'diario'] },
  { verb: 'cancelar', aliases: ['cancel', 'parar'], contexts: ['crystalab', 'hea'], category: 'app', syntax: 'cancelar', examples: ['cancelar'], descriptionKey: 'cmd.desc.cancelar', parse: noArgs({ type: 'op.cancel' }) },
];

export function specsFor(context: Context): CommandSpec[] {
  return COMMANDS.filter((c) => c.contexts.includes(context));
}
