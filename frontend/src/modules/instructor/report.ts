/**
 * Relatório do professor (6.18): PDF (impressão do navegador) e Word (.docx, biblioteca
 * `docx` carregada sob demanda). Só exporta quando há dados válidos; dados demonstrativos
 * saem com aviso explícito em cada página/seção.
 */
import { downloadBlob } from '../../features/export/download.ts';

export interface ReportRow { label: string; values: Array<string | number> }
export interface ReportData {
  title: string;
  subtitle: string;
  demo: boolean;
  demoNotice: string;
  generatedAt: string;
  sections: Array<{ heading: string; columns: string[]; rows: ReportRow[]; note?: string }>;
}

export function reportHasData(r: ReportData): boolean {
  return r.sections.some((s) => s.rows.length > 0);
}

export async function exportDocx(r: ReportData, filename: string): Promise<void> {
  if (!reportHasData(r)) throw new Error('empty');
  const d = await import('docx');
  const cell = (text: string, bold = false) => new d.TableCell({ children: [new d.Paragraph({ children: [new d.TextRun({ text, bold })] })] });
  const children: Array<InstanceType<typeof d.Paragraph> | InstanceType<typeof d.Table>> = [
    new d.Paragraph({ heading: d.HeadingLevel.TITLE, children: [new d.TextRun(r.title)] }),
    new d.Paragraph({ children: [new d.TextRun({ text: r.subtitle, italics: true })] }),
    new d.Paragraph({ children: [new d.TextRun({ text: r.generatedAt, size: 18 })] }),
  ];
  if (r.demo) children.push(new d.Paragraph({ children: [new d.TextRun({ text: r.demoNotice, bold: true, color: '9A3412' })] }));
  for (const s of r.sections) {
    children.push(new d.Paragraph({ heading: d.HeadingLevel.HEADING_2, children: [new d.TextRun(s.heading)] }));
    if (s.rows.length) {
      children.push(new d.Table({
        width: { size: 100, type: d.WidthType.PERCENTAGE },
        rows: [
          new d.TableRow({ tableHeader: true, children: s.columns.map((c) => cell(c, true)) }),
          ...s.rows.map((row) => new d.TableRow({ children: [cell(row.label, true), ...row.values.map((v) => cell(String(v)))] })),
        ],
      }));
    }
    if (s.note) children.push(new d.Paragraph({ children: [new d.TextRun({ text: s.note, italics: true, size: 18 })] }));
  }
  const doc = new d.Document({ creator: 'Alloy Virtual Lab', title: r.title, sections: [{ children }] });
  const blob = await d.Packer.toBlob(doc);
  downloadBlob(blob, filename);
}

export function exportPdf(): void {
  const root = document.documentElement;
  root.classList.add('print-report');
  window.print();
  root.classList.remove('print-report');
}
