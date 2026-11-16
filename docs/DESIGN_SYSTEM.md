# Design system

Base: o design system do alloy-frontend (projeto C), preservado na consolidação (ADR-010).
Identidade visual "Carvão, Areia e Azul" desde 10/11/2026 (registro em
[`REFORMA_VISUAL.md`](REFORMA_VISUAL.md)). Código: `frontend/src/design-system/`.

## 1. Identidade

Três cores oficiais, cada uma com um papel:

| Cor | Hex | Papel | Onde aparece |
|---|---|---|---|
| Carvão | `#1E1E1C` | estrutura | cabeçalho, painel do laboratório, terminal, faixas de título, texto sobre areia e papel |
| Areia | `#D8CBB3` | área de trabalho | fundo da página no tema claro; títulos e texto sobre carvão; etiquetas de estrutura |
| Azul | `#2F6BFF` | sinal | página ativa, seleção, foco, progresso, série principal dos gráficos, átomos de vértice |

A composição do tema claro é uma moldura em carvão (cabeçalho, painel esquerdo e faixa de título)
em volta de folhas de papel (`#F3EDE1`) pousadas na areia. No tema escuro a página inteira é carvão e a
areia vira a cor do texto e dos preenchimentos neutros.

Regras de uso do azul:

* O azul oficial não serve de fundo para texto: branco sobre `#2F6BFF` dá 4,499:1. O botão primário usa
  o **azul de ação** `#2A63F2` (4,9:1 com branco), derivado do oficial.
* O azul oficial sobre a areia dá 2,81:1. Indicadores azuis ficam sobre papel ou carvão. Texto azul usa
  `--blue-700` (`#1A44C2`) no tema claro e `--blue-300` (`#9DB8FF`) no escuro.
* Uma tela tem uma ação primária azul. O destaque secundário é o preenchimento neutro
  (`--color-solid`): carvão no tema claro, areia no escuro.

## 2. Tokens (`tokens.css`)

Os temas claro e escuro só redefinem tokens, sem trocar componentes. Grupos:

| Grupo | Prefixo | Uso |
|---|---|---|
| Marca e escalas | `--brand-*`, `--charcoal-*`, `--sand-*`, `--blue-*` | cores oficiais e tons derivados |
| Cor semântica | `--color-*` | superfícies (`bg`, `surface`, `surface-2`, `surface-raised`, `surface-sunken`), texto, bordas, ação (`primary`), neutro forte (`solid`), sinal (`signal`), estados |
| Interação | `--state-*`, `--focus-*` | hover, pressionado, selecionado, foco |
| Categoria de informação | `--cat-*` | resultado, parâmetro, referência, controle, feedback, demonstrativo, nota |
| Gráficos | `--chart-*`, `--axis-*` | séries e eixos legíveis nos dois temas |
| Laboratório e viewer | `--lab-*`, `--term-*`, `--tag-*`, `--viewer-*`, `--site-*` | moldura em carvão, terminal, etiquetas de estrutura, cena 3D |
| Tipografia | `--font-*`, `--fs-2xs` … `--fs-3xl`, `--fs-metric`, `--fw-*`, `--lh-*` | escala de 12 px a 32 px; pesos 400, 500 e 600 |
| Espaço | `--space-1` … `--space-16` | múltiplos de 4 px (4 a 64 px) |
| Forma | `--radius-xs` (4), `--radius-sm` (6), `--radius` (10), `--radius-lg` (14), `--radius-pill` | controles 6 px, cartões 10 px, diálogos 14 px; pílula só para estado e contagem |
| Layout | `--header-h`, `--lab-w`, `--side-w`, `--content-max`, `--gutter`, `--control-h` | controles de 36 px (40 px em telas de toque) |

**Região em carvão dentro do tema claro:** a classe `.ds-on-dark` aplica o conjunto de tokens do tema
escuro a uma região (cabeçalho, `.topbar`, `.module-head`). Botões, campos e menus ali dentro leem os
tokens escuros sem regras próprias.

**Regra R7 do lint:** cores literais (`#hex`, `rgb()`) só podem aparecer em `tokens.css` e `print.css`.
**Teste:** `tests/unit/i18n-tokens.test.ts` mede o contraste WCAG 2.2 AA dos pares usados pelos
componentes nos dois temas (texto ≥ 4,5:1, elementos gráficos ≥ 3:1), incluindo os pares da identidade
nova. A auditoria E2E (`tests/e2e/a11y-keyboard.spec.ts`) mede o contraste real em cada rota.

## 3. Tipografia

* **IBM Plex Sans** (400, 500, 600) para a interface e **IBM Plex Mono** (400, 500) só para terminal,
  código, siglas e contagens. Servidas pelo próprio site (`fonts.css`, pacotes `@fontsource`, licença
  OFL), com os subconjuntos latim, latim estendido e grego. Funcionam offline e sob a CSP.
* Hierarquia: título de página `--fs-3xl` (faixa em carvão), título de resultado `--fs-2xl`, título de
  painel `--fs-md` em peso 600, corpo `--fs-md`/`--fs-sm`, rótulo `--fs-2xs` em peso 500 e cor atenuada.
* Rótulos em caixa normal. Só o selo "DEMONSTRATIVO" usa maiúsculas.
* Números de métrica e de tabela usam algarismos tabulares.

## 4. Categorias de informação

Toda caixa de conteúdo declara uma categoria (`CategoryBox`, `CategoryTag`). Cada categoria tem ícone,
rótulo textual e padrão de borda próprios; a cor nunca é o único código.

| Categoria | Sinal visual |
|---|---|
| `result` (cálculo do servidor) | filete azul à esquerda; nos cartões de métrica, o ícone de cálculo |
| `param` (entrada) | borda tracejada, papel claro |
| `reference` (literatura) | fundo de areia mais escura, filete neutro |
| `control` | borda pontilhada |
| `feedback` | fundo verde-claro, borda esquerda de 3 px |
| `demo` (sempre com `DemoSeal`) | hachurado diagonal ocre e selo |
| `note` | borda tracejada sépia |

O HEA mantém o padrão **indisponível com motivo**: o painel `hea-unavailable` (categoria `feedback`)
lista cada grandeza não calculada com o motivo devolvido pelo servidor.

## 5. Componentes

| Camada | Componentes |
|---|---|
| Primitivos | `Button`, `IconButton`, `ToggleButton`, `TextInput`, `TextArea`, `Select`, `Checkbox`, `Segmented`, `Slider`, `Tabs`/`TabPanel`, `Dialog`, `Disclosure`, `Menu`, `Tooltip`, `Toast`, `Badge`, `Spinner`, `Kbd`, `VisuallyHidden` |
| Layout | `AppShell` (com link "pular para o conteúdo"), `ModuleNavigation`, `Workbench`, `Panel`, `MetricCard`, `StepPanel`, `SettingsPanel` |
| Utilidades | `Icon` (SVG próprio), `announce` (região ao vivo) |

Variantes de botão:

| Variante | Aparência | Uso |
|---|---|---|
| `primary` | azul de ação, texto branco | a ação principal da tela ou do formulário |
| `accent` | preenchimento neutro forte | ação de destaque que não é a principal |
| `secondary` (padrão) | papel elevado com borda | ações comuns |
| `ghost` | sem borda | ações de baixa ênfase e ícones |
| `danger` | borda e texto vermelhos sobre papel | ações destrutivas |
| `lab` | carvão | dentro do painel do laboratório |

Estados dos campos (`.ds-input`): normal, hover (borda mais escura), foco (borda e anel azuis),
preenchido, inválido (borda dupla vermelha e mensagem com marca "!"), desabilitado (borda tracejada,
fundo atenuado) e ocupado (`aria-busy`).

Padrões de página:

* **Faixa de título** (`.module-head.ds-on-dark`): carvão de ponta a ponta, título em areia, texto de
  apoio com até 68 caracteres por linha. A trilha de navegação (`.breadcrumb`) fica dentro da faixa.
* **Folha de papel**: painéis, cartões e a área de resolução dos exercícios são superfícies
  `--color-surface` com borda de 1 px, sem sombra. Sombra só em menus, diálogos e notificações.
* **Tabela**: cabeçalho em preenchimento neutro forte, linhas com filete, linha atual com filete azul.
* **Palco 3D** (`.viewer-stage`): fundo plano com grade de 32 px, sem gradiente.
* **Métricas** (`.metrics-grid`): 3 por linha; 6 quando a coluna passa de 1080 px e 2 abaixo de 520 px
  (container queries).

## 6. Acessibilidade

Foco vai para o `<main>` a cada troca de módulo; toda ação tem teclado (paleta Ctrl/⌘K); erros de
campo ficam ligados por `aria-describedby` e anunciados com `role="alert"`; os gráficos SVG têm
descrição textual e tabela de dados. O anel de foco tem 2 px na cor `--focus-color`
(≥ 3:1 sobre areia, papel e carvão). `prefers-reduced-motion` zera as transições.
E2E: `tests/e2e/a11y-keyboard.spec.ts`.

## 7. Idiomas

pt-BR (referência), en e es. Tabelas-fonte: `src/i18n/source/*.tsv`. Os catálogos em `src/i18n/locales/`
são gerados por `npm run i18n`. Os testes verificam três coisas: todas as chaves existem nos três idiomas,
os marcadores são os mesmos e nenhuma chave fica sem uso (regra R9 do lint).
