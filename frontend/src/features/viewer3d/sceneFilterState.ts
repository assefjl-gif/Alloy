/**
 * Ponte entre o store de filtros (T-23) e o filtro de VISIBILIDADE usado pela cena e pelos painéis.
 * Fica fora do `SceneController` (e não importa Three.js) para a barra lateral poder calcular a
 * mesma visibilidade que o viewer desenha, sem carregar o motor gráfico.
 *
 * Nada científico acontece aqui: só se resolve o centro da vizinhança de exibição a partir do
 * átomo selecionado, usando as posições que o motor devolveu.
 */
import type { AlloyResult, StructureResult, Vec3 } from '../../services/api/contracts.ts';
import { atomKey, type AtomRef } from '../../stores/overlays.ts';
import { useAlloy } from '../../stores/alloy.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useSceneFilter, type SceneFilterState } from '../../stores/sceneFilter.ts';
import { useViewer } from '../../stores/viewer.ts';
import { buildAtoms } from './geometry.ts';
import { alloyAtomId } from './alloyScene.ts';
import type { VisibilityFilter } from './visibility.ts';

/** Posição (unidades de a) do átomo selecionado, na liga ou na célula do metal puro. */
export function selectedPosition(
  alloy: AlloyResult | null,
  alloySelection: string | null,
  structure: StructureResult | null,
  selection: AtomRef | null,
  supercell: [number, number, number],
): Vec3 | null {
  if (alloy && alloySelection) {
    const atom = alloy.atomos.find((a, i) => alloyAtomId(a, i) === alloySelection);
    return atom ? atom.pos : null;
  }
  if (!alloy && structure && selection) {
    const key = atomKey(selection);
    const atom = buildAtoms(structure, supercell).find((a) => a.key === key);
    return atom ? atom.pos : null;
  }
  return null;
}

export function toVisibilityFilter(f: Pick<SceneFilterState, 'hiddenElements' | 'hiddenOccupations' | 'hiddenSites' | 'cut' | 'neighbourhoodRadius'>, center: Vec3 | null): VisibilityFilter {
  return {
    hiddenElements: f.hiddenElements,
    hiddenOccupations: f.hiddenOccupations,
    hiddenSites: f.hiddenSites,
    cut: f.cut,
    neighbourhood: f.neighbourhoodRadius !== null && center ? { center, radius: f.neighbourhoodRadius } : null,
  };
}

/** Filtro de exibição em vigor agora (lê os stores). */
export function currentFilter(): VisibilityFilter {
  const f = useSceneFilter.getState();
  const v = useViewer.getState();
  const alloy = useAlloy.getState().alloy;
  const center = f.neighbourhoodRadius === null ? null : selectedPosition(alloy, v.alloySelection, useCrystalab.getState().structure, v.selection, v.supercell);
  return toVisibilityFilter(f, center);
}
