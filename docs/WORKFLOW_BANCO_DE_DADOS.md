# Workflow de desenvolvimento — profissionalização do banco de dados e tabela periódica completa

| Item | Valor |
|---|---|
| Data | 03–09/11/2026 |
| Decisão | [ADR-018](DECISOES_TECNICAS.md#adr-018) |
| Versão dos dados | `2026.11.3-tp` (novo conjunto `tabela_periodica`); demais conjuntos inalterados |
| Migração | `0003_tabela_periodica_completa` (reversível) |
| Estado | Implementado e testado localmente; **não publicado no GitHub** (aguarda revisão do supervisor) |

## 1. Objetivo

Levar o banco de 18 elementos (15 metais + C, N, H, só com as propriedades que os motores usam) a uma tabela
periódica completa e profissional: 118 elementos, cada valor com fonte citável, unidade, incerteza quando
publicada, estado de validação e versão, sem alterar nenhum resultado dos motores já aprovados.

## 2. Etapas e responsáveis (Agentes 01–07)

| # | Etapa | Responsável | Revisor | Saída verificável |
|---|---|---|---|---|
| 1 | Levantamento do banco atual e lacunas | Agente 02 (Banco) | Agente 05 | Inventário: 18 elementos, sem período/grupo/bloco, sem incerteza, fontes sem data de acesso |
| 2 | Pesquisa bibliográfica e escolha das fontes | Agente 02 | Agente 05 | CIAAW (pesos padrão), PubChem (propriedades atômicas, agrega NIST/LANL/Jefferson Lab/IAEA), Wikipédia pt (nomes). [`FONTES.txt`](../database/seeds/tabela_periodica/FONTES.txt) |
| 3 | Modelagem e migração 0003 | Agente 02 | Agente 06 | `elementos` com `CHECK`, `propriedades_elemento`, `fontes.acessado_em`; `alembic check` limpo; upgrade/downgrade testados sobre dados existentes |
| 4 | Importação reprodutível dos 118 elementos | Agente 04 (Automação) | Agente 02 | `scripts/importar_tabela_periodica.py` (cache, `--offline`, `sha256` das fontes brutas, conferência cruzada) |
| 5 | Repositório, serviço e API `/api/v1/elements` | Agente 01 (API) | Agente 06 | JSON e SQL com saída idêntica campo a campo; filtros; busca por símbolo ou Z; procedência e aviso de validação |
| 6 | Integração com o restante do sistema | Agente 06 (Integração) | Agente 05 | Motores intactos; OpenAPI documenta as rotas; seed idempotente e com controle de versão |
| 7 | Testes, segurança e auditoria de latência | Agente 07 (Tester/Pentester) | Agente 05 | 86 testes novos (injeção SQL, path traversal, restrições do banco, backup); [`AUDITORIA_LATENCIA_BANCO.txt`](AUDITORIA_LATENCIA_BANCO.txt) |
| 8 | Apresentação dos dados ao usuário | Agente 03 (UX/UI) | Agente 05 | Contrato pronto para o módulo de tabela periódica no frontend (próxima etapa, não implementada) |
| 9 | Gate | Agente 05 (Supervisor) | — | Revisão deste pacote antes de publicar no GitHub |

## 3. Caminhos avaliados e escolhidos

| Questão | Escolha | Alternativa descartada e por quê |
|---|---|---|
| Onde guardar as propriedades atômicas | Tabela própria `propriedades_elemento` | Reusar `valores_propriedade`: exigiria criar 118 "materiais" e mudaria a entrada dos motores |
| Peso atômico | Só CIAAW, valor abreviado ± incerteza + intervalo | Massa do PubChem para todos: mistura peso padrão com massa isotópica |
| Elementos sem peso padrão (Tc, Pm, Po…Og) | `massa_isotopica_referencia` com nota | Inventar peso padrão: não existe na CIAAW |
| Convenção de grupos | IUPAC 18 colunas, bloco f sem grupo | La/Ac no grupo 3: controverso, a IUPAC não fixa |
| Divergências com o seed antigo | Registradas e testadas, à espera do validador (Q-03) | Corrigir em silêncio: quebraria rastreabilidade (ADR-014) |
| Estado inicial | `importado` / `aguardando_validacao` | `validado`: nenhuma revisão humana registrada |
| Latência | Cache de retrato por versão + invalidação por commit + TTL | Redis: proibido sem evidência (ADR-012); materialized view: só PostgreSQL |

## 4. Diferenças em relação à versão anterior

| Aspecto | Antes (v0.9 / dados v1.4) | Agora |
|---|---|---|
| Elementos | 18 | **118** |
| Classificação | só símbolo, nome e Z | + nome em inglês, período, grupo, bloco, categoria, configuração eletrônica, estados de oxidação, estado padrão, descoberta |
| Propriedades atômicas | as dos motores (Callister) | + 763 valores de 9 propriedades com fonte, unidade, incerteza e intervalo |
| Integridade no banco | PK/FK | + 7 `CHECK` em `elementos`, 4 em `propriedades_elemento`, índice único parcial de vigência, fonte obrigatória |
| Fontes | citação | + DOI, URL, licença, versão da fonte, data de acesso, `sha256` do arquivo bruto |
| API | sem rota de elementos | `GET /api/v1/elements` (filtros) e `GET /api/v1/elements/{símbolo ou Z}` |
| Backup | documentado | comando `app.cli backup` com verificação de integridade e restauração testada |
| Latência (SQLite, p50) | 22–26 ms cálculos; ~50 ms elementos; 5–6 SQL/req | 12–15 ms; ~13–16 ms; 1 SQL/req |
| DDL PostgreSQL | 0001 | + `schemas/0003_tabela_periodica.postgresql.sql` |
| Testes do backend | 397 aprovados | 401+ aprovados (inclui 86 novos de tabela periódica e cache) |

## 5. Pendências

1. Validação humana dos 763 valores (Q-03), começando pelas divergências registradas em `FONTES.txt` §4.
2. Repetir a auditoria de latência em PostgreSQL (staging).
3. Módulo visual de tabela periódica no frontend (Agente 03).
4. Publicar no GitHub depois do gate do supervisor.
