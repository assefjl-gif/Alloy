# Motor científico (cristalografia e temperatura; HEA em [MOTOR_HEA.md](MOTOR_HEA.md))

Núcleo único de cálculo do Alloy Virtual Lab (ADR-004). Código em `backend/app/engines/`.
Versão do motor de cristalografia: **2.1.0** (rodada R1 — correções aprovadas no portão G1;
ver `docs/architecture/2026-11-12_decisoes_G1_R1.md`, `docs/architecture/2026-11-12_contrato_R1.md` e
`docs/agent_reports/2026-11-12_parecer_cristalografia.md`).

## 1. Princípios verificados por teste

| Princípio | Como é garantido | Teste |
|---|---|---|
| Motores puros, sem I/O | Análise estática de imports (`ast`): proíbe `app.api`, `app.repositories`, `app.models`, FastAPI, SQLAlchemy, `open`, `pathlib`, `os` etc. Verificado com violação injetada | `tests/unit/test_arquitetura.py` |
| Uma única constante de Avogadro (CODATA 2018) | Só uma definição de `N_AVOGADRO` em `app/` | idem |
| Resultado igual ao B | Saídas congeladas de A, B e D; motor = B com tolerância 1e-12 | `tests/scientific/test_regressao_versoes.py` |
| Toda divergência explicada | A/D × motor: só N_A (CIE-02), Ti com rede medida (ADR-005) e arredondamento prematuro da HC em A/D (CR-08, ~5e-7) | idem |
| Banco não altera dado | Motor com repositório SQL = motor com JSON, campo a campo | `tests/integration/test_persistencia.py` |

## 2. Módulos

| Módulo | Conteúdo | Origem | Classe do resultado |
|---|---|---|---|
| `crystallography/celula.py` | Célula, rede medida/derivada/**informada** (*a* → R), FEA, densidade | B + v1.4 | analítico |
| `crystallography/passos.py` | Passo a passo de *a* e do FEA (fecha D-12) | v1.4 | analítico |
| `crystallography/miller.py` | (hkl)/(hkil), direções, **famílias de planos em supercélula** | B + v1.4 | analítico |
| `crystallography/planar.py` | Densidade e fração planar **só para famílias validadas** | v1.4 | analítico |
| `crystallography/supercelula.py` | Blocos n×n×n (n ≤ 4), HC em célula primitiva (fecha D-10); **átomos únicos × imagens de fronteira** (R1) | v1.4 + R1 | analítico |
| `crystallography/sitios.py` | **Sítios intersticiais octaédricos, tetraédricos e cúbico: posições, multiplicidade, NC e raio livre pela geometria (c/a real no HC)** | R1 | analítico |
| `crystallography/ligas_entrada.py` | **Validação do pedido de liga: solutos, modo, sítio, base de composição, erros com subtipo** | R1 | — |
| `crystallography/ligas.py` | Vegard sobre raios, % at ↔ % massa, Hume-Rothery, intersticiais, protótipos ordenados, distorção; **multicomponente (até 6 solutos) e realização estatística sobre a supercélula periódica** | v1.4 + R1 | estimativa de modelo (distorção: simulação ilustrativa) |
| `crystallography/exportacao.py` | CIF e XYZ | B | — |
| `thermodynamics/termico.py` | Dilatação linear (α isotrópico), deslocamento quadrático médio por Lindemann, alotropia sob política de dados, mistura em fração atômica; domínio de validade explícito (100 K a T_f) | v1.4 + R2 | estimativa de modelo |
| `procedencia.py` | Valor com estado e fonte, política por ambiente, bloco `procedencia` | novo | — |

## 3. Referências dos modelos

| Modelo | Referência | Onde |
|---|---|---|
| Relações de contato, FEA, densidade | Callister & Rethwisch, seções 3.4–3.5 | `celula.py`, `passos.py` |
| Densidade planar (CFC/CCC/CS {100},{110},{111}; HC (0001)) | Callister & Rethwisch, seção 3.11; valores fechados conferidos (ex.: CFC(111) = π/(2√3)) | `planar.py` |
| Lei de Vegard | Vegard, Z. Phys. 5, 17–26 (1921) | `ligas.py` |
| % atômica ↔ % em peso | Callister & Rethwisch, eq. 4.6–4.7 | `ligas.py` |
| Hume-Rothery (±15 %, estrutura, valência) | Callister & Rethwisch, seção 4.3 | `ligas.py` |
| Eletronegatividade ±0,4 | Darken & Gurry, Physical Chemistry of Metals (1953) | `ligas.py` |
| Regra de Hägg (r/R < 0,59) | Hägg (1931), via literatura de intersticiais | `ligas.py` |
| Raio livre dos sítios (CS cúbico 0,732R; CCC octaédrico 0,155R e tetraédrico 0,291R; CFC octaédrico 0,414R e tetraédrico 0,225R; HC pela geometria com o c/a em uso) | Geometria de esferas rígidas (derivação analítica, parecer R1-CRI-01 §3.4) | `sitios.py` |
| FEA do HC pelo raio de contato R_c = ½·mín(a, c, d_entre_planos) | Derivação de esferas rígidas sem sobreposição (parecer R1-CRI-01 §1.4, com a ressalva R-1 do parecer de termodinâmica §7.a: a translação `c` é a menor distância quando c/a < 2/3); limite π/(3√2) ≈ 0,74048 garantido em todo c/a > 0 | `geometria.py`, `passos.py` |
| Dilatação linear | Callister & Rethwisch, seção 19.3 | `termico.py` |
| Critério de Lindemann (f = 0,10) | Lindemann, Phys. Z. 11, 609–612 (1910) | `termico.py` |

As faixas de temperatura homóloga (0,3 e 0,5·T_f) **não têm fonte verificada neste repositório**: as notas que as
usam saem com `fonte` explicando isso e a resposta traz o aviso correspondente em `procedencia.avisos`
(consulta C-07-D ao auditor bibliográfico). A convenção de f do critério de Lindemann (√⟨u²⟩ 1D ou 3D) também
não foi verificada na fonte (C-07-A), e as faixas de alotropia seguem sem fonte (C-07-B).

> As referências citadas pela edição do Callister ainda precisam de edição e página (CR-10, Q-03). As demais referências também devem ser conferidas pelo validador científico antes da publicação.

## 4. Política de dados (PI-02, ADR-014)

| Dado | Estado inicial | Em `dev`/`test` | Em `prod` |
|---|---|---|---|
| Seed do B (raio, massa, densidade, c/a, *a* do Ti) | `aguardando_validacao` | usado, com aviso | **usado, com aviso** (já estava em produção na v1.1; ver decisão abaixo) |
| Dados da v1.4 (χ, valência, T_f, α, raios de C/N/H, alotropia) | `rascunho`, sem fonte | usados, com aviso em `procedencia.avisos` e listados em `dados_usados` | **recusados** (`DADO_NAO_VALIDADO`). Regras de Hume-Rothery que dependem deles ficam `indisponivel`; Vegard e densidade continuam |

**Decisão registrada (complemento do ADR-014):** o seed do B alimenta o motor de células em todos os ambientes, com aviso explícito. Bloqueá-lo deixaria a aplicação sem a função central até a validação humana. Os dados novos da v1.4 nunca tiveram fonte e por isso ficam bloqueados em produção.

## 5. Mudanças de comportamento em relação às origens

| Mudança | Antes | Agora | Por quê |
|---|---|---|---|
| Repositório | Padrão implícito (`repositorio_padrao()` dentro do motor) | Injetado obrigatoriamente | Motor puro (ADR-004) |
| Densidade planar | A publicava para qualquer plano | Só famílias validadas; demais retornam `validado: false` + motivo | CIE-04 |
| Ordenação L1₂/L1₀/B2 | A apresentava como fase | Protótipo geométrico com aviso "hipotético" | Ex.: Fe–Cr não forma B2 (forma σ) |
| *a* informado | Só na A, sem `a_fonte` | `a_fonte = "informado"`, R derivado com validação de faixa | Rastreabilidade |
| Densidade do Ti | A/D: 4,792 g/cm³ (+6,3 %) | 4,500 g/cm³ (−0,2 %) | ADR-005 |
| **FEA do HC com c/a < ideal (V-15)** | R = a/2 em qualquer c/a → Mg 0,744581; Ti 0,761816; Co 0,745040 (acima do limite de empacotamento: esferas sobrepostas) | R_c = ½·mín(a, d_entre_planos) → Mg 0,736418; Ti 0,720132; Co 0,735968; Zn inalterado (0,651508) | Achado E-1 do parecer R1-CRI-01 §1.4; FEA > π/(3√2) é fisicamente impossível |
| **FEA do HC com c/a < 2/3 (R2, ressalva R-1)** | `R_c = ½·mín(a, d_entre_planos)`: abaixo de c/a = 2/3 a translação `c` passa a ser a menor distância e faltava na fórmula, de modo que o FEA voltava a crescer (≈1,2 em c/a = 0,2, impossível) | `R_c = ½·mín(a, c, d_entre_planos)`; FEA ≤ π/(3√2) em todo c/a > 0 | Ressalva R-1 do parecer de termodinâmica §7.a. **Nenhum valor alcançável pela API muda**: `FAIXA_C_A` começa em 1,0 |
| **Motor térmico acima da T_f (T-1)** | `a_nm`, `fator`, `delta_a_pct`, `delta_v_pct` e `densidade` eram devolvidos para um líquido; a curva ia de −273,15 °C a T_f + 200 °C | Esses cinco campos saem `null` com o motivo em `indisponiveis`; a curva vale de 100 K à T_f (`curva_dominio`) | Parâmetro de rede de líquido não tem significado (parecer §2.2) |
| **Motor térmico, mistura (T-6)** | `fundido = T ≥ T_f` disparava "o material é líquido" com a T_f da regra das misturas | `fundido` é falso em mistura (o estado líquido não é afirmado); `acima_da_tf_nominal`, `tf_natureza` e `tf_rotulo` ("T_f nominal (regra das misturas) — não é solidus nem liquidus") | Ligas fundem entre solidus e liquidus (parecer §2.4) |
| **Motor térmico, alotropia (T-8, T-9)** | As faixas eram lidas sem passar pela `PoliticaDados` e não entravam em `dados_usados`: o sistema afirmava a fase estável sem procedência, inclusive em produção | A faixa passa pela política e é registrada na procedência; sem dado validado, `alotropia = null` com o motivo e nenhuma nota de fase | Achados críticos do parecer §2.6 |
| **Motor térmico, Lindemann (T-4, T-11)** | u era chamado de amplitude e a curva começava em 0 K (u = 0, fisicamente errado) | `u_natureza`/`u_rotulo` = deslocamento quadrático médio estimado; abaixo de 100 K o valor vai para `extrapolacao` com alerta e a curva é truncada | Movimento de ponto zero e limite clássico (parecer §2.3) |
| **Motor térmico, textos (T-5, T-7)** | "Entre 0,3 e 0,5·T_f ocorrem recuperação e recristalização", incondicional e sem fonte | Texto condicionado a deformação prévia a frio, marcado como faixa de ordem de grandeza e com `fonte` dizendo que não há fonte verificada | Recristalização é cinética e exige deformação (parecer §2.5) |
| **Textos do HC (V-16)** | "12 vizinhos a essa distância", contato "na aresta basal", FEA = FEA_ideal·(c/a)_ideal/(c/a) | 6 + 6 vizinhos (`nc_txt`), contato "entre planos" quando c/a < ideal, FEA derivado do raio de contato | idem |
| **Amostragem das ligas (V-8, V-9)** | Sorteio e contagem sobre as esferas DESENHADAS: imagens do mesmo átomo com elementos diferentes; `n_soluto`/`n_solvente` contavam esferas | Supercélula periódica: sorteio e contagem sobre os Z·n³ átomos ÚNICOS; imagem herda o elemento da origem e nunca é contada | Achados L-1 e L-5 (críticos) |
| **Intersticiais (V-10)** | `max(1, round(n_esferas·x/(1−x)))` — mínimo forçado de 1 átomo | `⌊N_rede·x/(1−x) + ½⌋`, sem mínimo; 0 átomo é devolvido com aviso de resolução | Achado L-5 |
| **`semente: 0` (V-11)** | Trocada por 1 em silêncio | Respeitada | Achado L-11 |
| **Conclusões de solubilidade (V-12)** | "solubilidade sólida extensa, possivelmente completa", "solubilidade intersticial alta" | Redação de critério: as regras são empíricas e o limite depende do diagrama de fases | Achado L-4 |
| **Ligas multicomponentes (V-13)** | Só binária (`soluto` obrigatório) | `solutos` com 1 a 6 itens, substitucionais e/ou intersticiais; `soluto` continua válido | Achado L-2 |

## 6. Limitações conhecidas

- A validação CIF com Gemmi está prevista, mas o Gemmi não tem pacote para Python 3.15 nesta máquina. O teste fica pulado aqui e deve rodar no CI com Python 3.11–3.13.
- O α do modelo térmico é constante: abaixo de 20 °C é extrapolação (a resposta avisa) e abaixo de 100 K o
  valor vai para `extrapolacao`, porque α → 0 pela terceira lei.
- A fração 0,10 de Lindemann é o limite inferior da faixa ~0,1–0,15 citada na literatura (viés sistemático
  para baixo, declarado em `hipoteses`). Usar Lindemann para estimar u é inverter um critério de fusão:
  estimativa de ordem de grandeza, não medida.
- A dilatação é **isotrópica por hipótese** (`dilatacao_isotropica = true`). Em HC (Mg, Ti, Zn, Co) a dilatação
  real é anisotrópica; não há coeficientes por eixo no repositório, e a resposta alerta em vez de estimar.
- O motor térmico **não calcula solidus nem liquidus** e não avalia alotropia de liga: a T_f de mistura é uma
  interpolação linear em fração atômica, declarada em `tf_rotulo`.
- A distorção de rede é ilustrativa e não resolve elasticidade (calculada sobre os átomos únicos, com imagem mínima, e copiada para as imagens).
- **Ligas: o motor não verifica limite de solubilidade nem prevê fases secundárias.** O repositório não tem
  diagramas de fases. Toda resposta traz `verificacoes.limite_solubilidade.verificado = false`,
  `verificacoes.fases_secundarias.previstas = null` e o aviso de modelo de fase única. Sistemas multifásicos
  NÃO são implementados (parecer R1-CRI-01 §3.7).
- O parâmetro de rede da liga é interpolação linear de raios TABELADOS na estrutura do solvente (extensão da
  regra de Vegard); não há dado experimental de liga no repositório. Intersticiais não dilatam a rede neste
  modelo, e a densidade com intersticial tende a ser superestimada (hipótese declarada em `modelo.hipoteses`).
- Pendência V-14 (fora do contrato R1): com solvente de rede medida (hoje só o Ti) a liga continua usando
  a = k·R̄ e avisa. Trocar a base da interpolação pelo `a` medido muda `a_base_nm`, `a_nm`, `densidade` e
  `densidade_base` e depende de aprovação.
- Letras de Wyckoff dos sítios intersticiais e das fases ordenadas: `wyckoff` é sempre `null` até conferência
  bibliográfica (decisão D-e do portão G1). O sítio padrão (`sitio = "auto"`, octaédrico) vem com
  `padrao_verificado: false`.
- O limite operacional de 20 % atômica para intersticiais não é limite físico. Com ele, a capacidade de sítios
  nunca é excedida (há sempre pelo menos Z sítios por célula), e o erro `capacidade_sitios_excedida`
  permanece como guarda defensiva.
