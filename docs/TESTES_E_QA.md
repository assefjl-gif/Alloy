# Testes e QA

Última execução: 02/11/2026, Windows 10, Python 3.15.1, Node 24.22, Chromium do Playwright.

## 1. Pirâmide e onde cada coisa é testada

| Camada | Onde | O que garante |
|---|---|---|
| Motores (unidade) | `backend/tests/unit/engines/` | valores conferidos à mão e por referência (célula, Miller, planar, supercélula, ligas, temperatura, HEA, exportação) |
| Regressão científica | `backend/tests/scientific/` | A/B/D produzem o mesmo resultado onde devem; divergências conhecidas (CR-08, Ti) explicadas |
| Arquitetura | `backend/tests/unit/test_arquitetura.py` | camadas por análise estática de imports; motores sem I/O; N_A definido uma única vez |
| Segurança (unidade) | `backend/tests/unit/test_seguranca.py` | política de senha, Argon2id, tokens, matriz RBAC célula a célula |
| Integração | `backend/tests/integration/` | migrações reais + seed + repositório SQL = seed JSON; histórico; FK; política de produção (SQLite sempre; PostgreSQL com `ALLOY_TEST_POSTGRES_URL`) |
| API | `backend/tests/api/` | HTTP real: erros padronizados, aliases, cabeçalhos, produção com banco migrado, HEA, contas (cookie, CSRF, bloqueio, expiração, revogação, isolamento), educacional (gabarito não vaza, IDOR, escopo) |
| Contrato | `backend/tests/contract/` + `scripts/contrato_frontend.mts` | uvicorn real × esquemas zod do frontend (38 respostas: rotas canônicas, aliases e HEA) |
| Front (unidade) | `frontend/tests/unit/` | comandos, núcleo, i18n e contraste AA; adaptadores e conta **contra o backend real** |
| Front (estático) | `npm run typecheck`, `npm run lint` | TS estrito + `openapi-compat.ts` (requisições cabem no OpenAPI); 9 regras do projeto |
| E2E | `frontend/tests/e2e/` (Playwright) | fluxos A–E, viewer, interação, teclado/a11y, offline, desempenho, orçamento do bundle |

## 2. Resultados

| Suíte | Comando | Resultado |
|---|---|---|
| Backend completo | `cd backend && python -m pytest` | **311 aprovados, 23 pulados, 0 falhas** |
| ↳ pulados | — | 22 variantes PostgreSQL (sem servidor aqui, L-01); 1 validação CIF com Gemmi (sem pacote para Python 3.15, T-01) |
| Lint backend | `ruff check .` | sem achados |
| Migrações | `python -m app.cli preparar && alembic check` | sem divergências |
| Contrato | (dentro do pytest) | **38/38** |
| Front typecheck | `npm run typecheck` | 0 erros |
| Front lint | `npm run lint` | ok — 112 arquivos TS/TSX, 5 CSS, 9 regras |
| Front unitários | `npm test` | **77/77** |
| E2E | `npm run e2e` | **54/55** na rodada final completa (backend real); o único que falhou (4.9, gerenciador de camadas) passou 5/5 repetido isolado → intermitente, registrado em PENDENCIAS (T-12) |
| Bundle | `npm run build && npm run measure` | inicial 204,2 kB gzip (meta < 300 kB), Three.js fora do carregamento inicial |

## 3. Como rodar

```bash
cd backend && ../.venv/Scripts/python -m pytest -rs           # -rs lista o motivo de cada teste pulado
ALLOY_TEST_POSTGRES_URL=postgresql+psycopg://u:s@localhost:5432/alloy_teste python -m pytest tests/integration
cd frontend && npm test                                        # sobe o backend real (../.venv ou ALLOY_PYTHON)
cd frontend && npm run build && npx playwright install chromium && npm run e2e
```

## 4. Critérios de aprovação (§13.5) — situação

| Critério | Situação |
|---|---|
| Zero erro crítico de compilação | ✔ (typecheck, ruff, build) |
| Testes obrigatórios aprovados no Linux **e** no Windows | ◐ Windows ✔ aqui; Linux só no CI (escrito, não executado — Q-07) |
| Nenhuma regressão nos fluxos preservados | ✔ regressão científica + E2E (ver §2) |
| Nenhuma divergência científica sem explicação | ✔ (CR-08 e Ti explicados nos testes) |
| Persistência após reinicialização | ✔ em SQLite (banco em arquivo + migrações); PostgreSQL pendente (L-01) |
| Contratos front/back gerados do OpenAPI | ✔ tipos gerados + verificação estática + contrato real |
| Build reproduzível | ✔ lockfile npm, `pyproject`, imagens Docker definidas (não construídas aqui, L-02) |
