/**
 * “Anotar cena” (6.13): cria uma nota com miniatura da cena (JPEG reduzido, para caber no
 * armazenamento local), valores copiados da resposta do motor, medições e link da cena.
 */
import { getViewer } from '../../features/registry.ts';
import { buildShareUrl } from '../../features/url/sceneUrl.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { useOverlays } from '../../stores/overlays.ts';
import { formatNumber, type Locale } from '../../utils/format.ts';
import { addNote, type Note } from './store.ts';

export async function thumbnail(dataUrl: string, maxWidth = 480): Promise<string> {
  const img = new Image();
  img.src = dataUrl;
  await img.decode();
  const scale = Math.min(1, maxWidth / img.width);
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(img.width * scale);
  canvas.height = Math.round(img.height * scale);
  const ctx = canvas.getContext('2d');
  if (!ctx) return dataUrl;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/jpeg', 0.82);
}

export async function captureSceneNote(title: string, locale: Locale): Promise<Note | null> {
  const r = useCrystalab.getState().structure;
  const request = useCrystalab.getState().request;
  if (!r) return null;
  const png = getViewer()?.capturePng() ?? null;
  const image = png ? await thumbnail(png) : undefined;
  const share = buildShareUrl();
  const measurements = useOverlays.getState().items.flatMap((o) => (o.kind === 'measurement'
    ? [{ label: o.label, value: o.data.type === 'distance' ? (o.data.valueNm != null ? `${formatNumber(o.data.valueNm, 4, locale)} nm` : `${formatNumber(o.data.valueA ?? 0, 4, locale)} a`) : `${formatNumber(o.data.degrees ?? 0, 2, locale)}°` }]
    : (o.kind === 'plane' || o.kind === 'direction') ? [{ label: o.kind === 'plane' ? 'plano' : 'direção', value: o.label }] : []));
  return addNote({
    kind: 'observation',
    title,
    body: '',
    structure: { rotulo: r.rotulo, estrutura: r.estrutura, request: { ...(request ?? {}) } },
    params: { R_nm: r.raio_nm, A_g_mol: r.peso, n: r.n, a_nm: r.a_nm, FEA: r.fea, densidade_motor: r.densidade },
    ...(measurements.length ? { measurements } : {}),
    ...(share.truncated ? {} : { sceneUrl: share.url }),
    ...(image ? { image } : {}),
  });
}
