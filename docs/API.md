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
| POST | `/api/v1/crystallography/solid-solutions` | publico* | `SolidSolutionRequest {base, soluto, x, n, arranjo, distorcer, semente}` → resultado da liga + regras de Hume-Rothery | A (`/api/liga`) |
| POST | `/api/v1/thermodynamics/thermal` | publico* | `{material_id, temperatura_c}` → a(T), ρ(T), Lindemann, notas de alotropia | A (`/api/termico`) |
| POST | `/api/v1/thermodynamics/phase-diagram` | publico* | Especificação A/docs/2 §7 | novo (Fase 6) |

\* Público com rate limit. Com sessão, o cálculo também é gravado em `execucoes_calculo` (histórico pessoal).

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
| HEA | `GET hea/bootstrap`; `POST hea/analyses` (ΔS_mix, δ, T_m, VEC, fase; ΔH_mix e Ω `null` com motivo) | `compositions/validate`, `compare`, `predictions/{id}` (o histórico já cobre); ΔH_mix/Ω dependem de Q-01 |
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
