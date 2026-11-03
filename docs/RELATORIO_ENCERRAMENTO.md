# Relatório de encerramento (§19)

Projeto: Alloy Virtual Lab — consolidação de CrystaLab v1.0 (D), v1.1.0 (B), v1.4 (A) e alloy-frontend (C).
Período: 02/11/2026 (fases 1–10). API **0.9.0**, motor de cristalografia 2.0.0, térmico 1.0.0, HEA 1.0.0.
Ambiente de execução: Windows 10, Python 3.15.1, Node 24, sem PostgreSQL nem Docker (limitações L-01/L-02).

---

## A. Situação inicial

| Base | Forma | O que tinha de melhor | Principais problemas |
|---|---|---|---|
| A — CrystaLab v1.4 | um arquivo de 6 044 linhas (servidor, motor, HTML/CSS/JS embutidos) | ligas (Vegard, Hume-Rothery, intersticiais), temperatura (dilatação, Lindemann, alotropia), densidade planar, supercélulas | sem testes; N_A arredondado; *a* do Ti derivado de R (+6,3 % na densidade); dados novos sem fonte; "login" só por e-mail |
| B — CrystaLab v1.1.0 | FastAPI modular, 71 testes | motor com protocolo de repositório, N_A CODATA, *a* medido com prioridade, CIF/XYZ, envelope de erro | sem banco, sem usuários, rate limit desligado |
| C — alloy-frontend | React/TS estrito, design system, i18n, viewer 3D, PWA | a interface mais madura | HEA 100 % aleatório (motor ausente); professor e turmas só em rascunho local; 6/76 testes e o lint falhavam no Windows; validado contra um stub, nunca contra a API real |
| D — v1.0 | servidor stdlib | referência histórica (era o "motor" usado pelo C) | igual à A nos defeitos de N_A e Ti |

Problema estrutural: **três motores científicos com regras diferentes** e nenhum banco, autenticação ou
correção de exercícios no servidor. Detalhes em [RELATORIO_AUDITORIA_GERAL.md](RELATORIO_AUDITORIA_GERAL.md).

## B. Decisões arquiteturais

| Decisão | Tipo | ADR |
|---|---|---|
| Motor científico único em `backend/app/engines` com base no B, recebendo os recursos da A (ligas, temperatura, planar, supercélula) reescritos com testes | **preservado** (B) + **refatorado** (A) | ADR-001/002 |
| Motores puros (sem I/O); dados injetados por repositório; regras de camada verificadas por teste | reconstruído | ADR-004 |
| PostgreSQL + SQLAlchemy 2 + Alembic; 36 tabelas; seeds versionados; SQLite só nos testes rápidos | novo | ADR-003 |
| Estados de validação dos dados (`rascunho` → `aguardando_validacao` → `validado`) e política por ambiente: produção recusa dado não validado | novo | ADR-014/016 |
| API `/api/v1` com envelope único, procedência obrigatória e aliases `/v1` depreciados | refatorado (B) | ADR-007 |
| Frontend = C, sem vendoring e sem motor legado, consumindo só a API | **preservado** (C) + refatorado | ADR-010 |
| Sessão opaca em cookie + CSRF; Argon2id; RBAC com escopo | novo (o "login" da A foi **descartado**) | ADR-008/009 |
| Motor HEA analítico construído a partir da literatura (não havia código para portar) | reconstruído | ADR-013 |
| Mesmo domínio via Caddy; Docker Compose; CI Linux + Windows | novo | ADR-011/015 |
| Sem filas, Redis ou ML até haver necessidade medida | decisão de não fazer | ADR-012 |

## C. Melhorias realizadas

**Motores.** N_A CODATA 2018 numa constante única; *a* medido com prioridade; ligas, temperatura,
densidade planar validada só para as famílias com referência; supercélula e famílias com limites; passos de cálculo em toda
resposta; bloco `procedencia` com classe, versões e cada dado usado com estado e fonte; motor HEA (ΔS_mix,
δ, T_m, VEC, fase por Guo 2011) com indisponíveis explícitos.

**Banco.** Modelo completo (identidade, ciência, educação, auditoria); migrações 0001–0002; carga de seed
idempotente por versão de conjunto; repositório SQL que entrega exatamente o mesmo resultado que o seed JSON
(testado campo a campo); CLI `python -m app.cli migrar|seed|preparar`.

**API.** 35 rotas: cristalografia, termodinâmica, exportação, HEA, contas, histórico, questões, progresso
e plataforma. Erros padronizados com `request_id`; OpenAPI versionado e verificado no CI.

**Frontend.** Um cliente (`apiBase`) com rotas canônicas; tipos gerados do OpenAPI e verificação estática
das requisições; HEA com grandezas anuláveis e painel de indisponíveis; módulo `#/conta` (entrar, criar conta,
histórico, questões corrigidas no servidor); CSRF automático; portabilidade Windows.

**Educacional.** Três geradores de questões parametrizadas cujo gabarito e cuja resolução vêm do motor;
instâncias com semente registrada; correção, limite de tentativas e classificação do erro (fator 10ⁿ, sinal) no servidor.

**Infraestrutura.** Dockerfiles (API sem privilégios, borda Caddy), compose com PostgreSQL e serviço de
migração, `.env.example`, CI com PostgreSQL, contrato real, E2E e subida das imagens.

## D. Correções

| ID | Defeito | Causa-raiz | Solução |
|---|---|---|---|
| CIE-01 | Densidade do Ti +6,3 % | *a* derivado de R na A/D | *a* medido com prioridade e `a_fonte` (B); regressão entre versões |
| CIE-02 | N_A arredondado | constante local | constante única CODATA 2018 (teste garante uma só definição) |
| CIE-04 | Densidade planar de planos HC não basais | regra genérica aplicada a polígono não periódico | só famílias validadas (`FAMILIAS_VALIDADAS`) |
| CIE-05 | HEA com números aleatórios | motor inexistente | motor analítico; demonstrativo só quando forçado e sempre rotulado |
| A-B2 | v1.4 apresentava B2/L1₂ como fase para qualquer par (ex.: Fe–Cr) | heurística sem critério | aviso "hipotético" e classe `estimativa_modelo` |
| CR-08 | Diferença de ~5e-7 na geometria HC entre A/D e B | arredondamento prematuro na A/D | explicado no teste de regressão (tolerância só para HC da A/D) |
| BUG-01 | lint do C com 193 falsos positivos no Windows | `path.relative` comparado com `/` | caminhos normalizados para `/` (lint, build, i18n) |
| BUG-02 | 6/76 testes do C falhando no Windows | `python3` e `URL.pathname` | `fileURLToPath`; backend iniciado por `scripts/backend.mjs` com o Python do venv |
| INT-01 | C nunca validado contra a API real | ambiente | teste de contrato com servidor real (38/38) |
| F4-1 | `operationId` duplicado no OpenAPI (HEA GET/POST) | dois decoradores na mesma função | IDs explícitos (depois as rotas foram substituídas pelas reais) |
| F4-2 | API importando repositórios (violação de camada) | atalho na injeção de dependência | `services/provedor.py`; o teste de arquitetura pegou |
| F4-3 | Validação de `ThermalRequest` não rodava com campo ausente | `field_validator` não roda em ausentes | `model_validator(mode="after")` |
| F3-1 | Chaves estrangeiras não aplicadas nos testes SQLite | SQLite desliga FK por padrão | `PRAGMA foreign_keys=ON` no fixture |
| F9-1 | E2E de "mesma cena" falhava | os overlays guardam `procedencia.calculado_em`, que muda a cada chamada | a comparação ignora o carimbo de tempo (não faz parte da cena) |
| F9-2 | Testes HEA do C presumiam motor ausente | escritos para o modo demo | C1–C3 forçam `?demo=1`; C4 cobre o motor real; exemplo padrão com fase única (CoCrFeNi) |
| F9-4 | Na primeira carga, a detecção da API às vezes estourava o tempo-limite e o app ficava "sem motor" até recarregar | uma falha de detecção era tratada como definitiva | novas tentativas com espera crescente (1,5 s, 4 s, 10 s) enquanto houver rede |
| F9-5 | Barra de endereço sem a última camada logo após "Compartilhar" | a sincronização da URL tem atraso de 700 ms; o botão só copiava o link | compartilhar grava na barra de endereço o mesmo link copiado |
| F9-3 | OpenAPI gerado com CRLF no Windows | `write_text` no modo texto | `newline="\n"` (o CI compara com o versionado) |

## E. Qualidade (resultados reais desta máquina)

| Suíte | Resultado |
|---|---|
| Backend (`pytest`) | **311 aprovados, 23 pulados, 0 falhas** — pulados: 22 variantes PostgreSQL (L-01) e 1 validação CIF com Gemmi (T-01) |
| Lint backend (`ruff`) | sem achados |
| `alembic check` | modelos = migrações |
| Contrato API × frontend (servidor real, esquemas zod) | **38/38** |
| Frontend `typecheck` / `lint` | 0 erros / ok (112 arquivos, 9 regras) |
| Frontend unitários (`node --test`, incluindo backend real) | **77/77** |
| E2E Playwright (Chromium, backend real) | **54/55** na rodada final completa (backend real); o único que falhou (4.9, gerenciador de camadas) passou 5/5 repetido isolado → intermitente, registrado em PENDENCIAS (T-12) |
| Bundle inicial | **204,2 kB gzip** (meta < 300 kB), Three.js fora do inicial |

Detalhes por suíte e como reproduzir: [TESTES_E_QA.md](TESTES_E_QA.md). **Não executado aqui:** variantes PostgreSQL,
imagens Docker e CI no GitHub (o repositório não foi publicado, Q-07).

## F. Segurança

Implementado: Argon2id com política de senha; sessão opaca (só o hash no banco) com expiração por
inatividade e absoluta; revogação individual e global; CSRF por cabeçalho; bloqueio progressivo
de login; mensagens que não permitem enumerar contas; RBAC com escopo (404 fora da instituição; IDOR testado);
gabarito só no servidor; produção recusa configuração insegura; CSP, HSTS, `nosniff`, `DENY`,
limite de corpo e rate limit.

Limitações: limitador de login por processo; sem verificação de e-mail e recuperação de senha (Q-04);
sem API de administração de instituições; sem pentest externo; sem varredura automática de dependências.
Ver [SEGURANCA.md](SEGURANCA.md).

## G. Desempenho

| Métrica | Antes | Depois |
|---|---|---|
| Cálculo de célula (motor) | 0,24–0,94 ms de mediana (B, Fase 2) | mesmo motor; as rotas respondem em poucos ms (o custo dominante é HTTP/JSON) |
| Bundle inicial do front | 200,8 kB gzip (C migrado, Fase 5) | 204,2 kB gzip com conta e questões (+3,4 kB); os módulos novos carregam sob demanda |
| Testes backend | 71 (B) | 311 |

Não houve medição de carga, porque não havia ambiente com PostgreSQL. O ADR-012 adia filas e cache até haver uma medição que mostre a necessidade.

## H. Funcionalidades

**Implementadas e testadas:** célula unitária (4 estruturas, 15 metais + genéricas), densidade com passos,
FEA, Miller e Miller-Bravais com densidade planar validada, supercélulas, soluções sólidas
(substitucional e intersticial), temperatura (dilatação, Lindemann, alotropia), exportação CIF/XYZ,
HEA analítico (ΔS_mix, δ, T_m, VEC, fase), ponte HEA → CrystaLab, contas e sessões, histórico pessoal,
questões parametrizadas corrigidas no servidor com progresso, viewer 3D, i18n (3 idiomas), PWA offline do que é local.

**Implementadas parcialmente:** produção científica (em `prod`, só o que tem dado validado; hoje
nenhum dado está validado, por isso a temperatura e partes do HEA ficam indisponíveis); Fluxo C (as questões e o RBAC
existem; turmas, atribuições e notas têm tabela mas não têm rota); infraestrutura (escrita, mas não executada aqui).

**Demonstrativas (rotuladas):** HEA em modo demo quando forçado; painel do professor e atividades de
`#/aprender` (práticas locais, com semente); coloração ilustrativa por elemento.

**Não implementadas:** ΔH_mix, Ω, veredito de estabilidade e curva de Gibbs do HEA (Q-01); diagrama de fases;
repositório de materiais e ligas pela API; upload de tutoriais; verificação de e-mail e recuperação de senha;
IA (desligada por decisão, RQ-EDU-05).

## I. Pendências

Validação científica (Q-03: nenhum dado está `validado`); entalpias HEA com fonte (Q-01); SMTP (Q-04);
hospedagem (Q-02); licença (Q-06); publicação do repositório para o CI rodar (Q-07); PostgreSQL e Docker
para verificar as partes não executadas (L-01/L-02). Lista completa com responsáveis: [PENDENCIAS.md](PENDENCIAS.md).

## J. Recomendações futuras

1. **Validação científica como processo.** Uma tela de revisão (`revisoes_validacao` já existe), com duas
   assinaturas por dado e diff de versão dos seeds. É o que libera a produção.
2. **HEA completo.** Matriz de Miedema com fonte, depois Ω e o veredito; comparar com bases públicas
   (por exemplo, os dados de Gorsse et al., 2018) e publicar o conjunto de validação.
3. **Fluxo do professor de ponta a ponta.** API de instituições, turmas, atribuições e notas, com
   relatórios por turma. As tabelas e o RBAC já sustentam isso.
4. **Migrar `#/aprender` para os geradores do servidor**, mantendo a prática offline como modo local declarado.
5. **Operação:** limitador de login compartilhado, `pip-audit`/`npm audit` no CI, métricas
   Prometheus, backup automatizado com teste de restauração e pentest antes do lançamento público.
6. **Abertura científica:** API pública somente leitura de dados validados com DOI por versão de seed,
   o que torna a plataforma uma referência citável.
