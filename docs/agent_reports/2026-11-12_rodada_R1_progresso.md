# Rodada R1 — ARQUIVO DE ESTADO (reescrito pelo Supervisor a cada etapa)

Plano e achados iniciais: `2026-11-12_rodada_R1_plano_e_linha_de_base.md`.
Decisoes G1: `docs/architecture/2026-11-12_decisoes_G1_R1.md`.
Contrato: `docs/architecture/2026-11-12_contrato_R1.md` · aprovacao: `..._aprovacao_contrato_R1.md`.
Uma retomada parte deste arquivo. Nao refazer o que esta em "Concluido".

Ultima atualizacao: 13/11/2026 (fim da rodada R1). Interrupcoes por limite de uso (429): 5.
RELATORIO FINAL: `2026-11-13_rodada_R1_relatorio_consolidado.md`.

## Linha de base de testes (ANTES de qualquer alteracao de codigo)

| Suite | Resultado |
|---|---|
| Backend `pytest` | 401 aprovados, 42 pulados, 0 falhas |
| Frontend `typecheck` / `lint` | sem erros / ok (115 TS/TSX, 6 CSS) |
| Frontend `npm test` | 83 aprovados, 0 falhas |
| Frontend `build` | ok (inicial 693,1 kB; 215,8 kB gzip) |
| Frontend `e2e` (maquina ociosa) | 60 aprovados, 1 falha PREEXISTENTE: `flow-b-miller.spec.ts:57` (B3) |

A E2E derruba workers (code 3221225794) sob carga: rodar sozinha.

## Medicoes DEPOIS (verificadas pelo Supervisor)

| Suite | Resultado | Quando |
|---|---|---|
| Backend `pytest` | **631 aprovados, 42 pulados, 0 falhas** | apos R1-BE-01 e os 64 testes de estruturas |
| Frontend `typecheck` / `lint` | sem erros / ok (120 TS/TSX) | apos R1-FE-01 |
| Frontend `npm test` | 83 aprovados, 0 falhas | apos R1-FE-01 |
| Frontend `build` | ok (inicial 712,8 kB; 220,5 kB gzip) | apos R1-FE-01 |
| Frontend `e2e` | **63 aprovados, 3 falhas NOVAS** (B3 preexistente passou a aprovar) | apos R1-FE-01 |

As 3 falhas novas tem causa unica: o selo `demo-seal` ("Ilustrativo") saiu de dentro de
`viewer-stage` e passou para `.cl-hud__notices` (SceneHud.tsx:125-126), irmao do palco.
O rotulo continua existindo e visivel sobre a cena; as specs afirmam a relacao de DOM.
Specs: `etapa3-viewer.spec.ts:145`, `etapas5-7.spec.ts:34`, `viewer-didactics.spec.ts:36`.

## Concluido

| ID | Agente | Artefato |
|---|---|---|
| R1-HEA-01 | hea-specialist | `2026-11-12_auditoria_hea.md` — 22 achados (A-01..A-22) + especificacao G1 |
| R1-CRI-01 | crystallography-engineer | `2026-11-12_parecer_cristalografia.md` + `backend/tests/unit/engines/test_validacao_estruturas.py` (64 testes) |
| R1-API-01 | api-architect | `docs/architecture/2026-11-12_contrato_R1.md` (aprovado com ressalvas) |
| R1-BE-01 | backend-engineer | **CONCLUIDA** (motor HEA 2.0.0). Relatorio `2026-11-12_backend_BE-01.md`. Suite 631/0 conferida pelo Supervisor. NAO remandar |
| G0, G1 | Supervisor | plano, decisoes, aprovacao do contrato |

## Em andamento

| ID | Agente | Estado real |
|---|---|---|
| R1-FE-01 | frontend-engineer | CONCLUIDA (fechada em 13/11). Layout novo implementado e gravado (StageLayout, Sidebar, SceneHud, cameraApi, crystalUi, 07-stage.tsv, crystalab-layout.spec.ts). Falta: corrigir as 3 falhas de E2E, `docs/FRONTEND.md`, fechar o relatorio (o arquivo `2026-11-12_frontend_FE-01.md` ainda diz "nenhum arquivo") |

## A fazer (ordem de prioridade)

1. Fechamento da R1-FE-01 (3 falhas de E2E + docs + relatorio).
2. R1-BE-02 — ligas e FEA do HC (supercelula periodica, realizacao estatistica, multicomponente, campos por atomo).
3. R1-FE-02 — aparencia (cores, tamanho, transparencia), filtros/isolamento, selecao e inspecao na cena de ligas.
4. R1-FE-03 — HEA no front (graficos G-A e G-B, triagem, base massica) e ligas multicomponentes.
5. R1-MAT-01 — parecer de termodinamica (nao iniciado; 1a tentativa interrompida).
6. R1-BIB-01 — relatorio bibliografico e fonte de dH binario (nao iniciado).
7. R1-QA-01, R1-INT-01, consolidacao, HISTORICO_DE_ALTERACOES.md, PENDENCIAS.md.

## Codigo de producao alterado nesta rodada

- Backend (R1-BE-01): `app/engines/hea/analitico.py` (reescrito, 2.0.0), `app/api/erros.py`,
  `app/api/v1/schemas.py`, `app/api/v1/rotas.py`, `app/services/calculo.py`; novos
  `app/engines/hea/{entrada,erros,referencia,textos}.py`,
  `app/repositories/{identidade_elementos,entalpias_json}.py`; testes; `docs/openapi.json`,
  `docs/API.md`, `docs/MOTOR_HEA.md`, `scripts/contrato_frontend.mts` (so o caso Xx).
- Frontend (R1-FE-01): ver tabela "Em andamento".
- Nenhum seed, nenhuma migracao, nenhum commit.

## Risco aberto (encaminhado pelo backend-engineer)

`execucoes_calculo` tem FK para `motores(codigo, versao)`. Num banco carregado antes desta entrega
nao existe a linha ('hea','2.0.0'); com usuario autenticado, gravar o historico de uma analise HEA
pode falhar. `python -m app.cli seed` registra a versao nova (leitura de `seed_sql.py`), mas isso
NAO foi executado em banco existente. Decidir com o database-engineer antes de publicar.

## Encerramento da rodada R1 (13/11/2026)

Concluidas: R1-HEA-01, R1-CRI-01, R1-API-01, R1-BE-01, R1-BE-02, R1-FE-01 (+ fechamento), R1-FE-04,
R1-MAT-01, R1-BIB-01 (parcial: extracao de dH bloqueada).
NAO executadas: R1-FE-02 (aparencia, filtros, selecao em ligas), R1-FE-03 (front consumir os campos novos),
R1-QA-01 (QA adversarial), R1-INT-01 (integracao formal). Viraram T-22 a T-25 em PENDENCIAS.md.

Suites no encerramento: backend 772 aprovados / 42 pulados / 0 falhas; contrato 46/46; frontend typecheck,
lint e unitarios limpos; build ok; E2E ver o relatorio consolidado §3.1.

Proxima rodada deve comecar por: T-25 (front consumir a API nova), T-22/T-23/T-24 (aparencia, filtros,
selecao em ligas), T-21 (intersticial com supercelula pequena), T-26 (correcoes do motor termico) e as
decisoes Q-01, Q-11 a Q-15.
