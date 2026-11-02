// Comandos do Módulo 1 — mesma sintaxe e mesma ordem de avaliação da v1.0.
import {
  applyEditor, clearOverlays, drawMiller, loadStructure, parseIndices, setMode, setTheme, setToggle,
  showDensity,
} from "./acoes.js";
import { state } from "./estado.js";
import { clearLog, logLine } from "./log.js";
import { comandoExato, linhasDeAjuda, registrarComando } from "./terminal.js";
import { $ } from "./util.js";

comandoExato("ajuda", ["ajuda", "help"], () => logLine(linhasDeAjuda().join("\n")));

// Textos de ajuda. Os comandos não se sobrepõem, então a ordem de registro = ordem da ajuda.
const AJUDA = {
  usar: ["usar Fe", "carrega um metal"],
  estrutura: ["estrutura CFC [r=0.128 A=63.55 c/a=1.62]", "  célula genérica"],
  plano: ["plano 1 1 1 | plano 1 0 -1 1", "desenha um plano"],
  direcao: ["direcao 1 1 0", "desenha uma direção"],
  densidade: ["calcular densidade", "passo a passo da densidade"],
  aplicar: ["aplicar", "usa os parâmetros do editor"],
};

registrarComando({
  id: "usar",
  ajuda: AJUDA.usar,
  testar: (_lower, raw) => raw.match(/^usar\s+(.+)$/i),
  executar: (match) => loadStructure({ nome: match[1].trim() }),
});

registrarComando({
  id: "estrutura",
  ajuda: AJUDA.estrutura,
  testar: (lower) => lower.match(/^estrutura\s+([a-z]+)(.*)$/),
  executar: (match) => {
    let rest = match[2];
    const payload = { nome: match[1] };
    const ratio = rest.match(/c\/a\s*=\s*([\d.,]+)/);
    if (ratio) { payload.c_a = ratio[1].replace(",", "."); rest = rest.replace(ratio[0], " "); }
    const radius = rest.match(/(?:^|\s)r\s*=\s*([\d.,]+)/);
    const weight = rest.match(/(?:^|\s)a\s*=\s*([\d.,]+)/);
    if (radius) payload.raio = radius[1].replace(",", ".");
    if (weight) payload.peso = weight[1].replace(",", ".");
    loadStructure(payload);
  },
});

registrarComando({
  id: "plano",
  ajuda: AJUDA.plano,
  testar: (lower) => lower.match(/^plano\s+(.+)$/),
  executar: (match) => {
    setMode("plano");
    $("millerInput").value = match[1].replace(/[()]/g, "").trim();
    drawMiller("plano", parseIndices(match[1]));
  },
});

registrarComando({
  id: "direcao",
  ajuda: AJUDA.direcao,
  testar: (lower) => lower.match(/^direcao\s+(.+)$/),
  executar: (match) => {
    setMode("direcao");
    $("millerInput").value = match[1].replace(/[[\]]/g, "").trim();
    drawMiller("direcao", parseIndices(match[1]));
  },
});

comandoExato("densidade", ["calcular densidade", "densidade"], () => showDensity(), AJUDA.densidade);

comandoExato("aplicar", ["aplicar", "renderizar"], () => applyEditor(), AJUDA.aplicar);

comandoExato("listar", ["listar"], () => {
  const metals = Object.entries(state.data.metais).map(([symbol, metal]) => `${symbol} (${metal.estrutura})`).join(", ");
  logLine(`metais: ${metals}\nestruturas: ${state.data.estruturas.map((s) => s.sigla).join(", ")}`);
}, "listar");

comandoExato("esferas", ["esferas"], () => {
  setToggle("rigid", !state.rigid);
  logLine(state.rigid ? "esferas rígidas (raio real R)." : "esferas reduzidas.", "terminal-ok");
}, "esferas");

comandoExato("girar", ["girar"], () => {
  setToggle("rotate", !state.autoRotate);
  logLine(state.autoRotate ? "auto-rotação ligada." : "auto-rotação desligada.", "terminal-ok");
}, "girar");

comandoExato("eixos", ["eixos"], () => setToggle("axes", !state.showAxes), "eixos");

comandoExato("tema", ["tema"], () => setTheme(state.theme === "dark" ? "light" : "dark"), "tema");

comandoExato("limpar", ["limpar"], () => {
  clearOverlays();
  clearLog();
  logLine("planos, direções e terminal limpos.", "terminal-ok");
}, "limpar");
