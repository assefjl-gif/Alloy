/**
 * Auditoria automatizada de acessibilidade — implementação própria do projeto.
 *
 * IMPORTANTE: isto NÃO é o axe-core nem o Lighthouse. Os dois não puderam ser
 * instalados (registro npm bloqueado). Esta auditoria cobre um subconjunto
 * explícito de critérios WCAG 2.2 usando a árvore de acessibilidade calculada
 * pelo próprio Chromium (CDP Accessibility.getFullAXTree) e estilos computados.
 * Ela não produz "nota Lighthouse"; produz uma lista de violações por regra.
 *
 * Regras cobertas (id → critério WCAG):
 *   name-required       4.1.2  controles interativos com nome acessível
 *   image-alt           1.1.1  imagens/ícones com papel img têm nome
 *   contrast            1.4.3  contraste de texto (4,5:1; 3:1 para texto grande)
 *   doc-lang / doc-title 3.1.1 / 2.4.2
 *   landmark-main       1.3.1  existe exatamente uma região main
 *   heading-order       1.3.1  níveis de cabeçalho não saltam (h2 → h4)
 *   duplicate-id        4.1.1  ids duplicados referenciados por ARIA
 *   tabindex-positive   2.4.3  tabindex > 0
 *   target-size         2.5.8  alvo de toque ≥ 24×24 CSS px (AA, WCAG 2.2)
 *   focus-visible       2.4.7  foco visível nos primeiros N elementos tabuláveis
 *   aria-pressed-role   4.1.2  aria-pressed só em botões
 */
import type { Page } from 'playwright';

export interface A11yViolation {
  rule: string;
  wcag: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  target: string;
  detail: string;
}

export interface A11yReport {
  url: string;
  checkedAt: string;
  rules: string[];
  violations: A11yViolation[];
  needsReview: A11yViolation[];
  counts: Record<string, number>;
  stats: { interactive: number; textNodesChecked: number; focusChecked: number };
}

const INTERACTIVE_ROLES = new Set([
  'button', 'link', 'textbox', 'checkbox', 'radio', 'combobox', 'listbox', 'menuitem', 'tab',
  'switch', 'slider', 'spinbutton', 'searchbox', 'option', 'menuitemcheckbox', 'menuitemradio', 'treeitem',
]);

interface AXNode {
  nodeId: string;
  ignored: boolean;
  role?: { value?: string };
  name?: { value?: string };
  backendDOMNodeId?: number;
  properties?: Array<{ name: string; value: { value?: unknown } }>;
}

export async function runA11yAudit(page: Page, options: { focusSamples?: number; scope?: string } = {}): Promise<A11yReport> {
  // tsx/esbuild (keepNames) injeta __name nas funções serializadas para o navegador.
  await page.evaluate('globalThis.__name = globalThis.__name || ((f) => f)');
  const violations: A11yViolation[] = [];
  const needsReview: A11yViolation[] = [];
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Accessibility.enable');
  await cdp.send('DOM.enable');
  const { nodes } = (await cdp.send('Accessibility.getFullAXTree')) as { nodes: AXNode[] };

  let interactive = 0;
  for (const node of nodes) {
    if (node.ignored) continue;
    const role = node.role?.value ?? '';
    const name = String(node.name?.value ?? '').trim();
    const hidden = node.properties?.some((p) => p.name === 'hidden' && p.value.value === true);
    if (hidden) continue;
    if (INTERACTIVE_ROLES.has(role)) {
      interactive += 1;
      if (!name) {
        const target = await describeBackendNode(cdp, node.backendDOMNodeId);
        violations.push({ rule: 'name-required', wcag: '4.1.2', impact: 'serious', target, detail: `papel "${role}" sem nome acessível` });
      }
    }
    if ((role === 'img' || role === 'image') && !name) {
      const target = await describeBackendNode(cdp, node.backendDOMNodeId);
      violations.push({ rule: 'image-alt', wcag: '1.1.1', impact: 'serious', target, detail: 'imagem sem texto alternativo' });
    }
  }

  const dom = await page.evaluate((scope) => {
    const root: ParentNode = scope ? (document.querySelector(scope) ?? document) : document;
    const out = {
      lang: document.documentElement.getAttribute('lang') ?? '',
      title: document.title,
      mains: document.querySelectorAll('main, [role="main"]').length,
      headings: [] as Array<{ level: number; text: string }>,
      dupIds: [] as string[],
      tabPositive: [] as string[],
      smallTargets: [] as Array<{ target: string; w: number; h: number }>,
      ariaPressedMisuse: [] as string[],
      contrast: [] as Array<{ target: string; ratio: number; required: number; fg: string; bg: string; review: boolean; text: string }>,
      textChecked: 0,
    };
    const describe = (el: Element): string => {
      const id = el.id ? `#${el.id}` : '';
      const testid = el.getAttribute('data-testid');
      const cls = (el.getAttribute('class') ?? '').split(/\s+/).filter(Boolean).slice(0, 2).map((c) => `.${c}`).join('');
      return `${el.tagName.toLowerCase()}${id}${testid ? `[data-testid=${testid}]` : ''}${cls}`;
    };
    root.querySelectorAll('h1,h2,h3,h4,h5,h6,[role="heading"]').forEach((h) => {
      const level = h.getAttribute('aria-level') ? Number(h.getAttribute('aria-level')) : Number(h.tagName.slice(1));
      const st = getComputedStyle(h);
      if (st.display !== 'none' && st.visibility !== 'hidden') out.headings.push({ level, text: (h.textContent ?? '').trim().slice(0, 60) });
    });
    const ids = new Map<string, number>();
    document.querySelectorAll('[id]').forEach((el) => ids.set(el.id, (ids.get(el.id) ?? 0) + 1));
    ids.forEach((count, id) => { if (count > 1) out.dupIds.push(id); });
    root.querySelectorAll('[tabindex]').forEach((el) => { if (Number(el.getAttribute('tabindex')) > 0) out.tabPositive.push(describe(el)); });
    root.querySelectorAll('[aria-pressed]').forEach((el) => {
      const role = el.getAttribute('role');
      if (el.tagName !== 'BUTTON' && role !== 'button') out.ariaPressedMisuse.push(describe(el));
    });
    const interactiveSel = 'button, a[href], input:not([type=hidden]), select, textarea, [role=button], [role=tab], [role=checkbox], [role=switch], [role=menuitem], [role=option]';
    root.querySelectorAll(interactiveSel).forEach((el) => {
      const r = (el as HTMLElement).getBoundingClientRect();
      const st = getComputedStyle(el);
      if (r.width === 0 || r.height === 0 || st.visibility === 'hidden' || st.display === 'none') return;
      // Exceção WCAG 2.5.8: alvos em linha dentro de texto (links em parágrafos) estão isentos.
      const inline = st.display === 'inline' && el.tagName === 'A';
      if (!inline && (r.width < 24 || r.height < 24)) out.smallTargets.push({ target: describe(el), w: Math.round(r.width), h: Math.round(r.height) });
    });

    const parse = (c: string): [number, number, number, number] | null => {
      const m = c.match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const parts = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
      return [parts[0], parts[1], parts[2], parts.length > 3 ? parts[3] : 1];
    };
    const lum = (rgb: [number, number, number]) => {
      const f = (v: number) => { const s = v / 255; return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4); };
      return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2]);
    };
    const blend = (top: [number, number, number, number], bottom: [number, number, number]): [number, number, number] => {
      const a = top[3];
      return [top[0] * a + bottom[0] * (1 - a), top[1] * a + bottom[1] * (1 - a), top[2] * a + bottom[2] * (1 - a)];
    };
    const effectiveBg = (el: Element): { rgb: [number, number, number]; review: boolean } => {
      const layers: Array<[number, number, number, number]> = [];
      let review = false;
      let cur: Element | null = el;
      while (cur) {
        const st = getComputedStyle(cur);
        if (st.backgroundImage && st.backgroundImage !== 'none') review = true;
        const c = parse(st.backgroundColor);
        if (c && c[3] > 0) { layers.push(c); if (c[3] >= 1) break; }
        cur = cur.parentElement;
      }
      let base: [number, number, number] = [255, 255, 255];
      for (let i = layers.length - 1; i >= 0; i -= 1) base = blend(layers[i], base);
      return { rgb: base, review };
    };
    const walker = document.createTreeWalker(root as Node, NodeFilter.SHOW_TEXT);
    const seen = new Set<Element>();
    let n: Node | null;
    while ((n = walker.nextNode())) {
      const text = (n.textContent ?? '').trim();
      const el = n.parentElement;
      if (!text || !el || seen.has(el)) continue;
      seen.add(el);
      const st = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      if (st.visibility === 'hidden' || st.display === 'none' || rect.width === 0 || rect.height === 0 || Number(st.opacity) === 0) continue;
      if (el.closest('[aria-hidden="true"], .sr-only, .visually-hidden, .katex-mathml, canvas')) continue;
      const fg = parse(st.color);
      if (!fg) continue;
      out.textChecked += 1;
      const bg = effectiveBg(el);
      const fgRgb = blend(fg, bg.rgb);
      const l1 = lum(fgRgb), l2 = lum(bg.rgb);
      const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      const size = parseFloat(st.fontSize);
      const bold = Number(st.fontWeight) >= 700;
      const large = size >= 24 || (bold && size >= 18.66);
      const required = large ? 3 : 4.5;
      if (ratio + 0.01 < required) {
        out.contrast.push({ target: describe(el), ratio: Math.round(ratio * 100) / 100, required, fg: st.color, bg: `rgb(${bg.rgb.map(Math.round).join(',')})`, review: bg.review, text: text.slice(0, 40) });
      }
    }
    return out;
  }, options.scope ?? null);

  const url = page.url();
  if (!dom.lang) violations.push({ rule: 'doc-lang', wcag: '3.1.1', impact: 'serious', target: 'html', detail: 'atributo lang ausente' });
  if (!dom.title) violations.push({ rule: 'doc-title', wcag: '2.4.2', impact: 'moderate', target: 'title', detail: 'título ausente' });
  if (dom.mains !== 1) violations.push({ rule: 'landmark-main', wcag: '1.3.1', impact: 'moderate', target: 'main', detail: `${dom.mains} regiões main (esperado 1)` });
  let prev = 0;
  for (const h of dom.headings) {
    if (prev && h.level > prev + 1) violations.push({ rule: 'heading-order', wcag: '1.3.1', impact: 'moderate', target: `h${h.level}`, detail: `salto de h${prev} para h${h.level}: "${h.text}"` });
    prev = h.level;
  }
  if (!dom.headings.some((h) => h.level === 1)) violations.push({ rule: 'heading-order', wcag: '1.3.1', impact: 'moderate', target: 'h1', detail: 'nenhum h1 visível' });
  for (const id of dom.dupIds) violations.push({ rule: 'duplicate-id', wcag: '4.1.1', impact: 'minor', target: `#${id}`, detail: 'id duplicado' });
  for (const t of dom.tabPositive) violations.push({ rule: 'tabindex-positive', wcag: '2.4.3', impact: 'serious', target: t, detail: 'tabindex > 0 altera a ordem de foco' });
  for (const t of dom.ariaPressedMisuse) violations.push({ rule: 'aria-pressed-role', wcag: '4.1.2', impact: 'moderate', target: t, detail: 'aria-pressed em elemento que não é botão' });
  for (const s of dom.smallTargets) violations.push({ rule: 'target-size', wcag: '2.5.8', impact: 'moderate', target: s.target, detail: `alvo de ${s.w}×${s.h} px (< 24×24)` });
  for (const c of dom.contrast) {
    const v: A11yViolation = { rule: 'contrast', wcag: '1.4.3', impact: 'serious', target: c.target, detail: `contraste ${c.ratio}:1 < ${c.required}:1 ("${c.text}", ${c.fg} sobre ${c.bg})` };
    (c.review ? needsReview : violations).push(v);
  }

  // Foco visível: percorre os primeiros N elementos com Tab e compara o estilo com/sem foco.
  const samples = options.focusSamples ?? 25;
  let focusChecked = 0;
  await page.evaluate(() => { (document.activeElement as HTMLElement | null)?.blur(); window.scrollTo(0, 0); });
  for (let i = 0; i < samples; i += 1) {
    await page.keyboard.press('Tab');
    const info = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement | null;
      if (!el || el === document.body) return null;
      const st = getComputedStyle(el);
      const ring = (s: CSSStyleDeclaration) => (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || Boolean(s.boxShadow && s.boxShadow !== 'none');
      let visible = ring(st);
      // controle nativo visualmente oculto (ex.: rádio de um segmentado): o indicador fica no rótulo irmão/ancestral
      if (!visible && parseFloat(st.opacity) === 0) {
        const proxies = [el.nextElementSibling, el.closest('label')].filter(Boolean) as Element[];
        visible = proxies.some((p) => ring(getComputedStyle(p)));
      }
      const id = el.id ? `#${el.id}` : '';
      const testid = el.getAttribute('data-testid');
      return { visible: Boolean(visible), target: `${el.tagName.toLowerCase()}${id}${testid ? `[data-testid=${testid}]` : ''}` };
    });
    if (!info) break;
    focusChecked += 1;
    if (!info.visible) violations.push({ rule: 'focus-visible', wcag: '2.4.7', impact: 'serious', target: info.target, detail: 'sem indicador de foco (outline/box-shadow) ao receber foco por teclado' });
  }

  const counts: Record<string, number> = {};
  for (const v of violations) counts[v.rule] = (counts[v.rule] ?? 0) + 1;
  await cdp.detach();
  return {
    url,
    checkedAt: new Date().toISOString(),
    rules: ['name-required', 'image-alt', 'contrast', 'doc-lang', 'doc-title', 'landmark-main', 'heading-order', 'duplicate-id', 'tabindex-positive', 'target-size', 'focus-visible', 'aria-pressed-role'],
    violations,
    needsReview,
    counts,
    stats: { interactive, textNodesChecked: dom.textChecked, focusChecked },
  };
}

async function describeBackendNode(cdp: import('playwright').CDPSession, backendNodeId?: number): Promise<string> {
  if (!backendNodeId) return '(sem nó DOM)';
  try {
    const { node } = (await cdp.send('DOM.describeNode', { backendNodeId })) as { node: { localName: string; attributes?: string[] } };
    const attrs = node.attributes ?? [];
    const get = (k: string) => { const i = attrs.indexOf(k); return i >= 0 ? attrs[i + 1] : undefined; };
    const id = get('id');
    const testid = get('data-testid');
    const cls = get('class');
    return `${node.localName}${id ? `#${id}` : ''}${testid ? `[data-testid=${testid}]` : ''}${cls ? `.${cls.split(' ')[0]}` : ''}`;
  } catch {
    return `(backend ${backendNodeId})`;
  }
}
