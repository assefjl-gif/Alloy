# Segurança

Decisões: ADR-008 (sessão), ADR-009 (RBAC), ADR-011 (mesmo domínio), ADR-016 (política em produção).
Código: `backend/app/security/`, `backend/app/services/autenticacao.py`, `backend/app/api/dependencias.py`.

## 1. Identidade e sessão

| Mecanismo | Implementação | Teste |
|---|---|---|
| Senha | Argon2id (`argon2-cffi`, parâmetros RFC 9106 *low memory*) + rehash automático quando os parâmetros mudam | `tests/unit/test_seguranca.py` |
| Política de senha | ≥ 10 caracteres, ≤ 256, recusa senhas comuns, repetitivas ou que contêm o e-mail | idem |
| Token de sessão | 256 bits (`secrets.token_urlsafe(32)`), só no cookie; o banco guarda o SHA-256 | `test_auth.py::test_login_cookie_seguro_e_token_so_no_cookie` |
| Cookie | `alloy_sessao`; `HttpOnly; Secure; SameSite=Lax; Path=/api`; `Secure` obrigatório em prod | idem |
| Expiração | inatividade de 7 dias (com renovação deslizante, no máximo uma escrita por minuto) e 30 dias absolutos | `test_sessao_expira_por_inatividade_e_por_idade` |
| Revogação | `POST /auth/logout` (sessão atual) e `/auth/logout-all` (todas as sessões da conta) | `test_logout_revoga_e_logout_all_encerra_todas` |
| CSRF | token próprio (hash no banco), renovado a cada `GET /auth/me`; cabeçalho `X-Alloy-CSRF` obrigatório em POST/PUT/PATCH/DELETE quando há cookie | `test_csrf_obrigatorio_com_cookie_e_historico_pessoal`, `test_me_renova_csrf_e_exige_sessao` |
| Força bruta | 5 falhas em 15 min por e-mail ou por IP → bloqueio de 30 s que dobra a cada nova falha | `test_bloqueio_progressivo_por_conta` |
| Enumeração | a mesma mensagem e o mesmo status para senha errada e para conta inexistente; o tempo também é igual (hash executado mesmo sem conta) | `test_login_errado_nao_revela_se_a_conta_existe` |
| Identidade no cliente | nenhuma: o front chama `/auth/me` na carga; o CSRF fica só em memória | `frontend/tests/unit/account.test.ts` |

## 2. Autorização (RBAC com escopo)

`app/security/rbac.py`: `autorizar(ator, acao, contexto)` é a única porta de decisão. Papéis
institucionais (`admin_institucional`, `professor`, `estudante`, `pesquisador`) valem **só** na
instituição do vínculo. Os papéis de turma (`professor_responsavel`, `estudante_matriculado`, `monitor`,
`professor_assistente`) são derivados de matrículas e turmas. `admin_geral` é o único papel global.

* Recurso de outra instituição → **404**, para não revelar que existe (`test_questao_de_outra_instituicao_e_invisivel`).
* Instância de questão de outro usuário → **404** (teste de IDOR `test_idor_instancia_de_outro_estudante_e_404`).
* Histórico pessoal isolado (`test_historico_isolado_entre_usuarios_e_anonimo_nao_grava`).
* Matriz papel × ação testada célula a célula (`test_matriz_rbac`).

## 3. Integridade científica como requisito de segurança

* O gabarito de questões nunca sai antes da tentativa (`test_fluxo_completo_sem_vazar_gabarito`).
* Em produção, dados não validados são recusados (`DADO_NAO_VALIDADO`, 422) ou a grandeza fica indisponível.
* Em produção o modo demonstrativo é proibido. A configuração `prod` recusa subir sem segredos, sem banco,
  com CORS `*`, com IA ligada ou com cookie sem `Secure`.

## 4. Borda HTTP

* Middlewares (`app/security/middlewares.py`): limite de corpo (413), rate limit por IP (429),
  cabeçalhos `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, CSP; `X-Request-ID` em toda resposta.
* Erro 500: o cliente recebe só o código de correlação; o detalhe fica no log.
* Caddy (`infrastructure/deployment/Caddyfile`): TLS automático, HSTS, CSP sem nada externo e sem script inline,
  `Permissions-Policy`, remoção do cabeçalho `Server`.
* Mesmo domínio: sem CORS em produção (ADR-011).

## 5. Limitações conhecidas

| Item | Situação | Risco | Plano |
|---|---|---|---|
| Limitador de login em memória | vale por processo | com várias réplicas, cada uma conta separado | mover para tabela ou Redis antes de escalar horizontalmente |
| Verificação de e-mail e recuperação de senha | modelo e tabela prontos (`tokens_uso_unico`); sem envio | conta nasce ativa e sem e-mail verificado | depende de SMTP (Q-04) |
| Administração de instituições e vínculos | sem API; criação direta no banco | operação manual | painel de administração (próxima etapa) |
| Pentest externo | não realizado | — | antes do lançamento público |
| Varredura de dependências | não automatizada no CI | CVE não detectada | adicionar `pip-audit` e `npm audit --omit=dev` ao CI |
| `ALLOY_SESSION_SECRET` / `ALLOY_CSRF_SECRET` | exigidos em prod, mas os tokens são aleatórios e não assinados | — | reservados para assinatura de tokens de e-mail |
