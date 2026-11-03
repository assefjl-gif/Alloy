/**
 * Serializa uma operação no comando canônico equivalente. Usado para mostrar ao estudante
 * a sintaxe do que ele fez por formulário/paleta/viewer (4.8) e no teste de equivalência
 * (parse(toCommand(op)) ≡ op).
 */
import type { Operation } from './types.ts';

function num(v: number): string {
  return String(v);
}

export function toCommand(op: Operation): string | null {
  switch (op.type) {
    case 'material.load': {
      const r = op.request;
      const isStructure = r.nome && ['CS', 'CCC', 'CFC', 'HC'].includes(r.nome);
      if (!r.estrutura && r.raio === undefined && r.peso === undefined && r.c_a === undefined && r.nome && !isStructure) return `usar ${r.nome}`;
      const code = r.estrutura ?? (isStructure ? r.nome : undefined);
      if (code && (!r.nome || isStructure)) {
        const parts = [`estrutura ${code}`];
        if (r.raio !== undefined) parts.push(`r=${num(r.raio)}`);
        if (r.peso !== undefined) parts.push(`A=${num(r.peso)}`);
        if (r.c_a !== undefined) parts.push(`c/a=${num(r.c_a)}`);
        return parts.join(' ');
      }
      const parts = [`usar ${r.nome}`];
      if (r.estrutura) parts.push(`estrutura=${r.estrutura}`);
      if (r.raio !== undefined) parts.push(`r=${num(r.raio)}`);
      if (r.peso !== undefined) parts.push(`A=${num(r.peso)}`);
      if (r.c_a !== undefined) parts.push(`c/a=${num(r.c_a)}`);
      return parts.join(' ');
    }
    case 'editor.apply': return 'aplicar';
    case 'miller.draw': return `${op.tipo} ${op.indices.join(' ')}`;
    case 'density.show': return 'calcular densidade';
    case 'overlays.clear': return null;
    case 'lab.clear': return 'limpar';
    case 'view.atoms': return `esferas ${{ rigid: 'rigidas', reduced: 'reduzidas', ballstick: 'bola-bastao', points: 'pontos' }[op.mode]}`;
    case 'view.toggle': {
      const map = { edges: 'arestas', axes: 'eixos', latticePoints: 'rede', labels: 'rotulos', autoRotate: 'girar', rigid: 'esferas' } as const;
      return op.value === undefined ? map[op.key] : null;
    }
    case 'view.reset': return 'vista';
    case 'supercell.set': return op.n[0] === op.n[1] && op.n[1] === op.n[2] ? `supercelula ${op.n[0]}` : `supercelula ${op.n.join(' ')}`;
    case 'measure.start': return `medir ${op.kind === 'distance' ? 'distancia' : 'angulo'}`;
    case 'measure.add': return `medir ${op.kind === 'distance' ? 'distancia' : 'angulo'} ${op.atoms.map((a) => `${a.index + 1}${a.cell.some((c) => c !== 0) ? `@${a.cell.join('')}` : ''}`).join(' ')}`;
    case 'measure.stop': return 'encerrar medicao';
    case 'history.undo': return 'desfazer';
    case 'history.redo': return 'refazer';
    case 'export': return `exportar ${op.format}`;
    case 'theme.set': return op.theme ? `tema ${op.theme === 'dark' ? 'escuro' : 'claro'}` : 'tema';
    case 'locale.set': return `idioma ${op.locale === 'pt-BR' ? 'pt' : op.locale}`;
    case 'module.open': return `abrir ${op.module}`;
    case 'help': return op.topic ? `ajuda ${op.topic}` : 'ajuda';
    case 'list': return 'listar';
    case 'share': return 'compartilhar';
    case 'animation.open':
      return op.name === 'stacking' ? `animacao empilhamento ${op.variant ?? 'abcabc'}` : op.name === 'alpha-gamma' ? 'animacao alfa-gama' : 'animacao termica';
    case 'workspace.save': return op.name ? `salvar ${op.name}` : 'salvar';
    case 'op.cancel': return 'cancelar';
    case 'hea.load': return `usar ${op.key}`;
    case 'hea.set': return `set ${Object.entries(op.composition).map(([e, v]) => `${e}=${v}`).join(' ')}`;
    case 'hea.add': return `add ${op.element}=${op.amount}`;
    case 'hea.remove': return `rem ${op.element}`;
    case 'hea.name': return `nome ${op.name}`;
    case 'hea.analyze': return 'analisar';
    case 'hea.normalize': return 'normalizar';
    case 'hea.clear': return 'limpar';
    case 'hea.toCrystalab': return op.choice ? `cristalab ${op.choice}` : 'cristalab';
    default: return null;
  }
}
