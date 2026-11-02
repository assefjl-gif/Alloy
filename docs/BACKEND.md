# Backend (Fase 3)

## Estrutura entregue

```text
backend/
├── alembic.ini                 → migrações em ../database/migrations
├── pyproject.toml              → dependências, pytest, ruff
├── app/
│   ├── core/config.py          → Settings por ambiente (ALLOY_ENV dev/test/prod) e política de dados
│   ├── engines/                → motores puros (ver MOTOR_CIENTIFICO.md)
│   ├── models/                 → 36 tabelas SQLAlchemy 2.x (identidade, ciência, educacional)
│   ├── repositories/
│   │   ├── materiais_json.py   → seed JSON (testes do motor, ambiente sem banco)
│   │   ├── materiais_sql.py    → retrato dos valores vigentes do banco
│   │   └── seed_sql.py         → carga idempotente por versão dos seeds
│   └── services/calculo.py     → casos de uso: célula, Miller, solução sólida, temperatura + histórico
└── tests/
    ├── unit/                   → motor (B + v1.4) e regras de arquitetura
    ├── scientific/             → regressão entre versões A/B/D
    └── integration/            → migração real + seed + repositório SQL + serviço
```

Ainda **não** existem: a API `/api/v1` (Fase 4), autenticação e sessões (Fase 8; as tabelas já existem) e os serviços educacionais (Fase 7; as tabelas já existem).

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

## Resultado da última execução (02/11/2026, Windows, Python 3.15.1)

| Conjunto | Resultado |
|---|---|
| Suíte completa | **206 aprovados, 22 pulados**, 0 falhas |
| Pulados | 21 = variantes PostgreSQL (sem servidor nesta máquina, L-01); 1 = validação CIF com Gemmi (sem pacote para Python 3.15) |
| Lint (`ruff`) | sem achados |
| Migrações | `upgrade head` → `downgrade base` → `upgrade head` no SQLite; `alembic check` sem diferenças; DDL do PostgreSQL gerado em modo offline (`database/schemas/0001_esquema_inicial.postgresql.sql`) |

## Divergências do modelo da Fase 2 (BANCO_DE_DADOS.md)

| Item | Planejado | Implementado | Motivo |
|---|---|---|---|
| E-mail | `citext` | `varchar` + `CHECK (email = lower(email))` | Portável para o teste em SQLite; mesmo efeito |
| Listas (`topicos`, `materiais_ids`) | `text[]` / `uuid[]` | JSONB | Portável; consultas por elemento não são necessárias agora |
| Faixas de temperatura | `temperatura_*_k` | `temperatura_*_c` | Mesma unidade do seed; conversão é trivial |
| `materiais.tipo` | sem `intersticial` | `intersticial` incluído | C, N e H não são "elemento puro" estrutural |
| `materiais_estruturas` | sem `c_a`, `fonte_rede_id`, `referencia_ambiente` | incluídos | Fidelidade ao `Metal` do B (teste de ida e volta) |
| `versoes_dados` | não previsto | tabela nova (migração 0002) | `procedencia.versao_dados` vem do banco |
| Soma das frações da composição | gatilho `DEFERRABLE` | ainda não | Será validada no serviço de materiais (Fase 6/7) e o gatilho escrito com PostgreSQL disponível |
