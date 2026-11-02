// Ações de alto nível. Terminal, botões e blocos chamam APENAS estas funções.
import { ENDPOINTS, postJson } from "./api.js";
import { OVERLAY_COLORS, STORAGE_KEYS, state } from "./estado.js";
import { logLine } from "./log.js";
import {
  markActiveBlock, overlayDetail, parseEditor, renderDensity, renderLower, renderOverlayList,
  renderSummary, resultToEditor,
} from "./paineis.js";
import { $, ptNumber } from "./util.js";
import { viewer } from "./viewer.js";

export async function loadStructure(payload) {
  const result = await postJson(ENDPOINTS.estrutura, payload);
  if (result) applyResult(result);
  return result;
}

export function applyEditor() {
  const payload = parseEditor();
  if (!payload.nome && !payload.estrutura) {
    logLine("Informe 'elemento = Fe' ou 'estrutura = CFC' no editor.", "terminal-error");
    return;
  }
  loadStructure(payload);
}

export function applyResult(result) {
  state.current = result;
  state.selectedKey = result.simbolo && !result.editado ? result.simbolo
    : (result.generica && !result.raio_nm ? `gen:${result.estrutura}` : "");
  $("currentName").textContent = result.simbolo ? `${result.simbolo} · ${result.estrutura}` : `genérica · ${result.estrutura}`;
  resultToEditor(result);
  markActiveBlock();
  renderSummary(result);
  renderLower(result);
  if (state.densityVisible) renderDensity(result);
  state.overlays = [];
  renderOverlayList();
  viewer.build(result);
  const density = result.densidade ? ` · ρ = ${ptNumber(result.densidade, 3)} g/cm³` : "";
  logLine(`${result.rotulo}: ${result.estrutura} · NC ${result.nc} · FEA ${ptNumber(result.fea, 3)}${density}`, "terminal-ok");
  (result.avisos || []).forEach((aviso) => logLine(`aviso: ${aviso}`, "terminal-step"));
}

export function showDensity() {
  const result = state.current;
  if (!result) return;
  state.densityVisible = true;
  renderDensity(result);
  $("densityPanel").scrollIntoView({ behavior: "smooth", block: "start" });
  if (!result.densidade) { logLine(result.passos_densidade[0].detalhe, "terminal-error"); return; }
  logLine(`densidade teórica — ${result.rotulo}`, "terminal-ok");
  result.passos_densidade.forEach((step, index) => logLine(`${index + 1}. ${step.titulo}\n   ${step.formula.replace(/\n/g, "\n   ")}`, "terminal-step"));
}

export function hideDensity() {
  state.densityVisible = false;
  $("densityPanel").hidden = true;
}

export function parseIndices(text) {
  const clean = String(text).replace(/[()[\]{}<>]/g, " ").trim();
  if (!clean) return null;
  const tokens = /[\s,;]/.test(clean) ? clean.split(/[\s,;]+/).filter(Boolean) : (clean.match(/-?\d/g) || []);
  const numbers = tokens.map(Number);
  if (!numbers.length || numbers.some((n) => !Number.isInteger(n))) return null;
  return numbers;
}

export async function drawMiller(type, indices) {
  const result = state.current;
  if (!result) return;
  if (!indices || indices.length < 3) {
    logLine("Informe 3 índices inteiros (ou 4 na HC). Ex.: plano 1 1 1", "terminal-error");
    return;
  }
  const overlay = await postJson(ENDPOINTS.miller, { estrutura: result.estrutura, c_a: result.c_a, a_nm: result.a_nm, tipo: type, indices });
  if (!overlay) return;
  if (state.current !== result) {
    // FE-07: antes o resultado era descartado em silêncio.
    logLine("resultado descartado: a estrutura mudou durante o cálculo. Desenhe novamente.", "terminal-step");
    return;
  }
  overlay.color = OVERLAY_COLORS[state.overlays.length % OVERLAY_COLORS.length];
  state.overlays.push(overlay);
  viewer.addOverlay(overlay);
  renderOverlayList();
  const name = overlay.tipo === "plano" ? "plano" : "direção";
  const extra = overlay.notacao_alternativa ? ` = ${overlay.notacao_alternativa}` : "";
  logLine(`${name} ${overlay.notacao}${extra}: ${overlayDetail(overlay)}`, "terminal-ok");
  if (overlay.tipo === "direcao" && overlay.densidade_linear_rel === null) {
    logLine("o vetor não termina em um ponto da rede dentro da célula; densidade linear não calculada.", "terminal-step");
  }
  (overlay.avisos || []).forEach((aviso) => logLine(`aviso: ${aviso}`, "terminal-step"));
}

export function clearOverlays() {
  state.overlays = [];
  viewer.clearOverlays();
  renderOverlayList();
}

export function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".segmented button").forEach((button) => {
    const on = button.dataset.mode === mode;
    button.classList.toggle("is-on", on);
    button.setAttribute("aria-pressed", String(on));
  });
}

export function setToggle(name, value) {
  if (name === "rigid") { state.rigid = value; viewer.updateAtomScale(); }
  if (name === "rotate") { state.autoRotate = value; viewer.requestRender(); }
  if (name === "axes") { state.showAxes = value; viewer.setAxesVisible(value); }
  const button = document.querySelector(`[data-toggle="${name}"]`);
  if (button) {
    button.classList.toggle("is-on", value);
    button.setAttribute("aria-pressed", String(value));
  }
}

export function toggleValue(name) {
  return { rigid: state.rigid, rotate: state.autoRotate, axes: state.showAxes }[name];
}

export function setTheme(theme, persist = true) {
  state.theme = theme;
  document.documentElement.dataset.theme = theme;
  $("themeToggle").textContent = theme === "dark" ? "☀ claro" : "☾ escuro";
  if (persist) { try { localStorage.setItem(STORAGE_KEYS.theme, theme); } catch (error) { /* armazenamento indisponível */ } }
  viewer.applyTheme();
}

export function initTheme() {
  let stored = null;
  try { stored = localStorage.getItem(STORAGE_KEYS.theme); } catch (error) { /* armazenamento indisponível */ }
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  setTheme(stored || (prefersDark ? "dark" : "light"), false);
}
