# Rodada R1 — Relatório consolidado do Supervisor

Pedido: documento do usuário de 12/11/2026 (8 seções) — evolução científica, funcional e visual do CrystaLab
e do módulo HEA. Período: 12 e 13/11/2026. Interrupções por limite de uso da API: 5 (nenhuma por erro de execução).

Artefatos desta rodada: `2026-11-12_rodada_R1_plano_e_linha_de_base.md`, `2026-11-12_rodada_R1_progresso.md`
(estado), `2026-11-12_auditoria_hea.md`, `2026-11-12_parecer_cristalografia.md`,
`2026-11-13_parecer_termodinamica.md`, `2026-11-12_backend_BE-01.md`, `2026-11-13_backend_BE-02.md`,
`2026-11-12_frontend_FE-01.md`, `docs/architecture/2026-11-12_{decisoes_G1_R1,contrato_R1,aprovacao_contrato_R1}.md`,
`docs/research/2026-11-13_{relatorio_bibliografico.md,entalpias_binarias_candidatas.json}`.

## 1. Matriz de requisitos por seção do pedido

Estados: **verificado** (implementado e demonstrado por teste executado) · **implementado, não verificado
visualmente** · **parcial** · **pendente** · **fora de escopo com justificativa**.

### Seção 1 — Coordenação e diagnóstico

| Requisito | Estado | Evidência |
|---|---|---|
| Examinar arquitetura, dados, cálculos e fluxos antes de alterar | verificado | Linha de base em `..._plano_e_linha_de_base.md` §2-3: commit `93755eb`, 41 arquivos modificados preservados, suítes medidas, 15 achados iniciais reproduzidos pelo Supervisor via TestClient |
| Classificar cada solicitação em atendida/parcial/falha | verificado | Esta matriz; auditoria HEA §1.1 (22 achados); parecer de cristalografia §2.1 (13 achados) |
| Considerar atendido só após verificar funcionamento | verificado | Nenhum item marcado "verificado" sem teste executado; validação visual declarada NÃO feita (§5) |
| Preservar o que está correto | verificado | Auditoria HEA §1.2 e parecer §1.6/OK-1..OK-3 listam o preservado; motor HEA 1.0.0 × 2.0.0 comparado em 15 ligas × 2 políticas de dados: 0 diferenças em ΔS, δ, VEC, T_m |
| Registrar problemas, prioridades, dependências e aceite | verificado | Cartões de tarefa com dono único, arquivos permitidos e critérios; portões G0–G4 registrados |

### Seção 2 — Visualização 3D como elemento principal

| Requisito | Estado | Evidência |
|---|---|---|
| 3D ocupando toda a área útil | implementado, não verificado visualmente | `StageLayout.tsx`, `ViewerPanel.tsx`; spec `crystalab-layout.spec.ts` mede o retângulo do palco contra a janela |
| Uma única barra lateral recolhível | implementado, não verificado visualmente | `Sidebar.tsx` com as seis seções (Estrutura, Composição, Seleção de átomos, Propriedades, Aparência, Análise); `stores/crystalUi.ts` |
| Seções expansíveis, controles avançados sob demanda | implementado, não verificado visualmente | `Disclosure` com `testId`; seções fechadas por padrão |
| Rotação, zoom, deslocamento, centralização, restauração | implementado, não verificado visualmente | `cameraApi.ts` + `SceneController` (pan e enquadrar o conteúdo são novos; "centralizar" distinto de "restaurar"); botões no HUD e atalhos de teclado |
| Célula unitária × supercélulas | já atendido antes, preservado | seletor movido para a seção Estrutura |
| Eixos, parâmetros de rede, limites, legenda | implementado, não verificado visualmente | seção Aparência + HUD; os valores vêm do motor |
| Tamanho, transparência, visibilidade, representação dos átomos | **parcial** | representação (reduzido / esferas rígidas / bola-e-bastão / pontos), eixos, arestas, pontos de rede, rótulos e rotação prontos; **tamanho e transparência pendentes** (T-22) |
| Filtros, cortes, isolamento para alcançar átomos internos | **pendente** | hoje só o corte por plano de Miller, que já existia. T-23 |
| Seleção de qualquer átomo visível, inclusive após corte | **parcial** | funciona na célula do metal puro (preexistente, com teste de plano de corte); **não funciona na cena de ligas** (T-24) |
| Destaque inequívoco do átomo selecionado | já atendido antes | marcadores em `SceneController` |
| Inspeção: elemento, id, cartesianas, fracionárias, fase, sítio, ocupação | **parcial** | o backend passou a devolver todos esses campos por átomo (R1-BE-02, achado L-3); o inspetor do front ainda não os consome (T-25) |
| Não apresentar propriedade do elemento puro como propriedade do átomo na liga | verificado (backend) | R1-BE-02 separou as propriedades de elemento puro em bloco próprio `elementos` |
| Menu de aparência: cores por elemento, grupo e átomo; vértices e arestas; restaurar padrão | **pendente** | T-22 (era também a pendência antiga T-14) |

### Seção 3 — Estruturas cristalinas e representação de ligas

| Requisito | Estado | Evidência |
|---|---|---|
| Validar CS, CCC, CFC | **verificado** | `backend/tests/unit/engines/test_validacao_estruturas.py` (64 testes): NC por contagem de vizinhos, n, a(R), FEA, periodicidade, Wyckoff. Parecer §1.6: validados |
| Validar HC, explicitando célula, base e c/a ideal × real | **verificado, com correção** | Parecer §1.3 e §1.4. Falha E-1: o FEA do HC era fisicamente impossível (Mg 0,7446; Ti 0,7618 acima do limite π/(3√2) = 0,7405, isto é, esferas interpenetradas). Corrigido: R_c = ½·mín(a, distância entre planos); Mg 0,7364, Ti 0,7201, Co 0,7360; invariante FEA ≤ 0,7405 testado para c/a ∈ [1,0; 2,5] |
| Ligas multicomponentes (Fe, Cr, C identificáveis) | **verificado (backend)** | `solutos` com até 6 itens; caso R6 do parecer: Fe 47 / Cr 7 / C 1, a = 0,286823 nm, ρ = 7,8288 g/cm³. O front ainda é binário (T-25) |
| Distinguir substitucional × intersticial | verificado | campo `ocupacao` por átomo; sítios em `sitios.py` |
| Distinguir ordenada × desordenada | verificado | bloco `prototipo` (L1₂, L1₀, B2) com contagem por átomos únicos (25/50/75 at% exatos) |
| Distinguir monofásica × multifásica | **fora de escopo com justificativa** | não há dados de diagrama de fases no repositório. A API devolve `fases` com `fracao: null` e `verificacoes` dizendo que fases secundárias não são previstas. Nada inventado |
| Distinguir idealizado × experimental/calculado | verificado | `modelo` com `parametro_rede_solvente` e rótulos de natureza (§3.6 do parecer) |
| Não atribuir posição exata pela composição global; realização estatística com composição solicitada, representada, nº de átomos e semente | **verificado** | Falhas L-1 e L-5 (críticas) corrigidas: o sorteio passou a ser sobre os átomos ÚNICOS da supercélula periódica; imagens de fronteira são marcadas (`imagem`, `imagem_de`), herdam o elemento da origem e nunca entram em contagem ou composição. Antes: Fe–Cr 12 %, n=2 dava 4/31 sobre 35 esferas desenhadas; agora 2/14 sobre 16 átomos únicos |
| Intersticiais em sítios compatíveis | verificado | octaédricos e tetraédricos por rede, com multiplicidade, NC ("2 + 4" na CCC) e raio livre calculado com o c/a real; sítio padrão com `padrao_verificado: false` |
| Não supor todo o carbono dissolvido; considerar fases secundárias | verificado (como aviso) | `verificacoes`: limite de solubilidade não verificado, fases secundárias não previstas; avisos em `procedencia.avisos` |
| Não apresentar animação como dinâmica molecular | **parcial** | selos "Ilustrativo" presentes e agora dentro do palco (R1-FE-01); **a animação α→γ continua sem selo** (T-27) |

### Seção 4 — Auditoria e recuperação do HEA

| Item do pedido | Estado | Evidência |
|---|---|---|
| (a) Entrada e validação de composições | **verificado** | A-02, A-03, A-08, A-09, A-10 corrigidos; 25 entradas hostis testadas em dev e em produção, nenhum 500 |
| (b) Conversão atômica ↔ mássica | **verificado (15 metais)** | `base` = atomica/massica; saída nas duas bases; ida e volta com erro ≤ 5,6e-17. Limitada aos metais do repositório do motor (ADR-018 preservado) |
| (c) Normalização, unidades, limites | verificado | fração mínima, aviso de zeros descartados, tolerância 1e-9 nos limiares, limites 0 ≤ q ≤ 1e6 |
| (d) Fontes e disponibilidade de parâmetros | **parcial** | `dados_faltantes` e `criterios` com `fonte`; mas todos saem com `verificada: false` — a auditoria bibliográfica não conseguiu confirmar nenhum limiar no texto da fonte (Q-08, Q-09) |
| (e) Equações, hipóteses, algoritmos, tratamento de erros | verificado | auditoria §2; erros com `details[].type` |
| (f) Integração cálculo-gráfico-tabela-interface | **parcial (backend pronto)** | o motor devolve `curva_T`, `criterios`, `triagem`; o front ainda não consome (T-25) |
| (g) Persistência, atualização, exportação | **parcial** | o histórico de cálculo existe; **exportação do HEA não existe** (A-19) e há o risco Q-15 na chave estrangeira de `motores` |
| Reproduzir as falhas antes de corrigir | **verificado** | 22 achados com payload e saída real na auditoria §1.1 |
| Recuperar os gráficos de estabilidade e formação com dados rastreáveis | **parcial** | entregue o que não depende de dado externo: curva analítica −T·ΔS_mix (G-A) e δ × VEC (G-B). Os gráficos δ×ΔH e ΔG×T continuam indisponíveis: **sem a matriz de ΔH binário com fonte (Q-01) não há como desenhá-los sem inventar dado** |
| Diferenciar energia de formação, de mistura e de Gibbs | **verificado (documentado e no contrato)** | auditoria §2.5: quatro grandezas com unidade, referência, condições, significado e "o que não é"; `energia_formacao: null` com motivo (o sistema não a calcula) |
| Descritores empíricos como triagem, não prova de fase | **verificado** | `triagem.estado` ∈ {favoravel, desfavoravel, inconclusiva}; a palavra "ESTÁVEL" saiu do motor; `vec_aplicavel` restringe o critério de Guo ao seu domínio |
| Indisponível aparece como indisponível, com a causa | **verificado** | todo campo nulo tem chave em `indisponiveis`; o teste E2E C4 afirma grandeza + causa |

### Seção 5 — Termodinâmica e transformação de fases

| Requisito | Estado | Evidência |
|---|---|---|
| Análise integrada no escopo que os dados sustentam | **especificado, não implementado** | `2026-11-13_parecer_termodinamica.md`: matriz de 23 capacidades classificadas A (analítico hoje), B (bloqueado por Q-01), N (não sustentável sem CALPHAD), D (didático) |
| Documentar equações, convenções, validade | verificado | parecer §1–3 e §7 |
| Gibbs das fases, potenciais, minimização, frações de fase, diagramas | **fora de escopo com justificativa** | exige CALPHAD; nada existe no repositório (verificado: sem numpy, scipy ou pycalphad; sem base TDB). Classificados "N" |
| Entalpia e entropia de mistura | parcial | ΔS_mix ideal pronto; ΔH_mix bloqueado por Q-01 |
| Distinguir equilíbrio de cinética; TTT/CCT só com modelo próprio | **verificado como regra** | parecer §5: regra dura, nenhum eixo no tempo. Nada de cinética foi implementado |
| Verificar CALPHAD (existência, compatibilidade, cobertura, licença) | **verificado parcialmente** | não existe no repositório; opções listadas com tudo marcado "a verificar". Decisão do usuário: Q-11 |
| Sem dados, representação didática identificada ou explicar a limitação | verificado | enunciado honesto proposto (Q-12), com lista de termos proibidos |
| Parecer sobre o motor térmico existente | **verificado** | validado com ressalvas e 4 correções obrigatórias; **o bloco de alotropia foi REJEITADO para produção** (lido sem passar pela política de dados, sem procedência, com dados em rascunho) — T-26 |

### Seção 6 — Gráficos, tabelas e integração com o 3D

| Requisito | Estado | Evidência |
|---|---|---|
| Eixos, unidades, condições, legenda, fonte e natureza em todo gráfico | **parcial** | regras definidas (parecer §6) e o backend passou a enviar `criterios` com fonte e marca de verificação; **a aplicação no front é a T-25**; hoje `HeaCharts.tsx` ainda rotula "zona estável" com faixa sem fonte |
| Energia livre × T e composição; frações de fase × T; diagramas | **fora de escopo com justificativa** | ver seção 5 |
| Sincronização gráfico-tabela-3D | **pendente** | T-25 |
| Explicar que a distribuição atômica é representativa | verificado (backend) | aviso obrigatório em `procedencia.avisos` |

### Seção 7 — Referências e rastreabilidade

| Requisito | Estado | Evidência |
|---|---|---|
| Verificar as 11 obras fornecidas antes de citá-las como verificadas | **verificado (com resultado parcial)** | `docs/research/2026-11-13_relatorio_bibliografico.md`: 7 com metadados confirmados (com divergências: coautores omitidos em Gaskell, Callister, Cullity e Porter), **4 não localizadas** (Reed-Hill em português, Padilha "Metalurgia Física", Ávila & Becker, Chvátal) — Q-10 |
| Não inventar páginas ou trechos | **verificado** | nenhuma página foi confirmada; recomendação de remover ou marcar as citações "CAL9 p. 75" e "ASK6 p. 72" (Q-09) |
| Relatório numerado, fornecidas × adicionais | verificado | seções 1 e 2 do relatório bibliográfico; matriz afirmação-fonte com 34 linhas |
| Rastreabilidade das afirmações | **resultado grave, registrado** | das 32 afirmações citadas em código, **só uma está sustentada e verificada**: R = 8,314462618 J/(mol·K) (NIST). Alerta de integridade: a revisão Heliyon 10(22):e39660 está RETRATADA e não deve ser citada |

### Seção 8 — Validação e entrega

| Requisito | Estado | Evidência |
|---|---|---|
| Casos de referência com tolerância justificada | verificado | R1–R17 do parecer de cristalografia e T-01..T-21 da auditoria HEA, implementados como testes |
| Conservação de massa, normalização, unidades, periodicidade | verificado | ida e volta at↔massa; composição representada = átomos únicos; invariante de periodicidade testado |
| Fluxos completos | **parcial** | backend coberto por teste; os fluxos de tela dependem de T-25 e da conferência visual |
| Desempenho da cena com supercélulas | **não verificado** | existe `perf-metrics.spec.ts` (passa), mas nenhuma medição nova foi feita com o layout em área total |
| Entregáveis (matriz, auditoria, modelos, evidências, bibliografia, pendências) | verificado | este documento e os artefatos do cabeçalho |

## 2. Falhas do HEA: causa e correção

| ID | Falha (reproduzida) | Causa-raiz | Correção |
|---|---|---|---|
| A-01 | `dH` e `omega` nulos e `gibbs` vazio sem motivo; os dois gráficos nunca apareciam | o motor só preenchia motivo para dH e omega | todo campo nulo tem chave em `indisponiveis`; `pares_faltantes` e `dados_faltantes`; curva −T·ΔS_mix sempre presente |
| A-02 | elemento inexistente aceito com 200 (`{"Xx":1,"Fe":1}` calculava ΔS) | o símbolo nunca era conferido contra uma lista | conferência contra os 118 símbolos; `Xx`, `""`, `Fe2O3` → 400 |
| A-03 | `{"fe":1,"Fe":1,"Ni":1}` virava três elementos | só `strip()`; duplicata sensível a caixa | forma canônica; duplicata → 400 `elemento_repetido` |
| A-07 | critério de VEC aplicado fora do domínio (Al+Mg → "CCC"; Fe 99,9 % + Ni 0,1 % → "CFC") | nenhum teste de aplicabilidade | `vec_aplicavel`; fora do domínio não há `estrutura_sugerida`, com aviso que declara a regra como conservadora e sem fonte |
| A-08 | HTTP 500 com `{"Fe":1e308,"Ni":1e308}` | a soma estourava e caía em `log(0)` | limite 0 ≤ q ≤ 1e6 e `math.fsum`; passa a 400 |
| A-09 | quantidade `"1"` ou `true` aceita | coerção frouxa | número JSON estrito → 422 |
| A-04 | sem % em massa na entrada nem na saída | ausente | `base` atomica/massica e saída nas duas bases |
| A-06, A-15, A-17 | interface tratava todo veredito como risco; zona do gráfico sem fonte fixa no front; demo com "ESTÁVEL" sorteado | frontend | **pendentes (T-25, Q-14)**; o motor já não emite "ESTÁVEL" |
| A-10 a A-22 | códigos de erro, arredondamento, vocabulário de previsão, tolerância de limiar, mensagens | diversos | corrigidos no motor 2.0.0 (ver `2026-11-12_backend_BE-01.md`) |
| A-05 | cobertura de 15 metais; Mn ausente (liga de Cantor sem δ, T_m e VEC) | seed | **pendente**: ampliar depende de decidir ADR-018/C-02 e do validador (Q-03) |

## 3. Testes — resultado real

| Suíte | Antes | Depois |
|---|---|---|
| Backend `pytest` | 401 aprovados, 42 pulados, 0 falhas | **772 aprovados, 42 pulados, 0 falhas** (+371; reexecutado pelo Supervisor) |
| Contrato front-back | 46/46 | **46/46 aceitos** (`tests/contract`, executado) |
| Frontend `typecheck` | sem erros | sem erros |
| Frontend `lint` | ok (115 TS/TSX) | ok (120 TS/TSX) |
| Frontend `npm test` | 83 aprovados, 0 falhas | 83 aprovados, 0 falhas |
| Frontend `build` | inicial 693,1 kB (215,8 kB gzip) | inicial 712,8 kB (220,5 kB gzip) |
| Frontend `npm run e2e` | 60 aprovados, 1 falha preexistente (B3) | ver §3.1 |

### 3.1 E2E — leitura honesta

A E2E roda contra `dist/`: medir sem `npm run build` imediatamente antes NÃO vale (achado desta rodada).
Ela também derruba workers (`code=3221225794`) quando a máquina está carregada. Medições válidas: linha de
base 60 aprovados / 1 falha; após a R1-FE-01, 63/3 (as 3 de uma única causa, corrigida); após o fechamento,
64–65 aprovados com 1–2 falhas. A falha determinística restante é `alloy-thermal.spec.ts:46` e é
**consequência intencional da correção L-5/V-10**: Fe–C 2 at% em supercélula 2×2×2 dá
⌊16·x/(1−x) + ½⌋ = 0 intersticiais (antes havia um mínimo forçado de 1, que falsificava a composição).
O teste espera ver carbono na cena. Pendência T-21. `flow-a-density.spec.ts:41` (A2) falha na suíte completa
e passa isolada: instabilidade, T-29.

## 4. Agentes efetivamente acionados

| Agente | Tarefa | Resultado |
|---|---|---|
| hea-specialist | R1-HEA-01 | concluída na 2ª tentativa (1ª cortada por 429): 22 achados + especificação G1 |
| crystallography-engineer | R1-CRI-01 | parecer completo e 64 testes gravados; handoff perdido por 429, artefatos conferidos pelo Supervisor |
| api-architect | R1-API-01 | contrato R1 (aprovado com ressalvas) |
| backend-engineer | R1-BE-01 | motor HEA 2.0.0 |
| backend-engineer | R1-BE-02 | motor de cristalografia 2.1.0: FEA do HC, ligas periódicas e multicomponentes |
| frontend-engineer | R1-FE-01 + fechamento | palco em área total, barra lateral única, HUD, câmera |
| frontend-engineer | R1-FE-04 | asserção E2E C4 alinhada ao texto novo do motor |
| materials-science-specialist | R1-MAT-01 | parecer de termodinâmica (2ª tentativa) |
| academic-research-auditor | R1-BIB-01 | relatório bibliográfico (parcial: extração de ΔH bloqueada) |

Delegações que falharam: 5 interrupções por limite de uso (429) — R1-HEA-01, R1-CRI-01, R1-MAT-01, R1-BIB-01
e R1-FE-01 na primeira tentativa; a R1-CRI-01 perdeu o handoff, mas não o trabalho. **Não acionados:**
database-engineer, devsecops-engineer, adversarial-qa-tester, integration-engineer, pedagogical-engineer,
learning-analytics, machine-learning-engineer. QA adversarial e integração formal (G3/G4 completos) NÃO
foram executados.

## 5. O que NÃO foi verificado

- **Validação visual no navegador**: nenhuma. Nenhum agente abriu navegador para julgar aparência.
- **Desempenho da cena com supercélulas** no layout novo: não medido.
- **Fontes bibliográficas**: nenhum limiar científico confirmado no texto da fonte.
- **Produção**: o comportamento estrito foi exercitado só por teste; nenhum ambiente de produção foi usado.
- **Banco existente**: a chave estrangeira de `motores` com as versões novas (Q-15) não foi testada em banco
  já carregado.
- **QA adversarial independente** e integração formal.

## 6. Decisões de arquitetura tomadas nesta rodada

Em `docs/architecture/2026-11-12_decisoes_G1_R1.md` e `..._aprovacao_contrato_R1.md`. As principais:
ADR-018 preservado (o motor HEA usa a tabela periódica só como identidade, não como fonte de propriedade);
multifásico não implementado por falta de dados; nenhum valor de entalpia binária cadastrado; mudanças de
contrato aditivas, com as mudanças de valor V-1 a V-16 registradas e cobertas por teste de regressão.


---

# Adendo da rodada R2 (15/11/2026) — atualização da matriz

A rodada R2 fechou os itens que a R1 deixou como "parcial" ou "pendente". Estado das suítes no encerramento:
backend **864 aprovados / 51 pulados / 0 falhas**; contrato **46/46**; frontend typecheck e lint limpos (132 TS/TSX);
`npm test` **107 aprovados / 0 falhas**; build 813,5 kB (249,5 kB gzip, meta < 300 kB); E2E **74 aprovados / 0 falhas**.
Detalhe por entrega em `2026-11-14_rodada_R2_estado.md`; integração em `2026-11-15_integracao_R2.md`.

## Seção 2 — Visualização 3D: itens que mudaram de estado

| Requisito | Estado na R1 | Estado agora | Evidência |
|---|---|---|---|
| Tamanho e transparência dos átomos | parcial | **verificado** | `AppearancePanel.tsx`, `features/viewer3d/appearance.ts`; escala 0,3×–2,5× e opacidade 20–100 %; teste prova que nenhum número muda |
| Filtros, cortes e isolamento para alcançar átomos internos | pendente | **verificado** | `features/viewer3d/visibility.ts`, `modules/crystalab/FilterPanel.tsx`; isolar por elemento, ocupação e sítio; corte por plano de eixo em três modos |
| Seleção de qualquer átomo visível, inclusive após corte | parcial | **verificado** | `SceneController.pickAlloyAt`; corte aplicado como visibilidade, então o átomo oculto não é sequer visto pelo raycasting; teste seleciona átomo que só ficou alcançável depois do corte |
| Inspeção: elemento, id, cartesianas, fracionárias, fase, sítio, ocupação | parcial | **verificado** | `modules/crystalab/AlloyAtomInspector.tsx` com os 11 campos da API; `wyckoff` aparece como não disponível, sem invenção |
| Menu de aparência: cores por elemento, grupo e átomo; vértices e arestas; restaurar padrão | pendente | **verificado** | precedência átomo > grupo > elemento resolvida num único lugar (`resolveAtomColor`), usada pelo desenho E pela legenda; restaurar por seção e geral |
| Marcadores geométricos distintos de átomos reais | não avaliado na R1 | **verificado** | distinção por acabamento, não por cor: átomo = esfera sólida iluminada; eixos = setas; pontos de rede, vértices e seleção = arame; Miller = translúcido tracejado |
| Legenda consistente | parcial | **verificado** | legenda usa a cor efetiva, diz o que a cor codifica e permanece correta após filtrar, isolar e cortar, com mais de dois elementos |

## Seção 3 — Estruturas e ligas

| Requisito | Estado na R1 | Estado agora | Evidência |
|---|---|---|---|
| Liga intersticial com supercélula pequena | defeito aberto (T-21) | **resolvido** | o motor estava certo (0 átomos é a amostragem honesta); a interface passou a dizer isso, explicar a causa e sugerir o menor tamanho que representa um átomo, com o número vindo de um novo pedido ao motor |
| Não apresentar animação como dinâmica molecular | parcial | **verificado** | a animação α→γ deixou de ser exceção: recebeu selo "Interpolação visual entre dois estados calculados", declarando que não é dinâmica molecular nem cinética |

## Seção 4 — HEA

| Requisito | Estado na R1 | Estado agora | Evidência |
|---|---|---|---|
| Integração cálculo-gráfico-tabela-interface | parcial (backend pronto) | **verificado** | o front consome `triagem.estado`, `criterios`, `curva_T`, as duas bases de composição, `dados_faltantes` e `pares_faltantes` |
| Gráficos de estabilidade e formação | parcial | **parcial, pelo motivo certo** | G-A (−T·ΔS_mix × T) e G-B (δ × VEC) implementados com eixos, unidades, condições, legenda, fonte e natureza; a zona "estável" fixa e sem fonte foi REMOVIDA. Os gráficos que dependem de ΔH_mix continuam indisponíveis com a causa: falta a matriz de entalpias binárias com fonte (Q-01) |
| Modo demonstrativo | risco aberto (A-17) | **verificado** | decisão Q-14 do usuário (manter com selo): selo junto de cada valor, gráfico e tabela demonstrativos, distinto do selo "Ilustrativo"; a demo não sorteia mais veredito e usa a estrutura de triagem do motor |

## Seção 5 — Termodinâmica

| Requisito | Estado na R1 | Estado agora | Evidência |
|---|---|---|---|
| Parecer sobre o motor térmico | validado com ressalvas | **ressalvas corrigidas** | motor térmico 2.0.0: parâmetro de rede nulo acima da fusão com motivo; alotropia só com procedência e sob a política de dados (antes afirmava "a fase estável é Fe-γ" sem rastro); T_f nominal não confundida com solidus/liquidus; isotropia declarada; domínio da curva limitado |
| Gibbs por fase, frações de fase, diagramas, cinética | fora de escopo | **continua fora de escopo** | exige CALPHAD, que não existe no repositório. Decisão Q-11 com o usuário |

## Seção 6 — Gráficos e integração com o 3D

| Requisito | Estado na R1 | Estado agora | Evidência |
|---|---|---|---|
| Eixos, unidades, condições, legenda, fonte e natureza | parcial | **verificado para os gráficos existentes** | limiares vêm da API com `verificada: false` e são rotulados como não verificados na fonte; nenhuma faixa científica fixa no código do front |
| Sincronização gráfico-tabela-3D | pendente | **parcial** | a seleção de átomo sincroniza cena, inspetor e seção da barra lateral; a sincronização gráfico→3D de condições termodinâmicas depende do que não é sustentável sem CALPHAD |

## Seção 8 — Validação

| Requisito | Estado | Evidência |
|---|---|---|
| Integração formal (G4) | **integrado com ressalvas** | `2026-11-15_integracao_R2.md`: todas as suítes reproduzidas, OpenAPI em sincronia byte a byte, 242 campos do zod com correspondência no OpenAPI, zero divergência de contrato |
| QA adversarial independente | **feito para backend/API** | `2026-11-15_qa_R2.md`: 6 defeitos, nenhum crítico; fuzz de 1269 requisições sem nenhum 500; 4 defeitos corrigidos |
| Robustez do caminho autenticado | **corrigida** | achado F-1 da integração: o cálculo autenticado caía com 500 em banco preexistente por FK de `motores`. Corrigido sem migração: gravação de histórico em savepoint (nunca derruba o resultado), registro idempotente do motor e `PRAGMA foreign_keys` imposto em SQLite |
| Desempenho com supercélulas, validação visual, PostgreSQL, Docker, acessibilidade real | **não verificado** | continua pendente (T-37) |
