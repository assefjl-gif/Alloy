# Histórico de alterações

| Data | Commit | Fase | Alteração |
|---|---|---|---|
| 02/11/2026 | `2a6f79a` | 0 | Estado inicial das bases A, B, C e D (intactas em `_origem/`) |
| 02/11/2026 | `7e82fcf` | 1 | Requisitos-base e auditoria geral; scripts de comparação e contrato |
| 02/11/2026 | `114e718` | 2 | Arquitetura final, ADR-001..017, modelo de dados, contratos da API, esqueleto do monorepo |
| 02/11/2026 | `1989992` | 3 | Motor científico único com recursos da v1.4 e testes de referência |
| 02/11/2026 | `6ed0af0` | 3 | Modelos, migrações, repositório SQL, carga de seed, serviço de cálculo, configuração por ambiente, documentação |
| 02/11/2026 | `bd80d6f` | 4 | API /api/v1, aliases /v1, contrato 34/34 com o frontend, OpenAPI |
| 02/11/2026 | `a4c330d` | 5 | Frontend migrado para `/api/v1` (apiBase único), legado e vendor removidos, tipos do OpenAPI, portabilidade Windows (BUG-01/02) |
| 02/11/2026 | `d75db0a` | 6 | Motor HEA analítico (ΔS_mix, δ, T_m, VEC, fase; ΔH_mix/Ω indisponíveis), seed VEC, rotas HEA, front com grandezas anuláveis |
| 02/11/2026 | `f437ac8` | 8a | Contas: Argon2id, sessão opaca em cookie, CSRF, bloqueio progressivo, RBAC com escopo, histórico pessoal, CLI de banco, módulo `#/conta` |
| 02/11/2026 | `0ad16bd` | 7 | Questões parametrizadas com gabarito do motor e correção no servidor, tentativas, progresso |
| 02/11/2026 | `92b5aad` | 8b | Dockerfiles, Caddyfile, docker-compose, `.env.example`, CI Linux+Windows |
| 02/11/2026 | (este) | 9–10 | Regressão completa e E2E; documentação do §16; relatório de encerramento; API 0.9.0 |
| 03/11/2026 | (este) | T-13 | Abas Liga e Temperatura no CrystaLab: átomos da liga e vibração no viewer, regras de Hume-Rothery, curva de Lindemann; contrato real 46/46 |
| 10/11/2026 | (este) | Reforma visual | Identidade "Carvão, Areia e Azul" (#1E1E1C, #D8CBB3, #2F6BFF): tokens, tipografia IBM Plex servida pelo site, componentes, faixas de título e todas as páginas; sem mudança de função, cálculo ou API. Registro em `REFORMA_VISUAL.md` |

| 13/11/2026 | (nao commitado) | Rodada R1 | **Evolucao cientifica do CrystaLab e do HEA** (pedido de 12/11/2026). Motor HEA 2.0.0: validacao de simbolo contra os 118, erros com `details`, motivo para todo campo nulo, composicao em base atomica e massica, curva analitica -T&middot;dS_mix, `criterios` com fonte e `verificada: false`, triagem sem a palavra ESTAVEL, dominio de aplicabilidade do VEC, dH_mix e Omega condicionais (Q-01 continua aberta). Motor de cristalografia 2.1.0: FEA do HC corrigido para esferas nao interpenetradas (V-15), supercelula periodica como unidade de amostragem (L-1/L-5), realizacao estatistica com semente e composicao representada, ligas multicomponentes (ate 6 solutos, substitucionais e intersticiais), sitios octaedricos e tetraedricos, campos por atomo, avisos de solubilidade e fases. Frontend: palco 3D em area total com barra lateral unica de seis secoes, HUD de cena e camera com deslocar/centralizar/restaurar. Relatorios em `docs/agent_reports/` e `docs/research/`; contrato em `docs/architecture/2026-11-12_contrato_R1.md` |
| 15/11/2026 | (nao commitado) | Rodada R2 | **Interface 3D, rotulagem honesta e robustez.** Frontend: selecao e inspecao de atomo na cena de LIGAS com os campos do motor (id, cartesianas em a e nm, fracionarias, fase, sitio, ocupacao, imagem periodica) e bloco separado de propriedade do elemento puro; filtros e isolamento por elemento, ocupacao e sitio, e corte por plano de eixo com tres modos, aplicados como visibilidade (a selecao continua funcionando no interior da celula); menu de aparencia (cor por elemento, grupo e atomo, cor de vertices e arestas, tamanho, transparencia, restaurar padrao) com marcadores geometricos distinguiveis de atomos reais por acabamento; selo de demonstracao em todo valor, grafico e tabela vindos do modo demonstrativo, distinto do selo Ilustrativo (decisao Q-14 do usuario: manter com selo); selo na animacao alfa-gama; `demo_permitido` do servidor respeitado (indisponivel vira desabilitado, nunca demonstrativo); aviso acionavel quando a amostragem nao cabe nenhum atomo de soluto. Backend: motor termico 2.0.0 (parametro de rede nulo acima da fusao com motivo, alotropia so com procedencia e politica de dados, T_f nominal nao confundida com solidus/liquidus, isotropia declarada, dominio da curva de vibracao); FEA do HC protegido tambem para c/a abaixo de 2/3; procedencia preenchida em `/cells` e `/density`; mensagens de erro em portugues sem vazar detalhe interno; indice de lista em `details[].loc`; gravacao de historico isolada em savepoint (falha nao derruba mais o calculo), registro idempotente do motor e `PRAGMA foreign_keys` imposto em SQLite. Relatorios em `docs/agent_reports/`; decisoes em `docs/architecture/2026-11-14_decisoes_R2.md` |
Substituições relevantes (o que saiu e o que entrou no lugar):

| Removido | Substituído por | Por quê |
|---|---|---|
| `legacy/crystalab_modulo1.py` e `engine-stub/` no front | backend FastAPI real (`scripts/backend.mjs`) | um só motor (ADR-001/002) |
| `vendor/` e `scripts/link-deps.mjs` | npm com `package-lock.json` | o registro npm está acessível (ADR-010) |
| rotas `/v1/*` no front | `/api/v1/*` canônicas | API.md §3 |
| HEA demonstrativo como única opção | motor analítico com indisponíveis explícitos | PI-02; Q-01 aberta |
| login por e-mail da v1.4 (A) | contas com senha Argon2id e sessão revogável | ADR-008 |
