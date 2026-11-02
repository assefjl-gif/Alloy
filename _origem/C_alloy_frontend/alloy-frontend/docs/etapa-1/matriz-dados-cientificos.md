# Matriz de dados científicos (1.4)

Regra que esta matriz sustenta: **nenhum valor científico é calculado no front-end**. Cada número exibido tem origem no motor; o front apenas formata (casas decimais, separador do idioma) e converte unidades quando indicado.

Motor de referência: `legacy/crystalab_modulo1.py` (v1.0). Rotas legadas `/api/*`; as rotas `/v1/*` da versão FastAPI devolvem os mesmos campos dentro de `result`.

## CrystaLab — célula unitária (`POST /api/estrutura` · `calcular_estrutura`)

| Grandeza exibida | Campo | Unidade | Precisão recebida | Exibição | Passos intermediários do motor? |
|---|---|---|---|---|---|
| Estrutura (sigla e nome) | `estrutura`, `estrutura_nome` | — | texto | texto | — |
| Rótulo do material | `rotulo`, `simbolo`, `nome_metal`, `editado`, `generica` | — | texto/booleano | texto | — |
| Parâmetro de rede a | `a_nm` | nm | float64 | 4 casas | Sim: `passos_densidade[1]` (texto formatado pt-BR) |
| a em unidades de R | `a_em_R`, `relacao_a` | adimensional | float64 / texto | 3 casas | Não (relação textual) |
| Parâmetro c (HC) | `c_nm` | nm | float64 | 4 casas | Sim: `passos_densidade[1]` |
| Razão c/a (HC) | `c_a` | adimensional | float64 | 3 casas | Não |
| Fator de empacotamento | `fea` | adimensional | float64 | 3 casas | **Não** (pendência D-12) |
| Fração de vazios | `vazios` | adimensional | float64 | % com 1 casa (×100 é formatação) | Não |
| Densidade teórica | `densidade` | g/cm³ | float64 | 3 casas | Sim: `passos_densidade[0..3]` |
| Densidade experimental | `densidade_exp` | g/cm³ | 2 casas (tabela) | 2 casas | — (dado de referência) |
| Desvio teórico × experimental | `erro_percent` | % | float64 | 2 casas | Sim: `passos_densidade[4]` |
| Átomos por célula | `n` | átomos/célula | inteiro | inteiro | Sim: `contagem[]` |
| Número de coordenação | `nc` | vizinhos | inteiro | inteiro | Não |
| Volume da célula | `volume_nm3`, `volume_cm3` | nm³, cm³ | float64 | notação científica | Sim: `passos_densidade[2]` |
| Raio relativo R/a | `raio_relativo` | adimensional | float64 | usado no desenho das esferas | Não |
| Posições atômicas | `atomos[].pos` | unidades de a (cartesianas; nas cúbicas = fracionárias) | 6 casas | 3 casas | — |
| Tipo e fração de cada sítio | `atomos[].tipo`, `fracao`, `fracao_txt` | — | float/texto | texto | — |
| Arestas da célula | `arestas` | unidades de a | 6 casas | desenho | — |
| Contagem por posição | `contagem[]` (`quantidade`, `fracao_txt`, `contribuicao`) | átomos | float | texto | É o próprio passo |
| Interpretação didática | `interpretacao[]` | — | texto pt-BR | texto | — |
| Passo a passo da densidade | `passos_densidade[]` (`titulo`, `formula`, `detalhe`) | — | texto pt-BR já formatado | exibido literalmente + fórmula simbólica em KaTeX | — |

Campos aditivos previstos na v1.1.0 (changelog) e já aceitos pelos contratos TypeScript como opcionais: `base` (sítios únicos com coordenadas fracionárias), `z`, `grupo_espacial`, `a_fonte`, `avisos`, `fonte`.

## CrystaLab — índices de Miller (`POST /api/miller` · `calcular_miller`)

| Grandeza | Campo | Unidade | Exibição | Observação |
|---|---|---|---|---|
| Notação (hkl)/(hkil), [uvw]/[uvtw] | `notacao`, `notacao_alternativa` | — | texto com barra combinante | — |
| Polígono do plano | `poligono`, `centro`, `normal` | unidades de a | desenho | — |
| Área do plano na célula | `area_rel`, `area_nm2` | a², nm² | 3–4 casas | `area_nm2` só com `a_nm` |
| Distância interplanar | `d_rel`, `d_nm` | a, nm | 3–4 casas | CR-05 (d de rede × d atômico) pendente no motor |
| Átomos no plano/direção | `atomos[]` | índices em `atomos` da célula | destaque | — |
| Vetor da direção | `inicio`, `fim` | unidades de a | seta | — |
| Comprimento | `comprimento_rel`, `comprimento_nm` | a, nm | 3–4 casas | — |
| Átomos contados / densidade linear | `atomos_contados`, `densidade_linear_rel`, `densidade_linear_nm` | átomos, át/a, át/nm | 2–3 casas | `null` quando o vetor não termina em ponto de rede (CR-04) |
| Ordem e índices reduzidos | `ordem`, `indices_reduzidos`, `avisos` | — | texto | só v1.1.0 (opcionais) |

## CrystaLab — tabelas e exportação

| Dado | Rota | Unidade |
|---|---|---|
| Tabela de estruturas (`sigla`, `nome`, `n`, `nc`, `a_em_R`, `relacao`, `fea`) | `GET /api/estruturas` · `/v1/crystals/structures` | — |
| Metais (`nome`, `estrutura`, `raio`, `peso`, `densidade_exp`, `c_a`, `nc`) | `GET /api/metais` · `/v1/crystals/metals` | nm, g/mol, g/cm³ |
| CIF / XYZ (`filename`, `content`, `content_type`) | `POST /v1/export/cif|xyz` | arquivo texto (v1.0: comprimentos em nm no CIF, EX-01) |

## HEA Virtual Lab (`POST /api/analyze` · `hea_engine.analisar_liga`) — motor ausente

Campos lidos do código da UI v1.17 (o motor não está no projeto, então unidades e precisões vêm dos rótulos da UI):

| Grandeza | Campo | Unidade (rótulo da UI) |
|---|---|---|
| Veredito, fase, ductilidade, dureza | `veredito`, `fase`, `ductilidade`, `dureza`, `dureza_indice` | texto; índice 0–100 |
| Entropia de mistura | `dS` | J/mol·K |
| Entalpia de mistura | `dH` | kJ/mol |
| Distorção atômica | `delta` | % |
| Parâmetro Ω | `omega` | adimensional |
| VEC | `VEC` | elétrons |
| Temperatura de fusão média | `Tm` | K |
| Composição normalizada | `comp_percent` | % atômica |
| Curva de energia livre | `gibbs[] {T, G}` | K, J/mol |
| Interpretação | `interpretacao[]`, `fragilidade` | texto |
| Referência (Cantor) | `reference {dS, omega, delta, VEC, dH, T_padrao, P_padrao}` | idem |
| Estrutura sugerida | — | **não existe campo próprio**; ver regra de correspondência (Etapa 5) |

## O que o front faz com os números

- Formata (`Intl.NumberFormat` do idioma ativo) e escolhe casas decimais.
- Converte unidade **somente** por fator exato e rotulado (ex.: posição em unidades de a × `a_nm` → nm no painel do átomo; fração × 100 → %).
- Desenha réplicas de supercélula por translação da célula do motor (elemento gráfico; nunca entra em contagens).
- Mede distâncias e ângulos entre posições do motor na ferramenta de medição do viewer (geometria de visualização, rotulada como tal).
- Compara a resposta do estudante com o valor do motor nos exercícios (tolerância declarada).
