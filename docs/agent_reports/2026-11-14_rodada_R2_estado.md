# Rodada R2 — ARQUIVO DE ESTADO (reescrito pelo Supervisor a cada etapa)

Continuacao da R1, encerrada e reportada em `2026-11-13_rodada_R1_relatorio_consolidado.md`.
Pendencias de origem: `docs/PENDENCIAS.md`, secao "Rodada R1 (13/11/2026)".
Pareceres e contrato que valem como G1 nesta rodada: `2026-11-12_auditoria_hea.md`,
`2026-11-12_parecer_cristalografia.md`, `2026-11-13_parecer_termodinamica.md`,
`docs/architecture/2026-11-12_contrato_R1.md` e `..._aprovacao_contrato_R1.md`.

Inicio: 14/11/2026. Uma retomada parte deste arquivo.

## Linha de base da R2 (medida pelo Supervisor em 14/11)

| Suite | Resultado |
|---|---|
| Backend `pytest` | 772 aprovados, 42 pulados, 0 falhas |
| Frontend `typecheck` / `lint` | sem erros / ok (120 TS/TSX, 6 CSS) |
| Frontend `npm test` | 83 aprovados, 0 falhas |
| Frontend `build` | inicial 712,8 kB (220,5 kB gzip) |
| Frontend `e2e` | 64 aprovados, 2 falhas: `etapa3-viewer.spec.ts:14` (3.5 CS/HC) e `alloy-thermal.spec.ts:46` (T-21) |

Metodo obrigatorio da E2E: roda contra `dist/`; `npm run build` imediatamente antes, sem outros processos
pesados (derruba workers sob carga, code 3221225794).

## Diagnostico ja feito (nao refazer)

**FE-05 / falha 3.5:** `metric-structure` e `metric-n` migraram para a secao recolhivel **Propriedades**
da barra lateral nova; o estado da barra e PERSISTIDO em `stores/crystalUi.ts`. Resultado: dependencia de
ordem entre specs. Isolado, CS (Po) e HC (Mg) falham; CCC (Fe) e CFC (Cu) passam. Erros observados:
`toBeAttached() failed / Expected: attached` e `toContainText() failed`. Correcao preferida: cada teste comeca
com estado conhecido da interface (limpar/semear `crystalUi` no fixture) ou revelar a secao explicitamente,
SEM enfraquecer a assercao (continua comparando contagem e tipos de atomo contra
`POST /api/v1/crystallography/cells`).

## Ordem da R2

| # | Item | Dono | Estado |
|---|---|---|---|
| 0 | FE-05: dependencia de ordem do 3.5 | frontend-engineer | CONCLUIDO (causa real era tempo, nao ordem) |
| 1 | T-25: front consumir os campos novos da API | frontend-engineer | CONCLUIDO |
| 2 | T-26 + T-28: correcoes do motor termico e protecao do FEA do HC | backend-engineer | CONCLUIDO |
| 3 | T-24 (selecao/inspecao na cena de ligas) + T-23 (filtros, cortes, isolamento) | frontend-engineer | EM ANDAMENTO |
| 4 | T-22: aparencia (cores por elemento/grupo/atomo, vertices e arestas, tamanho, transparencia, restaurar) | frontend-engineer | a fazer |
| 5 | T-23: filtros, cortes e isolamento para alcancar atomos internos | frontend-engineer | a fazer |
| 2.5 | D-R2-1 (zod do termico) | sessao principal | CONCLUIDO em 15/11 |
| 2.6 | D-R2-2 (selo da demo, Q-14), D-R2-3 (T-21 interface), D-R2-4 (T-27) | frontend-engineer | CONCLUIDO (R2-FE-02) |
| 2.7 | QA adversarial da API e dos motores | adversarial-qa-tester | CONCLUIDO (R2-QA-01): 6 defeitos, nenhum critico, veredito liberar com ressalvas (so backend) |
| 2.8 | Correcao dos defeitos QA-R2-02/03/04/06 | backend-engineer | EM ANDAMENTO |
| 7 | R1-QA-01 (QA adversarial) e R1-INT-01 (integracao formal) | adversarial-qa-tester, integration-engineer | a fazer |

Serializacao obrigatoria (colidem): `frontend/src/modules/crystalab/*`, `frontend/src/features/viewer3d/*`,
`frontend/src/i18n/*`, `frontend/src/services/api/*`. Nunca dois agentes nesses caminhos ao mesmo tempo.

## Bloqueado por dado externo (nao tratar como tarefa de codigo)

Q-01 (matriz de dH binario com fonte legivel), Q-08 (faixa de dH da zona do grafico), Q-09 (edicao e paginas
das citacoes), Q-10 (4 obras nao localizadas), Q-11 (CALPHAD). As decisoes Q-01 e Q-08 a Q-15 estao sendo
levadas ao usuario em paralelo; o resto avanca.

## Medicoes apos os itens 0-2 (verificadas pelos agentes; o Supervisor confere na proxima etapa)

| Suite | Resultado |
|---|---|
| Backend `pytest` | 827 aprovados, 42 pulados, **1 falha**: `tests/contract/test_contrato_frontend.py` (zod do front recusa `fator: null`) |
| Frontend `npm test` | 91 testes, 89 aprovados, 2 falhas (T-21 e o mesmo `fator: null`) |
| Frontend `e2e` | 66 testes, 63 aprovados, 3 falhas (T-21 + 2 que passam isoladas: carga) |
| Frontend `build` | 752,1 kB (232,0 kB gzip); meta < 300 kB gzip atingida |

Decisoes tomadas: `docs/architecture/2026-11-14_decisoes_R2.md` (D-R2-1 a D-R2-5).

## Correcao do diagnostico da falha 3.5

O frontend-engineer REFUTOU, com medicao, a hipotese do Supervisor (estado persistido de `crystalUi`):
o conteudo recolhido fica no DOM com `hidden` e cada teste Playwright tem contexto de navegador novo.
A causa real e fragilidade de TEMPO no primeiro carregamento da estrutura sob carga: o teste que falha
muda a cada execucao e todos passam isolados. Mitigado no fixture (semeia o estado da barra e espera a
estrutura chegar ao store). Investigar a causa raiz continua pendente (sugerido a integracao/DevSecOps).

## Codigo alterado na R2

- Backend (R2-BE-01): `engines/thermodynamics/termico.py` (motor 2.0.0), `engines/crystallography/geometria.py`
  (so o raio de contato do HC), `api/v1/schemas.py` e `rotas.py` (so o termico), testes, `docs/openapi.json`,
  `docs/MOTOR_CIENTIFICO.md`, `docs/API.md`.
- Frontend (R2-FE-01): `services/api/{contracts.ts,openapi.gen.ts,openapi-compat.ts}`, `modules/hea/*`,
  `modules/crystalab/*`, `features/viewer3d/alloyScene.ts`, i18n, estilos, testes; novos `modules/hea/display.ts`,
  `modules/crystalab/{alloyDisplay.ts,AlloyDetails.tsx}`, `i18n/nature.ts`, `i18n/source/08-contrato-r1.tsv`.

## Fechamento das duas falhas da R2 (15/11/2026, pela sessao principal)

Feito fora da delegacao, para desbloquear a R2 enquanto o limite de uso da API estava ativo.
O ponto de contrato que o Supervisor deixou em aberto foi decidido pelo principio do projeto
("o que nao tem base volta `null`, com o motivo") e pelo achado T-1 do parecer de termodinamica:
o motor esta certo ao devolver nulo acima da T_f; quem estava fora de sincronia era o zod do front.

**Falha A — `fator: null` recusado pelo zod (contrato).**

- `frontend/src/services/api/contracts.ts`: em `ThermalResult`, `fator`, `a_nm`, `delta_a_pct` e
  `delta_v_pct` passaram a `z.number().nullable()`. Declarados tambem os campos novos do motor 2.0.0:
  `acima_da_tf_nominal`, `tf_natureza`, `tf_rotulo`, `u_rotulo`, `dilatacao_isotropica`, `hipoteses`,
  `curva_dominio`, `indisponiveis`, `extrapolacao`, e `fonte` dentro de `notas`.
- `frontend/src/modules/crystalab/AlloyPanels.tsx`: os cartoes de rede e de dilatacao volumetrica
  mostram a CAUSA (de `indisponiveis`) junto do valor quando ele e nulo, em vez de um zero ou um
  traco sem explicacao (pedido secao 4). `VibrationCurve` deixa de desenhar grafico vazio quando a
  curva vem vazia: mostra o motivo de `indisponiveis.curva`.
- `frontend/tests/unit/alloy.test.ts`: as assercoes abaixo da T_f passaram a exigir nao-nulo
  explicitamente; teste novo "acima da T_f ... nulos COM causa, nunca zero" fixa o comportamento
  (os quatro campos nulos E com chave em `indisponiveis`; `a_ref_nm` continua, por ser dado tabelado).

**Falha B — T-21, intersticial com supercelula pequena.**

Confirmado no motor real (TestClient, rota `/api/v1/crystallography/solid-solutions`):
Fe-C 2 at% n=2 -> `n_soluto` 0 (16 unicos); x=4 n=2 -> 1 (17); 2 at% n=3 -> 1 (55); x=6 n=2 -> 1 (17).
O motor esta correto; a expectativa do teste estava velha. `alloy.test.ts` agora cobre os DOIS casos,
como a pendencia pedia: o teste de intersticial usa n=3 (onde 2 at% comporta 1 atomo) e um teste novo
fixa que 2 at% em 2x2x2 da 0 solutos, sem minimo forcado, e que a mesma composicao em 3x3x3 ja tem C.
Falta ainda a parte de INTERFACE da T-21: sugerir supercelula maior ao usuario quando a amostra der 0.

**Medicoes depois (executadas, 15/11/2026)**

| Suite | Antes (estado da R2) | Depois |
|---|---|---|
| Backend `pytest` | 827 aprovados, **1 falha** (contrato) | **828 aprovados, 42 pulados, 0 falhas** |
| Contrato `contrato_frontend.mts` | recusava `fator: null` | **46/46 respostas aceitas** (API 0.9.0) |
| Frontend `typecheck` / `lint` | — | sem erros / ok (124 TS/TSX, 6 CSS) |
| Frontend `npm test` | 91 testes, 89 aprovados, **2 falhas** | **93 testes, 93 aprovados, 0 falhas** |

NAO reexecutado aqui: `npm run build` e `npm run e2e` (a E2E precisa de build imediatamente antes e de
maquina ociosa). As 3 falhas de E2E registradas acima incluem a T-21, cuja causa foi resolvida no teste
unitario; conferir na proxima execucao da E2E se `alloy-thermal.spec.ts:46` ainda falha.


## Situacao em 15/11/2026, 15:45 (Supervisor)

### Decisoes sobre os 6 defeitos do QA (texto integral em `docs/architecture/2026-11-14_decisoes_R2.md`)

| Defeito | Severidade | Decisao |
|---|---|---|
| QA-R2-01 (politica de dado nao validado: `/cells` devolve valor em producao, termico e HEA recusam) | alta | **ESCALADO AO USUARIO** (pendencia Q-16). Nao alterar em nenhuma direcao. Alinhar ao principio 3 desligaria o CrystaLab em producao (nenhum dado validado hoje, Q-03); manter a excecao exige escrever a ressalva. Recomendacao do Supervisor: manter com a excecao documentada e reverter quando Q-03 for resolvida. D-R2-6 |
| QA-R2-02 (procedencia vazia em `/cells` e `/density`) | media | CORRIGIDO (R2-BE-02) |
| QA-R2-03 (mensagem de erro em ingles vazando a regex interna) | media | CORRIGIDO (R2-BE-02) |
| QA-R2-04 (`details[].loc` com indice de lista como texto) | baixa | CORRIGIDO na API (R2-BE-02); consolidar no motor fica como P-1 |
| QA-R2-06 (truncamento do valor ecoado nao uniforme) | baixa | CORRIGIDO, uniformizado em 16 caracteres (R2-BE-02) |
| QA-R2-05 (banco sem migracao devolve 500) | baixa | PENDENCIA T-30 (operacao, nao motor) |

Tambem registrado: D-R2-8 — divergencia do Ti entre `/cells` (a=0,2951; rho=4,5005) e `/solid-solutions`
(a=0,2890; rho=4,7915), 6,5 % no mesmo metal em duas telas. E a mudanca V-14, nao aprovada: segue como Q-13,
agora com evidencia de impacto visivel ao usuario.

### Estado das frentes

- R2-BE-02 (defeitos do QA): **CONCLUIDA**. Suite backend **850 aprovados, 42 pulados, 0 falhas**; contrato 46/46.
  Pedidos de ratificacao do agente: usou `services/calculo.py` e `schemas.py` fora da lista (justificado: o bloco de
  procedencia de `/cells` e `/density` e montado no servico, nao no motor) — **ratificado pelo Supervisor**.
  Pendencias dele: P-1 (loc inteiro no motor), P-2 (nomes dos 3 codigos novos de `dados_usados`), P-3 (escopo do
  truncamento), P-4 (`fontes_modelo` x `fontes_dados` em /cells), P-5 (procedencia tambem falta no termico).
- R2-FE-03 (T-24 + T-23): **INTERROMPIDA por limite de uso, com a arvore QUEBRADA**. `npm run typecheck` tem
  exatamente 2 erros: `modules/crystalab/FilterPanel.tsx` linhas 140 e 141 usam as chaves de i18n `filter.occupancy`
  e `filter.sites`, que nao existem no catalogo. O relatorio do agente diz "feito: so o passo 1", mas o disco mostra
  MUITO mais: criados `features/viewer3d/{visibility.ts,sceneFilterState.ts}` e `modules/crystalab/FilterPanel.tsx`;
  alterados `features/viewer3d/{SceneController.ts,Viewer3D.tsx}` e
  `modules/crystalab/{SidePanels.tsx,ViewerPanel.tsx}`. Relancada para concluir.
- Itens ainda nao iniciados: T-22 (aparencia: cores por elemento/grupo/atomo, vertices e arestas, tamanho,
  transparencia, restaurar padrao); `demo_permitido` nao respeitado pelo front (bloqueio relatado na R2-FE-02);
  variante do selo em `SidePanels.tsx:343,357` e `ProvenancePanel.tsx:110`; integracao formal (R1-INT-01);
  QA de frontend/E2E e rodada com PostgreSQL + gemmi (o QA so cobriu backend/API).


## ENCERRAMENTO DA R2 (15/11/2026, Supervisor)

### Achado novo da integracao e decisao

**F-1 (alta, confirmado empiricamente pelo integration-engineer).** `services/calculo.py` inseria
`ExecucaoCalculo(motor_codigo, motor_versao, ...)` sem garantir a linha correspondente em `motores`. Como existe a
chave estrangeira composta `fk_execucoes_calculo_motor` e as versoes dos motores mudaram nesta rodada
(crystallography 2.1.0, thermodynamics 2.0.0, hea 2.0.0), um banco carregado ANTES destas entregas nao tem a linha
nova: a insercao viola a FK e, por estar na MESMA transacao do calculo, **o calculo inteiro falhava com HTTP 500**
para usuario autenticado. Anonimo nao era afetado. Pior do que o previsto em Q-15, que falava so em perda do historico.

**F-2 (media).** A aplicacao nao habilitava `PRAGMA foreign_keys` em SQLite: em desenvolvimento a FK nao era
aplicada, e foi por isso que nenhuma suite pegou o F-1.

**Decisao do Supervisor:** corrigir no CODIGO, sem tocar em banco. Nada de migracao, de alteracao de esquema nem de
execucao de seed contra banco do projeto — isso continua dependendo do usuario (Q-15). Tres exigencias:
(1) gravar historico e efeito secundario e NUNCA pode derrubar o resultado cientifico; (2) registro idempotente do
motor antes de referencia-lo, seguro sob concorrencia, reaproveitando o conhecimento da tabela que ja existe no seed;
(3) impor a FK em SQLite para que defeitos assim aparecam em teste, sem relaxar nenhuma verificacao se surgirem
violacoes latentes.

**Resultado (R2-BE-03, concluida):** correcao feita nos tres pontos, sem migracao e sem mexer em esquema. O aviso de
historico nao gravado entra em `procedencia.avisos`, que ja e contratado e exibido — zero campo novo de contrato.
`PRAGMA foreign_keys=ON` nao revelou nenhuma outra violacao latente nas 309 provas de API e integracao.
Um teste existente afirmava o proprio defeito (`test_id_de_usuario_inexistente_falha_na_chave_estrangeira`, exigindo
`IntegrityError`): foi reescrito para exigir que o calculo NAO caia. Nenhum valor cientifico mudou.

### Itens que o coordenador listou como abertos e que JA estavam fechados (conferidos pelo Supervisor)

| Item | Situacao real |
|---|---|
| Arvore quebrada: 2 erros em `FilterPanel.tsx:140,141` (`filter.occupancy`, `filter.sites`) | FECHADO na relanca da R2-FE-03: as chaves entraram na fonte TSV nos tres idiomas e o catalogo foi regerado. Typecheck limpo, conferido 3 vezes |
| T-22 (aparencia) nunca comecou | CONCLUIDA (R2-FE-04): cor por elemento, grupo e atomo; cor de vertices e arestas; tamanho e transparencia; marcadores geometricos distinguiveis por acabamento (arame x esfera solida); restaurar por secao e geral; legenda coerente |
| Selo do modo demonstrativo (Q-14) | CONCLUIDO (R2-FE-02): selo junto de cada valor, grafico e tabela de origem demonstrativa, visualmente distinto do selo "Ilustrativo"; a demo deixou de sortear veredito |
| `demo_permitido` nao respeitado pelo front | CONCLUIDO (R2-FE-04): indisponivel vira `disabled`, nunca `demo`, mesmo com preferencia local ligada |
| `npm run build` e `npm run e2e` nao reexecutados | REEXECUTADOS: build 813,5 kB (249,5 kB gzip, meta < 300 kB); E2E 74 aprovados / 0 falhas, confirmado tambem pelo integration-engineer |

### Suites no encerramento da R2 (executadas pelo Supervisor)

| Suite | Linha de base da R2 | Encerramento |
|---|---|---|
| Backend `pytest` | 772 aprovados, 42 pulados | **864 aprovados, 51 pulados, 0 falhas** |
| Contrato front-back | 46/46 | **46/46** |
| Frontend `typecheck` / `lint` | limpo / 120 TS/TSX | limpo / **132 TS/TSX** |
| Frontend `npm test` | 83 aprovados | **107 aprovados, 0 falhas** |
| Frontend `build` | 712,8 kB (220,5 kB gzip) | **813,5 kB (249,5 kB gzip)** |
| Frontend `e2e` | 64 aprovados, 2 falhas | **74 aprovados, 0 falhas** (medido duas vezes de forma independente: pelo integration-engineer e pelo Supervisor, cada um com `npm run build` imediatamente antes) |

Os 9 pulados a mais sao parametros PostgreSQL (limitacao L-01: nao ha PostgreSQL nesta maquina).

### Veredito dos portoes

G2 (implementacao) e G3 (validacao): cumpridos para backend/API/motores, com QA adversarial independente
(`2026-11-15_qa_R2.md`, 6 defeitos, nenhum critico, 4 corrigidos). G4 (integracao):
**integrado com ressalvas** (`2026-11-15_integracao_R2.md`). G5 (liberacao): **NAO atingido** e nem solicitado —
publicacao nao foi autorizada pelo usuario.

### RISCO DE PROCESSO MAIS URGENTE (decisao do usuario)

Nao existe ponto de retorno. Sao 153 entradas nao commitadas na arvore, misturando R1, R2 e trabalho anterior do
proprio usuario. Nao ha rollback seletivo possivel por git, e qualquer `git restore/checkout/reset/stash/clean`
destroi tudo de forma irrecuperavel. O Supervisor NAO tem autorizacao para commitar. Recomendacao: autorizar a criacao
de um ponto de retorno (commit numa branch de integracao ou copia integral da arvore) ANTES de qualquer nova rodada.

### Pendencias que seguem abertas

Q-01, Q-03, Q-08 a Q-13, Q-15, Q-16 (politica de dado nao validado em `/cells`), T-30 (500 com banco sem migracao),
P-1 a P-5 do backend, F-4 (`fracoes_massa` validado e nao usado), e as validacoes que faltam: QA de frontend/E2E,
parecer pedagogico das telas novas, PostgreSQL, Docker, desempenho sob carga, acessibilidade com leitor de tela e
**toda a validacao visual em navegador**.
