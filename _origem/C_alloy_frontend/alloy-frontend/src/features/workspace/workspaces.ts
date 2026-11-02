/**
 * Workspaces (tarefa 4.14). Não há serviço de workspaces no servidor (pendência D-04):
 * salvamos neste navegador, rotulado como local, com exportação/importação em JSON.
 */
import { z } from 'zod';
import { readJSON, writeJSON } from '../../utils/storage.ts';
import { uid } from '../../utils/id.ts';
import { captureSceneState, SceneV1 } from '../url/sceneUrl.ts';
import { useCrystalab } from '../../stores/crystalab.ts';

const KEY = 'alloy.workspaces';

export const Workspace = z.object({ id: z.string(), name: z.string().max(80), savedAt: z.string(), storage: z.literal('local'), scene: SceneV1 });
export type Workspace = z.infer<typeof Workspace>;
const WorkspaceFile = z.object({ format: z.literal('alloy-workspaces'), version: z.literal(1), workspaces: z.array(Workspace).max(200) });

export function listWorkspaces(): Workspace[] {
  const raw = readJSON<unknown>(KEY, []);
  const parsed = z.array(Workspace).safeParse(raw);
  return parsed.success ? parsed.data : [];
}

export function saveWorkspace(name?: string): Workspace {
  const scene = captureSceneState(true);
  if (!scene) throw new Error('nenhuma cena para salvar');
  const label = useCrystalab.getState().structure?.rotulo ?? 'cena';
  const ws: Workspace = { id: uid('ws'), name: (name ?? `${label} — ${new Date().toLocaleString()}`).slice(0, 80), savedAt: new Date().toISOString(), storage: 'local', scene };
  const all = [ws, ...listWorkspaces()].slice(0, 200);
  if (!writeJSON(KEY, all)) throw new Error('armazenamento local indisponível neste navegador');
  window.dispatchEvent(new Event('alloy:workspaces'));
  return ws;
}

export function deleteWorkspace(id: string): void {
  writeJSON(KEY, listWorkspaces().filter((w) => w.id !== id));
}

export function exportWorkspacesJson(): string {
  return JSON.stringify({ format: 'alloy-workspaces', version: 1, workspaces: listWorkspaces() }, null, 2);
}

export function importWorkspacesJson(text: string): { added: number } {
  let data: unknown;
  try { data = JSON.parse(text); } catch { throw new Error('arquivo não é JSON'); }
  const parsed = WorkspaceFile.safeParse(data);
  if (!parsed.success) throw new Error(`arquivo fora do formato alloy-workspaces v1 (${parsed.error.issues[0]?.path.join('.') ?? 'raiz'})`);
  const existing = listWorkspaces();
  const ids = new Set(existing.map((w) => w.id));
  const fresh = parsed.data.workspaces.filter((w) => !ids.has(w.id));
  writeJSON(KEY, [...fresh, ...existing].slice(0, 200));
  return { added: fresh.length };
}
