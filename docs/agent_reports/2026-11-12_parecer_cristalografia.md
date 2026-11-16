# R1-CRI-01 — Parecer de cristalografia: validação das estruturas, auditoria de ligas e especificação G1

Autor: crystallography-engineer (Agente 09). Destinatário: Supervisor (Agente 01). Data: 12/11/2026.
Estado do documento: EM ELABORAÇÃO (gravado por partes; seções marcadas "[pendente]" ainda não foram preenchidas).

Legenda de natureza das afirmações: **[FATO]** observado em execução minha nesta tarefa; **[DERIVAÇÃO]** resultado
analítico demonstrado no texto; **[INFERÊNCIA]** conclusão a partir de fatos; **[RECOMENDAÇÃO]** proposta;
**[NÃO VERIFICADO]** afirmação de literatura que não pude conferir na fonte (a verificar pelo auditor bibliográfico).

## 0. Escopo, método e linha de base

- **Escopo:** motor `backend/app/engines/crystallography/` (`estruturas.py`, `geometria.py`, `supercelula.py`,
  `celula.py`, `ligas.py`, `constantes.py`), contrato `backend/app/api/v1/schemas.py` (linhas 370–443), seeds
  `database/seeds/cristalografia/metais.json` e `propriedades_v14.json`. Nenhum código de produção foi alterado.
- **Método:** dois scripts de leitura executados com `cwd = backend/` e `../.venv/Scripts/python` (Python 3.15.1, sem numpy):
  - `cri_val_estruturas.py` — importa o motor, gera a supercélula e, de forma independente, reduz as posições
    módulo n, conta vizinhos com condição periódica, calcula volume por determinante e FEA por esferas em contato;
  - `cri_aud_ligas.py` — chama `calcular_solucao_solida` e a API (`TestClient`, `Settings(_env_file=None)`), reduz os
    átomos desenhados aos átomos únicos e compara elementos/contagens; verifica os sítios intersticiais.
  - Ambos estão em `C:\Users\JORGEF~1\AppData\Local\Temp\claude\853d3254d3b39e1a\1ab1e244-7dd8-4076-a7e9-688d77eedfbc\scratchpad\`
    (com as saídas `saida_estruturas.txt` e `saida_ligas.txt`). Não estão no repositório.
- **Linha de base:** commit `93755eb` + alterações não commitadas de trabalho anterior. `.env` não foi lido.
- **Dados de fases:** busca por `solubil|diagrama de fases|limite_solub|phase_diagram|cementita|Fe3C` em `backend/app/**`
  e `database/**` só encontra texto de regras em `ligas.py`, `schemas.py` e `termico.py`; **não há dado de diagrama
  de fases, limite de solubilidade nem fase secundária** nos seeds [FATO].

### 0.1 Convenções do motor (conferidas)

| Item | Convenção | Onde |
|---|---|---|
| Unidade de posição | cartesiana em unidades de `a` (adimensional); `a`, `c`, `R` em nm; densidade em g/cm³; massa molar em g/mol | `geometria.py:3-7`, `celula.py` |
| Referencial cúbico | eixos x, y, z ao longo de a₁, a₂, a₃; origem num vértice ocupado | `geometria.py:4` |
| Referencial HC | a₁ = (1, 0, 0), a₂ = (−½, √3/2, 0), c = (0, 0, c/a); ângulo a₁^a₂ = 120,0000° [FATO] | `geometria.py:5-6, 131-136` |
| Fracionária ↔ cartesiana (HC) | x = f₁ − f₂/2, y = (√3/2)·f₂, z = f₃·c/a; ida e volta exata em (0,37; −0,21; 0,83) [FATO] | `geometria.py:44-53` |
| Célula replicada na supercélula | cúbicas: célula convencional; HC: célula **primitiva** hexagonal (2 átomos) | `supercelula.py:3-5` |
| Célula desenhada no módulo de célula | cúbicas: convencional; HC: **prisma hexagonal** (3 primitivas, n = 6) | `geometria.py:101-123` |
| N_A | 6,02214076 × 10²³ mol⁻¹ (exato no SI) | `constantes.py:9` |
| R | raio atômico tabelado (modelo de esferas rígidas); **não é** parâmetro de rede nem distância interplanar | `celula.py` |

## 1. Validação das quatro estruturas (CS, CCC, CFC, HC)

Comando: `cd backend && ../.venv/Scripts/python <scratchpad>/cri_val_estruturas.py` (saída integral em `saida_estruturas.txt`).

### 1.1 Tabela de conferência (rede ideal)

Referência = derivação analítica do modelo de esferas rígidas (geometria elementar, demonstrada em 1.2); é o mesmo
resultado dos livros-texto de ciência dos materiais (Callister & Rethwisch, capítulo de estruturas cristalinas —
**edição e página não verificadas por mim; a conferir pelo auditor**).

| Estrutura | Grandeza | Valor do motor | Referência (analítica) | Método independente | Resultado |
|---|---|---|---|---|---|
| CS | n (átomos/célula) | 1 | 8 × 1/8 = 1 | soma das frações do desenho = 1,000000; únicos mod n = n³ (1, 8, 27, 64) | confere |
| CS | NC e d₁ | 6 | 6 a d = a | contagem periódica em 3×3×3: camadas (1,0 a; 6), (1,414214; 12), (1,732051; 8); NC = 6 em todos os 27 átomos | confere |
| CS | a(R) | 2,000000000 R | a = 2R | 2/d₁ = 2,000000000 | confere |
| CS | FEA | 0,523598776 | π/6 = 0,523598776 | Z·(4/3)π(d₁/2)³/det(a₁,a₂,a₃) = 0,523598776 | confere |
| CCC | n | 2 | 8 × 1/8 + 1 = 2 | soma das frações = 2,000000; únicos = 2n³ (2, 16, 54, 128) | confere |
| CCC | NC e d₁ | 8 | 8 a d = (√3/2)a = 0,866025 a | camadas (0,866025; 8), (1,0; 6), (1,414214; 12); NC = 8 nos 54 | confere |
| CCC | a(R) | 2,309401077 R | 4/√3 = 2,309401077 | 2/d₁ = 2,3094 (6 casas da distância) | confere |
| CCC | FEA | 0,680174762 | π√3/8 = 0,680174762 | esferas em contato: 0,68017 | confere |
| CFC | n | 4 | 8 × 1/8 + 6 × 1/2 = 4 | soma das frações = 4,000000; únicos = 4n³ (4, 32, 108, 256) | confere |
| CFC | NC e d₁ | 12 | 12 a d = a/√2 = 0,707107 a | camadas (0,707107; 12), (1,0; 6), (1,224745; 24); NC = 12 nos 108 | confere |
| CFC | a(R) | 2,828427125 R | 2√2 = 2,828427125 | 2/d₁ = 2,82843 | confere |
| CFC | FEA | 0,740480490 | π/(3√2) = 0,740480490 | esferas em contato: 0,74048 | confere |
| HC ideal | n do prisma / z da primitiva | 6 / 2 | 12 × 1/6 + 2 × 1/2 + 3 = 6; primitiva = 2 | soma das frações = 6,000000; V(prisma)/V(primitiva) = 3,000000000; únicos = 2n³ | confere |
| HC ideal | NC e d₁ | 12 | 6 no plano basal (a) + 6 fora do plano (a) | camadas (1,0; 12), (1,414214; 6), (1,632993; 2); NC = 12 nos 54 | confere |
| HC ideal | a(R) | 2,000000000 R | a = 2R | 2/d₁ = 2,000000000 | confere |
| HC ideal | c/a | 1,632993161855 | √(8/3) = 1,632993161855 | d(fora do plano) = √(1/3 + (c/a)²/4)·a = 1,000000000000 a | confere |
| HC ideal | FEA | 0,740480490 | π/(3√2) = 0,740480490 | esferas em contato: 0,740480490 | confere |
| Todas | periodicidade da supercélula | — | Z·n³ átomos únicos; imagens só em coordenada = n | nenhum átomo desenhado duplicado (menor distância = d₁); toda imagem tem origem presente; 12 arestas | confere |
| Todas | grupo espacial / Wyckoff do CIF | Pm-3m 1a; Im-3m 2a; Fm-3m 4a; P6₃/mmc 2c | multiplicidade = z | órbita do sítio sob as operações exportadas: 1, 2, 4, 2 = z; órbita geral: 48, 96, 192, 24 | confere (ver ressalva HC-3) |
| 15 metais do seed | densidade teórica | ver saída | ρ = n·A/(V_c·N_A) | cálculo independente idêntico em 4 casas; desvio vs. densidade do seed entre −0,59 % e +0,68 % | confere |

Contagens de átomos desenhados × únicos [FATO]: CS 8/1, 27/8, 64/27, 125/64; CCC 9/2, 35/16, 91/54, 189/128;
CFC 14/4, 63/32, 172/108, 365/256; HC (primitiva) 9/2, 35/16, 91/54, 189/128 para n = 1, 2, 3, 4.

### 1.2 Derivações de referência [DERIVAÇÃO]

- **CS:** contato na aresta, a = 2R; FEA = (4/3)πR³/(2R)³ = π/6.
- **CCC:** contato na diagonal do cubo, √3·a = 4R; FEA = 2·(4/3)πR³/(4R/√3)³ = π√3/8.
- **CFC:** contato na diagonal da face, √2·a = 4R; FEA = 4·(4/3)πR³/(2√2·R)³ = π/(3√2).
- **HC ideal:** átomo B sobre o baricentro de um triângulo de átomos A: distância horizontal a/√3, vertical c/2;
  contato exige (a/√3)² + (c/2)² = a² ⇒ c/a = √(8/3). Volume da primitiva = (√3/2)·a²·c; FEA = 2·(4/3)π(a/2)³/((√3/2)a²c) =
  π/(3√2) quando c/a = √(8/3).
- **Limite superior:** π/(3√2) ≈ 0,74048 é a maior fração de empacotamento de esferas rígidas iguais (conjectura de
  Kepler, demonstrada por Hales) [NÃO VERIFICADO na fonte; resultado matemático de conhecimento geral — referência a
  registrar pelo auditor]. Nenhum arranjo de esferas iguais **sem sobreposição** ultrapassa esse valor.

### 1.3 HC: célula, base, origem e c/a (pedido explícito do usuário)

- **Célula escolhida** [FATO]: há duas, usadas em lugares diferentes, e isso precisa ficar explícito na interface.
  (i) módulo de célula (`/cells`, `geometria._geometria_hc`) e viewer: **prisma hexagonal**, 17 esferas desenhadas
  (12 vértices × 1/6, 2 centros basais × 1/2, 3 interiores × 1) = **6 átomos**, volume (3√3/2)a²c;
  (ii) supercélula, ligas e CIF: **célula primitiva hexagonal**, **2 átomos**, volume (√3/2)a²c. O prisma equivale a
  exatamente 3 primitivas (razão medida 3,000000000) — é uma célula didática, não a célula convencional do grupo espacial.
- **Base** [FATO]: no referencial do motor, (0, 0, 0) e (2/3, 1/3, 1/2) (`estruturas.py:53`). O CIF usa a posição de
  Wyckoff 2c de P6₃/mmc (nº 194), (1/3, 2/3, 1/4) e (2/3, 1/3, 3/4). As duas descrições são a **mesma estrutura com a
  origem deslocada de (1/3, 2/3, 1/4)**: somando esse vetor à órbita 2c obtém-se a base do motor (verificado numericamente).
- **c/a ideal × real** [FATO]: ideal √(8/3) = 1,632993. Metais cadastrados: Mg 1,6240 (−0,55 %), Ti 1,5873 (−2,80 %,
  de a e c medidos), Zn 1,8560 (+13,66 %), Co 1,6230 (−0,61 %). Os valores de c/a vêm do seed; **não conferi as fontes
  primárias desses números** (pedido ao auditor, seção 4).
- **Consequência geométrica do c/a real** [FATO]: fora do ideal os 12 vizinhos deixam de ser equidistantes. Contagem
  periódica: Mg 6 a 0,996332 a + 6 a 1,000000 a; Ti 6 a 0,981417 a + 6 a 1,000000 a; Co 6 a 0,995924 a + 6 a 1,000000 a;
  Zn 6 a 1,000000 a + 6 a 1,092939 a. NC = 12 continua sendo a descrição usual, mas como **6 + 6**.

### 1.4 Achado E-1 — FEA do HC com c/a real: **CONFIRMADO**

**Reprodução** [FATO] (motor, `fator_empacotamento("HC", c_a)`; coluna "esferas rígidas" = cálculo independente com
R = d_mín/2):

| Metal | c/a | d fora do plano (em a) | FEA do motor (R = a/2) | Sobreposição com R = a/2? | FEA de esferas rígidas (R = d_mín/2) |
|---|---|---|---|---|---|
| Mg | 1,6240 | 0,996332 | 0,744581 | sim (d < 2R) | 0,736418 |
| Ti | 1,5873 | 0,981418 | 0,761816 | sim | 0,720132 |
| Co | 1,6230 | 0,995924 | 0,745040 | sim | 0,735968 |
| Zn | 1,8560 | 1,092940 | 0,651508 | não | 0,651508 |
| ideal | 1,6330 | 1,000000 | 0,740480 | não (contato) | 0,740480 |

Varredura: c/a = 1,50 → motor 0,806133 × esferas rígidas 0,683514; c/a = 1,60 → 0,755750 × 0,725722.

**Causa-raiz:** `geometria.py:62-72` fixa R = a/2 (`a_em_R = 2`) para qualquer c/a e calcula FEA = n·(4/3)πR³/V_c.
Quando c/a < √(8/3), a distância entre planos vizinhos é menor que a: as esferas de raio a/2 **se interpenetram**, o
volume de sobreposição é contado duas vezes e o resultado passa de 0,7405.

**O que é fisicamente correto** [DERIVAÇÃO]: para esferas rígidas o raio é metade da menor distância entre vizinhos,
R_c = ½·mín(a, d_fora), com d_fora = a·√(1/3 + (c/a)²/4). Então
FEA_rígidas = 2·(4/3)π·R_c³ / ((√3/2)·a²·c) = (2π/(3√3))·(2R_c/a)³ / (c/a); na forma usada no script:
`2*(4/3)*pi*(dmin/2)**3 / ((sqrt(3)/2)*c_a)` com distâncias em unidades de a (conferência: com 2R_c/a = 1 e
c/a = √(8/3) dá 1,2092/1,63299 = 0,74048). Esse valor **nunca** excede 0,74048
e tem o máximo exatamente em c/a = √(8/3). Para c/a ≥ ideal coincide com o valor atual do motor.

**Textos do motor que ficam errados fora do ideal** [FATO] (saída para Mg e Ti):
- "Cada átomo tem 12 vizinhos a essa distância (NC = 12)" com d = 2R = a — falso para c/a ≠ ideal (são 6 + 6).
- "As esferas rígidas se tocam ao longo da aresta do hexágono basal" — para c/a < ideal o primeiro contato é entre planos.
- "FEA = FEA_ideal × (c/a)_ideal/(c/a) … acima do ideal os planos basais se afastam e o FEA cai" — a fórmula é
  apresentada como geral, mas abaixo do ideal produz valor acima do limite de empacotamento.
- Para Ti o motor já mostra um segundo número, "Com a rede medida: FEA = 0,7155" (`passos.py:96`), que usa o raio tabelado
  e o volume medido: é um terceiro critério (R tabelado = 0,1445 nm; d_mín/2 = 0,14481 nm).

**Correção proposta** [RECOMENDAÇÃO] (mudança de fórmula → exige aprovação do supervisor e parecer do materials-science):
1. Manter `fea` como está **somente** quando c/a ≥ ideal; para c/a < ideal devolver `fea` calculado com
   R_c = d_fora/2 (esferas rígidas sem sobreposição). Alternativa conservadora e aditiva: manter `fea` e acrescentar
   `fea_esferas_rigidas`, `raio_contato_rel` (= R_c/a), `contato` ("basal" | "entre_planos" | "ambos") e um aviso
   obrigatório quando `fea > π/(3√2)`. Recomendo a primeira, porque um FEA > 0,7405 é resultado enganoso.
2. Rotular a natureza: `c_a_natureza` = "ideal" | "tabelado" | "derivado_de_a_c_medidos" | "informado".
3. Devolver as duas distâncias de primeiros vizinhos (basal e entre planos, em a e em nm) e trocar o texto de NC para
   "6 + 6" quando |c/a − ideal| > tolerância (sugestão: 1 × 10⁻⁴ relativo, a mesma `TOLERANCIA_EDICAO`).
4. Em nenhum caso o FEA de um metal real deve ser lido como "empacotamento medido": é propriedade do modelo de esferas
   rígidas aplicado à geometria; isso deve constar no texto.

### 1.5 Ressalvas adicionais

| ID | Ressalva | Evidência | Severidade |
|---|---|---|---|
| HC-1 | `relacao "a = 2R"` e `contato "aresta do hexágono basal"` valem só para c/a ≥ ideal | 1.4 | média |
| HC-2 | n = 6 (prisma) e z = 2 (primitiva) coexistem; a interface precisa dizer qual célula está desenhada e qual foi usada no cálculo (o FEA e a densidade são iguais nas duas, a contagem não) | 1.3 | baixa (didática) |
| HC-3 | Base do motor e sítio de Wyckoff do CIF diferem por deslocamento de origem (1/3, 2/3, 1/4); coordenadas fracionárias exibidas no inspetor não coincidem com as do CIF | 1.3 | baixa (documentar) |
| A-1 | Para metais sem rede medida, `a` é **derivado de R** pelo modelo de contato (`a_fonte = derivado_de_R`); só Ti usa a e c medidos. O rótulo existe na resposta e deve aparecer na interface: a derivado de R não é parâmetro de rede experimental | saída E do script: 14 metais `derivado_de_R`, Ti `medido` | média (rotulagem) |
| A-2 | As estruturas são as do seed (uma por elemento, condição ambiente presumida). Fe aparece só como CCC; alotropia existe em `propriedades_v14.json` em estado `rascunho`, sem fonte | seed, linhas 654–717 | média |
| A-3 | Po como CS: único caso de CS; estrutura e raio vêm do seed, não conferidos na fonte | seed | baixa (auditor) |

### 1.6 Parecer por estrutura

| Estrutura | Parecer | Fundamento |
|---|---|---|
| CS | **validado** | n, NC, a(R), FEA, periodicidade e Wyckoff conferem por contagem e por derivação |
| CCC | **validado** | idem |
| CFC | **validado** | idem |
| HC ideal (c/a = √(8/3)) | **validado** | idem; célula (prisma × primitiva), base e origem explicitadas em 1.3 |
| HC com c/a real | **validado com ressalvas — FEA rejeitado para c/a < ideal** | geometria, posições, periodicidade, volume e densidade corretos; FEA, texto de contato e de NC incorretos quando c/a < √(8/3) (E-1, HC-1) |

O parecer cobre geometria e fórmulas do modelo. **Não** é validação dos dados de material do seed (raios, c/a, massas,
densidades), que dependem de auditoria bibliográfica.

## 2. Auditoria da representação de ligas

Comando: `cd backend && ../.venv/Scripts/python <scratchpad>/cri_aud_ligas.py` (saída integral em `saida_ligas.txt`).
"Átomo único" = classe de posições fracionárias iguais módulo n (um átomo da supercélula periódica); "desenhado" =
esfera devolvida em `atomos` (únicos + imagens de fronteira). Severidade: crítica = resultado científico enganoso
exibido como se fosse correto; alta = requisito do usuário não atendido; média = hipótese não rotulada ou
inconsistência entre módulos; baixa = robustez/rotulagem.

### 2.1 Resumo dos achados

| ID | Achado | Situação | Severidade |
|---|---|---|---|
| L-1 | Sorteio do soluto substitucional sobre átomos desenhados; imagens do mesmo átomo com elementos diferentes; contagem e composição não correspondem à supercélula periódica | **confirmado** | crítica |
| L-5 | Intersticiais: quantidade calculada sobre átomos desenhados, mínimo forçado de 1 átomo e sorteio sobre sítios desenhados (periodicidade quebrada; o mesmo sítio contado mais de uma vez) | novo | crítica |
| L-2 | Só liga binária; `solutos` → 422; Fe–Cr–C não é representável; Mn e Si não cadastrados | **confirmado** | alta |
| L-3 | Só um tipo de sítio por estrutura; sem tetraédricos; sem identificador, sítio, ocupação ou fase por átomo; comentário "maior sítio" é falso para CCC | **confirmado, com correção** | alta |
| L-4 | Nenhuma verificação de limite de solubilidade nem de fases secundárias; todo o soluto é posto na matriz; textos de conclusão afirmam solubilidade | **confirmado** | alta |
| L-6 | Protótipos ordenados: contagem por esferas desenhadas (25 % aparece como 27/63 = 42,9 %); tolerância de ±2 % faz composição exibida ≠ composição usada nos cálculos; grupo espacial e tetragonalidade da fase ordenada não informados | novo | média |
| L-7 | Solvente com rede medida (Ti): a liga ignora `a` medido e usa a = 2R; densidade do Ti "puro" na liga difere da do módulo de célula | novo | média |
| L-8 | "Lei de Vegard" aplicada a raios tabelados, inclusive de soluto com outra estrutura/coordenação; c/a do solvente mantido | novo | média (rotulagem) |
| L-9 | Densidade com intersticial calculada com a rede do solvente não dilatada | novo | média (rotulagem) |
| L-10 | Raio livre do sítio em HC usa sempre o fator do c/a ideal | novo | baixa |
| L-11 | `semente = 0` é trocada por 1 em silêncio | novo | baixa |
| L-12 | Distorção ilustrativa aplicada a átomos desenhados: cópias do mesmo átomo recebem deslocamentos diferentes; `frac` não é atualizada | novo | baixa |
| L-13 | `x = 100` aceito (solvente ausente) | novo | baixa |
| OK-1 | Conversão % atômica → % em massa (substitucional e intersticial) | **validada** | — |
| OK-2 | Fatores de raio livre implementados (CS cúbico 0,7321; CCC oct. 0,1547; CFC oct. 0,4142; HC ideal oct. 0,4142), número e posição dos sítios octaédricos | **validados** | — |
| OK-3 | Posições dos protótipos L1₂, L1₂ invertida, L1₀ e B2 nos átomos únicos (25, 75, 50 e 50 %) e ausência de imagens inconsistentes no modo ordenado | **validadas** (geometria; ver L-6) | — |

### 2.2 L-1 — sorteio sobre átomos desenhados (crítica) — CONFIRMADO

- **Reprodução:** `{"base":"Fe","soluto":"Cr","x":12,"n":2,"semente":1}` →
  `desenhados=35 n_soluto=4 n_solvente=31` (round(0,12 × 35) = 4; fração desenhada 11,43 %); átomos únicos = 16.
  Classes com imagens de elementos diferentes: 2 —
  `átomo único (0,0,0): 8 cópias desenhadas -> ['Fe','Cr','Fe','Fe','Fe','Fe','Fe','Fe']` e
  `átomo único (0,1,1): 2 cópias -> ['Cr','Fe']`. Só 2 átomos únicos são inteiramente Cr.
- **Varredura de 200 sementes:** imagens inconsistentes em **200/200** (n = 2) e **200/200** (n = 3). Cr entre os átomos
  de origem (coordenadas < n): n = 2 → {0: 17, 1: 62, 2: 76, 3: 40, 4: 5} sementes (esperado 2 de 16); n = 3 →
  de 2 a 10 (esperado 6 de 54). A composição da caixa periódica varia de 0 a 25 at% para um pedido de 12 at%.
- **Causa-raiz:** `supercelula.py:19-27` (`pontos_na_caixa` devolve as bordas, de propósito, para o desenho);
  `ligas.py:228` usa essa lista como se fosse a lista de átomos; `ligas.py:254`
  `rng.sample(range(len(atomos)), round(x * len(atomos)))` sorteia sobre ela; `ligas.py:266` e `:299` contam
  `n_soluto`/`n_solvente` sobre as esferas.
- **Impacto:** o desenho não é uma célula periódica (um átomo de vértice é Fe num canto e Cr em outro); os números
  exibidos (4 Cr, 31 Fe) não são a composição de nada físico. O teste atual
  `test_aleatorio_e_reprodutivel_pela_semente` fixa esse comportamento (`n_soluto == round(0.30 * len(atomos))`).
- **Correção:** seção 3.1–3.2 (sortear sobre os Z·n³ átomos únicos; imagem herda o elemento da origem; contar só únicos).

### 2.3 L-5 — intersticiais: quantidade e sítios (crítica)

- **Reprodução:** `{"base":"Fe","soluto":"C","x":4,"n":2,"semente":1}` → `desenhados=36 n_soluto=1 n_solvente=35`,
  C em `frac=[0.0, 1.5, 0.5]` (sítio de face na fronteira x = 0, **sem** a imagem em x = 2).
  O motor calcula round(35 × 0,04/0,96) = 1 sobre 35 esferas; a supercélula tem 16 Fe, para a qual o valor exato é
  16 × 0,04/0,96 = 0,667. Composição lida no desenho: 1/36 = 2,78 at%; composição real da caixa (1 C, 16 Fe): 5,88 at%;
  pedido: 4 at%. Nenhum desses números é devolvido.
- **Mínimo forçado:** `x = 0,01 at%`, n = 1 → 1 C para 2 Fe únicos (33 at% representados para 0,01 at% pedidos).
  Tabela completa (x; n; C do motor; C exato periódico) na saída, p. ex. 0,5 %/n=2 → 1 × 0,080; 20 %/n=2 → 9 × 4,000.
- **Sítios desenhados:** CCC n = 2 → 90 sítios na lista sorteada × 48 sítios únicos (6 por célula × 8). Em 200 sementes
  (x = 8 at%): periodicidade quebrada (sítio de fronteira ocupado sem todas as suas imagens) em 197/200 (Fe–C, n = 2),
  200/200 (Fe–C, n = 3), 200/200 (Cu–C CFC, n = 2 e 3); o mesmo sítio único contado mais de uma vez (sítio e imagem
  sorteados como dois átomos) em 8, 19, 40 e 92 de 200. HC: 0/200, porque os dois sítios octaédricos são interiores.
- **Causa-raiz:** `ligas.py:235` (`pontos_na_caixa(SITIOS[...]["frac"], n)` com bordas) e `ligas.py:236`
  (`min(len(sitios), max(1, round(len(atomos) * x / (1.0 - x))))`: usa `len(atomos)` desenhados e força ≥ 1).
- **Correção:** seção 3.1–3.2 e 3.4.

### 2.4 L-2 — só binária (alta) — CONFIRMADO

- **Reprodução (API):** `{"base":"Fe","solutos":[{"elemento":"Cr","x":12},{"elemento":"C","x":2}]}` → **422**
  `"Validação falhou em 'soluto': campo obrigatório"`. `{"base":"Fe","soluto":"Si","x":2}` e `...,"soluto":"Mn"` →
  **400** `MATERIAL_DESCONHECIDO`.
- **Causa-raiz:** `schemas.py:370-382` (`extra="forbid"`, `soluto: str` obrigatório); `ligas.py:160-165` (um soluto;
  substitucional × intersticial decidido só pela lista de intersticiais C, H, N do seed).
- **Cobertura de dados:** substitucionais = 15 metais de `metais.json`; intersticiais = C, H, N, com raio e massa em
  estado `rascunho`, sem fonte (`propriedades_v14.json`; em produção o pedido Fe–C é recusado — teste existente
  `test_intersticial_em_producao_exige_dado_validado`).

### 2.5 L-3 — sítios e campos por átomo (alta) — CONFIRMADO, com correção

- `SITIOS` (`ligas.py:32-42`) tem um tipo de sítio por estrutura e o comentário "Maior sítio intersticial de cada
  rede". **Para CCC isso é falso** [FATO]: octaédrico r/R = 0,15470; tetraédrico r/R = 0,29099 (seção 3.4). O sítio
  octaédrico é a escolha usual para C em ferro CCC, mas não por ser o maior.
- CCC octaédrico é irregular: 2 vizinhos a a/2 e 4 a a/√2 [FATO]; o motor devolve `nc = 6` sem essa distinção.
- `AtomoLiga` (`schemas.py:393-398`) tem só `pos`, `frac`, `tipo`, `elemento`, `raio_rel` (confirmado na resposta da
  API): sem identificador, sítio, ocupação, fase, marca de imagem nem posição em nm.
- O que está correto (OK-2): posições e número dos sítios implementados — CS 1/célula, CCC oct. 6/célula, CFC oct.
  4/célula, HC oct. 2/primitiva — e os fatores, todos reproduzidos por contagem de vizinhos.

### 2.6 L-4 — solubilidade e fases (alta) — CONFIRMADO

- Fe–C com 4 at% (= 0,8881 % em massa, conferido de forma independente) é desenhado inteiramente como C dissolvido na
  rede CCC do Fe. O repositório não tem como dizer se isso é possível; o motor não avisa.
- Textos de conclusão que afirmam solubilidade a partir de critério geométrico [FATO]:
  Cu–H, Ti–H e Po–H → "O soluto cabe no sítio sem distorção: **solubilidade intersticial alta**" (`ligas.py:211-212`);
  substitucional com as 4 regras atendidas → "**solubilidade sólida extensa, possivelmente completa**" (`ligas.py:122`).
  As regras de Hume-Rothery e de Hägg são critérios empíricos de favorabilidade; não são previsão de limite de
  solubilidade [INFERÊNCIA a partir do próprio enunciado das regras; redação a validar pelo materials-science].
- O solvente entra sempre com a estrutura do seed (Fe = CCC). Não há como pedir Fe CFC (austenita).
- **Correção:** seção 3.7 (avisos obrigatórios e campos `null` com motivo) e 3.3 (reformulação dos textos).

### 2.7 L-6 — protótipos ordenados (média)

| Pedido | Fase devolvida | `n_soluto`/desenhados | Átomos únicos | Observação |
|---|---|---|---|---|
| Cu–Au 25 %, n = 2, ordenado | L1₂ | 27/63 = 42,9 % | 8/32 = 25,00 % | contagem exibida não é a estequiometria |
| Cu–Au 50 % | L1₀ | 39/63 = 61,9 % | 16/32 = 50,00 % | célula mantida cúbica (L1₀ real é tetragonal — [NÃO VERIFICADO], auditor) |
| Cu–Au 75 % | L1₂ invertida | 36/63 = 57,1 % | 24/32 = 75,00 % | |
| Fe–Cr 50 % | B2 | 8/35 = 22,9 % | 8/16 = 50,00 % | par não ordena assim; aviso de hipotético já existe |
| Fe–Cr 48,5 % | B2 | 8/35 | 8/16 = 50,00 % | `x_pct = 48,5`, `pct_peso = 46,719`, `a_nm` calculados com 48,5 %; desenho com 50 % |
| Cu–Au 27 % | nenhuma (cai em aleatório) | 17/63 | 10/32 = 31,25 %, 8 classes inconsistentes | herda L-1 |

Causa: `ligas.py:62-71` (tolerância |x − x₀| ≤ 0,02) e `:243-249`. `estrutura` devolvida continua "CFC"/"CCC",
embora a fase ordenada tenha outro grupo espacial (L1₂ e B2: rede cúbica primitiva). Correção: seção 3.6.

### 2.8 L-7 a L-13 (média/baixa)

- **L-7** [FATO]: módulo de célula, Ti: `a = 0,2951 nm (medido)`, ρ = 4,5005 g/cm³. Liga com solvente Ti e x = 0:
  `a_nm = 0,28900`, `densidade = densidade_base = 4,7915` (+6,5 %). Causa: `ligas.py:188` (`a_base = k * base.raio_nm`)
  ignora `metal.tem_rede_medida`. Para Fe (sem rede medida) os dois módulos coincidem (0,28660 nm; 7,8793 g/cm³).
- **L-8** [FATO]: Fe (CCC) + 10 % Ni (CFC) → a = 0,28671 nm, obtido com o raio do Ni tabelado para a sua própria
  estrutura aplicado a 4R/√3 (`ligas.py:216-217`). A regra é uma interpolação linear de raios tabelados na estrutura
  do solvente; a lei de Vegard propriamente dita interpola parâmetros de rede de fases de mesma estrutura
  [NÃO VERIFICADO na fonte de 1921; auditor]. A classe `estimativa_modelo` já é devolvida; falta dizer a hipótese.
- **L-9** [FATO]: Fe–C 4 at%: `a_nm = a_base_nm = 0,28660`; ρ = 7,9499 × 7,8793 do Fe puro. A massa do C é somada e o
  volume não muda (`ligas.py:195-199, 224-225`): a densidade sobe por construção. Hipótese não declarada na resposta.
- **L-10** [FATO]: raio livre do sítio octaédrico em HC com R = a/2: Mg 0,4116 R; Ti 0,4011 R; Co 0,4113 R; Zn 0,4814 R;
  o motor usa 0,4142 R para todos (`ligas.py:41, 201`).
- **L-11** [FATO]: `semente: 0` → resposta com `semente = 1` e arranjo idêntico ao da semente 1 (`ligas.py:175`,
  `int(payload.get("semente") or 1)`); o schema aceita 0 (`schemas.py:382`).
- **L-12** [FATO]: Cu–Ag 10 %, n = 2, `distorcer: true` → 18 de 32 átomos únicos têm cópias com deslocamentos
  diferentes; `frac` continua com o valor ideal (`ligas.py:129-154`). A classe `simulacao_ilustrativa` é devolvida.
- **L-13** [FATO]: Cu–Ni com x = 100 → `n_solvente = 0`, estrutura CFC do Cu, a = 0,35242 nm.

## 3. Especificação científica G1 — ligas multicomponentes

Tudo nesta seção é [RECOMENDAÇÃO] para o contrato (api-architect) e a implementação (backend-engineer). Nomes de
campos são propostas; o que é normativo é o **conteúdo** e as **regras**. Números de exemplo vêm de execução minha
(seção 3.9). Nada aqui exige dado novo: usa só `metais.json`, `propriedades_v14.json` e geometria.

### 3.0 Princípios

1. O modelo representa **uma fase única imposta** (a matriz com a estrutura do solvente). Ele não decide se a liga
   existe como solução sólida; isso é dito em toda resposta (3.7).
2. A unidade de amostragem é a **supercélula periódica**; o desenho é derivado dela, nunca o contrário.
3. Em solução desordenada a posição de cada elemento é **uma realização estatística** com semente, não a posição real.
4. Propriedades nominais (% em massa, parâmetro de rede, densidade) usam a **composição solicitada**; contagens e
   posições usam a **composição representada**; as duas são devolvidas lado a lado.

### 3.1 Supercélula periódica: átomos únicos × imagens de fronteira

- **Célula replicada:** a mesma de `supercelula.py` — convencional nas cúbicas (Z = 1, 2, 4), primitiva em HC (Z = 2).
- **Sítios de rede únicos:** f = (i + b₁, j + b₂, k + b₃), com i, j, k ∈ {0, …, n − 1} e b na ordem de
  `ESTRUTURAS[estrutura]["base"]`. Total N_rede = Z·n³ (16 para CCC n = 2). Todas as coordenadas ficam em [0, n).
- **Ordem canônica** (usada no sorteio e na saída): crescente em (i, j, k, índice de b); índice canônico
  s = ((i·n + j)·n + k)·Z + b.
- **Imagens de fronteira (só para o desenho):** para cada átomo único com coordenada fracionária nula (|f_m| < EPS)
  num conjunto S de eixos, gerar uma imagem para cada subconjunto não vazio T ⊆ S, somando n nas coordenadas de T.
  Conferência: CCC n = 2 → 1 átomo com 3 zeros (7 imagens) + 3 com 2 zeros (3 cada) + 3 com 1 zero (1 cada) = 19
  imagens; 16 + 19 = 35 esferas, igual ao desenho atual.
- **Regras invioláveis:** (a) a imagem tem **sempre** o elemento, o tipo, o sítio, a fase e o deslocamento do átomo de
  origem; (b) imagens **não entram** em nenhuma contagem, composição, massa ou sorteio; (c) cada imagem aponta para a
  origem (`imagem_de`) e é marcada (`imagem: true`).
- **Sítios intersticiais:** mesma regra — sítios únicos em [0, n) pela lista da seção 3.4, na ordem dada, com índice
  canônico ((i·n + j)·n + k)·N_s + s; um intersticial em sítio de fronteira ganha imagens como qualquer átomo.
- **Distorção ilustrativa** (se mantida): calculada sobre os átomos únicos com a convenção de imagem mínima e copiada
  para as imagens; devolver também a posição ideal. Continua `simulacao_ilustrativa`.

### 3.2 Realização estatística

**Quantidades (arredondamento).** Sejam x_i as frações atômicas solicitadas sobre **todos** os átomos (solvente +
substitucionais + intersticiais = 1) e x_I = Σ x_j dos intersticiais.
- Fração de sítios de rede do substitucional i: y_i = x_i / (1 − x_I). Alvo t_i = y_i·N_rede.
- Total de substitucionais S = ⌊Σ t_i + ½⌋; distribuir pelo **método do maior resto**: N_i = ⌊t_i⌋ e as S − Σ⌊t_i⌋
  unidades restantes vão para os maiores restos t_i − ⌊t_i⌋ (empate: ordem canônica dos solutos, 3.3).
  N_solvente = N_rede − S.
- Intersticial j: alvo t_j = N_rede·x_j / (1 − x_I); N_j = ⌊t_j + ½⌋.
- Usar ⌊t + ½⌋ explicitamente: o `round()` do Python arredonda ao par (`round(0.5) = 0`, `round(2.5) = 2` [FATO]).
- **Sem mínimo forçado.** Se x > 0 e N = 0, devolver N = 0 e o aviso "x abaixo da resolução desta supercélula
  (1 átomo = 100/N_total at%); aumente n". Se N_j exceder o número de sítios do tipo escolhido → erro de domínio
  (400), nunca truncar em silêncio.

**Sorteio (algoritmo `mt19937-chaves-v1`).**
1. `rng = random.Random(semente)`, semente inteira; **0 é semente válida** (corrige L-11).
2. Para cada sítio de rede, na ordem canônica, `u_s = rng.random()` (sempre N_rede sorteios, qualquer que seja a composição).
3. Ordenar os sítios por (u_s, s). Os primeiros N_1 recebem o 1º substitucional (ordem canônica), os N_2 seguintes o
   2º, etc.; os demais ficam com o solvente.
4. Depois, para cada tipo de sítio intersticial em uso (ordem: cúbico, octaédrico, tetraédrico), `u = rng.random()`
   por sítio único na ordem canônica; ordenar por (u, índice); os primeiros N_j recebem o 1º intersticial daquele
   tipo, etc.
5. No arranjo ordenado (3.6) o passo 3 é substituído pela regra do protótipo; os passos 2 e 4 continuam (o consumo
   de números aleatórios não depende do arranjo).

Propriedades: (i) mesma semente e mesmo n → mesma ordem de sítios; aumentar x **acrescenta** solutos aos já sorteados
(aninhamento: semente 1, N = 16 → 2 sítios {13, 9}; 4 sítios {13, 9, 8, 0} [FATO]); (ii) acrescentar um intersticial
não muda o arranjo substitucional.

**`random.Random` basta?** Sim, **desde que só `rng.random()` seja usado**. A documentação do módulo `random`
("Notes on Reproducibility") garante a mesma sequência de `random()` para a mesma semente entre versões do Python, e
diz que os demais algoritmos (`sample`, `shuffle`, `randrange`) podem mudar [NÃO VERIFICADO nesta sessão — citado de
memória; conferir na documentação oficial]. O código atual usa `rng.sample` (`ligas.py:237, 254`), que não tem essa
garantia. Não é gerador criptográfico e não precisa ser. Vetores de teste [FATO, Python 3.15.1]:
`random.Random(1).random()` = 0,13436424411240122; `random.Random(12345).random()` = 0,41661987254534116;
semente 1, N = 16, 2 menores chaves → índices canônicos {9, 13}; semente 0 → {3, 15}; semente 7, N = 54, k = 6 →
{6, 8, 10, 21, 33, 34}.

**Campos a devolver** (bloco novo; nomes sugeridos):

```text
composicao:
  unidade_entrada: "at" | "wt"
  solicitada:   [{elemento, papel, at_pct, wt_pct}]            # papel: solvente | substitucional | intersticial
  representada: [{elemento, papel, n_atomos, at_pct, wt_pct}]  # n_atomos = átomos ÚNICOS
  n_sitios_rede, n_intersticiais, n_atomos_unicos, n_desenhados
  resolucao_at_pct: 100 / n_atomos_unicos
  desvio_maximo_at_pct: máx |representada − solicitada|
realizacao:
  tipo: "estatistica" | "ordenada_prototipo" | "sem_soluto"
  semente, algoritmo: "mt19937-chaves-v1", n
  aviso: "Uma realização estatística entre muitas possíveis para esta composição e esta semente. Não é a posição
          real dos átomos na liga; outra semente dá outro arranjo igualmente válido."
```

Conversões [DERIVAÇÃO]: wt_i = x_i·A_i / Σ_k x_k·A_k; x_i = (w_i/A_i) / Σ_k (w_k/A_k), com a soma sobre **todos** os
elementos (intersticiais incluídos). A_i do seed; para intersticiais a massa está em `rascunho` (política de dados
decide: em produção, hoje, o pedido é recusado).

### 3.3 Multicomponente: solvente + lista de solutos

**Pedido (aditivo).** Além de `soluto`/`x` (legado), aceitar:

```text
solutos: [{elemento: str, x: número ≥ 0, modo?: "auto" | "substitucional" | "intersticial",
           sitio?: "auto" | "octaedrico" | "tetraedrico" | "cubico"}]     # 1 a 6 itens (limite a definir no contrato)
unidade?: "at" | "wt"            # padrão "at"; vale para todos os x
estrutura_matriz?: "CS" | "CCC" | "CFC" | "HC"   # padrão: estrutura do solvente no seed (ver 3.7)
```

Exatamente um entre `soluto` e `solutos`; `{soluto: S, x: X}` equivale a `solutos: [{elemento: S, x: X}]`.

**Validação (erro de domínio, sem correção silenciosa):**
1. Cada `elemento` resolvido pelo repositório (símbolo, nome ou alias, sem diferenciar caixa); após a resolução, os
   símbolos são distintos entre si e diferentes do solvente.
2. `modo = auto`: intersticial se o símbolo estiver em `intersticiais` do seed (C, H, N); senão substitucional.
   Substitucional exige metal cadastrado (raio, massa, estrutura). Pedir um metal como intersticial ou C/H/N como
   substitucional → erro "sem dados para este modo".
3. `sitio` só para intersticiais e só os tipos existentes na estrutura da matriz (3.4).
4. Números finitos, x_i ≥ 0. Em at%: Σ x_i < 100 (o solvente fica com 100 − Σ x_i > 0) e Σ dos intersticiais ≤ 20 at%
   (limite operacional já existente, `X_MAXIMO_INTERSTICIAL`; não é limite físico). Em wt%: mesma regra após converter.
   O caso legado `x = 100` com `soluto` continua aceito para não quebrar o contrato, com aviso (L-13).
5. Se o solvente não for o componente majoritário em átomos: aceitar com aviso "a estrutura do solvente foi imposta".
6. Capacidade: N_j ≤ sítios únicos do tipo (3.2).

**Ordem determinística.** Ordem canônica dos solutos = substitucionais em ordem crescente de símbolo (comparação de
código Unicode), depois intersticiais na mesma regra. O resultado **não depende da ordem do pedido**. Saída sempre:
solvente, substitucionais, intersticiais.

**O que é sustentável com mais de um soluto:**

| Grandeza | Regra | Natureza | Observações obrigatórias |
|---|---|---|---|
| % em massa ↔ % atômica | 3.2 | exata (dados: massas do seed) | — |
| Parâmetro de rede `a_nm` | R̄ = y_solv·R_solv + Σ y_i·R_i (só sítios de rede); a = a_base·R̄/R_solv, com a_base = `a` medido do solvente quando `tem_rede_medida`, senão k·R_solv | `estimativa_modelo` | interpolação linear de raios tabelados (extensão da regra de Vegard a vários solutos), sem termos de interação; raios tabelados para a estrutura de cada elemento puro; intersticiais **não** dilatam a rede neste modelo; em HC o c/a do solvente é mantido |
| Densidade | ρ = Z_cel·[y_solv·A_solv + Σ y_i·A_i + Σ_j x_j/(1 − x_I)·A_j] / (V_cel·N_A), V_cel com o `a_nm` acima | `estimativa_modelo` | com intersticial: hipótese "rede não dilatada" declarada em `hipoteses` e aviso de que o valor tende a superestimar a densidade; sem lacunas |
| Regras de Hume-Rothery | uma avaliação **por par solvente–soluto substitucional** | critério empírico | não avalia interação soluto–soluto nem o sistema multicomponente |
| Hägg e raio livre do sítio | por par solvente–intersticial, com o sítio efetivamente usado | geométrico | raio livre calculado pela geometria (3.4), inclusive com c/a real |
| Conclusão global de solubilidade (>1 soluto) | — | **`null`** | motivo: "as regras são binárias; o motor não prevê solubilidade em sistema multicomponente" |
| Limite de solubilidade, fases presentes, frações de fase | — | **`null`** | motivo em 3.7 |
| Parâmetro de rede/densidade "medidos" da liga | — | **`null`** | não há dado experimental de liga no repositório |

Para a_base: com solvente sem rede medida a fórmula coincide com a atual (a = k·R̄). Com Ti passa de 0,2890 para
0,2951 nm em x = 0 (corrige L-7) — **é mudança de resultado numérico e precisa de aprovação**.

**Campos:** `regras_por_soluto: [{soluto, modo, regras: [...], conclusao}]`; os campos legados `regras` e `conclusao`
continuam e, com um único soluto, têm o mesmo conteúdo. **Redação** (a validar pelo materials-science): trocar
"solubilidade intersticial alta" e "solubilidade sólida extensa, possivelmente completa" por formulações de critério,
p. ex. "critérios geométricos favoráveis à solução intersticial; não é previsão de solubilidade" e "as quatro regras
são atendidas: par favorável à solução substitucional; o limite depende do diagrama de fases".

### 3.4 Sítios intersticiais por estrutura

Verificação [FATO]: para cada lista abaixo gerei a rede ideal, contei os vizinhos do sítio e calculei
r_livre/R = (d_sítio–átomo − R)/R com R = d₁/2; a multiplicidade foi conferida pela órbita do sítio sob as operações
de simetria que o próprio motor exporta para o CIF. As letras de Wyckoff são das International Tables for
Crystallography, vol. A, **citadas de memória — a conferir pelo auditor**; as multiplicidades (números) são [FATO].

| Estrutura | Sítio | Posições fracionárias na célula replicada (referencial do motor) | Sítios por célula (por átomo) | Vizinhos (distância em a) | r_livre/R | Wyckoff |
|---|---|---|---|---|---|---|
| CS | cúbico | (½, ½, ½) | 1 (1) | 8 a 0,86603 | √3 − 1 = 0,73205 | 1b de Pm-3m |
| CCC | octaédrico | (½,½,0), (½,0,½), (0,½,½), (½,0,0), (0,½,0), (0,0,½) | 6 (3) | **2 a 0,50000 + 4 a 0,70711** (irregular) | 2/√3 − 1 = 0,15470 (eixo curto); 0,63299 no plano | 6b de Im-3m |
| CCC | tetraédrico | (½,¼,0), (½,¾,0), (¼,½,0), (¾,½,0), (½,0,¼), (½,0,¾), (¼,0,½), (¾,0,½), (0,½,¼), (0,½,¾), (0,¼,½), (0,¾,½) | 12 (6) | 4 a 0,55902 | √(5/3) − 1 = 0,29099 | 12d de Im-3m |
| CFC | octaédrico | (½,½,½), (½,0,0), (0,½,0), (0,0,½) | 4 (1) | 6 a 0,50000 | √2 − 1 = 0,41421 | 4b de Fm-3m |
| CFC | tetraédrico | (¼ ou ¾, ¼ ou ¾, ¼ ou ¾) — 8 combinações | 8 (2) | 4 a 0,43301 | √(3/2) − 1 = 0,22474 | 8c de Fm-3m |
| HC (ideal) | octaédrico | (⅓, ⅔, ¼), (⅓, ⅔, ¾) | 2 por primitiva = 6 por prisma (1) | 6 a 0,70711 | √2 − 1 = 0,41421 | 2a de P6₃/mmc (origem padrão: (0,0,0), (0,0,½)) |
| HC (ideal) | tetraédrico | (0, 0, ⅜), (0, 0, ⅝), (⅔, ⅓, ⅛), (⅔, ⅓, ⅞) | 4 por primitiva = 12 por prisma (2) | 4 a 0,61237 | √(3/2) − 1 = 0,22474 | 4f de P6₃/mmc, z = ⅝ na origem padrão |

**Derivações** [DERIVAÇÃO] (R do solvente pelo contato de cada estrutura):
- CS cúbico: centro do cubo, distância √3·a/2 aos 8 vértices; a = 2R ⇒ r = (√3 − 1)R.
- CCC octaédrico (½,½,0): átomos de centro em (½,½,±½) a a/2 e 4 vértices a a/√2; a = 4R/√3 ⇒
  r = a/2 − R = (2/√3 − 1)R. O octaedro é achatado ao longo de um eixo ⟨100⟩.
- CCC tetraédrico (½,¼,0): vizinhos (0,0,0), (1,0,0), (½,½,±½), todos a √(¼ + 1/16)·a = (√5/4)a ⇒ r = (√5/√3 − 1)R.
- CFC octaédrico (½,½,½): 6 centros de face a a/2; a = 2√2R ⇒ r = (√2 − 1)R.
- CFC tetraédrico (¼,¼,¼): vértice e 3 centros de face a (√3/4)a ⇒ r = (√6/2 − 1)R = (√(3/2) − 1)R.
- HC: mesmos poliedros do empacotamento compacto (1 octaédrico e 2 tetraédricos por átomo); o tetraedro com ápice
  no átomo (0,0,0) e base nos três átomos da camada z = ½ tem o centro a ¾ da altura c/2 a partir do ápice,
  z = 3/8; os demais seguem por simetria. Octaédrico: entre duas camadas, sobre a posição não ocupada (⅓, ⅔).

**HC com c/a real:** as posições fracionárias acima são mantidas (rótulo "posição idealizada") e o raio livre é
calculado pela geometria: d_oct = a·√(⅓ + (c/a)²/16); para o tetraédrico, o menor entre 3c/8 e a·√(⅓ + (c/a)²/64);
r_livre = d − R. Valores [FATO], R = a/2: Mg oct. 0,4116 R, tet. 0,2180 R; Ti 0,4011 e 0,1904; Co 0,4113 e 0,2172;
Zn 0,4814 e 0,2444. Fora do ideal o sítio tetraédrico deixa de ser equidistante (1 + 3 vizinhos).

**Restrições de ocupação:** no máximo um átomo por sítio. Distâncias mínimas entre sítios do mesmo tipo [FATO]:
CCC oct. 0,5 a; CCC tet. 0,35355 a; CFC oct. 0,70711 a; CFC tet. 0,5 a; HC oct. 0,81650 a; HC tet. 0,40825 a (pares
que compartilham face). O modelo **não** aplica exclusão entre sítios vizinhos nem entre tipos diferentes; isso entra
em `hipoteses` ("ocupação aleatória sem interação soluto–soluto").

**Sítio padrão (`sitio = auto`)** — decisão conservadora: **octaédrico para C, N e H em CCC, CFC e HC; cúbico em CS**,
isto é, o comportamento atual; o tetraédrico fica disponível por escolha explícita. Justificativas e seu estado:
- C e N em CFC (ex.: γ-Fe): o octaédrico é o maior sítio (0,414 R × 0,225 R) [FATO geométrico]; é também o sítio
  descrito na literatura de aços [NÃO VERIFICADO — fonte a verificar pelo auditor].
- C e N em CCC (ex.: α-Fe): o octaédrico é o **menor** sítio (0,155 R × 0,291 R) [FATO]. A literatura de aços atribui
  o C ao sítio octaédrico porque ali ele desloca principalmente os 2 vizinhos do eixo curto (origem da
  tetragonalidade da martensita) [NÃO VERIFICADO — fonte a verificar pelo auditor]. A resposta deve dizer isto
  textualmente e **não** dizer "maior sítio".
- H: o sítio preferido depende do metal (tetraédrico em vários metais CCC e HC, octaédrico em vários CFC, segundo meu
  conhecimento geral) [NÃO VERIFICADO — não adotar como padrão antes do parecer do auditor/materials-science]. Até
  lá: padrão octaédrico com `sitio.padrao_verificado = false` e aviso.
- Devolver em `sitio`: `nome`, `tipo`, `nc` (CCC octaédrico: "2 + 4"), `fator` e `raio_nm` calculados pela geometria,
  `sitios_por_celula`, `wyckoff`, `escolha: "padrao" | "informado"`, `justificativa`, `padrao_verificado`.
  Com mais de um intersticial: `sitios: [...]`; o campo legado `sitio` continua com o primeiro.

### 3.5 Campos por átomo

`AtomoLiga` mantém `pos`, `frac`, `tipo`, `elemento`, `raio_rel` e ganha (todos aditivos):

| Campo | Conteúdo | Regra |
|---|---|---|
| `id` | identificador estável | depende só de estrutura, n e sítio, nunca da semente nem da composição. Sugestão: rede `r:{i}.{j}.{k}:{b}`; intersticial `i:{oct|tet|cub}:{i}.{j}.{k}:{s}`; imagem = id da origem + `+{tx}{ty}{tz}` (ex.: `r:0.0.0:0+110`) |
| `imagem` | bool | `true` para imagem periódica de fronteira (não contada) |
| `imagem_de` | id ou `null` | id do átomo único de origem |
| `pos` (existente) | cartesiana em unidades de `a` da liga | referencial da seção 0.1 |
| `pos_nm` | cartesiana em nm | `pos × a_nm`; herda a natureza de `a_nm` (estimativa) |
| `frac` (existente) | fracionária na base da célula replicada, de 0 a n | inalterado |
| `celula`, `frac_celula` | (i, j, k) e fracionária em [0, 1) dentro da célula | `frac = celula + frac_celula`; em HC a origem é a do motor, deslocada de (⅓, ⅔, ¼) em relação ao CIF (informar em `convencoes`) |
| `ocupacao` | `"solvente"` \| `"substitucional"` \| `"intersticial"` | `tipo` legado continua `rede`/`intersticial` |
| `sitio` | `{nome, wyckoff, nc}` | rede desordenada: sítio da estrutura-mãe (1a, 2a, 4a, 2c); intersticial: tabela 3.4; protótipo ordenado: ver 3.6; `wyckoff: null` quando não houver valor verificado |
| `fase` | id da fase em `fases` (3.7) | hoje sempre `"matriz"` |
| `pos_ideal` | posição de rede antes da distorção | só quando `distorcer = true` |

**Propriedade de elemento puro não é propriedade do átomo na liga.** Raio tabelado, massa molar, estrutura do
elemento puro e eletronegatividade ficam num bloco separado, no nível da resposta —
`elementos: [{simbolo, papel, raio_nm, massa_g_mol, estrutura_elemento_puro, estado_do_dado, fonte}]`, com o rótulo
"propriedade tabelada do elemento puro". O inspetor mostra esse bloco sob esse título e não o repete como atributo
calculado do átomo. `raio_rel` é **raio de desenho** (raio tabelado/a), e assim deve ser rotulado: o motor não calcula
raio de átomo em solução. Carga, volume atômico local, energia ou "raio efetivo na liga" por átomo: **não devolver**
(não há modelo).

### 3.6 Ordenada × desordenada; idealizado × experimental

Campos de natureza no nível da resposta:

```text
modelo:
  tipo_solucao: "substitucional" | "intersticial" | "mista"
  ordenacao: "desordenada" | "ordenada_prototipo"
  fases: "monofasica_imposta"
  geometria: "idealizada"              # posições ideais de rede; sem relaxação (a distorção é ilustrativa)
  parametro_rede: "estimativa_vegard_sobre_raios"   # e, para o solvente: "derivado_de_R" | "medido"
  c_a: "ideal" | "tabelado" | "derivado_de_a_c_medidos" | null
  hipoteses: [lista de frases curtas]   # ex.: "todos os sítios de rede ocupados (sem lacunas)",
                                        # "intersticiais não dilatam a rede", "ocupação aleatória sem interação
                                        # soluto–soluto", "c/a do solvente mantido", "fase única imposta"
prototipo: null | {strukturbericht, prototipo, composicao_ideal_at_pct, rede_ordenada, observacao}
```

Regras do arranjo ordenado:
1. Só com **um** soluto substitucional e sem alterar as regras geométricas atuais (validadas, OK-3). Com mais de um
   substitucional: sem protótipo, cai em desordenado com nota.
2. A ordenação é sempre `ordenada_prototipo` + aviso de hipotético (já existente). O motor não sabe se o par ordena.
3. `composicao.representada` traz a estequiometria exata do protótipo (25, 50 ou 75 at%); se diferir da solicitada
   (tolerância atual de ±2 at%), aviso explícito: "o desenho tem a estequiometria ideal do protótipo; % em massa,
   parâmetro de rede e densidade foram calculados para a composição solicitada".
4. `estrutura` continua sendo a da rede-mãe (compatibilidade); `prototipo.rede_ordenada` informa que a fase ordenada
   tem outra rede/grupo espacial: L1₂ (protótipo Cu₃Au) e B2 (protótipo CsCl) são cúbicas primitivas, Pm-3m; L1₀
   (protótipo CuAu) é tetragonal, e o motor a desenha com c/a = 1 (`observacao`). Grupos espaciais e Wyckoff das
   fases ordenadas: [NÃO VERIFICADO — conferir com o auditor antes de exibir]; até lá `sitio.wyckoff = null` nesses átomos
   e `sitio.nome` descritivo ("vértice", "centro de face", "centro do cubo", "camada z inteiro/semi-inteiro").
5. "Experimental" só pode aparecer onde há dado medido no repositório: hoje, apenas `a`/`c` do Ti e as densidades
   experimentais dos elementos puros. Não existe dado experimental de liga: nenhum campo de liga recebe esse rótulo.

### 3.7 Limite de solubilidade e sistemas multifásicos

**O que os dados sustentam** [FATO]: nada. Não há diagrama de fases, limite de solubilidade, fase secundária,
composição ou fração de fase nos seeds. A única informação de fase é a tabela `transicoes_alotropicas` (Co, Fe, Ti),
em estado `rascunho` e sem fonte.

**Comportamento honesto exigido (sempre presente na resposta):**

```text
fases: [{id: "matriz", nome: "solução sólida na estrutura do solvente", estrutura, origem: "imposta_pelo_modelo",
         composicao: <igual a composicao.representada>, fracao: null,
         fracao_motivo: "o motor não calcula equilíbrio de fases"}]
verificacoes:
  limite_solubilidade: {verificado: false, valor: null,
     motivo: "não há dados de diagrama de fases no repositório"}
  fases_secundarias:   {previstas: null,
     motivo: "o motor não prevê fases; a liga real pode ser multifásica nesta composição"}
avisos: [...]   # texto abaixo
```

Avisos obrigatórios (redação a validar pelo pedagogical-engineer e pelo materials-science):
- Sempre: "Modelo de fase única: todos os solutos foram colocados na matriz. O motor não verifica o limite de
  solubilidade nem prevê fases secundárias. A liga real, nesta composição e temperatura, pode ter mais de uma fase."
- Com intersticial: "Nem todo o {elemento} de uma liga real está dissolvido na matriz: acima do limite de
  solubilidade ele forma outras fases (por exemplo, carbonetos ou nitretos), que não são representadas aqui."
- Com `estrutura_matriz` diferente da estrutura do seed: o mesmo aviso de `celula.py:159-163` (raio tabelado depende
  da coordenação; resultado hipotético), mais o nome da forma alotrópica e a faixa de temperatura **somente** se a
  tabela de alotropia tiver a entrada e a política de dados permitir (hoje: `rascunho`).

**Proibido:** recusar ou "corrigir" a composição com um limite que o repositório não tem; exibir fração de fase;
desenhar carboneto ou qualquer segunda fase; distribuir a composição global entre fases.

**O que seria necessário para ir além** (pendência; exige esquema de dados e fonte — fora desta rodada):
- por sistema: `{sistema, fase, estrutura (protótipo, grupo espacial, parâmetros de rede), faixa de composição,
  temperatura, limite de solubilidade, fonte, estado}`;
- por resultado multifásico: lista de fases, cada uma com **estrutura, composição própria e fração** (molar ou em
  massa, indicando qual) e a **origem do dado** (diagrama avaliado, CALPHAD com a base usada, ou "informado pelo
  usuário");
- representação: **uma célula/supercélula por fase**, lado a lado, com a fração como rótulo; a composição global nunca
  é forçada numa célula única. A relação de orientação e a morfologia entre fases não são representadas.
- Alternativa de menor custo, que não inventa dado: aceitar fases **informadas pelo usuário** (estrutura, composição,
  fração), rotuladas `origem: "informado_pelo_usuario"`. Sugiro para rodada futura; depende do parecer R1-MAT-01.

### 3.8 Compatibilidade

- **Pedido:** `soluto`, `x`, `n`, `arranjo`, `distorcer`, `semente` continuam válidos. Novos e opcionais: `solutos`,
  `unidade`, `estrutura_matriz`. `extra="forbid"` permanece.
- **Resposta:** todos os campos atuais de `SolidSolutionResponse` e `AtomoLiga` continuam, com o mesmo tipo. Com mais
  de um soluto, os campos escalares legados (`soluto`, `intersticial`, `x_pct`, `pct_peso`, `sitio`) referem-se ao
  **primeiro soluto da ordem canônica**, e os dados completos vêm em `composicao`, `regras_por_soluto` e `sitios`.
- **Mudanças de valor em campos existentes (correções; precisam constar do contrato e do histórico):**
  1. `n_soluto` e `n_solvente` passam a contar **átomos únicos** (antes: esferas). Ex.: Fe–Cr 12 %, n = 2: 4/31 → 2/14.
     Com vários solutos, `n_soluto` = soma dos solutos. `composicao.n_desenhados` guarda o número de esferas.
  2. Elementos das esferas mudam para toda semente (novo algoritmo de sorteio).
  3. Quantidade de intersticiais: sem mínimo de 1 e calculada sobre N_rede.
  4. `semente: 0` é respeitada.
  5. Solvente com rede medida: `a_base_nm`, `a_nm`, `densidade`, `densidade_base` (hoje só Ti).
  6. `conclusao` e `regras[].detalhe`: nova redação.
- **Testes existentes que fixam o comportamento a corrigir** (o backend-engineer atualiza junto com a correção):
  `test_ligas.py::test_aleatorio_e_reprodutivel_pela_semente` (`n_soluto == round(0.30 * len(atomos))`) e
  `::test_ordenacao_l12_coloca_soluto_nos_vertices` (`n_soluto == (n + 1) ** 3`; passa a `n ** 3`).
  `::test_ordenacao_b2_na_ccc_e_so_geometrica` (`n ** 3`) continua válido.
- **Versão:** incrementar `VERSAO_MOTOR` e registrar o algoritmo em `realizacao.algoritmo`.

### 3.9 Casos de referência para os testes de regressão

Números de execução minha (massas do seed: Fe 55,85; Cr 52,00; C 12,011; raios Fe 0,1241, Cr 0,1249 nm). Tolerâncias:
contagens e conjuntos de índices **exatos**; composições e conversões `abs = 1e-4` (pontos percentuais);
geometria e fatores `rel = 1e-9`; FEA e densidade `abs = 1e-4`.

| # | Caso | Esperado |
|---|---|---|
| R1 | Fe–Cr 12 at%, n = 2, qualquer semente | N_rede = 16; Cr = ⌊1,92 + ½⌋ = 2; Fe = 14; representada 12,5000 at% Cr = 11,7395 wt%; solicitada 11,2660 wt%; 35 esferas = 16 únicos + 19 imagens; toda imagem com o elemento da origem |
| R2 | idem, semente 1, algoritmo `mt19937-chaves-v1` | Cr nos índices canônicos {9, 13} = sítios (1,5; 0,5; 0,5) e (1,5; 1,5; 0,5); com 25 % (4 átomos): {0, 8, 9, 13} ⊃ anterior |
| R3 | Fe–Cr 12 at%, n = 3 | 54 únicos; Cr = 6 (alvo 6,48); 11,1111 at% = 10,4250 wt% |
| R4 | Fe–C 4 at%, n = 2 / 3 / 4 | Fe 16 / 54 / 128; C = 1 / 2 / 5 (alvos 0,6667; 2,25; 5,3333); representada 5,8824 / 3,5714 / 3,7594 at% = 1,3263 / 0,7902 / 0,8331 wt%; solicitada 0,8881 wt% |
| R5 | Fe–C 0,5 at%, n = 2 | C = 0 (alvo 0,080), com aviso de resolução — não 1 |
| R6 | Fe + Cr 12 + C 2 (at%), n = 3 | alvos Cr 6,6122 → 7, C 1,1020 → 1; Fe 47, Cr 7, C 1 (55 únicos); representada Fe 85,4545 / Cr 12,7273 / C 1,8182 at% = 87,4703 / 12,1294 / 0,4002 wt%; solicitada 88,1121 / 11,4472 / 0,4407 wt%; R̄ = 0,124198 nm, a = 0,286823 nm; ρ = 7,8288 g/cm³ com C e rede não dilatada (7,7943 só com os átomos de rede) |
| R7 | entrada em massa: Fe–12Cr–0,4C (wt%) | 85,5900 / 12,5927 / 1,8173 at% |
| R8 | maior resto: Fe + 10 Cr + 10 Ni + 5 Mo (at%), n = 2 | alvos 1,6 / 1,6 / 0,8; S = 4; Cr 2, Ni 1, Mo 1 (Mo pelo maior resto; empate Cr × Ni pela ordem de símbolo); Fe 12 |
| R9 | ordem do pedido | `solutos` [Cr, C] e [C, Cr] → respostas idênticas |
| R10 | Cu–Au 25 / 50 / 75 %, ordenado, n = 2 | Au em 8 / 16 / 24 de 32 únicos; nenhuma imagem inconsistente; `n_soluto` = 8 / 16 / 24 |
| R11 | Fe–Cr 48,5 %, ordenado | B2 com 8 de 16; representada 50 at%; aviso de diferença para a solicitada |
| R12 | sítios (rede ideal) | tabela 3.4: número de sítios únicos por célula 1; 6 e 12; 4 e 8; 2 e 4; NC e distâncias; r_livre/R 0,73205; 0,15470 e 0,29099; 0,41421 e 0,22474; 0,41421 e 0,22474 |
| R13 | periodicidade de intersticiais | para 200 sementes, CCC e CFC, x = 8 at%, n = 2 e 3: nenhum sítio único ocupado mais de uma vez; todo intersticial de fronteira com todas as suas imagens |
| R14 | Ti como solvente, x = 0 | `a_base_nm = a_nm = 0,2951`; densidade = 4,5005 (igual ao módulo de célula) |
| R15 | semente 0 | `realizacao.semente = 0`; índices (N = 16, k = 2) {3, 15} |
| R16 | HC, FEA de esferas rígidas (se a correção de E-1 for aprovada) | Mg 0,736418; Ti 0,720132; Co 0,735968; Zn 0,651508; ideal 0,740480; para todo c/a ∈ [1,0; 2,5]: FEA ≤ π/(3√2) |
| R17 | `solutos` com elemento repetido, igual ao solvente, soma ≥ 100, intersticiais > 20 at%, metal como intersticial, sítio inexistente na estrutura | erro de domínio com mensagem específica |

Os testes de referência do que **já está correto** estão em `backend/tests/unit/engines/test_validacao_estruturas.py`.

## 4. Consultas para o Supervisor encaminhar

**Ao academic-research-auditor (fontes; nada disto foi verificado por mim na fonte):**
1. c/a (ou a e c) de Mg, Ti, Zn, Co e a estrutura CS do Po com o raio usado; raios, massas e densidades dos 15 metais.
2. Raio e massa de C, N, H em `propriedades_v14.json` (hoje `rascunho`, `fonte: null`); a noção de "raio" de um
   intersticial precisa de definição (covalente? de qual tabela?).
3. Sítio de C e N em α-Fe (octaédrico, apesar de o tetraédrico ser maior) e em γ-Fe (octaédrico); sítio preferido do H
   por estrutura/metal.
4. Letras de Wyckoff da tabela 3.4 (ITA vol. A) e protótipos/grupos espaciais de L1₂, L1₀ (tetragonalidade) e B2.
5. Enunciado original da lei de Vegard (1921) × uso com raios; limites ±15 % (Hume-Rothery), ±0,4 (Darken–Gurry),
   0,59 (Hägg).
6. Limite de empacotamento π/(3√2) (Kepler/Hales) e as relações de livro (a(R), FEA) com edição e página.
7. Nota de reprodutibilidade do módulo `random` do Python.
8. Tabela de alotropia de Fe, Co, Ti (temperaturas), hoje sem fonte.

**Ao materials-science-specialist (parecer):**
1. Aprovar a correção do FEA em HC com c/a < ideal (1.4): substituir o valor ou acrescentar `fea_esferas_rigidas`.
2. Densidade com intersticial sem dilatação da rede: manter o número com hipótese declarada (minha recomendação,
   porque `densidade` é campo obrigatório hoje) ou torná-lo `null`.
3. Uso de `a` medido do solvente como base da interpolação (L-7) e validade da interpolação linear de raios com
   vários solutos e com soluto de outra estrutura (L-8).
4. Redação das conclusões de Hume-Rothery/Hägg como critério, não como previsão (3.3).
5. `estrutura_matriz` (ex.: Fe CFC para austenita) com o raio tabelado da forma CCC: aceitável como hipótese rotulada?
6. Sítio padrão do H; necessidade de exclusão entre sítios intersticiais vizinhos.
7. Dados mínimos e fonte para limite de solubilidade e fases (3.7), em conjunto com R1-MAT-01.

**Ao api-architect:** nomes e formato dos campos novos (3.2, 3.3, 3.5–3.7); semântica corrigida de `n_soluto`/
`n_solvente`; `semente = 0`; código de erro para capacidade de sítios; limite de itens em `solutos`; formato de `id`.

**Ao backend-engineer (R1-BE-02):** implementar 3.1–3.8; atualizar os dois testes citados em 3.8; escrever os testes
R1–R17; não usar `rng.sample`/`round()` no sorteio e no arredondamento.

**Ao frontend-engineer:** não contar imagens em legendas e totais; inspetor com os campos de 3.5 e o bloco "elemento
puro" separado; legenda para mais de dois elementos (`alloyLegend` hoje assume solvente + 1 soluto,
`alloyScene.ts:41-46`); em HC, dizer qual célula está na tela (prisma de 6 átomos no metal puro; paralelepípedo
primitivo de 2 átomos na liga e em `/supercells`) e que as fracionárias seguem a origem do motor.

**Ao supervisor (decisão):** (a) autorizar ou não a mudança de fórmula do FEA em HC; (b) autorizar as mudanças de valor
listadas em 3.8; (c) `geometry.ts` gera no front as translações da supercélula do metal puro e um empilhamento de
planos compactos (linhas 10–13, 32 e 153–161) — os valores que li estão geometricamente corretos, mas é geometria
calculada fora do motor; avaliar frente ao princípio "o front não recalcula" (não auditei o arquivo inteiro).

## 5. Limitações e o que não foi verificado

- **Fontes bibliográficas:** nenhuma foi aberta nesta tarefa. Toda referência de literatura está marcada
  [NÃO VERIFICADO]; não cito edição, página nem DOI. As referências de conferência são derivações analíticas e
  contagens numéricas minhas.
- **Dados do seed** (raios, massas, c/a, densidades, intersticiais, alotropia): usados como estão; não validados.
  A concordância de densidade (−0,59 % a +0,68 %) mostra consistência interna entre raio, massa e densidade do seed,
  não exatidão dos dados.
- **Letras de Wyckoff, grupos espaciais das fases ordenadas e sítios preferidos de C, N e H:** de memória; só as
  multiplicidades e a geometria foram conferidas por execução.
- **Operações de simetria do CIF:** conferi o tamanho das órbitas (geral e do sítio), não cada operação contra as
  International Tables. O teste com `gemmi` do repositório está pulado (biblioteca ausente).
- **Garantia de reprodutibilidade de `random()` entre versões do Python:** citada de memória; os vetores de teste foram
  produzidos só em Python 3.15.1.
- **Frontend:** li `alloyScene.ts` (70 linhas) e trechos de `geometry.ts` por busca; não executei o viewer nem testes
  de frontend. A afirmação sobre `geometry.ts` na seção 4 é parcial.
- **Não examinei:** `miller.py`, `planar.py`, `exportacao.py` (além de `operacoes_simetria`), `passos.py` (além das
  três linhas citadas), `termico.py` e o uso de ligas pelo módulo térmico (`ThermalRequest.liga`), que herdará as
  mudanças desta especificação.
- **Modelo físico:** a especificação continua sendo de esferas rígidas em rede ideal, fase única, sem relaxação, sem
  ordem de curto alcance, sem lacunas e sem energia. Ela torna a representação internamente consistente e honesta;
  não a torna preditiva.
- **Varreduras estatísticas:** 200 sementes por caso; suficientes para mostrar que os defeitos são sistemáticos
  (197–200 de 200), não para estimar frequências finas.

## 6. Relatório no formato da equipe

```text
TÍTULO DA TAREFA: R1-CRI-01 — Validação das 4 estruturas, auditoria de ligas e especificação G1
Agente responsável: crystallography-engineer (Agente 09)
Status: concluído (com consultas pendentes de terceiros — seção 4)
Objetivo: validar CS/CCC/CFC/HC com evidência numérica; auditar a representação de ligas reproduzindo as falhas;
  especificar (G1) as correções e a ampliação para ligas multicomponentes.
Escopo analisado: backend/app/engines/crystallography (estruturas, geometria, supercelula, celula, ligas,
  constantes), schemas de solução sólida, seeds de cristalografia, testes de ligas; leitura parcial do viewer.
Arquivos consultados: os da seção 0; docs/agent_reports/2026-11-12_rodada_R1_plano_e_linha_de_base.md;
  frontend/src/features/viewer3d/alloyScene.ts e geometry.ts (parcial).
Método utilizado: execução do motor e da API por scripts de leitura; conferência independente por redução
  periódica, contagem de vizinhos, determinante e derivação analítica.
Constatações: CS, CCC, CFC e HC ideal validados; HC com c/a real validado com ressalvas (E-1 confirmado: FEA acima
  de 0,7405 por sobreposição de esferas). Ligas: L-1 a L-4 confirmados; 9 achados novos (L-5 a L-13); conversão
  at%→wt%, fatores e posições dos sítios implementados e geometria dos protótipos validados.
Evidências: seções 1 e 2; saídas saida_estruturas.txt e saida_ligas.txt no scratchpad.
Problemas encontrados: seção 2.1 (2 críticos, 3 altos, 4 médios, 4 baixos) e seção 1.5.
Riscos e impactos: composição e contagem exibidas hoje para ligas não correspondem a nenhuma célula periódica;
  FEA fisicamente impossível para Mg, Ti e Co; todo soluto desenhado como dissolvido, sem aviso.
Dependências: parecer do materials-science e auditoria bibliográfica (seção 4); contrato do api-architect.
Recomendações: seção 3 (especificação) e 1.4 (FEA).
Ações executadas: criação deste parecer e de backend/tests/unit/engines/test_validacao_estruturas.py; scripts
  temporários no scratchpad. Nenhum código de produção alterado; nenhum commit.
Arquivos alterados: docs/agent_reports/2026-11-12_parecer_cristalografia.md (novo);
  backend/tests/unit/engines/test_validacao_estruturas.py (novo).
Testes realizados: pytest tests/unit/engines/test_validacao_estruturas.py; pytest tests/unit/engines; ruff no
  arquivo novo.
Resultado dos testes: 64 passed in 6.48s; 204 passed, 1 skipped in 10.91s (skip: gemmi ausente,
  test_exportacao.py:126); ruff "All checks passed!".
Limitações e incertezas: seção 5.
Pendências para o supervisor: seção 4 (decisões a, b, c e encaminhamentos).
```

### 6.1 Saída dos testes (colada)

```text
$ cd backend && ../.venv/Scripts/python -m pytest tests/unit/engines/test_validacao_estruturas.py
................................................................         [100%]
64 passed in 6.48s

$ ../.venv/Scripts/python -m pytest tests/unit/engines
.............................................................            [100%]
204 passed, 1 skipped in 10.91s
SKIPPED [1] tests\unit\engines\test_exportacao.py:126: could not import 'gemmi': No module named 'gemmi'

$ ../.venv/Scripts/python -m ruff check tests/unit/engines/test_validacao_estruturas.py
All checks passed!
```

Na primeira execução do arquivo novo, 7 testes de HC falharam por um erro **do meu auxiliar de teste** (eu calculava
distâncias a partir da coordenada 2/3 arredondada a 6 casas, erro de 3 × 10⁻⁷); corrigi o auxiliar para usar a
coordenada original do motor. Não foi falha do motor.
