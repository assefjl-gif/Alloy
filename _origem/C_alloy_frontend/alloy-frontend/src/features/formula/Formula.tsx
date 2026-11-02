import { useEffect, useState } from 'react';

/**
 * Fórmula em KaTeX carregada sob demanda (tarefa 2.16 / 4.12). Enquanto o KaTeX não chega,
 * mostra o texto LaTeX simplificado. A saída inclui MathML para leitores de tela.
 * Este é o ÚNICO componente autorizado a usar dangerouslySetInnerHTML (conteúdo gerado
 * pelo KaTeX a partir de fórmulas estáticas do código, nunca de dados do usuário).
 */
type KatexApi = { renderToString: (tex: string, opts: Record<string, unknown>) => string };
let katexPromise: Promise<KatexApi> | null = null;

function loadKatex(): Promise<KatexApi> {
  if (!katexPromise) {
    if (!document.querySelector('link[data-katex]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = './vendor/katex/katex.min.css';
      link.dataset.katex = '1';
      document.head.appendChild(link);
    }
    katexPromise = import('katex').then((m) => (m as unknown as { default: KatexApi }).default ?? (m as unknown as KatexApi));
  }
  return katexPromise;
}

export function Formula({ tex, display = false, label }: { tex: string; display?: boolean; label?: string }) {
  const [html, setHtml] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    loadKatex()
      .then((k) => { if (alive) setHtml(k.renderToString(tex, { displayMode: display, throwOnError: false, output: 'htmlAndMathml', strict: 'ignore' })); })
      .catch(() => { if (alive) setHtml(null); });
    return () => { alive = false; };
  }, [tex, display]);
  if (!html) return <code className="formula-fallback" aria-label={label}>{tex}</code>;
  return <span className={`formula ${display ? 'formula--display' : ''}`} role={label ? 'math' : undefined} aria-label={label} dangerouslySetInnerHTML={{ __html: html }} />;
}
