# Registro de gates (Agente 05 §8 e §12)

A decisão final de cada gate é **humana** (responsável pelo projeto). O agente registra a recomendação técnica e as evidências.

## Gate 0 — Diagnóstico

| Campo | Valor |
|---|---|
| ID da revisão | G0-2026-11-02 |
| Etapa | Fase 1 — Auditoria |
| Decisão | **APROVADO COM RESSALVAS** (o usuário autorizou o avanço para a Fase 2 em 02/11/2026) |
| Critérios verificados | Inventário, testes reais (B 71+1; C typecheck ok, lint e 6/76 com falha de portabilidade), comparação de motores, contrato B↔C 15/15 |
| Evidências | `docs/RELATORIO_AUDITORIA_GERAL.md`, `_auditoria/*` (commit `7e82fcf`) |
| Ressalvas e responsável | Q-01 (motor HEA), Q-03 (validador científico) — responsável pelo projeto; E2E do C e pentest dinâmico não executados (L-04) |
| Módulos protegidos | `_origem/` (somente leitura) |
| Próxima etapa autorizada | Fase 2 |

## Gate 1 — Arquitetura

| Campo | Valor |
|---|---|
| ID da revisão | G1-2026-11-02 |
| Etapa | Fase 2 — Arquitetura |
| Decisão recomendada | **APROVADO COM RESSALVAS** — aguarda o responsável |
| Entregas | `ARQUITETURA_FINAL.md`, `DECISOES_TECNICAS.md` (ADR-001..017), `BANCO_DE_DADOS.md`, `API.md`, esqueleto do monorepo (`backend/`, `frontend/`, `database/`, `infrastructure/`, `scripts/` com READMEs) |
| Critérios verificados | Checklist A–K em ARQUITETURA_FINAL §12; cada RQ-ARQ, RQ-DAD, RQ-API e RQ-SEG tem dono, rota ou tabela; decisões com alternativas registradas |
| Evidência medida nesta fase | Tempo do motor B: 0,24–0,94 ms de mediana por chamada (base do ADR-003 e do ADR-012) |
| Riscos residuais | (1) PostgreSQL e Docker ausentes nesta máquina (L-01/L-02) bloqueiam testes de integração da Fase 3. (2) Seed científico entra majoritariamente como "aguardando validação" até Q-03. (3) HEA parcial até Q-01 |
| Ressalvas | Decidir Q-02 (hospedagem) antes da Fase 8; Q-04 (e-mail) antes de habilitar o cadastro público |
| Próxima etapa | Fase 3 — Backend e banco, depois da aprovação |

## Gate 1 — decisão

O responsável aprovou o Gate 1 e autorizou a Fase 3 em 02/11/2026 ("Sim, Fase 3"). Registrado como **APROVADO COM RESSALVAS** (as ressalvas listadas acima continuam valendo).

## Gate 2 — Implementação por domínio (Fase 3: motor, banco e serviços)

| Campo | Valor |
|---|---|
| ID da revisão | G2-F3-2026-11-02 |
| Etapa | Fase 3 — Backend e banco |
| Decisão recomendada | **APROVADO COM RESSALVAS** — aguarda o responsável |
| Entregas | Motor único (`engines/`), recursos da v1.4 com testes de referência, 36 modelos, migrações 0001–0002, repositórios JSON e SQL, carga de seed, `ServicoCalculo`, `Settings` por ambiente; `docs/BACKEND.md` e `docs/MOTOR_CIENTIFICO.md` |
| Testes e evidências | 206 aprovados / 22 pulados / 0 falhas; ruff limpo; ciclo de migração no SQLite; `alembic check` sem diferenças; DDL do PostgreSQL em `database/schemas/` |
| Achados durante a fase | (1) A/D arredondam a geometria HC antes de calcular (CR-08): diferença de ~5e-7 explicada no teste de regressão. (2) A v1.4 apresentava B2/L1₂ como fase para qualquer par (ex.: Fe–Cr real forma σ): agora é protótipo com aviso. (3) A v1.4 publicava densidade planar para planos não validados: agora oculta com motivo |
| Riscos residuais | Variantes PostgreSQL dos testes não executadas (L-01). Gemmi indisponível em Python 3.15. Seed do B usado em produção com aviso até a validação (decisão em MOTOR_CIENTIFICO §4) |
| Módulos protegidos | `backend/app/engines/` (mudanças só com teste de referência e regressão) |
| Próxima etapa | Fase 4 — API `/api/v1` sobre `ServicoCalculo`, aliases `/v1` e teste de contrato com o frontend |

## Gates das fases 4–10 (execução contínua autorizada)

O responsável aprovou as Fases 2, 3 e 4 uma de cada vez e depois autorizou "finalize as demais fases".
Por isso os gates abaixo foram executados em sequência, **sem pausa para aprovação humana entre eles**. Cada um
registra a recomendação técnica. A decisão formal de release (Gate 6) continua sendo do responsável.

| Gate | Fase | Commit | Recomendação | Evidências | Ressalvas |
|---|---|---|---|---|---|
| G2/3-F4 | 4 — API | `bd80d6f` | APROVADO | OpenAPI; contrato 34/34; testes de API | — |
| G2/3-F5 | 5 — Frontend | `a4c330d` | APROVADO | typecheck 0, lint ok, 76/76 (incl. adaptadores × backend real), build 200,8 kB gzip, contrato 34/34 | — |
| G4-F6 | 6 — Integração científica (Fluxo B) | `d75db0a` | APROVADO COM RESSALVAS | motor HEA testado à mão; banco = JSON; contrato 38/38 | ΔH_mix/Ω indisponíveis (Q-01); em prod só ΔS_mix até Q-03 |
| G3/4-F8a | 8 — Segurança | `f437ac8` | APROVADO COM RESSALVAS | 38 testes de conta/segurança; fluxo do front × backend real | sem SMTP (Q-04); limitador por processo; sem pentest externo |
| G4-F7 | 7 — Educacional (Fluxos C/E parciais) | `0ad16bd` | APROVADO COM RESSALVAS | 10 testes (gabarito não vaza, IDOR, escopo, progresso) | turmas, atribuições e notas sem rota (T-04/T-05) |
| G3/4-F8b | 8 — Infraestrutura | `92b5aad` | **PENDENTE DE EXECUÇÃO** | YAML validado; `alembic check` e CLI verificados | Docker/PostgreSQL/CI não executados aqui (L-01/L-02/Q-07) |
| G5 | 9 — Homologação | (Fase 10) | APROVADO COM RESSALVAS | backend 311/23 pulados/0 falhas; front 77/77; E2E 54/55 (1 intermitente) | variantes PostgreSQL e Linux só no CI |
| G6 | 10 — Release | (Fase 10) | **AGUARDA O RESPONSÁVEL** | 15 documentos do §16 + RELATORIO_ENCERRAMENTO | publicação depende de Q-02, Q-03 e Q-07 |
