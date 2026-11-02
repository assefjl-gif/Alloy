# Etapas 3 e 4 — Viewer 3D científico · Terminal, paleta de comandos e modo guiado

Relatório de conclusão. Execução em 23–24/10/2026 no contêiner registrado na Etapa 1 (Xeon 2,1 GHz × 2 núcleos, 8 GB, Chromium 141 headless, **WebGL por software — SwiftShader**). Motor: CrystaLab v1.0 real (`legacy/crystalab_modulo1.py`); exportação CIF/XYZ testada contra o servidor de contrato `/v1` (`engine-stub/`).

## Resultado dos comandos

```
npm run typecheck   → 0 erros
npm run lint        → ok (9 regras)
npm test            → 76/76 testes unitários (inclui 49 casos de equivalência terminal ↔ operação)
npm run build       → inicial 199,1 kB gzip, Three.js só sob demanda
npm run e2e:etapa3 + e2e:etapa4 + e2e:etapa2 (regressão) → 36/36 testes Playwright aprovados
```

## Gate da Etapa 3

| Critério | Situação | Evidência (`tests/e2e/`) |
|---|---|---|
| Estruturas carregam com dados do motor | **Atingido** | `etapa3-viewer` 3.5: CS (Po), CCC (Fe), CFC (Cu), HC (Mg) — átomos desenhados e tipos de sítio = resposta do motor |
| Seleção mostra dados válidos | **Atingido** | 3.7/3.8: clique no centro do Fe → sítio, posição (0,5; 0,5; 0,5) e contribuição vindos do motor; Esc limpa |
| Réplicas não alteram contagens | **Atingido** | 3.9/3.10: Cu 2×2×2 = 63 esferas (27 vértices + 36 faces), só 14 não-réplicas; n e ρ inalterados |
| Cena parada não consome GPU | **Atingido** | 3.2: 0 quadros em 1,5 s parada; interação volta a desenhar; ao sair do módulo o canvas e o contexto WebGL são liberados |
| Métricas registradas | **Atingido (registradas)** | `perf-metrics` → `reports/metrics.json` |

### Metas medidas (3.18) — supercélula CFC 3×3×3 (172 esferas instanciadas)

| Meta | Alvo | Medido neste contêiner | Situação |
|---|---|---|---|
| Taxa de quadros | ≈ 60 FPS em notebook intermediário | **10,4 FPS** (WebGL por software) | **Não confirmada** — o equipamento do teste não é o do alvo (D-20) |
| Latência de seleção (raycast + estado + quadro do destaque) | < 16 ms | **4,6 ms** mediana, 13 ms máximo (14 cliques reais) | **Atingida** |

O FPS medido aqui reflete renderização por CPU, não o desempenho em GPU. Para melhorá-lo, as esferas passam a usar uma geometria mais leve quando a cena tem mais de 60 átomos (o valor subiu de 5,2 para cerca de 11 FPS). A meta de 60 FPS só pode ser declarada depois de medir em um notebook intermediário com GPU (D-20).

### Tarefas da Etapa 3

| Tarefa | Situação |
|---|---|
| 3.1 Viewer sob demanda, Three.js r160 local, cena separada do estado | Feito — chunk próprio (133 kB gzip), fora do inicial |
| 3.2 Render sob demanda, pausa com aba oculta, reuso de materiais, dispose | Feito e testado (exceto aba oculta: implementado via `visibilitychange`, sem teste automatizado) |
| 3.3 Atualização incremental + instancing | Feito (`InstancedMesh` por forma/sítio; overlays atualizados por diferença) |
| 3.4 Câmera por mouse, teclado e toque, serializável | Feito e testado (setas, +/−, Home; toque com cena travada por padrão; câmera vai na URL) |
| 3.5 CS/CCC/CFC/HC só com dados do motor | Feito e testado |
| 3.6 Esferas rígidas, bola-bastão, arestas, pontos de rede | Feito; **poliedros desativados com explicação** (o motor não envia — D-11) |
| 3.7 Seleção por raycasting, destaque, Esc | Feito e testado |
| 3.8 Painel acessível do átomo | Feito e testado; **fracionárias da HC** só quando o motor enviar `base` (D-09) |
| 3.9 Supercélula 1–4 por eixo, volta à unitária, aviso de custo | Feito e testado |
| 3.10 Réplicas fora de qualquer contagem | Feito e testado |
| 3.11 Planos/direções do motor, clipping | Feito; **famílias de planos** dependem do motor (D-11) |
| 3.12 Plano × direção diferenciados, itens independentes | Feito (contorno tracejado × seta; forma + cor + rótulo) |
| 3.13 Medições de distância e ângulo | Feito e testado (clique ou número do átomo; inválidas explicadas). É geometria do visualizador sobre posições do motor, rotulada como tal |
| 3.14 Empilhamento ABAB/ABCABC passo a passo | Feito e testado; **esquemático e rotulado como ilustração** (o motor não envia camadas A/B/C — D-13) |
| 3.15 α → γ do ferro | Feito com as duas estruturas reais do motor (Fe CCC e Fe forçado em CFC); quadros intermediários rotulados como transição visual, sem cinética |
| 3.16 Expansão térmica | **Só ilustrativa, sem números** (sem parâmetros térmicos válidos — D-07) |
| 3.17 Reproduzir/pausar/reiniciar/passo a passo + textos | Feito e testado; respeita movimento reduzido |
| 3.18 Medições | Feito (tabela acima) |

## Gate da Etapa 4

| Critério | Situação | Evidência |
|---|---|---|
| Fluxo A executável sem digitar comandos | **Atingido** | `flow-a-density` A1: modo guiado escolhe Cu, carrega e calcula a densidade; o terminal registra os comandos equivalentes “via formulário” |
| Fluxo B executável sem digitar comandos | **Atingido** | `etapa4-interaction` “Fluxo B sem digitar”: bloco Mg → formulário de 4 índices → plano → botão compartilhar → outra sessão reconstrói os mesmos dados |
| Teste de equivalência terminal ↔ formulário | **Atingido** | `tests/unit/commands.test.ts` (49 operações: `parse(toCommand(op)) ≡ op`) + `flow-b-miller` B1 (formulário e terminal produzem dados idênticos do motor) |
| Desfazer/refazer coerente | **Atingido** | `flow-b-miller` B2 (botões e Ctrl+Z) e `etapa4-interaction` 4.9 (desfazer remoção) — sem recálculo |
| Link compartilhado reconstrói a mesma cena | **Atingido** | `flow-b-miller` B3 (HC, plano de 4 índices, supercélula 2×2×1) e `etapa3-viewer` 3.4 (câmera); link adulterado é recusado (B4) |

### Tarefas da Etapa 4

| Tarefa | Situação |
|---|---|
| 4.1 Gramática formal + parser (sem regex sobre a linha inteira) | Feito — `src/commands/{lexer,parser,catalog}.ts`; comandos do v1.0 preservados |
| 4.2 Ambiguidades com escolha explícita | Feito e testado (`a=` minúsculo; texto que é metal e estrutura) |
| 4.3 Camada única de operações + teste de equivalência | Feito e testado (`src/commands/bus.ts`) |
| 4.4 Autocompletar, histórico ↑/↓, ajuda, exemplos | Feito e testado |
| 4.5 Estados (execução, conclusão, cancelamento, falha) e erros que ensinam a corrigir | Feito e testado (inclui cancelamento de uma consulta lenta) |
| 4.6 Paleta Ctrl/⌘K e botão, busca aproximada agrupada | Feito e testado (8 grupos, com sintaxe e descrição) |
| 4.7 Formulários: material, revisão, densidade, planos/direções | Feito e testado |
| 4.8 Comando equivalente de cada formulário | Feito e testado |
| 4.9 OverlayManager (visibilidade, cor Okabe–Ito, seleção, remoção) | Feito e testado |
| 4.10 Desfazer/refazer sobre o histórico, sem recalcular | Feito e testado |
| 4.11 Descarte de respostas obsoletas + carregamento com cancelar | Feito e testado |
| 4.12 KaTeX: fórmula, variáveis, substituição, resultado, interpretação | Feito e testado; etapas não fornecidas pelo motor não são inventadas (FEA — D-12) |
| 4.13 Estado na URL (câmera, overlays, visualização), limite de tamanho | Feito e testado (≤ 1 800 caracteres; sem dados pessoais; validação estrita) |
| 4.14 Workspaces | Feito e testado — **armazenamento local rotulado + exportar/importar JSON** (sem serviço — D-04) |
| 4.15 Exportação CIF/XYZ/PNG/PDF | PNG e JSON locais; PDF pela impressão do navegador (D-06); **CIF/XYZ só com a API /v1** — desabilitados com motivo no motor v1.0, funcionando com o servidor /v1 (D-05) |

## Correções feitas durante a verificação

- Link compartilhado aberto antes da detecção do motor não restaurava a cena — a restauração agora espera a detecção; link inválido carrega o material padrão em vez de deixar a tela em “Carregando…”.
- Ctrl+Z / Ctrl+Shift+Z anunciados nas dicas não estavam ligados — atalhos adicionados (fora de campos de texto).
- Latência de seleção media até o próximo quadro de animação — separada em trabalho de CPU e tempo até o quadro.
- Esferas com nível de detalhe por tamanho da cena.

## Pendências que ficam

D-05 (CIF/XYZ no motor stdlib), D-07 (parâmetros térmicos), D-09 (fracionárias da HC), D-11 (poliedros e famílias), D-12 (passos do FEA), D-13 (camadas A/B/C), D-04 (workspaces no servidor), **D-20 (medir FPS no notebook-alvo)**. A inspeção manual com leitor de tela (7.15) não foi feita.
