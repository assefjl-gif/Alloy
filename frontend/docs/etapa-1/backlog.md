# Backlog por épico (1.1)

Fonte: o plano de desenvolvimento (que resume as 5 sugestões de front-end do Tópico 9 do relatório de auditoria). O texto integral do Tópico 9 não está no projeto; o backlog segue as descrições do plano. Cada item aponta para a tarefa do plano e para o código.

Legenda de estado: ✅ implementado e testado · 🟡 implementado, verificação parcial · 🧪 demonstrativo (depende de pendência) · ⛔ bloqueado.

## Épico S1 — Arquitetura modular e design system (Etapa 2)

| Item | Tarefa | Estado | Onde |
|---|---|---|---|
| Plataforma única HEA + CrystaLab sem recarga | 2.1, 2.14 | ✅ | `src/app/`, `tests/e2e/foundation-regression.spec.ts` |
| TypeScript estrito, scripts de CI | 2.1 | ✅ (esbuild em vez de Vite — D-19) | `tsconfig.json`, `scripts/` |
| Adaptadores com modo demonstrativo explícito | 2.6 | ✅ | `src/services/adapters/` |
| Cancelamento e descarte de respostas obsoletas | 2.7 | ✅ | `src/services/api/http.ts`, `latest.ts` |
| Stores por domínio com histórico | 2.8 | ✅ | `src/stores/` |
| Tokens, temas, 6 categorias, primitivos, catálogo | 2.9–2.13 | ✅ | `src/design-system/`, rota `#/catalogo` |
| i18n pt-BR / en / es | 2.15 | ✅ | `src/i18n/` |
| Divisão de bundle e orçamento | 2.16 | ✅ medido | `scripts/build.mjs`, `reports/bundle.json` |
| Port de BlockBank e resultados com `data-testid` | 2.17 | ✅ | `src/modules/crystalab/` |

## Épico S2 — Viewer 3D científico (Etapa 3)

| Item | Tarefa | Estado |
|---|---|---|
| Viewer sob demanda, Three local, render sob demanda, dispose | 3.1–3.3 | ✅ |
| Câmera por mouse, teclado e toque, serializável | 3.4 | ✅ |
| CS/CCC/CFC/HC do motor; modos de exibição | 3.5–3.6 | ✅ (poliedros ⛔ D-11) |
| Seleção por raycasting + painel do átomo | 3.7–3.8 | ✅ (fracionárias HC 🧪 D-09) |
| Supercélulas 1–4, réplicas gráficas | 3.9–3.10 | ✅ |
| Planos, direções, clipping | 3.11–3.12 | ✅ (famílias ⛔ D-11) |
| Medições distância/ângulo | 3.13 | ✅ |
| Animações ABAB/ABCABC, α→γ, térmica | 3.14–3.17 | 🧪 ilustrativas onde faltam dados (D-07, D-13) |
| FPS e latência | 3.18 | 🟡 medido em contêiner (D-20) |

## Épico S3 — Interação unificada (Etapa 4)

| Item | Tarefa | Estado |
|---|---|---|
| Gramática formal + parser | 4.1–4.2 | ✅ |
| Barramento único + teste de equivalência | 4.3 | ✅ |
| Terminal (autocompletar, histórico, estados) | 4.4–4.5 | ✅ |
| Paleta Ctrl+K | 4.6 | ✅ |
| Modo guiado com comando equivalente | 4.7–4.8 | ✅ |
| OverlayManager, desfazer/refazer | 4.9–4.10 | ✅ |
| KaTeX, URL, workspaces, exportação | 4.12–4.15 | ✅ (CIF/XYZ 🧪 D-05) |

## Épico S4 — Didática ativa (Etapas 5 e 6)

| Item | Tarefa | Estado |
|---|---|---|
| Ponte HEA → CrystaLab imutável + procedência | 5.1–5.8 | ✅ com motor HEA 🧪 D-01 |
| Modelo de atividade, banco, sementes | 6.1–6.4 | ✅ (faixas 🧪 D-17) |
| ExerciseWorkspace 7 passos, dicas, tipos de erro | 6.5–6.7 | ✅ |
| ABP | 6.8–6.9 | ✅ |
| Quiz, flashcards, progresso | 6.10–6.11 | ✅ |
| IA | 6.12 | ⛔ D-08 (desativada, identificada) |
| Diário de laboratório | 6.13–6.14 | ✅ |
| Modo professor | 6.15–6.18 | ✅ interface e rascunhos · 🧪 turmas D-03 |

## Épico S5 — Acessibilidade, responsividade e PWA (Etapa 7)

| Item | Tarefa | Estado |
|---|---|---|
| Auditoria de componentes, anúncios, viewer acessível | 7.1–7.3 | ✅ (leitor de tela real 🟡 D-20) |
| Sem dependência de cor, movimento reduzido | 7.4–7.5 | ✅ |
| Layouts até 360 px, painéis recolhíveis, gesto no viewer | 7.6–7.9 | ✅ |
| Manifesto, service worker, conectividade, notas offline | 7.10–7.13 | ✅ |
| Auditoria automatizada | 7.14 | ✅ auditoria própria (axe/Lighthouse ⛔ D-19) |
