# Parecer científico — termodinâmica, estabilidade e transformação de fases (G1)

- **Tarefa:** R1-MAT-01 (2ª tentativa)
- **Agente responsável:** materials-science-specialist (Agente 07)
- **Emissor:** Supervisor (Agente 01)
- **Data:** 2026-11-13
- **Status:** concluído (parecer; nenhum código alterado, nenhum teste executado — fora do escopo autorizado)

> **Convenção deste parecer:** **[FATO]** = observado no repositório nesta tarefa, com arquivo:linha;
> **[DERIVAÇÃO]** = álgebra/aritmética feita por mim nesta tarefa; **[INFERÊNCIA]** = dedução a partir de fatos
> observados; **[HIPÓTESE]** = suposição não verificada; **[RECOMENDAÇÃO]** = proposta de ação.
> **Nenhuma referência bibliográfica foi conferida na fonte nesta tarefa** (não tenho acesso à web): todas as
> citações abaixo estão marcadas *não verificada na fonte nesta tarefa* e dependem do Agente 15.
> Não executei testes nem código: as derivações numéricas são aritméticas manuais, com precisão declarada.

---

## 1. Inventário do que existe

### 1.1 Modelos e equações implementadas

| # | Grandeza / modelo | Equação implementada | Local (arquivo:linha) | Unidades e convenções | Classe de resultado |
|---|---|---|---|---|---|
| M-1 | Dilatação linear | a(T) = a(20 °C)·[1 + α·(T − 20)] | `backend/app/engines/thermodynamics/termico.py:61` | α em 10⁻⁶ K⁻¹; ΔT em °C (≡ K); T_ref = 20 °C; P não modelada | `estimativa_modelo` (`:114`) |
| M-2 | Dilatação volumétrica e densidade | ΔV/V = f³ − 1; ρ(T) = ρ(20 °C)/f³, f = 1 + αΔT | `termico.py:110-111` | isotropia imposta; massa constante | `estimativa_modelo` |
| M-3 | Amplitude de vibração (Lindemann) | u/d_nn = f_L·√(T/T_f), f_L = 0,10 | `termico.py:22, 62` | T e T_f em K (`:59-60`) ✔; d_nn em nm | `estimativa_modelo` |
| M-4 | Temperatura homóloga | T/T_f em **kelvin** | `termico.py:63` | correto (ver §2.5) | `estimativa_modelo` |
| M-5 | Regra das misturas para α e T_f da liga | α = Σ fᵢαᵢ; T_f = Σ fᵢT_f,ᵢ | `termico.py:55-57`; frações montadas em `backend/app/services/calculo.py:127,135` | frações **atômicas** (de `x_pct`); intersticiais usam só o solvente (`calculo.py:129-131`) | `estimativa_modelo` |
| M-6 | Faixas de alotropia | tabela (de_c, ate_c, fase, estrutura) por elemento | `termico.py:92-102`; dados em `database/seeds/cristalografia/propriedades_v14.json:654-717` | °C, pressão ambiente não declarada | tabelado (ver §2.6: **não passa pela PoliticaDados**) |
| M-7 | ΔS_mix ideal | −R·Σ xᵢ ln xᵢ | `backend/app/engines/hea/analitico.py:84-85` | J mol⁻¹ K⁻¹ por mol de átomos; R = 8,314462618 (`:57`) | analítico dentro do modelo; devolvido como `estimativa_modelo` (`:562`) |
| M-8 | −T·ΔS_mix(T) e ΔG_mix(T) | −T·ΔS_mix; ΔG = ΔH_mix − T·ΔS_mix | `analitico.py:421-445` | kJ/mol; 300 K → T_sup, passo 50 K | `estimativa_modelo` |
| M-9 | ΔH_mix (solução regular, pares) | Σ_{i<j} 4·ΔH_ij·xᵢxⱼ | `analitico.py:399` | kJ/mol; **só com todos os pares** (`:390-399`) | `estimativa_modelo` (hoje indisponível) |
| M-10 | Ω | Ω = T_m·ΔS_mix/(1000·|ΔH_mix|) | `analitico.py:411` | adimensional | idem |
| M-11 | T de cruzamento | T* = 1000·ΔH_mix/ΔS_mix (só ΔH>0) | `analitico.py:442` | K | idem |
| M-12 | δ (descompasso de raios) | 100·√(Σ xᵢ(1 − rᵢ/r̄)²) | `analitico.py:337-338` | %; r̄ = Σ xᵢrᵢ | `estimativa_modelo` |
| M-13 | VEC e T_m | Σ xᵢVECᵢ; Σ xᵢ(T_f,ᵢ + 273,15) | `analitico.py:348, 358` | e/átomo; K | `estimativa_modelo` |
| M-14 | Vegard multicomponente | R̄ = Σ yᵢRᵢ; a = k·R̄ | `backend/app/engines/crystallography/ligas.py:522-524` | nm; y = fração atômica na sub-rede de rede | `estimativa_modelo` |
| M-15 | Hume-Rothery / Darken-Gurry / Hägg | ΔR ≤ 15 %; Δχ ≤ 0,4; r/R ≤ 0,59 | `ligas.py:53-55, 147-210` | critérios **binários** e empíricos | critério, não previsão (`ligas.py:176-191`) |
| M-16 | Distorção local | vizinhos deslocados em ½ do desajuste, ≤ 0,12·a | `ligas.py:337-373` | — | `simulacao_ilustrativa` (`:573`) |

### 1.2 O que o código declara explicitamente que **não** calcula [FATO]

| Grandeza | Onde está declarado |
|---|---|
| Energia de formação de fase | `analitico.py:464` (`MOTIVO_ENERGIA_FORMACAO`) |
| Dureza, ductilidade, fragilidade | `analitico.py:461-463` |
| Fração de fases | `ligas.py:70, 648` (`MOTIVO_FRACAO_FASE` = "o motor não calcula equilíbrio de fases") |
| Limite de solubilidade | `ligas.py:71, 650` ("não há dados de diagrama de fases no repositório") |
| Fases secundárias | `ligas.py:72, 651` |
| Conclusão de solubilidade multicomponente | `ligas.py:73, 667` |
| Liga multicomponente no módulo térmico | `calculo.py:125` (`_recusar_liga_multicomponente`) |

### 1.3 Dados e estado de validação

| Dado | Arquivo | Estado | Fonte | Consequência operacional |
|---|---|---|---|---|
| α (coef. dilatação linear), T_fusão, eletronegatividade, valência etc. (v1.4) | `database/seeds/cristalografia/propriedades_v14.json:1-12` (cabeçalho), ex. `:5-22` | **`rascunho`** | `fonte: null` | `ColetorDados.exigir` **recusa** em produção (`procedencia.py:81-84`) → **o motor térmico só roda em ambiente de desenvolvimento** [INFERÊNCIA] |
| Transições alotrópicas (Co, Fe, Ti) | `propriedades_v14.json:654-717` | **`rascunho`** | `fonte: null` | **usadas mesmo assim** (§2.6) |
| VEC (convenção Guo 2011) | `database/seeds/hea/vec.json:3-19` | `aguardando_validacao` | `guo2011` (citação presente, transcrição não revisada) | recusado em produção |
| Raio atômico e massa atômica usados pelos motores | `analitico.py:102-113` (estado fixado no código) | `aguardando_validacao` | fonte do repositório de materiais | recusado em produção |
| Tabela periódica (763 valores, 118 elementos) | `database/seeds/tabela_periodica/FONTES.txt:94-100` | `aguardando_validacao` | CIAAW 2021/2024; PubChem 2025 (com DOI no arquivo) | dado de **referência**, não entra nos motores (ADR-018) |
| Entalpias binárias ΔH_ij | **não existe no repositório** | — | — | ΔH_mix, Ω, ΔG_mix(T) indisponíveis (pendência Q-01) |
| Diagramas de fases, TDB, dados TTT/CCT, difusividades | **não existem no repositório** | — | — | §3, §4, §5 |

**Divergências de dados já registradas** [FATO] (`FONTES.txt:78-91`), relevantes para termodinâmica: T_f do Cr
1857 °C (v1.4) × 2180 K = 1906,85 °C (PubChem) — diferença de ~50 K que propaga para T_m, Ω e temperatura
homóloga; eletronegatividade de Al, Au, Mg, Mo, Pb, W, Ni divergente entre edições (propaga para Darken-Gurry);
massas de Zn e Mo desatualizadas no seed antigo.

---

## 2. Parecer sobre o motor térmico (`thermodynamics/termico.py`)

**Parecer global: VALIDADO COM RESSALVAS** como ferramenta didática de estimativa, **com 4 correções
obrigatórias de rotulagem/escopo (T-1, T-2, T-3, T-6) antes de qualquer uso em produção.**
A ciência implementada é a esperada para o nível declarado; os problemas são de **domínio de validade,
rotulagem e procedência**, não de álgebra.

### 2.1 Conferências que passaram [DERIVAÇÃO]

| Verificação | Resultado |
|---|---|
| Consistência dimensional de M-1 | ✔ α[10⁻⁶ K⁻¹]·10⁻⁶·ΔT[K] adimensional; ΔT em °C = ΔT em K |
| ρ(T) = ρ₀/f³ | ✔ massa constante, volume isotrópico ∝ f³ |
| ΔV/V = f³ − 1 ≈ 3αΔT | ✔ exato para isotropia, não linearizado |
| Temperatura homóloga em kelvin (`:63`) | ✔ **correto e essencial** — erro clássico evitado |
| Regra das misturas de T_f feita em °C (`:57`) e usada em K (`:60`) | ✔ **sem erro**: Σfᵢ(Tᵢ+273,15) = ΣfᵢTᵢ + 273,15 quando Σfᵢ = 1 (garantido em `:37`) |
| Normalização da razão de Lindemann | ✔ `razao` = u/d_nn é comparada ao limiar 0,10; a linha de referência do gráfico usa a mesma base (`frontend/src/modules/crystalab/AlloyPanels.tsx:285`) |
| Validação das frações da mistura | ✔ positivas e somando 1 (`:37-38`) |
| Classe de procedência | ✔ `estimativa_modelo` para tudo (`:114`) |

### 2.2 Dilatação linear com α constante — **validado com ressalvas**

- **Equação, convenções, estado de referência:** a(T) = a(20 °C)[1 + α(T − 20 °C)]; α médio de engenharia;
  estado de referência explícito (20 °C); **pressão não modelada e não declarada** → RECOMENDAÇÃO: declarar
  "pressão não modelada (fase condensada); valores de α de referência são a ~1 bar".
- **Faixa de validade científica:** α tabelado de engenharia é um **valor médio**, tipicamente sobre ~20–100 °C.
  α(T) cresce com T e **tende a zero quando T → 0 K** (consequência da terceira lei). A linearização é
  aceitável para |ΔT| de algumas centenas de K acima da ambiente, com erro crescente.
- **T-1 (ALTA, rotulagem) [FATO]:** a curva vai de −273,15 °C a T_f + 200 °C (`:66-69`) e `a_nm`, `densidade`,
  `delta_a_pct`, `delta_v_pct` são devolvidos **mesmo com `fundido = True`** (`:61, 109-111`). Parâmetro de rede
  e densidade cristalina de um líquido não têm significado. **RECOMENDAÇÃO:** acima de T_f devolver esses
  campos como `null` com motivo, ou marcá-los `extrapolacao: true`; limitar a curva a T_f.
- **T-2 (ALTA, hipótese não declarada) [INFERÊNCIA]:** M-1/M-2 impõem **isotropia**. Mg, Ti, Zn e Co no catálogo
  são HC: a dilatação é **anisotrópica** (α_a ≠ α_c; no Zn a anisotropia é grande). O α do seed é, na melhor
  hipótese, a média policristalina — logo **não descreve a célula desenhada**, e a conversão ΔV = f³ − 1 e a
  densidade herdam o erro. **RECOMENDAÇÃO:** declarar "α isotrópico médio (policristal); em estruturas não
  cúbicas a dilatação real é anisotrópica e a célula exibida não se deforma como no cristal real".
- **T-3 (ALTA, procedência) [FATO]:** α e T_f estão em `rascunho` com `fonte: null`
  (`propriedades_v14.json:5-22`) → em produção `exigir` recusa o cálculo (`procedencia.py:81-84`).
  **O módulo térmico é hoje funcional apenas em desenvolvimento.** Isso deve constar na documentação do
  produto e no gate: hoje não há resultado térmico publicável.
- **Nota de extrapolação abaixo da ambiente** (`:84-86`): correta e bem escrita, mas é `info`;
  **RECOMENDAÇÃO:** `alerta` abaixo de ~0 °C e supressão numérica abaixo de, por exemplo, 100 K.

### 2.3 Lindemann com f = 0,10 — **validado com ressalvas graves de interpretação**

- **O que a grandeza é:** o critério de Lindemann (Lindemann 1910; *não verificada na fonte nesta tarefa*)
  afirma que a fusão ocorre quando o **deslocamento quadrático médio** √⟨u²⟩ dos átomos atinge uma fração f da
  distância entre vizinhos. A forma u/d = f·√(T/T_f) é o **limite clássico de alta temperatura** de um modelo
  harmônico (Einstein/Debye), em que ⟨u²⟩ ∝ T, normalizado para dar exatamente f em T = T_f [DERIVAÇÃO].
- **O que a grandeza NÃO é:** não é a amplitude de uma oscilação determinística, não é deslocamento instantâneo
  e não é resultado de dinâmica de rede. É uma **média estatística (RMS)**. O campo é hoje chamado `u_nm` e
  rotulado "amplitude" na interface (`AlloyPanels.tsx:315`) e usado como amplitude de senoide no 3D
  (`frontend/src/features/viewer3d/alloyScene.ts:80-93`) — **deriva conceitual que precisa de rótulo** (§5.3, §6).
- **Limites de validade (todos a declarar):**
  1. **Alta temperatura:** ⟨u²⟩ ∝ T só vale para T ≳ θ_D/2 (modelo harmônico clássico). Abaixo disso a curva é
     inválida. **T-4 (MÉDIA) [FATO]:** a curva começa em −273,15 °C e dá u = 0 em 0 K (`:68`), o que é
     **fisicamente errado**: o movimento de ponto zero é finito em 0 K. **RECOMENDAÇÃO:** truncar a curva em
     ~θ_D/2 ou, sem θ_D no repositório, em 100 K, com nota "abaixo desta faixa o modelo harmônico clássico não
     vale e o movimento de ponto zero, não modelado, domina".
  2. **Anarmonicidade** e vacâncias próximas de T_f não são modeladas.
  3. **Inversão de uso:** Lindemann é um critério *para a temperatura de fusão*; usá-lo *para estimar u* é uma
     inversão cuja incerteza é muito maior que a do critério original. **RECOMENDAÇÃO:** declarar "estimativa de
     ordem de grandeza (incerteza da ordem de ±50 %)".
  4. **Convenção de f:** f ≈ 0,10–0,15 depende de a média ser 1D ou 3D e da estrutura. O código escolhe o limite
     inferior (`:22` e docstring `:6-7`) — viés **sistemático para baixo**, a declarar. **[HIPÓTESE]** a
     convenção pretendida é √⟨u²⟩ 3D; **não verifiquei na fonte** → consulta C-07-A ao Agente 15.
  5. **Ligas:** d_nn vem de Vegard sobre raios tabelados (`calculo.py:134`), não de medida; e T_f vem da regra
     das misturas (§2.4). Dois modelos empilhados.
- **Parecer:** o uso é legítimo como **ilustração quantitativa de ordem de grandeza**, nunca como "amplitude
  medida" nem como previsão de fusão.

### 2.4 Regra das misturas para α e T_f da liga — **validado com ressalvas (T-6 é obrigatória)**

- **α_liga = Σ xᵢαᵢ com frações ATÔMICAS** [FATO] (`calculo.py:127,135`; `termico.py:55`). Não há lei para isso:
  para compósitos os modelos usuais pesam por **fração volumétrica** (e há limites tipo Voigt/Reuss, modelos de
  Turner/Kerner); para uma solução sólida substitucional o comportamento experimental é aproximadamente linear
  na composição, **sem base teórica**. **A base (atômica) é uma convenção não declarada em nenhum texto da
  resposta.** **RECOMENDAÇÃO:** declarar "interpolação linear empírica em fração atômica"; registrar como
  hipótese do modelo. Para liga intersticial o motor usa só o solvente (`calculo.py:129-131`) — escolha
  defensável, **a declarar**.
- **T-6 (ALTA, erro de rotulagem) [FATO]:** com mistura, `fundido = T ≥ T_f` (`:64`) dispara o texto
  "*Acima da temperatura de fusão a ordem cristalina de longo alcance desaparece: o material é líquido*"
  (`:73-74`) — **afirmação sobre fusão de liga baseada numa média ponderada de T_f dos puros**. Ligas fundem num
  **intervalo solidus–liquidus**, e eutéticos ficam **muito abaixo** de todos os T_f puros (centenas de K de
  erro possível). A nota de advertência existe (`:88-89`), mas é `info` e vem *depois* da afirmação categórica.
  **RECOMENDAÇÕES:** (a) renomear o conceito para `acima_da_tf_nominal`; (b) rotular sempre
  "**T_f nominal (regra das misturas) — não é solidus nem liquidus**", harmonizando com o texto já adotado no
  HEA (`AVISO_TM_NOMINAL`, `analitico.py:418`); (c) para mistura, nunca afirmar "o material é líquido";
  (d) elevar a nota `:88-89` a `alerta`.
- **Propagação:** T_f nominal entra na temperatura homóloga, nas notas de 0,3/0,5·T_f e em toda a curva de
  Lindemann da liga. **Toda a interpretação térmica de liga herda essa incerteza** — a declarar junto.

### 2.5 Notas de temperatura homóloga (0,3 e 0,5 T_f) — **validado com ressalvas**

- Razões em **kelvin** ✔ (`:63`). Os patamares 0,3–0,5·T_f para recuperação/recristalização e ~0,4–0,5·T_f para
  fluência são **regras de ordem de grandeza** de metalurgia física (atribuíveis a Callister, seção 7.12/8.4;
  *não verificada na fonte nesta tarefa*).
- **T-5 (MÉDIA, afirmação categórica) [FATO]:** os textos são **incondicionais** — "*Entre 0,3 e 0,5·T_f ocorrem
  recuperação e recristalização*" (`:79-80`). Recristalização **exige deformação prévia a frio**, e a
  temperatura depende de grau de deformação, tempo, tamanho de grão e pureza (ligas e solutos a deslocam para
  cima; é **cinética, não propriedade da temperatura**). **RECOMENDAÇÃO:** condicionar ("*em metal previamente
  deformado a frio, nesta faixa ocorrem…*") e dizer que é faixa típica, dependente de tempo.
- **T-7 (MÉDIA, procedência) [FATO]:** `FONTES_MODELO` (`:25-28`) cita **apenas** dilatação (Callister 19.3) e
  Lindemann. As afirmações sobre recristalização, fluência, trabalho a quente/frio e encruamento **não têm
  fonte declarada** na procedência que a resposta devolve. **RECOMENDAÇÃO:** acrescentar a fonte dessas
  afirmações a `fontes_modelo` (pedido ao Agente 15) ou reduzi-las a vocabulário sem compromisso quantitativo.

### 2.6 Faixas de alotropia — **REJEITADO para produção; aceitável em desenvolvimento com rótulo**

- **T-8 (CRÍTICA, contorno de política de dados) [FATO]:** `props.transicoes()` é lida **sem passar pela
  `PoliticaDados`** (`:92-102`), ao contrário de α e T_f. Os dados estão todos em `rascunho` com `fonte: null`
  (`propriedades_v14.json:654-717`). O motor emite a afirmação científica "*a fase estável é Fe-γ (CFC)*",
  apenas acrescentando "*[faixa ainda sem validação]*" (`:96-97`). Isso **viola o principio 1 e 3 de
  `CLAUDE.md`** (dado não validado é recusado em produção) e é inconsistente com o tratamento das outras
  propriedades.
- **T-9 (ALTA, procedência) [FATO]:** as transições **não são registradas no `ColetorDados`**, logo não aparecem
  em `dados_usados` nem em `fontes_dados` do bloco `procedencia`. O resultado afirma uma fase de equilíbrio
  **sem rastro de procedência**.
- **RECOMENDAÇÕES:** (1) submeter `transicoes` à `PoliticaDados` (em produção: nota suprimida, com motivo);
  (2) registrar cada faixa usada no coletor; (3) declarar "à pressão ambiente (pressão não modelada)" — o ε-Fe
  (HC) de alta pressão não existe no modelo; (4) quando não houver faixa cadastrada para o elemento, dizer
  "sem dados de alotropia cadastrados para X" em vez de silêncio.
- **Conteúdo:** Co (ε-HC → β-CFC em 422 °C), Fe (α 912 / γ 1394 / δ 1538 °C) e Ti (α→β 882 °C) são
  **plausíveis** e coerentes entre si e com os T_f do seed [INFERÊNCIA], **mas não posso declará-los corretos**:
  sem fonte. → consulta C-07-B ao Agente 15. Observação: o limite inferior −273,15 °C afirma estabilidade até
  0 K; o ponto de Curie do Fe (~770 °C) **não** é transição alotrópica e corretamente não aparece.

### 2.7 Textos, rótulos e interface do motor térmico

| ID | Achado | Evidência | Severidade |
|---|---|---|---|
| T-10 | α exibido com categoria "reference" e a amplitude de Lindemann com categoria **"result"** — "result" esconde que é estimativa de modelo | `frontend/src/modules/crystalab/AlloyPanels.tsx:311, 315` | média (rotulagem) |
| T-11 | Rótulo "amplitude" para uma grandeza RMS (§2.3) | `AlloyPanels.tsx:315`; `termico.py:112` | média (conceitual) |
| T-12 | Não verifiquei se os textos i18n do gráfico de Lindemann traz eixos, unidades, condição, fonte e natureza | `AlloyPanels.tsx:265-290` usa chaves `thermal.*`; **não li o i18n** | **não verificado** |
| T-13 | Citação "Callister & Rethwisch, seção 19.3" sem edição; Lindemann com volume/páginas, não conferidos | `termico.py:25-28` | baixa (auditoria) |

---

## 3. MATRIZ DE ESCOPO do item 5 (pedido do usuário)

**Legenda de sustentação:** **A** = sustentável hoje com modelo analítico; **B** = sustentável **só** se chegar
o dado indicado, com fonte; **D** = só didático-ilustrativo, com fonte citada e selo; **N** = não sustentável
(não implementar).

> **Estado de referência comum às linhas 1-11:** componentes puros **não misturados**, na mesma estrutura
> cristalina da solução, na mesma T e P (referência **raoultiana**). Base: **1 mol de átomos**.
> **Hipóteses comuns:** mistura substitucional aleatória numa única sub-rede; sem contribuição vibracional,
> magnética ou eletrônica para ΔS; sem ordem de curto alcance; sem vacâncias; **pressão não modelada**
> (sem equação de estado, sem V(T,P)); parâmetros independentes de T.

| # | Capacidade pedida | Sust. | Modelo e equações (convenções) | Dados necessários / existem? | Natureza e **rótulo obrigatório** | Faixa de validade | Decisão recomendada |
|---|---|---|---|---|---|---|---|
| 1 | Entropia de mistura ideal | **A** | ΔS_mix = −R Σ xᵢ ln xᵢ [J mol⁻¹K⁻¹] | só composição ✔ (já em `analitico.py:84`) | calculado, exato **dentro** do modelo → "**ΔS_mix configuracional ideal (solução aleatória)**" | qualquer x > 0; não é a entropia total da liga | **manter** |
| 2 | ΔG de mistura ideal | **A** | ΔG_mix^id = RT Σ xᵢ ln xᵢ = −T·ΔS_mix | idem ✔ | calculado → "**ΔG_mix ideal do modelo — não é G da liga nem prova estabilidade**" | idem | **implementar** (hoje existe −T·ΔS_mix, `analitico.py:424`) |
| 3 | Potencial químico ideal | **A** | μᵢ − μᵢ° = RT ln xᵢ [J/mol]; μᵢ° = puro i na mesma estrutura, T, P | só composição ✔ | calculado → "**modelo de solução ideal; referência raoultiana; não é atividade medida**" | x > 0; só solução ideal | **implementar**, com a referência impressa junto |
| 4 | Atividade ideal | **A** | aᵢ = xᵢ; γᵢ = 1 | ✔ | calculado → "**aᵢ = xᵢ por hipótese de idealidade (não é medida)**" | idem | **implementar** com ressalva forte: valor **imposto**, não previsto |
| 5 | ΔH_mix (solução regular) | **B** | ΔH_mix = Σ_{i<j} 4ΔH_ij xᵢxⱼ [kJ/mol]; Ω_ij = 4ΔH_ij (ΔH_ij = valor equimolar do par) | **matriz ΔH_ij com fonte — NÃO existe** (pendência Q-01); código pronto (`analitico.py:399`) | estimativa por modelo → "**ΔH_mix (modelo de Miedema, solução regular) — não é calorimetria, não é energia de formação**" | ligas metálicas substitucionais; parâmetros do **líquido** na literatura de HEA (a confirmar); sem T nem P | **implementar quando chegar o dado**; manter `null` com motivo |
| 6 | ΔG_mix(T) do modelo regular | **B** | ΔG_mix(T) = ΔH_mix − T·ΔS_mix | depende de (5) | estimativa → "**ΔG_mix do modelo**" | Ω constante em T e x | idem; código pronto (`:426`) |
| 7 | Coeficiente de atividade (regular, binário) | **B** | RT ln γ_A = Ω x_B²; a_A = γ_A x_A | Ω com fonte | estimativa → "**modelo de solução regular binária**" | **binário** simétrico | implementar **só binário** |
| 8 | Lacuna de miscibilidade (binodal), binário regular | **B** | Minimização de ΔG com conservação de massa = **tangente comum**; condição simétrica: ln[x/(1−x)] + (Ω/RT)(1−2x) = 0 (raiz numérica, bisseção em Python puro) | Ω com fonte | estimativa → "**decomposição em duas soluções da MESMA estrutura, dentro do modelo regular — não é diagrama de fases**" | binário, Ω > 0, uma única estrutura, sem compostos | implementar se chegar Ω; **é a única "minimização de Gibbs" honesta hoje** |
| 9 | Espinodal e T crítica | **B** | ∂²ΔG/∂x² = 0 → T_sp(x) = 2Ω x(1−x)/R; máximo em x = ½ → **T_c = Ω/(2R)** [DERIVAÇÃO conferida] | Ω com fonte | estimativa → "**limite de estabilidade do modelo regular**" | idem (8) | idem |
| 10 | Frações de fase × T **dentro do modelo** | **B** | regra da alavanca entre os dois ramos da binodal de (8) | Ω com fonte | estimativa → "**frações das duas soluções do modelo regular; NÃO é fração de fases de equilíbrio real**" | idem (8) | implementar **junto com (8)**, nunca isolada |
| 11 | Metaestabilidade / coexistência | **B** | região entre binodal e espinodal do modelo binário | Ω com fonte | estimativa, com o rótulo de (8) | idem | implementar junto com (8)-(9) |
| 12 | Lacuna/espinodal **multicomponente** | **N** | exigiria det[∂²G/∂xᵢ∂xⱼ] = 0 com todos os Ω_ij | todos os Ω_ij + validade do modelo regular em n componentes | — | **extrapolação indevida**: solução regular com Ω_ij binários constantes não descreve n>2 (ignora termos ternários, ordem, e estruturas distintas) | **não implementar**; registrar como fora de escopo |
| 13 | Energia de Gibbs **por fase** (absoluta) | **N** | G^φ(T,x) = Σxᵢ°G_i^φ + RTΣxᵢlnxᵢ + ^exG^φ, referência SER (298,15 K, 1 bar) | funções de rede (lattice stabilities), termos de excesso Redlich-Kister, modelo magnético — **nada no repositório** | — | — | **CALPHAD (§4) ou nada**; hoje declarar indisponível |
| 14 | Equilíbrio por minimização global de Gibbs entre **várias fases** | **N** | min Σ_φ n^φ G^φ sujeito a conservação de massa | depende de (13) | — | — | **não prometer**; a interface deve dizer o que não faz |
| 15 | Diagramas binários/ternários calculados | **N** | consequência de (14) | depende de (13) | — | — | **não implementar** |
| 16 | Diagrama de fases **ilustrativo** | **D** | nenhuma equação: figura/tabela de fonte citada | precisa de dado/figura com licença (Agente 15) | ilustração → "**figura didática de [fonte]; não é cálculo deste sistema**" | sistema exato da fonte | só com fonte e licença aprovadas |
| 17 | Composição de cada fase e partição | **N** (exceto o caso (8)) | coeficientes de partição saem de (14) | depende de (13) | — | — | **não implementar** fora do caso (8) |
| 18 | Fases candidatas escolhidas pelo usuário | **N** | exigiria G^φ de cada candidata | depende de (13) | — | — | **não implementar**; é promessa sem motor |
| 19 | Pressão como entrada | **N** | exigiria V(T,P) / equação de estado | nada no repositório | — | — | **não aceitar P como parâmetro de cálculo**; só exibir "pressão não modelada (fases condensadas)" |
| 20 | Temperatura como entrada | **A** | entra em (2),(3),(6),(8)-(11) e no motor térmico | ✔ | — | ver linhas respectivas | **manter**, com faixa explícita por grandeza |
| 21 | Comparação de estado inicial × final | **A/B** | diferença dos **descritores** calculados entre dois estados (composição, T) | ✔ para descritores; (8)-(11) se houver Ω | calculado/estimativa → "**comparação de descritores do modelo; não é caminho de transformação nem equilíbrio**" | — | implementar só como tabela comparativa de descritores |
| 22 | Tabela de propriedades termodinâmicas | **A** | ΔS_mix, −TΔS_mix, ΔG_mix^id, T_m nominal, δ, VEC (+ ΔH, Ω, ΔG quando houver dado) | ✔ parcialmente | cada linha com **coluna "natureza"** e fonte | — | **implementar** (§6) |
| 23 | Curvas no tempo, nucleação, crescimento, difusão, TTT/CCT | **N** | §5 | nenhum parâmetro cinético no repositório | — | — | **proibido** (§5) |

### 3.1 Enunciado honesto recomendado para o produto [RECOMENDAÇÃO]

> "Modelos de **solução** (ideal e, quando houver dados de entalpia binária com fonte, regular) para **uma única
> fase substitucional desordenada hipotética**, mais descritores empíricos de triagem (δ, VEC, Ω). O sistema
> **não calcula equilíbrio de fases**: não há energia de Gibbs por fase, nem diagramas, nem frações de fase, nem
> cinética. Temperatura é parâmetro; **pressão não é modelada**."

**É proibido** usar, para o escopo atual, os termos: "termodinâmica completa", "previsão de fases",
"estabilidade", "diagrama de fases", "energia livre da liga", "zona estável".
**T-14 (ALTA, rotulagem já no código) [FATO]:** o mapa δ×ΔH do HEA rotula a região como
"**stableZone**" (`frontend/src/modules/hea/HeaCharts.tsx:74`), com limites −15 < ΔH < 5 kJ/mol e δ < 6,6 %
fixados no front (`:66, :69`) e **sem citação de literatura** (`:5` os atribui ao "HEA Virtual Lab v1.17").
Isso é exatamente o vocabulário proibido. **RECOMENDAÇÃO:** renomear para "faixa empírica de triagem de solução
sólida (fonte: …)", ou remover o retângulo até o Agente 15 fornecer a fonte dos dois limites. Observação: o
limite δ ≤ 6,6 % tem origem citada no backend (Yang & Zhang 2012, `analitico.py:74`); **a faixa de ΔH
−15…5 kJ/mol não tem nenhuma fonte em nenhum arquivo que eu li** → consulta C-07-C.

---

## 4. CALPHAD — opções reais, verificações e **DECISÃO PENDENTE DO USUÁRIO**

**[FATO]** Não há motor CALPHAD, base TDB, numpy, scipy nem dado de diagrama no repositório (linha de base do
supervisor + inventário §1.3). Sem isso, as linhas 13-15, 17 e 18 da matriz são impossíveis — não por escolha
de implementação, mas por **ausência de dados**.

| Opção | O que é | O que **precisa ser verificado** (eu **não** verifiquei nada disto) |
|---|---|---|
| `pycalphad` | motor CALPHAD em Python | existência da versão atual; **licença** (a verificar); dependências (numpy, scipy, sympy/symengine) e se há **wheels para Python 3.15 em Windows** (a verificar); peso da instalação; compatibilidade com Python puro do projeto |
| `OpenCalphad` | motor em Fortran com interface Python | licença (a verificar); necessidade de **toolchain de compilação em Windows**; estabilidade da API |
| Software comercial (p. ex. Thermo-Calc) | motor + bases avaliadas | **licença comercial** por usuário/servidor; incompatível com software livre educacional? (decisão do usuário) |
| Bases TDB | funções de Gibbs avaliadas por sistema | **licença de CADA base** (a verificar); **cobertura**: há base aberta que cubra **Fe–Cr–C**? e **Al–Co–Cr–Fe–Ni**? (a verificar); se as funções unárias SGTE podem ser redistribuídas (a verificar) |

**Critérios de aceite técnico-científicos que eu exigirei antes de declarar suporte quantitativo**
[RECOMENDAÇÃO]:

1. **Cobertura declarada por sistema:** a interface só pode oferecer cálculo para sistemas **presentes na base**;
   para qualquer elemento/par ausente → `null` com motivo. **Nunca** extrapolar para sistema ausente.
2. **Procedência:** cada resultado traz nome e versão da base, referência da avaliação e faixa de T, x e P da
   avaliação original.
3. **Casos de referência:** antes do uso, reproduzir valores publicados de pelo menos 2 sistemas (ex.: um binário
   simples e um multicomponente) dentro de tolerância acordada; sem isso, resultado fica `aguardando_validacao`.
4. **Licença explícita** do motor **e** de cada base, registrada em `docs/` e compatível com a distribuição do
   projeto.
5. **Peso e reprodutibilidade:** impacto no Docker, no CI (Linux + Windows) e no tempo de resposta.

**DECISÃO PENDENTE DO USUÁRIO (D-TERMO-01):** (a) **não adotar CALPHAD** e manter o escopo honesto de §3.1
(recomendação do especialista para esta rodada, por ser a única opção com evidência hoje); ou (b) **autorizar
uma investigação técnica** (não implementação) de motor + base aberta, com relatório de licença, cobertura e
compatibilidade; ou (c) adotar solução comercial, assumindo custo e licenciamento.
**Até a decisão, a interface deve dizer que o sistema não faz CALPHAD.**

---

## 5. Cinética — requisitos e **regra dura**

### 5.1 Regra dura (parecer vinculante)

> **Nenhum gráfico, tabela ou texto com o tempo como variável — nem TTT/CCT, nem fração transformada,
> nem taxa — pode existir sem um modelo cinético explícito e seus parâmetros com fonte.**
> **É proibido deduzir cinética de curvas de equilíbrio** (de ΔG_mix, da curva de Lindemann, de faixas
> alotrópicas ou de temperatura homóloga). Equilíbrio responde "o quê"; cinética responde "quando" — são
> modelos e dados distintos.

### 5.2 O que cada capacidade cinética exigiria

| Capacidade | Modelo | Parâmetros necessários (unidades) | Existem no repositório? |
|---|---|---|---|
| Fração transformada × tempo | **JMAK/Avrami**: f = 1 − exp(−k tⁿ); k = k₀exp(−Q/RT) | n (—), k₀ (s⁻ⁿ), Q (J/mol) por reação e por liga | **não** |
| Nucleação | clássica: I = I₀ exp(−ΔG*/k_BT)·exp(−Q_d/k_BT); ΔG* = 16πσ³/(3ΔG_v²) (homogênea, esférica) | energia interfacial σ (J/m²), ΔG_v (J/m³, vem de (13) da matriz!), Q_d, densidade de sítios | **não** |
| Crescimento | controlado por difusão (parabólico, x ∝ √(Dt)) ou por interface | D = D₀exp(−Q/RT) por soluto, fase e caminho (volume/contorno) | **não** |
| Difusão | 1ª e 2ª leis de Fick; solução por erro complementar para meio semi-infinito | D₀ (m²/s), Q (J/mol), condições de contorno | **não** |
| TTT / CCT | **são dados experimentais**, por aço e por composição exata | curvas medidas, com norma e fonte | **não** |

**[INFERÊNCIA]** Note que até a nucleação depende de ΔG_v, que exige energia de Gibbs **por fase** (linha 13 da
matriz) — isto é, **a cinética está bloqueada duas vezes**: falta modelo e falta o insumo termodinâmico.
**RECOMENDAÇÃO:** não abrir frente cinética nesta rodada; se o usuário quiser difusão, a opção **mínima e
honesta** é um módulo de **Fick isolado** ("calculadora de perfil de difusão"), com D₀ e Q **fornecidos pelo
usuário ou vindos de seed validado com fonte**, rotulado "não é previsão de microestrutura".

### 5.3 Animações existentes — risco de leitura como simulação física e rótulo obrigatório

| Animação | O que é de fato | Risco | Selo hoje | **Rótulo obrigatório** |
|---|---|---|---|---|
| Empilhamento ABAB / ABCABC | ilustração **geométrica** da sequência de planos compactos | baixo (pode ser lido como mecanismo de crescimento) | ✔ selo "Ilustrativo" (`SceneHud.tsx:130`) | "Ilustração **geométrica** da sequência de empilhamento. Não representa crescimento, nucleação nem movimento de átomos no tempo." |
| **α → γ do Fe** | interpolação/morfismo entre as células CCC e CFC | **ALTO** | **SEM selo** — `SceneHud.tsx:130` **exclui explicitamente** `'alpha-gamma'` [FATO] | **T-15 (ALTA) — corrigir:** "**Transição geométrica entre as duas células (interpolação de posições). Não é o mecanismo, nem o caminho, nem a cinética da transformação α→γ** (que envolve nucleação e crescimento, com relações de orientação específicas). A temperatura de 912 °C vem de dado em **rascunho, sem fonte** (§2.6)." |
| Vibração térmica | senoides **independentes**, fase e frequência por átomo e por eixo, amplitude = u(Lindemann) × exagero (≥1×) (`alloyScene.ts:80-93`) | **ALTO** (parece dinâmica molecular) | ✔ selo (thermal recebe selo em `:130`) | "**Animação ilustrativa de agitação térmica**: osciladores independentes, sem correlação entre átomos — **não é dinâmica de rede, não há fônons, não há escala de tempo física**. Amplitude = estimativa RMS do critério de Lindemann × exagero visual N×." |

**T-16 (MÉDIA, quantitativa) [INFERÊNCIA]:** em `alloyScene.ts:80-86` a amplitude do motor é aplicada **a cada
componente** do deslocamento ("|componente| ≤ amplitude"), de modo que o módulo do deslocamento chega a
**√3·u**. Se `u` é o RMS 3D (§2.3), o desenho **superestima** em ~73 % mesmo com exagero 1×, e o rótulo
"1× = real" (`:92`) fica incorreto. **RECOMENDAÇÃO:** usar u/√3 por componente **ou** remover a alegação
"1× = real". Pendência para o frontend/integração, com meu parecer anexado.

---

## 6. Regras de rotulagem de gráficos, tabelas e resultados (vinculantes)

### 6.1 Classificação de natureza (vocabulário único)

| Natureza | Quando usar | Exemplos no sistema |
|---|---|---|
| **experimental / medido** | valor medido, com método e fonte | T_f e α **se** validados com fonte; a e c medidos do Ti |
| **calculado (analítico)** | fechado dentro de um modelo exato e sem parâmetro ajustado | ΔS_mix ideal; geometria da célula; FEA de esferas rígidas |
| **estimativa por modelo** | modelo aproximado ou parâmetro empírico | a(T), ρ(T), u de Lindemann, Vegard, ΔH_mix de Miedema, Ω, T_m nominal |
| **empírico / critério de triagem** | correlação sem derivação | δ ≤ 6,6 %, Ω ≥ 1,1, VEC, Hume-Rothery, Darken-Gurry, Hägg |
| **ilustrativo** | imagem/animação sem valor preditivo | distorção local, vibração, animações, cores Jmol |
| **indisponível** | não calculável → `null` + motivo | ΔH_mix, Ω, energia de formação, fração de fases |

**Nunca** usar "resultado" (`category=result`) para item de classe *estimativa por modelo* (corrigir T-10).
**Nunca** nomear uma grandeza de modelo com o nome da grandeza física medida (corrigir T-11, T-14 e o campo
`gibbs`/`G` do HEA, que é **ΔG_mix do modelo em J/mol**, não G — `analitico.py:436` já marca "obsoleto").

### 6.2 Metadados obrigatórios em **todo** gráfico e **toda** tabela

1. **Eixos** com grandeza + **símbolo** + **unidade** (ex.: "T (K)", "ΔG_mix (kJ·mol⁻¹)", "u/d_nn (—)").
2. **Condições:** T (ou faixa), composição, base da composição (atômica ou mássica), estrutura,
   "**pressão não modelada (fase condensada)**".
3. **Legenda** identificando cada série e marcando a série selecionada.
4. **Fonte dos dados** (versão do seed + citação) **e** fonte do modelo; marcas de verificação quando a fonte
   não foi conferida (o backend já faz isso: `verificada: False`).
5. **Natureza** do resultado, com o vocabulário de 6.1, visível no gráfico (não só no `alt`).
6. **Faixa de validade** e aviso quando a curva sai dela (ex.: T < 100 K na curva de Lindemann; T > T_f).
7. **Nada é recalculado no front** (regra já seguida: `HeaCharts.tsx:4`) — inclusive **limiares e zonas**, que
   devem vir do backend com fonte (hoje não: `HeaCharts.tsx:66,69`, T-14).
8. **Indisponibilidade é conteúdo:** gráfico sem dado mostra o motivo, não um eixo vazio (já feito,
   `HeaCharts.tsx:40-43` ✔).

### 6.3 Marcações específicas exigidas

| Item | Marcação |
|---|---|
| Curva ΔG_mix × T (HEA) | "ΔG_mix **do modelo** (solução regular, ΔS ideal)"; marcar T_m com "**T_m nominal (regra das misturas) — não é solidus nem liquidus**"; eixo em kJ·mol⁻¹ (padronizar: hoje `gibbs.G` sai em J/mol e a curva em kJ/mol) |
| Mapa δ × ΔH | remover "zona estável"; usar "faixa empírica de triagem"; citar a fonte de **cada** limite ou retirá-lo (T-14) |
| Curva de Lindemann | eixo y "u/d_nn (—)"; linha "f_L = 0,10 (limite inferior da literatura)"; truncar/avisar abaixo de ~100 K; chamar u de "deslocamento quadrático médio estimado" |
| Painel térmico | α como *valor de referência* (com estado do dado), a(T), ρ(T), ΔV como *estimativa por modelo*; suprimir valores acima de T_f (T-1) |
| Tabela de propriedades | coluna **Natureza** + coluna **Fonte/estado** em cada linha, obrigatórias |

### 6.4 Sincronização com o 3D (regra vinculante)

> **"A distribuição atômica exibida é apenas representativa: é uma realização estatística da composição
> solicitada, não a microestrutura prevista nem a posição real dos átomos."**
> O 3D **nunca** pode sugerir fases, precipitados, contornos de grão ou partição de soluto que o motor não
> calcula. Quando um resultado numérico mudar (T, composição), a cena só pode mudar no que o motor devolveu;
> e quando a cena mostra algo que o motor não calculou (vibração, distorção, coloração, animação), o selo
> "Ilustrativo" é obrigatório **dentro da área da cena** — regra já adotada (`SceneHud.tsx:106-110`), com a
> **exceção indevida de `alpha-gamma`** (T-15).
> O motor de ligas já traz os textos corretos para isso (`ligas.py:65-69`, `AVISO_FASE_UNICA`,
> `AVISO_REALIZACAO`): **mantê-los visíveis**, não só no JSON.

---

## 7. Revisão cruzada

### 7.a FEA do HC (parecer de cristalografia, §1.4) — **APROVADO COM 3 RESSALVAS**

**Conferência algébrica** [DERIVAÇÃO, feita nesta tarefa]:

- Volume da célula primitiva hexagonal (2 átomos): V = a²c·sen 120° = (√3/2)a²c. ✔
- FEA = 2·(4/3)πR_c³ / ((√3/2)a²c). Com u ≡ 2R_c/a:
  FEA = (8π/3)·(a³u³/8)/((√3/2)a²c) = **(2π/(3√3))·u³/(c/a)**. ✔ **A fórmula do parecer está correta.**
- Conferência no ponto ideal: c/a = √(8/3) = 1,632993 → d_fora/a = √(1/3 + (c/a)²/4) = √(1/3 + 2/3) = 1 → u = 1 →
  FEA = 1,2091996/1,632993 = **0,740480** = π/(3√2). ✔
- **Máximo exatamente no c/a ideal** (afirmação do parecer): d(ln FEA)/d(c/a) = 3u′/u − 1/r, com r = c/a e
  u′/u = r/(4/3 + r²) → derivada ∝ (2r² − 4/3). Zera em r = √(2/3) = 0,8165; é **positiva** em
  0,8165 < r < 1,63299 e **negativa** acima. Logo, **para r ≥ 2/3 o máximo é no ideal e FEA ≤ 0,740480**. ✔
  **Ressalva R-1 (domínio):** a afirmação "nunca excede 0,74048" **não é global**. Para r < 2/3 a própria
  expressão de R_c está incompleta — falta a terceira distância candidata, a translação **c** (c < d_fora
  ⇔ r < 2/3), e aí FEA cresce sem limite (ex.: r = 0,2 → FEA ≈ 1,2, impossível). Nenhum metal real está nessa
  faixa (c/a real ~1,56–1,89), **mas se a interface permitir editar c/a** isso precisa de guarda.
  **RECOMENDAÇÃO:** usar **R_c = ½·mín(a, c, d_fora)** e manter a asserção FEA ≤ π/(3√2) como invariante testado.
- **Ressalva R-2 (4º decimal) [DERIVAÇÃO]:** com os c/a impressos no parecer eu obtenho
  **Mg 0,736427** (parecer 0,736418), **Ti 0,720162** (parecer 0,720132), **Co 0,735900** (parecer 0,735968).
  As diferenças (até 7×10⁻⁵) **mudam o 4º decimal** de Ti e Co (0,7202 × 0,7201; 0,7359 × 0,7360).
  [INFERÊNCIA] a causa provável é o c/a efetivo do seed ter mais dígitos que a tabela do parecer (Ti é o caso com
  a e c medidos). **RECOMENDAÇÃO:** os valores de regressão devem ser gerados a partir do c/a do seed, com o
  número de dígitos documentado no teste, e o teste deve fixar **tolerância** (não string).
  Os valores arredondados a 4 casas citados no cartão (Mg 0,7364; Co 0,7360) são compatíveis; **Ti 0,7201
  precisa de conferência** antes de entrar como valor de referência.
- **Ressalva R-3 (rotulagem) — concordo e reforço:** o FEA de um metal real **nunca** deve ser rotulado
  "empacotamento medido"; é **propriedade do modelo de esferas rígidas aplicado à geometria** (ponto 4 do
  parecer). Concordo também com a correção de NC para "6 + 6" fora do ideal e com `c_a_natureza`.
  Acrescento: é obrigatório dizer **qual raio** foi usado (a/2, d_mín/2, ou raio tabelado) — o parecer mostra que
  para o Ti coexistem **três** critérios (0,7618 / 0,7201 / 0,7155), e três números iguais em nome e diferentes
  em valor são a maior fonte de confusão didática aqui.
- **Preferência entre as duas alternativas do parecer:** concordo com a **opção 1** (corrigir `fea`), porque
  FEA > 0,740480 é resultado **enganoso**, não apenas impreciso. **Mas** recomendo manter **também** os campos
  aditivos (`fea_esferas_rigidas` ou equivalente, `raio_contato_rel`, `contato`), para que a mudança seja
  auditável e o aluno veja a diferença entre os critérios.

**Parecer: APROVADO para implementação** (fórmula correta, rótulos adequados), condicionado a R-1 (guarda e
mín(a, c, d_fora)) e R-2 (reproduzir os valores de referência do seed antes de fixá-los em teste).

### 7.b Heurísticas sem fonte do HEA (consulta C-05)

| Item | Parecer | Justificativa e condição |
|---|---|---|
| (i) **Domínio do VEC: ΔS_mix ≥ 1R** (`analitico.py:247`) | **APROVADO** como triagem conservadora, **com texto obrigatório** | ΔS = 1R corresponde a ≈ e = 2,72 componentes equimolares [DERIVAÇÃO: ΔS/R = ln n para equimolar] — exclui ligas diluídas e quase-binárias, que é o efeito desejado. **Não é critério da literatura**: deve aparecer como "**regra de triagem deste software, sem fonte**" em `definicoes`, nunca como condição de Guo et al. |
| (i) **Conjunto grupos 4-11 + Al** (`analitico.py:69, 249`) | **APROVADO com ressalva documental** | Conservador e coerente com o universo típico do critério (metais de transição 3d/4d + Al). **Ressalva [FATO]:** a convenção do seed (`vec.json:3`) cobre também **Zn** (grupo 12) e **Mg** (grupo 2), que `range(4,12)` **exclui** — ou seja, **o domínio de aplicação é deliberadamente mais estreito que o dado**. Isso precisa estar escrito, senão parece bug. Cu/Ag/Au (grupo 11) entram; Zn não. |
| (iii) **Não aplicar VEC quando a triagem é desfavorável** (`analitico.py:252`) | **APROVADO, condicionado à correção de (ii)** | Cientificamente coerente: o critério de VEC distingue CFC × CCC **entre ligas que formam solução sólida**; se a triagem de solução sólida falha, a sugestão de estrutura não tem domínio. **Condição:** não pode ser acionado por uma triagem "desfavorável" que se apoie num único critério com o outro indisponível (ver (ii)) — seria heurística encadeada em heurística. |
| (ii) **Triagem `desfavoravel` com um critério falhando e o outro indisponível** (`analitico.py:205-219`) | **AJUSTAR** (lógica aprovada, rótulo rejeitado) | A **lógica é correta**: numa conjunção A∧B, A falso ⇒ conjunção não atendida, independentemente de B. O **rótulo** não: "DESFAVORÁVEL" comunica uma previsão sobre a liga, mais forte que "critério não atendido". O texto atual já anexa "; Ω não foi avaliado (motivo)" (`:213`) — bom. **Recomendo:** estado `criterio_nao_atendido` (ou manter `desfavoravel` **apenas** quando os **dois** critérios foram avaliados), e **não** usar esse estado para desligar o VEC em (iii) quando o segundo critério é indisponível. |
| (iv) **Aviso para \|ΔH_mix\| < 1 kJ/mol** (`analitico.py:63, 412-413`) | **APROVADO como convenção do software**, com texto obrigatório e pendência | Justificado: Ω = T_m·ΔS/(1000·\|ΔH\|) **diverge** quando ΔH→0, e ΔH_mix pequeno costuma vir de **cancelamento** de termos de par maiores, de modo que a incerteza **relativa** explode; além disso Ω ≥ 1,1 passa a ser satisfeito trivialmente. O valor **1 kJ/mol é arbitrário** → declarar "convenção deste software, sem fonte". **Texto exigido:** "Ω é grande porque \|ΔH_mix\| é próximo de zero; a triagem favorável decorre do denominador pequeno, não de afinidade química definida." **Pendência:** quando o seed de entalpias trouxer **incerteza por par**, substituir o limiar fixo pela comparação \|ΔH_mix\| × incerteza propagada. |
| (v) **Margem de 2 % para "próximo do limiar"** (`analitico.py:61, 293`) | **APROVADO como convenção**, **REJEITADO** como medida de incerteza | [INFERÊNCIA] 2 % provavelmente **subestima** a sensibilidade real: δ depende de raios atômicos cuja dispersão entre fontes/convenções é da ordem de 1-2 % **por elemento**, o que pode mover δ em mais de 2 %. **Texto exigido:** "a menos de 2 % do limiar (**convenção do software**, não estimativa de incerteza)". **Pendência:** substituir por incerteza propagada dos dados de entrada; a divergência de T_f do Cr (1857 °C × 1906,85 °C, `FONTES.txt:85`) é um exemplo concreto de que a incerteza real é maior que 2 % em Ω. **Achado menor [FATO]:** `proximo_do_limiar` é calculado mesmo quando `aplicavel` é falso (`:293`) — só o aviso filtra (`:483`); recomendo devolver `null` quando não aplicável, para não deixar um booleano enganoso no JSON. |
| (v) fração mínima **1e-6** (`analitico.py:166-171`) | **APROVADO** como limite de **resolução de apresentação** | Não tem efeito científico: a contribuição de x = 10⁻⁶ para ΔS é −x ln x·R = 1,15×10⁻⁴ J mol⁻¹K⁻¹ ≈ 1,4×10⁻⁵·R [DERIVAÇÃO] — desprezível; e evita ln(0). **Ressalva importante [INFERÊNCIA]:** um elemento-traço em 10⁻⁶ **continua exigindo todos os seus dados**, inclusive **todos os seus pares** na matriz de entalpias → **um traço pode bloquear ΔH_mix da liga inteira**. Isso deve ser dito na mensagem de indisponibilidade, e recomendo oferecer ao usuário a ação explícita de remover o elemento (nunca remover em silêncio). |
| (vi) **δ nulo / raios de fontes diferentes** (item do relatório HEA, fora do cartão) | **REJEITAR** misturar fontes | δ é definido sobre um **conjunto consistente** de raios (mesma convenção: raio metálico, mesma coordenação, mesma referência). Misturar fontes produz um δ sem significado e **não comparável** entre ligas. **Exigência:** todos os raios de uma análise vêm da **mesma chave de fonte**; se não for possível, δ sai `null` com motivo. Além disso, δ = 0 só é verdade se todos os raios forem iguais; δ pequeno **não** significa ausência de distorção de rede real (o modelo ignora relaxação e transferência de carga). |

**Observação transversal [FATO]:** o código já marca essas escolhas como heurísticas nos comentários
(`analitico.py:61, 63, 69, 238, 251`). O que falta é que isso **apareça ao usuário**, em `definicoes`, com a
palavra "sem fonte" — e não só no código.

---

## 8. Parecer final por bloco, consultas e limitações

### 8.1 Parecer por bloco

| Bloco | Parecer | Condições |
|---|---|---|
| Motor térmico — dilatação | **validado com ressalvas** | T-1 (suprimir valores acima de T_f), T-2 (declarar isotropia), T-3 (dado em rascunho ⇒ sem produção) |
| Motor térmico — Lindemann | **validado com ressalvas graves de interpretação** | renomear para deslocamento RMS; truncar/avisar abaixo de ~100 K; declarar f = 0,10 como limite inferior e incerteza de ordem de grandeza |
| Motor térmico — regra das misturas | **validado com ressalvas** | T-6 obrigatória: "T_f nominal, não solidus/liquidus"; nunca afirmar "é líquido" para liga; declarar base atômica |
| Motor térmico — alotropia | **rejeitado para produção** | T-8/T-9: submeter à PoliticaDados e registrar na procedência; fonte pelo Agente 15 |
| Motor térmico — notas 0,3/0,5 T_f | **validado com ressalvas** | condicionar a deformação prévia; acrescentar fonte a `fontes_modelo` (T-5, T-7) |
| HEA — ΔS_mix, δ, VEC, T_m, curva −TΔS | **validado** (como descritores) | rótulos de §6; vocabulário de triagem (já correto no backend) |
| HEA — ΔH_mix, Ω, ΔG_mix | **inconclusivo por falta de dado** | manter `null` com motivo (Q-01); regra "todos os pares ou nenhum" (`analitico.py:390-399`) **aprovada e a preservar** |
| Mapa δ×ΔH do front | **rejeitado como está** | T-14: "zona estável" e a faixa de ΔH sem fonte |
| Item 5 do usuário (análise integrada) | **parcialmente sustentável** | só as linhas A e, com dado, B da matriz §3; linhas N exigem CALPHAD ou são extrapolação |
| CALPHAD | **decisão pendente do usuário** (D-TERMO-01) | §4 |
| Cinética | **rejeitado nesta rodada** | §5.1; animações com os rótulos de §5.3, incluindo T-15 |
| Revisão 7.a (FEA do HC) | **aprovado com ressalvas** R-1, R-2, R-3 | §7.a |
| Revisão 7.b (heurísticas) | aprovados (i), (iii cond.), (iv), (v-fração); **ajustar** (ii) e o texto de (v-margem); **rejeitar** mistura de fontes de raio | §7.b |

### 8.2 Consultas para o Supervisor encaminhar

| ID | Destinatário | Pedido |
|---|---|---|
| C-07-A | academic-research-auditor (15) | Fonte primária do critério de Lindemann **com a convenção de f** (√⟨u²⟩ 1D ou 3D; faixa 0,10-0,15 e a que estrutura/metais se aplica) |
| C-07-B | academic-research-auditor (15) | Fontes para as **transições alotrópicas** de Fe, Co e Ti (temperaturas, fases, estruturas, pressão de referência, incerteza) e para os **T_f** e **α** do seed v1.4; resolver a divergência do Cr (1857 °C × 2180 K) |
| C-07-C | academic-research-auditor (15) | Fonte (se existir) da faixa **−15 < ΔH_mix < 5 kJ/mol** usada no mapa do front (`HeaCharts.tsx:66`); e da atribuição do limiar δ ≤ 6,6 % a Yang & Zhang (2012) |
| C-07-D | academic-research-auditor (15) | Fonte das faixas de **temperatura homóloga** (0,3-0,5 T_f: recuperação/recristalização; fluência) com edição e seção |
| C-07-E | academic-research-auditor (15) | Existência, **licença** e **cobertura** de motor CALPHAD aberto e de bases TDB abertas para **Fe-Cr-C** e **Al-Co-Cr-Fe-Ni**, e compatibilidade com Python 3.15/Windows (insumo da decisão D-TERMO-01) |
| C-07-F | hea-specialist (via Supervisor) | Formato do seed de entalpias binárias deve prever **incerteza por par** e **chave de fonte única por conjunto de raios** (§7.b, itens iv/v/vi) |
| C-07-G | frontend-engineer / integration-engineer | T-10, T-11, T-14, T-15 e **T-16** (amplitude por componente ⇒ √3·u; "1× = real" incorreto) |
| C-07-H | backend-engineer | T-1, T-6, T-8, T-9 (política de dados nas transições e registro na procedência) |

### 8.3 Pendências que exigem **decisão do usuário**

1. **D-TERMO-01 — CALPHAD:** não adotar (recomendado nesta rodada) / investigar / contratar (§4).
2. **D-TERMO-02 — escopo publicado do item 5:** aprovar o enunciado honesto de §3.1 e aceitar que
   diagramas, frações de fase, partição e fases candidatas ficam **fora de escopo** até haver base de dados.
3. **D-TERMO-03 — validação dos dados v1.4:** sem a validação humana com fonte (Q-03), **o módulo térmico não
   funciona em produção**. Decidir: validar com fonte, substituir pela tabela periódica importada (que tem
   DOI e licença, `FONTES.txt`) ou manter o módulo como recurso apenas de desenvolvimento.
4. **D-TERMO-04 — entalpias binárias (Q-01):** autorizar a criação do seed com fonte e licença verificadas
   (de que depende tudo marcado "B" na matriz §3) ou manter ΔH_mix/Ω permanentemente indisponíveis.
5. **D-TERMO-05 — animação α→γ:** aceitar o selo "Ilustrativo" obrigatório (T-15) ou remover a animação.

### 8.4 Limitações e incertezas deste parecer

1. **Nenhuma referência foi conferida na fonte** (sem acesso à web): nenhuma afirmação baseada em literatura
   está verificada; não invento página, edição nem DOI.
2. **Não executei nada:** nenhum teste, nenhum script, nenhum motor. As derivações numéricas de §7.a e §7.b são
   **aritmética manual** (precisão estimada ~10⁻⁶ relativo); os valores de regressão devem ser gerados pelo
   código, não copiados daqui.
3. **Li apenas os arquivos listados no cartão.** Em particular **não li**: os textos i18n (T-12), `textos.py`
   do HEA, `sitios.py`, `SidePanels.tsx` na íntegra, os testes, `docs/MOTOR_CIENTIFICO.md` e
   `docs/MOTOR_HEA.md`. Achados de rotulagem no frontend podem estar já cobertos por textos que não vi.
4. **Fatos de ambiente** (Python 3.15.1; ausência de numpy/scipy/pycalphad/TDB) foram **informados pelo
   supervisor**, não verificados por mim.
5. A plausibilidade das temperaturas de transição e de fusão (§2.6) é **julgamento de especialista**, não
   verificação: nenhum valor do seed pode ser declarado correto sem C-07-B.
6. Não avaliei desempenho, acessibilidade, nem o impacto de UX das mudanças de rótulo propostas.
7. O repositório está com **muitos arquivos modificados e não commitados** (git status da sessão): este parecer
   descreve o estado dos arquivos **como lidos hoje, 2026-11-13**, não um commit.
