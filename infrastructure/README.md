# infrastructure/

| Pasta | Conteúdo |
|---|---|
| `docker/backend.Dockerfile` | imagem da API (Python 3.12, usuário sem privilégios, healthcheck em `/health/live`) — também roda as migrações (`python -m app.cli preparar`) |
| `docker/web.Dockerfile` | build do frontend (typecheck + lint + esbuild) servido pelo Caddy |
| `deployment/Caddyfile` | borda única: estáticos + proxy `/api` → API, TLS automático, CSP/HSTS, cache imutável dos assets |
| `monitoring/` | convenções de logs e saúde (abaixo) |

O `docker-compose.yml` fica na raiz: `db` (PostgreSQL 16) → `migrate` (uma vez) → `api` → `web`.
Passo a passo em `docs/DEPLOY.md`.

## Observabilidade mínima

* **Saúde:** `/health/live` (processo), `/health/ready` (banco + dados carregados) — usados pelos
  healthchecks do compose e por qualquer monitor externo.
* **Logs:** Caddy em JSON no stdout; API com `X-Request-ID` em toda resposta e no log de erro 500
  (o cliente recebe só o código de correlação).
* **Não verificado nesta máquina:** Docker não está instalado no ambiente de desenvolvimento usado
  na consolidação; as imagens e o compose são exercitados no job `imagens` do CI.
