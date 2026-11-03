# Alloy Virtual Lab

Plataforma de engenharia de materiais para ensino e pesquisa: **CrystaLab** (células unitárias, Miller,
densidade, FEA, soluções sólidas, temperatura, exportação CIF/XYZ), **HEA** (ligas de alta entropia:
ΔS_mix, δ, T_m, VEC e fase), **contas com histórico** e **questões corrigidas no servidor**.

Resultado da consolidação de quatro bases (CrystaLab v1.0, v1.1.0 e v1.4, e alloy-frontend) conduzida pelo
*Prompt Mestre* em 10 fases. Relatório final: [`docs/RELATORIO_ENCERRAMENTO.md`](docs/RELATORIO_ENCERRAMENTO.md).

## Princípios

1. **Nenhum dado científico inventado.** Todo resultado traz `procedencia` (classe, motor, versão, dados usados
   e estado de validação). O que não tem base volta como `null`, com o motivo.
2. **Um motor, um lugar.** A ciência roda só no backend (`backend/app/engines/`). O front exibe.
3. **Produção é estrita.** Dados não validados são recusados, a demonstração é proibida e os segredos são obrigatórios.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `backend/` | FastAPI: motores puros (`engines/`), serviços, API `/api/v1`, segurança, CLI de banco — [BACKEND.md](docs/BACKEND.md) |
| `frontend/` | React 19 + TypeScript estrito, viewer Three.js, PWA, 3 idiomas — [FRONTEND.md](docs/FRONTEND.md) |
| `database/` | migrações Alembic, DDL PostgreSQL de referência, seeds versionados |
| `infrastructure/` | Dockerfiles, Caddyfile, observabilidade — [DEPLOY.md](docs/DEPLOY.md) |
| `scripts/` | exportação do OpenAPI, teste de contrato, geração de seed |
| `docs/` | os 15 documentos do §16 + requisitos, gates e relatório final |
| `_origem/` | as quatro bases recebidas, **intactas** (somente leitura) |
| `_auditoria/` | scripts reproduzíveis da auditoria da Fase 1 |

## Começar (desenvolvimento)

```bash
python -m venv .venv
.venv/Scripts/pip install -e "backend[dev]"          # Linux/macOS: .venv/bin/pip
cd frontend
npm install
npm run build
npm run engine -- --db ../var/dev.db                 # API em http://127.0.0.1:8010 (SQLite + seed)
npm run serve                                        # outro terminal: http://127.0.0.1:5173
```

## Testes

```bash
cd backend && ../.venv/Scripts/python -m pytest      # unidade, científicos, integração, API, contrato
cd frontend && npm run typecheck && npm run lint && npm test
cd frontend && npx playwright install chromium && npm run e2e
```

Números atuais e o que cada suíte cobre: [TESTES_E_QA.md](docs/TESTES_E_QA.md).

## Produção

`cp .env.example .env`, preencha os segredos e rode `docker compose up -d --build`. Detalhes, rollback e o
que ainda não foi verificado: [DEPLOY.md](docs/DEPLOY.md). Segurança: [SEGURANCA.md](docs/SEGURANCA.md).

## Documentação

[Arquitetura](docs/ARQUITETURA_FINAL.md) · [Decisões (ADRs)](docs/DECISOES_TECNICAS.md) ·
[API](docs/API.md) · [Banco](docs/BANCO_DE_DADOS.md) · [Motor científico](docs/MOTOR_CIENTIFICO.md) ·
[Motor HEA](docs/MOTOR_HEA.md) · [Design system](docs/DESIGN_SYSTEM.md) · [Pendências](docs/PENDENCIAS.md) ·
[Histórico](docs/HISTORICO_DE_ALTERACOES.md) · [Gates](docs/REGISTRO_DE_GATES.md) ·
[Auditoria](docs/RELATORIO_AUDITORIA_GERAL.md) · [Requisitos](docs/REQUISITOS_BASE.md)
