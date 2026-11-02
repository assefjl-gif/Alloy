# Relatório de Auditoria Geral — Fase 1 (Gate 0)

| Item | Valor |
|---|---|
| Data | 02/11/2026 |
| Escopo | Bases A, B, C e D (seção 1) — leitura, execução de testes e comparação numérica |
| Requisitos de referência | [`REQUISITOS_BASE.md`](REQUISITOS_BASE.md) |
| Ambiente | Windows 10, Python 3.15.1, Node 24.22.1, npm 11.19.1; FastAPI 0.162.0 e Pydantic 2.14.2 instalados em `.venv` |
| Estado inicial preservado | commit `2a6f79a` (bases intactas em `_origem/`); trabalho na branch `fase-1-auditoria` |
| Evidências reproduzíveis | `_auditoria/comparar_motores.py`, `_auditoria/comparacao_motores.json`, `_auditoria/contrato_b_c.mts` |
| Decisão solicitada ao Supervisor | Gate 0: **APROVADO COM RESSALVAS** (ressalvas = questões Q-01..Q-06 do documento de requisitos) |

> Escala de prioridade (§4.4): **P0** crítico (impede execução ou compromete integridade/segurança) · **P1** alto · **P2** moderado · **P3** baixo.
> Todo achado abaixo foi **observado nesta auditoria**. Onde a causa não foi confirmada, o texto diz "hipótese".

---

## 1. Diagnóstico individual

### A — CrystaLab v1.4 (`crystalab.zip`)
- **Forma:** um arquivo Python de 6 044 linhas com servidor `http.server`, motor, HTML, CSS e JS embutidos. Só usa a biblioteca padrão.
- **Pontos fortes exclusivos:** ligas (Vegard, Hume-Rothery, % at ↔ % peso, intersticiais C/N/H, ordenação L1₂/L1₀/B2, distorção ilustrativa); temperatura (dilatação, vibração pelo critério de Lindemann, alotropia de Fe, Ti e Co); densidade e fração planar; famílias de planos em supercélula; prática "qual é o plano?"; passo a passo de *a* e de FEA; caminho inverso *a* → R; cores Jmol editáveis; biblioteca de tutoriais com upload seguro; 3 especificações técnicas (`docs/1..3_*.txt`).
- **Fraquezas:** monolito; sem testes automatizados; N_A = 6,022e23; *a* sempre derivado de R (gera o erro do Ti); dados novos (α, T_f, eletronegatividade, valência, *a* medido) sem procedência conferida; "login" é só identificação por e-mail (o §9 proíbe reproduzir); persistência em arquivos JSON.

### B — CrystaLab v1.1.0 (`crystalab_v1.1.0.zip`)
- **Forma:** pacote Python modular de 29 arquivos: `core/` (motor), `api/` (FastAPI) e `web/` (UI estática com Three.js local).
- **Verificado:** `pytest` → **71 passaram, 1 pulado** (o E2E de UI ficou de fora por depender de Playwright); `ruff` sem achados.
- **Pontos fortes:** motor independente da API; `RepositorioMateriais` como protocolo (pronto para trocar JSON por banco); N_A CODATA 2018; *a* medido com prioridade e campo `a_fonte`; avisos de desvio acima de 3%; grupo espacial e Wyckoff; CIF/XYZ no servidor; schemas Pydantic; envelope de erro com `code`; health/live/ready; middlewares de CSP, limite de corpo e rate limit; rotas legadas marcadas como depreciadas.
- **Fraquezas:** `current_user` sempre anônimo; rate limit desligado por padrão; sem banco; sem correlation ID; dados de *a* medido só para o Ti; fonte do Callister sem edição e página (registrado pela própria base como CR-10).

### C — Alloy frontend (`alloy-frontend-completo.zip`)
- **Forma:** React 19 + TypeScript estrito + Zustand + Three.js r160 + KaTeX + Zod, com build próprio em esbuild. São 119 arquivos em `src` (13 515 linhas TS/TSX), 4 arquivos de teste unitário (76 testes) e 13 especificações E2E. O `vendor/` tem 5,4 MB (tipos e libs vendorizados porque o registro npm era bloqueado no ambiente original).
- **Verificado:** `npm install` funcionou nesta máquina; `typecheck` com **0 erros**; `lint` retorna **193 "problemas"**; `npm test` dá **70/76** (ver BUG-01 e BUG-02, ambos de portabilidade); E2E não executado (L-04).
- **Pontos fortes:** design system com catálogo; i18n em 3 idiomas; adaptadores com cancelamento e descarte de respostas obsoletas; validação Zod em tempo de execução; viewer 3D avançado; módulos de didática, caderno e professor; PWA offline; demonstrações rotuladas; registro honesto de pendências (D-01..D-20).
- **Fraquezas:** HEA 100% fictício (valores aleatórios com semente, D-01); professor e turmas só em rascunho local (D-03); toda persistência no navegador; o C foi validado contra um **servidor simulado** (`engine-stub/`) e contra o motor v1.0, nunca contra o B real; o lint e os testes não são portáveis para Windows.

### D — `crystalab_modulo1.py`
- **Idêntico** a `C/legacy/crystalab_modulo1.py` (v1.0, 2 860 linhas). A única diferença é a quebra de linha (CRLF × LF), verificada com `diff`. Não traz nada de novo: é o ancestral comum de A e B.

## 2. Comparação das versões

| Critério | A v1.4 | B v1.1.0 | C frontend | Melhor referência |
|---|---|---|---|---|
| Arquitetura | Monolito | Camadas core/api/web | Módulos + design system | **B** (backend) + **C** (frontend) |
| Código científico | Mais completo (ligas, térmico, planar) | Mais correto (CODATA, *a* medido, Wyckoff) | Não deve calcular (renderiza) | **B** como núcleo + portar o escopo de **A** |
| Frontend | HTML/JS embutido | JS modular simples | React/TS profissional | **C** |
| Backend | `http.server` | FastAPI + Pydantic | — | **B** |
| API | Rotas ad hoc `/api/*` | `/v1/*` versionada + OpenAPI | Cliente para v1 e legado | **B** |
| Banco de dados | Arquivos JSON | Seed JSON atrás de protocolo | localStorage | Nenhuma (criar PostgreSQL) |
| Segurança | Host + cabeçalho anti-CSRF; upload em lista branca; sem auth | CSP e cabeçalhos; limites; sem auth | Sem auth | **B** como base; auth do zero |
| Desempenho | Não medido | Não medido | Bundle 201 kB gzip (medição da própria base, não refeita aqui) | — |
| Design | Bom, coeso | Básico | Mais maduro | **C** |
| Testes | Nenhum automatizado | 71 ok | 70/76 no Windows; 54 E2E declarados | **B** + **C** |
| Escalabilidade | Baixa | Boa | Boa | **B** + **C** |

**Teste de compatibilidade real B ↔ C** (`_auditoria/contrato_b_c.mts`): a API B rodando de verdade, consultada com os schemas Zod do C, teve **15/15 respostas aceitas** (metais, estruturas, 7 células incluindo editada e genérica, 3 Miller, CIF e XYZ). Os contratos já são compatíveis, então a integração B+C não exige reescrita.

**Comparação numérica dos motores** (`_auditoria/comparar_motores.py`, 15 metais e 10 casos de Miller):
- A geometria de Miller (notação, átomos marcados, d, área) é **idêntica** em A, B e D nos 10 casos.
- Parâmetro de rede e densidade batem em 14 de 15 metais. As diferenças na 3ª casa (ex.: Fe 7,880 em A/D × 7,879 em B) vêm só da constante de Avogadro.
- **Ti diverge:** A e D dão *a* = 0,2890 nm e ρ = 4,792 g/cm³ (+6,3% sobre o experimental 4,51); B dá *a* = 0,2951 nm (medido) e ρ = 4,500 (−0,2%).

## 3. Funcionalidades preserváveis (migram com mínima alteração)

| Funcionalidade | Origem | Destino |
|---|---|---|
| Motor `core/` (células, Miller, geometria, exportação, entradas, erros, formatação) | B | `backend/app/engines/crystallography/` |
| API FastAPI: schemas, erros, middlewares de segurança, health checks | B | `backend/app/api/`, `backend/app/security/` |
| Testes do motor e da API (38 funções parametrizadas em 72 casos, mais 1 E2E de UI) | B | `backend/tests/` |
| Frontend inteiro (design system, i18n, viewer, comandos, didática, caderno, professor) | C | `frontend/` |
| Adaptadores com cancelamento, Zod, cliente HTTP único | C | `frontend/src/services/` |
| Especificações (histórico por usuário, diagrama de fases, exercícios) | A | `docs/especificacoes/` como insumo das Fases 3 e 7 |

## 4. Funcionalidades que precisam de refatoração

| Funcionalidade | Origem | Refatoração necessária |
|---|---|---|
| Ligas, temperatura, densidade planar, famílias de planos, passos de *a* e FEA, *a* → R | A | Extrair do monolito para `engines/` com a convenção do B (`constantes`, `geometria`, `erros`), testes de referência e dados com procedência |
| Tutoriais (upload e streaming com Range) | A | Reescrever como rotas FastAPI com auth, armazenamento fora da raiz servida e autoria vinculada ao usuário real |
| Repositório de materiais | B | Implementar `RepositorioPostgres` com o mesmo protocolo; o JSON vira seed versionado |
| Supercélula e famílias de planos no viewer | C (desenho no cliente) | Passar a consumir a geometria do motor (fecha D-10 e D-11) |
| Professor, turmas, caderno, progresso | C (local) | Trocar os adaptadores locais pelas rotas reais; manter o modo offline como cache, não como fonte de verdade |
| Lint e testes do C | C | Portabilidade (BUG-01, BUG-02) |

## 5. Funcionalidades que precisam ser reconstruídas

| Funcionalidade | Motivo |
|---|---|
| Autenticação e autorização (RQ-SEG-01..04) | Nenhuma base tem. O "login" da A é só identificação e o §9 proíbe reproduzi-lo |
| Banco relacional, migrações, histórico e versionamento científico | Inexistente |
| Motor HEA | O C só tem placeholders aleatórios. Reconstruir a partir de equações publicadas (Q-01) |
| Curva de Gibbs do HEA | Hoje é um passeio aleatório. Só pode voltar com ΔG = ΔH − TΔS real |
| Serviço educacional no servidor (atividades, tentativas, notas, relatórios) | Inexistente no backend |
| Repositório científico aberto com fluxo de validação | Inexistente |
| Infraestrutura (Docker, compose, CI unificado) | Inexistente para o conjunto |

## 6. Problemas críticos e defeitos encontrados

| ID | Pri. | Onde | Achado (observado) | Causa | Solução proposta |
|---|---|---|---|---|---|
| CIE-01 | **P1** | A, D (motor usado pelo C) | Densidade do Ti +6,3% sobre o experimental (4,792 × 4,51 g/cm³) | *a* sempre derivado de R = 0,1445 nm, que não reproduz a rede do α-Ti | Adotar a regra do B (*a* medido com prioridade e `a_fonte`); cadastrar *a* medido com fonte para todos os metais (Q-03) |
| CIE-02 | P2 | A, D | N_A = 6,022e23 (Fe 7,880 × 7,879 g/cm³ no B) | Constante arredondada | N_A CODATA 2018 = 6,02214076e23 em constante única (já no B) |
| CIE-03 | P2 | A | Valores de α, T_f, eletronegatividade, valência e *a* medido sem procedência conferida | Inseridos na v1.4 a partir de valores de manual não verificados nesta auditoria | Marcar como "a validar" no seed; só promover com fonte (RQ-DAD-06, Q-03) |
| CIE-04 | P2 | A | Densidade planar de planos HC não basais (ex.: (10-11) = 1,5 átomos) sem validação bibliográfica | Regra genérica de ângulo/aresta aplicada a polígono não periódico | Validar ou ocultar fora de (0001) e dos planos cúbicos (RQ-CIE-05) |
| CIE-05 | P1 | C | HEA mostra números aleatórios (ΔS, ΔH, Ω, δ, VEC, T_m, Gibbs) | Motor ausente (D-01); demo com semente | Manter rotulado só em modo demo; em produção, "indisponível" até RQ-HEA-01 |
| INT-01 | P1 | C | Nunca validado contra a API B real (só contra stub e v1.0) | B não estava no ambiente do C (D-14) | **Resolvido em auditoria:** 15/15 compatível. Transformar o script em teste de contrato no CI |
| INT-02 | P2 | A × B × D | Três motores com regras diferentes (Ti, N_A) | Evolução paralela | Núcleo único (PI-03) e teste de regressão entre versões (RQ-QA-03) |
| BUG-01 | P2 | C `scripts/lint.mjs` | No Windows, 193 falsos positivos (182× R7, 6× R5, 4× R1, 1× R3) e saída 1 | Exceções comparam `path.relative()` com caminhos `/`; no Windows o separador é `\` | Normalizar com `.split(path.sep).join('/')` |
| BUG-02 | P2 | C `tests/unit` | 6/76 falham no Windows: 4 por `spawn python3 ENOENT`, 2 por caminho `C:\C:\...%20` | `python3` inexistente no Windows; `new URL(...).pathname` em vez de `fileURLToPath` | Usar `fileURLToPath`; resolver o interpretador por `PYTHON` ou `process.platform` |
| SEG-01 | **P0 para a meta** | A, B, C | Nenhuma autenticação ou autorização real | Escopo das versões anteriores | RQ-SEG-01..04 na Fase 8. Até lá, nada sai do `127.0.0.1` |
| DAD-01 | P1 | A, B, C | Sem banco; dados acadêmicos só no navegador (C) ou em JSON local (A) | Escopo anterior | PostgreSQL + Alembic (RQ-DAD) |
| OPS-01 | P3 | B | Aviso: `starlette.testclient` com `httpx` está depreciado | Versão nova do Starlette | Ajustar a dependência de teste na Fase 3 |

## 7. Vulnerabilidades identificadas

Análise estática e de configuração. Pentest dinâmico não foi executado: depende de ambiente autorizado (Agente 07 §8).

| ID | Classe | Base | Situação | Recomendação |
|---|---|---|---|---|
| V-01 | Autenticação ausente | B (`current_user` anônimo), C | Confirmada | JWT/cookie + RBAC no backend |
| V-02 | Identidade forjável | A (qualquer e-mail @ufc.br sem senha) | Confirmada, documentada pela própria A | Não migrar; substituir por RQ-SEG-01 |
| V-03 | Abuso de endpoints | B (rate limit desligado por padrão) | Confirmada (configuração) | Ligar por padrão fora de dev; limitar no proxy |
| V-04 | XSS via HTML gerado | C (`Formula.tsx` usa `dangerouslySetInnerHTML` com saída do KaTeX) | **Suspeita, não confirmada**: depende de `trust: false` e da origem do texto | Verificar a configuração do KaTeX e criar teste com payload inofensivo (Fase 9) |
| V-05 | Dados pessoais no cliente | C (notas e progresso em localStorage) | Confirmada | Sincronizar com o servidor sob auth; LGPD (RQ-SEG-07) |
| V-06 | Uploads | A (tutoriais) | Mitigada: lista branca, sem HTML/SVG, anti-traversal, Host check | Manter as defesas ao migrar e adicionar auth e cota por usuário |

## 8. Incompatibilidades entre tecnologias

| Item | Detalhe | Decisão proposta |
|---|---|---|
| Servidor | A usa `http.server`; B usa FastAPI | FastAPI (B) |
| Build do frontend | C usa scripts esbuild próprios; o Prompt sugere avaliar alternativas | Manter esbuild (funciona, bundle medido); Vite só com ganho demonstrado (§5.1: "não substituir por preferência") |
| Dependências vendorizadas | C embute `vendor/` (5,4 MB) porque o npm era bloqueado lá | Aqui o `npm install` funcionou: remover `vendor/` e `link-deps.mjs` na Fase 5, após conferir versões |
| Viewer | A usa Three r128 via CDN; B usa r128 local; C usa r160 | r160 do C |
| Python mínimo | B declara ≥ 3.9; aqui roda 3.15 | Fixar ≥ 3.11 no backend unificado (tipagem moderna) e testar no CI |
| Contratos | C escreve Zod à mão; B gera OpenAPI | Gerar os tipos TS do OpenAPI e manter Zod como validação em tempo de execução (RQ-API-03) |

## 9. Problemas de arquitetura

1. **Fonte de verdade fragmentada.** Fórmulas em A, B e D, e dados em três formatos (dict Python, seed JSON, localStorage).
2. **O frontend decide geometria de supercélula e famílias** (D-10/D-11), contra o PI-03.
3. **Demonstração e realidade misturadas no mesmo adaptador.** O C resolve com rótulo e modo `auto`. Em produção é preciso `demo: 'off'` imposto por configuração de ambiente.
4. **Monolito da A sem testes.** O valor científico dela só pode migrar com testes de referência escritos antes.
5. **Sem camada educacional no servidor.** Turmas, atividades e tentativas não têm dono no backend.

## 10. Recomendações técnicas

1. **Base do backend = B.** Estender `engines/crystallography` com os recursos da A, refeitos com testes primeiro e usando as constantes, a geometria e os erros do B.
2. **Base do frontend = C.** Corrigir a portabilidade (BUG-01/02), remover o vendoring, gerar tipos do OpenAPI e portar as telas da A (ligas, temperatura, prática, tutoriais) consumindo a API.
3. **Teste de regressão entre motores permanente:** transformar `_auditoria/comparar_motores.py` em teste com tolerâncias e casos de literatura.
4. **Seed científico com procedência obrigatória:** cada valor com fonte, unidade e classificação (PI-06/07); valores da A sem fonte entram como "rascunho".
5. **Auth desde o primeiro endpoint novo:** as rotas educacionais já nascem protegidas; as de cálculo podem ser públicas com rate limit.
6. **HEA honesto:** entregar primeiro só o que é analítico e citável (ΔS_mix ideal, T_m média, VEC e δ a partir de dados de elementos com fonte). Ω e ΔH dependem da tabela de entalpias de pares (Q-01). Sem isso, "indisponível".

## 11. Plano de consolidação

| Fase | Entregas | Agentes | Gate |
|---|---|---|---|
| 2 — Arquitetura | `ARQUITETURA_FINAL.md`, ER e dicionário de dados, ADRs (B como backend, C como frontend, PostgreSQL, esbuild), mapa de rotas `/api/v1` | 05, 06, 02, 01 | 1 |
| 3 — Backend e banco | Monorepo; `engines/crystallography` a partir do B + recursos da A com testes; modelos SQLAlchemy e Alembic; `RepositorioPostgres`; seed com procedência | 01, 02 | 2 |
| 4 — API | Rotas `/api/v1` por domínio; OpenAPI → tipos TS; teste de contrato B↔C no CI | 01, 06 | 2/3 |
| 5 — Frontend | C no monorepo; portabilidade; vendoring removido; telas da A portadas; supercélula vinda do motor | 03, 06 | 2/3 |
| 6 — Integração científica | Fluxo A real; HEA com o subconjunto analítico citável | 06, 01 | 4 |
| 7 — Educacional | Atividades, tentativas, progresso, professor, exercícios com gabarito (especificações A/docs 1 e 3) | 04, 02, 01 | 4 |
| 8 — Segurança e infra | Auth+RBAC, isolamento institucional, Docker/compose, CI, pentest autorizado | 01, 06, 07 | 3/4 |
| 9 — Testes | Regressão, a11y (axe), E2E Playwright Linux+Windows, desempenho | 07 | 5 |
| 10 — Entrega | Docs do §16 e relatório §19 | 05 | 6 |

## 12. Critérios de aceitação desta fase (Gate 0)

| Critério | Situação | Evidência |
|---|---|---|
| Inventário das quatro bases | Atendido | Seção 1; árvore em `_origem/` (commit `2a6f79a`) |
| Testes existentes executados com resultado real | Atendido (B: 71+1 skip; C: typecheck ok, lint com falha, unit 70/76) | Seções 1 e 6 |
| Comparação científica entre versões | Atendido (15 metais × 3 motores; 10 casos de Miller) | `_auditoria/comparacao_motores.json` |
| Compatibilidade de contrato front↔back verificada | Atendido (15/15) | `_auditoria/contrato_b_c.mts` |
| Problemas classificados com solução proposta | Atendido | Seções 6 e 7 |
| Plano de consolidação e critérios das próximas fases | Atendido | Seção 11 e `REQUISITOS_BASE.md` |
| Questões humanas registradas | Atendido | Q-01..Q-06 em `REQUISITOS_BASE.md` §8 |
| E2E Playwright do C | **Não executado** | Limitação L-04 |
| Pentest dinâmico | **Não executado** (fora do escopo de auditoria estática) | Agente 07 §8 |

**Riscos residuais:** motor HEA indefinido (Q-01); dados científicos da v1.4 sem procedência (Q-03); infraestrutura de banco e containers indisponível nesta máquina (L-01, L-02).
