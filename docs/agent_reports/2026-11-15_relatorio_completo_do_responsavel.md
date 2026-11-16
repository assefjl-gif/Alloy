# Relatório completo — rodadas R1 e R2 (12 a 15/11/2026)

Pedido de origem: `prompt aperfeiçoamento 12112026.txt` (8 seções).
Branch com o ponto de retorno: `integracao/r1-r2-2026-11-15`, commit `74e3181`. `main` intacta em `93755eb`.
Nada foi enviado ao remoto. Nada foi publicado. O portão G5 não foi atingido.

---

## 1. Estado verificado

Números que eu (a sessão principal) medi nesta árvore, em 15/11/2026, e os que vieram dos relatórios dos agentes.

| Suíte | Linha de base (12/11) | Agora | Fonte |
|---|---|---|---|
| Backend `pytest` | 401 aprovados, 42 pulados | 864 aprovados, 51 pulados, 0 falhas (exit 0) | medido por mim; contagem do relatório do supervisor |
| Contrato front↔back (`scripts/contrato_frontend.mts`) | — | 46/46 respostas aceitas | relatório do supervisor, reexecutado pela integração |
| Frontend `typecheck` | limpo | limpo | medido por mim |
| Frontend `npm test` | 83 aprovados | 107/107 | medido por mim |
| Frontend `build` | 693,1 kB (215,8 gzip) | 813,5 kB (249,5 gzip); meta < 300 kB gzip atendida | medido por mim |
| Frontend `npm run e2e` | 60 aprovados, 1 falha | 74/74 | medido por mim, com `build` imediatamente antes |

Observação honesta: no `pytest` a saída que vi foi só a barra de progresso sem o resumo final. O total de 864 aprovados e 51 pulados vem do relatório do supervisor e é consistente com a contagem de pontos na saída; o que medi diretamente foi exit 0 e nenhuma linha de falha.

O que **não** foi verificado: validação visual em navegador (ninguém fez), PostgreSQL (os 41–51 testes pulados dependem dele e esta máquina não tem), Docker/compose/CI, leitor de tela real, desempenho da cena com supercélulas no layout novo, e bancos preexistentes reais (o cenário de F-1 foi simulado).

---

## 2. Modificações feitas

### 2.1 Ciência (corrigida nos motores)

- **Motor cristalográfico 2.1.0 — FEA do hexagonal compacto (HC).** O valor estava fisicamente impossível: Mg 0,7446 e Ti 0,7618, acima do limite de esferas rígidas π/(3√2) = 0,7405, o que significa esferas interpenetradas. Agora: Mg 0,7364, Ti 0,7201, Co 0,7360, com invariante testado em toda a faixa de c/a. O raio de contato do HC passou a ser exibido no painel de primeiros vizinhos.
- **Amostragem das soluções sólidas.** O sorteio era feito sobre as esferas desenhadas, e imagens periódicas do mesmo átomo recebiam elementos diferentes. A unidade de amostragem passou a ser a supercélula periódica. Composição representada, número de átomos e semente são informados.
- **Intersticiais.** Fe–C a 2 at% em 2×2×2 dá 0 solutos (⌊16·x/(1−x)+½⌋ = 0); antes havia um mínimo forçado de 1 átomo que falsificava a composição. O teste antigo esperava o comportamento errado e foi reescrito para cobrir os dois casos.
- **Motor térmico 2.0.0.** Afirmava "a fase estável é Fe-γ" sem procedência, em produção; removido. Acima da temperatura de fusão do modelo, `fator`, `a_nm`, `delta_a_pct` e `delta_v_pct` voltam `null`, com a causa em `indisponiveis`. Não há mais zero silencioso.
- **Motor HEA 2.0.0.** Ver seção 3 (achados A-01 a A-22).

### 2.2 Backend e banco

- **F-1 (corrigido sem migração).** `ExecucaoCalculo` era inserido sem garantir a linha em `motores`. Com a FK aplicada e as versões novas, o cálculo autenticado inteiro dava HTTP 500 em banco preexistente. Correção: gravação do histórico isolada em savepoint (falha nunca derruba o resultado científico), registro idempotente do motor e aviso em `procedencia.avisos` (campo já contratado, sem campo novo). Um teste existente afirmava o próprio defeito (exigia `IntegrityError`) e foi reescrito.
- **F-2 (corrigido).** SQLite não habilitava `PRAGMA foreign_keys`, o que escondia o F-1 de todas as suítes. Passou a ser imposto. Não revelou outra violação.
- **Erros de API (QA-R2-02 a 06).** Procedência preenchida em `/cells` e `/density`; mensagem de erro em português sem vazar regex interna; `details[].loc` como caminho legível; truncamento do valor ecoado uniforme (16 caracteres).
- **Contrato OpenAPI.** `docs/openapi.json` reexportado; a integração confirmou que é idêntico byte a byte ao gerado e que os 242 campos do zod do front têm correspondência.

### 2.3 Frontend — CrystaLab

- Palco 3D em área total, com **uma** barra lateral recolhível de seis seções: estrutura, composição, seleção de átomos, propriedades, aparência, análise.
- Câmera: girar, zoom, pan, centralizar e restaurar (pan e centralizar são novos).
- Tamanho e transparência dos átomos; visibilidade por elemento, ocupação e sítio; corte por plano de eixo em três modos; isolamento para alcançar átomos internos.
- Seleção e inspeção de átomo na cena de **ligas**, com os campos do motor: id, coordenadas cartesianas em a e nm, fracionárias, fase, sítio, ocupação, imagem periódica.
- Propriedade de elemento puro em bloco separado e rotulado, para não ser lida como propriedade do átomo na liga.
- Menu de aparência: cor por elemento, grupo e átomo; cor de vértices e arestas; restaurar por seção e geral.
- Marcadores geométricos (sítios, vértices) distinguidos de átomos reais pelo acabamento: arame contra esfera sólida iluminada, não só pela cor.
- Legenda coerente depois de filtrar, isolar e cortar, com mais de dois elementos.
- Animação α→γ com selo "Interpolação visual".
- Gráficos de rede e dilatação: quando o valor é nulo, o cartão mostra a causa de `indisponiveis`, sem zero nem traço mudo. A curva de vibração não desenha gráfico vazio.

### 2.4 Frontend — HEA

- Gráficos recuperados apenas no que os dados sustentam: G-A (−T·ΔS_mix × T) e G-B (δ × VEC). Ambos com eixos, unidades, condições, legenda, fonte e natureza.
- Removida a zona "estável" fixa e sem fonte que o front desenhava.
- Energia de formação, energia de mistura e energia de Gibbs apresentadas separadamente, com unidade, referência e condições. `energia_formacao: null` com motivo, porque o sistema não a calcula.
- Descritores empíricos como triagem: `triagem.estado` ∈ {favorável, desfavorável, inconclusiva}. A palavra "ESTÁVEL" foi retirada.
- **Modo demonstrativo mantido, com selo** (decisão sua, Q-14). O adaptador usa a estrutura de triagem do motor, sem veredito sorteado, e cada valor, gráfico e tabela vindo de `heaDemo.ts` leva o selo.

### 2.5 Testes e processo

- Testes novos ou reescritos: alinhamento de FEA, validação de estruturas (64 testes), ligas, erros da API, procedência, histórico (F-1), termo HEA, E2E de seleção, filtros, aparência, layout, térmico.
- Fuzz adversarial independente: 1.269 requisições em 9 rotas, **zero HTTP 500**.
- Preservação do HEA: comparado o motor 1.0.0 com o 2.0.0 em 15 ligas × 2 políticas de dados — zero diferença em ΔS, δ, VEC, T_m e composição.
- **Ponto de retorno (commit `74e3181`, branch `integracao/r1-r2-2026-11-15`).** 236 arquivos, +32.243 / −2.058 linhas. Antes disso, a árvore tinha 105 arquivos modificados e 61 novos sem ponto de retorno (pendência Q-17). Agora `git checkout main` devolve o estado anterior sem destruir nada. O `package-lock.json` dentro de `_origem/` ficou de fora, por ser resíduo gerado numa base somente leitura.

### 2.6 Documentação

Atualizados: `docs/API.md`, `docs/MOTOR_HEA.md`, `docs/MOTOR_CIENTIFICO.md`, `docs/FRONTEND.md`, `docs/BANCO_DE_DADOS.md`, `docs/HISTORICO_DE_ALTERACOES.md`, `docs/PENDENCIAS.md`, `docs/openapi.json`. Decisões em `docs/architecture/`. Relatórios de agentes em `docs/agent_reports/`. Pesquisa bibliográfica em `docs/research/`.

---

## 3. Pontos que falharam e o que aconteceu com cada um

### 3.1 Falhas do HEA (auditoria)

Causa observada → correção:

- **A-01** `dH`/`omega` nulos e `gibbs` vazio sem motivo (gráficos nunca apareciam) → todo campo nulo tem motivo em `indisponiveis`, com `pares_faltantes` e `dados_faltantes`.
- **A-02** Elemento inexistente (`Xx`) calculava ΔS → conferência contra os 118 símbolos, HTTP 400.
- **A-03** `fe` e `Fe` viravam dois elementos → forma canônica, HTTP 400 `elemento_repetido`.
- **A-07** VEC fora do domínio sugeria estrutura (Al+Mg → CCC; Fe 99,9 % + Ni 0,1 % → CFC) → aplicabilidade explícita (`vec_aplicavel`); fora do domínio não há sugestão, com aviso dizendo que a regra é conservadora e não tem fonte primária verificada.
- **A-08** HTTP 500 com `Fe: 1e308, Ni: 1e308` (soma estourava, caía em log(0)) → limites e `math.fsum`, HTTP 400.
- **A-09** Quantidade `"1"` ou `true` aceita por coerção → número JSON estrito, HTTP 422.
- **A-04** Ausência de % em massa → entrada e saída nas duas bases; ida e volta com erro ≤ 5,6e-17.
- **A-17** Modo demo sorteava veredito "ESTÁVEL" → adaptador usa a estrutura de triagem; selo em cada valor.
- **A-10 a A-22** (códigos de erro, arredondamento, vocabulário de previsão, tolerância de limiar, mensagens) → corrigidos no motor 2.0.0.

**Não corrigido:**
- **A-05** Cobertura de 15 metais (Mn ausente, liga de Cantor sem δ, T_m e VEC). Depende de Q-03 e da decisão sobre ADR-018.

### 3.2 Falhas do motor e do contrato

- **Contrato térmico.** O zod do front recusava `fator: null` e derrubava a tela de temperatura. Decidido a favor do motor (princípio do projeto: sem base, `null` com motivo). Corrigido em `contracts.ts`, com os campos do motor 2.0.0 declarados.
- **T-21 (intersticial com supercélula pequena).** Confirmado que o motor estava certo e o teste estava velho. A parte de **interface** (sugerir supercélula maior quando a amostra dá 0 solutos) segue como pendência do frontend — verifique no navegador (ver seção 6).
- **E2E `alloy-thermal.spec.ts:46`.** Falhava com a T-21 e com o contrato; na última execução, com build imediatamente antes, a suíte fechou 74/0.

### 3.3 Falhas de processo (registradas, não resolvidas)

- **Interrupções por limite de uso da API.** Foram 7 cortes por HTTP 429 em 4 dias. Em 2 casos o trabalho foi recuperado pelos artefatos em disco; em 1 a árvore ficou com typecheck quebrado (`FilterPanel.tsx`, chaves de i18n inexistentes) e foi consertada. Nenhuma interrupção foi erro de execução.
- **Sub-agentes não acionados:** `database-engineer`, `devsecops-engineer`, `pedagogical-engineer`, `learning-analytics`, `machine-learning-engineer`. Não houve parecer pedagógico nem de segurança sobre as telas novas. O item deve ser tratado como não cumprido.
- **Divergência de dado (Q-13).** O titânio aparece com densidade e parâmetro diferentes em duas telas: `a` = 0,2951 nm em `/cells` e 0,2890 nm em `/solid-solutions` (6,5 % no mesmo metal). A mudança V-14, que resolveria isso, não foi aprovada. Fica como decisão sua.
- **Divergência dev/prod (F-2 resolvido, mas com risco).** Antes, o SQLite de desenvolvimento escondia defeitos de integridade. Com a FK imposta, uma nova classe de erro pode aparecer em dev, e isso ainda não foi reexecutado num banco preexistente real.

---

## 4. O que não pode ser feito agora (e o que destrava)

| Item | Por que não | O que destrava |
|---|---|---|
| **Matriz de entalpias binárias de mistura (ΔH_mix, Ω, veredito HEA completo, gráficos δ×ΔH e G×T)** | O PDF de Takeuchi & Inoue (2005) não tem camada de texto. Foram lidos 0 pares da fonte primária; 15 pares de fonte secundária com atribuição conjunta têm confiança baixa e **não foram usados**. | PDF com OCR, transcrição revisada da tabela, ou a compilação de de Boer/Miedema (1988). **Q-01** |
| **Diagramas de fase, multifásico, Gibbs por fase, frações de fase × T, partição** | Exigem CALPHAD. Não há biblioteca (sem `pycalphad`, `numpy` ou `scipy`) nem base TDB no repositório. | Decisão sua: não adotar (recomendação do especialista) ou autorizar investigação de licença, cobertura e compatibilidade. **Q-11** |
| **Cinética (TTT, CCT)** | Precisa de modelo próprio de cinética, que não existe no repositório. | Fora de escopo declarado. |
| **Promover dados a "validado" e liberar δ, T_m, VEC, ligas e temperatura em produção** | Sem validador científico nomeado, nenhum dado pode ser promovido. Hoje o módulo térmico não funciona em produção. | Nomear o especialista validador. **Q-03** |
| **Cobertura de 15 metais no HEA (Mn, liga de Cantor, T_m e VEC)** | Depende de Q-03 e de decisão sobre ADR-018. | Q-03 + decisão sobre ADR-018 |
| **Citações com página do Callister e do Askeland** | Só 1 das 32 afirmações citadas em código está verificada na fonte (R = 8,314462618 J/(mol·K), NIST). As edições e páginas não foram conferidas. | Definir a edição e conferir as páginas, ou remover o número de página. **Q-09** |
| **4 obras da bibliografia fornecida** | Reed-Hill (ed. em português), Padilha "Metalurgia Física", Ávila & Becker e Chvátal não foram localizados em catálogo. | Confirmar autoria e edição. **Q-10** |
| **Zona "solução sólida" do gráfico HEA** | As fontes secundárias divergem: −15 a 5, −15 a −5 e −10 a 5 kJ/mol. | Conferir em Zhang et al. (2008). **Q-08** |
| **Publicar o projeto** | O portão G5 não foi atingido e a publicação nunca foi autorizada. | Validação visual, validador científico, PostgreSQL, QA de frontend e decisão de hospedagem (Q-02) |
| **Rodar a seed em banco já carregado** | A linha de `motores` das versões novas (`hea 2.0.0`, `crystallography 2.1.0`) não foi gravada em banco existente, e isso exige migração ou seed, que você não autorizou. | Autorização explícita e revisão com o database-engineer. **Q-15 / T-31** |
| **Alterar esquema do banco ou aplicar migração** | Não autorizado pelo CLAUDE.md sem pedido explícito. | Pedido seu, com o plano de rollback. |
| **Validação visual no navegador** | Nenhum agente abriu a aplicação visualmente. Eu posso fazer, mas ainda não fiz. | Pedido seu (ver seção 6). |
| **Testes de PostgreSQL, Docker, compose e CI** | Esta máquina não tem PostgreSQL. Docker e CI não foram rodados. | Ambiente com PostgreSQL e Docker. |
| **Leitor de tela real, outros navegadores, rede degradada** | Não executados. | Ambiente de teste de acessibilidade. |
| **Commit/push no remoto** | Commit local feito a pedido. Push depende de pedido seu. | Pedido seu. |
| **Mudança do valor de `a` do titânio (V-14)** | Não aprovada; mudaria valores visíveis. | Decisão sua. **Q-13** |
| **Desempenho da cena com supercélulas no layout novo** | Não medido com a interface nova. | Medição no navegador. |

---

## 5. Riscos que continuam abertos

1. **Q-16 — política de dado não validado aplicada de forma desigual.** `/cells` e `/density` devolvem valor em produção com dado que aguarda validação; o térmico recusa; o HEA anula. Opções: (A) alinhar ao princípio 3 e desligar o CrystaLab em produção até Q-03; (B) manter a exceção escrita no `CLAUDE.md` e revertê-la quando Q-03 for resolvida. **Recomendação do supervisor: (B). Sua decisão.**
2. **Risco de processo — Q-17.** Resolvido localmente pelo commit `74e3181`. Continua valendo para trabalho futuro: não usar `git restore`, `checkout`, `reset`, `stash` ou `clean` sem antes criar um ponto de retorno.
3. **Retratação.** A revisão Heliyon 10(22):e39660 está retratada e não deve ser citada.
4. **Afirmações não verificadas no código.** 31 das 32 afirmações citadas em código não foram verificadas na fonte. Não devem ser apresentadas como verificadas.
5. **Processo de sub-agentes.** Sete cortes por limite de uso. Se continuarem, a rodada seguinte deve começar com um ponto de retorno e um arquivo de estado atualizado a cada decisão.

---

## 6. Verificação que falta (roteiro para o navegador)

Subir: `cd frontend && npm run dev` (sobe a API real e a página em `http://127.0.0.1:5173`).

1. `#/crystalab`: o palco ocupa tudo abaixo do cabeçalho; recolher e reabrir a barra; câmera por mouse e teclado (girar, deslocar, aproximar, centralizar, restaurar).
2. Composição → Fe + C a 2 % em 2×2×2: deve avisar que nenhum carbono cabe, explicar a causa e oferecer refazer em 3×3×3. **Ponto que eu mais desconfio.**
3. Clicar num átomo da liga: cartão com elemento, id, coordenadas em a e nm, fracionárias, fase, sítio, ocupação; bloco de elemento puro separado.
4. Aparência: cor por elemento, grupo e átomo; vértices e arestas; tamanho e transparência; comparar o marcador (arame) com o átomo (esfera sólida); restaurar.
5. Filtros e cortes: isolar elementos, cortar, clicar em átomos internos.
6. Animação α→γ com selo "Interpolação visual"; HEA demonstrativo com selo em cada valor, gráfico e tabela. **Ponto que eu mais desconfio.**
7. Células de Mg e Ti: painel de primeiros vizinhos dizendo qual raio entrou no FEA.
8. Temas claro e escuro; tela estreita (gaveta); Ctrl+P.

---

## 7. Limpeza pendente

- **API de teste na porta 8130.** Subida para o teste de contrato; o modo automático bloqueou o encerramento. Pode ainda estar de pé. Encerrar pelo Gerenciador de Tarefas.
- **Branch.** Você está em `integracao/r1-r2-2026-11-15`, não em `main`.
- **`_origem/C_alloy_frontend/alloy-frontend/package-lock.json`.** Não rastreado, deixado de fora do commit de propósito. Resíduo gerado numa base somente leitura.
- **`docs/PENDENCIAS.md`, Q-17.** Ainda descreve o risco como aberto. Deve ser atualizado para "resolvido localmente em `74e3181`; sem push".

---

## 8. Decisões que dependem de você

1. **Q-16** — manter a exceção documentada (B, recomendado) ou desligar o CrystaLab em produção até Q-03 (A).
2. **Q-03** — nomear o validador científico.
3. **Q-01** — fornecer a fonte legível da matriz de ΔH binário.
4. **Q-11** — adotar ou não CALPHAD (recomendação: não adotar nesta fase).
5. **Q-13 / V-14** — autorizar ou não a mudança do parâmetro de rede do titânio.
6. **Q-15 / T-31** — autorizar a inserção da linha de `motores` em banco existente.
7. **Q-09 / Q-10** — edição e páginas das citações; as 4 obras não localizadas.
8. **Push e publicação** — só com pedido explícito.
