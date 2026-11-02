# Relatório de conclusão — Front-end Alloy Virtual Lab + CrystaLab (Etapa 8)

Data: 24/10/2026. Repositório: tag `etapa-8`. Ambiente de medição: contêiner Linux, Intel Xeon 2,1 GHz × 2 núcleos, 8 GB, Chromium 141 headless, WebGL por software (SwiftShader), viewport 1366×900 (e 360×740 no Fluxo E). Motor: CrystaLab v1.0 real (`legacy/crystalab_modulo1.py`); `/v1` pelo servidor de contrato de teste; HEA demonstrativo (D-01).

## 1. Comandos executados e resultados (8.1)

| Comando | Resultado |
|---|---|
| `npm run typecheck` | 0 erros (app, service worker, testes) |
| `npm run lint` | ok — 106 arquivos TS/TSX, 5 CSS, 9 regras |
| `npm test` | **76/76** testes unitários e de adaptadores |
| `npm run build` | sem erros; inicial 635,3 kB / **201,1 kB gzip** |
| `npm run measure` | meta de bundle **atingida** |
| `npx playwright test` | **54/54** testes de fluxo aprovados (2,4 min) |

## 2. Fluxos de validação

| Fluxo | O que comprova | Situação | Testes |
|---|---|---|---|
| A — Densidade do cobre | Cálculo guiado completo sem saber a sintaxe | **Aprovado** | `flow-a-density` A1 (laboratório, modo guiado) e A2 (exercício de 7 passos) |
| B — Plano de Miller | Representação consistente; estado compartilhável | **Aprovado** | `flow-b-miller` B1–B4, `etapa4-interaction` “Fluxo B sem digitar” |
| C — HEA → CrystaLab | Transição não cria dados nem altera o original | **Aprovado (com HEA demonstrativo)** | `flow-c-hea` C1–C3, `etapas5-7` 5.3 |
| D — Professor e turma | Real × demonstrativo; nada publicado sem serviço | **Aprovado** | `flow-d-instructor` D1–D2, `etapas5-7` 6.15 |
| E — Móvel com conexão limitada | 360 px; conectividade; registros locais preservados | **Aprovado (emulação)** | `flow-e-mobile-offline` E1–E3 |

## 3. Metas medidas (8.2)

| Meta | Alvo | Resultado real | Situação |
|---|---|---|---|
| Bundle inicial sem Three.js | < 300 kB gzip | 201,1 kB gzip | **Atingida** |
| Taxa de quadros (CFC 3×3×3, 172 esferas) | ≈ 60 FPS em notebook intermediário | 11,5 FPS em WebGL por software | **Não confirmada** — equipamento diferente do alvo (D-20) |
| Latência de seleção (mesmo cenário) | < 16 ms | 3,6 ms mediana, 13,6 ms máx. | **Atingida** |
| Lighthouse Accessibility | ≥ 95 | não medido (Lighthouse indisponível — D-19); auditoria própria: 0 violações em 20 páginas | **Não medida** |
| Largura mínima utilizável | 360 px | 9 rotas sem rolagem horizontal | **Atingida (emulação)** |
| Offline após o primeiro acesso | Recursos declarados locais | shell, caderno, viewer da cena carregada e flashcards funcionam offline | **Atingida** |

Dados brutos: `reports/metrics.json`, `reports/a11y.json`, `reports/bundle.json`, `reports/e2e-results.json`.

## 4. Regressões nos recursos preservados (8.3)

Temas claro/escuro (inclusive a preferência salva pelo v1.0), comandos do v1.0 (`usar`, `estrutura`, `plano`, `direcao`, `calcular densidade`, `limpar`), visualizações, resultados e os seis `data-testid` (`block-list`, `terminal-log`, `parameter-editor`, `render-button`, `result-root`, `viewer-stage`) — verificados por `foundation-regression` e pela regra R6 do lint. A interface legada continua em `/legacy/crystalab/`.

## 5. Implementado · testado · demonstrativo · pendente

**Implementado e testado automaticamente**
- Plataforma única HEA + CrystaLab sem recarga, rotas por módulo, URL de cena versionada e validada.
- Design system alloy-ui (tokens, temas, 6 categorias + nota, primitivos, catálogo `#/catalogo`); contraste testado.
- i18n pt-BR/en/es (959 mensagens), formatação numérica por idioma.
- Adaptadores com cancelamento, descarte de respostas obsoletas e erros tipados, testados contra o motor real.
- Viewer 3D: CS/CCC/CFC/HC do motor, seleção, painel do átomo, supercélulas, réplicas, planos/direções, clipping, medições, animações, render sob demanda.
- Linguagem de comandos (gramática, ambiguidades, equivalência), terminal, paleta Ctrl/⌘K, modo guiado, OverlayManager, desfazer/refazer, KaTeX, workspaces locais, exportação PNG/PDF/JSON e CIF/XYZ via `/v1`.
- Ponte HEA → CrystaLab imutável (store + URL), procedência, cor + forma por elemento.
- Didática: 9 atividades, exercício de 7 passos, dicas, tipos de erro, ABP, quiz/flashcards, progresso com recomendações e selos, caderno com captura de cena, painel do professor.
- Acessibilidade (auditoria própria), 360 px, toque, movimento reduzido, PWA offline.

**Demonstrativo (rotulado na interface)**
- Todo o módulo HEA (motor ausente — D-01).
- Turmas e indicadores do painel do professor (D-03).
- Animações de empilhamento e térmica, e a distribuição de elementos nos sítios (ilustrações — D-13, D-07).

**Desativado e identificado**
- Assistente de IA (D-08); poliedros de coordenação e famílias de planos (D-11); CIF/XYZ com o motor v1.0 (D-05).

**Pendente (fora do alcance deste ambiente ou de outra equipe)**
- Aprovação humana da classificação preservar/refatorar/novo (gate da Etapa 1) e validação das faixas dos exercícios pelo especialista em materiais (D-17).
- Medir FPS no notebook-alvo com GPU, testar em celular real e fazer inspeção manual com leitor de tela (D-20, 7.15).
- Lighthouse CI e axe-core; Vite/ESLint/Prettier (D-19).
- Motor HEA, serviço de turmas, workspaces no servidor, sincronização de notas, IA, dados do motor listados em D-05 a D-13.

## 6. Problemas remanescentes

1. A taxa de quadros só foi medida com renderização por CPU; o número real em GPU é desconhecido.
2. Os testes de 360 px e offline usam emulação do Chromium.
3. O texto integral do Tópico 9 do relatório de auditoria não está no projeto; o backlog segue as descrições do plano.
4. Polônio sem fonte autorizada e desvio do Ti continuam como avisos do motor (D-16); o front não corrige dados.

## 7. Documentação

`README.md` (instalação, execução, build, testes, estrutura) · `docs/decisoes-tecnicas.md` · relatórios por etapa em `docs/etapa-1/`, `docs/etapa-2/`, `docs/etapa-3-4/`, `docs/etapa-5-7/` · registro de pendências em `docs/etapa-1/registro-dependencias.md`.
