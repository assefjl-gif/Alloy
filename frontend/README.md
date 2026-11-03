# frontend/

SPA do Alloy Virtual Lab: React 19 + TypeScript estrito, Zustand, Three.js r160, KaTeX e zod,
empacotada com esbuild (scripts/build.mjs). Origem: alloy-frontend (`_origem/C`), migrada na Fase 5.

**Nenhum cálculo científico acontece aqui (PI-03).** Todo número exibido vem da API unificada
(`/api/v1`, ver `docs/API.md`); sem servidor, os recursos ficam desativados ou em modo
demonstrativo rotulado — nunca simulados em silêncio.

## Comandos

| Comando | O que faz |
|---|---|
| `npm install` | instala dependências (lockfile versionado) |
| `npm run engine` | sobe o backend (FastAPI) em `127.0.0.1:8010` usando `../.venv` ou `ALLOY_PYTHON` |
| `npm run dev` | build em modo watch + servidor em `127.0.0.1:5173` com proxy `/api` → backend |
| `npm run build` / `npm run serve` | build de produção em `dist/` e servidor estático com proxy |
| `npm run typecheck` | `tsc` estrito (app, service worker e scripts) — inclui a verificação estática contra o OpenAPI |
| `npm run lint` | regras do projeto (scripts/lint.mjs, R1–R9) |
| `npm test` | testes unitários (`node --test`); os de adaptador sobem o backend real |
| `npm run e2e` | Playwright contra `dist/` + backend real (requer `npx playwright install chromium`) |
| `npm run types:api` | regenera `src/services/api/openapi.gen.ts` a partir de `../docs/openapi.json` |

## Configuração em tempo de implantação

`public/config.js` define `apiBase` (padrão `'.'`: mesmo domínio do front, servido pelo Caddy —
ADR-011) e a política `demo` (`auto` | `on` | `off`). Não é preciso recompilar para mudar.

## Contrato com o backend

1. **Estático:** `openapi.gen.ts` é gerado do `docs/openapi.json`; `openapi-compat.ts` faz o
   `typecheck` falhar se as requisições do front deixarem de caber no contrato.
2. **Tempo de execução:** os esquemas zod de `contracts.ts` validam toda resposta.
3. **Integração:** `backend/tests/contract` sobe o backend real e valida as respostas com esses
   mesmos esquemas (34 casos, rotas canônicas e aliases `/v1`).

O histórico de desenvolvimento herdado do projeto C está em `docs/` (somente referência).
