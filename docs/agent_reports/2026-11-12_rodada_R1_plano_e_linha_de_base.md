# Rodada R1 (12/11/2026) — Plano, linha de base e controle de arquivos

Autor: Supervisor (Agente 01). Pedido de origem: documento do usuário "prompt aperfeiçoamento 12112026"
(8 seções: diagnóstico, 3D como elemento principal, estruturas e ligas, auditoria do HEA, termodinâmica,
gráficos e sincronização, referências, validação e entrega).

Este arquivo é o registro de G0 (requisitos) e a referência comum das delegações. Fatos abaixo foram
observados pelo supervisor nesta sessão; o que for hipótese está marcado.

## 1. Autorização e limites (dados pelo usuário)

- Autorizado: alterar código de `frontend/` e `backend/` e a documentação, dentro do escopo do pedido.
- NÃO autorizado: commit, push, deploy, migração de banco, exclusão de dados, mudança de infraestrutura.
- Proibido: `git checkout/restore/reset/stash/clean` (há muito trabalho não commitado a preservar);
  ler ou imprimir `.env`, tokens ou dados pessoais; alterar `_origem/` e `_auditoria/`.
- Mudança de contrato de API, esquema de banco ou fórmula científica exige parecer do especialista em
  `docs/agent_reports/` ANTES da implementação. Mudança de esquema de banco fica como pendência.
- Princípios: nenhum dado científico inventado (resultado com `procedencia`; sem base → `null` com motivo);
  a ciência roda só em `backend/app/engines/`; o front exibe e não recalcula; nada é "testado/validado"
  sem execução registrada.

## 2. Linha de base (medida em 12/11/2026)

- Commit base: `93755eb` (branch `main`), com 41 arquivos modificados e 14 caminhos não rastreados de
  trabalho anterior (reforma visual, `alloyScene.ts`, `AlloyPanels.tsx`, `stores/alloy.ts`, etc.).
- Frontend: `npm run typecheck` OK; `npm run lint` OK (115 arquivos TS/TSX, 6 CSS); `npm test` 83 aprovados, 0 falhas.
- Backend: `python -m pytest` terminou com código 0 (contagem exata registrada no relatório consolidado).
- Ambiente: Windows 10, Python 3.15.1 (venv em `.venv/`), FastAPI 0.162, pydantic 2.14, SQLAlchemy 2.1.
  NÃO há numpy, scipy, pycalphad nem base TDB no repositório ou no venv.
- Playwright com Chromium instalado (`npm run e2e`).

## 3. Diagnóstico inicial (fatos reproduzidos pelo supervisor)

Script de reprodução (TestClient, sem `.env`): ver seção 6.

### HEA (`backend/app/engines/hea/analitico.py`, motor 1.0.0)
- H-1 (falha de função): `dH`, `omega` e `gibbs` sempre `null`/`[]` → os dois gráficos do front
  (`HeaCharts.tsx`: mapa δ×ΔH e curva G×T) mostram só "indisponível". Causa registrada: Q-01 (não há
  entalpias binárias com fonte no repositório).
- H-2 (validação): elemento inexistente é aceito. `{"Xx":1,"Fe":1}` → 200 com ΔS calculado.
- H-3 (validação): `{"fe":1,"Fe":1,"Ni":1}` → 200; duplicata por caixa não é detectada.
- H-4 (ausente): não há conversão % atômica ↔ % em massa no HEA; a entrada é sempre molar.
- H-5 (cobertura): 15 metais (Fe Cr Mo W Cu Al Ni Ag Au Pb Mg Ti Zn Co Po). Sem Mn: a liga de Cantor
  devolve δ, T_m e VEC indisponíveis. `samples` do bootstrap é vazio.
- H-6 (interface): `HeaModule.tsx` trata qualquer veredito que não comece com "ESTÁVEL" como risco;
  a tabela "comparação com referência" subtrai o limiar do valor calculado.
- Correto e preservado: ΔS_mix ideal, δ, VEC, T_m por regra das misturas, política de dados, `indisponiveis`.

### Ligas (`backend/app/engines/crystallography/ligas.py`)
- L-1 (hipótese forte, a confirmar pelo especialista): o sorteio de soluto é feito sobre os átomos
  DESENHADOS (inclui imagens periódicas das faces da caixa). Ex.: Fe–Cr 12 %, n=2 → 35 esferas, 4 Cr.
  Imagens do mesmo átomo podem receber elementos diferentes e a contagem não corresponde à composição
  de uma supercélula periódica (16 átomos em CCC 2×2×2).
- L-2: só liga binária (base + 1 soluto). `{"solutos":[...]}` → 422. Fe–Cr–C não é representável.
- L-3: só o maior sítio intersticial por estrutura (octaédrico); sem tetraédricos; sem identificador,
  sítio ou ocupação por átomo; não há "composição efetivamente representada" explícita.
- L-4: nada sobre fases secundárias, limite de solubilidade ou sistemas multifásicos.

### Estruturas (`estruturas.py`, `celula.py`)
- E-1 (a avaliar): HC com c/a real < ideal e R = a/2 devolve FEA > 0,7405 (Mg 0,7446; Ti 0,7618),
  o que não é possível para esferas rígidas sem sobreposição.
- CS/CCC/CFC/HC ideais: n, NC e FEA conferem com os valores de livro (0,5236; 0,6802; 0,7405; 0,7405).

### Interface 3D (`frontend/src/modules/crystalab/*`, `features/viewer3d/*`)
- V-1: o viewer é um painel dentro de uma coluna rolável; há painel à esquerda (LabPanel) e à direita
  (9 abas). Pendência antiga T-16.
- V-2: seleção e inspeção funcionam só para a célula do metal puro; a cena de liga (`setThermalScene`)
  não é selecionável e o inspetor não conhece o elemento de cada átomo da liga.
- V-3: não há menu de aparência (cores por elemento/grupo/átomo, arestas e vértices), nem controle de
  tamanho/transparência/visibilidade, nem isolamento por elemento ou camada. Há corte por plano de Miller.
- V-4: coordenadas fracionárias em HC só para os átomos da base.

### Termodinâmica
- `thermodynamics/termico.py`: dilatação linear com α constante, Lindemann (f = 0,10), alotropia tabelada.
- Não existe motor CALPHAD, base TDB, nem energia de Gibbs de fases.

## 4. Tarefas e donos (um responsável por entrega)

| ID | Dono | Entrega | Arquivos permitidos |
|---|---|---|---|
| R1-HEA-01 | hea-specialist | Auditoria do HEA + especificação G1 | `docs/agent_reports/2026-11-12_auditoria_hea.md` |
| R1-CRI-01 | crystallography-engineer | Validação das 4 estruturas + especificação G1 de ligas | `docs/agent_reports/2026-11-12_parecer_cristalografia.md`, `backend/tests/unit/engines/test_validacao_estruturas.py` (novo) |
| R1-MAT-01 | materials-science-specialist | Parecer de termodinâmica e escopo do item 5 | `docs/agent_reports/2026-11-12_parecer_termodinamica.md` |
| R1-BIB-01 | academic-research-auditor | Relatório bibliográfico numerado + busca da fonte de ΔH binário | `docs/research/2026-11-12_*` |
| R1-FE-01 | frontend-engineer | 3D em área útil + barra lateral única recolhível | `frontend/` (exceto `modules/hea/*`, `services/api/*`) |
| R1-FE-02 | frontend-engineer | Aparência, filtros, seleção e inspeção (após FE-01) | idem |
| R1-API-01 | api-architect | Contrato das mudanças (após HEA-01, CRI-01, MAT-01) | `docs/architecture/2026-11-12_contrato_R1.md` |
| R1-BE-01 | backend-engineer | HEA conforme especificação e contrato | `backend/app/engines/hea/*`, schemas, serviços, testes |
| R1-BE-02 | backend-engineer | Ligas/estruturas conforme especificação e contrato (após BE-01) | `backend/app/engines/crystallography/*`, schemas, testes |
| R1-FE-03 | frontend-engineer | Consumo dos novos campos, gráficos e sincronização (após BE-02 e FE-02) | `frontend/` |
| R1-QA-01 | adversarial-qa-tester | QA adversarial das entregas | `docs/agent_reports/2026-11-12_qa_R1.md` |
| R1-INT-01 | integration-engineer | Regressão final e contrato | `docs/agent_reports/2026-11-12_integracao_R1.md` |

Serialização obrigatória: `frontend/src/modules/crystalab/*`, `frontend/src/features/viewer3d/*`,
`frontend/src/i18n/*`, `backend/app/api/v1/schemas.py`, `docs/openapi.json`.

## 5. Portões aplicáveis

G0 (este documento) · G1 (pareceres HEA/CRI/MAT + contrato API) · G2 (implementação com testes) ·
G3 (QA + parecer científico sobre o implementado + auditoria bibliográfica) · G4 (suíte completa e
contrato). G5 (liberação/publicação) NÃO se aplica: publicação não foi autorizada.

## 6. Reprodução da linha de base

`backend/` como diretório de trabalho, usando `fastapi.testclient.TestClient(create_app(Settings(_env_file=None)))`
e as rotas `POST /api/v1/hea/analyses`, `GET /api/v1/hea/bootstrap`,
`POST /api/v1/crystallography/solid-solutions` e `POST /api/v1/crystallography/cells`.
