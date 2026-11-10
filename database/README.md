# database/

Banco de dados do Alloy Virtual Lab: PostgreSQL 16 em produção, SQLite em desenvolvimento e testes
(ADR-003). Modelo lógico e dicionário de dados: [`docs/BANCO_DE_DADOS.md`](../docs/BANCO_DE_DADOS.md).

| Pasta | Conteúdo |
|---|---|
| `migrations/` | Alembic, versionadas, reversíveis; nunca destrutivas sem gate manual |
| `seeds/` | Dados de referência com procedência obrigatória (fonte, unidade, estado de validação, versão) |
| `schemas/` | DDL PostgreSQL gerado das migrações (`alembic upgrade --sql`), para revisão do DBA |

## Migrações

| Revisão | Conteúdo |
|---|---|
| `0001` | Esquema inicial: identidade, ciência, cálculos, educacional, arquivos e auditoria |
| `0002` | Versões dos conjuntos de dados (`versoes_dados`) |
| `0003` | Tabela periódica completa (ADR-018): colunas de classificação em `elementos` com `CHECK`, `fontes.acessado_em`/`versao_fonte` e a tabela `propriedades_elemento` |

```bash
cd backend
../.venv/Scripts/python -m alembic upgrade head      # aplica
../.venv/Scripts/python -m alembic downgrade 0002    # reverte a 0003 sem perder dados anteriores
../.venv/Scripts/python -m alembic check             # modelos == migrações
```

## Seeds

| Conjunto | Arquivo | Versão | Conteúdo |
|---|---|---|---|
| `cristalografia` | `seeds/cristalografia/` | v1.4 | 15 metais, estruturas, intersticiais (entrada dos motores) |
| `propriedades_v14` | `seeds/cristalografia/propriedades_v14.json` | v1.4 | propriedades usadas pelos cálculos de ligas e temperatura |
| `hea` | `seeds/hea/` | — | VEC e dados do motor HEA |
| `tabela_periodica` | `seeds/tabela_periodica/elementos.json` | `2026.11.3-tp` | 118 elementos, 763 valores atômicos com fonte; fontes em `FONTES.txt` |

A carga é idempotente e recusa um banco que já tenha outra versão do mesmo conjunto
(`SeedJaCarregadoComOutraVersao`). Para regenerar a tabela periódica a partir das fontes:

```bash
.venv/Scripts/python scripts/importar_tabela_periodica.py            # baixa (CIAAW, PubChem, Wikipédia) e gera o seed
.venv/Scripts/python scripts/importar_tabela_periodica.py --offline  # usa o cache em var/fontes_tabela_periodica
```

## Backup

```bash
cd backend && ../.venv/Scripts/python -m app.cli backup ../var/backup.db
```

SQLite: cópia online + `PRAGMA integrity_check` (restauração testada). PostgreSQL: o comando mostra o `pg_dump` equivalente.

## Desempenho

Auditoria de latência API ↔ banco: [`docs/AUDITORIA_LATENCIA_BANCO.txt`](../docs/AUDITORIA_LATENCIA_BANCO.txt).
