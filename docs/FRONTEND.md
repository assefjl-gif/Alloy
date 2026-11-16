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

* Bundle inicial: **215,9 kB gzip** (meta < 300 kB), sem Three.js no carregamento inicial (medido por
  `npm run measure` e verificado em `foundation-regression.spec.ts`).
* Módulos, viewer e fontes sob demanda (29 arquivos, 13 deles fontes IBM Plex); service worker com pré-cache (101 arquivos) e funcionamento offline
  do que é local.

## 6. Mudanças da consolidação (Fase 5 em diante)

* Saíram o motor legado stdlib, o `engine-stub`, o `vendor/` e `scripts/link-deps.mjs`. Dependências via npm com lockfile.
* O cliente foi unificado em `apiBase` com rotas canônicas `/api/v1`. Os aliases `/v1` não são mais usados.
* `scripts/backend.mjs` sobe o FastAPI real para dev, testes e E2E (`--db` cria SQLite migrado).
* Portabilidade no Windows: caminhos com `/` no lint, no build e nos testes (BUG-01/BUG-02 da auditoria).
* HEA: contrato com grandezas anuláveis, painel de indisponíveis, gráficos e quiz protegidos contra `null`.
* Conta e questões do servidor (`#/conta`).

## 7. Ligas e temperatura (T-13)

Dois formulários do CrystaLab (`modules/crystalab/AlloyPanels.tsx`). Desde a R1-FE-01 eles vivem na barra lateral
única: **Liga** na seção *Composição* e **Temperatura** em *Análise → Temperatura*; os resultados aparecem em
*Propriedades → Resultados da liga* e junto ao formulário de temperatura (antes eram duas abas, com os resultados
abaixo do viewer). Nenhuma fórmula no cliente: rede, densidade, regras e vibração vêm de
`POST /crystallography/solid-solutions` e `POST /thermodynamics/thermal`.

| Formulário | O que faz | Viewer |
|---|---|---|
| **Liga** | base (padrão: o metal carregado), soluto (metal ou C, N, H), % atômica, supercélula n×n×n, arranjo aleatório/ordenado com semente, distorção ilustrativa. Mostra composição, *a*, densidade, contagem de átomos, as 4 regras de Hume-Rothery (atende / não atende / indisponível, com o motivo), conclusão do motor, sítio intersticial, passo a passo e procedência | desenha **um átomo por átomo devolvido pelo motor**, em cores acessíveis (base azul, soluto laranja) e legenda textual por papel |
| **Temperatura** | -200 a 2500 °C (recalcula ao soltar o controle, com cancelamento do pedido anterior); alvo = metal carregado ou liga formada. Mostra T/T_f, α, *a*(T), ΔV, densidade, amplitude *u*, a curva *u/d* × T com a linha de Lindemann e as observações do motor (inclui aviso de fusão) | botão **Vibrar átomos**: cada átomo oscila em torno da posição de rede com a amplitude do motor |

Pontos de integridade:
* A vibração é **ilustrativa**: osciladores independentes (modelo de Einstein simplificado), movimento determinístico (`displacement()`).
  O controle "exagero visual" multiplica a amplitude só para enxergar e está rotulado; 1× é a amplitude real do motor.
* Com **movimento reduzido** no sistema, a cena mostra um instante congelado, sem animar.
* O viewer só exibe a liga quando há resultado do servidor. Com a liga na tela, um aviso sobre a cena (`hud-alloy`) e a
  faixa da seção *Composição* lembram que os cartões de propriedades continuam descrevendo o metal carregado.
  Carregar outro metal invalida liga e temperatura.
* A vibração só é liberada depois de calcular a temperatura (sem amplitude do motor não há movimento).

Testes: `tests/unit/alloy.test.ts` (backend real + cena pura), `tests/e2e/alloy-thermal.spec.ts` (6 fluxos) e o contrato real
(`scripts/contrato_frontend.mts`, 46 casos).

## 8. CrystaLab: palco em área total e barra lateral única (R1-FE-01)

O CrystaLab não usa mais o `Workbench` de três colunas (painel esquerdo + coluna de resultados rolável + abas à
direita). Ele usa `design-system/layout/StageLayout.tsx` — os outros módulos continuam no `Workbench`.

* **Palco (`viewer-stage`)** ocupa toda a área entre o fim do cabeçalho da aplicação e a base da janela, e da borda
  da barra até a borda direita. A página não rola atrás da cena e o canvas é redimensionado junto
  (verificado em `tests/e2e/crystalab-layout.spec.ts`, L1).
* **Barra lateral única** (`modules/crystalab/Sidebar.tsx`), recolhível por um botão só (`sidebar-toggle`), com modo
  *Barra larga* para tabelas e passo a passo. Até 960 px (`NARROW_QUERY`) ela vira gaveta sobreposta: não empurra a
  cena e fecha com Esc ou tocando fora (L5).

### Seis seções da barra

| Seção | Conteúdo |
|---|---|
| **Estrutura** | resumo da célula (estrutura, material, n, NC, R, parâmetros de rede), célula unitária × supercélula, banco de materiais, modo guiado, editor de parâmetros e o botão *Desenhar* |
| **Composição** | faixa do resultado HEA transportado, faixa da liga e o formulário de liga |
| **Seleção de átomos** | inspetor do átomo escolhido na cena |
| **Propriedades** | resultados principais (faixa de estado + métricas), densidade (guiada + painel), resultados da liga, comparação entre estruturas, contagem de átomos, interpretação e procedência |
| **Aparência** | modo dos átomos, eixos, arestas, pontos de rede, rótulos, girar, legenda, a nota sobre poliedros e, em subseções, **Cores** (elemento, grupo, átomo), **Células: arestas e vértices**, **Átomos: tamanho e transparência**, **Marcadores geométricos**, **Filtros de exibição** e *Restaurar toda a aparência* |
| **Análise** | Miller (formulário, camadas, guia), gerenciador de camadas, medições, temperatura, animações, terminal e workspaces |

As seções usam `Disclosure` (h2/h3 com `aria-expanded`/`aria-controls`), são operáveis por teclado (Enter e Espaço) e
o estado aberto/fechado fica em `stores/crystalUi.ts`, persistido em `localStorage`. O essencial começa aberto
(`DEFAULT_OPEN`); o resto, recolhido (L2). `useAutoReveal()` abre a seção certa quando o estado muda por outro
caminho (clique na cena, terminal, paleta de comandos, ponte do HEA).

### HUD da cena

Sobreposto ao palco, sem reduzir a área da cena (`modules/crystalab/SceneHud.tsx`):

* título e subtítulo do resultado, botão *Ferramentas*, desfazer/refazer, compartilhar, anotar no caderno e menu de
  exportação;
* **avisos da cena** (`SceneNotices`) — renderizados **dentro** de `viewer-stage` (prop `overlay` de `SceneStage`):
  banner de medição, atalho para a composição quando a cena mostra liga ou resultado do HEA e o selo
  **Ilustrativo** (`demo-seal`) das animações didáticas e da coloração por elemento. Ficar dentro do palco é
  proposital: "o selo de ilustrativo é descendente da cena a que se refere" é uma asserção de honestidade
  verificada em `etapa3-viewer`, `etapas5-7` e `viewer-didactics`;
* **legenda** recolhível, coerente com o que está desenhado: parâmetros de rede como o motor os devolveu, papéis e
  cores da liga, sítios, eixos, arestas, pontos de rede, planos e direções (L4);
* **câmera** por botões: seletor *Girar*/*Deslocar* + quatro setas, aproximar, afastar, **centralizar**
  (`frame()`, enquadra o conteúdo mantendo a orientação) e **restaurar a vista inicial** (`view.reset`). No palco
  focado, pelo teclado: setas giram, Ctrl/Alt+setas deslocam (Shift = passo maior), `+`/`−` aproximam e afastam,
  `F` centraliza, `R`/`0`/`Home` restauram e Esc limpa a seleção (L3). A implementação é registrada pelo viewer em
  `features/viewer3d/cameraApi.ts` (módulo leve, sem Three.js) e exposta para teste em `window.__alloy.viewer`.

Teclas digitadas nos avisos sobrepostos não acionam a câmera: `SceneStage` só trata `onKeyDown` quando o alvo do
evento é o próprio palco.

## 9. Campos do contrato R1 no front (R2-FE-01, 14/11/2026)

Contrato: `docs/architecture/2026-11-12_contrato_R1.md` (aprovado em `..._aprovacao_contrato_R1.md`).
Motores: HEA **2.0.0** e cristalografia **2.1.0**. Tipos estáticos: `npm run types:api` →
`src/services/api/openapi.gen.ts`. Validação em tempo de execução: `src/services/api/contracts.ts`
(todos os esquemas afetados passaram a `.passthrough()`; `HeaBootstrap`, `AlloyAtom` e o sítio do
átomo descartavam os campos novos antes desta rodada).

### Regras que a interface segue

| Regra | Onde |
|---|---|
| Nenhuma grandeza científica é calculada no cliente | `modules/hea/display.ts` e `modules/crystalab/alloyDisplay.ts` só escolhem e ordenam o que a API enviou |
| Nenhum limiar ou faixa científica fixo no código | as faixas dos gráficos vêm de `criterios` (resposta) e `bootstrap.criterios`; a zona fixa "δ < 6,6 %, −15 < ΔH < 5 kJ/mol" que existia em `HeaCharts.tsx` foi REMOVIDA |
| Ausência nunca vira zero | campo nulo/ausente aparece como "indisponível" com o motivo de `indisponiveis` |
| Estabilidade não se lê em texto | o estado vem de `triagem.estado` (`favoravel`/`desfavoravel`/`inconclusiva`); estado desconhecido vira "não classificada pelo motor". O teste do prefixo "ESTÁVEL" saiu de `HeaModule.tsx` e de `handlers.ts` |
| Limiar sem fonte conferida é rotulado | `verificada: false` → selo "limiar não verificado na fonte" na tabela e `*` no gráfico (decisão D-h) |

### HEA (`modules/hea/`)

- **Triagem**: `triagem.estado` + `triagem.texto` (`data-testid="hea-triage"`), com os três avisos
  obrigatórios de `bootstrap.avisos_fixos` em "Limites desta análise".
- **Composição nas duas bases**: `comp_percent` (at.%) ao lado de `comp_massa_pct` (massa%), com
  `base_entrada`, `soma_informada` e `massa_molar_media`. Sem base mássica utilizável, a coluna diz
  indisponível e mostra o motivo da API (em produção as massas estão `aguardando_validacao`).
- **Dados que faltaram**: `dados_faltantes` (elemento ou par, com código e situação) e
  `pares_faltantes`, junto dos `indisponiveis`.
- **Critérios** (`data-testid="hea-criteria"`): `criterios` da resposta — grandeza, operador,
  limiar, unidade, valor da liga, situação (atende / não atende / não avaliado / fora do domínio),
  `proximo_do_limiar`, natureza e fonte. Substituiu a "comparação com a liga de referência", que
  subtraía limiares do valor calculado; `bootstrap.reference` deixou de ser exibido (obsoleto).
- **Métricas novas**: `dS_R` com `classe_entropia` e `raio_medio_nm`; `vec_aplicavel: false` avisa
  que o critério de VEC está fora do domínio.
- **Gráficos** (`HeaCharts.tsx`), cada um com eixos, unidades, condições, legenda, FONTE e NATUREZA:
  - **G-A** `temperature-chart`: −T·ΔS_mix × T de `curva_T`; a curva de ΔG_mix só é desenhada quando
    o motor tem valor em TODOS os pontos — hoje não tem, e o gráfico diz isso com a causa
    (`ga-gibbs-unavailable`). `guias_entropia` do bootstrap ficou de fora: usá-las exigiria calcular
    −T·ΔS no cliente.
  - **G-B** `delta-vec-chart`: δ × VEC, com os limiares de `criterios` desenhados e identificados.
  - `gibbs` (J/mol) continua no contrato, marcado obsoleto; o front deixou de desenhá-lo.

### Ligas (`modules/crystalab/AlloyDetails.tsx`, `alloyDisplay.ts`, `features/viewer3d/alloyScene.ts`)

- **Contagem**: `composicao.n_atomos_unicos` (átomos únicos) × `composicao.n_desenhados` (esferas,
  inclui imagens periódicas). `n_soluto`/`n_solvente` contam ÚNICOS desde V-8 do contrato; a tela
  deixou de somar `atomos.length` com eles.
- **Imagem periódica** (`imagem`, `imagem_de`): nunca entra em contagem, composição, massa ou
  legenda — `uniqueAtoms()` é a base de qualquer contagem feita na interface.
- **Composição pedida × representada**, nas duas bases, com átomos por elemento, resolução
  (`resolucao_at_pct`) e desvio máximo.
- **Realização** (`realizacao`): semente, algoritmo e o aviso de que é UMA realização estatística,
  não a posição real dos átomos.
- **Modelo** (`modelo`): o que é idealizado e o que é parâmetro medido (`parametro_rede_solvente`,
  `c_a`), com as hipóteses; `prototipo` quando o arranjo é ordenado.
- **O que o motor não verifica** (`verificacoes`): limite de solubilidade e fases secundárias.
- **Fases** (`fases`): a matriz imposta, com `fracao` nula e o motivo.
- **Regras por soluto** (`regras_por_soluto`) e `conclusao_global`; com mais de um soluto não há
  conclusão única e o motivo da API é exibido.
- **Sítios** (`sitios`): tipo, `nc_txt`, sítios por célula, escolha, justificativa e o aviso de
  `padrao_verificado: false`. **Elementos puros** (`elementos`): dado TABELADO, com estado e fonte.
- **Convenções** (`convencoes`): em HC ficam visíveis sem abrir nada, porque dizem qual célula está
  na tela (a primitiva hexagonal replicada) e onde está a origem em relação ao CIF.
- **Legenda** com até 7 elementos (solvente + 6 solutos), uma cor por elemento
  (`ALLOY_PALETTE`), papel e átomos únicos.

### Células (`modules/crystalab/Results.tsx`)

- `ContactPanel` (`data-testid="contact-panel"`): `fea_modelo` (o FEA é do modelo de esferas
  rígidas, não empacotamento medido), `raio_contato_rel` (QUAL raio entrou no FEA — decisivo porque
  para o Ti coexistem valores diferentes), `contato_tipo`, `c_a_ideal`, `c_a_natureza` e `vizinhos`
  (6 basais + 6 entre planos, com d em unidades de `a` e em nm).
- `nc_txt` aparece ao lado de `nc` quando difere ("12 (6 + 6)" no HC fora do ideal).
- O c/a ideal e a nota do HC passaram a vir de `c_a_ideal`/`contato_tipo`: o valor 1,633 não está
  mais escrito na interface nem no catálogo de mensagens.

## 10. Rotulagem honesta (R2-FE-02, 15/11/2026)

Decisões implementadas: `docs/architecture/2026-11-14_decisoes_R2.md` (D-R2-2, D-R2-3, D-R2-4).

### Dois selos, dois significados (`design-system/primitives/Category.tsx`)

`DemoSeal` tem duas variantes, com texto, ícone, cor e estilo de borda diferentes (nunca só cor);
o `data-testid` continua `demo-seal` nas duas e `data-seal` diz qual é:

| Variante | Significado | Aparência |
|---|---|---|
| `demo` (padrão) | número **fictício**, sem dado e sem motor (`heaDemo.ts`) | âmbar, borda cheia, ícone `demo` |
| `illustrative` | representação **sem pretensão preditiva sobre dado real** do motor | neutra, borda tracejada, ícone `eye` |

Estilos em `styles/app.css` (`.ds-demo-seal--illustrative`). Desde R2-FE-04 todos os selos de
conteúdo ilustrativo usam a variante: explicação das animações de empilhamento e térmica
(`SidePanels.tsx`), coloração ilustrativa do HEA (`ProvenancePanel.tsx`) e o passo intermediário da
α→γ. No explicador da α→γ a **tabela** continua `result` (são dois resultados reais do motor) e só a
linha do passo intermediário ("misturando 40%") recebe selo ilustrativo, porque ela descreve a
interpolação visual, não um estado físico.

### Animação α→γ com selo (D-R2-4)

`SceneHud.tsx` não exclui mais `alpha-gamma` do selo. Como a animação interpola entre **dois
resultados reais** do motor (α-Fe CCC e γ-Fe CFC), o selo é `illustrative` com o texto
"Interpolação visual" e o detalhe `anim.ag.sealDetail`: não é dinâmica molecular, não é cinética de
transformação e não representa o caminho real da transformação.

### Modo demonstrativo do HEA mantido, com selo (D-R2-2)

- `services/adapters/heaDemo.ts` deixou de sortear veredito. Emite `triagem` na forma do contrato
  (R1 §1.2) com `estado: 'inconclusiva'` e texto "TRIAGEM NÃO REALIZADA (modo demonstrativo)…", e
  `veredito` repete esse texto (achado A-17: a demo não pode sugerir estabilidade). A procedência é
  declarada: `classe: 'demonstrativo'`, sem motor e sem fontes.
- O selo acompanha o próprio dado, não só o aviso do topo: cada `MetricCard` (`hint`), a triagem, a
  fase, as tabelas de critérios e de composição, os dois gráficos (e as tabelas de dados dentro
  deles) e a lista de ligas de demonstração. Testes: `tests/e2e/flow-c-hea.spec.ts` (C1b) e
  `tests/unit/core.test.ts`.

### Soluto não representado na supercélula (D-R2-3 / T-21)

Quando a realização estatística do motor não comporta nenhum átomo do soluto (`n_atomos === 0` em
`composicao.representada`), a interface diz isso em três lugares — banner da composição, nota nos
resultados da liga e aviso acionável junto do seletor de tamanho (`alloy-absent-solute`) — explica a
causa (a quantidade pedida corresponde a menos de meio átomo nesta supercélula) e mostra a
resolução de composição informada pela API (`resolucao_at_pct`).

O tamanho sugerido **não é calculado no cliente**: `AbsentSoluteNotice` repete o pedido ao motor
(`POST /api/v1/crystallography/solid-solutions`) com a mesma composição e supercélulas maiores
(1..4, o limite do motor) e mostra o primeiro tamanho cuja RESPOSTA traz ao menos um átomo do
soluto, com a contagem que veio do motor. Nenhum átomo é inventado para a cena parecer completa.
Detecção em `alloyDisplay.ts` (`absentSolutes`, `representedAtomsOf`): só leitura de contagens da API.

## 11. Seleção de átomo na liga e filtros de exibição (R2-FE-03, 15/11/2026)

### Seleção e inspeção na cena de liga (T-24)

A cena de liga é montada por `features/viewer3d/alloyScene.ts` (`sceneFromAlloy`) e desenhada por
`SceneController.setThermalScene` em `thermalGroup`, com um `InstancedMesh` por `elemento|tipo`.
Essas malhas não entram em `this.batches` (usado pela célula do metal puro), então ganharam
raycasting próprio: `pickAlloyAt()` percorre as malhas do `thermalGroup` e devolve o **`id` do
motor** da instância atingida; `pickTargetAt()` escolhe a cena certa e `Viewer3D` grava
`useViewer.alloySelection: string | null`. A identidade nunca é inventada: é `atomos[].id` da
resposta (`r:0.0.0:3`, `i:oct:1.0.1:2`, imagem `…+x`); sem `id` (motor anterior) cai no índice da
lista desenhada.

`modules/crystalab/AlloyAtomInspector.tsx` mostra, só com campos da API: `elemento`, `id`, `pos`
(unidades de a), `pos_nm`, `frac`, `frac_celula`, `celula`, `fase`, `sitio.nome`, `sitio.wyckoff`,
`sitio.nc_txt`, `ocupacao`, `pos_ideal`, `imagem` e `imagem_de`. Campo ausente aparece como
indisponível — `wyckoff` vem `null` de propósito e a tela diz "não disponível — o motor não
confirmou o símbolo em fonte". Imagem periódica leva selo, a nota de que não entra em contagem,
composição nem legenda, e um botão que seleciona o átomo de origem. Raio e massa do elemento ficam
num bloco à parte, rotulado **propriedades do ELEMENTO PURO**, com `estado_do_dado` e `fonte` do
motor. A lista navegável por teclado (`role="listbox"`, setas, Home, End, Esc) existe também na
liga e lista apenas os átomos desenhados.

### Filtros, cortes e isolamento (T-23)

Estado em `stores/sceneFilter.ts`, três dimensões independentes como o motor as informa — elemento
(`elemento`), ocupação (`ocupacao`) e sítio (`sitio.nome`; na célula do metal puro, o `tipo` do
sítio) — mais corte e vizinhança, com `clear()`. "Isolar X" é expresso como "ocultar todos os
outros valores daquela dimensão", de modo que isolar e ocultar compartilham o mesmo estado. Nenhuma
lista de valores está fixada no código: elas vêm da resposta.

A decisão de visibilidade vive em `features/viewer3d/visibility.ts` (puro, sem Three.js, testável
em Node) e a ponte com os stores em `features/viewer3d/sceneFilterState.ts`. Controles em
`modules/crystalab/FilterPanel.tsx`, na seção **Aparência** (`appearance.filters`), porque mudam só
o que aparece; a seção Análise reúne o que produz resultado do motor.

**Mecanismo de corte escolhido:** plano de corte ao longo de um eixo (x, y ou z), com posição em
unidades de a e três modos — fica o lado de baixo, o de cima, ou só uma fatia de espessura
escolhida. A faixa dos controles vem das coordenadas que o motor devolveu (`axisRange`), não de
limites fixos. O corte é aplicado como **visibilidade de átomo**, e não como `clippingPlane` do
Three.js: o átomo escondido sai da malha instanciada, logo deixa de ser alcançável pelo raycasting
por construção (requisito duro: escondido não é selecionável, revelado é), não aparecem
meias-esferas e a regra fica testável sem WebGL. O plano de Miller continua usando
`clippingPlanes` na célula do metal puro; ele nunca se aplicou à cena de liga e continua sem se
aplicar.

Filtrar e cortar **não alteram nenhum valor científico**. O painel, a legenda da cena e o inspetor
mostram a contagem de EXIBIÇÃO rotulada como tal e, ao lado, a contagem do motor
(`composicao.n_atomos_unicos` e `n_desenhados`), que não muda. O enquadramento da câmera usa todos
os átomos da cena, visíveis ou não, para o corte não mudar escala nem centro.

### Menu de aparência (T-22)

Estado em `stores/appearance.ts` (persistido em `localStorage`, como o resto do estado de
interface); as regras puras ficam em `features/viewer3d/appearance.ts` (sem Three.js e sem React,
testável em Node). Controles em `modules/crystalab/AppearancePanel.tsx`, dentro da seção
**Aparência**, junto da representação e dos filtros — um lugar só, sem controle duplicado.

O que é configurável:

| Escolha | Onde se aplica | Observação |
|---|---|---|
| cor por **elemento** | liga e metal puro | a legenda passa a usar a cor escolhida |
| cor por **grupo** | ocupação do motor (`ocupacao`: solvente, substitucional, intersticial) e, na célula do metal puro, o tipo de sítio | vence a cor do elemento |
| cor por **átomo** | átomo selecionado (identidade `id` do motor; na célula, a chave `índice@célula`) | vence grupo e elemento |
| cor das **arestas** e dos **vértices** | célula e supercélula (também na caixa da cena de liga) | vértice é marcador, ver abaixo |
| **tamanho** (escala 0,3× a 2,5×) e **opacidade** (20 % a 100 %) | átomos desenhados | escala de desenho; o raio do motor não muda |
| **restaurar o padrão** | por seção e geral (`appearance-reset-*`) | volta a `DEFAULT_APPEARANCE` |

**Agrupamento escolhido para "cor por grupo":** a **ocupação que o motor devolve por átomo**
(`ocupacao`) e, quando ela não existe (célula do metal puro), o **tipo de sítio**. Os dois são
campos da própria resposta, já usados pelos filtros de exibição (T-23) e pela legenda da célula:
o front não inventa categoria nem deduz papel a partir de número, e o vocabulário da tela é o mesmo
em aparência, filtro e legenda.

**Precedência** átomo > grupo > elemento > padrão da cena, resolvida em um lugar só
(`resolveAtomColor`) e usada tanto pelo desenho quanto pela legenda — por isso as duas não divergem,
inclusive depois de filtrar, isolar ou cortar, e com mais de dois elementos.

**Marcador geométrico × átomo real** (requisito explícito): o átomo é sempre esfera **sólida
iluminada**; os marcadores nunca são. Eixos são setas com rótulo; pontos de rede, octaedro em
**arame**; vértices da célula, cubo em **arame**; marcador de seleção, esfera em **arame**;
planos e direções de Miller, superfície translúcida com contorno **tracejado**. Nenhum marcador usa
cor de elemento, e a legenda os lista sob "Marcadores geométricos (não são átomos)". A distinção,
portanto, não depende de cor (acessibilidade: cor nunca é o único código).

**Aparência não é dado:** nada aqui altera valor, contagem ou composição — o que a cor codifica
está escrito na legenda (`legend-color-means`), junto da frase "escolha de exibição: não altera
dado", e a cor sempre vem acompanhada de rótulo em texto e do valor hexadecimal escrito.
Telemetria para teste: `window.__alloy.viewer.appearance()`.

### Política de demonstração do servidor (`demo_permitido`)

`GET /api/v1/meta/capabilities` informa `demo_permitido` por serviço e, em produção, a demonstração
é proibida. `services/api/hea.ts` lê o campo (`detectDemoPolicy`) junto da detecção do serviço e o
guarda em `HeaCapabilities.demoAllowed`; `stores/capabilities.ts` o aplica em `serviceMode`
(`effectivePolicy`): servidor com `false` desliga a política, de modo que o serviço indisponível
fica **`disabled`**, nunca `demo` — mesmo que a preferência local ou `public/config.js` peçam
demonstração. `demoAllowed: null` (servidor não respondeu) não é lido como autorização nem como
proibição: vale a política local, porque não há decisão do servidor a respeitar. A mesma regra
desliga a coloração ilustrativa do HEA em `ProvenancePanel.tsx`.
