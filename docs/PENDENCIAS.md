# Pendências

Atualizado na Fase 10. "Responsável" = quem precisa agir; nada aqui se resolve só com código.

## Decisões e insumos humanos

| ID | Pendência | Bloqueia | Responsável | Ação |
|---|---|---|---|---|
| Q-01 | Entalpias binárias de mistura (Miedema / Takeuchi & Inoue) com fonte | ΔH_mix, Ω, veredito HEA, curva G×T | Responsável pelo projeto | Fornecer a tabela ou o dataset de referência ([MOTOR_HEA §5](MOTOR_HEA.md)) |
| Q-02 | Hospedagem | Publicação | Responsável | Escolher o host (o compose roda em qualquer VM com Docker) |
| Q-03 | Validador científico | Promover dados a `validado`, liberar δ, T_m, VEC, ligas e temperatura em produção | Responsável | Nomear um professor; conferir o Callister (edição e página, CR-10), o *a* do Ti, os dados da v1.4 e a tabela VEC (Guo 2011) |
| Q-04 | Provedor de e-mail | Verificação de e-mail e recuperação de senha | Responsável | SMTP institucional ou serviço transacional |
| Q-05 | SSO institucional | Opcional | TI da UFC | Consultar disponibilidade |
| Q-06 | Licença do projeto e dos dados | Repositório científico aberto | Responsável | Definir |
| Q-07 | Publicar o repositório no GitHub | Execução do CI (Linux/Windows, PostgreSQL, imagens) | Responsável | Criar o repositório e fazer o push |

## Limitações do ambiente usado na consolidação

| ID | Limitação | Efeito | Como fechar |
|---|---|---|---|
| L-01 | Sem PostgreSQL | 23 variantes PostgreSQL dos testes puladas | Job `backend-linux` do CI, ou `ALLOY_TEST_POSTGRES_URL` local |
| L-02 | Sem Docker | Imagens, compose e Caddyfile não executados | Job `imagens` do CI ou Docker Desktop |
| T-01 | Gemmi sem pacote para Python 3.15 | 1 teste de validação CIF pulado | CI com Python 3.12 (`.[validacao]`) |

## Técnicas (próximas implementações)

| ID | Pendência | Prioridade | Observação |
|---|---|---|---|
| T-02 | Gatilho de soma da composição (`composicao_itens`) | média | escrever e testar com PostgreSQL |
| T-03 | *a* medido com fonte para os outros 14 metais | média | ADR-005 pleno; depende de Q-03 |
| T-04 | API de instituições, turmas e matrículas | alta | as tabelas e o RBAC existem; hoje os vínculos são criados direto no banco |
| T-05 | Atividades, atribuições a turmas, entregas e notas | alta | tabelas prontas; o Fluxo C completo (professor → turma → desempenho) depende de T-04 |
| T-06 | Limitador de login compartilhado (banco ou Redis) | média antes de escalar | hoje vale por processo |
| T-07 | `pip-audit` e `npm audit` no CI | média | varredura de dependências |
| T-08 | Migrar as atividades didáticas locais (`#/aprender`) para os geradores do servidor | média | o servidor já tem 3 geradores; o front local continua como prática offline |
| T-09 | Diagrama de fases (`/thermodynamics/phase-diagram`) | baixa | especificação em A/docs/2 |
| T-10 | Repositório de materiais e ligas (`/materials`, `/sources`) e upload de tutoriais (`/files`) | média | Fluxo D; tabelas prontas |
| T-11 | Remover os aliases `/v1` | baixa | depois de confirmar que não há clientes antigos |
| T-12 | E2E 4.9 (gerenciador de camadas) intermitente: 1 falha em uma rodada completa, 5/5 isolado | baixa | investigar com trace no CI; possível corrida entre comandos de terminal enviados em sequência |
| T-13 | ~~Telas de Ligas e Temperatura~~ — **concluída em 03/11/2026** (abas Liga e Temperatura em `#/crystalab`) | — | ver [FRONTEND.md](FRONTEND.md) §7; resta o comando de terminal equivalente (T-19) |
| T-14 | Seletor de cor por elemento (Miná 1 / Gisele 1) | alta | `viewer.elementColoring` e tabela `cores_elementos` existem |
| T-15 | Aba Tutoriais com upload seguro (.txt, .md, .mp4, .pdf, planilhas, docs) | alta | tabela `arquivos` pronta, sem rotas |
| T-16 | Barra lateral única e 3D maior (Gisele 3) | média | hoje há painel à esquerda e à direita |
| T-17 | Login restrito a `@ufc.br` configurável + tela de início (Gisele 4) | média | verificação de e-mail depende de Q-04 |
| T-18 | Levantamento documentado de pacotes abertos (Gisele 2) | baixa | — |
| T-19 | Comandos de terminal para liga e temperatura (`liga Cu Ni 30`, `temperatura 600`) e desfazer/refazer | baixa | as abas chamam a API direto; as demais operações têm comando equivalente |
| T-20 | Carregar `AlloyPanels` sob demanda | baixa | o carregamento inicial subiu 204,2 → 212,8 kB compactados (meta < 300 kB) |

## Rodada R1 (13/11/2026) — novas pendências

Fonte: `docs/agent_reports/2026-11-13_rodada_R1_relatorio_consolidado.md`. "Decisão/dado necessário" diz o que
destrava o item; nada aqui se resolve só com código.

### Decisões e insumos humanos

| ID | Pendência | Bloqueia | Decisão/dado necessário |
|---|---|---|---|
| Q-01 (atualizada) | Matriz de ΔH binário de mistura com fonte legível | ΔH_mix, Ω, veredito completo, gráficos δ×ΔH e ΔG×T | O PDF de Takeuchi & Inoue (2005) não tem camada de texto; o auditor leu 0 pares da fonte primária e 15 de fonte secundária com atribuição conjunta (confiança baixa, em `docs/research/2026-11-13_entalpias_binarias_candidatas.json`, NÃO usados). Fornecer PDF com OCR, transcrição revisada da tabela, ou a compilação de de Boer/Miedema (1988) |
| Q-08 | Faixa de ΔH da "zona de solução sólida" do gráfico do HEA | Desenhar a zona com fonte | As fontes secundárias divergem: −15 a 5, −15 a −5 e −10 a 5 kJ/mol. Conferir em Zhang et al. (2008); hoje a zona sai marcada como não verificada |
| Q-09 | Edição e páginas do Callister e do Askeland citados na interface | Citações com página | Das 32 afirmações citadas em código, só R = 8,314462618 está verificada. Definir a edição e conferir as páginas, ou remover o número de página |
| Q-10 | Obras 7, 8, 10 e 11 da bibliografia fornecida não localizadas em catálogo | Relatório bibliográfico completo | Confirmar autoria/edição de Reed-Hill (ed. em português), Padilha "Metalurgia Física", Ávila & Becker e Chvátal |
| Q-11 | CALPHAD | Energia de Gibbs por fase, frações de fase × T, diagramas, partição | Decidir: não adotar nesta fase (recomendação do especialista) ou autorizar investigação de licença, cobertura e compatibilidade (nada verificado) |
| Q-12 | Escopo honesto de termodinâmica | Texto público do módulo | Aprovar o enunciado D-TERMO-02: modelos de solução (ideal e, com dado, regular) para uma fase desordenada + descritores de triagem; sem equilíbrio de fases e sem cinética |
| Q-13 | V-14: usar o `a` medido do solvente como base da interpolação da liga | Coerência entre o módulo de célula e o de liga (Ti) | Ficou fora do contrato R1. Autorizar ou não a mudança de valor |
| Q-14 | Modo demonstrativo do HEA (`heaDemo.ts`) | Risco de número fictício ser lido como resultado | **DECIDIDO pelo responsável em 14/11/2026: MANTER, com marca de demonstração nos gráficos.** Implementar o selo em todo gráfico, tabela e número vindo de `heaDemo.ts`, de modo que nenhum valor fictício possa ser lido como resultado do motor. Rejeitada a retirada sugerida pelo especialista |
| Q-15 | Linha ('hea','2.0.0') e ('crystallography','2.1.0') em `motores` | Gravar histórico de cálculo de usuário autenticado em banco já existente | `execucoes_calculo` tem FK para `motores`. `python -m app.cli seed` registra as versões novas (leitura de código), mas NÃO foi executado em banco existente. Conferir com o database-engineer antes de publicar |

### Técnicas

| ID | Pendência | Prioridade | Observação |
|---|---|---|---|
| T-16 (concluída) | ~~Barra lateral única e 3D maior~~ | — | Entregue na R1-FE-01: palco em área total e barra única de seis seções |
| T-21 | Liga intersticial com supercélula pequena mostra 0 átomos de soluto | alta | Fe–C 2 at% em 2×2×2 dá ⌊16·x/(1−x)+½⌋ = 0 (correto como amostragem; era 1 por mínimo forçado). A tela fica sem carbono. Sugerir supercélula maior na interface e cobrir os dois casos no teste `alloy-thermal.spec.ts:46` |
| T-22 | Aparência: cores por elemento/grupo/átomo, cores de vértices e arestas, tamanho e transparência | alta | R1-FE-02, não iniciada (item 2 do pedido) |
| T-23 | Filtros, cortes e isolamento para alcançar átomos internos | alta | R1-FE-02; hoje só há corte por plano de Miller |
| T-24 | Seleção e inspeção de átomo na cena de LIGAS | alta | `alloyScene.ts` monta a liga sem `AtomRef`; depende dos campos por átomo da R1-BE-02, já disponíveis |
| T-25 | Front consumir os campos novos da API | alta | R1-FE-03: regenerar `openapi.gen.ts`, declarar no zod, usar `composicao.n_atomos_unicos`, `imagem`, `triagem.estado`, gráficos G-A e G-B |
| T-26 | Correções do motor térmico apontadas no parecer | alta | T-1 (rede de líquido acima de T_f), T-6 (T_f nominal não é solidus/liquidus), T-8/T-9 (alotropia lida sem política de dados e sem procedência — rejeitado para produção) |
| T-27 | Selo "Ilustrativo" na animação α→γ | média | `SceneHud.tsx` exclui justamente a animação que mais parece simulação de transformação |
| T-28 | FEA do HC: proteger c/a < 2/3 e gerar os valores de regressão do c/a do seed | média | Ressalvas R-1 e R-2 do parecer de termodinâmica |
| T-29 | Instabilidade do E2E A2 (`flow-a-density.spec.ts:41`) | baixa | Falha na suíte completa, passa isolada |


## Rodada R2 (15/11/2026) — situação das pendências

Fonte: `docs/agent_reports/2026-11-14_rodada_R2_estado.md` (encerramento) e
`docs/agent_reports/2026-11-15_integracao_R2.md`.

### Fechadas nesta rodada

T-21 (motor confirmado correto + aviso acionável na interface), T-22 (menu de aparência), T-23 (filtros, cortes e
isolamento), T-24 (seleção e inspeção na cena de ligas), T-25 (front consumindo os campos novos da API),
T-26 (correções do motor térmico), T-27 (selo na animação α→γ), T-28 (FEA do HC protegido), T-29 (instabilidade do
E2E: causa era tempo no primeiro carregamento sob carga, mitigada no fixture; suíte 74/0), Q-14 (decidida pelo
usuário: manter o modo demonstrativo com selo — implementado).

### Novas

| ID | Pendência | Prioridade | Decisão/dado necessário |
|---|---|---|---|
| Q-16 | Política de dado não validado aplicada de forma desigual: `/cells` e `/density` devolvem valor em produção com dado que aguarda validação, enquanto o térmico recusa e o HEA anula | alta | Decisão do usuário. (A) alinhar ao princípio 3 e desligar o CrystaLab em produção até Q-03; (B) manter a exceção, escrita como exceção no `CLAUDE.md` e na documentação, e revertê-la quando Q-03 for resolvida. Recomendação do Supervisor: (B) |
| Q-17 | **Não existe ponto de retorno.** 153 entradas não commitadas misturam R1, R2 e trabalho anterior do usuário | **crítica (processo)** | Autorizar a criação de um ponto de retorno (commit numa branch de integração ou cópia integral da árvore) antes de qualquer nova rodada. Nenhum `git restore/checkout/reset/stash/clean` pode ser usado: destruiria tudo de forma irrecuperável |
| T-30 | Banco sem migração devolve 500 em todas as rotas de cálculo | baixa | Verificação de prontidão (`/health/ready`); item de operação, não de motor |
| T-31 | Inserir a linha de `motores` de cada versão na migração ou no seed | média | Hoje depende do seed ou do registro idempotente feito em requisição (corrigido em R2-BE-03). Decisão do database-engineer |
| T-32 | `fileConfig` do Alembic desabilita os loggers da aplicação (`alloy.api`, `alloy.historico`) | baixa | Afeta processos que rodam migração no mesmo processo |
| T-33 | `fracoes_massa` é validado no contrato do front e não é usado por nenhuma tela | baixa | Remover do zod ou passar a exibir |
| T-34 | Plano de Miller (`clippingPlanes`) não se aplica à cena de ligas | média | Decisão de produto: o corte novo por eixo já cobre "ver o interior" na liga |
| T-35 | Vizinhança do átomo selecionado está implementada como raio de EXIBIÇÃO | média | Vizinhança cristalográfica (primeiros vizinhos) é grandeza científica e teria de vir do motor: exige contrato e parecer |
| T-36 | Sem verificação de contraste da cor escolhida pelo usuário contra o fundo da cena | baixa | O teste de contraste do projeto cobre tokens do tema, não escolhas pessoais. Mitigado porque cor nunca é o único código |
| T-37 | Validações que nunca foram feitas | alta | QA adversarial de frontend/E2E; parecer pedagógico das telas novas; PostgreSQL (41 testes pulados); Docker/CI; desempenho sob carga; acessibilidade com leitor de tela; **toda a validação visual em navegador** |
