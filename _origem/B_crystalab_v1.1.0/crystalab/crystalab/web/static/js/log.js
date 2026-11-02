// Saída do terminal (região aria-live).
import { $ } from "./util.js";

export function logLine(text, className = "") {
  const terminalLog = $("terminalLog");
  const line = document.createElement("div");
  if (className) line.className = className;
  line.textContent = text;
  terminalLog.appendChild(line);
  terminalLog.scrollTop = terminalLog.scrollHeight;
}

export function clearLog() {
  $("terminalLog").replaceChildren();
}
