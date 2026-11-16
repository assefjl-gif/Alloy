# API — contratos `/api/v1`

| Item | Valor |
|---|---|
| Estilo | REST + JSON, FastAPI/Pydantic, OpenAPI 3.1 em `/api/v1/openapi.json` |
| Convenções | ADR-006 (rotas em inglês, campos em português, envelope atual) |
| Autenticação | Cookie de sessão + `X-Alloy-CSRF` em escritas (ADR-008) |
| Autorização | `autorizar(ator, ação, recurso)` em `services` (ADR-009) |
| Responsável | Agente 01; consumidores alinhados pelo Agente 06 |
| Estado | **Proposta para o Gate 1**. A implementação começa na Fase 4; os nomes de schema existentes no B são preservados. |

## 1. Convenções

### 1.1 Envelope (compatível com B e C)

```json
{ "ok": true, "result": { ... } }
{ "ok": false, "error": "Mensagem em pt-BR para o usuário", "code": "ENTRADA_INVALIDA", "status": 422,
  "request_id": "01JC…", "detalhes": [{"campo": "indices", "motivo": "…"}] }
```

### 1.2 Cabeçalhos

| Cabeçalho | Direção | Uso |
|---|---|---|
| `X-Request-ID` | ambos | Correlação; gerado se ausente |
| `X-Alloy-CSRF` | requisição | Obrigatório em POST, PUT, PATCH e DELETE autenticados |
| `If-Match` / `ETag` | ambos | Controle otimista (atividades, questões, caderno) → 409/412 |
| `Idempotency-Key` | requisição | Opcional em POST de tentativa e de entrega |
| `Deprecation`, `Link` | resposta | Rotas alias `/v1/*` e legadas (padrão já existente no B) |
| `Retry-After` | resposta | 429 |

### 1.3 Coleções

`GET /recurso?pagina=1&tamanho=20&ordem=-criado_em&<filtro>=valor`, com `tamanho` ≤ 100.
Resposta: `result = {"itens": [...], "total": 123, "pagina": 1, "tamanho": 20}`.

### 1.4 Códigos de erro

Mantidos do B: `ENTRADA_INVALIDA`, `VALIDACAO`, `REQUISICAO_INVALIDA`, `NAO_AUTENTICADO`, `PROIBIDO`, `NAO_ENCONTRADO`, `METODO_NAO_PERMITIDO`, `TIPO_NAO_SUPORTADO`, `CORPO_GRANDE_DEMAIS`, `LIMITE_DE_REQUISICOES`, `ERRO_INTERNO`, `ERRO_DOMINIO`, `MATERIAL_DESCONHECIDO`, `INDICE_MILLER_INVALIDO`, `PLANO_FORA_DA_CELULA`, `DADOS_INSUFICIENTES`.

Novos:

| Código | Status | Quando |
|---|---|---|
| `CONFLITO_VERSAO` | 409 | `If-Match` desatualizado |
| `CSRF_INVALIDO` | 403 | Escrita sem `X-Alloy-CSRF` válido |
| `CREDENCIAIS_INVALIDAS` | 401 | Login (mensagem única, sem revelar se o e-mail existe) |
| `EMAIL_NAO_VERIFICADO` | 403 | Login antes da verificação |
| `CAPACIDADE_INDISPONIVEL` | 503 | Motor ou serviço ausente (HEA sem dados, IA desligada). **Nunca** valor fictício |
| `DADO_NAO_VALIDADO` | 422 | Cálculo pediria um valor sem fonte em produção |
| `TRANSICAO_INVALIDA` | 409 | Mudança de estado não permitida (validação, entrega) |
| `TENTATIVAS_ESGOTADAS` | 403 | Política da questão |
| `COMPOSICAO_INVALIDA` | 422 | Soma ≠ 100% ± tolerância, ou elemento sem dados |

**Regra para recurso de outra instituição:** responde 404 `NAO_ENCONTRADO`, nunca 403 (ADR-009).

**`details` em erro de domínio (rodada R1):** o erro de domínio que tem subtipo traz `details` no mesmo formato do
422 de esquema: `[{"loc": [...], "type": "<subtipo>", "msg": "<mensagem pt-BR>"}]`. `error` repete a mensagem do
primeiro item. Texto enviado pelo usuário e ecoado na mensagem é truncado em 16 caracteres. Implementado no HEA
(§2.5.1); os demais erros de domínio continuam sem `details`.

**Mensagens e `loc` (rodada R2, correção R2-BE-02):**

- `details[].msg` é sempre pt-BR e **nunca** expõe construção interna. Em campo com `pattern` (e-mail, referência
  de elemento) a mensagem diz o que se espera (“informe um e-mail válido, no formato nome@dominio.com”); a expressão
  regular não é devolvida. `details[].type` continua sendo o subtipo nativo do validador
  (`string_pattern_mismatch`, `string_too_short`, …) e **não** mudou.
- `details[].loc` usa **inteiro** para índice de lista (`["solutos", 0, "elemento"]`) e texto para nome de campo ou
  chave de objeto (`["composicao", "Fe"]`), conforme o contrato R1 §4.2.
- O truncamento de 16 caracteres do valor ecoado vale também para `/crystallography/cells`,
  `/crystallography/density`, `/thermodynamics/thermal` e `/exports/*` (antes só HEA e ligas truncavam).

### 1.5 Procedência

Todo resultado científico traz `procedencia` (ARQUITETURA_FINAL §6). Os campos ausentes por falta de dado aparecem como:

```json
"omega": {"indisponivel": true, "motivo": "Tabela de entalpias de pares sem fonte para Mn–W"}
```

### 1.6 Perfis de acesso usados nas tabelas

`publico` (sem sessão) · `autenticado` · `estudante` · `professor` · `admin_inst` · `admin_geral` · `validador` (permissão `validar_dados`) · `dono` (dono do recurso).

## 2. Catálogo de rotas

### 2.1 Plataforma

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/health/live`, `/health/ready` | publico | Saúde (do B, fora do prefixo) |
| GET | `/api/v1/meta/capabilities` | publico | Por serviço: `{disponivel, demo_permitido, versao, motivo}` (ADR-016) |
| GET | `/api/v1/meta/version` | publico | Versões da API, dos motores e dos dados |

### 2.2 Autenticação e usuários (`/auth`, `/users`)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/api/v1/auth/register` | publico | Cadastro → e-mail de verificação (sem revelar duplicidade) |
| POST | `/api/v1/auth/verify-email` | publico | `{token}` |
| POST | `/api/v1/auth/login` | publico | `{email, senha}` → cookie de sessão + `csrf` no corpo |
| POST | `/api/v1/auth/logout` | autenticado | Revoga a sessão atual |
| POST | `/api/v1/auth/logout-all` | autenticado | Revoga todas as sessões |
| POST | `/api/v1/auth/password/forgot` | publico | Sempre 202 |
| POST | `/api/v1/auth/password/reset` | publico | `{token, nova_senha}` → revoga as sessões |
| GET | `/api/v1/auth/me` | autenticado | Usuário, vínculos, papéis efetivos e `csrf` |
| GET | `/api/v1/auth/sessions` | autenticado | Sessões ativas próprias |
| GET/PATCH | `/api/v1/users/me` | autenticado | Perfil e preferências (cores, tema, idioma — A/docs/1) |
| GET | `/api/v1/users/me/export` | autenticado | LGPD: exportar dados |
| POST | `/api/v1/users/me/anonymize` | autenticado | LGPD: com confirmação por senha |
| GET | `/api/v1/users` | admin_inst, admin_geral | Lista no escopo |
| PATCH | `/api/v1/users/{id}/status` | admin_inst, admin_geral | Bloquear ou reativar |

### 2.3 Organização acadêmica (`/institutions`, `/classes`)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET/POST | `/api/v1/institutions` | admin_geral (POST) · autenticado (GET das próprias) | |
| GET/PATCH | `/api/v1/institutions/{id}` | admin_inst do escopo | Configurações |
| POST | `/api/v1/institutions/{id}/members` | admin_inst | Vincular usuário com papel |
| GET/POST | `/api/v1/institutions/{id}/courses` | admin_inst | Cursos |
| GET/POST | `/api/v1/classes` | professor (POST) · membro (GET) | Turmas no escopo |
| GET/PATCH | `/api/v1/classes/{id}` | professor responsável | |
| POST | `/api/v1/classes/{id}/enrollments` | professor | Cadastrar estudantes (lista de e-mails → convite) |
| POST | `/api/v1/classes/join` | estudante | `{codigo_convite}` |

### 2.4 Cristalografia (`/crystallography`)

Contratos de entrada e saída **reaproveitados do B** (`StructureRequest`, `StructureResponse`, `MillerRequest`, `MillerResponse`, `DensityRequest`, `DensityResponse`, `ExportRequest`, `ExportResponse`), com os campos novos marcados como opcionais.

| Método | Rota | Acesso | Schema | Origem |
|---|---|---|---|---|
| GET | `/api/v1/crystallography/structures` | publico | `StructureInfo[]` | B `/v1/crystals/structures` |
| GET | `/api/v1/crystallography/metals` | publico | `Record<string, MetalInfo>` (só dados validados em prod) | B `/v1/crystals/metals` |
| POST | `/api/v1/crystallography/cells` | publico* | `StructureRequest` → `StructureResponse` + `passos_parametro`, `passos_fea`, `procedencia` | B `/v1/crystals/structure` + A |
| POST | `/api/v1/crystallography/density` | publico* | `DensityRequest` → `DensityResponse` | B `/v1/calculations/density` |
| POST | `/api/v1/crystallography/miller` | publico* | `MillerRequest` (+ `supercelula`) → `MillerResponse` (+ `atomos_plano`, `dp_nm`, `fracao_planar`, `poligonos`) | B + A |
| POST | `/api/v1/crystallography/supercells` | publico* | `{estrutura, n, c_a}` → átomos, arestas e vetores de rede (fecha D-10) | A |
| POST | `/api/v1/crystallography/solid-solutions` | publico* | `SolidSolutionRequest {base, soluto \| solutos, x, base_composicao, estrutura_matriz, n, arranjo, distorcer, semente}` → resultado da liga + regras de Hume-Rothery (ver 2.4.1) | A (`/api/liga`) |
| POST | `/api/v1/thermodynamics/thermal` | publico* | `{material \| liga, temperatura_c}` → a(T), ρ(T), deslocamento quadrático médio (Lindemann), alotropia, hipóteses e domínio (ver 2.4.2) | A (`/api/termico`) |
| POST | `/api/v1/thermodynamics/phase-diagram` | publico* | Especificação A/docs/2 §7 | novo (Fase 6) |

\* Público com rate limit. Com sessão, o cálculo também é gravado em `execucoes_calculo` (histórico pessoal).

#### 2.4.1 Ligas e células na rodada R1 (motor de cristalografia 2.1.0)

Contrato campo a campo: `docs/architecture/2026-11-12_contrato_R1.md`, seções 2, 3 e 4.2. Ciência:
`docs/agent_reports/2026-11-12_parecer_cristalografia.md` (§1.4 e §3). Todas as mudanças são aditivas, com as
exceções de valor listadas no fim desta seção.

**Pedido de liga.** Exatamente um entre `soluto` (forma binária legada, com `x`, padrão 10) e
`solutos` (1 a 6 itens `{elemento, x, modo?, sitio?}`). `modo`: `auto` (intersticial se o símbolo é C, H ou N),
`substitucional` ou `intersticial`. `sitio` (só intersticial): `auto` (octaédrico em CCC, CFC e HC; cúbico em CS),
`octaedrico`, `tetraedrico` ou `cubico`. `base_composicao`: `atomica` (padrão) ou `massica`, para todos os `x`.
`estrutura_matriz` impõe a estrutura da matriz (aviso de resultado hipotético quando difere do repositório).
`semente: 0` é válida e respeitada. A ordem dos itens de `solutos` não altera a resposta: a ordem canônica é
solvente, substitucionais em ordem de símbolo, intersticiais em ordem de símbolo.

**Resposta de liga — campos novos de primeiro nível:** `composicao` (solicitada × representada, `n_sitios_rede`,
`n_intersticiais`, `n_atomos_unicos`, `n_desenhados`, `resolucao_at_pct`, `desvio_maximo_at_pct`), `realizacao`
(`tipo`, `semente`, `algoritmo` = `mt19937-chaves-v1`, `n`, `aviso`), `modelo` (rótulos de natureza e
`hipoteses`), `prototipo` (só no arranjo ordenado), `fases` (1 item em R1, `fracao` sempre `null`),
`verificacoes` (o que o motor NÃO verifica), `regras_por_soluto`, `conclusao_global` (nulo com mais de um
soluto), `sitios`, `elementos` (propriedades TABELADAS dos elementos puros), `convencoes` e `indisponiveis`.

**Campos novos por átomo** (`atomos[]`): `id` estável (`r:{i}.{j}.{k}:{b}`, `i:{oct|tet|cub}:{i}.{j}.{k}:{s}`,
imagem = id da origem + `+{tx}{ty}{tz}`), `imagem`, `imagem_de`, `pos_nm`, `celula`, `frac_celula`, `ocupacao`,
`sitio {nome, wyckoff, nc, nc_txt}`, `fase` e `pos_ideal`. **Imagem de fronteira nunca entra em contagem,
composição ou massa** e tem sempre o elemento, o sítio e a ocupação do átomo de origem.

Avisos obrigatórios (modelo de fase única; intersticial acima do limite de solubilidade; estrutura de matriz
imposta; resolução da supercélula; solvente não majoritário; `x = 100` legado; pendência V-14) vão em
`procedencia.avisos`. `wyckoff` é sempre `null` (decisão D-e: aguarda conferência bibliográfica).

Erros de `POST /crystallography/solid-solutions`:

| Caso | Status | `code` | `details[].type` |
|---|---|---|---|
| `soluto` e `solutos` juntos, ou nenhum | 422 | `VALIDACAO` | `soluto_ou_solutos` |
| `x` junto com `solutos` | 422 | `VALIDACAO` | `x_com_solutos` |
| `solutos` vazia ou com mais de 6 itens | 422 | `VALIDACAO` | `too_short` / `too_long` |
| `modo`, `sitio`, `base_composicao` ou `estrutura_matriz` fora da enumeração | 422 | `VALIDACAO` | `literal_error` |
| elemento não resolvido pelo repositório | 400 | `MATERIAL_DESCONHECIDO` | `material_desconhecido` |
| soluto repetido depois da resolução | 400 | `ENTRADA_INVALIDA` | `soluto_repetido` |
| soluto igual ao solvente | 400 | `ENTRADA_INVALIDA` | `soluto_igual_ao_solvente` |
| metal como intersticial, ou C/H/N como substitucional | 400 | `ENTRADA_INVALIDA` | `modo_sem_dados` |
| `sitio` em soluto substitucional, ou sítio inexistente na estrutura | 400 | `ENTRADA_INVALIDA` | `sitio_incompativel` |
| Σx ≥ 100 % (fora o caso legado `soluto` com x = 100) | 400 | `ENTRADA_INVALIDA` | `soma_solutos_invalida` |
| Σ intersticiais > 20 % atômica (limite operacional) | 400 | `ENTRADA_INVALIDA` | `intersticial_acima_do_limite` |
| mais intersticiais que sítios do tipo | 400 | `ENTRADA_INVALIDA` | `capacidade_sitios_excedida` |
| dado necessário não validado, em produção | 422 | `DADO_NAO_VALIDADO` | — |

**Células (`POST /crystallography/cells`) — campos novos:** `nc_txt` (`"6 + 6"` no HC com c/a ≠ ideal),
`fea_modelo` (`esferas_rigidas`), `raio_contato_rel`, `contato_tipo` (`basal` | `entre_planos` | `ambos`),
`c_a_ideal`, `c_a_natureza` (`ideal` | `tabelado` | `derivado_de_a_c_medidos` | `informado`) e `vizinhos`
(dois grupos de 6, com `d_rel` e `d_nm`). Os cinco últimos são nulos fora do HC ("não se aplica"). O pedido
não muda e nenhum erro novo aparece.

**Térmico:** `POST /thermodynamics/thermal` com `liga.solutos` de mais de um item devolve 400
`ENTRADA_INVALIDA` com `details[].type = liga_multicomponente_nao_suportada` (decisão D-a: o motor térmico não
foi especificado para liga multicomponente).

#### 2.4.2 Térmico na rodada R2 (motor `thermodynamics` 2.0.0)

O pedido não muda e nenhum erro novo aparece. Os campos antigos continuam presentes; cinco deles passam a
poder ser `null`. Base: parecer de termodinâmica de 2026-11-13, §2.2 a §2.6.

| Campo | Tipo | Significado |
|---|---|---|
| `fator`, `a_nm`, `delta_a_pct`, `delta_v_pct`, `densidade` | número **ou `null`** | Nulos acima da T_f do modelo, com o motivo em `indisponiveis[campo]` (T-1): não há cristal, logo parâmetro de rede, densidade cristalina e dilatação não têm significado. `a_ref_nm` (20 °C) continua sempre presente. |
| `fundido` | booleano | **Semântica revista (T-6):** afirma estado líquido. Só é verdadeiro para elemento puro acima da T_f tabelada; em mistura é **sempre falso**, porque a T_f da regra das misturas não é solidus nem liquidus. |
| `acima_da_tf_nominal` | booleano | A comparação numérica `T ≥ T_f do modelo`, sem afirmação sobre o estado físico. |
| `tf_natureza` | `tabelada_do_elemento` \| `nominal_regra_das_misturas` | Origem da T_f usada. |
| `tf_rotulo` | texto | Rótulo obrigatório da T_f ("T_f nominal (regra das misturas) — não é solidus nem liquidus" em mistura). |
| `mistura_base` | `atomica` \| `null` | Base da interpolação de α e T_f; nulo sem mistura. |
| `dilatacao_isotropica` | booleano | Hipótese imposta pelo modelo (T-2). Em HC a resposta traz nota de alerta sobre a anisotropia real. |
| `u_natureza`, `u_rotulo` | texto | `u_nm` é o **deslocamento quadrático médio estimado**, não amplitude de oscilação (T-11). |
| `lindemann_natureza` | texto | `limite_inferior_da_faixa_0_10_a_0_15`: f = 0,10 enviesa u para baixo. |
| `curva` | lista `[T (°C), u/d]` | Agora limitada ao domínio do modelo: de 100 K à T_f (antes: −273,15 °C a T_f + 200 °C). Vazia se não houver domínio válido, com motivo em `indisponiveis.curva`. |
| `curva_dominio` | objeto | `de_c`, `ate_c`, `limite_inferior`, `limite_superior` (motivos do corte). |
| `alotropia` | objeto ou `null` | Faixa de estabilidade com `fase`, `estrutura`, `de_c`, `ate_c`, `estado`, `fonte` e `pressao = "nao_modelada"`. **Null com motivo em `indisponiveis.alotropia`** quando o dado não passa pela política do ambiente, quando não há faixa cadastrada, acima da T_f e em liga (T-8, T-9). |
| `hipoteses` | lista de textos | Isotropia, natureza e incerteza do Lindemann, pressão não modelada e (em mistura) base atômica. |
| `indisponiveis` | objeto `campo → motivo` | Convenção do contrato R1 §0. |
| `extrapolacao` | objeto `campo → motivo` | Valor devolvido fora do domínio (abaixo de 100 K e acima da T_f, para `u_nm` e `razao_lindemann`). |
| `notas[].fonte` | texto ou `null` | Fonte da afirmação ou o motivo de não haver fonte verificada (T-5, T-7: as faixas de 0,3 e 0,5·T_f não têm fonte neste repositório). |

**Efeito no frontend:** os cinco campos que podem virar `null` são hoje `z.number()` não anuláveis em
`frontend/src/services/api/contracts.ts` (`ThermalResult`). A migração do zod e dos painéis é tarefa do
frontend; o backend não a fez.

Mudanças de VALOR e de comportamento (contrato R1 §5.1, V-8 a V-16): `n_soluto` e `n_solvente` passam a contar
átomos ÚNICOS; o elemento de cada esfera muda para toda semente (novo algoritmo de sorteio); intersticiais sem
mínimo forçado de 1; `semente: 0` respeitada; `soluto` passou de obrigatório a opcional; nova redação de
`conclusao` e `regras[].detalhe`; no HC com c/a < ideal `fea` e `vazios` mudam (Mg 0,744581 → 0,736418;
Ti 0,761816 → 0,720132; Co 0,745040 → 0,735968; Zn inalterado) e os textos de `passos_fea`, `passos_parametro`,
`interpretacao` e `contato` foram reescritos. V-14 (usar o `a` medido do solvente como base da interpolação)
ficou FORA desta rodada.

### 2.5 HEA (`/hea`)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/api/v1/hea/compositions/validate` | publico | Normaliza (at% ↔ peso%), checa soma e dados disponíveis |
| POST | `/api/v1/hea/predictions` | publico* | ΔS_mix, T_m, VEC, δ; ΔH_mix e Ω quando houver pares com fonte; campos `indisponivel` explícitos (ADR-013) |
| GET | `/api/v1/hea/predictions/{id}` | dono | Resultado gravado |
| GET | `/api/v1/hea/history` | autenticado | Histórico paginado |
| POST | `/api/v1/hea/compare` | publico* | Até 6 composições lado a lado |
| GET | `/api/v1/hea/references` | publico | Equações, limiares e fontes usadas pelo motor |

Enquanto Q-01 não for resolvida: `/meta/capabilities` informa `hea.preditor_fase = indisponivel`. O frontend mostra "indisponível" e, só em dev, o demonstrativo rotulado.

#### 2.5.1 HEA implementado (rodada R1, motor 2.0.0)

A tabela acima é o desenho original. O que existe são duas rotas (contrato campo a campo em
`docs/architecture/2026-11-12_contrato_R1.md`, seções 1 e 4.1; motor em [MOTOR_HEA.md](MOTOR_HEA.md)):

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/api/v1/hea/bootstrap` | publico | `elements`, `alloys`, `reference` (obsoleto), `samples`, `versao_motor`, `elementos_aceitos` (118), `criterios`, `entalpias`, `guias_entropia`, `definicoes`, `avisos_fixos` |
| POST | `/api/v1/hea/analyses` | publico* | Descritores de triagem de uma liga |

Pedido: `{"nome"?: texto até 80, "composicao": {símbolo: número}, "base"?: "atomica" | "massica"}`. `composicao`: 1 a 12
chaves, número JSON estrito (texto e booleano recusados), 0 ≤ q ≤ 1e6, soma livre, pelo menos 2 quantidades maiores
que zero. O símbolo é normalizado (`fe` → `Fe`) e conferido contra os 118 da tabela periódica.

Resposta (campos principais): `dS`, `dS_R`, `classe_entropia`, `delta`, `raio_medio_nm`, `VEC`, `Tm`, `dH`, `omega`,
`comp_percent` e `fracoes` (base atômica), `fracoes_massa`, `comp_massa_pct`, `massa_molar_media`, `base_entrada`,
`soma_informada`, `curva_T` (`{T, menos_TdS, dG}`, kJ/mol, de 300 K a `T_sup_k`, passo 50 K), `dG_Tm`,
`T_cruzamento_k`, `energia_formacao` (sempre `null`), `criterios`, `triagem {estado, texto}`, `vec_aplicavel`, `fase`,
`estrutura_sugerida`, `classes`, `pares_faltantes`, `dados_faltantes`, `indisponiveis`, `procedencia`.

* Todo campo nulo de primeiro nível é **enviado** com `null` e tem o motivo em `indisponiveis[<nome do campo>]`.
* `veredito` repete `triagem.texto`. O estado é lido de `triagem.estado` (`favoravel`, `desfavoravel`,
  `inconclusiva`), nunca do texto. A palavra "ESTÁVEL" não é usada.
* `dH`, `omega`, `dG_Tm`, `T_cruzamento_k` e `curva_T[].dG` são `null` em qualquer ambiente: a matriz de entalpias
  por par não está cadastrada (`bootstrap.entalpias.disponivel = false`). `gibbs` (J/mol) é obsoleto e volta vazio.
* `estrutura_sugerida` só vem preenchida dentro do domínio do critério de VEC (`vec_aplicavel`), que é uma regra
  conservadora do especialista, sem fonte bibliográfica.
* Todo `criterios[].verificada` é `false`: nenhuma fonte foi conferida.
* Elemento real sem dados de HEA (ex.: Mn): 200 com cálculo parcial.

Erros de `POST /hea/analyses`:

| Caso | Status | `code` | `details[].type` |
|---|---|---|---|
| quantidade em texto ou booleano | 422 | `VALIDACAO` | `float_type` |
| mais de 12 chaves | 422 | `VALIDACAO` | `too_long` |
| `base` fora da enumeração | 422 | `VALIDACAO` | `literal_error` |
| campo não reconhecido (inclui `temperatura_k`, reservado) | 422 | `VALIDACAO` | `extra_forbidden` |
| menos de 2 elementos com quantidade maior que zero | 422 | `VALIDACAO` | `elementos_insuficientes` |
| quantidade negativa, NaN, ±Infinity ou maior que 1e6 | 400 | `ENTRADA_INVALIDA` | `quantidade_invalida` |
| símbolo que não tem 1 ou 2 letras | 400 | `ENTRADA_INVALIDA` | `simbolo_invalido` |
| símbolo fora dos 118 | 400 | `ENTRADA_INVALIDA` | `elemento_desconhecido` |
| mesmo elemento em duas chaves (inclusive por caixa) | 400 | `ENTRADA_INVALIDA` | `elemento_repetido` |
| base mássica e elemento sem massa no repositório | 400 | `ENTRADA_INVALIDA` | `massa_indisponivel` |
| base mássica, produção, massa não validada | 422 | `DADO_NAO_VALIDADO` | `massa_indisponivel` |
| fração atômica menor que 1e-6 | 400 | `ENTRADA_INVALIDA` | `fracao_abaixo_do_minimo` |

Mudanças de comportamento em relação ao motor 1.0.0 (contrato R1, V-1 a V-7): símbolo que não é elemento passou de
200 a 400; quantidade em texto ou booleano passou a 422; símbolos saem na forma canônica; `veredito` mudou de
"INCONCLUSIVO — …" para "TRIAGEM …"; a sugestão de estrutura só sai dentro do domínio; um só elemento devolve o
`type` `elementos_insuficientes`.

### 2.6 Materiais e repositório científico (`/elements`, `/materials`, `/alloys`, `/properties`, `/sources`)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/api/v1/elements` | publico | Elementos com valores **validados** e fontes |
| GET | `/api/v1/materials` | publico (validados) · escopo (demais) | Filtros: `tipo`, `estado`, `elemento`, `estrutura` |
| POST | `/api/v1/materials` | autenticado | Cria em `rascunho` (composição, processamento, estrutura) |
| GET/PATCH | `/api/v1/materials/{id}` | dono (rascunho) · leitura no escopo | PATCH só em `rascunho` |
| POST | `/api/v1/materials/{id}/properties` | dono | Novo `valor_propriedade` (unidade, classe, condições, fonte) |
| POST | `/api/v1/materials/{id}/submit` | dono | `rascunho → aguardando_validacao` |
| POST | `/api/v1/materials/{id}/review` | validador | `{decisao: validar\|rejeitar, comentario}` |
| POST | `/api/v1/materials/{id}/archive` | dono, validador | |
| GET | `/api/v1/materials/{id}/history` | escopo | Versões e revisões |
| GET | `/api/v1/alloys` | publico | Atalho de `/materials?tipo=liga,hea` |
| GET | `/api/v1/properties` | publico | Catálogo com unidades |
| GET/POST | `/api/v1/sources` | publico (GET) · validador (POST) | Fontes bibliográficas |

### 2.7 Educacional (`/activities`, `/assessments`, `/progress`, `/notebook`, `/files`)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET/POST | `/api/v1/activities` | professor (POST) · escopo (GET) | |
| GET/PUT | `/api/v1/activities/{id}` | autor | `If-Match` obrigatório no PUT |
| POST | `/api/v1/activities/{id}/publish` | autor | |
| GET/POST | `/api/v1/assessments/questions` | professor (POST) · estudante (GET **sem gabarito**) | |
| POST | `/api/v1/assessments/questions/{id}/test` | autor | Simula como estudante, sem gravar |
| POST | `/api/v1/assessments/questions/{id}/instances` | estudante | Cria ou retoma instância (parâmetros sorteados no servidor) |
| POST | `/api/v1/assessments/instances/{id}/attempts` | dono | Corrige no servidor; devolve `correta`, `tipo_erro`, feedback; gabarito só pela política |
| POST | `/api/v1/assessments/instances/{id}/hint` | dono | Próxima dica |
| GET | `/api/v1/progress/me` | autenticado | Por tópico, pontos fracos, recomendações |
| GET/POST | `/api/v1/notebook` | dono | Notas do caderno |
| GET/PUT/DELETE | `/api/v1/notebook/{id}` | dono | `If-Match` (sincronização offline do C) |
| GET | `/api/v1/files` | escopo | Biblioteca (tutoriais) com filtros por tipo |
| POST | `/api/v1/files` | professor, admin_inst | Upload binário em fluxo (lista branca, cota) |
| GET | `/api/v1/files/{id}/content` | escopo | Download com Range (vídeo) |
| DELETE | `/api/v1/files/{id}` | dono, admin_inst | Arquivamento |

### 2.8 Professor e relatórios (`/instructor`, `/reports`)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/api/v1/instructor/assignments` | professor da turma | Atividade → turma, prazos e critérios |
| GET | `/api/v1/instructor/assignments/{id}/submissions` | professor da turma | Entregas e tentativas |
| POST | `/api/v1/instructor/submissions/{id}/grade` | professor da turma | Nota (com histórico) |
| GET | `/api/v1/reports/classes/{id}` | professor da turma | Desempenho, dificuldades recorrentes (tipos de erro), distribuição |
| GET | `/api/v1/reports/classes/{id}/export` | professor da turma | CSV (UTF-8 com BOM) |

### 2.9 Exportação e IA

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/api/v1/exports/cif` | publico* | B `/v1/export/cif` (validado com Gemmi no CI) |
| POST | `/api/v1/exports/xyz` | publico* | B `/v1/export/xyz`; aceita supercélula e liga |
| POST | `/api/v1/ai/*` | autenticado | Sempre 503 `CAPACIDADE_INDISPONIVEL` até decisão (RQ-EDU-05) |

## 3. Compatibilidade e migração de contratos

| Rota atual | Consumidor | Rota nova | Transição |
|---|---|---|---|
| `/v1/crystals/metals` | C (modo v1) | `/api/v1/crystallography/metals` | Alias com `Deprecation` até a Fase 5 |
| `/v1/crystals/structures` | C | `/api/v1/crystallography/structures` | idem |
| `/v1/crystals/structure` | C | `/api/v1/crystallography/cells` | idem |
| `/v1/crystallography/miller` | C | `/api/v1/crystallography/miller` | idem |
| `/v1/calculations/density` | C | `/api/v1/crystallography/density` | idem |
| `/v1/export/cif` e `/v1/export/xyz` | C | `/api/v1/exports/cif` e `/api/v1/exports/xyz` | idem |
| `/api/bootstrap`, `/api/estrutura`, `/api/miller`, `/api/metais`, `/api/estruturas` | C (modo legado), A, D | removidas | O C deixa o modo legado na Fase 5. A e D não migram |
| `/api/liga`, `/api/termico`, `/api/tutoriais`, `/api/login` (A) | A | `/solid-solutions`, `/thermal`, `/files`, `/auth/*` | Reescritas; o `/api/login` da A **não** tem equivalente (ADR-008) |

**Regra de evolução:** dentro de `/api/v1` só entram mudanças **aditivas** (campos opcionais, rotas novas). Mudança incompatível exige `/api/v2` com período de coexistência.

**Teste de contrato obrigatório (CI):** as respostas reais de cada rota são validadas contra o OpenAPI e contra os schemas Zod do frontend. O ponto de partida é `_auditoria/contrato_b_c.mts`, que hoje dá 15/15.

## 4. Limites (padrão; configuráveis por ambiente)

| Recurso | Limite |
|---|---|
| Corpo JSON | 1 MiB |
| Upload | 2 GiB por arquivo (herdado da A); cota institucional configurável |
| Rate limit geral (prod) | 120 requisições/min por IP |
| `/auth/login`, `/auth/password/*` | 10/min por IP e 5 falhas por conta antes de atraso progressivo |
| Respostas de tentativa | 30/min por usuário |
| Supercélula | n ≤ 4 (pior caso CFC 4×4×4 = 5³ vértices + 3·(4·4·5) faces = 365 átomos) |
| Índices de Miller | \|índice\| ≤ 9 (B) |

## 5. Estado da implementação (Fase 10 — 35 rotas, API 0.9.0)

O catálogo do §2 é o **contrato-alvo**. Esta tabela registra o que está implementado e testado. O
esquema executável está em `docs/openapi.json` (gerado; o CI falha se estiver desatualizado).

| Grupo | Implementado | Pendente |
|---|---|---|
| Cristalografia | `GET metals, structures`; `POST cells, density, miller, supercells, solid-solutions` | — |
| Termodinâmica | `POST thermal` | `phase-diagram` (especificação A/docs/2) |
| Exportação | `POST exports/cif, exports/xyz` | — |
| HEA | `GET hea/bootstrap`; `POST hea/analyses` (ΔS_mix, curva −T·ΔS_mix, δ, T_m, VEC, composição nas bases atômica e mássica, critérios, triagem; ΔH_mix, Ω e ΔG_mix `null` com motivo). Ver §2.5.1 | `compositions/validate`, `compare`, `predictions/{id}` (o histórico já cobre); ΔH_mix/Ω dependem de Q-01 (matriz de entalpias por par) |
| Conta | `POST auth/register, auth/login, auth/logout, auth/logout-all`; `GET auth/me`, `me/history` | `verify-email`, `password/*` (dependem de SMTP, Q-04); `auth/sessions` |
| Educacional | `GET edu/generators, edu/questions, me/progress`; `POST edu/questions, edu/questions/{id}/instances, edu/instances/{id}/attempts` | atividades, atribuições a turmas, entregas e notas (tabelas prontas, sem rotas) |
| Organização acadêmica | — (instituições e vínculos são criados direto no banco) | `/institutions`, `/classes` |
| Materiais e arquivos | — | `/materials`, `/sources`, `/files` |
| Plataforma | `/health`, `/health/live`, `/health/ready`, `meta/capabilities`, `meta/version` | — |
| Aliases `/v1` | 7 rotas do B com `Deprecation` + `Link`; o front não usa mais | remover quando não houver clientes antigos |

Diferenças em relação ao §2: a análise HEA ficou em `POST /hea/analyses`, no lugar de `/hea/predictions`, porque
não há preditor de fase com dados completos. Os nomes do §2 continuam reservados para quando Q-01 for resolvida.

**Autenticação nas rotas de cálculo:** são públicas. Quando a requisição traz cookie de sessão, precisa trazer também
`X-Alloy-CSRF` (senão volta 403 `CSRF_INVALIDO`), e o cálculo entra no histórico pessoal.

Executar: `cd frontend && npm run engine -- --db ../var/dev.db` (API em 8010 com SQLite migrado) ou
`cd backend && python -m uvicorn app.main:create_app --factory --port 8000` (só o seed JSON, sem contas).
Documentação interativa (fora de produção): `/api/v1/docs`.
Contrato com o frontend: `backend/tests/contract/test_contrato_frontend.py` (38/38 respostas reais validadas pelos esquemas zod).
