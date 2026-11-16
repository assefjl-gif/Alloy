# R2-INT-01 — Integração formal (portão G4)

- Agente: integration-engineer (Agente 06)
- Data: 2026-11-15
- Estado: EM EXECUÇÃO (gravação incremental; pode ser interrompida por limite de API)
- Linha de base: branch `main`, 153 entradas em `git status --porcelain`, nenhum commit das rodadas R1/R2.
- Último commit: 93755eb "Banco de dados: tabela periódica completa (118 elementos) e cache de retratos"

## 1. Tabela de execução

| # | Comando | Saída resumida | Resultado | Tempo |
|---|---|---|---|---|
| (preenchido abaixo conforme execução) | | | | |

### Execuções confirmadas (saída real colada)

**(a) Backend — suíte completa**
```
$ cd backend && ../.venv/Scripts/python -m pytest -o addopts="-p no:cacheprovider" -q
...
850 passed, 42 skipped, 1 warning in 66.16s (0:01:06)
exit=0
```
Resultado: APROVADO. Confirma a medição do Supervisor (850/42/0). Tempo medido: 69 s de parede.
Aviso único (não bloqueante): `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead` (fastapi/testclient.py).

**(b) Teste de contrato**
```
$ cd backend && ../.venv/Scripts/python -m pytest tests/contract -s -o addopts="-p no:cacheprovider"
tests\contract\test_contrato_frontend.py 46/46 respostas aceitas pelos schemas do frontend (API 0.9.0)
1 passed in 3.32s
```
Resultado: APROVADO, 46/46 — contagem inalterada em relação à última medição. Nenhum caso mudou.

**(c) OpenAPI versionado vs. reexportado**
Script `scripts/exportar_openapi.py` escreve direto em `docs/openapi.json`; para não sobrescrever o versionado
reexportei por cópia equivalente no scratchpad (`export_tmp.py`, mesmo `create_app(Settings(env="dev"))`,
mesmo `indent=1`, newline LF).
```
$ .venv/Scripts/python <scratchpad>/export_tmp.py <scratchpad>/openapi_reexportado.json
37 rotas, 115 schemas -> ...\openapi_reexportado.json
$ diff -u docs/openapi.json <scratchpad>/openapi_reexportado.json
(sem saída; exit=0)
```
Resultado: APROVADO — `docs/openapi.json` está em sincronia byte a byte com o código (37 rotas, 115 schemas).

**(d) Frontend — typecheck + lint + testes unitários**
```
$ cd frontend && npm run typecheck && npm run lint && npm test
> tsc --noEmit -p tsconfig.json && tsc --noEmit -p tsconfig.sw.json && tsc --noEmit -p tsconfig.node.json
(sem erros; exit=0)
> node scripts/lint.mjs
lint: ok (132 arquivos TS/TSX, 6 CSS, 9 regras)
ℹ tests 107  ℹ pass 107  ℹ fail 0  ℹ skipped 0  ℹ duration_ms 8409.6623
```
Resultado: APROVADO. 107/107, 0 falhas. Confirma a medição do Supervisor. Tempo: 32 s os três juntos.

**(e) Build de produção**
```
$ cd frontend && npm run build
build production 20261115195846: inicial 813.5 kB (249.5 kB gzip, Three no inicial: não) · 29 arquivos sob demanda · 103 no pré-cache
```
Resultado: APROVADO, 3 s. Confirma 813,5 kB / 249,5 kB gzip do relatório R2-FE.

**(f) E2E (executada sozinha, imediatamente após o build, contra `dist/`)**
```
$ npx playwright test
  ...
  ok 74 [chromium] › tests\e2e\viewer-didactics.spec.ts:53:1 › ABP Al × Cu: hipóteses, evidências dos três tipos e conclusão registrada no caderno (2.3s)

  74 passed (5.3m)
```
Resultado: APROVADO, 74/74, 0 falhas. Tempo de parede 322 s. Nenhum worker caiu (máquina dedicada, conforme instrução).

**(g) Orçamento de bundle**
```
$ cd frontend && npm run measure
bundle inicial: 813.5 kB (249.5 kB gzip) · Three no inicial: não · meta < 300 kB gzip: ATINGIDA
maiores sob demanda: Viewer3D 136.7 kB · dist-OL3IBSNW 127.9 kB · katex 75.1 kB · fontes woff2 ~23 kB cada
```
Resultado: APROVADO. 249,5 kB gzip < 300 kB. Three.js fora do carregamento inicial.

### Resumo da tabela de execução

| # | Comando | Saída resumida | Resultado | Tempo |
|---|---|---|---|---|
| a | `backend: pytest` | 850 passed, 42 skipped, 0 failed | APROVADO | 66 s |
| b | `backend: pytest tests/contract -s` | 46/46 respostas aceitas (API 0.9.0) | APROVADO | 3,3 s |
| c | reexport OpenAPI + `diff` | sem diferenças (37 rotas, 115 schemas) | APROVADO | 5 s |
| d | `frontend: typecheck && lint && test` | 0 erros; lint ok (132 TS/TSX); 107/107 | APROVADO | 32 s |
| e | `frontend: npm run build` | inicial 813,5 kB (249,5 kB gzip) | APROVADO | 3 s |
| f | `frontend: npx playwright test` | 74 passed | APROVADO | 322 s |
| g | `frontend: npm run measure` | 249,5 kB gzip, meta < 300 kB ATINGIDA | APROVADO | 2 s |

## 2. Contrato e OpenAPI

- **Contrato zod vs. respostas reais:** 46/46 aceitas (API 0.9.0). Nenhum caso mudou em relacao a ultima medicao.
  O teste sobe uvicorn real e roda `scripts/contrato_frontend.mts` com os schemas zod do proprio frontend.
- **OpenAPI versionado:** `docs/openapi.json` identico ao reexportado (37 rotas, 115 schemas). O versionado NAO foi
  sobrescrito: reexportei para o scratchpad e comparei com `diff`.
- **Verificacao reversa de nomes de campo** (minha, alem do que o QA fez): extrai os 242 campos declarados nos
  schemas zod de `frontend/src/services/api/contracts.ts` e comparei com as 379 propriedades do OpenAPI:
  0 campos zod sem correspondencia. Nenhum campo exibido pela interface foi removido ou renomeado no backend.
  (Checagem de nomes; a checagem de forma e caminho e o teste de contrato acima.)

## 3. Coerencia por campo (respostas reais do backend)

Metodo: `TestClient` sobre `create_app(Settings(env="dev"))`, chamadas reais a cada rota, inspecao do JSON devolvido
(scripts no scratchpad: `probe2.py`, `probe3.py`). Consumo no front: presenca em `contracts.ts` mais arquivo de UI que le o campo.

| Campo | Backend devolve? | Front consome? | Observacao |
|---|---|---|---|
| `triagem.estado` (HEA) | SIM - "inconclusiva" em FeCoNiCrMn | SIM | coerente; inconclusiva por falta de raio de Mn |
| `criterios` (HEA) | SIM - lista com `codigo`, `limiar`, `unidade`, `natureza`, `fonte`, `verificada`, `atende`, `aplicavel` | SIM (2 arquivos UI) | rotulo e limiar vem do motor, nao do front |
| `curva_T` (HEA) | SIM - pontos `{T, menos_TdS, dG}`, com `dG: null` quando falta dH | SIM | front so desenha dG quando todos os pontos tem valor |
| `indisponiveis` (HEA) | SIM - motivo textual por grandeza (`delta`, `raio_medio_nm`, `Tm`) | SIM (5 arquivos UI) | motivos nomeiam o elemento faltante (Mn) |
| bases de composicao (HEA): `base_entrada`, `fracoes`, `fracoes_massa`, `comp_massa_pct`, `comp_percent` | SIM - `base_entrada="atomica"`; `fracoes` preenchido; `fracoes_massa` e `comp_massa_pct` = `null` na base atomica | PARCIAL | `fracoes_massa` esta no zod mas NAO e lido por nenhum componente de UI (`comp_massa_pct` e o usado). Campo a mais, nao a menos: nao quebra nada |
| `composicao` solicitada x representada (ligas) | SIM - `composicao.solicitada[]` e `composicao.representada[]` com `at_pct` e `massa_pct` | SIM | coerente |
| `realizacao` (ligas) | SIM - `{tipo:"estatistica", semente, algoritmo:"mt19937-chaves-v1", n, aviso}` | SIM | aviso de "uma realizacao entre muitas" presente |
| `imagem` / `imagem_de` (ligas) | SIM - POR ATOMO, nao no topo: 64 de 172 atomos com `imagem=true` e `imagem_de` apontando o id de origem | SIM (`AlloyAtomInspector.tsx`, com botao "ir para a origem") | coerente |
| `id`, `pos_nm`, `frac_celula`, `ocupacao`, `sitio`, `fase` (por atomo) | SIM - todos presentes; `sitio` e objeto `{nome, wyckoff, nc, nc_txt}` | SIM | coerente em substitucional (Cu-Ni) e intersticial (Fe-C) |
| `fea_modelo` (celulas) | SIM - "esferas_rigidas" em CFC, CCC e HC | SIM | coerente |
| `raio_contato_rel`, `contato_tipo` | SIM - HC Zn: `0.5` / "basal"; CFC e CCC: `null` (contato unico, sem ambiguidade) | SIM | nulo por desenho, nao por falha |
| `c_a_ideal` | SIM - HC: `1.632993...`; CFC/CCC: `null` | SIM | coerente |
| `vizinhos` | SIM - HC: `[{basal, n=6, d_rel=1.0}, {entre_planos, n=6, d_rel=1.0929}]`; CFC/CCC: `null` | SIM | coerente |
| `nc_txt` | SIM - CFC "12", CCC "8", HC "6 + 6" | SIM (3 arquivos) | o "6 + 6" do HC e o ponto didatico da entrega 2.1.0 |
| `fator`, `a_nm`, `delta_a_pct`, `delta_v_pct` (termico) | SIM - Cu@800 C com valores; Ti@2000 C e Fe@1600 C todos `null` | SIM | coerente |
| `indisponiveis` (termico) | SIM - acima da T_f traz motivo por campo: "acima da T_f do modelo nao ha ordem cristalina de longo alcance: parametro de rede, densidade cristalina e dilatacao da celula nao tem significado fisico" | SIM | cada campo anulado tem motivo nomeado, como exigido |
| `demo_permitido` (capabilities) | SIM - `crystallography:false`, `thermodynamics:false`, `hea:true` (dev) | SIM (`stores/capabilities.ts`) | coerente com FE-04 |

Conclusao do item 3: nenhuma divergencia de campo entre backend e frontend. A unica observacao e um campo
devolvido e validado mas nao exibido (`fracoes_massa`), que nao quebra contrato nem interface.

## 4. Versoes e caminhos de dados

### Versoes declaradas
```
$ GET /api/v1/meta/version
{"api": "0.9.0",
 "motores": {"crystallography": "2.1.0", "thermodynamics": "2.0.0", "hea": "2.0.0"},
 "versao_dados": "2026.10.1+2026.11.1-v14+2026.11.2-hea"}
```
`procedencia.versao_motor` nas respostas reais: cells e solid-solutions = 2.1.0; thermal = 2.0.0; hea = 2.0.0.
`/api/v1/meta/capabilities` repete as mesmas tres versoes. Coerente em todos os pontos - VERIFICADO.

### Banco NOVO (verificado)
```
$ DATABASE_URL=sqlite+pysqlite:///<scratchpad>/int_novo.db python -m app.cli preparar
Running upgrade  -> 0001 / 0001 -> 0002 / 0002 -> 0003
migracoes aplicadas (head)
seed: {'fontes': 6, 'elementos': 118, 'materiais': 18, 'valores': 890, 'estruturas_material': 22}
$ select codigo,versao,ativo from motores
[('crystallography','2.1.0',1), ('hea','2.0.0',1), ('thermodynamics','2.0.0',1)]
```
Historico de usuario autenticado (login + cabecalho `X-Alloy-CSRF`, quatro calculos reais):
```
cells -> 200 | thermal -> 200 | hea -> 200 | solid-solutions -> 200
GET /api/v1/me/history -> 200 {"total":4,...}
select motor_codigo, motor_versao, count(*) from execucoes_calculo group by 1,2
[('crystallography','2.1.0',2), ('hea','2.0.0',1), ('thermodynamics','2.0.0',1)]
```
Banco novo: APROVADO. Sem risco.

### Banco PREEXISTENTE - risco Q-15 CONFIRMADO (sem migrar, sem tocar em dado do projeto)
`app/services/calculo.py:224` insere `ExecucaoCalculo(motor_codigo, motor_versao, ...)` sem get-or-create da linha
em `motores`. A FK composta existe:
```
database/migrations/versions/0001_esquema_inicial.py:358
sa.ForeignKeyConstraint(['motor_codigo','motor_versao'], ['motores.codigo','motores.versao'],
                        name='fk_execucoes_calculo_motor', ondelete='RESTRICT')
```
Simulei um banco anterior as entregas numa COPIA DE SCRATCH (`int_antigo.db`, criada por mim; nenhum banco do
projeto foi lido, migrado ou alterado), com `motores` contendo so as versoes 1.0.0, e com `PRAGMA foreign_keys=ON`
para emular o PostgreSQL, que sempre aplica FK:
```
motores na copia antiga: [('crystallography','1.0.0'),('hea','1.0.0'),('thermodynamics','1.0.0')]
login -> 200
POST /api/v1/crystallography/cells (autenticado) -> sqlite3.IntegrityError: FOREIGN KEY constraint failed
   -> "erro interno [359193920d9443c2a5e978816eb7c6f8] em POST /api/v1/crystallography/cells" (HTTP 500)
```
Impacto maior do que "o historico falharia": o CALCULO INTEIRO falha com 500 para o usuario autenticado, porque a
gravacao acontece dentro da mesma transacao da requisicao. Calculo anonimo nao e afetado (`usuario_id is None`).

Agravante secundario: a aplicacao NAO habilita `PRAGMA foreign_keys` em SQLite
(`grep -rn foreign_keys backend/app` nao retorna nada; `pragma foreign_keys` no banco novo devolve `0`).
Em SQLite a FK nao e aplicada e a linha entraria com referencia pendente; em PostgreSQL seria 500. O comportamento
divergem entre dev (SQLite) e producao (PostgreSQL) - o defeito nao aparece em dev, o que explica por que nenhuma
suite o pegou.

Remediacao verificada, sem migracao e sem exclusao: `python -m app.cli seed` e idempotente e so insere o que falta
(`app/repositories/seed_sql.py:107-109` faz `sessao.get(Motor, (codigo, versao)) is None` -> `add`). Rodado na copia antiga:
```
seed: {'fontes': 0, 'elementos': 0, 'materiais': 0, 'valores': 0, 'estruturas_material': 0}
motores depois do seed: crystallography 1.0.0 + 2.1.0 | hea 1.0.0 + 2.0.0 | thermodynamics 1.0.0 + 2.0.0
```
Portanto o procedimento de liberacao precisa exigir `app.cli seed` (ou `preparar`) ANTES de expor a versao nova.
NAO executei nada contra banco do projeto.

O que NAO foi verificado neste item: PostgreSQL real (so emulei a aplicacao de FK em SQLite); nenhum banco de
producao ou de desenvolvimento preexistente do projeto foi aberto; nao executei migracao alguma.

## 5. Plano de reversao (descrito, NAO executado)

Nada foi commitado: as rodadas R1 e R2 vivem inteiras na arvore de trabalho, misturadas a trabalho anterior tambem nao
commitado. Linha de base: `git status --porcelain` = 153 entradas (96 modificados + 57 nao rastreados); ultimo commit
`93755eb`.

Distribuicao dos 96 modificados: `frontend/src` 68, `backend/app` 22, `frontend/tests` 19, `backend/tests` 14,
`frontend/public` 5, mais `docs/` (incluindo `docs/openapi.json`), `frontend/package.json` e `package-lock.json`,
`frontend/index.html`, `scripts/contrato_frontend.mts`.

Novos (nao rastreados) relevantes a entrega:
- backend: `app/engines/crystallography/ligas_entrada.py`, `sitios.py`; `app/engines/hea/entrada.py`, `erros.py`,
  `referencia.py`, `textos.py`; `app/repositories/entalpias_json.py`, `identidade_elementos.py`; testes novos
  `tests/api/test_cristalografia_r1.py`, `test_erros_r2.py`, `test_hea_r1.py`, `test_procedencia_r2.py`,
  `test_termico_r2.py`, `tests/unit/engines/test_fea_hc_regressao.py`, `test_ligas_r1.py`, `test_validacao_estruturas.py`.
- frontend: `design-system/fonts.css`, `layout/StageLayout.tsx`;
  `features/viewer3d/alloyScene.ts`, `appearance.ts`, `cameraApi.ts`, `sceneFilterState.ts`, `visibility.ts`;
  `i18n/nature.ts` mais 5 TSV de origem; `modules/crystalab/AlloyAtomInspector.tsx`, `AlloyDetails.tsx`,
  `AlloyPanels.tsx`, `AppearancePanel.tsx`, `FilterPanel.tsx`, `SceneHud.tsx`, `Sidebar.tsx`, `alloyDisplay.ts`;
  `modules/hea/display.ts`; `stores/alloy.ts`, `appearance.ts`, `crystalUi.ts`, `sceneFilter.ts`;
  specs novos `tests/e2e/alloy-selection-filters.spec.ts`, `alloy-thermal.spec.ts`, `appearance.spec.ts`,
  `crystalab-layout.spec.ts`, `tests/unit/alloy.test.ts`.

Consequencia honesta: NAO existe rollback seletivo de R1/R2 por git. Reverter os arquivos modificados ao commit
`93755eb` descartaria tambem o trabalho anterior nao commitado que esta no mesmo diff, e nao ha como separar as
camadas sem um commit intermediario.

Plano recomendado, em ordem:
1. Antes de qualquer outra coisa, criar um ponto de retorno: copia integral da arvore para fora do repositorio
   (`robocopy` ou `cp -a`) OU um commit em branch de integracao (`git switch -c integracao/r2` e commit). Isso exige
   autorizacao do usuario; nao fiz nada disso.
2. Com o ponto de retorno existindo, o rollback passa a ser trivial: voltar ao commit anterior na branch, ou restaurar a copia.
3. Rollback de dados: nenhum necessario. Nenhuma migracao foi aplicada ao banco do projeto e `motores` so recebe
   insercoes idempotentes. `python -m app.cli backup var/backup.db` existe e e o caminho para preservar o SQLite antes de operar.
4. Rollback de bundle: `frontend/dist/` e artefato gerado; `npm run build` reconstroi.

Risco registrado: enquanto nao houver commit nem copia, qualquer `git restore`, `checkout`, `reset`, `stash` ou `clean`
na arvore destroi R1+R2 de forma irrecuperavel. E o maior risco operacional aberto hoje.

## 6. Falhas classificadas

| # | Componente | Achado | Severidade | Dono sugerido | Bloqueia liberacao (G5)? |
|---|---|---|---|---|---|
| F-1 | backend + banco | `ExecucaoCalculo` insere `motor_codigo`/`motor_versao` sem garantir a linha em `motores`; em banco preexistente com FK aplicada o calculo autenticado devolve 500 (nao so o historico). Q-15 | Alta | database-engineer (esquema/seed) com backend-engineer (`services/calculo.py`) | SIM para liberacao em PostgreSQL preexistente. Nao bloqueia G4 em banco novo |
| F-2 | infraestrutura/banco | SQLite nao habilita `PRAGMA foreign_keys`: FK nao aplicada em dev, defeitos de integridade referencial invisiveis ate producao (PostgreSQL). Divergencia dev/prod | Media | database-engineer, com devsecops para o checklist de deploy | Nao bloqueia G4; deve entrar no checklist de G5 |
| F-3 | processo/git | Nenhum commit: R1+R2 e trabalho anterior no mesmo diff nao commitado; sem rollback seletivo possivel e com risco de perda total por um comando de git | Alta (operacional) | supervisor com devsecops | SIM - ponto de retorno e pre-requisito de G5 |
| F-4 | frontend | `fracoes_massa` validado no zod mas nao lido por nenhum componente de UI | Baixa (cosmetica) | frontend-engineer | Nao |
| F-5 | backend (dependencia) | `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead` em toda execucao de teste | Informativa | devsecops / backend-engineer | Nao |

Nenhuma divergencia CIENTIFICA e nenhuma divergencia DE CONTRATO DE API foi encontrada; portanto nao ha nada para
encaminhar a materials-science-specialist, hea-specialist, crystallography-engineer ou api-architect por esse motivo.

## 7. Veredito G4

INTEGRADO COM RESSALVAS.

Justificativa: as quatro suites e as medicoes auxiliares foram reexecutadas por mim e todas passam, com as contagens
que o Supervisor informou (850/42/0, 107/107, 74/74, 46/46 de contrato, 249,5 kB gzip); `docs/openapi.json` esta em
sincronia byte a byte com o codigo; os 242 campos dos schemas do frontend tem correspondencia no OpenAPI; e cada campo
nomeado no cartao de tarefa foi conferido contra resposta real do backend, inclusive os casos anulaveis do termico, que
vem com motivo em `indisponiveis`. Nao ha regressao conhecida, divergencia de contrato nem divergencia cientifica.
As ressalvas sao F-1 (defeito real de integracao backend-banco, invisivel em SQLite e reproduzido por mim) e F-3
(ausencia de ponto de retorno), que sao de integracao e de processo, nao de ciencia.

Falta para G5 (liberacao) - e publicacao NAO foi autorizada pelo usuario:
1. Correcao de F-1 pelo dono (get-or-create do motor, ou passo de seed obrigatorio e verificado na partida).
2. Decisao sobre F-2 (habilitar FK em SQLite) para que dev e producao concordem.
3. Ponto de retorno autorizado pelo usuario (commit em branch de integracao ou copia da arvore) - F-3.
4. Validacao visual em navegador real e acessibilidade com leitor de tela, fora do meu escopo.
5. Verificacao em PostgreSQL e em Docker, nao feitas aqui.
6. Autorizacao expressa do usuario para commit e publicacao.

## 8. O que NAO foi verificado

- Validacao visual em navegador real: nao abri a interface; a evidencia de UI e a E2E em chromium headless.
- PostgreSQL: nenhuma execucao real; a aplicacao de FK foi emulada em SQLite com `PRAGMA foreign_keys=ON`.
- Docker, docker-compose, Caddy e CI: nada executado.
- Desempenho sob carga: nao medido (ha um `perf-metrics.spec.ts` de FPS do viewer, que passou, mas nao e teste de carga).
- Acessibilidade com leitor de tela real: nao verificada; so os testes automatizados de teclado e contraste.
- Conectividade limitada: coberta apenas pelo spec `flow-e-mobile-offline`; nao medi em rede degradada real.
- Navegadores alem do chromium: nao testados.
- Bancos preexistentes do projeto: nao abertos, nao migrados, nao alterados.
- Conteudo cientifico dos resultados: fora do meu papel; nao reavaliei formulas nem fontes.
- `.env`: nao lido.
- Anomalia observada, fora de escopo: `_origem/C_alloy_frontend/alloy-frontend/package-lock.json` aparece como nao
  rastreado dentro de `_origem/`, que e somente leitura. Nao toquei nele; registro para o supervisor.

## Encerramento

Nenhuma correcao de codigo foi feita por mim (o cartao proibe). Arquivos escritos: apenas este relatorio e temporarios
no scratchpad. Nenhum servidor de desenvolvimento ficou em execucao (usei `TestClient` em processo, encerrado a cada script).
Estado: CONCLUIDO.
