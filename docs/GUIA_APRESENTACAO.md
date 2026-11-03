# Guia de apresentação — Alloy Virtual Lab (nova versão × anterior)

Data: 03/11/2026 · Versão apresentada: **API 0.9.0** (branch `consolidacao-alloy-virtual-lab`, commit `b47d6c3`)
Versão anterior de referência: **CrystaLab v1.4** (arquivo único, a que recebeu as sugestões dos professores).
Evidências: [RELATORIO_ENCERRAMENTO.md](RELATORIO_ENCERRAMENTO.md), [TESTES_E_QA.md](TESTES_E_QA.md), [PENDENCIAS.md](PENDENCIAS.md).

> **Resposta curta à pergunta "foi tudo atendido?": não.** A nova versão é muito mais sólida (motor único, banco, contas
> reais, correção no servidor, testes, infraestrutura), mas **as telas de ligas, temperatura, cores configuráveis e tutoriais
> da v1.4 ainda não foram portadas para o novo frontend**, e a barra lateral única e o login restrito à UFC também não.
> Os motores e as rotas de API dessas funções existem e estão testados. Falta a interface (seções 5 e 8).

---

## 1. Mensagem central (30 segundos)

"Tínhamos três motores de cálculo diferentes, sem banco, sem usuários reais e com um HEA que mostrava números aleatórios.
Agora há **um motor só**, que mostra de onde vem cada número; um **banco de dados**; **contas seguras**; **questões corrigidas
no servidor**; e **311 + 77 testes automáticos**. O que ainda falta é levar para a tela nova algumas funções que a v1.4 já
tinha (ligas, temperatura, tutoriais, cores)."

## 2. Roteiro (≈ 20 min)

| # | Tempo | Slide / ação | Ponto principal |
|---|---|---|---|
| 1 | 2 min | Problema | 3 motores com regras diferentes (Ti +6,3 %, N_A arredondado), HEA fictício, sem banco nem autenticação |
| 2 | 2 min | Arquitetura | Motor puro → serviços → API `/api/v1` → front. Diagrama de [ARQUITETURA_FINAL.md](ARQUITETURA_FINAL.md) |
| 3 | 5 min | **Demo 1 — CrystaLab** | Resultado com passos e **procedência**; Ti corrigido; Miller; compartilhar; CIF do servidor |
| 4 | 4 min | **Demo 2 — HEA** | Só o que tem base; "indisponível" com motivo; ponte para o CrystaLab; contraste com o modo demo |
| 5 | 3 min | **Demo 3 — Conta e questões** | Cadastro, histórico, gabarito que só aparece depois da tentativa |
| 6 | 2 min | Qualidade e segurança | Números reais dos testes; o que a segurança cobre e o que não cobre |
| 7 | 2 min | O que falta | Seções 5 e 8: honestidade sobre as telas não portadas |

### Preparar a demonstração

```bash
cd frontend
npm run build
npm run engine -- --db ../var/dev.db     # API em 127.0.0.1:8010 com SQLite migrado e seed
npm run serve                            # outro terminal: http://127.0.0.1:5173
```

**Atenção (demo 3):** a lista de questões só mostra questões que alguém criou, e criar questão pública exige `admin_geral`.
Não há API de administração (pendência T-04), então **antes de apresentar** marque um usuário como `admin_geral` direto no
banco e crie 1–2 questões, ou deixe a demo 3 só com cadastro, login e histórico. Sem isso a lista aparece vazia.

### Demo 1 — CrystaLab (comandos no terminal da tela)

1. `usar Cu`: mostre FEA, densidade e o painel "Procedência" (classe, versão do motor, dados usados e estado de validação).
2. `usar Ti`: densidade de 4,5 g/cm³ (a v1.4 dava 4,79, porque derivava *a* de R; agora o *a* medido tem prioridade).
3. Planos: `plano 1 1 1` e, em HC, `plano 1 0 -1 1`: polígono e distância interplanar. A densidade planar só aparece onde há validação.
4. Botão **Compartilhar**: o link reabre a mesma cena. **Exportar → CIF**: gerado no servidor.

### Demo 2 — HEA

1. `#/hea` → **Analisar** (CoCrFeNi): ΔS_mix, δ, VEC = 8,25, fase prevista CFC.
2. Aponte o painel **"Grandezas não calculadas"**: ΔH_mix e Ω aparecem como indisponíveis, com o motivo (Q-01). Os gráficos que dependem delas dizem que estão indisponíveis.
3. **Abrir no CrystaLab**: a estrutura vem do critério de VEC, sem criar dados novos.
4. Contraste: abra `/?demo=1#/hea` para ver valores fictícios com o selo "Demonstrativo".

### Demo 3 — Conta e questões

1. `#/conta` → criar conta (senha de pelo menos 10 caracteres; senha comum é recusada) e entrar.
2. Faça um cálculo e veja o histórico: ele fica gravado com versão do motor e parâmetros.
3. Questões corrigidas no servidor: responda errado (o feedback indica o tipo de erro, por exemplo fator 10ⁿ) e depois certo (aparece o gabarito com a resolução do motor).

## 3. O que mudou: v1.4 → nova versão

| Área | v1.4 (anterior) | Nova versão | Evidência |
|---|---|---|---|
| Estrutura | 1 arquivo de 6 044 linhas, servidor e HTML embutidos | monorepo em camadas; regras de dependência verificadas por teste | `tests/unit/test_arquitetura.py` |
| Motor científico | N_A = 6,022e23; *a* sempre derivado de R | N_A CODATA 2018 única; *a* medido com prioridade e fonte; regressão A/B/D | `tests/scientific/` |
| Rastreabilidade | sem origem dos dados | **procedência em todo resultado** (classe, motor, versão, dados e estado de validação) | campo `procedencia` da API |
| Dados | `dict` no código, sem fonte | banco com estados *rascunho → aguardando validação → validado*; produção recusa o não validado | [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md) |
| HEA | não existia (no frontend anterior era aleatório) | **motor analítico**: ΔS_mix, δ, T_m, VEC e fase; o resto é "indisponível" com motivo | [MOTOR_HEA.md](MOTOR_HEA.md) |
| Usuários | "login" só por e-mail, sem senha, em arquivo JSON | contas com Argon2id, sessão em cookie protegido, CSRF, bloqueio de tentativas, permissões por instituição | [SEGURANCA.md](SEGURANCA.md) |
| Histórico | arquivo local | histórico pessoal no banco, isolado por usuário | `test_auth.py` |
| Exercícios | prática no navegador | **questões com gabarito calculado pelo motor e corrigidas no servidor** | `test_educacao.py` |
| API | rotas soltas `/api/*` | `/api/v1` versionada, 35 rotas, erros padronizados, OpenAPI e tipos TypeScript gerados | `docs/openapi.json` |
| Frontend | HTML/JS embutido | React 19 + TypeScript estrito, design system, 3 idiomas, PWA offline, teclado e leitor de tela, paleta Ctrl+K | [FRONTEND.md](FRONTEND.md) |
| Exportação | XYZ no cliente | CIF e XYZ gerados no servidor | rotas `/exports/*` |
| Testes | nenhum | 311 backend + 77 frontend + 55 E2E + contrato 38/38 | [TESTES_E_QA.md](TESTES_E_QA.md) |
| Operação | `python arquivo.py` | Docker, Caddy (HTTPS), compose com PostgreSQL, CI Linux + Windows | [DEPLOY.md](DEPLOY.md) |
| Documentação | README | 15 documentos + relatório de encerramento | `docs/` |

**Números para citar (medidos em 02–03/11/2026):** backend 311 aprovados / 23 pulados / 0 falhas · frontend 77/77 ·
E2E 54/55 (1 intermitente registrado) · contrato real 38/38 · carregamento inicial de 204 kB compactados (meta: menos de 300 kB).

## 4. O que ainda **não** foi verificado (dizer na apresentação)

- **PostgreSQL, Docker e o CI no GitHub** não rodaram na máquina de desenvolvimento. O CI foi publicado com o código, mas **o resultado ainda não foi conferido**.
- **Nenhum dado científico está validado** (Q-03). Em produção, o HEA mostraria só ΔS_mix e a temperatura ficaria bloqueada.
- **ΔH_mix, Ω, veredito de estabilidade e curva de Gibbs** dependem de uma tabela de entalpias com fonte (Q-01).
- Sem envio de e-mail (verificação de conta e recuperação de senha, Q-04) e sem pentest externo.

## 5. Atendimento das sugestões dos professores

Legenda: ✔ atendida · ◐ parcial · ✘ não atendida.

| Sugestão | v1.4 | Nova versão | Situação na nova versão |
|---|---|---|---|
| **Miná 1 / Gisele 1**: cor por elemento, configurável na 3D | ✔ seletor de cor por elemento | ◐ | Só há coloração **ilustrativa** (semente) na ponte HEA, e apenas no modo demonstrativo. Não há seletor de cor. A tabela `cores_elementos` existe no banco, sem tela. |
| **Miná 2**: ver a formação da liga e a posição de cada átomo | ✔ | ◐ | A API de soluções sólidas devolve os átomos da supercélula com o soluto, mas **não há tela de liga**. O viewer mostra célula e supercélula. |
| **Miná 3**: efeito da temperatura e vibração dos átomos | ✔ controle de temperatura + vibração | ◐ | Motor e API de temperatura prontos (dilatação, Lindemann, alotropia). Na tela há só uma animação de vibração **ilustrativa, sem valores** e sem controle de temperatura. |
| **Miná 4**: aprendizado com desenho de planos | ✔ | ✔ | Exercício "qual é o plano?" em `#/aprender`; planos, direções e famílias no viewer; questões de distância interplanar no servidor. |
| **Miná 5**: melhorar parâmetro de rede e FEA | ✔ | ✔ | *a* medido com prioridade e fonte, N_A CODATA, Ti corrigido, passos completos, regressão testada. |
| **Miná 6**: mostrar o impacto das ligas nos átomos | ✔ distorção ilustrativa | ◐ | O motor devolve distorção e ordenação, mas **sem tela**. |
| **Gisele 2**: usar pacotes abertos para funções visuais e de estudo | ◐ (CDN) | ◐ | Adota Three.js, KaTeX, Zod, Zustand, Argon2, Gemmi (opcional) e Playwright. **Não há levantamento formal documentado** dos pacotes avaliados. |
| **Gisele 3**: uma barra lateral e 3D maior | ✔ | ✘ | O layout herdado tem painel do laboratório à esquerda **e** painel de abas à direita. Não foi reduzido. |
| **Gisele 4**: tela inicial com login de e-mail da UFC, gravado | ✔ só `@ufc.br`, sem senha | ◐ | Conta real com senha e histórico no banco (mais seguro), mas **sem restrição ao domínio `@ufc.br`**, sem tela de início obrigatória e sem verificação de e-mail. |
| **Aba Tutoriais** (pedida por você: .txt, .mp4, .pdf, planilhas, docs) | ✔ | ✘ | A tabela de arquivos existe no banco, mas **não há rota nem tela**. |

**Resumo:** na nova versão, 2 atendidas, 6 parciais e 2 não atendidas (barra única e Tutoriais). Na v1.4, todas estavam atendidas.

## 6. Atendimento das demandas do projeto

| Demanda | Situação | Observação |
|---|---|---|
| Revisar a v1.3 (usuário e designer) e relatar | ✔ | feito no início do trabalho |
| Aplicar as sugestões dos professores + aba Tutoriais (v1.4) | ✔ na v1.4 · ◐ na nova | ver seção 5 |
| Relatório curto das mudanças, limitações, erros e sugestões | ✔ | entregue |
| 3 documentos técnicos (sugestões 5, 6 e 7) em `.txt` | ✔ | em `_origem/A_crystalab_v1.4/crystalab/docs/` |
| Salvar o código no Drive, pasta "crystalab" | ✔ | conta `assefjl@alu.ufc.br` |
| E-mail ao supervisor com instruções de instalação e execução | ✘ **não enviado** | pelo meu registro, o rascunho está pronto, mas o `.zip` precisa ser anexado por você (não consigo anexar arquivos); **ação pendente sua** |
| Usar o Prompt Mestre como base e executar as 10 fases | ✔ com ressalvas | fases 1–10 concluídas e publicadas; ressalvas na seção 7 |
| Publicar no GitHub | ✔ | branch `consolidacao-alloy-virtual-lab` (a `main` do repositório não foi alterada) |

## 7. Atendimento dos requisitos do Prompt Mestre (71 requisitos)

✔ atendido e testado · ◐ parcial · ✘ não atendido · ○ adiado por decisão registrada

| Domínio | ✔ | ◐ | ✘ / ○ | Observação |
|---|---|---|---|---|
| Cristalografia (CIE, 13) | 11 | 2 (CIE-11 ligas, CIE-12 temperatura) | — | motor e API prontos; sem tela |
| API (6) | 4 | 1 (API-04: paginação só no histórico) | ○ API-06 | cálculo longo adiado: não houve necessidade medida |
| Arquitetura (5) | 3 | 2 (ARQ-04 sem módulo de administração; ARQ-05 não auditado) | — | |
| Banco (8) | 3 | 4 (DAD-01 PostgreSQL não executado, DAD-03, DAD-05, DAD-08 só em SQLite) | ✘ DAD-07 backup | |
| Segurança (7) | 2 | 4 (SEG-01, 03, 04, 05) | ✘ SEG-07 LGPD | sem recuperação de senha, administração e pentest |
| Frontend (7) | 5 | 1 (FE-04: axe e Lighthouse não rodados) | ✘ **FE-06** | FE-06 = funções da v1.4 que o frontend anterior não tinha (ligas, temperatura, cores, tutoriais) |
| HEA (6) | 1 | 3 (HEA-01, 02, 05) | ✘ HEA-03, 06 | depende de Q-01 |
| Educacional (6) | 1 | 3 (EDU-01, 02, 03) | ✘ EDU-06 · ○ EDU-05 | IA desligada por decisão |
| Operação (5) | 2 | 3 (OPS-01, 03, 04: escritos, não executados) | — | |
| Qualidade (5) | 1 | 4 (QA-01, 02, 04, 05) | — | concorrência, acessibilidade automatizada e Gemmi local pendentes |
| Documentação (3) | 3 | — | — | |
| **Total** | **36** | **27** | **6 ✘ + 2 ○** | |

## 8. Plano para fechar as lacunas (ordem sugerida)

| Prioridade | Entrega | O que já existe | O que falta |
|---|---|---|---|
| 1 | **Telas de Ligas e Temperatura** (Miná 2, 3, 6) | rotas `/solid-solutions` e `/thermal`, testadas | telas, controle de temperatura ligado ao motor, vibração com amplitude real |
| 2 | **Cores configuráveis por elemento** (Miná 1 / Gisele 1) | `viewer.elementColoring`, tabela `cores_elementos` | seletor de cor e persistência da preferência |
| 3 | **Aba Tutoriais** | tabela `arquivos` e extensões permitidas | rotas de upload seguro e a aba |
| 4 | **Barra lateral única + 3D maior** (Gisele 3) | layout com painéis recolhíveis | fundir os dois painéis em um |
| 5 | **Login restrito à UFC** (Gisele 4) | contas, sessão e histórico | regra de domínio (configurável), tela de início e e-mail de verificação (depende de Q-04) |
| 6 | Levantamento de pacotes abertos (Gisele 2) | — | documento curto com as bibliotecas avaliadas |
| 7 | API de instituições e turmas (T-04) | tabelas e permissões | rotas e painel de administração |

Cada item cabe em uma fase própria com o mesmo ciclo (implementar, testar, documentar). O item 1 é o de maior valor para os professores.
