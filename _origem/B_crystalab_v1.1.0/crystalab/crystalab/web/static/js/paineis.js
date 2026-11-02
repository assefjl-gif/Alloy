// Painéis da interface. Mesmo layout da v1.0, agora montado com h() em vez de innerHTML (SE-02).
import { state } from "./estado.js";
import { $, compactNumber, h, plainText, ptNumber } from "./util.js";

// ---------------------------------------------------------------- blocos
export function blockItems() {
  const { data } = state;
  const generic = data.estruturas.map((structure) => ({
    key: `gen:${structure.sigla}`,
    name: `Célula ${structure.sigla}`,
    tag: "genérica", tagKey: "gen",
    formula: `${structure.nome} · ${structure.relacao}`,
    chips: [structure.sigla, `NC ${structure.nc}`, `n = ${structure.n}`],
    payload: { nome: structure.sigla },
  }));
  const metals = Object.entries(data.metais).map(([symbol, metal]) => ({
    key: symbol,
    name: `${symbol} · ${metal.nome}`,
    tag: metal.estrutura, tagKey: metal.estrutura,
    formula: `R = ${ptNumber(metal.raio, 4)} nm · A = ${ptNumber(metal.peso, 2)} g/mol`,
    chips: [metal.estrutura, `NC ${metal.nc}`, `ρ ${ptNumber(metal.densidade_exp, 2)}`],
    payload: { nome: symbol },
  }));
  return [...metals, ...generic];
}

export function renderBlocks(onSelect) {
  const items = blockItems();
  $("blockCount").textContent = items.length;
  $("blockList").replaceChildren(...items.map((item) => {
    const block = h("article", {
      class: "alloy-block", draggable: "true", tabindex: "0", role: "button",
      "aria-label": `Carregar ${item.name}`, dataset: { key: item.key },
    },
      h("div", { class: "block-head" },
        h("div", { class: "block-name" }, item.name),
        h("div", { class: "block-tag", dataset: { s: item.tagKey } }, item.tag)),
      h("div", { class: "block-formula" }, item.formula),
      h("div", { class: "composition-strip" }, item.chips.map((chip) => h("span", { class: "element-chip" }, chip))));
    block.addEventListener("click", () => onSelect(item.payload));
    block.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(item.payload); }
    });
    block.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", item.key);
      event.dataTransfer.effectAllowed = "copy";
    });
    return block;
  }));
}

export function markActiveBlock() {
  document.querySelectorAll(".alloy-block").forEach((block) => {
    block.classList.toggle("is-active", block.dataset.key === state.selectedKey);
  });
}

// ---------------------------------------------------------------- editor de parâmetros
export function resultToEditor(result) {
  const lines = [
    `elemento = ${result.simbolo || "(genérico)"}`,
    `estrutura = ${result.estrutura}`,
    `raio = ${result.raio_nm ?? ""}`.padEnd(18) + "# nm",
    `peso = ${result.peso ?? ""}`.padEnd(18) + "# g/mol",
  ];
  if (result.estrutura === "HC") lines.push(`c/a = ${Number(result.c_a.toFixed(4))}`);
  $("parameterEditor").value = lines.join("\n");
}

const EDITOR_KEYS = { elemento: "nome", metal: "nome", nome: "nome", estrutura: "estrutura", raio: "raio", r: "raio", peso: "peso", massa: "peso", "c/a": "c_a", ca: "c_a" };

export function parseEditor() {
  const payload = {};
  $("parameterEditor").value.split("\n").forEach((rawLine) => {
    const line = rawLine.split("#")[0];
    const match = line.match(/^\s*([^=:]+?)\s*[=:]\s*(.*?)\s*$/);
    if (!match) return;
    const key = EDITOR_KEYS[plainText(match[1])];
    if (!key) return;
    const value = match[2];
    if (key === "nome" || key === "estrutura") { if (value && !value.startsWith("(")) payload[key] = value; }
    else if (value) { payload[key] = value.replace(",", "."); }
  });
  return payload;
}

// ---------------------------------------------------------------- resumo e métricas
function metric(label, value, unit) {
  return h("article", { class: "metric" },
    h("span", { class: "label" }, label),
    h("span", { class: "metric-value" }, String(value)),
    h("span", { class: "metric-unit" }, unit));
}

export function renderSummary(result) {
  $("resultTitle").textContent = result.rotulo;
  $("resultSubtitle").textContent = result.generica && !result.raio_nm
    ? "Célula genérica em unidades do raio atômico R · informe r e A para obter a densidade"
    : "Modelo de esferas rígidas · N_A = 6,022 × 10²³ átomos/mol";
  $("structureVerdict").textContent = `${result.estrutura_nome} (${result.estrutura})`;
  $("structureSub").textContent = `Os átomos se tocam ao longo da ${result.contato} · ${result.relacao_a}`;
  $("phaseMain").textContent = `NC = ${result.nc} · n = ${result.n} átomos/célula`;
  $("phaseSub").textContent = result.estrutura === "HC"
    ? `c/a = ${ptNumber(result.c_a, 3)} (ideal 1,633)`
    : `Vazios: ${ptNumber(result.vazios * 100, 1)}% do volume da célula`;
  const measured = result.a_fonte === "medido" ? " (medido)" : "";
  const lattice = result.a_nm
    ? metric("Parâmetro a", ptNumber(result.a_nm, 4), (result.c_nm ? `nm · c = ${ptNumber(result.c_nm, 4)} nm` : "nm") + measured)
    : metric("Parâmetro a", `${ptNumber(result.a_em_R, 3)} R`, result.relacao_a);
  const densityUnit = result.densidade_exp ? `g/cm³ · exp. ${ptNumber(result.densidade_exp, 2)}` : "g/cm³";
  $("metricsGrid").replaceChildren(
    metric("Estrutura", result.estrutura, result.estrutura_nome),
    lattice,
    metric("FEA", ptNumber(result.fea, 3), `${ptNumber(result.vazios * 100, 1)}% de vazios`),
    metric("Densidade", result.densidade ? ptNumber(result.densidade, 3) : "n/d", densityUnit),
    metric("Coordenação", result.nc, "vizinhos mais próximos"),
    metric("Átomos/célula", result.n, "n efetivo"));
}

// ---------------------------------------------------------------- tabela, contagem, interpretação
export function renderLower(result) {
  const { data } = state;
  const rows = data.estruturas.map((structure) => h("tr", { class: structure.sigla === result.estrutura ? "is-current" : "" },
    h("td", {}, `${structure.sigla} · ${structure.nome}`),
    h("td", {}, String(structure.n)),
    h("td", {}, String(structure.nc)),
    h("td", {}, structure.relacao),
    h("td", {}, ptNumber(structure.fea, 3))));
  const table = h("table", { class: "comparison-table" },
    h("thead", {}, h("tr", {}, ["Estrutura", "n", "NC", "Relação a–R", "FEA"].map((t) => h("th", {}, t)))),
    h("tbody", {}, rows));
  const hcNote = result.estrutura === "HC" && Math.abs(result.c_a - 1.633) > 0.002
    ? h("p", { class: "table-note" }, `FEA da HC na tabela usa c/a ideal (1,633). Com c/a = ${ptNumber(result.c_a, 3)} o FEA é ${ptNumber(result.fea, 4)}.`)
    : null;
  $("comparisonTable").replaceChildren(...[table, hcNote].filter(Boolean));

  const countRows = result.contagem.map((group) => h("div", { class: "count-row" },
    h("strong", {}, group.rotulo),
    h("span", { class: "bar-track" }, h("span", { class: "bar-fill", style: { width: `${Math.min(100, (group.contribuicao / result.n) * 100)}%` } })),
    h("span", {}, `${group.quantidade} × ${group.fracao_txt} = ${compactNumber(group.contribuicao)}`)));
  countRows.push(h("div", { class: "count-row count-total" },
    h("strong", {}, "Total (n)"), h("span"), h("span", {}, `${result.n} átomo${result.n > 1 ? "s" : ""}`)));
  $("countBody").replaceChildren(...countRows);

  $("interpretationTag").textContent = result.estrutura;
  const avisos = (result.avisos || []).map((line) => h("p", { class: "aviso", role: "note" }, `⚠ ${line}`));
  $("interpretationBody").replaceChildren(...avisos, ...result.interpretacao.map((line) => h("p", {}, line)));
}

export function renderDensity(result) {
  $("densityPanel").hidden = false;
  $("densitySteps").replaceChildren(...result.passos_densidade.map((step, index) => h("div", { class: "step" },
    h("span", { class: "step-index" }, String(index + 1)),
    h("div", {},
      h("strong", {}, step.titulo),
      h("pre", {}, step.formula),
      step.detalhe ? h("p", {}, step.detalhe) : null))));
}

// ---------------------------------------------------------------- planos e direções
export function overlayDetail(overlay) {
  if (overlay.tipo === "plano") {
    const spacing = overlay.d_nm ? `${ptNumber(overlay.d_nm, 4)} nm` : `${ptNumber(overlay.d_rel, 3)} a`;
    return `d = ${spacing} · ${overlay.atomos.length} centros atômicos no plano`;
  }
  const length = overlay.comprimento_nm ? `${ptNumber(overlay.comprimento_nm, 4)} nm` : `${ptNumber(overlay.comprimento_rel, 3)} a`;
  let linear = "";
  if (overlay.densidade_linear_nm) linear = ` · DL = ${ptNumber(overlay.densidade_linear_nm, 2)} át/nm`;
  else if (overlay.densidade_linear_rel) linear = ` · DL = ${ptNumber(overlay.densidade_linear_rel, 3)} át/a`;
  return `|v| = ${length}${linear}`;
}

export function renderOverlayList() {
  const overlayList = $("overlayList");
  if (!state.overlays.length) {
    overlayList.replaceChildren(h("span", { class: "overlay-empty" },
      "Nenhum plano ou direção desenhado. Ex.: ", h("code", {}, "plano 1 1 1"), " · ",
      h("code", {}, "direcao 1 1 0"), " · na HC: ", h("code", {}, "plano 1 0 -1 1")));
    return;
  }
  overlayList.replaceChildren(...state.overlays.map((overlay) => h("span", { class: "overlay-chip" },
    h("i", { style: { background: overlay.color } }),
    h("strong", {}, overlay.notacao),
    overlay.notacao_alternativa ? [" ", h("em", {}, overlay.notacao_alternativa)] : null,
    ` · ${overlayDetail(overlay)}`)));
}
