# Motor HEA

Código: `backend/app/engines/hea/` (versão do motor **2.0.0**, rodada R1 de 12/11/2026). Rotas:
`GET /api/v1/hea/bootstrap` e `POST /api/v1/hea/analyses` (ver [API.md](API.md)).
Contrato: `docs/architecture/2026-11-12_contrato_R1.md` (seções 1 e 4.1). Especificação científica:
`docs/agent_reports/2026-11-12_auditoria_hea.md` (seção 2). Decisões: `docs/architecture/2026-11-12_decisoes_G1_R1.md` (D-1).

| Arquivo | Conteúdo |
|---|---|
| `analitico.py` | cálculo das grandezas, triagem, domínio do VEC, catálogo do bootstrap |
| `entrada.py` | validação da composição (símbolo, repetição, limites) |
| `erros.py` | erros de entrada com subtipo estável (`details[].type`) |
| `referencia.py` | contratos de dados injetados: identidade dos elementos e matriz de entalpias por par |
| `textos.py` | limiares, fontes citadas, definições e avisos fixos |

## 1. Princípio

O motor calcula **só o que tem base citável** (PI-02). Uma grandeza sem base volta como `null`, e o
motivo vem em `indisponiveis`, na chave com o **nome exato do campo**. Nenhum valor é estimado para
preencher a tela: dureza, ductilidade e energia de formação não são calculadas; ΔH_mix, Ω e ΔG_mix
só saem quando a matriz de entalpias por par existir com fonte (questão Q-01, ainda aberta).

**Nenhuma referência bibliográfica citada aqui foi conferida na fonte.** Todo critério sai da API
com `verificada: false` até a auditoria bibliográfica.

O HEA Virtual Lab v1.17 (fonte do contrato do frontend) dependia de um `hea_engine` que nunca fez
parte do material recebido (achado D-01 da auditoria). Por isso este motor foi **construído do zero**
a partir da literatura. Não é um porte.

## 2. Entrada

`{"nome"?, "composicao": {símbolo: quantidade}, "base"?: "atomica" | "massica"}`.

Regras, na ordem de aplicação (falha → erro com o subtipo em `details[].type`):

| # | Regra | Falha |
|---|---|---|
| esquema | quantidade é número JSON (texto e booleano recusados); até 12 chaves; pelo menos 2 quantidades diferentes de zero | 422 `float_type`, `too_long`, `elementos_insuficientes` |
| 1 | quantidade finita, 0 ≤ q ≤ 1e6 (limite operacional: evita estouro numérico) | 400 `quantidade_invalida` |
| 2 | símbolo com 1 ou 2 letras, normalizado para `Xx` (`fe` → `Fe`, `NI` → `Ni`) | 400 `simbolo_invalido` |
| 3 | símbolo existe entre os 118 da tabela periódica | 400 `elemento_desconhecido` |
| 4 | sem repetição depois da normalização (duplicatas nunca são somadas) | 400 `elemento_repetido` |
| 5 | quantidade zero é descartada, com aviso em `procedencia.avisos` | — |
| 7 | base mássica: todo elemento precisa de massa utilizável | 400 `massa_indisponivel` (ausente) ou 422 `DADO_NAO_VALIDADO` (não validada, produção) |
| 8 | toda fração atômica ≥ 1e-6 (resolução da saída) | 400 `fracao_abaixo_do_minimo` |

A soma é livre (partes proporcionais) e volta em `soma_informada`.

**Elemento real sem dados de HEA** (por exemplo Mn): 200 com cálculo parcial. ΔS_mix e a curva
−T·ΔS_mix saem; o que faltou vai em `indisponiveis` e `dados_faltantes`.

**Lista de símbolos:** vem de `database/seeds/tabela_periodica/elementos.json`, de onde o motor lê
**só identidade e classificação** (símbolo, nome, número atômico, categoria, grupo). Nenhuma
propriedade da tabela periódica entra no cálculo (ADR-018 mantido).

## 3. Grandezas

Todas usam frações **atômicas** xᵢ. A entrada em massa é convertida antes: xᵢ = (wᵢ/Mᵢ)/Σ(wⱼ/Mⱼ).

| Grandeza (campo) | Fórmula | Classe | Dados usados | Fonte do modelo (não verificada) |
|---|---|---|---|---|
| ΔS_mix (`dS`, `dS_R`) | −R·Σ xᵢ ln xᵢ | analítico (solução ideal) | nenhum | entropia configuracional de Boltzmann |
| −T·ΔS_mix (`curva_T[].menos_TdS`) | de 300 K a `T_sup_k`, passo 50 K | analítico | nenhum | idem |
| δ (`delta`), r̄ (`raio_medio_nm`) | 100·√(Σ xᵢ(1 − rᵢ/r̄)²), r̄ = Σ xᵢ rᵢ | estimativa | raio atômico (seed base, `aguardando_validacao`) | Zhang et al., *Adv. Eng. Mater.* 10, 534 (2008) |
| T_m (`Tm`) | Σ xᵢ·T_f,ᵢ | estimativa (regra das misturas) | temperatura de fusão (seed v1.4, `rascunho`) | prática usual na literatura de HEA |
| VEC | Σ xᵢ·VECᵢ | estimativa | VEC (seed `hea/vec.json`, `aguardando_validacao`) | Guo et al., *J. Appl. Phys.* 109, 103505 (2011) |
| composição em massa (`fracoes_massa`, `comp_massa_pct`, `massa_molar_media`) | wᵢ = xᵢMᵢ/Σ xⱼMⱼ; M̄ = Σ xᵢMᵢ | analítico | massa atômica do repositório de materiais (15 metais, `aguardando_validacao`) | — |
| ΔH_mix (`dH`) | Σ_{i<j} 4·ΔH_ij·xᵢxⱼ, kJ/mol | estimativa | matriz de entalpias por par (**inexistente**) | Takeuchi & Inoue, *Mater. Trans.* 46, 2817 (2005) |
| Ω (`omega`) | T_m·ΔS_mix/(1000·\|ΔH_mix\|) | estimativa | idem | Yang & Zhang, *Mater. Chem. Phys.* 132, 233 (2012) |
| ΔG_mix (`curva_T[].dG`, `dG_Tm`, `gibbs`) | ΔH_mix − T·ΔS_mix | estimativa | idem | solução regular |
| T* (`T_cruzamento_k`) | 1000·ΔH_mix/ΔS_mix, só com ΔH_mix > 0 | estimativa | idem | — |
| energia de formação (`energia_formacao`) | — | **sempre `null`** | exige DFT, CALPHAD ou calorimetria | — |

R = 8,314462618 J/(mol·K) (CODATA 2018). `T_sup_k` = T_m arredondado para cima ao múltiplo de 100 K;
sem T_m, 2000 K (com aviso). `gibbs` (J/mol) é obsoleto: use `curva_T` (kJ/mol).

**Massas:** são as do repositório de materiais (`peso_g_mol` dos 15 metais), as que os motores já
liam. Elemento fora dessa lista não tem massa: com base atômica, a composição em massa fica `null`
com motivo; com base mássica, o pedido é recusado. A troca para as massas da tabela periódica
(CIAAW) depende de decisão do usuário (consulta C-02).

### 3.1 ΔH_mix e Ω são condicionais

* O motor recebe a matriz por um repositório (`RepositorioEntalpias`). O leitor é
  `backend/app/repositories/entalpias_json.py`, que procura `database/seeds/hea/entalpias_binarias.json`
  no formato da auditoria (seção 2.4.5).
* **O arquivo não existe.** Nenhum valor de entalpia binária foi cadastrado nesta rodada. Arquivo ausente
  ou vazio significa "nenhum par": `dH`, `omega`, `dG_Tm`, `T_cruzamento_k` e todo `curva_T[].dG` voltam
  `null`, `gibbs` volta vazio, e `pares_faltantes` lista os n(n−1)/2 pares da liga.
* Com a matriz: ΔH_mix só é calculado se **todos** os pares da liga forem utilizáveis (em produção, só
  `validado`). Faltando um par, não há soma parcial nem ΔH_ij = 0 presumido.
* |ΔH_mix| < 1e-9 kJ/mol → Ω indefinido (`null` com motivo). |ΔH_mix| < 1 kJ/mol → Ω sai com aviso
  (limite heurístico do especialista, a confirmar).
* Regras de carga do arquivo: par em ordem alfabética e único, símbolos existentes, valor finito em
  kJ/mol, estado conhecido, `validado` exige fonte. Violação é erro de dados (`ErroDeDados`).
* O caminho "com matriz" é testado com uma matriz **fictícia** criada dentro do teste.

## 4. Critérios, triagem e domínio do VEC

`criterios` traz cada critério com valor, operador, limiar, `atende`, `aplicavel`, fonte e `verificada`
(sempre `false` nesta rodada):

| Código | Condição | Natureza | Fonte citada (não verificada) |
|---|---|---|---|
| `delta_yang_zhang` | δ ≤ 6,6 % | empírico | Yang & Zhang (2012) |
| `omega_yang_zhang` | Ω ≥ 1,1 | empírico | Yang & Zhang (2012) |
| `vec_cfc_guo` | VEC ≥ 8,0 | empírico | Guo et al. (2011) |
| `vec_ccc_guo` | VEC < 6,87 | empírico | Guo et al. (2011) |
| `ds_alta_entropia` | ΔS_mix ≥ 1,5R | definição | Yeh (2006); Miracle & Senkov (2017) |

As comparações usam o valor não arredondado, com tolerância 1e-9. `proximo_do_limiar` marca valor a
menos de 2 % do limiar (margem heurística do especialista).

**Triagem** (`triagem.estado`; `veredito` repete `triagem.texto`). Critério conjunto Ω ≥ 1,1 **e** δ ≤ 6,6 %:

| Estado | Regra |
|---|---|
| `favoravel` | os dois avaliados e atendidos |
| `desfavoravel` | pelo menos um avaliado e não atendido (δ > 6,6 % sem Ω já é desfavorável) |
| `inconclusiva` | nenhum falhou e pelo menos um não pôde ser avaliado; ou há elemento não metálico |

A palavra "ESTÁVEL" não é usada. A triagem é indicador empírico: não comprova fase única nem estabilidade.
Sem a matriz de entalpias, o estado real é sempre `inconclusiva` ou `desfavoravel`.

**Domínio do critério de VEC** (`vec_aplicavel`). O VEC é sempre calculado quando há dados, mas a
sugestão de estrutura (`fase`, `estrutura_sugerida`) só sai quando valem todas as condições:

1. VEC disponível;
2. ΔS_mix ≥ 1R;
3. todos os elementos são metais de transição dos grupos 4 a 11, ou Al;
4. a triagem não é `desfavoravel`.

> **Regra conservadora do especialista, sem fonte bibliográfica.** As condições 2 e 3 delimitam o
> domínio por prudência e estão pendentes de parecer (consulta C-05). O aviso correspondente vai em
> `procedencia.avisos`.

Fora do domínio: `fase` = "não avaliada: …", `estrutura_sugerida` = `null` (sempre enviado) e o motivo
em `indisponiveis["estrutura_sugerida"]`. Os textos de "não avaliada" não contêm siglas de estrutura
nem símbolos de elemento, porque a interface procura as siglas no texto sem diferenciar maiúsculas.

## 5. Política de dados

* **dev/test:** valores `rascunho` e `aguardando_validacao` são usados. Cada um aparece em
  `procedencia.dados_usados`, e um aviso é emitido.
* **prod:** só valores `validado` com fonte são usados. Como nenhum está validado ainda, a produção devolve
  ΔS_mix, `dS_R`, `classe_entropia`, a curva −T·ΔS_mix e os critérios (sem valor, exceto o de entropia).
  δ, T_m, VEC e a composição em massa voltam `null`, cada um com o motivo e a entrada em
  `dados_faltantes` (`situacao: "nao_validado"`). Base mássica em produção → 422 `DADO_NAO_VALIDADO`.
* `procedencia.dados_usados` só lista o dado que entrou num resultado calculado.

## 6. Bootstrap

Campos mantidos: `elements` (15 metais com dados), `alloys`, `reference` (obsoleto: são limiares, não
uma liga de referência), `samples`, `versao_motor`. Campos novos: `elements[].tem_massa`;
`elementos_aceitos` (118 símbolos com `tem_raio`, `tem_fusao`, `tem_vec`, `tem_massa` conforme o que
o ambiente consegue usar; sem valores de propriedade); `criterios`; `entalpias`
(`{"disponivel": false, "n_pares": 0, ...}` nesta rodada); `guias_entropia` (R·ln n, n = 2 a 6);
`definicoes` (9 itens); `avisos_fixos` (3 itens). `samples` são as ligas de exemplo calculadas pelo
próprio motor, com a mesma política de dados.

## 7. Verificação

* `backend/tests/unit/engines/test_hea.py`: casos T-01 a T-21 da auditoria (ΔS = R·ln n; invariância de
  escala; δ com raios sintéticos; regressão de ΔS, δ, VEC e T_m contra a saída do motor 1.0.0; ida e
  volta atômica ↔ mássica; ΔH_mix, Ω, ΔG e T* com matriz fictícia; validação de entrada; domínio do
  VEC; triagem; motivo para toda grandeza nula; produção; leitor da matriz de pares).
* `backend/tests/api/test_hea_r1.py`: T-H1 a T-H9 do contrato, tabela de erros, entradas hostis sem 500
  e regressão das falhas A-01, A-02, A-03, A-07, A-08 e A-09.
* `backend/tests/integration/test_servico_calculo.py`: resultado pelo banco é igual ao do seed JSON, e a
  execução fica gravada no histórico.
* Contrato real: `scripts/contrato_frontend.mts` valida as respostas HEA com os esquemas zod do front.

## 8. Pendências

1. **Q-01:** matriz de ΔH_mix por par, transcrita da fonte com conferência dupla. Sem ela, ΔH_mix, Ω e
   ΔG_mix continuam `null`.
2. **C-02:** massas da tabela periódica no motor (hoje só os 15 metais têm massa).
3. **C-03, C-04, P-HEA-01:** fonte única de T_f, VEC por regra do grupo e tabela de raios metálicos.
   Sem isso a liga de Cantor só devolve ΔS_mix.
4. **C-05:** parecer sobre o domínio do VEC e sobre as margens heurísticas (2 %, 1 kJ/mol).
5. Conferência bibliográfica de todos os limiares (`verificada`).
6. Não implementado nesta rodada: recusa de δ e T_m quando os dados vêm de fontes diferentes
   (auditoria 2.3, item 2); `temperatura_k` e `ponto_T` (fora de R1); a matriz de pares só é lida de
   arquivo (não há tabela no banco).
7. Dureza e ductilidade: só com modelo publicado e conjunto de dados. O ML continua reservado
   (`engines/machine_learning/`).
