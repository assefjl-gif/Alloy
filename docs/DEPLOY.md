# Deploy

## 1. Desenvolvimento local (sem Docker)

Requisitos: Python ≥ 3.11 (testado em 3.15) e Node ≥ 20 (testado em 24).

```bash
python -m venv .venv
.venv/Scripts/pip install -e "backend[dev]"        # Linux/macOS: .venv/bin/pip
cd frontend && npm install && npm run build
npm run engine -- --db ../var/dev.db               # API em 127.0.0.1:8010 (SQLite migrado + seed)
npm run serve                                      # outro terminal: front em http://127.0.0.1:5173
```

Sem `--db`, a API roda só com o seed JSON: cálculos, HEA e exportação funcionam, mas contas e questões
não. `npm run dev` recompila em modo watch.

## 2. Produção em um host (Docker Compose)

```bash
cp .env.example .env        # preencha POSTGRES_PASSWORD, ALLOY_SESSION_SECRET, ALLOY_CSRF_SECRET e ALLOY_DOMINIO
docker compose up -d --build
docker compose ps           # db healthy → migrate exited (0) → api healthy → web up
curl -f https://$ALLOY_DOMINIO/health/ready
```

| Serviço | Imagem | Papel |
|---|---|---|
| `db` | postgres:16-alpine | banco (volume `db-dados`) |
| `migrate` | alloy-api | `python -m app.cli preparar`: migrações Alembic + seeds (idempotente por versão de conjunto) |
| `api` | alloy-api | uvicorn, usuário sem privilégios, `/health/live` como healthcheck |
| `web` | alloy-web | Caddy: estáticos do front + proxy `/api` e `/health`, TLS automático |

O backend em `ALLOY_ENV=prod` recusa subir sem `DATABASE_URL`, sem os segredos, com demonstração
permitida, com CORS `*`, com IA ligada ou com cookie sem `Secure`.

## 3. Atualização e rollback

1. Faça backup antes: `docker compose exec db pg_dump -U alloy alloy > backup-$(date +%F).sql`.
2. Atualize: `git pull && docker compose up -d --build`. O `migrate` aplica só as migrações novas.
3. Rollback de código: volte ao commit anterior e rode `docker compose up -d --build`.
4. Rollback de banco: **manual e revisado** (RQ-OPS-05). Nenhuma migração faz DROP automático. Para voltar
   uma revisão, rode `docker compose run --rm migrate alembic downgrade -1` depois de revisar o downgrade, ou
   restaure o backup.
5. Seeds: uma versão nova de um conjunto de dados que já está no banco é **recusada**
   (`SeedJaCarregadoComOutraVersao`). Mudar dados científicos exige migração de dados revisada.

## 4. Verificação desta entrega

| Item | Verificado? |
|---|---|
| Backend, migrações, seed e CLI em SQLite | sim (local, Windows) |
| `alembic check` (modelos = migrações) | sim |
| Variantes PostgreSQL dos testes | **não** nesta máquina (sem PostgreSQL); rodam no job `backend-linux` do CI |
| Imagens Docker, compose e Caddyfile | **não** nesta máquina (sem Docker); YAML validado; subida completa no job `imagens` do CI |
| CI no GitHub | escrito; ainda não executado (o repositório não foi publicado) |
