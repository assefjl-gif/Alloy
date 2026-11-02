# Etapas 5, 6 e 7 — Integração HEA ↔ CrystaLab · Didática ativa · Acessibilidade, responsividade e PWA

Execução em 23–24/10/2026, mesmo contêiner das etapas anteriores. O motor HEA não está no projeto (D-01): todo resultado HEA nestes testes é **demonstrativo**, gerado com semente fixa e selado na interface.

## Gate da Etapa 5

| Critério | Situação | Evidência (`tests/e2e/`) |
|---|---|---|
| Fluxo C aprovado | **Atingido** | `flow-c-hea` C1: o resultado no módulo HEA é idêntico (JSON byte a byte) antes e depois da transição; a cópia no CrystaLab está congelada e é igual à original |
| Nenhuma estrutura idealizada apresentada como previsão validada | **Atingido** | C1: célula genérica sem densidade (“n/d”), aviso “célula idealizada”, limitação de δ; C2/C3: fase ambígua exige escolha marcada “escolhida por você — não é predição” |

| Tarefa | Situação |
|---|---|
| 5.1 Contrato do resultado HEA | Feito (`HeaResult` em zod; `estrutura_sugerida` opcional) |
| 5.2 Regra de correspondência | Feito e testado (campo do preditor → fase com estrutura única → escolha explícita) |
| 5.3 “Abrir no CrystaLab” via store **e URL**, imutável | Feito e testado: a URL leva `h=<impressão digital>`; a cópia fica no armazenamento da aba e é rejeitada se alterada (`etapas5-7` 5.3) |
| 5.4 Cor + forma por elemento com legenda textual | Feito e testado; ocupação mista só como ilustração |
| 5.5 Distribuição aleatória só em modo demonstrativo, com semente e selo | Feito e testado |
| 5.6 Distorção por δ | Não desenhada (sem base de cálculo); a limitação é exibida |
| 5.7 Painel de procedência | Feito (preditor · referência do motor · ilustração) |
| 5.8 Teste do Fluxo C | Feito |

## Gate da Etapa 6

| Critério | Situação | Evidência |
|---|---|---|
| Fluxo A completo com participação ativa do aluno | **Atingido** | `flow-a-density` A2: 7 passos; erro de equação e **erro de unidade** classificados; resultado do motor só depois da tentativa; registro no caderno; progresso atualizado |
| Fluxo D distingue dados reais de demonstrativos | **Atingido** | `flow-d-instructor` D1/D2: turma demonstrativa selada (semente 4242) × dados deste navegador (vazios até haver tentativas reais); relatório Word marcado DEMONSTRATIVO |

| Tarefa | Situação |
|---|---|
| 6.1 Modelo de atividade | Feito (`src/modules/didactics/model.ts`) |
| 6.2 Sementes determinísticas | Feito e testado; **faixas validadas pelo especialista ainda pendentes (D-17)** — só materiais do catálogo do motor |
| 6.3 Banco do CrystaLab | 9 atividades: estruturas, células, FEA, densidade (2), planos, direções, ABP, quiz |
| 6.4 Exercício HEA | Só sobre δ e ΔH que o preditor retorna (mapa de estabilidade) |
| 6.5–6.7 ExerciseWorkspace, dicas progressivas, tipos de erro | Feito e testado (conceitual, algébrico, unidade, entrada) |
| 6.8–6.9 ABP | Feito e testado (hipóteses comparáveis; evidências observação/cálculo/interpretação) |
| 6.10 Quiz e flashcards | Feito (embaralhamento por semente, feedback com referência CAL9) |
| 6.11 Progresso, histórico, recomendações, selos, sem ranking | Feito e testado |
| 6.12 IA | **Desativada e identificada** (D-08); adaptador pronto |
| 6.13–6.14 Caderno | Feito e testado: notas por tipo, captura da cena, valores do motor, link; persistência local rotulada |
| 6.15–6.18 Professor | Feito: tarefas com instruções e critérios, rascunhos locais, gráficos com pergunta didática, PDF/Word só com dados; **publicação nunca confirmada** (D-03) |

## Gate da Etapa 7

| Critério | Situação | Evidência |
|---|---|---|
| Fluxo E aprovado | **Atingido** | `flow-e-mobile-offline` E1–E3: 9 rotas sem rolagem horizontal em 360 px; cena travada ao toque (rolagem preservada) e destravável; offline com shell do cache, estado comunicado, nota criada offline preservada e anunciada ao reconectar |
| Recursos offline documentados e testados | **Atingido** | Matriz em `#/sobre` (funciona offline / apenas online / exige servidor); 84 arquivos pré-armazenados incluindo Three.js e KaTeX |
| Nenhum erro grave de acessibilidade conhecido nos fluxos principais | **Atingido na auditoria automática** | `a11y-keyboard`: **0 violações** em 10 rotas × 2 temas (738 controles, 2 194 nós de texto); teclado: pular para o conteúdo, paleta, terminal, viewer |

Ressalvas da Etapa 7:
- A auditoria é **própria** (`tests/helpers/a11yAudit.ts`, 12 regras WCAG 2.2). **Não** é axe-core e **não** produz nota Lighthouse (D-19). A meta “Lighthouse ≥ 95” não foi medida.
- **Inspeção manual com leitor de tela (7.15) não foi feita** — precisa de uma pessoa com NVDA/VoiceOver (D-20).
- O teste de 360 px usa emulação de celular no Chromium, não um aparelho real.

Correções feitas durante a verificação: foco visível em campo de data; alvos de toque ≥ 24 px; hierarquia de títulos nos exercícios; transbordamento horizontal da ABP em 360 px; selo demonstrativo com texto acessível (não só `title`).
