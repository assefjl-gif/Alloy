# Etapa 1 — Relatório de inspeção e linha de base

Data da inspeção: 21/10/2026 · Responsável pela frente: F1 (arquitetura) · Fonte do plano: documento “Alloy Virtual Lab + CrystaLab — Plano de Desenvolvimento do Front-end por Etapas” (20/10/2026).

**Conclusão:** o legado funciona como calculadora didática, mas depende de CDN para o 3D (que falhou neste ambiente), mistura apresentação e estado em uma string Python e não oferece acesso por teclado ao viewer. Os cálculos e os seis `data-testid` são preservados; a interface é reconstruída.

> **Gate da Etapa 1 — pendente de aprovação humana.** A classificação preservar/refatorar/novo (seção 5) precisa ser aprovada pela equipe e pelo especialista em materiais. Este relatório não substitui essa aprovação.

## 1. Fontes inspecionadas (1.2)

| Arquivo (projeto) | Papel | Executável aqui? |
|---|---|---|
| `crystalab_modulo1.py` | Motor CrystaLab v1.0 + servidor stdlib + UI em `HTML_TEMPLATE` | **Sim** — copiado sem alterações de lógica para `legacy/` e usado como motor real nos testes |
| `pesquisa_front1.17.py` | Matriz HEA Virtual Lab v1.17 (UI em `HTML_TEMPLATE`) | **Não** — importa `hea_engine`, que não está no projeto |
| `deepseek_python_20261012_784017.py` | CrystaLab v1.0 refatorado em FastAPI (rotas `/v1/*`, exportação CIF/XYZ) | **Não** — FastAPI e pydantic-settings não instaláveis (PyPI bloqueado, HTTP 403) |
| `deepseek_python_20261012_86eef1.py` | Rascunho FastAPI truncado | Descartado (já descartado na v1.1.0, QA-01) |
| `claude/crystalab_v1.1.0_CHANGELOG.md` | Descreve a v1.1.0 (pacote `crystalab/`) | O **código** da v1.1.0 não está no projeto; só o changelog |
| `claude/referencias_bibliograficas.md` | Bibliografia e conferência de dados | Usado para as referências exibidas na UI |

Pontos de entrada da interface: `GET /` de cada servidor devolve a página inteira com `window.BOOTSTRAP_DATA` embutido. Não há empacotador, módulos JS, nem arquivos estáticos separados.

Observação de transcrição: `legacy/crystalab_modulo1.py` foi transcrito do projeto com fim de linha LF (o original usa CRLF) e com dois caracteres combinantes escritos como escape (`̄` em Python, `̀-ͯ` na regex JS). O comportamento foi conferido contra valores do changelog: Fe ρ = 7,880 g/cm³; Ti desvio +6,26 % (CR-01); Fe com 9 átomos desenhados (EX-03).

## 2. Rotas disponíveis (1.3)

| Rota | Servidor | Situação neste ambiente |
|---|---|---|
| `GET /api/bootstrap`, `/api/metais`, `/api/estruturas` | CrystaLab stdlib | Disponível |
| `GET/POST /api/estrutura` | CrystaLab stdlib | Disponível |
| `POST /api/miller` | CrystaLab stdlib | Disponível |
| `GET /health`, `/v1/crystals/metals`, `/v1/crystals/structures` | FastAPI 784017 | Indisponível (FastAPI) — reproduzido em `engine-stub/` só para testes |
| `POST /v1/crystals/structure`, `/v1/crystallography/miller`, `/v1/calculations/density` | FastAPI 784017 | Idem |
| `POST /v1/export/cif`, `/v1/export/xyz` | FastAPI 784017 | Idem |
| `GET /openapi.json`, `/docs` | FastAPI 784017 | **Indisponível** → não há contrato OpenAPI utilizável; contratos TypeScript escritos à mão (2.5) |
| `GET /api/bootstrap`, `POST /api/analyze` | HEA v1.17 | **Indisponível** (`hea_engine` ausente) |

## 3. Problemas encontrados (1.6)

### Organização
- HTML, CSS e JS vivem dentro de uma string Python (`HTML_TEMPLATE`); CSS duplicado quase integralmente entre HEA e CrystaLab.
- Estado global mutável (`state`) alterado por dezenas de funções; renderização por `innerHTML` com dados do servidor (risco de injeção, SE-02 do relatório de auditoria).
- Terminal implementado com expressões regulares encadeadas; `a=` significa massa atômica (`A`) porque o texto é convertido para minúsculas — ambíguo com o parâmetro de rede `a`.

### Interação
- Sem histórico de comandos, autocompletar, cancelamento ou desfazer.
- Planos e direções só podem ser removidos todos de uma vez; cores dependem da posição na lista.
- Resposta de Miller é descartada em silêncio quando a estrutura muda durante a requisição (FE-07).
- Blocos são `<article tabindex=0>` sem papel de botão: chegam pelo Tab, mas leitores de tela não os anunciam como acionáveis.

### Acessibilidade (auditoria própria, 12 regras — ver linha de base)
- Editor de parâmetros sem rótulo acessível (4.1.2).
- `outline: 0` em `#parameterEditor` e `#terminalInput`: foco invisível (2.4.7).
- Contraste: veredito da estrutura 2,77:1 (mínimo 3:1 para texto grande) e botão de alternância ativo 2,51:1 (mínimo 4,5:1).
- Legenda do viewer depende só de cor; canvas 3D sem descrição textual nem lista navegável.
- Botões de alternância sem `aria-pressed`; terminal sem `aria-live`.

### Desempenho
- `requestAnimationFrame` contínuo mesmo com a cena parada (consumo de GPU ociosa).
- Three.js r128 via CDN: sem internet o viewer some. **Observado nesta inspeção:** as duas requisições ao CDN falharam (`ERR_TUNNEL_CONNECTION_FAILED`) e a página mostrou o aviso de fallback.
- Página inteira servida com `Cache-Control: no-store` (70 kB recarregados a cada visita).
- Troca de tema reconstrói eixos e todos os overlays.

### Responsividade (360 px)
- Sem rolagem horizontal (bom).
- O viewer começa a 2.007 px do topo (≈ 3 telas de rolagem) e tem `touch-action: none`: um dedo sobre os 380 px do palco não rola a página.

## 4. Linha de base medida (1.7)

Equipamento: contêiner de nuvem Linux 6.18, Intel Xeon 2,8 GHz × 2 vCPU, 8 GB RAM, Chromium 141.0.7390.37 headless, WebGL por SwiftShader (renderização em CPU). **Não é o notebook intermediário do plano**; serve como referência relativa. Dados brutos: `reports/baseline/legacy-baseline.json`; capturas: `legacy-1366.png`, `legacy-360.png`.

| Medida | Resultado | Observação |
|---|---|---|
| Documento inicial | 70.072 B (17.386 B gzip) | HTML+CSS+JS inline; sem bundle |
| Dependências externas | 2 (Three.js r128 e OrbitControls, CDN) | Ambas falharam aqui |
| DOMContentLoaded / load | 361 ms / 362 ms | servidor local |
| Viewer 3D | Não renderiza (Three ausente) | FPS não mensurável; o rAF da página roda a 60,2 FPS sem cena |
| Auditoria de acessibilidade | 5 violações (1 nome, 2 contraste, 2 foco); 6 contrastes “a revisar” sobre gradiente | 18 controles, 213 textos, 30 passos de Tab |
| 360 px | sem rolagem horizontal; viewer a 2.007 px; página com 3.339 px | `touch-action: none` no palco |
| Lighthouse / axe-core | **Não medidos** | ferramentas indisponíveis (registro npm bloqueado) |
| Front HEA | **Não medido** | `hea_engine` ausente |

## 5. Classificação dos recursos (1.5)

| Recurso legado | Classe | Destino no novo front |
|---|---|---|
| Cálculos do motor (estrutura, FEA, densidade, Miller) | **Preserva** (não migra para o front) | Chamados via adaptadores `services/api` |
| Banco de blocos (metais + células genéricas) | Refatorar | `BlockBank` com papel de botão, filtros e arrastar-e-soltar |
| Editor de parâmetros (`elemento = …`) | Refatorar | `ParameterEditor` rotulado; mesmo formato de texto |
| Comandos `usar`, `estrutura`, `plano`, `direcao`, `calcular densidade`, `aplicar`, `listar`, `esferas`, `girar`, `eixos`, `tema`, `limpar`, `ajuda` | Preserva (sintaxe) / refatorar (implementação) | Gramática formal + barramento de operações; todos os comandos antigos continuam válidos |
| Atalhos (densidade, plano 111, direção 110, limpar) | Preserva | Mesmos rótulos, agora via barramento |
| Temas claro/escuro e chave `crystalab-theme` | Preserva | Migrados para tokens; a chave antiga é lida na primeira carga |
| Viewer 3D | Refatorar | Módulo sob demanda com Three.js local, render sob demanda |
| Métricas, tabela comparativa, átomos por célula, interpretação, passo a passo | Preserva (conteúdo) / refatorar (componentes) | `MetricCard`, `StepPanel`, KaTeX |
| Supercélulas, medições, seleção de átomos, poliedros, animações | Novo | Etapa 3 |
| Paleta de comandos, modo guiado, desfazer, URL compartilhável, workspaces, exportação | Novo | Etapa 4 |
| Ponte HEA → CrystaLab | Novo | Etapa 5 |
| Exercícios, ABP, quiz, diário, modo professor | Novo | Etapa 6 |
| PWA/offline, i18n | Novo | Etapas 2 e 7 |

## 6. `data-testid` existentes (1.8)

Encontrados no CrystaLab legado: `block-list`, `parameter-editor`, `terminal-log`, `render-button`, `result-root`, `viewer-stage`. No HEA legado (lido do código, não executado): `block-list`, `composition-editor`, `terminal-log`, `analyze-button`, `result-root`. Todos são mantidos no novo front; `scripts/lint.mjs` falha o build se algum desaparecer.

## 7. Entregáveis desta etapa

- `docs/etapa-1/backlog.md` — backlog com um épico por sugestão.
- `docs/etapa-1/matriz-dados-cientificos.md` — grandeza → origem → unidade → precisão → passos.
- `docs/etapa-1/registro-dependencias.md` — pendências de back-end (atualizado nas etapas seguintes).
- `reports/baseline/legacy-baseline.json` — medições brutas.
