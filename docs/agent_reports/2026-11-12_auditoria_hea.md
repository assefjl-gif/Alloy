# R1-HEA-01 — Auditoria do módulo HEA e especificação científica (G1)

Agente responsável: hea-specialist (Agente 08). Emissor: Supervisor (Agente 01). Data: 12/11/2026.
Estado deste arquivo: CONCLUÍDO (auditoria e especificação G1). Aguarda pareceres e consultas da seção 3 antes da implementação.

Convenções deste relatório:
- **[FATO]** observado nesta tarefa (comando executado ou arquivo lido); **[INFERÊNCIA]** conclusão tirada dos fatos;
  **[RECOMENDAÇÃO]** proposta a implementar; **[NÃO VERIFICADO]** não conferido nesta tarefa.
- Nenhum código de produção foi alterado. Scripts de reprodução ficaram fora do repositório (scratchpad da sessão).
- Referências bibliográficas: "verificada nesta tarefa" significa que o texto da fonte foi consultado nesta tarefa.
  Não houve acesso a periódicos; por isso todas as referências de literatura estão marcadas **não verificada**
  (citadas de memória do especialista quanto a autor/periódico/ano; conferência a cargo do auditor bibliográfico).

## 0. Linha de base

[FATO] Medido nesta tarefa, em 12/11/2026, commit base `93755eb` com árvore de trabalho modificada (não alterada por mim):

- Motor: `backend/app/engines/hea/analitico.py`, `VERSAO_MOTOR = "1.0.0"` (linha 27). Rotas `POST /api/v1/hea/analyses` e
  `GET /api/v1/hea/bootstrap` (`backend/app/api/v1/rotas.py:134-146`).
- Testes existentes: `pytest tests/unit/engines/test_hea.py tests/api/test_api.py -k "hea or producao"` → 25 aprovados, código de saída 0.
- Versão dos dados devolvida: `2026.10.1+2026.11.1-v14+2026.11.2-hea`.
- Scripts de reprodução (fora do repositório, no scratchpad da sessão): `hea_auditoria.py` (casos A1..G2, saída em
  `hea_auditoria.out`), `hea_cobertura.py` (cobertura dos seeds). Cliente: `TestClient(create_app(Settings(_env_file=None)))`.
  Nenhum `.env` foi lido.
- Produção: a política de produção foi conferida pelos testes existentes `test_producao_hea_so_entropia` e
  `test_producao_capacidades` (aprovados acima). Minha tentativa de montar produção sem banco migrado devolveu 500
  (`no such table: versoes_dados`): é limitação do meu script (banco vazio), NÃO é achado do produto.

## 1. Auditoria

Itens do pedido: (a) entrada e validação; (b) conversão at.% ↔ % em massa; (c) normalização, unidades e limites de validade;
(d) fontes e disponibilidade de dados; (e) equações, hipóteses, algoritmos e erros; (f) integração cálculo/gráfico/tabela/interface;
(g) persistência, atualização e exportação.

Severidade: **Crítica** = resultado cientificamente enganoso ou função principal ausente; **Alta** = falha de validação ou de
rastreabilidade que chega ao usuário; **Média** = robustez ou clareza; **Baixa** = cosmético ou inconsistência menor.

Confirmação dos achados do supervisor: H-1, H-2, H-3, H-4, H-5 e H-6 **CONFIRMADOS** por execução ou leitura minha (linhas A-01..A-06).

### 1.1 Achados (falhas)

| ID | Item | Descrição | Reprodução (payload → saída observada) | Causa-raiz | Sev. | Correção proposta | Dono |
|---|---|---|---|---|---|---|---|
| A-01 (H-1) | (e)(f) | `dH`, `omega` sempre `null` e `gibbs` sempre `[]`; os dois gráficos nunca são desenhados. `gibbs`, `dureza`, `ductilidade` vazios NÃO têm entrada em `indisponiveis` (só `dH` e `omega` têm). | `{"Co":1,"Cr":1,"Fe":1,"Ni":1}` → 200, `dH:null, omega:null, gibbs:[]`, `indisponiveis` = {dH, omega}. | `analitico.py:111` (motivos fixos), `:167`, `:169`, `:176`; `HeaCharts.tsx:47` e `:98` (só desenham com δ+ΔH ou curva). Não existe matriz de ΔH binário no repositório (Q-01). | Crítica | Seção 2.4 a 2.6: ΔH/Ω condicionais à matriz com fonte; gráficos que não dependem de ΔH (−T·ΔS × T; δ × VEC); motivo em `indisponiveis` para TODA grandeza nula ou vazia. | dados + backend + frontend |
| A-02 (H-2) | (a) | Elemento inexistente ou texto arbitrário é aceito como elemento; devolve 200 com ΔS calculado. | `{"Xx":1,"Fe":1}` → 200, `dS:5.7631`, `comp_percent:{"Fe":50,"Xx":50}`. `{"":1,"Fe":1}` → 200 (chave vazia). `{"<b>x</b>":1,"Fe2O3":1}` → 200. `{"He":1,"O":1}` → 200. | `analitico.py:46-66` (não confere existência; só `strip`); `:73-76` trata símbolo desconhecido como "raio não cadastrado"; `schemas.py:497` (`Dict[str, float]` sem padrão de chave). | Alta | 2.1: símbolo validado contra a tabela periódica (118); desconhecido → 400. | backend |
| A-03 (H-3) | (a) | Símbolo com caixa errada não é normalizado nem detectado como duplicata. | `{"fe":1,"Fe":1,"Ni":1}` → 200, `comp_percent:{"Fe":33.3333,"Ni":33.3333,"fe":33.3333}`, `dS:9.1344` (3 "elementos"). `{"fe":1,"NI":1}` → 200 com tudo indisponível ("Não há raio atômico cadastrado para NI"). | `analitico.py:58` (só `strip`), `:63` (duplicata sensível a caixa). | Alta | 2.1: forma canônica (1ª maiúscula, resto minúsculo) antes de conferir repetição. | backend |
| A-04 (H-4) | (b) | Não há entrada nem saída em % em massa. A entrada é sempre interpretada como molar; quem digita % em massa recebe resultado de outra liga, sem aviso. | `{"composicao":{"Fe":1,"Ni":1},"base":"massa"}` → 422 "campo não reconhecido". Resposta não tem campo de massa (chaves listadas no caso B4). | `schemas.py:491-498` (sem campo de base), `analitico.py:66` (normalização molar única), `HeaModule.tsx:176` (rótulo fixo `hea.atomicPct`). | Alta | 2.2: campo `base` na entrada; saída com as duas bases. | backend + frontend |
| A-05 (H-5) | (d) | Cobertura: 15 metais com raio e T_f; 13 com VEC (faltam Pb e Po). Sem Mn, V, Nb, Ta, Zr, Hf: Cantor e ligas refratárias ficam sem δ, T_m e VEC. `samples` vazio. | `{"Co":1,"Cr":1,"Fe":1,"Mn":1,"Ni":1}` → 200, `dS:13.3816`, `delta/VEC/Tm:null`, motivos "Não há ... cadastrado para Mn". `{"Pb":1,"Fe":1}` → `VEC:null`. Bootstrap: `samples: 0`. | `database/seeds/cristalografia/metais.json` (15), `hea/vec.json` (13), `analitico.py:220` (`"samples": []`). | Alta | 2.3: T_f, massa e VEC (por regra, sob parecer) podem ser ampliados com dados já no repositório; raio metálico NÃO (pendência P-HEA-01). | dados |
| A-06 (H-6) | (f) | (i) Interface trata todo veredito que não começa com "ESTÁVEL" como risco (ícone ⚠, classe `is-risk`) e o registra no terminal como `error`. O motor nunca devolve "ESTÁVEL": toda análise real aparece como risco/erro. (ii) A tabela "Comparação com a liga de referência" subtrai LIMIARES de critério do valor calculado e chama de diferença para uma "liga de referência" que não existe. | Leitura de código (não executado em navegador). Motor: veredito sempre começa com "INCONCLUSIVO —" (caso D, CoCrFeNi). | `HeaModule.tsx:141` e `:153`; `handlers.ts:41-42`; `HeaModule.tsx:78-86`; rótulos em `i18n/source/04-panels.tsv:67` e `:72`; `analitico.py:208-209` (`REFERENCIA` são limiares). | Alta | 2.6 e 2.7: estado da triagem em campo próprio (`triagem.estado`); tabela de critérios (valor, operador, limiar, atende, fonte) no lugar da "diferença". | frontend + backend |
| A-07 | (c)(e) | Critério de VEC aplicado FORA do domínio de validade e sem a condição "forma solução sólida": liga binária Al–Mg recebe "CCC"; Mg–Ti–Zn (três metais HC) recebe "CCC"; Fe quase puro recebe "CFC". `estrutura_sugerida` alimenta o botão "abrir no CrystaLab" como se fosse predição. | `{"Al":1,"Mg":1}` → `VEC:2.5`, `fase:"CCC (critério VEC < 6,87)"`, `estrutura_sugerida:"CCC"`. `{"Mg":1,"Ti":1,"Zn":1}` → `"CCC"`, com δ = 7,53 % (acima do próprio limiar). `{"Fe":99.9,"Ni":0.1}` → `VEC:8.002`, `"CFC (critério VEC ≥ 8,0)"`, `estrutura_sugerida:"CFC"`. | `analitico.py:96-103` e `:137` (sem teste de aplicabilidade); `HeaModule.tsx:107-126` e `transfer.ts:39-44` (abertura direta com `estrutura_sugerida`). | Crítica | 2.7: critério de VEC só é emitido dentro do domínio declarado; fora dele `fase` = "não avaliada" com motivo e sem `estrutura_sugerida`. | backend (parecer do materials-science-specialist) |
| A-08 | (a)(e) | Erro interno 500 com quantidades grandes: a soma estoura para `inf`, as frações viram 0,0 e `log(0)` lança exceção. | `{"Fe":1e308,"Ni":1e308}` → **500** `ERRO_INTERNO`; traceback: `analitico.py:70` `ValueError: expected a positive input, got 0.0`. | `analitico.py:65-66` (soma sem limite) e `:70` (`math.log(x)` sem guarda). | Média | 2.1: limite superior por quantidade (1e6) e conferência de soma finita; erro 400. | backend |
| A-09 | (a) | Coerção frouxa de tipo: quantidade como texto ou booleano é aceita. | `{"Fe":"1","Ni":1}` → 200. `{"Fe":true,"Ni":1}` → 200 (true = 1). | `schemas.py:497` (`Dict[str, float]` em modo não estrito). | Média | 2.1: número JSON estrito; texto/booleano → 422. | backend |
| A-10 | (a) | Limites inconsistentes: o esquema conta chaves, o motor conta quantidades > 0; e o mesmo erro lógico sai com códigos diferentes. | 13 chaves com 1 zero (12 efetivos) → 422 "no máximo 12 itens". `{"Fe":1}` → 422 `VALIDACAO`; `{"Fe":0,"Ni":1}` → 400 `ENTRADA_INVALIDA` (ambos "menos de 2 elementos"). | `schemas.py:497` (`min_length=2, max_length=12`) × `analitico.py:57-62`. | Baixa | 2.1: regra única documentada. | backend + api |
| A-11 | (c) | Arredondamento e frações mínimas sem aviso: `comp_percent` arredondado a 4 casas não soma 100; elemento presente aparece com 0,0 % e ΔS = 0,0. Elementos com quantidade zero são descartados em silêncio. | `{"Al":0.3,"Co":1,"Cr":1,"Fe":1,"Ni":1}` → soma de `comp_percent` = 99,9999. `{"Fe":1e-12,"Ni":1}` → `dS:0.0`, `comp_percent:{"Fe":0.0,"Ni":100.0}`. | `analitico.py:166`, `:172`, `:57-58`. | Baixa | 2.1 e 2.2: fração mínima 1e-6; aviso para zeros descartados; somas conferidas nas frações não arredondadas. | backend |
| A-12 | (d) | T_f usada em T_m vem do seed v1.4 em estado `rascunho` e **sem fonte** (`fonte: null`), em °C; o repositório já tem T_f com fonte (PubChem, K) para 103 elementos, com divergência registrada no Cr. | Comparação que executei: Cr v1.4 = 1857 °C (2130,15 K) × PubChem 2180 K: +49,85 K; demais 14 metais: \|dif\| ≤ 0,47 K. Efeito: T_m(CoCrFeNi) 1859,4 K × 1871,8 K; T_m(AlCoCrFeNi) 1674,2 K × 1684,1 K. | `database/seeds/cristalografia/propriedades_v14.json` (`temperatura_fusao`, 15 registros, `fonte: null`); `analitico.py:123-128`; divergência anotada em `tabela_periodica/FONTES.txt` (seção 4). | Média | 2.3: decidir fonte única de T_f (consulta C-03). | dados (parecer materials-science + auditor) |
| A-13 | (d) | Raio atômico: o estado `aguardando_validacao` e a unidade são fixados no código, não lidos do dado; a fonte "callister" não tem edição nem página (CR-10). | `procedencia.dados_usados[0]` = `{"simbolo":"Co","codigo":"raio_atomico","valor":0.1253,"unidade":"nm","estado":"aguardando_validacao","fonte":"callister"}`. | `analitico.py:77-83`; `metais.json` (`fontes.callister.observacao`). | Média | Raio como propriedade versionada (mesma tabela das demais), com fonte completa. | dados + backend |
| A-14 | (d) | Exemplos do bootstrap trazem fase "de literatura" sem citação verificável: "CFC (literatura)", "CCC/B2 (literatura)", "CFC (Yeh 2004)". É afirmação de natureza experimental sem registro de fonte. | Bootstrap → `alloys` = CoCrFeNi, AlCoCrFeNi, CoCrCuFeNi, Al0.5CoCrCuFeNi com o campo `grupo` acima. | `analitico.py:199-205`. | Média | Citação por liga (auditor) ou rótulo "relatado na literatura (citação pendente)". | dados (auditor bibliográfico) |
| A-15 | (f) | Zona do mapa δ × ΔH desenhada com números fixos no frontend e sem fonte: "−15 < ΔH < 5 kJ/mol; δ < 6,6 %", rotulada "solução sólida", legenda "favorece solução sólida" e título "Mapa de estabilidade". O próprio código atribui os limites ao "HEA Virtual Lab v1.17", não à literatura. | Leitura de código. Hoje o gráfico não aparece no modo real (A-01), mas aparece no modo demonstrativo (A-17). | `HeaCharts.tsx:5`, `:66`, `:69`, `:74`; `i18n/source/04-panels.tsv:94` e `:98`. | Alta | 2.6: faixas vêm da API, cada uma com fonte; nome "mapa de triagem"; ver avaliação da zona em 2.6.1. | frontend + backend + auditor |
| A-16 | (e)(c) | Texto com linguagem de previsão sem base: "intermetálicos/amorfo mais prováveis"; "fase prevista pelo critério de Guo"; classe única `estimativa_modelo` para o resultado inteiro, embora ΔS_mix seja analítico. | CoCrFeNi → `interpretacao[2]` = "VEC = 8,25 → fase prevista pelo critério de Guo: CFC ..."; `procedencia.classe: "estimativa_modelo"`. | `analitico.py:147-150`, `:186`. | Média | 2.7: vocabulário de triagem; classe por grandeza. | backend |
| A-17 | (f) | Modo demonstrativo gera números, curva e veredito fictícios, inclusive "ESTÁVEL (valor demonstrativo)", que a interface pinta como aprovado (✓) e plota DENTRO da zona de critério real; limiares do demo são inventados e diferentes dos do motor. Os gráficos não recebem a marca de demonstração. | Leitura de código: `HEA_DEMO_REFERENCE = {dS:10, omega:5, delta:3, VEC:7, dH:-5}`; curva = passeio aleatório; `veredito` sorteado. | `heaDemo.ts:27`, `:42-46`, `:47-60`; `HeaModule.tsx:141`, `:172`; `HeaCharts.tsx` (sem `origin`); legenda "com os valores do preditor" (`04-panels.tsv:99`). | Alta | 2.8. | frontend (decisão do supervisor/usuário) |
| A-18 | (a)(f) | O analisador de composição do frontend descarta ou altera entradas em silêncio. | Executado em Node com cópia literal da regex de `store.ts:43`: `"FeNi=20\nCo=20"` → `{Ni:20,Co:20}` (Fe some); `"Fe=-5\nNi=1\nCo=1"` → `{Ni:1,Co:1}`; `"Fe=1e-3\nNi=1"` → `{Fe:1,Ni:1}`; `"Fe=10\nFe=30\nNi=10"` → `{Fe:30,Ni:10}`; `"Uue=1\nFe=1"` → `{Ue:1,Fe:1}`; `"Fe=1.234.5\nNi=1"` → `{Fe:1.234,Ni:1}`; `"Al0.5CoCrFeNi"` → `{}`. `compositionToText` grava 2 casas: `Fe=0.004` → `"Fe=0.00"`. | `store.ts:34-52`. | Alta | 2.1.4: o front envia o que foi digitado, linha a linha, e mostra o erro do servidor; nada é descartado em silêncio. | frontend |
| A-19 | (g) | Resultado antigo continua na tela, sem marca de desatualizado, depois que a composição é editada. Não há exportação do resultado do HEA (CSV/JSON/impressão dedicada). | Leitura de código (não executado em navegador): `onChange` só altera `editorText` e `selectedKey`; `result` permanece. Busca por `download`, `Blob(`, `csv` em `modules/hea/`: nenhuma ocorrência. | `HeaModule.tsx:63`; `store.ts`. | Média | 2.6.6: marca "resultado desatualizado" quando a composição do editor difere da composição do resultado; exportação com procedência. | frontend |
| A-20 | (g) | Persistência: a execução só é gravada com sessão de banco E usuário autenticado; o hash de parâmetros é do payload bruto (a mesma liga escrita como `Fe1Ni1` e `Fe50Ni50` tem hashes diferentes). Não é falha, é limite a documentar. | Leitura de `calculo.py:165-180`. Não executei gravação em banco. | `backend/app/services/calculo.py:171-179`; `analitico.py:188`. | Baixa | Guardar também a composição normalizada (canônica) nos parâmetros. | backend |
| A-21 | (e) | Risco latente (NÃO reproduzido pela API): comparação de VEC com o limiar em ponto flutuante sem tolerância. Demonstração aritmética: média equimolar de VEC (4, 10, 10) = `7.999999999999999` < 8,0. Varredura que executei nas ligas equimolares de 3 a 6 elementos com VEC exatamente 8 entre os 13 elementos atuais: 0 casos mal classificados. | Ver descrição. | `analitico.py:99-103`, `:135`. | Baixa | 2.7.3: comparação com tolerância 1e-9 e `math.fsum`. | backend |
| A-22 | (e) | Mensagem com concordância errada e redação técnica exposta ao usuário: "Não há temperatura de fusão cadastrado para Mn."; "questão Q-01". | Caso E1 (Cantor). | `backend/app/engines/procedencia.py:80`; `analitico.py:42-43`. | Baixa | Mensagens da seção 2.1.3 e 2.4.4. | backend |

Observação sobre A-06, A-15, A-17 e A-19: são constatações por leitura de código do frontend. Não executei o navegador (Playwright)
nesta tarefa; a reprodução visual fica para o QA (R1-QA-01).

### 1.2 Correto e a preservar

| Item | Conferência executada nesta tarefa | Resultado |
|---|---|---|
| ΔS_mix ideal = −R·Σ xᵢ ln xᵢ, R = 8,314462618 J/(mol·K) | Equimolar n = 2..6 pela API × R·ln n calculado à parte | 5,7631; 9,1344; 11,5263; 13,3816; 14,8975 J/(mol·K); diferença máxima 4,6e-5 (só arredondamento a 4 casas) |
| Invariância de escala | `Fe1Ni1`, `Fe50Ni50`, `Fe0.5Ni0.5` | Saídas idênticas |
| δ = 100·√(Σ xᵢ(1 − rᵢ/r̄)²), r̄ = Σ xᵢrᵢ | Recalculado à parte com `metais.json` para 4 ligas | AlCoCrFeNi 5,7324 %; CoCrFeNi 0,3512 %; CrMoW 4,1970 %; Al0.5CoCrCuFeNi 4,1368 %: iguais à API |
| VEC = Σ xᵢ·VECᵢ | Idem, com `hea/vec.json` | 7,2; 8,25; 6,0; 8,2727: iguais |
| T_m = Σ xᵢ·T_f,ᵢ (K) | Idem, com `propriedades_v14.json` (°C + 273,15) | 1674,2; 1859,4; 2907,2; 1684,1 K: iguais |
| Nunca inventa ΔH, Ω, dureza, ductilidade, curva | Todos os casos | Sempre `null`/`[]` (falta só o motivo de `gibbs`, `dureza`, `ductilidade`: A-01) |
| Cálculo parcial com `indisponiveis` | Cantor, Pb+Fe | ΔS sai; cada grandeza ausente traz o motivo |
| Política de produção | Testes existentes aprovados (25) | Produção devolve só ΔS_mix; δ, T_m, VEC nulos com motivo |
| Rejeições corretas | negativo, NaN, Infinity, 1e400, 1 elemento, 13 elementos, campo extra, nome > 80, repetido após `strip` | 400 ou 422 com mensagem em português |
| `procedencia` | CoCrFeNi | `dados_usados` com valor, unidade, estado e fonte; aviso de dados não validados; `versao_dados` composta; `fontes_modelo` |
| Frontend não recalcula grandezas | Leitura de `HeaCharts.tsx` e `HeaModule.tsx` | Só exibe o que recebe (exceções: a "diferença" de A-06 e o comando `normalizar`, que reescala o texto digitado) |
| Consistência dos 13 valores de VEC com o grupo IUPAC | Regra "grupo ≤ 12 → grupo; grupo 13 → grupo − 10" × `vec.json`, usando `grupo` de `tabela_periodica/elementos.json` | 13 de 13 iguais (conferência interna; NÃO substitui a conferência com a tabela de Guo et al.) |

## 2. Especificação G1

Tudo nesta seção é **[RECOMENDAÇÃO]** para implementação (portão G1), salvo onde marcado [FATO]. Nomes de campos são propostas
para o api-architect fechar no contrato; o conteúdo científico (significado, unidade, nulidade, regra) é o que este parecer fixa.
Versão do método após a implementação: motor HEA **2.0.0** (mudança de contrato e de regras de validação; resultados antigos
gravados com 1.0.0 permanecem rastreáveis pela `versao_motor`).

### 2.1 Validação de entrada

#### 2.1.1 Requisição

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `nome` | texto, até 80 | não | como hoje |
| `composicao` | objeto `{símbolo: quantidade}` | sim | 2 a 12 chaves; ver 2.1.2 |
| `base` | `"atomica"` \| `"massica"` | não (padrão `"atomica"`) | diz em que base as quantidades foram informadas (2.2) |
| `temperatura_k` | número | não (padrão `null`) | opcional; 0 < T ≤ 6000 K; pede o valor pontual de −T·ΔS_mix e de ΔG_mix nessa T (2.5). Prioridade menor: pode ficar para depois de R1 |

#### 2.1.2 Regras, na ordem de aplicação

1. **Tipo da quantidade:** número JSON (inteiro ou real). Texto (`"1"`) e booleano (`true`) → 422 `VALIDACAO`.
2. **Valor da quantidade:** finito e 0 ≤ q ≤ 1e6. Negativo, NaN, ±Infinity ou q > 1e6 → 400. O limite 1e6 é operacional (evita o estouro
   de A-08); a soma é feita com `math.fsum` e conferida como finita e > 0.
3. **Símbolo:** `s = chave.strip()`; deve casar com `^[A-Za-z]{1,2}$`; forma canônica = primeira letra maiúscula, segunda minúscula
   (`fe` → `Fe`, `NI` → `Ni`). Fora do padrão → 400 `simbolo_invalido`.
4. **Existência:** o símbolo canônico deve existir na tabela periódica do repositório (118 elementos,
   `database/seeds/tabela_periodica/elementos.json`, campo `simbolo`). Senão → 400 `elemento_desconhecido`.
5. **Repetição:** dois símbolos iguais depois da normalização → 400 `elemento_repetido`. O servidor NUNCA soma duplicatas em silêncio.
6. **Zeros:** chaves com quantidade 0 são descartadas e listadas em `procedencia.avisos`
   ("Elementos com quantidade zero foram ignorados: X, Y.").
7. **Contagem:** depois de descartar zeros, 2 ≤ n ≤ 12. O esquema continua limitando a 12 CHAVES (inclui as de quantidade zero);
   a descrição do campo deve dizer isso. Menos de 2 elementos com quantidade > 0 → sempre 400 `elementos_insuficientes`
   (o esquema deixa de ter `min_length=2` para que o código de erro seja único), ou o api-architect mantém 422 para os dois casos:
   o requisito científico é só que o código seja o mesmo. O limite 12 é operacional, sem base científica.
8. **Base mássica:** se `base = "massica"`, todo elemento precisa de massa atômica utilizável (2.2). Faltando → erro (2.1.3), porque sem a
   conversão nenhuma grandeza (nem ΔS_mix) pode ser calculada.
9. **Fração mínima:** depois da normalização para frações atômicas, todo xᵢ ≥ 1e-6. Abaixo disso → 400 `fracao_abaixo_do_minimo`.
   Justificativa: 1e-6 é a resolução da saída (% com 4 casas); abaixo disso o elemento apareceria como "0,0000 %" (A-11), e os
   descritores não têm significado para solutos em ppm.
10. **Soma:** as quantidades são partes proporcionais (fórmula, % ou fração); NÃO se exige soma 100. A resposta devolve
    `soma_informada` para a interface dizer "quantidades normalizadas (soma informada: 5,5)".

#### 2.1.3 Erros (envelope atual; `code` e HTTP como hoje, com subtipo estável em `details[].type`)

| Subtipo | HTTP / `code` | Mensagem (pt-BR) |
|---|---|---|
| `simbolo_invalido` | 400 `ENTRADA_INVALIDA` | "Símbolo inválido: '{chave}'. Use o símbolo químico do elemento, com 1 ou 2 letras (ex.: Fe, Ni, Co)." |
| `elemento_desconhecido` | 400 `ENTRADA_INVALIDA` | "Elemento desconhecido: '{símbolo}'. Não existe na tabela periódica." |
| `elemento_repetido` | 400 `ENTRADA_INVALIDA` | "Elemento repetido: '{chave1}' e '{chave2}' são o mesmo elemento ({símbolo}). Informe cada elemento uma única vez." |
| `quantidade_invalida` | 400 `ENTRADA_INVALIDA` | "A quantidade de {símbolo} deve ser um número entre 0 e 1 000 000." |
| `elementos_insuficientes` | 400 `ENTRADA_INVALIDA` | "Uma liga precisa de pelo menos 2 elementos com quantidade maior que zero." |
| `elementos_demais` | 422 `VALIDACAO` | "No máximo 12 elementos por liga." |
| `fracao_abaixo_do_minimo` | 400 `ENTRADA_INVALIDA` | "A fração de {símbolo} ({valor} at.%) está abaixo do mínimo aceito (0,0001 at.%). Remova o elemento ou aumente a quantidade." |
| `base_invalida` | 422 `VALIDACAO` | "Base da composição inválida: use 'atomica' ou 'massica'." |
| `massa_indisponivel` | 400 `ENTRADA_INVALIDA` (dado ausente) ou 422 `DADO_NAO_VALIDADO` (produção, dado não validado) | "Não é possível converter de % em massa: falta massa atômica utilizável para {lista}." |

Todos os erros de `ENTRADA_INVALIDA` devem trazer `details: [{"loc": ["composicao", "<chave original>"], "type": "<subtipo>", "msg": "..."}]`
(hoje só o 422 traz `details`). Nenhuma entrada pode produzir 500.

#### 2.1.4 Frontend (A-18)

- O analisador do editor deve aceitar ou recusar a linha inteira. Linha que não casa com `símbolo separador número` é ERRO mostrado ao
  usuário (com o número da linha), não é ignorada. Elemento repetido no texto é erro, não "vale o último". Número com sinal negativo,
  notação científica ou dois pontos decimais é erro.
- O front não decide se o elemento existe: envia o símbolo e mostra a mensagem do servidor.
- `compositionToText` não pode reduzir a precisão digitada (hoje grava 2 casas).
- O seletor de base (at.% ou % em massa) fica junto do editor, e o rótulo da tabela de composição acompanha a base.

#### 2.1.5 Decisão: elemento real, mas sem dados de HEA → **cálculo parcial (200) com `indisponiveis`**, não erro

Justificativa: (i) ΔS_mix depende só da composição e é exata dentro da hipótese ideal; recusar o pedido esconderia um resultado
legítimo (liga de Cantor); (ii) é o princípio PI-02 já adotado e o comportamento da produção; (iii) o erro fica reservado ao que
é de fato entrada inválida (símbolo que não é elemento). Condições para a decisão não virar "zero silencioso":

- cada grandeza nula tem motivo em `indisponiveis`, e a resposta ganha `dados_faltantes: [{simbolo, codigo, situacao}]`,
  com `situacao` = `"ausente"` ou `"nao_validado"` e `codigo` em {`raio_atomico`, `temperatura_fusao`, `vec`, `massa_atomica`,
  `entalpia_mistura_par`} (para pares, `simbolo` = `"Co-Mn"`);
- elemento de categoria `gás nobre`, `halogênio` ou `não metal` (campo `categoria` da tabela periódica) gera aviso:
  "{símbolo} não é metal: os descritores δ, VEC, ΔH_mix e Ω foram propostos para ligas metálicas substitucionais; a
  interpretação está fora do domínio de validade." A triagem (2.7) fica `inconclusiva` nesse caso.

### 2.2 Base da composição (atômica e mássica)

#### 2.2.1 Equações (verificadas nesta tarefa por cálculo de ida e volta)

Com Mᵢ = massa atômica (g/mol), xᵢ = fração atômica (molar), wᵢ = fração mássica:

- atômica → mássica: wᵢ = xᵢ·Mᵢ / Σⱼ xⱼ·Mⱼ
- mássica → atômica: xᵢ = (wᵢ/Mᵢ) / Σⱼ (wⱼ/Mⱼ)
- massa molar média: M̄ = Σᵢ xᵢ·Mᵢ (g/mol de átomos)

Todas as grandezas do HEA (ΔS_mix, δ, VEC, T_m, ΔH_mix, Ω) usam SEMPRE xᵢ. A entrada mássica é convertida antes de qualquer cálculo.
Não misturar bases: uma requisição tem uma única base.

#### 2.2.2 Origem das massas atômicas no repositório [FATO]

| Origem | Arquivo e campo | Cobertura | Fonte | Estado |
|---|---|---|---|---|
| Tabela periódica | `database/seeds/tabela_periodica/elementos.json`, propriedade `peso_atomico_padrao` (unidade registrada "adimensional") | 84 elementos (Mn incluído: 54,938) | `ciaaw_2024` (CIAAW, Atomic Weights 2021 + revisões 2024; DOI 10.1515/pac-2019-0603, conforme `FONTES.txt`) | `aguardando_validacao` |
| Seed de metais | `database/seeds/cristalografia/metais.json`, campo `peso_g_mol` | 15 metais | "callister" (sem edição nem página, CR-10) | `aguardando_validacao` (fixado no código) |
| Seed v1.4 | `propriedades_v14.json`, `massa_atomica` | só C, H, N | sem fonte | `rascunho` |

[FATO] `FONTES.txt` registra massas desatualizadas no seed de metais: Zn 65,41 × 65,38 e Mo 95,94 × 95,95 (CIAAW).
[FATO] Efeito medido da escolha: diferença máxima de 0,0019 ponto percentual em massa (AlCoCrFeNi e CoCrFeNi).

**Decisão:** usar `peso_atomico_padrao` (CIAAW) como única fonte de massa do HEA. Hipótese declarada: o peso atômico padrão
(adimensional) é usado numericamente como massa molar em g/mol (a constante de massa molar difere de 1 g/mol em ordem de 1e-9
relativo após o SI de 2019, sem efeito na 4ª casa). NÃO usar `massa_isotopica_referencia` (34 elementos sem peso padrão, como Po, Tc):
é a massa de um isótopo, não a do elemento natural. Para esses elementos a conversão fica indisponível.

**Conflito a resolver (consulta C-02):** `FONTES.txt` (seção 5) e o ADR-018 dizem que a tabela periódica é dado de REFERÊNCIA e que os
motores leem só o repositório de materiais. Usar a CIAAW no motor HEA muda essa decisão de arquitetura. Alternativa sem mudar o ADR:
massas de `metais.json` (só 15 metais; Mn sem massa).

**Política de dados:** a massa passa pela `PoliticaDados` como os demais dados. Em produção, enquanto estiver `aguardando_validacao`:
entrada atômica → `comp_massa_pct = null` com motivo; entrada mássica → 422 `DADO_NAO_VALIDADO`.

#### 2.2.3 Saída (sempre as duas bases, quando possível)

| Campo | Tipo | Unidade | Nulo? | Conteúdo |
|---|---|---|---|---|
| `base_entrada` | texto | — | não | `"atomica"` ou `"massica"` |
| `soma_informada` | número | unidade da entrada | não | soma das quantidades recebidas (> 0) |
| `fracoes` (existente) | objeto | fração atômica | não | sem arredondar |
| `comp_percent` (existente) | objeto | at.% | não | 4 casas; documentar que é ATÔMICA |
| `fracoes_massa` | objeto | fração mássica | sim | sem arredondar |
| `comp_massa_pct` | objeto | % em massa | sim | 4 casas |
| `massa_molar_media` | número | g/mol | sim | M̄, 4 casas |

Quando nulos, `indisponiveis["comp_massa"]` traz o motivo e `dados_faltantes` lista os elementos sem massa. As massas usadas entram em
`procedencia.dados_usados` (`codigo: "massa_atomica"`, unidade `g/mol`, fonte `ciaaw_2024`).

#### 2.2.4 Testes

- Ida e volta: at → massa → at reproduz xᵢ com erro absoluto ≤ 1e-12 (medido nesta tarefa: ≤ 5,6e-17 em 4 ligas).
- Somas: |Σxᵢ − 1| ≤ 1e-12 e |Σwᵢ − 1| ≤ 1e-12 nas frações NÃO arredondadas. Os percentuais arredondados a 4 casas podem somar
  100 ± 0,0001·n/2; a interface não deve "corrigir" o último valor.
- Equivalência: enviar `base: "massica"` com as `fracoes_massa` devolvidas (não arredondadas) reproduz os mesmos ΔS_mix, δ, VEC e T_m
  (tolerância 1e-9 relativa). Não usar `comp_massa_pct` nesse teste: o arredondamento a 4 casas propaga erro maior.
- Caso sintético e casos reais: seção 2.9.

### 2.3 Cobertura de dados elementares

[FATO] Levantamento executado (`hea_cobertura.py`) nos seeds:

| Dado | Onde está (arquivo, campo) | Cobertura | Unidade | Fonte / estado |
|---|---|---|---|---|
| Raio atômico metálico | `cristalografia/metais.json`, `raio_nm` | 15: Fe Cr Mo W Cu Al Ni Ag Au Pb Mg Ti Zn Co Po | nm | "callister" sem edição/página; `aguardando_validacao` |
| Raio de van der Waals | `tabela_periodica/elementos.json`, `raio_van_der_waals` | 99 de 118 | pm | PubChem; `aguardando_validacao` |
| T_f (usada hoje) | `cristalografia/propriedades_v14.json`, `temperatura_fusao` | os mesmos 15 | °C | **sem fonte**; `rascunho` |
| T_f (não usada) | `tabela_periodica/elementos.json`, `temperatura_fusao` | 103 de 118 (Mn, V, Nb, Ta, Zr, Hf incluídos) | K | PubChem; `aguardando_validacao` |
| VEC | `hea/vec.json`, `vec` | 13 (os 15 menos Pb e Po) | e/átomo | "guo2011"; `aguardando_validacao` |
| Grupo e configuração eletrônica | `tabela_periodica/elementos.json`, `grupo`, `configuracao_eletronica` | 118 | — | IUPAC / PubChem |
| Massa atômica | ver 2.2.2 | 84 (CIAAW) ou 15 (seed) | — / g/mol | ver 2.2.2 |
| ΔH de mistura por par | — | **nenhum** | — | Q-01 |

Dá para ampliar SEM inventar dado? Resposta por grandeza, com o exemplo do Mn:

| Grandeza | Mn hoje | Pode ampliar com o que já está no repositório? |
|---|---|---|
| Massa atômica | ausente no HEA | **Sim**: `peso_atomico_padrao` = 54,938 (CIAAW). Depende de C-02. |
| T_f → T_m | ausente no HEA | **Sim**: `temperatura_fusao` = 1519 K (PubChem). Depende de C-03 (fonte única de T_f) para não misturar v1.4 e PubChem na mesma média. |
| VEC | ausente | **Condicional**: a tabela não tem VEC, mas tem o grupo. Para metais de transição (grupos 3 a 12), VEC na convenção s + d é igual ao número do grupo; conferi que os 13 valores do seed obedecem à regra. Derivar Mn = 7 pela regra é dedução de dado com fonte + convenção declarada, não invenção, MAS exige parecer do materials-science-specialist e conferência da tabela de Guo et al. pelo auditor (C-04). A regra NÃO deve ser estendida ao bloco p além do Al (Pb, Sn, Si...): a contagem ali é ambígua. |
| Raio metálico → δ | ausente | **Não.** O único raio dos 118 é o de van der Waals, que é outra grandeza e não pode entrar em δ. **Pendência P-HEA-01**: tabela de raios atômicos metálicos com fonte única para todos os elementos de interesse (no mínimo Mn, V, Nb, Ta, Zr, Hf, além dos 15). Sugestão ao auditor: a tabela de raios usada na literatura de HEA para δ (candidata, citada de memória, **não verificada**: Senkov, O. N.; Miracle, D. B. *Mater. Res. Bull.* 36, 2183, 2001) e a de Kittel. |

Consequências:

1. Com C-02, C-03 e C-04 aprovados, a liga de Cantor passa a devolver ΔS_mix, T_m, VEC e composição em massa; **δ continua
   indisponível** até P-HEA-01. ΔH_mix e Ω dependem de Q-01.
2. **Fonte única por grandeza em cada cálculo.** δ é sensível à escala de raios: misturar Callister para uns elementos e outra tabela
   para outros produz um δ sem significado. Regra: se os raios usados num cálculo vierem de mais de uma fonte, δ = `null` com o motivo
   "raios de fontes diferentes". O mesmo vale para T_f.
3. δ publicado na literatura só é reproduzível com a MESMA tabela de raios do artigo. Os valores de δ do motor com raios do Callister
   são regressão interna, não valor de literatura (ver 2.9).
4. O bootstrap deve informar, por elemento, o que existe: `tem_raio`, `tem_fusao`, `tem_vec`, `tem_massa`; e `raio_nm` passa a ser
   anulável (hoje é obrigatório, o que impede listar o Mn).

### 2.4 ΔH_mix e Ω (condicionais)

Nenhum valor de entalpia binária é citado neste parecer: a matriz não existe no repositório (Q-01) e eu não a tenho como dado.

#### 2.4.1 Equações

- ΔH_mix = Σ_{i<j} 4·ΔH_ij·xᵢ·xⱼ, em kJ/mol, com ΔH_ij = entalpia de mistura do par i–j na composição equiatômica, do modelo de
  Miedema (tabela de Takeuchi & Inoue, *Mater. Trans.* 46, 2817, 2005; uso em HEA: Zhang et al., *Adv. Eng. Mater.* 10, 534, 2008).
  Referências **não verificadas** nesta tarefa. A soma percorre os n(n−1)/2 pares não ordenados; não há termo i = i.
- Ω = T_m·ΔS_mix / |ΔH_mix| (Yang & Zhang, *Mater. Chem. Phys.* 132, 233, 2012; **não verificada**). Com as unidades do motor:
  Ω = T_m[K]·ΔS_mix[J/(mol·K)] / (1000·|ΔH_mix|[kJ/mol]). Adimensional. T_m = Σ xᵢ·T_f,ᵢ (regra das misturas).
- Propriedades algébricas, verificáveis sem dado externo (base dos testes de 2.9): binária equimolar → ΔH_mix = ΔH_AB; liga equimolar
  de n elementos com todos os pares iguais a h → ΔH_mix = 2h(n−1)/n.

#### 2.4.2 Regra condicional

1. Montar a lista dos n(n−1)/2 pares da liga (símbolos canônicos, par em ordem alfabética, chave `"A-B"`).
2. Para cada par, pedir o valor ao repositório, passando pela `PoliticaDados` (em produção, só `validado`).
3. Se **todos** os pares têm valor utilizável → calcular ΔH_mix. Cada par usado entra em `procedencia.dados_usados`
   (`simbolo: "Co-Cr"`, `codigo: "entalpia_mistura_par"`, valor, `kJ/mol`, estado, fonte).
4. Se **qualquer** par falta ou não é utilizável → `dH = null`. NÃO se calcula soma parcial (seria um número errado com aparência de
   resultado) e NÃO se assume ΔH_ij = 0 para o par ausente.
5. Ω só é calculado com ΔH_mix, ΔS_mix e T_m disponíveis.

#### 2.4.3 ΔH_mix → 0

- Se |ΔH_mix| < 1e-9 kJ/mol: `omega = null`, com `indisponiveis["omega"]` = "Ω não é definido para ΔH_mix = 0 (divisão por zero).
  No modelo, a mistura é atérmica e o termo entrópico domina em qualquer temperatura."
- Se 1e-9 ≤ |ΔH_mix| < 1 kJ/mol: Ω é calculado e devolvido, com o aviso "ΔH_mix próximo de zero: Ω fica muito grande e muito
  sensível à incerteza das entalpias binárias; não compare valores de Ω nessa faixa." O limite de 1 kJ/mol é escolha heurística
  minha, a confirmar pelo materials-science-specialist (C-05).
- A interface mostra Ω com no máximo 3 algarismos significativos e "> 1000" acima de 1000; o valor completo fica na API.

#### 2.4.4 Falta de par: resposta

- `dH: null`, `omega: null`, `pares_faltantes: ["Co-Mn", "Cr-Mn", ...]` (ordenada; lista vazia quando nada falta).
- `indisponiveis["dH"]`: "ΔH_mix indisponível: faltam entalpias de mistura com fonte para {k} de {m} pares: {lista}." Quando a matriz
  inteira não existe: "ΔH_mix indisponível: a tabela de entalpias de mistura por par (modelo de Miedema) ainda não foi cadastrada
  com fonte. Nenhum valor é estimado."
- `indisponiveis["omega"]`: "Ω depende de ΔH_mix, que está indisponível." (ou de T_m, conforme o caso).
- Sem códigos internos ("Q-01") no texto mostrado ao usuário.

#### 2.4.5 Formato esperado do dado de par (seed sugerido: `database/seeds/hea/entalpias_binarias.json`)

```json
{
  "versao_dados": "AAAA.MM.N-hea-dh",
  "grandeza": "entalpia de mistura do par na composição equiatômica (modelo de Miedema)",
  "unidade": "kJ/mol",
  "fontes": {"takeuchi2005": {"citacao": "...", "doi": "...", "tabela": "...", "acessado_em": "..."}},
  "pares": [
    {"a": "Co", "b": "Cr", "valor": 0.0, "unidade": "kJ/mol", "estado": "aguardando_validacao",
     "fonte": "takeuchi2005", "origem": "transcrição da tabela N, linha/coluna ..."}
  ]
}
```

(`"valor": 0.0` acima é só marcador de formato, não é dado.) Regras de carga, com erro de dados em caso de violação:

- par NÃO ordenado e único: `a < b` em ordem alfabética, `a ≠ b`; `Co-Cr` e `Cr-Co` no mesmo arquivo é duplicata;
- `a` e `b` existem na tabela periódica; `valor` finito, em kJ/mol; sinal como na fonte (negativo = exotérmico);
- `estado` ∈ estados já usados (`rascunho`, `aguardando_validacao`, `validado`, ...); `validado` exige `fonte`;
- cada registro guarda de onde foi transcrito (`origem`), para a revisão humana;
- sem valores na diagonal e sem preenchimento de pares ausentes.

Interface de leitura proposta ao backend: `entalpia_par(a: str, b: str) -> Optional[ValorReferencia]`, simétrica.
A transcrição precisa de conferência dupla (auditor + revisor humano): um sinal trocado inverte a interpretação.

### 2.5 Entalpia de mistura, Gibbs de mistura e energia de formação

Quatro grandezas diferentes, que a interface deve mostrar com nomes diferentes. Texto para o glossário do módulo (campo `definicoes`
do bootstrap, seção 2.6.5). Referências de literatura: **não verificadas** nesta tarefa.

| | (1) Entalpia de mistura do modelo, ΔH_mix | (2) Termo entrópico ideal, −T·ΔS_mix | (3) Energia livre de Gibbs de mistura do modelo, ΔG_mix(T) | (4) Energia de formação, ΔH_f / ΔG_f |
|---|---|---|---|---|
| Definição | Σ_{i<j} 4·ΔH_ij·xᵢxⱼ (solução regular com parâmetros de Miedema) | −T·(−R·Σ xᵢ ln xᵢ) | ΔH_mix − T·ΔS_mix (ΔS_mix ideal) | Energia (ou entalpia, ou Gibbs) de uma FASE ou COMPOSTO definido, com estrutura cristalina definida, menos a dos elementos nos estados de referência |
| Unidade | kJ/mol (de átomos) | kJ/mol | kJ/mol | kJ/mol ou eV/átomo |
| Estado de referência | componentes puros, não misturados (os valores de Miedema usados na literatura de HEA são do líquido; a confirmar pelo auditor) | componentes puros, não misturados | componentes puros, não misturados | elementos na fase estável de referência (convenção SER, 298,15 K e 1 bar, em CALPHAD; 0 K em DFT) |
| Condições | só composição; sem dependência de T nem de P no modelo | composição e T; P não modelada | composição e T; parâmetros constantes em T; P não modelada | T, P e estrutura da fase |
| Significado | sinal e intensidade da afinidade química média entre os componentes: muito negativa sugere tendência a ordenação/compostos; positiva, tendência à separação | quanto a entropia configuracional ideal reduz a energia livre a cada T | balanço, dentro do modelo, entre afinidade química e entropia de uma solução desordenada hipotética | estabilidade de uma fase específica em relação aos elementos; base de diagramas de fases |
| O que NÃO é | não é entalpia medida por calorimetria; não é a entalpia de formação de nenhuma fase; não é CALPHAD | não é ΔG; não inclui entropia vibracional, magnética nem eletrônica; ignora ordem de curto alcance | ΔG_mix < 0 NÃO prova fase única nem estabilidade: a estabilidade exige comparar com a energia de Gibbs das fases concorrentes (intermetálicos, separação de fases); não é energia de formação; não é diagrama de fases | não é ΔH_mix nem ΔG_mix do modelo |
| Natureza | estimativa por modelo | analítico (exato na hipótese de solução ideal) | estimativa por modelo | cálculo de primeiros princípios, CALPHAD ou medida |
| O sistema calcula? | só com a matriz de pares completa (2.4) | **sempre** (qualquer composição válida, inclusive em produção) | só com ΔH_mix | **não** |
| Fonte do modelo | Miedema; Takeuchi & Inoue (2005); Zhang et al. (2008) | entropia configuracional de Boltzmann, solução ideal | modelo de solução regular; uso em HEA: Yang & Zhang (2012), em que Ω > 1 equivale a T_m·ΔS_mix > \|ΔH_mix\| | DFT, CALPHAD, calorimetria |

Regras de apresentação:

1. **Energia de formação:** [FATO] o sistema não pode calculá-la: não há DFT, CALPHAD, base TDB nem base termoquímica no repositório
   ou no ambiente (linha de base do supervisor). A API devolve `energia_formacao: null` e
   `indisponiveis["energia_formacao"]` = "Este sistema não calcula energia de formação: exige cálculo de primeiros princípios (DFT),
   CALPHAD ou medida calorimétrica da fase. ΔH_mix e ΔG_mix do modelo não a substituem." A interface mostra a linha "Energia de
   formação: indisponível" com esse texto. É proibido rotular ΔH_mix ou ΔG_mix como "energia de formação".
2. Rótulos obrigatórios: "ΔH_mix (modelo de Miedema, solução regular)", "−T·ΔS_mix (ideal)", "ΔG_mix do modelo". Nunca "energia livre
   da liga", "estabilidade" ou "ΔG" sem qualificação.
3. **Faixa de temperatura da curva:** de 300 K até T_sup, passo de 50 K, com T_sup = T_m arredondado para cima ao múltiplo de 100 K
   quando T_m existe; senão 2000 K, com o aviso "T_m indisponível: faixa de temperatura nominal". T_m é marcado no gráfico como
   "T_m (regra das misturas; não é solidus nem liquidus)". O modelo não descreve transformação de fase; acima de T_m real a liga é líquida.
4. **Temperatura de cruzamento (só quando ΔH_mix > 0):** T* = 1000·ΔH_mix/ΔS_mix (K), temperatura acima da qual ΔG_mix do modelo é
   negativo. Relação exata: Ω = T_m/T* para ΔH_mix > 0. Para ΔH_mix ≤ 0, ΔG_mix do modelo é negativo em toda T > 0 e
   `T_cruzamento_k = null` (com motivo "não se aplica: ΔH_mix ≤ 0").
5. Pressão: declarar "pressão não modelada (fases condensadas)". Não escrever "1 atm" como se fosse parâmetro do cálculo.

### 2.6 Gráficos e campos novos da API

#### 2.6.1 Avaliação da zona "−15 < ΔH < 5 kJ/mol; δ < 6,6 %" de `HeaCharts.tsx`

- [FATO] Os números estão fixos no frontend (`HeaCharts.tsx:66`, `:69`) e na legenda (`04-panels.tsv:94`). O comentário do arquivo
  (`HeaCharts.tsx:5`) os atribui ao "HEA Virtual Lab v1.17". Não há citação de literatura para o retângulo em nenhum arquivo lido.
- [FATO] O motor cita δ ≤ 6,6 % junto com Ω ≥ 1,1 (Yang & Zhang, 2012), ou seja, no plano δ × Ω, não no plano δ × ΔH.
- [INFERÊNCIA, de memória, **não verificada**] A faixa −15 a 5 kJ/mol é a geralmente atribuída a Zhang et al. (2008), que usam um limite
  de δ próprio (menor que 6,6 %; não cito o número por não tê-lo conferido). Há outra proposta com faixas diferentes de ΔH_mix e δ
  (Guo & Liu, *Prog. Nat. Sci.: Mater. Int.* 21, 433, 2011). O retângulo desenhado parece combinar o ΔH de um critério com o δ de outro.
- **Conclusão:** a zona, como está, **não tem fonte única rastreável**. Não deve ser desenhada nem rotulada "solução sólida" até o
  auditor bibliográfico confirmar cada limite na fonte (C-01). O título "Mapa de estabilidade" também deve sair: o mapa é de triagem.

#### 2.6.2 Regra geral dos gráficos

1. O front só desenha o que a API devolve: pontos, curvas E faixas de critério. Nenhum limiar fixo no frontend.
2. Cada faixa vem de `criterios` (2.6.5) com `fonte` e `verificada`. Faixa com `verificada = false` é desenhada tracejada e rotulada
   "limiar citado, conferência pendente"; a decisão de exibir ou ocultar essas faixas em produção é do supervisor (C-01).
3. Todo gráfico traz, na legenda ou em nota fixa: grandezas e unidades dos eixos, natureza de cada série, condições, e a frase
   "Critérios empíricos de triagem. Não provam estabilidade nem fase única."
4. Sem dado, o gráfico NÃO é desenhado (nem eixos com pontos fictícios): aparece "Indisponível" + o motivo específico vindo de
   `indisponiveis` (hoje a mensagem é genérica) + a indicação do gráfico alternativo disponível.
5. Pontos de comparação (`samples`) são ligas calculadas PELO MESMO MOTOR, rotuladas "calculado por este modelo". Não são pontos
   experimentais. Fase observada em experimento só aparece com citação (A-14).
6. Tabela de dados acessível por gráfico (já existe) com as mesmas unidades do eixo.

#### 2.6.3 Gráficos

| ID | Gráfico | Eixos e unidades | Séries | Faixas de critério (fonte; todas **não verificadas** nesta tarefa) | Natureza | Disponível quando | Sem dado |
|---|---|---|---|---|---|---|---|
| G-A | Termo entrópico ideal × temperatura | x: T (K); y: −T·ΔS_mix (kJ/mol) | liga analisada (reta pela origem, inclinação −ΔS_mix); guias analíticas −T·R·ln n para n = 2..6 (equimolares) | linha ΔS_mix = 1,5R (definição por entropia: Yeh, 2006; Miracle & Senkov, *Acta Mater.* 122, 448, 2017) | analítico (solução ideal) | **sempre** | não se aplica |
| G-B | Mapa de triagem δ × VEC | x: δ (%); y: VEC (e/átomo) | liga analisada; `samples` | δ = 6,6 % (Yang & Zhang, 2012, definido junto com Ω); VEC = 6,87 e 8,0 (Guo et al., 2011) | ponto: estimativa por modelo; faixas: empíricas | δ e VEC disponíveis | "Indisponível: δ (motivo)" e/ou "VEC (motivo)" |
| G-C | Mapa de triagem δ × ΔH_mix | x: δ (%); y: ΔH_mix (kJ/mol) | liga analisada; `samples` com ΔH | só as que o auditor confirmar (2.6.1); até lá, nenhuma zona preenchida | ponto: estimativa por modelo; faixas: empíricas | δ e ΔH_mix | "Indisponível: ΔH_mix (faltam pares: ...)"; sugerir G-B |
| G-D | ΔG_mix do modelo × temperatura | x: T (K); y: energia (kJ/mol) | três curvas da liga: ΔH_mix (constante), −T·ΔS_mix e ΔG_mix; linha zero; marca de T_m; marca de T* quando existir | nenhuma | estimativa por modelo (ΔH) + analítico (−TΔS) | ΔH_mix | "Indisponível: ΔH_mix (motivo)"; mostrar G-A no lugar |
| G-E (opcional) | Mapa de triagem δ × Ω | x: δ (%); y: Ω (escala logarítmica) | liga analisada; `samples` | Ω = 1,1 e δ = 6,6 % (Yang & Zhang, 2012): é o plano em que esse critério foi proposto | empírico | δ e Ω | "Indisponível: Ω (motivo)" |

Condições a declarar em todos: frações atômicas; ΔS_mix ideal; T_m pela regra das misturas; pressão não modelada; dados com o estado
de validação mostrado. Ordem recomendada na tela: G-A e G-B (existem hoje sem ΔH), depois G-C e G-D (aparecem quando Q-01 for resolvida).
Nenhum gráfico é classificado como "experimental": o sistema não tem dados experimentais de fase.

#### 2.6.4 Campos novos em `POST /hea/analyses` (resposta)

Campos existentes permanecem (`dS`, `dH`, `delta`, `omega`, `VEC`, `Tm`, `comp_percent`, `fracoes`, `fase`, `veredito`, `interpretacao`,
`indisponiveis`, `procedencia`, `gibbs`). Novos (além dos de 2.2.3):

| Campo | Tipo | Unidade | Nulo? | Conteúdo |
|---|---|---|---|---|
| `dS_R` | número | adimensional | não | ΔS_mix/R, 4 casas |
| `classe_entropia` | `"baixa"` \| `"media"` \| `"alta"` | — | não | ΔS_mix < 1R; 1R ≤ ΔS_mix < 1,5R; ≥ 1,5R (classificação por entropia; Yeh, 2006; não verificada) |
| `raio_medio_nm` | número | nm | sim | r̄ = Σ xᵢrᵢ |
| `pares_faltantes` | lista de texto | — | não (pode ser vazia) | pares `"A-B"` sem entalpia utilizável |
| `dados_faltantes` | lista de `{simbolo, codigo, situacao}` | — | não (pode ser vazia) | ver 2.1.5 |
| `curva_T` | lista de `{T, menos_TdS, dG}` | K; kJ/mol; kJ/mol | lista nunca nula; `dG` nulo em cada ponto quando ΔH_mix falta | 300 K a T_sup, passo 50 K (2.5); 4 casas |
| `T_sup_k` | número | K | não | limite superior da curva |
| `dG_Tm` | número | kJ/mol | sim | ΔG_mix do modelo em T_m |
| `T_cruzamento_k` | número | K | sim | T* (2.5, regra 4) |
| `ponto_T` | `{T, menos_TdS, dG}` | K; kJ/mol | sim | só quando `temperatura_k` foi enviada |
| `energia_formacao` | nulo | — | sempre nulo nesta versão | ver 2.5, regra 1 |
| `criterios` | lista (formato abaixo) | — | não | critérios avaliados para esta liga |
| `triagem` | `{estado, texto}` | — | não | 2.7; `veredito` passa a repetir `triagem.texto` (compatibilidade) |
| `vec_aplicavel` | booleano | — | não | 2.7.2 |
| `classes` | objeto grandeza → classe | — | não | ex.: `{"dS":"analitico","delta":"estimativa_modelo","VEC":"estimativa_modelo","Tm":"estimativa_modelo","dH":"estimativa_modelo","omega":"estimativa_modelo","curva_T.menos_TdS":"analitico"}` |

`gibbs` (existente, `[{T, G}]` com G em J/mol): manter por compatibilidade, preenchido a partir de `curva_T` quando ΔG existe, e
marcar como obsoleto no contrato. A unidade de trabalho passa a ser kJ/mol em `curva_T`, para o front não converter unidades.
Toda grandeza nula ou lista vazia tem chave em `indisponiveis`: `dH`, `omega`, `delta`, `VEC`, `Tm`, `comp_massa`, `gibbs`, `dG_Tm`,
`T_cruzamento`, `energia_formacao`, `dureza`, `ductilidade`.

Item de `criterios`:

| Campo | Tipo | Exemplo |
|---|---|---|
| `codigo` | texto | `"delta_yang_zhang"`, `"omega_yang_zhang"`, `"vec_cfc_guo"`, `"vec_ccc_guo"`, `"ds_alta_entropia"` |
| `grandeza` | texto | `"delta"` |
| `operador` | `"<="` \| `">="` \| `"<"` \| `">"` | `"<="` |
| `limiar` | número | `6.6` |
| `unidade` | texto | `"%"` |
| `valor` | número ou nulo | valor calculado da liga |
| `atende` | booleano ou nulo | nulo quando `valor` é nulo ou o critério não se aplica |
| `aplicavel` | booleano | falso fora do domínio (2.7.2) |
| `natureza` | `"empirico"` \| `"definicao"` | |
| `fonte` | texto | citação completa |
| `verificada` | booleano | conferida pelo auditor bibliográfico na fonte |
| `motivo` | texto ou nulo | por que não foi avaliado |

#### 2.6.5 Campos novos em `GET /hea/bootstrap`

| Campo | Tipo | Conteúdo |
|---|---|---|
| `elements[símbolo]` | `{simbolo, nome, numero_atomico, categoria, raio_nm (anulável), tem_raio, tem_fusao, tem_vec, tem_massa}` | todos os elementos aceitos na entrada (118), para a interface mostrar ANTES do cálculo o que ficará indisponível |
| `criterios` | lista no formato de 2.6.4, sem `valor`/`atende` | limiares e fontes, para as faixas dos gráficos. Substitui o uso de `reference` |
| `reference` (existente) | — | manter por compatibilidade; deixar de ser exibido como "liga de referência" (A-06) |
| `entalpias` | `{disponivel: bool, n_pares: int, fonte: texto ou nulo, estado: texto ou nulo}` | situação da matriz de ΔH |
| `samples` | lista de respostas de análise | os `alloys` de exemplo calculados pelo próprio motor, com a mesma política de dados |
| `definicoes` | lista de `{codigo, nome, simbolo, unidade, referencia, condicoes, significado, nao_e, natureza, disponivel}` | glossário de 2.5 (4 itens) + ΔS_mix, δ, VEC, Ω, T_m (2.7.4) |
| `avisos_fixos` | lista de texto | os avisos obrigatórios de 2.7.1 |

#### 2.6.6 Integração, atualização e exportação (itens f e g)

1. Estado da triagem lido de `triagem.estado`, nunca do prefixo do texto. Análise concluída é registrada como sucesso no terminal,
   qualquer que seja o estado da triagem.
2. A tabela "Comparação com a liga de referência" vira "Critérios de triagem": colunas critério, valor, condição (operador + limiar),
   atende (sim / não / não avaliado), fonte. Sem coluna "diferença".
3. Cartão de métrica nulo mostra "indisponível" + motivo curto (não "—" isolado, não 0).
4. Resultado desatualizado: quando a composição ou a base no editor diferem das do resultado exibido, a área de resultados recebe a
   marca "Resultado desatualizado: refere-se a {composição analisada}" até nova análise.
5. Exportação (se implementada nesta rodada): JSON da resposta integral (com `procedencia`) e CSV de `curva_T` e de `criterios`, com
   cabeçalho de unidades, versão do motor, versão dos dados e avisos. Resultado demonstrativo não é exportável.
6. Ponte para o CrystaLab: abertura direta só quando `vec_aplicavel` é verdadeiro e há `estrutura_sugerida`; o texto usa
   "estrutura sugerida pelo critério empírico de VEC", não "fase prevista".
7. Histórico: gravar nos parâmetros também a composição canônica normalizada e a base (A-20).

### 2.7 Veredito de triagem, avisos e limites de validade

O resultado separa quatro níveis, e a interface deve mostrá-los em blocos distintos:
(a) **cálculo** do indicador (número + unidade + classe); (b) **interpretação por critério empírico** (`criterios`);
(c) **triagem** (`triagem`, `fase`): sugestão, nunca previsão garantida; (d) **confirmação experimental**: o sistema não tem;
aparece como "sem confirmação experimental registrada" (ou a citação, quando o auditor a fornecer para as ligas de exemplo).

#### 2.7.1 Estado e texto da triagem

Critério conjunto usado: Ω ≥ 1,1 **e** δ ≤ 6,6 % (Yang & Zhang, 2012; não verificada). Vocabulário proibido: "ESTÁVEL", "estabilidade",
"fase prevista", "garante", "forma solução sólida".

| `triagem.estado` | Regra | `triagem.texto` (modelo) |
|---|---|---|
| `favoravel` | os dois critérios avaliados e atendidos | "TRIAGEM FAVORÁVEL à solução sólida desordenada: Ω = {Ω} ≥ 1,1 e δ = {δ} % ≤ 6,6 % (critério empírico de Yang & Zhang, 2012). É um indicador de triagem: não comprova fase única nem estabilidade." |
| `desfavoravel` | pelo menos um critério avaliado e NÃO atendido (a conjunção já falha, mesmo com o outro indisponível) | "TRIAGEM DESFAVORÁVEL à solução sólida desordenada: {δ = {δ} % > 6,6 %}{; Ω = {Ω} < 1,1}. O critério empírico de Yang & Zhang (2012) não é atendido{; Ω não foi avaliado ({motivo})}. É um indicador de triagem: não comprova a formação de intermetálicos nem de fase amorfa." |
| `inconclusiva` | nenhum critério falhou e pelo menos um não pôde ser avaliado; ou há elemento não metálico; ou dados de fontes mistas | "TRIAGEM INCONCLUSIVA: {δ = {δ} % ≤ 6,6 % (atendido); }{Ω não pôde ser avaliado ({motivo})}. O critério empírico de Yang & Zhang (2012) exige os dois indicadores." |

Mudança em relação ao motor 1.0.0: hoje δ > 6,6 % sem Ω sai como "INCONCLUSIVO — δ desfavorável"; pela lógica da conjunção passa a
`desfavoravel`. Os testes que conferem o prefixo "INCONCLUSIVO" terão de ser atualizados junto (backend).
Apresentação: `favoravel` e `desfavoravel` com ícone e cor NEUTROS de informação (não verde "aprovado" nem vermelho "erro");
`inconclusiva` em cinza. Nunca registrar a triagem como erro.

Avisos obrigatórios (`avisos_fixos` do bootstrap, mostrados junto de todo resultado):

1. "ΔS_mix, δ, ΔH_mix, Ω e VEC são critérios empíricos de triagem, ajustados a conjuntos limitados de ligas, em geral no estado bruto
   de fusão. Não são prova de estabilidade termodinâmica nem de fase única."
2. "A fase real depende de processamento, temperatura, tempo e taxa de resfriamento. A confirmação exige experimento (difração de
   raios X, microscopia) ou cálculo termodinâmico (CALPHAD, DFT), que este sistema não realiza."
3. "Critérios diferentes podem discordar entre si; quando isso acontece, a discordância é mostrada, não resolvida."

Avisos condicionais (em `procedencia.avisos`): dados não validados usados (já existe); menos de 5 elementos (já existe); elemento não
metálico (2.1.5); zeros descartados; critério de VEC fora do domínio (2.7.2); ΔH_mix próximo de zero (2.4.3); T_m indisponível na curva;
valor próximo do limiar (2.7.3); quando `criterios` têm `atende` verdadeiro e falso ao mesmo tempo: "Os critérios discordam: {lista}."

#### 2.7.2 Domínio do critério de VEC (corrige A-07)

VEC é sempre calculado quando há dados (é só uma média). A **classificação de estrutura** pelo critério de Guo et al. (2011) só é
emitida com `vec_aplicavel = true`, que exige TODAS as condições:

1. VEC disponível;
2. ΔS_mix ≥ 1R (liga concentrada de múltiplos elementos principais: média ou alta entropia). Exclui ligas diluídas e binárias
   (Fe com 0,1 % de Ni tem 0,008R; binária equimolar tem 0,693R);
3. todos os elementos são metais de transição dos grupos 4 a 11 ou Al;
4. `triagem.estado` ≠ `desfavoravel` (o critério de VEC pressupõe que a liga forma solução sólida).

As condições 2 e 3 são proposta minha de delimitação conservadora, **a confirmar** pelo materials-science-specialist e pelo auditor
(conjunto de ligas de Guo et al.): consulta C-05. Texto de `fase`:

| Situação | `fase` | `estrutura_sugerida` |
|---|---|---|
| aplicável, VEC ≥ 8,0 | "CFC sugerida pelo critério empírico de VEC (VEC ≥ 8,0; Guo et al., 2011)" | `"CFC"` |
| aplicável, VEC < 6,87 | "CCC sugerida pelo critério empírico de VEC (VEC < 6,87; Guo et al., 2011)" | `"CCC"` |
| aplicável, intermediário | "CFC + CCC sugeridas pelo critério empírico de VEC (6,87 ≤ VEC < 8,0; Guo et al., 2011)" | ausente |
| não aplicável | "não avaliada: critério de VEC fora do domínio de validade ({motivo})" | ausente |
| VEC indisponível | "não avaliada: VEC indisponível" | ausente |

Cuidado de integração: `transfer.ts:27-32` procura as siglas CFC, CCC, HC e CS no texto de `fase`. Os textos de "não avaliada" e os
motivos não podem conter essas siglas como palavras isoladas. Casos de teste: Al+Mg, Mg+Ti+Zn, Fe99,9Ni0,1 e Ag+Au+Cu+Zn → não aplicável;
CoCrFeNi → CFC; CrMoW → CCC; AlCoCrFeNi → CFC + CCC.

#### 2.7.3 Comparação com limiares

- Comparar o valor NÃO arredondado, com tolerância ε = 1e-9: VEC ≥ 8,0 − ε; VEC < 6,87 − ε; δ ≤ 6,6 + ε; Ω ≥ 1,1 − ε.
  Médias calculadas com `math.fsum` (A-21).
- `criterios[].proximo_do_limiar = true` quando |valor − limiar| ≤ 2 % do limiar, com o aviso "{grandeza} está a menos de 2 % do
  limiar: a classificação pode mudar com a incerteza dos dados de entrada." A margem de 2 % é heurística (C-05).

#### 2.7.4 Limites de validade de cada descritor (texto para `definicoes`)

| Descritor | Hipóteses | Limites de validade |
|---|---|---|
| ΔS_mix ideal | solução aleatória ideal, uma única sub-rede | superestima a entropia quando há ordem (fases ordenadas, ordem de curto alcance, várias sub-redes); não inclui termos vibracional, magnético e eletrônico; não depende de quais são os elementos; o limite 1,5R é definição, não critério de fase |
| δ | raios atômicos fixos por elemento | o valor depende da tabela de raios (o raio muda com coordenação e vizinhança); só é comparável entre cálculos com a mesma tabela; δ pequeno não garante solução sólida |
| T_m (regra das misturas) | média linear das temperaturas de fusão | não é solidus nem liquidus; pode errar por centenas de kelvins (por exemplo, em sistemas com eutético); serve só como escala de temperatura em Ω |
| VEC | contagem s + d por elemento (convenção de Guo et al.) | critério estatístico para ligas que JÁ formam solução sólida; não indica fase HC, intermetálicos nem fases ordenadas; há exceções relatadas; ver domínio em 2.7.2 |
| ΔH_mix | solução regular, só interações de pares, parâmetros de Miedema constantes | modelo semiempírico; sem termos ternários; sem dependência de T; incerteza da ordem de kJ/mol (qualitativo, não verificado) |
| Ω | herda T_m, ΔS_mix ideal e ΔH_mix | diverge quando ΔH_mix → 0; o limiar 1,1 é estatístico |
| ΔG_mix do modelo | ver 2.5 | não compara fases; não é diagrama de fases |

Geral: os critérios foram ajustados sobretudo a ligas brutas de fusão; não descrevem cinética, tratamento térmico nem decomposição
em recozimentos longos.

### 2.8 Modo demonstrativo

[FATO, por leitura de `frontend/src/services/adapters/heaDemo.ts`, `HeaModule.tsx`, `HeaCharts.tsx`, `handlers.ts`, `app/boot.ts`]

- `analyzeDemo` sorteia, com semente derivada do nome e da composição: ΔS, ΔH, δ, Ω, VEC, T_m, dureza, ductilidade, a fase, o veredito
  ("ESTÁVEL (valor demonstrativo)" ou "RISCO DE INTERMETÁLICOS (valor demonstrativo)") e uma "curva de Gibbs" que é um passeio
  aleatório decrescente (`heaDemo.ts:42-60`). O próprio arquivo declara que nada usa fórmula termodinâmica.
- É usado quando o serviço HEA não está disponível e a política de demonstração permite (`handlers.ts:39`, `boot.ts:59`,
  `stores/capabilities.ts:33-40`). O servidor em produção informa `demo_permitido: false` (teste `test_producao_capacidades`, aprovado).
  [NÃO VERIFICADO] se o frontend obedece a esse campo ou só à própria configuração.
- Há faixa de aviso (`hea-demo-banner`), selo e categoria "demo" nos cartões. Porém: (i) o veredito sorteado "ESTÁVEL..." recebe ✓ e a
  classe `is-ok` (`HeaModule.tsx:141`, `:153`); (ii) os gráficos não recebem a origem do resultado: o ponto fictício é plotado dentro
  da zona "solução sólida" de limites reais, e a legenda diz "com os valores do preditor"; (iii) os limiares do demo
  (`heaDemo.ts:27`: ΔS 10, Ω 5, δ 3, VEC 7, ΔH −5; "298,15 K (demo)") são inventados e diferentes dos do motor; (iv) o resultado demo
  pode ser enviado ao CrystaLab pela ponte (leva `origin: 'demo'`).

[INFERÊNCIA] Risco: em captura de tela, impressão, aula projetada ou leitura rápida, os números e a curva são lidos como resultado. A
curva fictícia tem forma plausível (decrescente com T), o que piora o risco. Isso contraria o requisito do usuário ("nunca curva
demonstrativa apresentada como real") mesmo com a faixa de aviso, porque a marca não acompanha cada gráfico.

[RECOMENDAÇÃO] Exigir, por ordem de preferência:

1. **Retirar o demonstrativo numérico do HEA.** O motivo original (motor ausente, D-01) deixou de existir: há motor real que devolve
   ΔS_mix sempre. Sem servidor, a tela mostra "Serviço HEA indisponível" e nenhum número. Os dados sintéticos ficam só nos testes.
2. Se o supervisor/usuário decidir manter (C-07), condições mínimas:
   - proibido em build de produção (bloqueio no código, não só na configuração) e obediência a `demo_permitido` do servidor;
   - nenhum vocabulário de veredito ("ESTÁVEL", "RISCO"); texto fixo "SEM RESULTADO: modo demonstrativo";
   - marca-d'água "DEMONSTRATIVO: valores fictícios" DENTRO de cada gráfico (no SVG), em cada tabela e na impressão;
   - sem faixas de critério reais sobre pontos fictícios; sem limiares inventados (ou os reais, ou nenhum);
   - sem curva com forma fisicamente plausível apresentada como ΔG; legenda sem "valores do preditor";
   - não exportável, não gravado em histórico, e a ponte para o CrystaLab desabilitada nesse modo.

### 2.9 Casos de referência para testes

#### 2.9.1 Analíticos ou de regressão (verificáveis agora; números calculados nesta tarefa)

| ID | Caso | Esperado | Tolerância |
|---|---|---|---|
| T-01 | ΔS_mix equimolar, n = 2, 3, 4, 5, 6 | R·ln n = 5,763146; 9,134371; 11,526293; 13,381611; 14,897517 J/(mol·K); 1,5R = 12,471694 | 5e-5 absoluto (saída com 4 casas) |
| T-02 | Invariância de escala: `Fe1Ni1`, `Fe50Ni50`, `Fe0.5Ni0.5` | saídas idênticas (exceto `soma_informada`) | exata |
| T-03 | δ binário equimolar com raios sintéticos 1,0 e 1,1 (repositório de teste) | δ = 100·\|r₁−r₂\|/(r₁+r₂) = 4,761905 %; raios iguais → δ = 0 | 1e-6 |
| T-04 | Regressão sobre os seeds atuais (NÃO é valor de literatura): AlCoCrFeNi | δ = 5,7324 %; VEC = 7,2; T_m = 1674,2 K (T_f do v1.4); ΔS = 13,3816 | 1e-4; T_m 0,1 K |
| T-05 | Regressão: CoCrFeNi; CrMoW; Al0.5CoCrCuFeNi | δ 0,3512 / 4,1970 / 4,1368 %; VEC 8,25 / 6,0 / 8,2727; T_m 1859,4 / 2907,2 / 1684,1 K | idem |
| T-06 | Conversão sintética: M_A = 10, M_B = 30, x = 0,5/0,5 | w = 25 % / 75 %; inversa devolve 50/50; M̄ = 20 | 1e-12 |
| T-07 | Conversão com massas CIAAW do repositório, equimolar | AlCoCrFeNi: Al 10,6881; Co 23,3445; Cr 20,5966; Fe 22,1213; Ni 23,2494 % em massa; M̄ = 50,4898 g/mol. CoCrFeNi: Co 26,1382; Cr 23,0615; Fe 24,7686; Ni 26,0317; M̄ = 56,3667. CoCrFeMnNi: Co 21,0171; Cr 18,5432; Fe 19,9158; Mn 19,5924; Ni 20,9315; M̄ = 56,0810 | 1e-4 (depende de C-02; com as massas de `metais.json` os valores mudam até 0,0019 p.p.) |
| T-08 | Ida e volta at → massa → at, e reenvio com `base: "massica"` | xᵢ recuperado; mesmas grandezas | 1e-12 nas frações; 1e-9 relativo no reenvio de `fracoes_massa` |
| T-09 | ΔH_mix com matriz SINTÉTICA de teste (valores fictícios, só para a álgebra; nunca em seed) | binária equimolar, h = −10 → −10 kJ/mol; equimolar n = 5, todos os pares h = −10 → 2h(n−1)/n = −16 kJ/mol; x = (0,5; 0,3; 0,2), h_AB = −10, h_AC = +5, h_BC = 0 → −4,0 kJ/mol | 1e-9 |
| T-10 | Ω sintético: T_m = 1500 K, ΔS = R·ln 2, ΔH = −10 e ΔH = +10 kJ/mol | Ω = 0,864472 nos dois casos (módulo) | 1e-6 |
| T-11 | ΔH_mix = 0 (matriz sintética nula) | `omega = null` com o motivo de 2.4.3; `dH = 0.0` | exata |
| T-12 | Par ausente na matriz sintética | `dH = null`, `omega = null`, `pares_faltantes` = lista exata; nenhuma soma parcial | exata |
| T-13 | ΔG_mix sintético: ΔH = +10 kJ/mol, ΔS = R·ln 2 | ΔG(1000 K) = 4,236854 kJ/mol; T* = 1735,163 K; Ω = T_m/T* | 1e-6; T* 1e-3 K |
| T-14 | −T·ΔS_mix sem ΔH: equimolar n = 5 a 1000 K | −13,381611 kJ/mol; `curva_T[].dG = null`; curva presente em produção | 1e-4 |
| T-15 | Validação (2.1): `Xx`; `fe`+`Fe`; `" Fe "`; `""`; `"Fe2O3"`; `"1"`; `true`; NaN; Infinity; 1e308+1e308; 1e7; −1; 13 chaves; 1 elemento; `Fe` + zero; fração 1e-12; `base: "massa"` | códigos e subtipos de 2.1.3; `fe`+`Ni` → 200 com chaves `Fe` e `Ni`; nenhuma resposta 500 | exata |
| T-16 | Domínio do VEC (2.7.2) | Al+Mg, Mg+Ti+Zn, Fe99,9Ni0,1, Ag+Au+Cu+Zn → "não avaliada", sem `estrutura_sugerida`; CoCrFeNi → CFC; CrMoW → CCC | exata |
| T-17 | Limiar exato: composição com VEC = 8 por construção (ex.: Al0,2CoCrFeNi, 33,6/4,2) | CFC, estável a permutações da ordem dos elementos | exata |
| T-18 | Triagem: δ > 6,6 % sem Ω (Mg+Fe+Pb+Al+W, δ = 12,0488 %) → `desfavoravel`; CoCrFeNi sem Ω → `inconclusiva`; com matriz sintética, os três estados | conforme 2.7.1 | exata |
| T-19 | Indisponibilidade: toda grandeza nula ou lista vazia tem chave em `indisponiveis` | propriedade verificada em todos os casos | exata |
| T-20 | Produção: ΔS_mix, `curva_T.menos_TdS` e `criterios` (sem valor) saem; dados não validados → nulos com motivo; `base: "massica"` → 422 | conforme 2.2.2 | exata |
| T-21 | Elemento real sem dados (Cantor, enquanto faltar raio do Mn) | 200; ΔS = 13,3816; `dados_faltantes` contém `{Mn, raio_atomico, ausente}` | exata |

#### 2.9.2 Dependentes de fonte externa — **a verificar pelo auditor bibliográfico** (não tenho os valores como dado)

| ID | O que obter | Para quê | Tolerância proposta |
|---|---|---|---|
| L-01 | Tabela de ΔH de mistura por par (Takeuchi & Inoue, 2005): valores, unidade, estado de referência, composição do par | Q-01; seed de 2.4.5 | transcrição exata |
| L-02 | Valores publicados de ΔH_mix, δ, Ω, ΔS_mix, T_m e VEC para ligas tabeladas em Yang & Zhang (2012) e Guo et al. (2011): no mínimo CoCrFeMnNi, CoCrFeNi, AlCoCrFeNi, CoCrCuFeNi, Al0.5CoCrCuFeNi | reprodução de literatura | ΔH_mix ± 0,1 kJ/mol com a mesma matriz; VEC ± 0,01; δ ± 0,1 p.p. SÓ se a tabela de raios for a mesma do artigo; Ω ± 2 % |
| L-03 | Qual tabela de raios cada artigo usou para δ | decidir P-HEA-01 e a comparabilidade de δ | — |
| L-04 | Limiares e seu enunciado exato: δ ≤ 6,6 % e Ω ≥ 1,1 (Yang & Zhang, 2012); VEC 8,0 e 6,87 (Guo et al., 2011); faixas de ΔH_mix e δ de Zhang et al. (2008) e de Guo & Liu (2011); 1,5R e 1R (Yeh, 2006; Miracle & Senkov, 2017); "5 ou mais elementos, 5 a 35 at.%" (Yeh et al., 2004) | campo `verificada` de `criterios`; zona do gráfico G-C | exato |
| L-05 | Fase observada experimentalmente e condição de processamento para as 4 ligas de exemplo e para CoCrFeMnNi, com citação | nível (d) "confirmação experimental"; A-14 | — |
| L-06 | Conjunto de elementos e de ligas em que o critério de VEC foi estabelecido, e exceções relatadas | domínio de 2.7.2 | — |
| L-07 | Tabela de VEC por elemento usada por Guo et al. (confirmar os 13 valores e Mn, V, Nb, Ta, Zr, Hf) | C-04 | exato |

## 3. Consultas para o Supervisor encaminhar

| ID | Para | Consulta |
|---|---|---|
| C-01 | academic-research-auditor | Confirmar na fonte cada limiar e referência de L-04 e a origem da zona "−15 < ΔH < 5; δ < 6,6 %" (2.6.1). Decisão do supervisor: faixas não verificadas aparecem tracejadas ou ficam ocultas? |
| C-02 | supervisor + api-architect + database-engineer | O motor HEA pode ler a tabela periódica (massas CIAAW, T_f, grupo, categoria)? Isso altera o ADR-018 ("tabela periódica é dado de referência; motores leem só o repositório de materiais"). Sem isso, a conversão em massa fica limitada a 15 metais e a validação de símbolo não tem lista de 118. |
| C-03 | materials-science-specialist + auditor | Fonte única de T_f para T_m: seed v1.4 (°C, sem fonte, `rascunho`) ou tabela periódica (K, PubChem, `aguardando_validacao`)? Divergência do Cr: 1857 °C × 2180 K (+49,85 K), que desloca T_m em cerca de 10 a 12 K nas ligas com 20 a 25 % de Cr. |
| C-04 | materials-science-specialist + auditor | VEC por regra do grupo para metais de transição (grupos 3 a 12), para incluir Mn, V, Nb, Ta, Zr, Hf: aceitável como dado derivado? Pb e Po continuam sem VEC? |
| C-05 | materials-science-specialist | Parecer sobre as escolhas heurísticas deste documento: (i) domínio do critério de VEC (ΔS_mix ≥ 1R; grupos 4 a 11 + Al; não aplicar quando a triagem é desfavorável); (ii) triagem `desfavoravel` quando um critério da conjunção falha e o outro é indisponível; (iii) aviso para \|ΔH_mix\| < 1 kJ/mol; (iv) margem de 2 % para "próximo do limiar"; (v) fração mínima 1e-6; (vi) δ nulo quando os raios vêm de fontes diferentes. |
| C-06 | academic-research-auditor | Q-01: obter a matriz de L-01 com condições de uso/licença para transcrição; indicar tabela de raios metálicos com fonte única (P-HEA-01, L-03). |
| C-07 | supervisor (decisão do usuário) | Modo demonstrativo do HEA: retirar (recomendado) ou manter com as condições de 2.8? |
| C-08 | academic-research-auditor | Citações de L-05 para o campo `grupo` das ligas de exemplo (A-14). |
| C-09 | api-architect | Fechar no contrato: nomes dos campos de 2.2.3, 2.6.4 e 2.6.5; `details` nos erros 400; código único para "menos de 2 elementos"; obsolescência de `gibbs`; `elements` com 118 itens e `raio_nm` anulável; `estrutura_sugerida` ausente × nulo. |
| C-10 | adversarial-qa-tester | Reproduzir no navegador A-06, A-15, A-17 e A-19 (constatados por leitura de código) e os casos T-15. |
| C-11 | database-engineer | Onde guardar os pares de ΔH: por ora seed JSON (2.4.5). `MOTOR_HEA.md` §5 diz que o banco "já prevê" tabela de pares; não conferi o esquema. Migração não está autorizada nesta rodada. |
| C-12 | backend-engineer (após G1) | Atualizar `docs/MOTOR_HEA.md` e os testes que fixam o prefixo "INCONCLUSIVO" e a forma de `HeaElement`. |

Pendências de dados abertas por esta tarefa: **P-HEA-01** (raios metálicos com fonte única para além dos 15 metais; bloqueia δ do Cantor e
das ligas refratárias). Pendência existente confirmada: **Q-01** (matriz de ΔH; bloqueia ΔH_mix, Ω, G-C, G-D, G-E).

## 4. Limitações e o que não foi verificado

1. **Literatura:** não consultei nenhum artigo nesta tarefa. Autores, periódicos, anos, volumes, páginas e limiares citados vêm do
   código/documentação do repositório ou da minha memória e estão TODOS marcados como não verificados. O limite de δ de Zhang et al. (2008) e as faixas
   de Guo & Liu (2011) não foram escritos, de propósito; a faixa "−15 a 5 kJ/mol" aparece porque está no código do frontend. A verificação é do auditor (C-01, C-06, C-08).
2. **Nenhum valor de ΔH binário nem de propriedade elementar foi citado de memória.** Os valores de propriedade que aparecem (raios, T_f,
   VEC, massas) foram lidos dos seeds do repositório, com o arquivo indicado; não validei esses valores contra a fonte primária.
3. **Frontend:** A-06, A-15, A-17, A-19 e A-20 vêm de leitura de código, sem execução em navegador. A-18 foi executado em Node com
   cópia literal da expressão regular, não com o módulo compilado.
4. **Produção:** não montei banco de produção; a política foi conferida só pelos testes existentes (aprovados). Não verifiquei se o
   frontend respeita `demo_permitido` do servidor.
5. **Persistência:** não executei gravação de histórico nem li o esquema do banco; A-20 e C-11 são por leitura de `calculo.py`.
6. **A-21** é risco latente demonstrado só aritmeticamente; não há caso reproduzido pela API com os dados atuais.
7. Não li `backend/tests/unit/engines/test_hea.py` por inteiro (só os nomes dos testes) nem `docs/agents/16_...` (a tarefa não envolveu
   coordenação). Não medi a suíte completa do backend nem do frontend: executei só os 25 testes ligados ao HEA.
8. As escolhas heurísticas listadas em C-05 são propostas deste agente, sem fonte; não devem ser implementadas como regra científica
   antes do parecer do materials-science-specialist.
9. Nenhuma fórmula do motor foi alterada. Esta especificação só vira regra depois dos pareceres (G1) e do contrato (R1-API-01).

## Estado

- [x] Linha de base
- [x] Auditoria (1.1, 1.2)
- [x] Especificação 2.1 a 2.9
- [x] Consultas e limitações

Arquivos alterados por esta tarefa: somente este relatório. Código de produção, seeds, banco e demais documentos: sem alteração.
