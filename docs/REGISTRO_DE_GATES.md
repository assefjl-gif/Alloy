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
