/**
 * Estado da cena na URL (tarefa 4.13 / 2.14). Esquema VERSIONADO e VALIDADO na leitura:
 *   #/crystalab?s=v1.<base64url(JSON)>
 * Contém apenas parâmetros de cena (material, índices de Miller, câmera, exibição) —
 * nenhum dado pessoal, nenhum resultado numérico (os números são sempre recalculados
 * pelo motor ao abrir o link). Limite de tamanho: 1800 caracteres no parâmetro.
 */
import { z } from 'zod';
import { decodeBase64Url, encodeBase64Url } from '../../utils/base64url.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useOverlays, OVERLAY_PALETTE, type OverlayItem } from '../../stores/overlays.ts';
import { useViewer } from '../../stores/viewer.ts';
import type { StructureRequest } from '../../services/api/contracts.ts';

export const SCENE_URL_MAX = 1800;

const vec = z.tuple([z.number().finite().min(-100).max(100), z.number().finite().min(-100).max(100), z.number().finite().min(-100).max(100)]);
const materialName = z.string().max(40).regex(/^[\p{L}\p{N} ()\-]+$/u);

export const SceneV1 = z.object({
  v: z.literal(1),
  m: z.object({
    nome: materialName.optional(),
    estrutura: z.enum(['CS', 'CCC', 'CFC', 'HC']).optional(),
    raio: z.number().min(0.02).max(0.5).optional(),
    peso: z.number().min(1).max(300).optional(),
    c_a: z.number().min(1).max(2.5).optional(),
  }).strict(),
  o: z.array(z.object({
    t: z.enum(['p', 'd']),
    i: z.array(z.number().int().min(-9).max(9)).min(3).max(4),
    c: z.string().regex(/^#[0-9A-Fa-f]{6}$/).optional(),
    h: z.literal(1).optional(),
    k: z.literal(1).optional(),
  }).strict()).max(12).optional(),
  c: z.object({ p: vec, t: vec }).strict().optional(),
  d: z.object({
    a: z.enum(['reduced', 'rigid', 'ballstick', 'points']).optional(),
    e: z.boolean().optional(),
    x: z.boolean().optional(),
    l: z.boolean().optional(),
    r: z.boolean().optional(),
  }).strict().optional(),
  s: z.tuple([z.number().int().min(1).max(4), z.number().int().min(1).max(4), z.number().int().min(1).max(4)]).optional(),
  dn: z.literal(1).optional(),
}).strict();
export type SceneV1 = z.infer<typeof SceneV1>;

const round = (v: number) => Math.round(v * 1000) / 1000;

export function captureSceneState(includeCamera = true): SceneV1 | null {
  const c = useCrystalab.getState();
  if (!c.request) return null;
  const v = useViewer.getState();
  const items = useOverlays.getState().items;
  const req = Object.fromEntries(Object.entries(c.request).filter(([, x]) => x !== undefined)) as StructureRequest;
  const scene: SceneV1 = { v: 1, m: req };
  const o = items.flatMap((it) => {
    if (it.kind !== 'plane' && it.kind !== 'direction') return [];
    const entry: NonNullable<SceneV1['o']>[number] = { t: it.kind === 'plane' ? 'p' : 'd', i: it.data.indices, c: it.color };
    if (!it.visible) entry.h = 1;
    if (it.kind === 'plane' && it.clip) entry.k = 1;
    return [entry];
  });
  if (o.length) scene.o = o.slice(0, 12);
  if (includeCamera && v.camera) scene.c = { p: v.camera.position.map(round) as [number, number, number], t: v.camera.target.map(round) as [number, number, number] };
  scene.d = { a: v.display.atoms, e: v.display.edges, x: v.display.axes, l: v.display.latticePoints, r: v.display.labels };
  if (v.supercell.some((x) => x !== 1)) scene.s = v.supercell;
  if (c.densityVisible) scene.dn = 1;
  return scene;
}

export function encodeScene(scene: SceneV1): string {
  return `v1.${encodeBase64Url(JSON.stringify(scene))}`;
}

export type DecodeResult = { ok: true; scene: SceneV1 } | { ok: false; reason: 'version' | 'format' | 'schema' | 'size'; detail?: string };

export function decodeScene(param: string): DecodeResult {
  if (param.length > SCENE_URL_MAX) return { ok: false, reason: 'size' };
  const dot = param.indexOf('.');
  const version = dot > 0 ? param.slice(0, dot) : '';
  if (version !== 'v1') return { ok: false, reason: 'version', detail: version || '(sem versão)' };
  let json: unknown;
  try {
    json = JSON.parse(decodeBase64Url(param.slice(dot + 1)));
  } catch {
    return { ok: false, reason: 'format' };
  }
  const parsed = SceneV1.safeParse(json);
  if (!parsed.success) return { ok: false, reason: 'schema', detail: parsed.error.issues[0]?.path.join('.') };
  return { ok: true, scene: parsed.data };
}

export function buildShareUrl(): { url: string; length: number; truncated: boolean } {
  let scene = captureSceneState(true);
  if (!scene) throw new Error('nenhuma cena carregada');
  let param = encodeScene(scene);
  let truncated = false;
  if (param.length > SCENE_URL_MAX) {
    scene = captureSceneState(false) as SceneV1;
    param = encodeScene(scene);
    truncated = true;
  }
  while (param.length > SCENE_URL_MAX && scene.o && scene.o.length) {
    scene = { ...scene, o: scene.o.slice(0, -1) };
    param = encodeScene(scene);
    truncated = true;
  }
  const base = `${window.location.origin}${window.location.pathname}`;
  const url = `${base}#/crystalab?s=${param}`;
  return { url, length: param.length, truncated };
}

/** Cor de overlay validada contra a paleta acessível (link adulterado não injeta cores arbitrárias). */
export function safeColor(c: string | undefined, fallback: string): string {
  if (!c) return fallback;
  return (OVERLAY_PALETTE as readonly string[]).includes(c) ? c : fallback;
}

export type RestoredOverlay = Pick<OverlayItem, 'color' | 'visible'> & { kind: 'plane' | 'direction'; indices: number[]; clip: boolean };
