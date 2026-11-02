/**
 * Exportação (tarefa 4.15), ligada aos mecanismos existentes:
 *  - CIF/XYZ → /v1/export/* do motor (só existe na versão FastAPI; senão desativado, D-05);
 *  - PNG → captura do canvas do viewer;
 *  - PDF → impressão do navegador com folha de estilo de relatório (D-06);
 *  - JSON → configuração da cena (mesmo esquema da URL), reimportável.
 */
import { tr } from '../../commands/bus.ts';
import { crystalabApi } from '../../services/api/crystalab.ts';
import { serviceMode } from '../../stores/capabilities.ts';
import { useCrystalab } from '../../stores/crystalab.ts';
import { getViewer } from '../registry.ts';
import { captureSceneState } from '../url/sceneUrl.ts';
import { downloadBlob, downloadDataUrl, downloadText, slug } from './download.ts';
import type { ExportFormat } from '../../commands/types.ts';

export interface ExportAvailability {
  format: ExportFormat;
  enabled: boolean;
  reasonKey?: 'export.reason.noStructure' | 'export.reason.engineV1' | 'export.reason.noViewer' | 'export.reason.noRadius';
}

export function exportAvailability(): ExportAvailability[] {
  const { structure } = useCrystalab.getState();
  const v1 = serviceMode('exportCif') === 'live';
  const viewer = Boolean(getViewer());
  const noStructure = { enabled: false, reasonKey: 'export.reason.noStructure' as const };
  if (!structure) return (['cif', 'xyz', 'png', 'pdf', 'json'] as ExportFormat[]).map((format) => ({ format, ...noStructure }));
  return [
    { format: 'cif', ...(v1 ? (structure.a_nm === null ? { enabled: false, reasonKey: 'export.reason.noRadius' as const } : { enabled: true }) : { enabled: false, reasonKey: 'export.reason.engineV1' as const }) },
    { format: 'xyz', ...(v1 ? { enabled: true } : { enabled: false, reasonKey: 'export.reason.engineV1' as const }) },
    { format: 'png', ...(viewer ? { enabled: true } : { enabled: false, reasonKey: 'export.reason.noViewer' as const }) },
    { format: 'pdf', enabled: true },
    { format: 'json', enabled: true },
  ];
}

export async function runExport(format: ExportFormat, signal: AbortSignal): Promise<string> {
  const avail = exportAvailability().find((a) => a.format === format);
  if (!avail?.enabled) throw new Error(`${tr('export.disabled', { format: format.toUpperCase() })} ${avail?.reasonKey ? tr(avail.reasonKey) : ''}`.trim());
  const { structure, request } = useCrystalab.getState();
  if (!structure || !request) throw new Error(tr('cmd.err.noStructure'));
  const base = `crystalab-${slug(structure.rotulo)}`;
  if (format === 'cif' || format === 'xyz') {
    const file = await crystalabApi.exportFile(format, request, signal);
    downloadBlob(new Blob([file.content], { type: file.content_type }), file.filename);
    return tr('export.done', { file: file.filename });
  }
  if (format === 'png') {
    const data = getViewer()?.capturePng();
    if (!data) throw new Error(tr('export.reason.noViewer'));
    downloadDataUrl(data, `${base}.png`);
    return tr('export.done', { file: `${base}.png` });
  }
  if (format === 'json') {
    const scene = captureSceneState(true);
    downloadText(JSON.stringify({ format: 'alloy-scene', version: 1, exportedAt: new Date().toISOString(), scene }, null, 2), `${base}.json`, 'application/json');
    return tr('export.done', { file: `${base}.json` });
  }
  document.documentElement.classList.add('print-report');
  window.setTimeout(() => {
    window.print();
    document.documentElement.classList.remove('print-report');
  }, 60);
  return tr('export.pdfPrint');
}
