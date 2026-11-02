# Etapa 2 — Fundação: arquitetura modular e design system

Relatório de conclusão da Etapa 2 do plano “Alloy Virtual Lab + CrystaLab — Plano de Desenvolvimento do Front-end por Etapas”. Medições e testes executados em 23–24/10/2026, no contêiner descrito em `docs/etapa-1/relatorio-inspecao.md` §4 (Xeon 2 núcleos, 8 GB, Chromium 141 headless).

## Gate da Etapa 2

| Critério do gate | Situação | Evidência |
|---|---|---|
| Build sem erros | **Atingido** | `npm run build` → `dist/` gerado, 0 erros |
| Typecheck e lint no CI | **Atingido** | `npm run typecheck` (3 projetos TS estritos, 0 erros) · `npm run lint` (9 regras, ok) · `.github/workflows/ci.yml` |
| Troca HEA ↔ CrystaLab sem recarga | **Atingido** | `tests/e2e/foundation-regression.spec.ts` — o `bootId` da página não muda ao navegar HEA → Aprender → Caderno → CrystaLab |
| Temas claro/escuro e 3 idiomas | **Atingido** | mesmo arquivo: `tema escuro/claro`, `idioma en/es/pt`; a chave `crystalab-theme` do v1.0 continua sendo lida |
| `data-testid` preservados | **Atingido** | `block-list`, `terminal-log`, `parameter-editor`, `render-button`, `result-root`, `viewer-stage` presentes e funcionais (teste e regra R6 do lint) |
| Bundle inicial < 300 kB gzip sem Three.js | **Atingido (medido)** | 629,7 kB brutos / **199,1 kB gzip**; Three.js, KaTeX, gráficos e `docx` só sob demanda — `reports/metrics.json` |

Resultado dos comandos do gate (última execução):

```
npm run typecheck   → 0 erros
npm run lint        → lint: ok (103 arquivos TS/TSX, 5 CSS, 9 regras)
npm test            → 76 testes, 76 aprovados
npm run build       → inicial 629.7 kB (199.1 kB gzip, Three no inicial: não)
npm run measure     → meta < 300 kB gzip: ATINGIDA
npm run e2e:etapa2  → 6 testes Playwright, 6 aprovados
```

## Tarefas

### 2A — Projeto e infraestrutura

| Tarefa | Situação | Onde |
|---|---|---|
| 2.1 React + TypeScript estrito + build; scripts typecheck/lint/test/build no CI | Feito, **com desvios registrados**: esbuild 0.28 no lugar do Vite (é o empacotador que o Vite usa); lint próprio no lugar do ESLint; sem Prettier — formatação fixada por `.editorconfig`. Motivo: registro npm bloqueado neste ambiente (D-19). Trocar por Vite/ESLint/Prettier é mecânico quando houver acesso ao registro. | `package.json`, `tsconfig*.json`, `scripts/build.mjs`, `scripts/lint.mjs`, `.github/workflows/ci.yml` |
| 2.2 Pastas por responsabilidade | Feito | `src/app`, `src/design-system`, `src/modules/{hea,crystalab}`, `src/features`, `src/services/{api,adapters}`, `src/stores`, `src/i18n`, `src/utils`, `tests/` |
| 2.3 Convivência com o legado | Feito: `scripts/serve.mjs` serve o novo build e faz proxy para o motor Python; a interface v1.0 continua em `/legacy/crystalab/` | `scripts/serve.mjs`, teste “interface legada” |
| 2.4 Playwright e primeiro teste (módulo sem recarga, tema, idioma) | Feito | `playwright.config.ts`, `tests/e2e/foundation-regression.spec.ts` |

### 2B — Serviços e estado

| Tarefa | Situação | Onde |
|---|---|---|
| 2.5 Cliente do OpenAPI ou contratos manuais | Contratos manuais (não há `/openapi.json` executável — D-15), validados em tempo de execução com zod a partir da matriz 1.4 | `src/services/api/contracts.ts` |
| 2.6 Adaptadores com modo demonstrativo explícito | Feito: `public/config.js` (`demo: auto/on/off`), `?demo=1`, preferência do usuário; selo “Demonstrativo” no cabeçalho e em todo dado fictício. HEA demonstrativo com semente fixa (motor ausente, D-01) | `src/services/adapters/`, `src/stores/capabilities.ts` |
| 2.7 AbortController e descarte de respostas obsoletas | Feito: `requestJson` com sinal, tempo-limite e erros tipados; `LatestRunner` cancela a chamada anterior e marca a antiga como obsoleta | `src/services/api/http.ts`, `latest.ts`; testes em `tests/unit/adapters.test.ts` (contra o motor real e o servidor de contrato `/v1`) |
| 2.8 Stores Zustand por domínio com histórico | Feito: material (`crystalab`), viewer, overlays, exercício (`didactics`), diário (`notebook`), preferências; histórico de cena para desfazer/refazer | `src/stores/`, `src/stores/history.ts` |

### 2C — Design system alloy-ui

| Tarefa | Situação | Onde |
|---|---|---|
| 2.9 Tokens centralizados | Feito: cores semânticas, tipografia, espaçamento, raios, sombras, estados, breakpoints, tokens do gráfico e do viewer | `src/design-system/tokens.css` |
| 2.10 Temas claro/escuro migrados | Feito, mesmas cores do v1.0 (painel do laboratório escuro nos dois temas) | `tokens.css`, `public/boot.js` |
| 2.11 Seis categorias de informação | Feito (+ “nota” do estudante): cor + ícone + rótulo + padrão de borda — a cor nunca é o único código | `components.css` (`.ds-cat-*`), `primitives/Category.tsx` |
| 2.12 Primitivos acessíveis + catálogo | Feito: Button/IconButton/ToggleButton, Dialog, Menu, Tabs, Tooltip, Toast (aria-live), campos; catálogo vivo em `#/catalogo` | `src/design-system/primitives/`, `src/modules/catalog/` |
| 2.13 Componentes de estrutura | Feito: AppShell, ModuleNavigation, MetricCard, StepPanel, SettingsPanel, Workbench (central + laterais + resultados) | `src/design-system/layout/` |

Contraste: teste automático dos pares de tokens nos dois temas (texto ≥ 4,5:1, elementos gráficos ≥ 3:1) — `tests/unit/i18n-tokens.test.ts`. A borda de campos (`--color-line-strong`) foi escurecida para atingir 3:1.

### 2D — Navegação, idioma e desempenho

| Tarefa | Situação | Onde |
|---|---|---|
| 2.14 Rotas por módulo + URL versionada validada | Feito: `#/crystalab`, `#/hea`, `#/aprender`, `#/diario`, `#/professor`, `#/catalogo`, `#/sobre`; estado em `?s=v1.<base64url>`, validado por esquema estrito (versão, tamanho ≤ 1800, campos desconhecidos recusados) | `src/app/router.ts`, `src/features/url/sceneUrl.ts` |
| 2.15 i18n pt-BR/en/es com formatação numérica | Feito: 942 mensagens geradas de tabelas-fonte com as 3 línguas lado a lado; teste de completude, de marcadores e de chaves sem uso; números por idioma (`8,94` / `8.94`). Textos que vêm do motor permanecem em português e isso é avisado | `src/i18n/source/*.tsv`, `scripts/i18n-build.mjs` |
| 2.16 Divisão do bundle e medição no CI | Feito e medido (tabela do gate) | `scripts/build.mjs`, `scripts/measure-bundle.mjs`, `reports/bundle.json` |
| 2.17 Port do BlockBank e resultados com `data-testid` | Feito: banco de blocos com filtro, editor de parâmetros (formato v1.0), métricas, comparação entre estruturas, contagem de átomos, interpretação didática com referência CAL9 | `src/modules/crystalab/` |

## Fora do escopo desta entrega

O repositório já contém código das Etapas 3 a 7 (viewer 3D completo, linguagem de comandos, integração HEA → CrystaLab, camada didática, PWA). Esse código **não faz parte desta entrega** e não teve seus gates verificados aqui; ele só aparece porque o port do v1.0 (2.17) precisa do viewer e do terminal para preservar `viewer-stage` e `terminal-log`.

## Pendências que afetam a Etapa 2

- **Gate da Etapa 1** — a classificação preservar/refatorar/novo continua aguardando aprovação da equipe e do especialista em materiais.
- **D-19** — Vite, ESLint, Prettier, axe-core e Lighthouse não puderam ser instalados; o CI usa substitutos documentados.
- **D-15** — sem OpenAPI executável; contratos manuais.
- **D-01** — sem motor HEA; módulo HEA em modo demonstrativo rotulado.
