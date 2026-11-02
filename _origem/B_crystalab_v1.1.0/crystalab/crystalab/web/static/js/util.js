// Utilitários sem estado: formatação pt-BR e construção segura de DOM (achado SE-02).
// Regra do projeto: dados vindos da API NUNCA passam por innerHTML — use h().

export function ptNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/d";
  if (!Number.isFinite(Number(value))) return "∞";
  return Number(value).toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function compactNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  if (Math.abs(number - Math.round(number)) < 0.0001) return String(Math.round(number));
  return number.toFixed(2).replace(".", ",");
}

export function plainText(text) {
  return String(text).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
}

/**
 * Cria um elemento: h("span", { class: "chip", style: { background: cor } }, "texto", filho).
 * Texto é sempre inserido como nó de texto (escapado); estilos via CSSOM (compatível com CSP).
 */
export function h(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key === "style") Object.assign(node.style, value);
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : String(child));
  }
  return node;
}

export const $ = (id) => document.getElementById(id);
