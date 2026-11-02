// Cliente HTTP do contrato v1 (achados BE-01 / FE-02).
// URLs RELATIVAS: o módulo funciona em "/" e também montado em "/crystalab/" dentro do Alloy.
import { logLine } from "./log.js";

export const ENDPOINTS = Object.freeze({
  estrutura: "v1/crystals/structure",
  miller: "v1/crystallography/miller",
  densidade: "v1/calculations/density",
  cif: "v1/export/cif",
  xyz: "v1/export/xyz",
});

/** Remove null/undefined/"" para respeitar extra="forbid" e evitar campos vazios. */
function limpar(payload) {
  return Object.fromEntries(Object.entries(payload || {}).filter(([, v]) => v !== null && v !== undefined && v !== ""));
}

/**
 * POST JSON → devolve body.result ou null (o erro já é registrado no terminal).
 * Envelope de erro: { ok:false, error, code, status, correlation_id?, details? }.
 */
export async function postJson(url, payload, { signal } = {}) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(limpar(payload)),
      signal,
    });
    let body = null;
    try { body = await response.json(); } catch (error) { body = null; }
    if (!response.ok || !body || !body.ok) {
      const message = (body && body.error) || `Falha na requisição (HTTP ${response.status}).`;
      const suffix = body && body.correlation_id ? ` [${body.correlation_id}]` : "";
      logLine(message + suffix, "terminal-error");
      return null;
    }
    return body.result;
  } catch (error) {
    if (error && error.name === "AbortError") return null;
    logLine(`erro de comunicação: ${error.message}`, "terminal-error");
    return null;
  }
}
