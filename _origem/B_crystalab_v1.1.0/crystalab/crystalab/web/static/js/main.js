// Ponto de entrada da UI do CrystaLab (módulo ES).
import {
  applyEditor, applyResult, clearOverlays, hideDensity, initTheme, loadStructure, setMode, setTheme,
  setToggle, toggleValue,
} from "./acoes.js";
import "./comandos.js";
import { state } from "./estado.js";
import { logLine } from "./log.js";
import { blockItems, renderBlocks } from "./paineis.js";
import { executeCommand } from "./terminal.js";
import { $ } from "./util.js";
import { viewer } from "./viewer.js";

function lerBootstrap() {
  const node = $("crystalab-bootstrap");
  return JSON.parse(node.textContent);
}

function ligarEventos() {
  const editor = $("parameterEditor");
  const terminalInput = $("terminalInput");

  $("terminalForm").addEventListener("submit", (event) => {
    event.preventDefault();
    executeCommand(terminalInput.value);
    terminalInput.value = "";
  });
  document.querySelectorAll(".shortcut-row button").forEach((button) => {
    button.addEventListener("click", () => executeCommand(button.dataset.command));
  });
  document.querySelectorAll(".segmented button").forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });
  document.querySelectorAll("[data-toggle]").forEach((button) => {
    button.addEventListener("click", () => setToggle(button.dataset.toggle, !toggleValue(button.dataset.toggle)));
  });
  $("millerForm").addEventListener("submit", (event) => {
    event.preventDefault();
    executeCommand(`${state.mode} ${$("millerInput").value}`);
  });
  $("clearOverlaysButton").addEventListener("click", () => {
    clearOverlays();
    logLine("planos e direções removidos.", "terminal-ok");
  });
  $("resetViewButton").addEventListener("click", () => viewer.resetView());
  $("densityClose").addEventListener("click", hideDensity);
  $("renderButton").addEventListener("click", applyEditor);
  $("themeToggle").addEventListener("click", () => setTheme(state.theme === "dark" ? "light" : "dark"));

  editor.addEventListener("dragover", (event) => { event.preventDefault(); editor.classList.add("is-drop-target"); });
  editor.addEventListener("dragleave", () => editor.classList.remove("is-drop-target"));
  editor.addEventListener("drop", (event) => {
    event.preventDefault();
    editor.classList.remove("is-drop-target");
    const key = event.dataTransfer.getData("text/plain");
    const item = blockItems().find((entry) => entry.key === key);
    if (item) loadStructure(item.payload);
  });
  editor.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); applyEditor(); }
  });
}

function iniciar() {
  state.data = lerBootstrap();
  renderBlocks(loadStructure);
  ligarEventos();
  initTheme();
  viewer.init();
  applyResult(state.data.inicial);
  logLine("terminal pronto. digite 'ajuda' para ver os comandos.");
}

iniciar();
