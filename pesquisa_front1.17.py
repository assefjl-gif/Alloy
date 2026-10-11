import argparse
import json
import socket
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

from hea_engine import (
    ELEMENTOS,
    LIGAS_PRE_DEFINIDAS,
    REFERENCIA_CANTOR,
    analisar_liga,
    analisar_ligas_pre_definidas,
)


HTML_TEMPLATE = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HEA Virtual Lab</title>
  <style>
    :root {
      color-scheme: dark light;
      --ink: #10131a;
      --ink-soft: #29313f;
      --graphite: #11151c;
      --graphite-2: #171d26;
      --panel: #f5f7fb;
      --panel-2: #ffffff;
      --line: #dbe2eb;
      --muted: #687386;
      --cyan: #1aa7d9;
      --green: #19a56b;
      --amber: #d79319;
      --red: #ce3f4f;
      --violet: #7256d9;
      --radius: 8px;
      --shadow: 0 18px 44px rgba(10, 14, 20, 0.18);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", Arial, sans-serif;
      background: #0b0d10;
      color: var(--ink);
    }

    button,
    textarea,
    input {
      font: inherit;
    }

    .app-shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: minmax(340px, 430px) minmax(0, 1fr);
      background: var(--panel);
    }

    .left-lab {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto minmax(230px, 0.92fr) minmax(330px, 1.08fr);
      gap: 14px;
      padding: 18px;
      background: linear-gradient(180deg, #11151c 0%, #161c24 100%);
      color: #eef5f8;
      border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    .brand-row {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
    }

    .brand-row h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.08;
      color: #44c5f2;
      letter-spacing: 0;
    }

    .brand-row p {
      margin: 6px 0 0;
      color: #a9b6c6;
      font-size: 12px;
      line-height: 1.35;
    }
.lab-badge {
      flex: 0 0 auto;
      min-width: 62px;
      padding: 7px 9px;
      border: 1px solid rgba(68, 197, 242, 0.38);
      border-radius: 999px;
      color: #d8f5ff;
      text-align: center;
      font-size: 11px;
      background: rgba(68, 197, 242, 0.09);
    }

    .block-bank,
    .terminal-panel {
      min-width: 0;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.035);
    }

    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      min-height: 40px;
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      color: #f3f7fb;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0;
    }

    .count-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 26px;
      height: 22px;
      padding: 0 8px;
      border-radius: 999px;
      color: #10131a;
      background: #44c5f2;
      font-size: 12px;
      font-weight: 800;
    }

    .block-list {
      height: calc(100% - 41px);
      overflow: auto;
      padding: 10px;
      display: grid;
      gap: 10px;
      align-content: start;
    }

    .alloy-block {
      min-height: 86px;
      padding: 11px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: var(--radius);
      background: #202833;
      cursor: grab;
      transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
      user-select: none;
    }

    .alloy-block:hover,
    .alloy-block.is-active {
      transform: translateY(-1px);
      border-color: rgba(68, 197, 242, 0.65);
      background: #263140;
    }

    .alloy-block:active {
      cursor: grabbing;
    }

    .block-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .block-name {
      min-width: 0;
      color: #ffffff;
      font-size: 14px;
      font-weight: 750;
      overflow-wrap: anywhere;
    }

    .block-tag {
      flex: 0 0 auto;
      padding: 3px 7px;
      border-radius: 999px;
color: #11151c;
      background: #f2c85b;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .block-formula {
      margin: 8px 0 9px;
      color: #aebccc;
      font-size: 12px;
      line-height: 1.3;
    }

    .composition-strip {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 5px;
    }

    .element-chip {
      min-height: 24px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 5px;
      background: rgba(68, 197, 242, 0.12);
      color: #dff7ff;
      border: 1px solid rgba(68, 197, 242, 0.18);
      font-size: 11px;
      font-weight: 700;
    }

    .terminal-panel {
      display: grid;
      grid-template-rows: auto minmax(96px, 0.78fr) auto minmax(110px, 1fr) auto;
    }

    .composition-editor {
      width: 100%;
      min-height: 92px;
      resize: none;
      border: 0;
      outline: 0;
      padding: 12px;
      color: #f7fbff;
      background: #202833;
      line-height: 1.38;
      font-family: Consolas, "Courier New", monospace;
      font-size: 13px;
    }

    .composition-editor.is-drop-target {
      box-shadow: inset 0 0 0 2px #44c5f2;
      background: #253243;
    }

    .shortcut-row {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 7px;
      padding: 9px 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(0, 0, 0, 0.1);
    }

    .shortcut-row button,
    .terminal-submit,
    .primary-action {
      min-height: 34px;
      border: 0;
      border-radius: 6px;
      color: #071017;
      background: #44c5f2;
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
    }

    .shortcut-row button:nth-child(2) {
      background: #39c38d;
    }

    .shortcut-row button:nth-child(3) {
      background: #f2c85b;
    }

    .shortcut-row button:nth-child(4) {
      background: #c9d4e2;
    }

    .terminal-log {
      overflow: auto;
      padding: 12px;
      color: #dce6ef;
      background: #131922;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.45;
white-space: pre-wrap;
   }

   .terminal-entry {
     color: #9de4ff;
   }

   .terminal-error {
     color: #ff9cab;
   }

   .terminal-ok {
     color: #91f2c3;
   }

   .terminal-input-row {
     display: grid;
     grid-template-columns: minmax(0, 1fr) 86px;
     gap: 8px;
     padding: 10px;
     background: #202833;
   }

   .terminal-input {
     width: 100%;
     min-height: 36px;
     border: 1px solid rgba(255, 255, 255, 0.12);
     border-radius: 6px;
     outline: 0;
     padding: 0 10px;
     color: #f8fbff;
     background: #10151d;
   }

   .output-panel {
     min-width: 0;
     min-height: 100vh;
     display: grid;
     grid-template-rows: auto minmax(0, 1fr);
     background: var(--panel);
   }

   .topbar {
     min-height: 76px;
     display: flex;
     justify-content: space-between;
     align-items: center;
     gap: 18px;
     padding: 16px 22px;
     border-bottom: 1px solid var(--line);
     background: rgba(255, 255, 255, 0.86);
     backdrop-filter: blur(12px);
   }

   .topbar h2 {
     margin: 0;
     color: var(--ink);
     font-size: 23px;
     line-height: 1.08;
     letter-spacing: 0;
   }

   .topbar p {
     margin: 5px 0 0;
     color: var(--muted);
     font-size: 13px;
   }

   .primary-action {
     min-width: 130px;
     min-height: 40px;
     background: #11151c;
     color: #ffffff;
   }

   .result-scroll {
     min-width: 0;
     overflow: auto;
     padding: 18px 22px 26px;
     display: grid;
     gap: 16px;
     align-content: start;
   }

   .status-band {
     display: grid;
     grid-template-columns: minmax(0, 1fr) minmax(180px, 0.28fr);
     gap: 12px;
     align-items: stretch;
   }

   .verdict-box,
   .phase-box,
   .metric,
   .chart-panel,
   .table-panel,
   .interpretation-panel,
   .composition-panel {
     border: 1px solid var(--line);
     border-radius: var(--radius);
background: var(--panel-2);
     box-shadow: var(--shadow);
   }

   .verdict-box,
   .phase-box {
     padding: 15px;
   }

   .label {
     display: block;
     margin-bottom: 7px;
     color: var(--muted);
     font-size: 11px;
     font-weight: 800;
     text-transform: uppercase;
     letter-spacing: 0;
   }

   .verdict-text {
     margin: 0;
     color: var(--green);
     font-size: 20px;
     font-weight: 850;
     line-height: 1.22;
     overflow-wrap: anywhere;
   }

   .verdict-text.is-risk {
     color: var(--red);
   }

   .phase-box strong {
     display: block;
     color: var(--ink);
     font-size: 16px;
     line-height: 1.25;
   }

   .phase-box span {
     display: block;
     margin-top: 6px;
     color: var(--muted);
     font-size: 13px;
     line-height: 1.35;
   }

   .metrics-grid {
     display: grid;
     grid-template-columns: repeat(6, minmax(105px, 1fr));
     gap: 10px;
   }

   .metric {
     min-height: 86px;
     padding: 12px;
     box-shadow: none;
   }

   .metric-value {
     display: block;
     color: var(--ink);
     font-size: 22px;
     font-weight: 850;
     line-height: 1.08;
   }

   .metric-unit {
     display: block;
     margin-top: 7px;
     color: var(--muted);
     font-size: 12px;
     line-height: 1.25;
   }

   .visual-grid {
     display: grid;
     grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
     gap: 14px;
   }

   .chart-panel {
     min-height: 350px;
     display: grid;
     grid-template-rows: auto minmax(0, 1fr);
     overflow: hidden;
   }

   .panel-title {
     min-height: 42px;
     display: flex;
     align-items: center;
     justify-content: space-between;
     gap: 10px;
     padding: 11px 13px;
     border-bottom: 1px solid var(--line);
     color: var(--ink);
     font-size: 13px;
     font-weight: 800;
   }
.panel-title span {
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
    }

    canvas {
      width: 100%;
      height: 100%;
      display: block;
      background: #ffffff;
    }

    .lower-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(270px, 0.8fr);
      gap: 14px;
    }

    .table-panel,
    .interpretation-panel,
    .composition-panel {
      overflow: hidden;
      box-shadow: none;
    }

    .comparison-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .comparison-table th,
    .comparison-table td {
      padding: 11px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
    }

    .comparison-table th {
      color: #ffffff;
      background: #263140;
      font-size: 12px;
    }

    .comparison-table td {
      color: var(--ink-soft);
      background: #ffffff;
    }

    .delta-pos {
      color: var(--green);
      font-weight: 800;
    }

    .delta-neg {
      color: var(--red);
      font-weight: 800;
    }

    .interpretation-body,
    .composition-body {
      padding: 13px;
      display: grid;
      gap: 10px;
    }

    .interpretation-body p {
      margin: 0;
      color: var(--ink-soft);
      font-size: 13px;
      line-height: 1.45;
    }

    .composition-row {
      display: grid;
      grid-template-columns: 38px minmax(0, 1fr) 58px;
      gap: 9px;
      align-items: center;
      color: var(--ink-soft);
      font-size: 13px;
    }

    .bar-track {
      height: 9px;
      border-radius: 99px;
      background: #e6ebf2;
      overflow: hidden;
    }

    .bar-fill {
      height: 100%;
      border-radius: 99px;
      background: linear-gradient(90deg, var(--cyan), var(--green));
    }

    .empty-state {
      min-height: 260px;
      display: grid;
place-items: center;
      color: var(--muted);
      border: 1px dashed #b8c3d1;
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.62);
      text-align: center;
      padding: 28px;
    }

    @media (max-width: 1180px) {
      .metrics-grid {
        grid-template-columns: repeat(3, minmax(105px, 1fr));
      }

      .visual-grid,
      .lower-grid,
      .status-band {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 860px) {
      .app-shell {
        grid-template-columns: 1fr;
      }

      .left-lab {
        min-height: auto;
        grid-template-rows: auto minmax(220px, 360px) minmax(330px, 420px);
      }

      .output-panel {
        min-height: auto;
      }

      .topbar {
        align-items: stretch;
        flex-direction: column;
      }

      .primary-action {
        width: 100%;
      }
    }

    @media (max-width: 560px) {
      .left-lab,
      .result-scroll,
      .topbar {
        padding-left: 12px;
        padding-right: 12px;
      }

      .metrics-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .shortcut-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="left-lab">
      <header class="brand-row">
        <div>
          <h1>LABORATÓRIO VIRTUAL DE HEAs</h1>
          <p>Preditor termodinâmico educativo-interativo</p>
        </div>
        <div class="lab-badge">v1.17</div>
      </header>

      <section class="block-bank" aria-label="Ligas pré-definidas">
        <div class="section-title">
          <span>Blocos de ligas</span>
          <span class="count-pill" id="blockCount">0</span>
        </div>
        <div class="block-list" id="blockList" data-testid="block-list"></div>
      </section>

      <section class="terminal-panel" aria-label="Terminal da liga">
        <div class="section-title">
          <span>Composição</span>
          <span id="currentName">Liga de Cantor</span>
        </div>
        <textarea id="compositionEditor" class="composition-editor" spellcheck="false" data-testid="composition-editor"></textarea>
        <div class="shortcut-row">
          <button type="button" data-command="analisar">analisar</button>
          <button type="button" data-command="normalizar">normalizar</button>
          <button type="button" data-command="ajuda">ajuda</button>
          <button type="button" data-command="limpar">limpar</button>
        </div>
        <div id="terminalLog" class="terminal-log" data-testid="terminal-log"></div>
        <form class="terminal-input-row" id="terminalForm">
          <input id="terminalInput" class="terminal-input" autocomplete="off" aria-label="Comando" placeholder="comando" />
          <button class="terminal-submit" type="submit">enviar</button>
        </form>
      </section>
</aside>

    <section class="output-panel">
      <header class="topbar">
        <div>
          <h2 id="resultTitle">Análise da liga</h2>
          <p id="resultSubtitle">Referência comparativa: Liga de Cantor, 298.15 K e 1 atm</p>
        </div>
        <button class="primary-action" id="analyzeButton" type="button" data-testid="analyze-button">ANALISAR LIGA</button>
      </header>

      <main class="result-scroll" id="resultRoot" data-testid="result-root">
        <div class="empty-state">Selecione uma liga ou envie uma composição pelo terminal.</div>
      </main>
    </section>
  </div>

  <script>
    window.BOOTSTRAP_DATA = __BOOTSTRAP_JSON__;
  </script>
  <script>
    const data = window.BOOTSTRAP_DATA;
    const state = {
      selectedKey: "cantor",
      currentName: "Liga de Cantor",
      userNamed: false,
      samples: data.samples,
      latest: null,
      palette: ["#1aa7d9", "#19a56b", "#d79319", "#7256d9", "#ce3f4f", "#3f6ecf"]
    };

    const blockList = document.getElementById("blockList");
    const blockCount = document.getElementById("blockCount");
    const editor = document.getElementById("compositionEditor");
    const terminalLog = document.getElementById("terminalLog");
    const terminalForm = document.getElementById("terminalForm");
    const terminalInput = document.getElementById("terminalInput");
    const currentName = document.getElementById("currentName");
    const analyzeButton = document.getElementById("analyzeButton");
    const resultRoot = document.getElementById("resultRoot");
    const resultTitle = document.getElementById("resultTitle");

    function ptNumber(value, digits = 2) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/d";
      if (!Number.isFinite(Number(value))) return "∞";
      return Number(value).toLocaleString("pt-BR", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
      });
    }

    function compactNumber(value) {
      const number = Number(value);
      if (!Number.isFinite(number)) return String(value);
      if (Math.abs(number - Math.round(number)) < 0.0001) return String(Math.round(number));
      return number.toFixed(2).replace(".", ",");
    }

    function compositionToText(composition) {
      return Object.entries(composition)
        .map(([element, amount]) => `${element}=${compactNumber(amount)}`)
        .join("\n");
    }

    function parseCompositionText(text) {
      const composition = {};
      const regex = /([A-Za-z][a-z]?)\s*(?:=|:|\s)\s*(-?\d+(?:[\.,]\d+)?)/g;
      let match;
      while ((match = regex.exec(text)) !== null) {
        const element = match[1].charAt(0).toUpperCase() + match[1].slice(1).toLowerCase();
        const value = Number(match[2].replace(",", "."));
        if (Number.isFinite(value) && value > 0) {
          composition[element] = value;
        }
      }
      return composition;
    }

    function normalizeEditorToPercent() {
      const composition = parseCompositionText(editor.value);
      const total = Object.values(composition).reduce((sum, value) => sum + value, 0);
      if (total <= 0) {
        logLine("Nenhuma composição válida para normalizar.", "terminal-error");
        return;
      }
      const normalized = {};
      for (const [element, value] of Object.entries(composition)) {
        normalized[element] = (value / total) * 100;
      }
      editor.value = compositionToText(normalized);
      logLine("Composição normalizada para porcentagem atômica.", "terminal-ok");
    }

    function logLine(text, className = "") {
      const line = document.createElement("div");
      if (className) line.className = className;
      line.textContent = text;
      terminalLog.appendChild(line);
      terminalLog.scrollTop = terminalLog.scrollHeight;
    }

function renderBlocks() {
  blockList.innerHTML = "";
  const entries = Object.entries(data.alloys);
  blockCount.textContent = entries.length;

  for (const [key, alloy] of entries) {
    const block = document.createElement("article");
    block.className = "alloy-block";
    block.draggable = true;
    block.dataset.key = key;
    block.tabIndex = 0;

    const elements = Object.keys(alloy.composicao);
    block.innerHTML = `
      <div class="block-head">
        <div class="block-name">${alloy.nome}</div>
        <div class="block-tag">${alloy.grupo}</div>
      </div>
      <div class="block-formula">${elements.join(" + ")}</div>
      <div class="composition-strip">
        ${elements.slice(0, 5).map((element) => `<span class="element-chip">${element}</span>`).join("")}
      </div>
    `;

    block.addEventListener("click", () => loadAlloy(key, true));
    block.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        loadAlloy(key, true);
      }
    });
    block.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", key);
      event.dataTransfer.effectAllowed = "copy";
    });
    blockList.appendChild(block);
  }
}

function markActiveBlock() {
  document.querySelectorAll(".alloy-block").forEach((block) => {
    block.classList.toggle("is-active", block.dataset.key === state.selectedKey);
  });
}

function loadAlloy(key, shouldAnalyze = false) {
  const alloy = data.alloys[key];
  if (!alloy) {
    logLine(`Liga não encontrada: ${key}`, "terminal-error");
    return;
  }
  state.selectedKey = key;
  state.currentName = alloy.nome;
  state.userNamed = false;
  currentName.textContent = alloy.nome;
  editor.value = compositionToText(alloy.composicao);
  markActiveBlock();
  logLine(`bloco carregado: ${alloy.nome}`, "terminal-ok");
  if (shouldAnalyze) analyzeCurrent();
}

function markCompositionEdited(fallbackName) {
  state.selectedKey = "";
  if (!state.userNamed) {
    if (fallbackName === "Liga modificada" && state.currentName && !state.currentName.includes("editada")) {
      state.currentName = `${state.currentName} editada`;
    } else {
      state.currentName = fallbackName;
    }
  }
  currentName.textContent = state.currentName;
  markActiveBlock();
}

async function analyzeCurrent() {
  const composition = parseCompositionText(editor.value);
  if (Object.keys(composition).length < 2) {
    logLine("Informe pelo menos dois elementos com quantidade maior que zero.", "terminal-error");
    return;
  }

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: state.currentName || "Liga do usuário", composition })
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      logLine(payload.error || "Falha ao analisar liga.", "terminal-error");
      return;
    }
    state.latest = payload.result;
    renderResult(payload.result);
    logLine(`análise concluída: ${payload.result.veredito}`, payload.result.veredito.startsWith("ESTÁVEL") ? "terminal-ok" : "terminal-error");
  } catch (error) {
    logLine(`erro de comunicação: ${error.message}`, "terminal-error");
  }
}
function executeCommand(rawCommand) {
      const command = rawCommand.trim();
      if (!command) return;
      logLine(`> ${command}`, "terminal-entry");

      const lower = command.toLowerCase();
      if (lower === "ajuda") {
        logLine("atalhos: usar cantor | usar senkov | set Fe=20 Ni=20 Cr=20 Co=20 Mn=20 | add Cu=5 | rem Cu | nome Minha Liga | analisar | normalizar | limpar");
        return;
      }
      if (lower === "analisar" || lower === "run") {
        analyzeCurrent();
        return;
      }
      if (lower === "normalizar") {
        normalizeEditorToPercent();
        return;
      }
      if (lower === "limpar") {
        editor.value = "";
        state.currentName = "Liga do usuário";
        state.userNamed = false;
        currentName.textContent = state.currentName;
        markActiveBlock();
        logLine("editor limpo.", "terminal-ok");
        return;
      }

      const useMatch = lower.match(/^usar\s+(.+)$/);
      if (useMatch) {
        const alias = useMatch[1].trim();
        const found = Object.entries(data.alloys).find(([key, alloy]) => {
          const haystack = `${key} ${alloy.nome}`.toLowerCase();
          return haystack.includes(alias);
        });
        if (found) {
          loadAlloy(found[0], true);
        } else {
          logLine(`atalho sem liga correspondente: ${alias}`, "terminal-error");
        }
        return;
      }

      const nameMatch = command.match(/^nome\s+(.+)$/i);
      if (nameMatch) {
        state.currentName = nameMatch[1].trim() || "Liga do usuário";
        state.userNamed = true;
        currentName.textContent = state.currentName;
        logLine(`nome definido: ${state.currentName}`, "terminal-ok");
        return;
      }

      const addMatch = command.match(/^(add|somar)\s+([A-Za-z][a-z]?)\s*=?\s*(-?\d+(?:[\.,]\d+)?)/i);
      if (addMatch) {
        const composition = parseCompositionText(editor.value);
        const element = addMatch[2].charAt(0).toUpperCase() + addMatch[2].slice(1).toLowerCase();
        const value = Number(addMatch[3].replace(",", "."));
        composition[element] = (composition[element] || 0) + value;
        editor.value = compositionToText(composition);
        markCompositionEdited("Liga modificada");
        logLine(`${element} atualizado.`, "terminal-ok");
        analyzeCurrent();
        return;
      }

      const removeMatch = command.match(/^(rem|remove)\s+([A-Za-z][a-z]?)/i);
      if (removeMatch) {
        const composition = parseCompositionText(editor.value);
        const element = removeMatch[2].charAt(0).toUpperCase() + removeMatch[2].slice(1).toLowerCase();
        delete composition[element];
        editor.value = compositionToText(composition);
        markCompositionEdited("Liga modificada");
        logLine(`${element} removido.`, "terminal-ok");
        analyzeCurrent();
        return;
      }

      const setText = command.replace(/^set\s+/i, "");
      const parsed = parseCompositionText(setText);
      if (Object.keys(parsed).length >= 2) {
        editor.value = compositionToText(parsed);
        markCompositionEdited("Liga do usuário");
        analyzeCurrent();
        return;
      }

      logLine("comando não reconhecido.", "terminal-error");
    }

    function metric(label, value, unit) {
      return `
        <article class="metric">
          <span class="label">${label}</span>
          <span class="metric-value">${value}</span>
          <span class="metric-unit">${unit}</span>
        </article>
      `;
    }
    function renderResult(result) {
      const isStable = result.veredito.startsWith("ESTÁVEL");
      resultTitle.textContent = result.nome;
      resultRoot.innerHTML = `
        <section class="status-band">
          <div class="verdict-box">
            <span class="label">Veredito</span>
            <p class="verdict-text ${isStable ? "" : "is-risk"}">${result.veredito}</p>
          </div>
          <div class="phase-box">
            <span class="label">Propriedades</span>
            <strong>${result.fase}</strong>
            <span>Ductilidade ${result.ductilidade.toLowerCase()} · dureza ${result.dureza.toLowerCase()} (${ptNumber(result.dureza_indice, 0)}/100)</span>
          </div>
        </section>

        <section class="metrics-grid">
          ${metric("ΔS mix", ptNumber(result.dS, 2), "J/mol.K")}
          ${metric("ΔH mix", ptNumber(result.dH, 2), "kJ/mol")}
          ${metric("δ", ptNumber(result.delta, 2), "%")}
          ${metric("Ω", ptNumber(result.omega, 2), "adimensional")}
          ${metric("VEC", ptNumber(result.VEC, 2), "elétrons")}
          ${metric("Tm média", ptNumber(result.Tm, 0), "K")}
        </section>

        <section class="visual-grid">
          <div class="chart-panel">
            <div class="panel-title">Mapa de estabilidade <span>Zhang</span></div>
            <canvas id="stabilityChart" width="900" height="520"></canvas>
          </div>
          <div class="chart-panel">
            <div class="panel-title">Energia livre <span>ΔG = ΔH - TΔS</span></div>
            <canvas id="gibbsChart" width="900" height="520"></canvas>
          </div>
        </section>

        <section class="lower-grid">
          <div class="table-panel">
            <div class="panel-title">Comparação com Cantor <span>${data.reference.T_padrao} · ${data.reference.P_padrao}</span></div>
            ${renderComparisonTable(result)}
          </div>
          <div class="composition-panel">
            <div class="panel-title">Composição normalizada <span>% atômica</span></div>
            <div class="composition-body">${renderComposition(result.comp_percent)}</div>
          </div>
        </section>

        <section class="interpretation-panel">
          <div class="panel-title">Interpretação didática <span>motor 1.15/1.16</span></div>
          <div class="interpretation-body">
            ${result.interpretacao.map((line) => `<p>${line}</p>`).join("")}
            ${result.fragilidade ? `<p>${result.fragilidade}</p>` : ""}
          </div>
        </section>
      `;

      requestAnimationFrame(() => {
        drawStabilityChart(document.getElementById("stabilityChart"), result);
        drawGibbsChart(document.getElementById("gibbsChart"), result);
      });
    }

    function renderComparisonTable(result) {
      const rows = [
        ["Entropia (ΔS)", result.dS, data.reference.dS, "%", true],
        ["Ômega (Ω)", result.omega, data.reference.omega, "%", true],
        ["Distorção (δ)", result.delta, data.reference.delta, "abs", false],
        ["VEC", result.VEC, data.reference.VEC, "abs", true],
        ["Entalpia (ΔH)", result.dH, data.reference.dH, "abs", false]
      ];

      return `
        <table class="comparison-table">
          <thead>
            <tr>
              <th>Parâmetro</th>
              <th>Calculado</th>
              <th>Referência</th>
              <th>Diferença</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(([label, value, reference, mode, highIsGood]) => {
              const diff = mode === "%" ? ((value / reference) - 1) * 100 : value - reference;
              const positive = highIsGood ? diff >= 0 : Math.abs(value) <= Math.abs(reference);
              return `
                <tr>
                  <td>${label}</td>
                  <td>${ptNumber(value, 2)}</td>
                  <td>${ptNumber(reference, 2)}</td>
                  <td class="${positive ? "delta-pos" : "delta-neg"}">${mode === "%" ? `${diff >= 0 ? "+" : ""}${ptNumber(diff, 1)}%` : `${diff >= 0 ? "+" : ""}${ptNumber(diff, 2)}`}</td>
                </tr>
              `;
            }).join("")}
          </tbody>
        </table>
      `;
    }

    function renderComposition(compPercent) {
const entries = Object.entries(compPercent).sort((a, b) => b[1] - a[1]);
     return entries.map(([element, percent]) => `
       <div class="composition-row">
         <strong>${element}</strong>
         <span class="bar-track"><span class="bar-fill" style="width:${Math.min(100, percent)}%"></span></span>
         <span>${ptNumber(percent, 1)}%</span>
       </div>
     `).join("");
   }

   function setupCanvas(canvas) {
     const context = canvas.getContext("2d");
     const rect = canvas.getBoundingClientRect();
     const ratio = window.devicePixelRatio || 1;
     canvas.width = Math.max(1, Math.round(rect.width * ratio));
     canvas.height = Math.max(1, Math.round(rect.height * ratio));
     context.setTransform(ratio, 0, 0, ratio, 0, 0);
     return { context, width: rect.width, height: rect.height };
   }

   function drawAxes(context, plot, labels) {
     context.strokeStyle = "#cfd8e4";
     context.lineWidth = 1;
     context.beginPath();
     context.moveTo(plot.left, plot.top);
     context.lineTo(plot.left, plot.bottom);
     context.lineTo(plot.right, plot.bottom);
     context.stroke();

     context.fillStyle = "#526070";
     context.font = "12px Segoe UI, Arial";
     context.textAlign = "center";
     context.fillText(labels.x, (plot.left + plot.right) / 2, plot.bottom + 38);
     context.save();
     context.translate(plot.left - 45, (plot.top + plot.bottom) / 2);
     context.rotate(-Math.PI / 2);
     context.fillText(labels.y, 0, 0);
     context.restore();
   }

   function drawStabilityChart(canvas, selected) {
     if (!canvas) return;
     const { context, width, height } = setupCanvas(canvas);
     context.clearRect(0, 0, width, height);
     context.fillStyle = "#ffffff";
     context.fillRect(0, 0, width, height);

     const plot = { left: 66, top: 24, right: width - 24, bottom: height - 58 };
     const points = [...state.samples, selected];
     const xMax = Math.max(8, ...points.map((point) => point.delta + 1));
     const yMin = Math.min(-18, ...points.map((point) => point.dH - 4));
     const yMax = Math.max(8, ...points.map((point) => point.dH + 4));
     const x = (value) => plot.left + (value / xMax) * (plot.right - plot.left);
     const y = (value) => plot.bottom - ((value - yMin) / (yMax - yMin)) * (plot.bottom - plot.top);

     context.fillStyle = "rgba(25, 165, 107, 0.12)";
     context.fillRect(plot.left, y(5), x(6.6) - plot.left, y(-15) - y(5));

     context.strokeStyle = "#edf1f6";
     context.lineWidth = 1;
     context.font = "11px Segoe UI, Arial";
     context.fillStyle = "#687386";
     for (let i = 0; i <= 5; i++) {
       const tx = (xMax / 5) * i;
       const px = x(tx);
       context.beginPath();
       context.moveTo(px, plot.top);
       context.lineTo(px, plot.bottom);
       context.stroke();
       context.textAlign = "center";
       context.fillText(ptNumber(tx, 1), px, plot.bottom + 18);
     }
     for (let i = 0; i <= 5; i++) {
       const ty = yMin + ((yMax - yMin) / 5) * i;
       const py = y(ty);
       context.beginPath();
       context.moveTo(plot.left, py);
       context.lineTo(plot.right, py);
       context.stroke();
       context.textAlign = "right";
       context.fillText(ptNumber(ty, 0), plot.left - 8, py + 4);
     }

     context.strokeStyle = "#ce3f4f";
     context.setLineDash([7, 6]);
     context.beginPath();
     context.moveTo(x(6.6), plot.top);
     context.lineTo(x(6.6), plot.bottom);
     context.stroke();
     context.setLineDash([]);

     drawAxes(context, plot, { x: "Distorção atômica δ (%)", y: "Entalpia ΔH (kJ/mol)" });

     points.forEach((point, index) => {
       const isSelected = point === selected;
       context.fillStyle = isSelected ? "#ce3f4f" : state.palette[index % state.palette.length];
       context.strokeStyle = "#10131a";
       context.lineWidth = isSelected ? 2.5 : 1.5;
       context.beginPath();
       context.arc(x(point.delta), y(point.dH), isSelected ? 7 : 5, 0, Math.PI * 2);
       context.fill();
       context.stroke();

    context.fillStyle = "#29313f";
    context.font = isSelected ? "700 12px Segoe UI, Arial" : "11px Segoe UI, Arial";
    context.textAlign = "left";
    context.fillText(point.nome, x(point.delta) + 10, y(point.dH) - 8);
  });

  context.fillStyle = "#4b775e";
  context.font = "12px Segoe UI, Arial";
  context.textAlign = "left";
  context.fillText("zona estável", plot.left + 10, y(4) + 16);
}

function drawGibbsChart(canvas, selected) {
  if (!canvas) return;
  const { context, width, height } = setupCanvas(canvas);
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  const plot = { left: 70, top: 24, right: width - 24, bottom: height - 58 };
  const series = [...state.samples.slice(0, 3), selected];
  const allValues = series.flatMap((item) => item.gibbs.map((point) => point.G));
  const yMin = Math.min(...allValues, -50000);
  const yMax = Math.max(...allValues, 5000);
  const xMin = 300;
  const xMax = 3000;
  const x = (value) => plot.left + ((value - xMin) / (xMax - xMin)) * (plot.right - plot.left);
  const y = (value) => plot.bottom - ((value - yMin) / (yMax - yMin)) * (plot.bottom - plot.top);

  context.strokeStyle = "#edf1f6";
  context.lineWidth = 1;
  context.font = "11px Segoe UI, Arial";
  context.fillStyle = "#687386";
  for (let i = 0; i <= 6; i++) {
    const tx = xMin + ((xMax - xMin) / 6) * i;
    const px = x(tx);
    context.beginPath();
    context.moveTo(px, plot.top);
    context.lineTo(px, plot.bottom);
    context.stroke();
    context.textAlign = "center";
    context.fillText(ptNumber(tx, 0), px, plot.bottom + 18);
  }
  for (let i = 0; i <= 5; i++) {
    const ty = yMin + ((yMax - yMin) / 5) * i;
    const py = y(ty);
    context.beginPath();
    context.moveTo(plot.left, py);
    context.lineTo(plot.right, py);
    context.stroke();
    context.textAlign = "right";
    context.fillText(ptNumber(ty / 1000, 0) + "k", plot.left - 8, py + 4);
  }

  context.strokeStyle = "#10131a";
  context.lineWidth = 1.3;
  context.beginPath();
  context.moveTo(plot.left, y(0));
  context.lineTo(plot.right, y(0));
  context.stroke();

  drawAxes(context, plot, { x: "Temperatura (K)", y: "ΔG (J/mol)" });

  series.forEach((item, index) => {
    const isSelected = item === selected;
    context.strokeStyle = isSelected ? "#ce3f4f" : state.palette[index % state.palette.length];
    context.lineWidth = isSelected ? 3 : 1.8;
    context.beginPath();
    item.gibbs.forEach((point, pointIndex) => {
      const px = x(point.T);
      const py = y(point.G);
      if (pointIndex === 0) context.moveTo(px, py);
      else context.lineTo(px, py);
    });
    context.stroke();

    const last = item.gibbs[item.gibbs.length - 1];
    context.fillStyle = context.strokeStyle;
    context.font = isSelected ? "700 12px Segoe UI, Arial" : "11px Segoe UI, Arial";
    context.textAlign = "right";
    context.fillText(item.nome, plot.right - 4, y(last.G) - 5);
  });
}

terminalForm.addEventListener("submit", (event) => {
  event.preventDefault();
  executeCommand(terminalInput.value);
  terminalInput.value = "";
});

document.querySelectorAll(".shortcut-row button").forEach((button) => {
  button.addEventListener("click", () => executeCommand(button.dataset.command));
});

analyzeButton.addEventListener("click", analyzeCurrent);

editor.addEventListener("dragover", (event) => {
  event.preventDefault();
      editor.classList.add("is-drop-target");
    });
    editor.addEventListener("dragleave", () => editor.classList.remove("is-drop-target"));
    editor.addEventListener("drop", (event) => {
      event.preventDefault();
      editor.classList.remove("is-drop-target");
      const key = event.dataTransfer.getData("text/plain");
      loadAlloy(key, true);
    });

    window.addEventListener("resize", () => {
      if (state.latest) {
        drawStabilityChart(document.getElementById("stabilityChart"), state.latest);
        drawGibbsChart(document.getElementById("gibbsChart"), state.latest);
      }
    });

    renderBlocks();
    loadAlloy("cantor", false);
    logLine("terminal pronto.");
    analyzeCurrent();
  </script>
</body>
</html>
"""


def bootstrap_payload() -> Dict[str, Any]:
    return {
        "elements": ELEMENTOS,
        "alloys": LIGAS_PRE_DEFINIDAS,
        "reference": REFERENCIA_CANTOR,
        "samples": analisar_ligas_pre_definidas(),
    }


def render_index() -> bytes:
    payload = json.dumps(bootstrap_payload(), ensure_ascii=False)
    return HTML_TEMPLATE.replace("__BOOTSTRAP_JSON__", payload).encode("utf-8")


class HEARequestHandler(BaseHTTPRequestHandler):
    server_version = "HEAVirtualLab/1.17"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_bytes(self, body: bytes, content_type: str = "text/html; charset=utf-8", status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_bytes(render_index())
            return
        if path == "/api/bootstrap":
            self._send_json(bootstrap_payload())
            return
        if path == "/api/elements":
            self._send_json({"ok": True, "elements": ELEMENTOS})
            return
        if path == "/api/alloys":
            self._send_json({"ok": True, "alloys": LIGAS_PRE_DEFINIDAS})
            return
        self._send_json({"ok": False, "error": "Rota não encontrada."}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "JSON inválido."}, 400)
            return

        if path == "/api/analyze":
            nome = str(payload.get("name") or "Liga do usuário")
            composicao = payload.get("composition") or {}
            if not isinstance(composicao, dict):
                self._send_json({"ok": False, "error": "Composição deve ser um objeto elemento: valor."}, 400)
                return
            try:
                composicao_float = {str(k): float(v) for k, v in composicao.items()}
            except (TypeError, ValueError):
                self._send_json({"ok": False, "error": "Todos os valores da composição devem ser numéricos."}, 400)
                return

            resultado = analisar_liga(nome, composicao_float)
            if "erro" in resultado:
                self._send_json({"ok": False, "error": resultado["erro"], "result": resultado}, 400)
                return
            self._send_json({"ok": True, "result": resultado})
            return

        self._send_json({"ok": False, "error": "Rota não encontrada."}, 404)


def encontrar_porta(preferida: int) -> int:
    for porta in range(preferida, preferida + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as teste:
            teste.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                teste.bind(("127.0.0.1", porta))
            except OSError:
                continue
            return porta
    raise RuntimeError("Nenhuma porta livre encontrada.")


def main() -> None:
    parser = argparse.ArgumentParser(description="HEA Virtual Lab")
    parser.add_argument("--port", type=int, default=8000, help="porta inicial do servidor")
    parser.add_argument("--open", action="store_true", help="abrir no navegador padrão")
    args = parser.parse_args()

    porta = encontrar_porta(args.port)
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), HEARequestHandler)
    url = f"http://127.0.0.1:{porta}"

    print(f"HEA Virtual Lab disponível em {url}")
    print("Use Ctrl+C para encerrar.")

    if args.open:
        webbrowser.open(url)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()