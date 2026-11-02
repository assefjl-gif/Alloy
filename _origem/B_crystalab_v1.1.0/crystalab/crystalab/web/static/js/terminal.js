// Registro de comandos do terminal (preparação para FE-08 e para novos módulos).
//
// Antes: uma cadeia única de if/regex dentro de executeCommand — cada comando novo
// mexia na mesma função. Agora cada comando é registrado com registrarComando();
// um módulo futuro adiciona os seus em outro arquivo sem tocar neste.
import { logLine } from "./log.js";
import { plainText } from "./util.js";

const registro = [];

/**
 * @param {{ id: string,
 *           testar: (lower: string, raw: string) => any,   // devolve args (truthy) ou null
 *           executar: (args: any, raw: string) => void,
 *           ajuda?: [string, string] | string }} comando
 *   ajuda: [sintaxe, descrição] gera uma linha própria; string entra na linha de atalhos curtos.
 */
export function registrarComando(comando) {
  if (registro.some((c) => c.id === comando.id)) throw new Error(`comando duplicado: ${comando.id}`);
  registro.push(comando);
}

/** Atalho para comandos de palavra exata (ex.: "listar", "girar"). */
export function comandoExato(id, palavras, executar, ajuda) {
  const conjunto = new Set(palavras);
  registrarComando({ id, ajuda, executar, testar: (lower) => (conjunto.has(lower) ? true : null) });
}

export function linhasDeAjuda() {
  const linhas = ["comandos disponíveis:"];
  const curtos = [];
  for (const c of registro) {
    if (Array.isArray(c.ajuda)) linhas.push(`  ${c.ajuda[0].padEnd(29)}${c.ajuda[1]}`);
    else if (typeof c.ajuda === "string") curtos.push(c.ajuda);
  }
  if (curtos.length) linhas.push(`  ${curtos.join(" | ")}`);
  return linhas;
}

export function executeCommand(rawCommand) {
  const command = String(rawCommand || "").trim();
  if (!command) return;
  logLine(`> ${command}`, "terminal-entry");
  const lower = plainText(command);
  for (const c of registro) {
    const args = c.testar(lower, command);
    if (args) { c.executar(args, command); return; }
  }
  logLine("comando não reconhecido. digite 'ajuda'.", "terminal-error");
}
