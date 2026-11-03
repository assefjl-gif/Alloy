# Frontend

SPA em `frontend/`: React 19, TypeScript estrito, Zustand, Three.js r160 (sob demanda), KaTeX, zod,
empacotada com esbuild. Base: alloy-frontend (projeto C), migrada na Fase 5 (ADR-010).
Comandos: [`frontend/README.md`](../frontend/README.md).

## 1. Regra central

**O front não calcula ciência (PI-03).** Todo número exibido vem da API `/api/v1` e chega validado por
esquema zod. Sem servidor, cada recurso fica `disabled` ou, se a política permitir, em `demo`
rotulado (`stores/capabilities.ts → serviceMode`). Nunca há simulação silenciosa.

## 2. Módulos (roteador por hash, sem recarga)

| Rota | Módulo | Serviço do backend |
|---|---|---|
| `#/crystalab` | célula, Miller, densidade, viewer 3D, exportação CIF/XYZ | `/api/v1/crystallography/*`, `/exports/*` |
| `#/hea` | composição, ΔS_mix, δ, T_m, VEC, fase; indisponíveis com motivo; ponte para o CrystaLab | `/api/v1/hea/*` |
| `#/aprender` | atividades didáticas locais (prática) | — (local, com semente) |
| `#/diario` | caderno do estudante (exporta Markdown) | — (local) |
| `#/professor` | painel do professor (rascunho local) | — |
| `#/catalogo` | catálogo de materiais | `/api/v1/crystallography/metals` |
| `#/conta` | entrar, criar conta, sair (desta sessão ou de todas), **questões corrigidas no servidor**, histórico | `/api/v1/auth/*`, `/api/v1/edu/*`, `/api/v1/me/*` |
| `#/sobre` | estado dos serviços, disponibilidade offline, pendências, referências | `/api/v1/meta/version` |

## 3. Camada de serviços (`src/services/api/`)

* `http.ts`: o **único** ponto que chama `fetch` (regra R1 do lint). Tem tempo-limite, `AbortSignal`, erros
  tipados (`ApiError.kind`) e validação zod. Envia `X-Alloy-CSRF` em toda escrita quando há sessão.
* `crystalab.ts`, `hea.ts`, `auth.ts`, `edu.ts`: um adaptador por domínio, todos sobre `config.apiBase`
  (padrão `'.'`, mesmo domínio).
* `contracts.ts`: esquemas zod das respostas, com campos extras preservados.
* `openapi.gen.ts`: tipos gerados de `docs/openapi.json` (`npm run types:api`). `openapi-compat.ts` faz o
  `typecheck` falhar se as requisições do front deixarem de caber no contrato publicado.

## 4. Estado

Zustand por domínio (`stores/`): `capabilities`, `crystalab`, `viewer`, `overlays`, `history` (local),
`preferences` (tema, idioma, movimento; só em `localStorage` via `utils/storage.ts`, regra R5),
`account` (identidade **não** é persistida), `terminal`, `toast`.

## 5. Desempenho

* Bundle inicial: **204,2 kB gzip** (meta < 300 kB), sem Three.js no carregamento inicial (medido por
  `npm run measure` e verificado em `foundation-regression.spec.ts`).
* Módulos e viewer sob demanda (16 arquivos); service worker com pré-cache (88 arquivos) e funcionamento offline
  do que é local.

## 6. Mudanças da consolidação (Fase 5 em diante)

* Saíram o motor legado stdlib, o `engine-stub`, o `vendor/` e `scripts/link-deps.mjs`. Dependências via npm com lockfile.
* O cliente foi unificado em `apiBase` com rotas canônicas `/api/v1`. Os aliases `/v1` não são mais usados.
* `scripts/backend.mjs` sobe o FastAPI real para dev, testes e E2E (`--db` cria SQLite migrado).
* Portabilidade no Windows: caminhos com `/` no lint, no build e nos testes (BUG-01/BUG-02 da auditoria).
* HEA: contrato com grandezas anuláveis, painel de indisponíveis, gráficos e quiz protegidos contra `null`.
* Conta e questões do servidor (`#/conta`).
