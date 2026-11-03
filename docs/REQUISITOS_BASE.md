# Requisitos-base do Alloy Virtual Lab

Documento normativo derivado do **Prompt Mestre — Auditoria, Engenharia Reversa, Integração e Consolidação** (`prompt matriz de concatenação.txt`). Ele é a referência de requisitos para todas as fases seguintes do projeto.

| Item | Valor |
|---|---|
| Versão | 1.0 (Fase 1 — auditoria) |
| Data | 02/11/2026 |
| Fonte primária | Prompt Mestre, seções 1–20 (citadas como §n) |
| Papéis e protocolo | Agentes 01–07 (`AGENTE_0X_*.txt`) |
| Autoridade de aprovação | Agente 05 — Supervisor-Chefe (gates 0–6) |
| Evidências da auditoria | [`RELATORIO_AUDITORIA_GERAL.md`](RELATORIO_AUDITORIA_GERAL.md) e `_auditoria/` |

## 0. Hierarquia e regras de uso

1. **O Prompt Mestre define o QUE** a plataforma precisa ter. Cada requisito abaixo tem um ID estável (`RQ-<DOMÍNIO>-nn`) e cita a seção de origem.
2. **Os Agentes 01–07 definem QUEM e COMO.** Cada requisito tem um agente responsável, e o Agente 05 decide o gate.
3. **Conflitos.** Se um requisito colidir com uma regra inegociável de algum agente (ex.: "não inventar dados científicos"), a regra de integridade prevalece. O conflito é registrado na seção 8 e decidido por um humano.
4. **Retrabalho isolado** (Agente 05 §7). Uma reprovação refaz só a unidade reprovada. Módulos aprovados ficam protegidos.
5. **Rastreabilidade.** Todo requisito precisa terminar ligado a componente → teste → evidência. A coluna "Cobertura atual" registra o ponto de partida medido na auditoria. Não é aprovação.

Legenda da cobertura atual (o que já existe nas bases de origem):
**A** = CrystaLab v1.4 (arquivo único) · **B** = CrystaLab v1.1.0 (FastAPI modular) · **C** = alloy-frontend (React/TS) · **D** = crystalab_modulo1.py (v1.0, idêntico a `C/legacy`)
`✔` existe e foi verificado nesta auditoria · `◐` parcial ou só demonstrativo · `✘` inexistente

## 1. Princípios invioláveis

Valem para todas as fases. Violar qualquer um é falha **P0**.

| ID | Princípio | Origem |
|---|---|---|
| PI-01 | Nenhum dado falso apresentado como real; demonstrações sempre rotuladas e isoladas de dados acadêmicos | §4.3, §12.3, §11.3 |
| PI-02 | Nenhum modelo, parâmetro ou resultado científico inventado; sem fonte confiável → infraestrutura + rótulo "experimental" | §6.3, §6.2 |
| PI-03 | Um único núcleo científico; nenhuma fórmula duplicada no frontend ou em outro módulo | §5.2, §6.1 |
| PI-04 | Permissões verificadas no backend; ocultar botão não é segurança | §9 |
| PI-05 | Um aluno não altera silenciosamente dado científico validado | §7.2 |
| PI-06 | Cada resultado científico guarda parâmetros, motor, versão, data e procedência | §7.1, §6.3 |
| PI-07 | Classificação explícita: analítico, estimativa de modelo, experimental, simulação ilustrativa ou demonstrativo | §6.3 |
| PI-08 | Testes nunca forçados a passar; testes falhos nunca escondidos | §12.3, §13.5 |
| PI-09 | Preservar originais: backup, branch, commits organizados; nada de destruir funcionalidade sem análise de dependência | §12.4 |
| PI-10 | A IA generativa nunca substitui cálculo nem inventa resultado experimental | §11.2 |
| PI-11 | Sem credenciais de produção em testes; sem migração destrutiva automática | §14 |

## 2. Papéis: Prompt Mestre ↔ Agentes

| Papel do Prompt (§1) | Agente responsável | Revisor obrigatório |
|---|---|---|
| Arquiteto de Software | 05 Supervisor-Chefe (decisão) + 06 Integração (execução) | 05 |
| Engenheiro Full-Stack | 06 Integração | 05, 07 |
| Engenheiro Python / motores | 01 API (contratos) + especialista de materiais (ver §8, Q-03) | 05, 07 |
| Engenheiro Frontend | 03 Designer UX/UI + 06 Integração | 05, 07 |
| UI/UX e Design System | 03 Designer | 05, 07 |
| Engenheiro de Dados | 02 Banco de Dados | 05 |
| ML/IA | 04 Automação (orquestração) + 01 API (contrato) | 05 |
| Ciência dos Materiais | Sem agente dedicado. Validação humana obrigatória (Q-03); o 07 confronta com a literatura | 05 |
| QA | 07 Tester/Pentester | 05 |
| DevOps e Segurança | 06 (ambiente) + 07 (pentest autorizado) + 01 (segurança da API) | 05 |

## 3. Requisitos funcionais e técnicos

### 3.1 Arquitetura (ARQ) — §5

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-ARQ-01 | Monorepo `frontend/` + `backend/` + `database/` + `infrastructure/` + `docs/` + `scripts/` | Estrutura criada; cada pasta com README; build de cada parte executável isoladamente | 06 | 2 | ◐ esqueleto e READMEs criados na Fase 2; builds a partir da Fase 3 |
| RQ-ARQ-02 | Camadas do backend: api, schemas, services, engines, repositories, models, security, educational, integrations | Imports respeitam a direção das camadas (teste de arquitetura) | 01 | 2–3 | ✔ Fase 3: camadas core/engines/models/repositories/services; regras testadas (`test_arquitetura.py`) |
| RQ-ARQ-03 | Motor científico independente de API e UI | `engines/` importável e testável sem FastAPI | 01 | 3 | ✔ Fase 3: `engines/` sem I/O nem FastAPI; teste com violação injetada |
| RQ-ARQ-04 | Frontend em módulos com fronteiras: app, hea, crystalab, didactics, instructor, notebook, assessments, administration, compartilhados | Lint de fronteiras sem violação | 03/06 | 5 | ◐ C (sem assessments/administration) |
| RQ-ARQ-05 | Nenhum cálculo científico em componentes React | Busca automática por fórmulas no `frontend/src` limpa; valores vêm da API | 06 | 5 | ◐ C (a confirmar na Fase 5) |

### 3.2 Motor CrystaLab (CIE) — §6.1, §6.2

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-CIE-01 | Estruturas CS, CCC, CFC, HC com n, NC, FEA, vazios | Testes de referência por estrutura (FEA 0,524/0,680/0,740/0,740 ideal) | 01 | 3 | ✔ A, B, D |
| RQ-CIE-02 | Parâmetro de rede: modelo de contato + medido com prioridade e procedência | Ti: ρ dentro de ±1% do experimental; fonte do *a* registrada | 01/02 | 3 | ✔ Fase 3: rede medida prioritária + *a* informado (`a_fonte`); Ti −0,2 %; *a* medido só para Ti até Q-03 |
| RQ-CIE-03 | Densidade teórica com N_A CODATA 2018 e comparação experimental com aviso de desvio | N_A = 6,02214076e23; aviso acima de 3% | 01 | 3 | ✔ Fase 3: N_A CODATA única (teste de unicidade); aviso de desvio > 3 % |
| RQ-CIE-04 | Miller (hkl) e Miller-Bravais (hkil), planos e direções, distância interplanar, densidade linear | Mesmos resultados em A/B/D para 10 casos (já verificado) + casos de literatura | 01 | 3 | ✔ A, B, D (geometria idêntica) |
| RQ-CIE-05 | Densidade e fração planar **só se validadas** | Casos CFC(111)=0,907, CCC(110)=0,833, CFC(100)=0,785 e basal HC confirmados por fonte; HC piramidal validado ou ocultado | 01 + especialista | 3 | ✔ Fase 3: publicada só para famílias validadas (Callister §3.11); demais ocultas com motivo |
| RQ-CIE-06 | Conversões nm/Å/cm e cartesiano↔fracionário centralizadas | Constantes únicas; testes de ida e volta | 01 | 3 | ✔ B (`constantes.py`, `geometria.py`) |
| RQ-CIE-07 | Grupo espacial e Wyckoff por estrutura | Pm-3m 221, Im-3m 229, Fm-3m 225, P6₃/mmc 194 | 01 | 3 | ✔ B |
| RQ-CIE-08 | Supercélulas e famílias de planos | Contagem de átomos por n×n×n; planos paralelos dentro da caixa | 01 | 3 | ✔ Fase 3: supercélula e famílias no motor (contagens por força bruta); consumo pelo viewer na Fase 5 |
| RQ-CIE-09 | Exportação CIF e XYZ | CIF validado com Gemmi (§13.3) | 01 | 3 | ✔ B (CIF/XYZ) · ◐ A (XYZ no cliente) |
| RQ-CIE-10 | Passo a passo de *a*, FEA e densidade | Passos com valores intermediários reais (fecha D-12 do C) | 01 | 3 | ✔ Fase 3: passos de *a*, FEA e densidade |
| RQ-CIE-11 | Ligas: Vegard, Hume-Rothery, % at↔% peso, intersticiais, ordenação, distorção ilustrativa | Cu–Ni conforme Callister; distorção rotulada como ilustrativa | 01 + especialista | 3/6 | ◐ Fase 3: motor pronto; χ e valência em rascunho (bloqueados em prod até Q-03) |
| RQ-CIE-12 | Temperatura: dilatação, vibração (Lindemann), alotropia | α e Tf com fonte por metal; modelo rotulado como aproximação | 01 + especialista | 3/6 | ◐ Fase 3: motor pronto; α, T_f e alotropia em rascunho (bloqueados em prod até Q-03) |
| RQ-CIE-13 | Resultados idênticos em qualquer módulo que os consuma | Teste de contrato garante uma só implementação por fórmula | 06 | 6 | ✔ Fase 3: núcleo único; regressão A/B/D com divergências explicadas; banco = JSON campo a campo |

### 3.3 Motor HEA — §6.3

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-HEA-01 | ΔS_mix, ΔH_mix, Ω, δ, VEC, T_m média com equações citadas | Cada grandeza com equação, referência (DOI) e teste numérico de literatura | 01 + especialista | 3/6 | ✘ (C é 100% demonstrativo, D-01) |
| RQ-HEA-02 | Critérios de estabilidade e previsão de fase rotulados como estimativa de modelo | Limiares com fonte; saída traz `classe = estimativa_modelo` | 01 | 6 | ✘ |
| RQ-HEA-03 | Dados de ΔH de pares (ex.: Takeuchi–Inoue) com procedência e licença | Tabela versionada com fonte; ausência de par → erro explícito, nunca zero silencioso | 02 | 3 | ✘ |
| RQ-HEA-04 | Infraestrutura e contratos mesmo sem modelo validado | Endpoints prontos; sem motor → estado "indisponível", nunca valor fictício | 01 | 4 | ◐ C (adaptador + demo rotulado) |
| RQ-HEA-05 | Histórico de predições e comparação entre ligas | Predição persistida com versão do modelo | 02 | 3 | ✘ |
| RQ-HEA-06 | Curva de Gibbs só com ΔG = ΔH − TΔS real | Remover a curva aleatória do demo em produção | 01/03 | 6 | ✘ (curva do C é passeio aleatório) |

### 3.4 Banco de dados e persistência (DAD) — §7

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-DAD-01 | PostgreSQL como fonte única de verdade; SQLAlchemy 2.x + Alembic | `alembic upgrade head` em banco vazio e downgrade testado | 02 | 3 | ◐ Fase 3: SQLAlchemy 2 + Alembic (2 migrações, upgrade/downgrade/check ok no SQLite, DDL Postgres gerado); falta executar em PostgreSQL (L-01) |
| RQ-DAD-02 | Entidades mínimas do §7.1 (usuários, instituições, turmas, materiais, ligas, propriedades, cálculos, educacional, professor) | Diagrama ER + dicionário de dados aprovados | 02 | 2 | ✔ Fase 3: 36 tabelas mapeadas (desvios em BACKEND.md) |
| RQ-DAD-03 | PK, FK, constraints, índices justificados por consulta, transações | Testes de integridade e de violação de FK | 02 | 3 | ◐ Fase 3: PK/FK/CHECK/índices parciais testados no SQLite com FK ligada; validar no PostgreSQL |
| RQ-DAD-04 | Versionamento e histórico de dados científicos | Alterar dado validado cria nova versão; antiga preservada | 02 | 3 | ✔ Fase 3: append-only com `substitui_id`/`vigente` (teste) + `versoes_dados` |
| RQ-DAD-05 | Repositório científico aberto com estados rascunho → aguardando validação → validado / rejeitado / arquivado | Máquina de estados testada; aluno não promove a "validado" | 02/04 | 3/7 | ✘ |
| RQ-DAD-06 | Unidade, procedência e licença por valor científico | Coluna/metadado obrigatório; inserção sem fonte rejeitada | 02 | 3 | ✔ Fase 3: unidade, classe, estado e fonte por valor; CHECK `validado` exige fonte (teste) |
| RQ-DAD-07 | Backup e restauração testados | Restore em ambiente de teste documentado | 02 | 8 | ✘ |
| RQ-DAD-08 | Persistência confirmada após reinicialização | Teste E2E reinicia o serviço e relê | 06/07 | 9 | ✘ |

### 3.5 API (API) — §8

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-API-01 | REST versionada `/api/v1/...` por domínio (§8.2) | Rotas do §8.2 mapeadas ou justificadas | 01 | 4 | ✔ Fase 4: `/api/v1` por domínio + aliases `/v1` depreciados |
| RQ-API-02 | Schemas Pydantic de entrada/saída; envelope e erros padronizados | Schemas para 100% das rotas; erros com `code` | 01 | 4 | ✔ Fase 4: Pydantic em todas as rotas; envelope com `code` e `request_id` |
| RQ-API-03 | OpenAPI funcional e **tipos TS gerados ou validados a partir dele** | Pipeline gera tipos; divergência quebra o CI | 01/06 | 4 | ◐ Fase 4: OpenAPI exportado; contrato real 34/34 com o Zod do frontend; tipos TS na Fase 5 |
| RQ-API-04 | Correlation ID, paginação, filtros, ordenação, rate limit, controle de acesso | Cabeçalho `X-Request-ID` propagado; coleções paginadas | 01 | 4 | ◐ Fase 4: request ID e rate limit; paginação entra com as coleções (Fases 7/8) |
| RQ-API-05 | Cliente HTTP central no frontend com cancelamento, timeout, interceptação de erro e auth | Lint R1 do C (fetch só em `http.ts`) mantido | 06 | 5 | ✔ C (`http.ts`, `latest.ts`) |
| RQ-API-06 | Cálculos longos fora da requisição HTTP | Jobs com estado/progresso quando a medição justificar (§15) | 04 | 9 | ✘ (desnecessário até agora; medir antes) |

### 3.6 Autenticação, permissões e segurança (SEG) — §9

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-SEG-01 | Cadastro, login, logout, recuperação de senha, verificação de e-mail | Fluxos E2E; senha com hash Argon2id ou bcrypt | 01 | 8 | ✘ (A: só identificação por e-mail — **não reproduzir**, §9) |
| RQ-SEG-02 | Sessão segura (cookie HttpOnly+Secure+SameSite ou token com rotação) | Teste de expiração, logout em outra aba, reuso de token | 01 | 8 | ✘ (B: `current_user` sempre anônimo) |
| RQ-SEG-03 | RBAC: admin geral, admin institucional, professor, estudante, pesquisador | Matriz papel × rota testada no backend | 01/02 | 8 | ✘ |
| RQ-SEG-04 | Isolamento por instituição e por turma | Teste de acesso cruzado (IDOR) negado | 02/07 | 8 | ✘ |
| RQ-SEG-05 | Proteção contra SQLi, XSS, CSRF, escalada, abuso, upload malicioso | Pentest autorizado do 07 sem achado P0/P1 aberto | 07 | 8–9 | ◐ B (CSP, limites de corpo, cabeçalhos) · ◐ A (anti-CSRF por cabeçalho, upload em lista branca) |
| RQ-SEG-06 | Segredos por variáveis de ambiente; logs sem dados sensíveis | `.env.example` sem segredos; varredura de logs | 06 | 8 | ◐ B (`.env.example`) |
| RQ-SEG-07 | LGPD para dados de estudantes: finalidade, retenção, exportar e apagar | Endpoints de exportação/exclusão; texto de consentimento revisado | 02 | 7–8 | ✘ (especificado em `_origem/A/docs/1_*.txt`) |

### 3.7 Frontend, design system e acessibilidade (FE) — §10

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-FE-01 | React + TypeScript estrito + Zustand + Three.js + KaTeX + Zod mantidos (troca só com justificativa) | `tsc --noEmit` sem erro | 03 | 5 | ✔ C (typecheck 0 erros, verificado) |
| RQ-FE-02 | Design system central (tokens, componentes, estados) | Catálogo cobre todos os componentes usados | 03 | 5 | ✔ C (alloy-ui + `#/catalogo`) |
| RQ-FE-03 | Viewer 3D fiel aos dados do motor: instancing, seleção, planos, supercélulas, medições, liberação de WebGL | Geometria vem da API; teste de vazamento de memória ao trocar de cena | 03/06 | 5 | ✔ C (supercélula desenhada pelo cliente — mover para motor, D-10) |
| RQ-FE-04 | Responsivo (desktop, notebook, tablet, smartphone) e WCAG 2.2 AA | axe-core sem violação séria; 360 px sem rolagem horizontal; teste com leitor de tela | 03/07 | 5/9 | ◐ C (auditoria própria; axe/Lighthouse e dispositivo real pendentes — D-19/D-20) |
| RQ-FE-05 | Estados de carregamento, vazio, erro, offline e operação longa | Matriz de estados por tela | 03 | 5 | ✔ C (PWA, conectividade) |
| RQ-FE-06 | Funcionalidades da v1.4 que o C não tem: ligas, temperatura, prática de Miller, densidade planar, cores por elemento, tutoriais | Cada uma portada consumindo a API (sem fórmula no cliente) | 03/06 | 5–6 | ✘ C · ✔ A |
| RQ-FE-07 | i18n pt-BR/en/es | Nenhuma chave sem uso; teste de catálogo | 03 | 5 | ✔ C (959 mensagens) |

### 3.8 Sistema educacional e IA (EDU) — §11

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-EDU-01 | Estudante: estudar, exercícios, simulações, quizzes, anotações, progresso; ABP/PBL | Fluxo E executável de ponta a ponta com persistência no servidor | 03/04 | 7 | ◐ C (tudo local, D-18) · ◐ A (prática de Miller) |
| RQ-EDU-02 | Professor: turmas, estudantes, atividades, dados da atividade, tentativas, correção, dificuldades, relatórios | Fluxo C executável; nada publicado sem serviço real | 04/02 | 7 | ◐ C (rascunhos locais; turmas demo, D-03) |
| RQ-EDU-03 | Tentativas persistidas e usadas para progresso e recomendação | Registro com tipo de erro; recomendação reproduzível | 02/04 | 7 | ◐ C (local) · especificado em `A/docs/1_*` e `3_*` |
| RQ-EDU-04 | Gabarito nunca exposto antes da política; exercícios paramétricos com gabarito calculado pelo motor | Teste automatizado de campos proibidos nas respostas | 01 | 7 | ✘ (especificado em `A/docs/3_*`) |
| RQ-EDU-05 | Camada de IA plugável com contexto autorizado; sem inventar resultados | Adaptador desativado por padrão; respostas citam a origem dos dados | 04 | 7 | ◐ C (adaptador desativado, D-08) |
| RQ-EDU-06 | Biblioteca de tutoriais (txt, md, mp4, pdf, planilhas, docs) com upload seguro | Lista branca, limite de tamanho, sem execução no navegador, autoria | 01/03 | 7 | ✔ A (servidor local) |

### 3.9 Qualidade e testes (QA) — §13

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-QA-01 | Backend: unitários, integração, API, schemas, persistência, auth, permissões, concorrência, erros, migração | Suíte verde no CI | 07 | 9 | ◐ Fase 3: 206 aprovados / 22 pulados (21 PostgreSQL, 1 Gemmi) |
| RQ-QA-02 | Frontend: typecheck, lint, unitários, componentes, navegação, a11y, responsividade, E2E Playwright | Suíte verde **em Linux e Windows** | 07 | 9 | ◐ C (typecheck ok; lint e 6/76 unitários falham no Windows; E2E não executado aqui) |
| RQ-QA-03 | Testes científicos de referência com literatura e comparação entre versões | Casos com fonte citada; regressão A/B/D automatizada | 07 + especialista | 3/9 | ✔ Fase 3: `tests/scientific/test_regressao_versoes.py` + referências de literatura nos testes do motor |
| RQ-QA-04 | Fluxos A–E (seção 4) aprovados sem dados fictícios | Evidência por fluxo | 07 | 9 | ◐ C (A–E aprovados contra stub e demo) |
| RQ-QA-05 | Validação de CIF com Gemmi | Teste usando o extra `validacao` do B | 07 | 9 | ◐ B (dependência opcional prevista) |

### 3.10 Infraestrutura (OPS) — §14

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-OPS-01 | Docker + Compose (backend, frontend, PostgreSQL; Redis só se necessário) | `docker compose up` sobe tudo com health checks | 06 | 8 | ✘ (Docker indisponível nesta máquina, ver L-02) |
| RQ-OPS-02 | Ambientes dev, teste e produção separados | Configuração por ambiente; testes nunca usam credencial de produção | 06 | 8 | ◐ B (`Settings` por ambiente) |
| RQ-OPS-03 | Health checks, logs estruturados, monitoramento | `/health/live` e `/health/ready` + logs JSON com request ID | 06 | 8 | ◐ B (health checks) |
| RQ-OPS-04 | CI/CD | Pipeline roda tudo da seção 3.9 | 06 | 8 | ◐ C (`.github/workflows`) |
| RQ-OPS-05 | Migrações controladas, nunca destrutivas automaticamente | Gate manual para downgrade e DROP | 02 | 8 | ✘ |

### 3.11 Documentação (DOC) — §16, §18, §19

| ID | Requisito | Critério de aceitação | Agente | Fase | Cobertura atual |
|---|---|---|---|---|---|
| RQ-DOC-01 | Os 15 documentos de `docs/` do §16 | Existem e batem com o código entregue | todos | 10 | ◐ (este documento + relatório de auditoria) |
| RQ-DOC-02 | README, dependências Python e JS, `.env.example`, Dockerfile, compose, OpenAPI | Outro desenvolvedor instala e roda sem ajuda externa | 06 | 10 | ◐ por base, sem unificação |
| RQ-DOC-03 | Relatório de encerramento A–J (§19) | Entregue na Fase 10 | 05 | 10 | ✘ |

## 4. Fluxos de aceitação (§13.4)

Cada fluxo é aprovado só com execução real, persistência confirmada e sem dado fictício em produção.

| Fluxo | Caminho | Depende de | Situação de partida |
|---|---|---|---|
| A — CrystaLab | Estudante escolhe metal → motor calcula → API devolve → front apresenta → atividade registrada | RQ-CIE-01..04, API-01..03, EDU-03, DAD-01 | Cálculo e apresentação ok (B+C compatíveis); registro inexistente |
| B — HEA | Composição → validação → motor HEA → resultado persistido → propriedades com procedência | RQ-HEA-01..05 | Bloqueado: motor HEA inexistente (D-01) |
| C — Professor | Atividade → materiais → turma → estudante executa → persistência → desempenho | RQ-EDU-02..04, SEG-03..04, DAD-02 | Apenas rascunho local |
| D — Banco de materiais | Cadastro de liga → validação → persistência → fonte → disponibilidade por permissão | RQ-DAD-05..06, SEG-03 | Inexistente |
| E — Aprendizagem | Exercício → tipo de erro → tentativa → progresso → recomendação | RQ-EDU-01, EDU-03 | Local (C) |

## 5. Critérios globais de aprovação (§13.5)

Zero erro crítico de compilação · zero vulnerabilidade crítica conhecida · todos os testes obrigatórios aprovados (Linux **e** Windows) · nenhuma regressão nos fluxos preservados · nenhuma divergência científica sem explicação · persistência confirmada após reinicialização · contratos front/back compatíveis (gerados do OpenAPI) · documentação atualizada · build reproduzível.

## 6. Fases do Prompt ↔ gates do Supervisor (Agente 05 §8)

| Fase do Prompt (§17) | Gate | Entregável que fecha o gate | Agente líder |
|---|---|---|---|
| 1 Auditoria | Gate 0 — Diagnóstico | `RELATORIO_AUDITORIA_GERAL.md` + este documento | 05/07 |
| 2 Arquitetura | Gate 1 — Arquitetura | `ARQUITETURA_FINAL.md`, ER, contratos, ADRs | 05/06/02 |
| 3 Backend e banco | Gate 2 — Implementação por domínio | Motor único + migrações + repositórios + testes | 01/02 |
| 4 API | Gate 2/3 | OpenAPI + tipos TS gerados + testes de contrato | 01 |
| 5 Frontend | Gate 2/3 | Front consumindo só a API; portabilidade da v1.4 | 03/06 |
| 6 Integração científica | Gate 4 — Integração | Fluxos A e B reais | 06 |
| 7 Sistema educacional | Gate 4 | Fluxos C e E reais | 04/06 |
| 8 Segurança e infraestrutura | Gate 3/4 | Auth+RBAC, Docker, CI, pentest | 01/06/07 |
| 9 Testes e otimização | Gate 5 — Homologação | Regressão, a11y, desempenho, evidências | 07 |
| 10 Entrega | Gate 6 — Release | Docs §16, relatório §19, rollback | 05 |

## 7. Limitações do ambiente atual

| ID | Limitação | Efeito | Contorno proposto |
|---|---|---|---|
| L-01 | PostgreSQL não instalado nesta máquina | RQ-DAD não testável localmente | Docker (L-02), instalador nativo do PostgreSQL ou SQLite **só** para testes, nunca como fonte de verdade |
| L-02 | Docker não instalado | RQ-OPS-01 não verificável localmente | Instalar Docker Desktop ou validar no CI (GitHub Actions) |
| L-03 | Windows: comando `python` (sem `python3`) e caminhos com espaço | Testes do C falham (ver auditoria BUG-02) | Corrigir a portabilidade na Fase 5 |
| L-04 | Navegadores do Playwright não instalados | E2E do C não executado nesta auditoria | `npx playwright install chromium` na Fase 9 |
| L-05 | Sem motor HEA nem fonte de dados HEA | Fluxo B bloqueado | Ver Q-01 |

## 8. Decisões que dependem de humanos

| ID | Questão | Por que bloqueia | Opção recomendada |
|---|---|---|---|
| Q-01 | Existe um motor ou dataset HEA da equipe (ex.: `hea_engine.py`, `pesquisa_front1.17.py`)? | PI-02 proíbe inventar o modelo; Fluxo B depende dele | Enviar o código ou definir a referência bibliográfica (ex.: Yang & Zhang 2012; Guo 2011; tabela de ΔH de Takeuchi & Inoue 2005). Até lá, a Fase 3 entrega só ΔS e T_m média, que são analíticos, e o resto fica como "indisponível" |
| Q-02 | Onde hospedar (servidor da UFC, nuvem, só local)? | Define auth, HTTPS, backup e LGPD | Começar com Docker local + CI e decidir antes da Fase 8 |
| Q-03 | Quem valida cientificamente (professor responsável)? | Dados de α, T_f, eletronegatividade, valência e *a* medido da v1.4 não têm fonte conferida; densidade planar HC precisa validação | Nomear o revisor; nenhum desses dados vai a "validado" sem ele |
| Q-04 | Provedor de e-mail para verificação e recuperação de senha | RQ-SEG-01 | SMTP institucional ou serviço transacional; em dev, captura local (Mailpit) |
| Q-05 | SSO institucional disponível? | Pode substituir senha própria | Verificar com a TI da UFC; o desenho de auth fica plugável |
| Q-06 | Licença do projeto e dos dados | C é "UNLICENSED"; B é "uso interno" | Definir antes de abrir o repositório científico |

## 9. Manutenção deste documento

- Mudança de requisito: nova versão do documento + registro em `HISTORICO_DE_ALTERACOES.md` + aprovação do Agente 05.
- A coluna "Cobertura atual" é atualizada ao fim de cada gate, sempre apontando a evidência (teste, commit ou relatório).
- Um requisito só fica "atendido" com teste automatizado ou evidência registrada. Declaração de agente não basta (Agente 05 §13).
