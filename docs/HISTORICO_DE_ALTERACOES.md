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

Substituições relevantes (o que saiu e o que entrou no lugar):

| Removido | Substituído por | Por quê |
|---|---|---|
| `legacy/crystalab_modulo1.py` e `engine-stub/` no front | backend FastAPI real (`scripts/backend.mjs`) | um só motor (ADR-001/002) |
| `vendor/` e `scripts/link-deps.mjs` | npm com `package-lock.json` | o registro npm está acessível (ADR-010) |
| rotas `/v1/*` no front | `/api/v1/*` canônicas | API.md §3 |
| HEA demonstrativo como única opção | motor analítico com indisponíveis explícitos | PI-02; Q-01 aberta |
| login por e-mail da v1.4 (A) | contas com senha Argon2id e sessão revogável | ADR-008 |
