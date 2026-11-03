import type { StructureCode, StructureRequest } from '../services/api/contracts.ts';
import type { AnimationName, AtomMode } from '../stores/viewer.ts';
import type { AtomRef } from '../stores/overlays.ts';
import type { Locale } from '../utils/format.ts';
import type { MessageKey, Vars } from '../i18n/index.ts';

export type ModuleId = 'crystalab' | 'hea' | 'aprender' | 'professor' | 'diario' | 'catalogo' | 'sobre' | 'conta';
export type ViewToggleKey = 'edges' | 'axes' | 'latticePoints' | 'labels' | 'autoRotate' | 'rigid';
export type ExportFormat = 'cif' | 'xyz' | 'png' | 'pdf' | 'json';

/**
 * Operação: a única forma de mudar o laboratório. Terminal, formulários, paleta e viewer
 * produzem operações e as entregam ao barramento (tarefa 4.3).
 */
export type Operation =
  | { type: 'material.load'; request: StructureRequest }
  | { type: 'editor.apply' }
  | { type: 'miller.draw'; tipo: 'plano' | 'direcao'; indices: number[] }
  | { type: 'density.show' }
  | { type: 'overlays.clear' }
  | { type: 'lab.clear' }
  | { type: 'view.atoms'; mode: AtomMode }
  | { type: 'view.toggle'; key: ViewToggleKey; value?: boolean }
  | { type: 'view.reset' }
  | { type: 'supercell.set'; n: [number, number, number] }
  | { type: 'measure.start'; kind: 'distance' | 'angle' }
  | { type: 'measure.add'; kind: 'distance' | 'angle'; atoms: AtomRef[] }
  | { type: 'measure.stop' }
  | { type: 'history.undo' }
  | { type: 'history.redo' }
  | { type: 'export'; format: ExportFormat }
  | { type: 'theme.set'; theme?: 'light' | 'dark' }
  | { type: 'locale.set'; locale: Locale }
  | { type: 'module.open'; module: ModuleId }
  | { type: 'help'; topic?: string }
  | { type: 'list' }
  | { type: 'share' }
  | { type: 'animation.open'; name: AnimationName; variant?: string }
  | { type: 'workspace.save'; name?: string }
  | { type: 'op.cancel' }
  | { type: 'hea.load'; key: string }
  | { type: 'hea.set'; composition: Record<string, number> }
  | { type: 'hea.add'; element: string; amount: number }
  | { type: 'hea.remove'; element: string }
  | { type: 'hea.name'; name: string }
  | { type: 'hea.analyze' }
  | { type: 'hea.normalize' }
  | { type: 'hea.clear' }
  | { type: 'hea.toCrystalab'; choice?: StructureCode };

export type OperationType = Operation['type'];

export type Source = 'terminal' | 'form' | 'palette' | 'viewer' | 'shortcut' | 'block' | 'url' | 'exercise' | 'system';

export interface ParseError {
  key: MessageKey;
  vars?: Vars;
  /** como corrigir (4.5) */
  hintKey?: MessageKey;
  hintVars?: Vars;
  position?: number;
}

/** Ambiguidade que exige escolha explícita do usuário (4.2). */
export interface Ambiguity {
  promptKey: MessageKey;
  promptVars?: Vars;
  choices: Array<{ labelKey: MessageKey; labelVars?: Vars; command: string }>;
}

export type ParseResult =
  | { ok: true; op: Operation; warnings?: ParseError[] }
  | { ok: false; error: ParseError }
  | { ok: 'ambiguous'; ambiguity: Ambiguity };

export type Context = 'crystalab' | 'hea';
