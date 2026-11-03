# Backend

## Estrutura

```text
backend/
├── alembic.ini                 → migrações em ../database/migrations
├── pyproject.toml              → dependências, pytest, ruff
├── app/
│   ├── main.py                 → create_app(): middlewares, roteadores, /health*
│   ├── cli.py                  → python -m app.cli migrar | seed | preparar
│   ├── core/                   → Settings por ambiente (ALLOY_ENV dev/test/prod), request ID
│   ├── engines/                → motores PUROS: crystallography, thermodynamics, hea (MOTOR_CIENTIFICO.md, MOTOR_HEA.md)
│   ├── educational/            → geradores de questões (puros; o gabarito vem dos motores)
│   ├── models/                 → 36 tabelas SQLAlchemy 2.x (identidade, ciência, educacional)
│   ├── repositories/           → seed JSON, retrato SQL dos valores vigentes, carga idempotente de seeds
│   ├── security/               → senhas (Argon2id), tokens, RBAC, middlewares HTTP
│   ├── services/               → calculo, autenticacao, educacao, provedor (unidade de trabalho), erros
│   └── api/                    → dependências e rotas /api/v1 (rotas, auth, educacao) + aliases /v1
└── tests/
    ├── unit/                   → motores, segurança/RBAC, regras de arquitetura (camadas por análise de imports)
    ├── scientific/             → regressão entre versões A/B/D
    ├── integration/            → migração real + seed + repositório SQL + serviço (SQLite e PostgreSQL)
    ├── api/                    → HTTP real (TestClient): cálculo, HEA, contas, educacional, produção
    └── contract/               → uvicorn real × esquemas zod do frontend
```

**Regras de camada** (verificadas por `tests/unit/test_arquitetura.py`): `engines` e `educational` não
importam banco, HTTP nem serviços; `api` não importa `models`, `repositories`, `engines` (a não ser os
contratos listados) nem `sqlalchemy`; `services` não importa `api` nem `fastapi`.

**Unidade de trabalho:** uma sessão de banco por requisição (`get_sessao_db`), compartilhada pelos
serviços. O cálculo, o histórico e a renovação da sessão entram no mesmo commit, e um erro faz rollback de tudo.

## Executar

```bash
cd backend
python -m venv ../.venv
../.venv/Scripts/python -m pip install -e ".[dev]"
../.venv/Scripts/python -m pytest
../.venv/Scripts/python -m ruff check app tests
```

Migrações (a URL vem sempre de `DATABASE_URL`):

```bash
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/alloy ../.venv/Scripts/python -m alembic upgrade head
```

Testes de integração no PostgreSQL. Use um banco **descartável**: o fixture recria o schema `public`.

```bash
ALLOY_TEST_POSTGRES_URL=postgresql+psycopg://usuario:senha@localhost:5432/alloy_teste ../.venv/Scripts/python -m pytest tests/integration
```

## Resultado da última execução (Fase 9, 02/11/2026, Windows, Python 3.15.1)

| Conjunto | Resultado |
|---|---|
| Suíte completa | ver [TESTES_E_QA.md](TESTES_E_QA.md) |
| Lint (`ruff`) | sem achados |
| Migrações | `upgrade head` no SQLite pelo CLI; `alembic check` sem diferenças |

## Divergências do modelo da Fase 2 (BANCO_DE_DADOS.md)

| Item | Planejado | Implementado | Motivo |
|---|---|---|---|
| E-mail | `citext` | `varchar` + `CHECK (email = lower(email))` | Portável para o teste em SQLite; mesmo efeito |
| Listas (`topicos`, `materiais_ids`) | `text[]` / `uuid[]` | JSONB | Portável; consultas por elemento não são necessárias agora |
| Faixas de temperatura | `temperatura_*_k` | `temperatura_*_c` | Mesma unidade do seed; conversão é trivial |
| `materiais.tipo` | sem `intersticial` | `intersticial` incluído | C, N e H não são "elemento puro" estrutural |
| `materiais_estruturas` | sem `c_a`, `fonte_rede_id`, `referencia_ambiente` | incluídos | Fidelidade ao `Metal` do B (teste de ida e volta) |
| `versoes_dados` | não previsto | tabela nova (migração 0002) | `procedencia.versao_dados` vem do banco |
| Soma das frações da composição | gatilho `DEFERRABLE` | ainda não | Pendência T-02 (escrever com PostgreSQL disponível) |
| Propriedade `vec` | não prevista | nova no catálogo + seed `hea/vec.json` (conjunto `hea`) | Motor HEA (Fase 6) |
