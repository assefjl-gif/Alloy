# Decisões Técnicas (ADRs)

Registro de decisões de arquitetura. Formato: contexto → decisão → alternativas → consequências.
Status possíveis: **Proposta** (aguarda gate), **Aceita**, **Substituída por ADR-n**, **Rejeitada**.
Todas estão como **Proposta** até a decisão do Gate 1 (Agente 05).

Índice: [001 Monorepo](#adr-001) · [002 Backend](#adr-002) · [003 Persistência](#adr-003) · [004 Motor único](#adr-004) · [005 Parâmetro de rede](#adr-005) · [006 Convenções da API](#adr-006) · [007 Contratos TS](#adr-007) · [008 Sessão e CSRF](#adr-008) · [009 RBAC](#adr-009) · [010 Frontend](#adr-010) · [011 Entrega](#adr-011) · [012 Assíncrono](#adr-012) · [013 HEA](#adr-013) · [014 Dados científicos](#adr-014) · [015 Arquivos](#adr-015) · [016 Demonstração](#adr-016) · [017 Portabilidade](#adr-017)

---

<a id="adr-001"></a>
## ADR-001 — Monorepo único

- **Contexto:** quatro bases separadas, com contratos acoplados (B↔C) e um mesmo motor em três cópias (A, B, D).
- **Decisão:** um repositório com `backend/`, `frontend/`, `database/`, `infrastructure/`, `docs/` e `scripts/`, e as bases originais congeladas em `_origem/` até o fim da migração.
- **Alternativas:** repositórios separados, que exigiriam versionar contratos entre repositórios sem necessidade nesta escala.
- **Consequências:** mudanças de contrato atômicas (backend + tipos + frontend no mesmo commit); CI único. `_origem/` sai do repositório na Fase 10, depois de arquivada.

<a id="adr-002"></a>
## ADR-002 — Backend: FastAPI a partir da base B, Python ≥ 3.11

- **Contexto:** B tem camadas, Pydantic, OpenAPI, 72 casos de teste verdes e middlewares de segurança. A usa `http.server` monolítico.
- **Decisão:** evoluir B. Python mínimo 3.11 (sintaxe de tipos moderna, `tomllib`, desempenho). CI testa 3.11 e 3.13.
- **Alternativas:** reescrever do zero (perderia testes e correções CR-01/CR-08 do B); Django (troca sem ganho para uma API de cálculo).
- **Consequências:** a A não migra como código; seus recursos são reimplementados no padrão do B. Isso já estava medido na auditoria (B é o motor mais correto).

<a id="adr-003"></a>
## ADR-003 — PostgreSQL 16 + SQLAlchemy 2.x (síncrono) + psycopg 3 + Alembic

- **Contexto:** hoje os dados estão em JSON local (A, B) e no localStorage (C). O §7 pede persistência central, integridade e histórico.
- **Decisão:** PostgreSQL 16; ORM SQLAlchemy 2.x no estilo `Mapped[]`, em modo **síncrono**; driver psycopg 3; migrações Alembic.
- **Por que síncrono:** os handlers do B são `def` e rodam no threadpool. Os cálculos levam menos de 1,1 ms (medido). O modo assíncrono traria complexidade (sessões async, drivers) sem ganho medido.
- **Alternativas:** SQLite (não serve para concorrência nem para produção; aceito só em teste unitário de repositório, nunca como fonte de verdade); ORM assíncrono (revisar se o p95 de E/S de banco justificar).
- **Consequências:** é preciso ter PostgreSQL no ambiente (L-01). Os testes de integração usam Postgres real (container no CI).

<a id="adr-004"></a>
## ADR-004 — Um único núcleo científico com motores puros

- **Contexto:** a auditoria encontrou três motores divergentes (Ti +6,3%; constantes de Avogadro diferentes).
- **Decisão:** `backend/app/engines/` contém funções puras, sem I/O. Dados de referência são **injetados**. Constantes vêm só de `engines/crystallography/constantes.py` (do B). Toda funcionalidade da A entra com **testes de referência escritos antes** da implementação.
- **Consequências:** o frontend não calcula (PI-03). O teste `tests/scientific/test_regressao_versoes.py` compara o motor novo com os resultados congelados de A e B e explica cada divergência.

<a id="adr-005"></a>
## ADR-005 — Parâmetro de rede: valor medido tem prioridade

- **Contexto:** CIE-01 (o Ti com *a* derivado de R dá +6,3% de densidade).
- **Decisão:** adotar a regra do B. Se existir *a* (e *c*) medido com fonte, ele é usado e `a_fonte = "medido"`. Senão, `a = k·R` com `a_fonte = "derivado_de_R"`. Em ambos os casos a resposta mostra o valor alternativo para fins didáticos.
- **Consequências:** é preciso cadastrar *a* medido com fonte para todos os metais (Q-03). Até lá, só o Ti tem esse dado.

<a id="adr-006"></a>
## ADR-006 — Convenções da API

- **Decisão:**
  - Prefixo canônico `/api/v1`. Os caminhos `/v1/*` atuais do B ficam como **alias depreciado** até o frontend migrar (Fase 5), com cabeçalhos `Deprecation` e `Link` (padrão já usado pelo B nas rotas legadas).
  - Caminhos em inglês (como no §8.2); **campos JSON em português `snake_case`**, mantendo os contratos existentes (`densidade`, `a_nm`, `passos_densidade`) que o C já valida.
  - Envelope atual preservado: `{"ok": true, "result": …}` e `{"ok": false, "error": …, "code": …, "status": …, "request_id": …}`.
  - Coleções: `result = {"itens": [...], "total": n, "pagina": p, "tamanho": t}`, com `?pagina=&tamanho=&ordem=campo,-campo` e filtros por campo.
- **Alternativas:** campos em inglês (quebraria os 15/15 contratos compatíveis e o C inteiro sem ganho funcional).
- **Consequências:** um só idioma de campos em toda a API. Os nomes de rota seguem o Prompt Mestre.

<a id="adr-007"></a>
## ADR-007 — Contratos TypeScript gerados do OpenAPI, com Zod mantido

- **Contexto:** o C escreve Zod à mão (D-15) e foi validado contra um stub.
- **Decisão:** `scripts/gerar-tipos` usa **openapi-typescript** (só desenvolvimento) para gerar `frontend/src/services/api/gerado.d.ts`. Os schemas Zod continuam fazendo a validação em tempo de execução. O teste de contrato (evolução de `_auditoria/contrato_b_c.mts`) valida as respostas reais da API contra os dois e quebra o CI se divergirem.
- **Alternativas:** gerar Zod a partir do OpenAPI (ferramentas menos maduras para os schemas atuais com `discriminatedUnion`).

<a id="adr-008"></a>
## ADR-008 — Autenticação por sessão opaca em cookie; sem JWT

- **Contexto:** a SPA e a API ficam no mesmo domínio (ADR-011); a LGPD exige revogação e logout efetivo.
- **Decisão:**
  - Token opaco de 256 bits em cookie `HttpOnly; Secure; SameSite=Lax; Path=/api`. A tabela `sessoes` guarda só o SHA-256 do token.
  - Expiração por inatividade (padrão 7 dias) e absoluta (30 dias), renovação deslizante, revogação individual e "sair de todos os dispositivos".
  - Anti-CSRF: cabeçalho `X-Alloy-CSRF` obrigatório em métodos de escrita (token vinculado à sessão) + `SameSite`.
  - Senha: Argon2id (`argon2-cffi`); política mínima de 10 caracteres com verificação contra lista de senhas comuns.
  - Tokens de verificação de e-mail e redefinição: uso único, hash no banco, 24 h e 1 h de validade.
  - Bloqueio progressivo após tentativas de login falhas (por conta e por IP).
- **Alternativas:** JWT em localStorage (exposto a XSS, revogação difícil); JWT em cookie (não ganha nada sobre a sessão opaca neste cenário).
- **Consequências:** o C deixa de guardar identidade no cliente e passa a chamar `GET /api/v1/auth/me` na inicialização. O "login" por e-mail da A **não** é reproduzido (§9). A interface fica plugável para SSO institucional (Q-05).

<a id="adr-009"></a>
## ADR-009 — RBAC com escopo (global, instituição, turma, dono)

- **Decisão:** papéis do §9 (administrador geral, administrador institucional, professor, estudante, pesquisador).
  - `usuarios.admin_geral` é o único papel global.
  - Os demais papéis valem **por instituição** (`vinculos_institucionais.papel`) e, em turma, por matrícula (`matriculas.papel_turma`).
  - Toda verificação acontece em `services`, por função `autorizar(ator, acao, recurso)` com tabela de permissões testada (matriz papel × ação).
- **Consequências:** um professor numa instituição pode ser estudante em outra. Acesso a objeto de outra instituição responde **404** (não revela existência), e o teste de IDOR é obrigatório para cada rota de recurso.

<a id="adr-010"></a>
## ADR-010 — Frontend a partir da base C; manter esbuild; remover vendoring

- **Contexto:** o C é a base mais madura (design system, i18n, viewer, PWA). O vendoring de 5,4 MB existia só porque o registro npm era bloqueado no ambiente original. Aqui o `npm install` funcionou.
- **Decisão:** migrar o C para `frontend/`; dependências via npm com `package-lock.json`; remover `vendor/`, `scripts/link-deps.mjs`, `engine-stub/` e `legacy/`; manter o build esbuild (funciona e tem metas medidas). Vite só se houver ganho demonstrado (§5.1). Corrigir BUG-01/02.
- **Consequências:** a meta de bundle continua < 300 kB gzip sem o Three.js, medida no CI.

<a id="adr-011"></a>
## ADR-011 — Entrega no mesmo domínio via proxy reverso (Caddy)

- **Decisão:** Caddy serve `frontend/dist` e encaminha `/api/*` para o uvicorn. Em dev, o `scripts/dev.mjs` do C faz o proxy para a API local.
- **Alternativas:** nginx (equivalente; Caddy simplifica TLS automático); servir os estáticos pelo FastAPI (aceitável só em dev).
- **Consequências:** sem CORS em produção; uma CSP para tudo; cookies `SameSite` funcionam sem exceções.

<a id="adr-012"></a>
## ADR-012 — Sem filas nem Redis até haver evidência

- **Decisão:** não adotar Celery, RQ ou Redis agora. Gatilhos objetivos para revisar: p95 de uma rota > 2 s, tarefa > 10 s, ou necessidade de agendamento (relatórios periódicos, lembretes).
- **Consequências:** o design de `execucoes_calculo` já tem `status` (pendente, em execução, concluído, falhou) para permitir migrar para worker sem mudar o contrato.

<a id="adr-013"></a>
## ADR-013 — HEA: só grandezas com fonte; modelo preditivo bloqueado até Q-01

- **Contexto:** o HEA do C é aleatório (D-01). O §6.3 e o PI-02 proíbem inventar modelo.
- **Decisão:**
  - **Fase 3:** ΔS_mix ideal (= −R Σ xᵢ ln xᵢ), T_m média ponderada, VEC médio e δ = 100·√Σxᵢ(1 − rᵢ/r̄)², com dados de elemento com fonte. Valores de referência das equações só com a citação conferida (Q-03).
  - **ΔH_mix e Ω:** dependem da tabela de entalpias de pares. Sem ela, os campos voltam como `indisponivel` com o motivo.
  - **Classificação de fase:** só com critérios publicados e citados, rotulada `estimativa_modelo`.
  - A curva de Gibbs aleatória sai de produção.
- **Consequências:** o Fluxo B fica parcialmente atendido na Fase 6 e completo quando Q-01 for resolvida.

<a id="adr-014"></a>
## ADR-014 — Dados científicos versionados, append-only, com estados de validação

- **Decisão:**
  - Cada valor de propriedade é uma linha imutável com fonte, unidade, classe e condições.
  - Corrigir um valor cria uma linha nova que aponta a anterior (`substitui_id`); a antiga fica preservada.
  - Estados `rascunho → aguardando_validacao → validado | rejeitado → arquivado`, com tabela de revisões.
  - O motor em produção consome só valores `validado` e vigentes.
  - O seed tem versão (`versao_dados`), como no B.
- **Consequências:** um estudante não altera dado validado (PI-05); todo resultado aponta a `versao_dados` usada.

<a id="adr-015"></a>
## ADR-015 — Arquivos fora da raiz web, metadados no banco

- **Decisão:** binários em `STORAGE_DIR` com nome igual ao `sha256`; metadados em `arquivos` (dono, instituição, visibilidade, tipo, tamanho). Download por rota autenticada com Range, `Content-Disposition` e `nosniff`. Lista branca de tipos herdada da A (sem HTML, SVG ou JS). Cota por usuário.
- **Consequências:** a biblioteca da A passa a ter dono, permissões e deduplicação.

<a id="adr-016"></a>
## ADR-016 — A política de demonstração é imposta pelo servidor

- **Decisão:** `GET /api/v1/meta/capabilities` informa, por serviço, `disponivel`, `demo_permitido` e `motivo`. Em `ALLOY_ENV=prod` a API força `demo_permitido=false`, e o frontend (modelo `live/demo/disabled` do C) obedece. Dados de demonstração nunca entram em tabelas acadêmicas.
- **Consequências:** o modo `auto` do C continua em dev; em produção nada demonstrativo aparece por engano.

<a id="adr-017"></a>
## ADR-017 — Portabilidade Linux e Windows obrigatória

- **Contexto:** BUG-01 e BUG-02 (lint e testes do C falham no Windows); a equipe desenvolve em Windows.
- **Decisão:** o CI roda backend e frontend em `ubuntu-latest` e `windows-latest`. Proibido `URL.pathname` para caminhos (usar `fileURLToPath`) e `python3` fixo (usar a variável `PYTHON` com padrão por plataforma).
- **Consequências:** o "build reproduzível" do §13.5 vale nos dois sistemas.
