# Design system

Base: o design system do alloy-frontend (projeto C), preservado na consolidação (ADR-010).
Código: `frontend/src/design-system/`.

## 1. Tokens (`tokens.css`)

219 variáveis CSS; os temas claro e escuro só redefinem tokens, sem trocar componentes. Grupos:

| Grupo | Prefixo | Uso |
|---|---|---|
| Cor | `--color-*` | superfícies, texto, bordas, ações, estados |
| Categoria de informação | `--cat-*` | resultado, parâmetro, referência, controle, feedback, demonstrativo, nota |
| Gráficos | `--chart-*`, `--axis-*` | séries e eixos legíveis nos dois temas |
| Laboratório e viewer | `--lab-*`, `--viewer-*`, `--site-*` | cena 3D, sítios atômicos, terminal |
| Tipografia | `--fs-2xs` … `--fs-2xl`, `--fs-metric` | escala de 11 px a 23 px |
| Espaço | `--space-1` … | múltiplos de 4 px |

**Regra R7 do lint:** cores literais (`#hex`, `rgb()`) só podem aparecer em `tokens.css` e `print.css`.
**Teste:** `tests/unit/i18n-tokens.test.ts` mede o contraste WCAG 2.2 AA dos pares usados pelos
componentes nos dois temas (texto ≥ 4,5:1, elementos gráficos ≥ 3:1).

## 2. Categorias de informação

Toda caixa de conteúdo declara uma categoria (`CategoryBox`, `CategoryTag`). Cada categoria tem cor
e ícone, e um leitor de tela também a identifica:

`result` (cálculo do servidor) · `param` (entrada) · `reference` (literatura) · `control` · `feedback` ·
`demo` (sempre com `DemoSeal`) · `note`.

Na consolidação, o HEA ganhou o padrão **indisponível com motivo**: o painel `hea-unavailable` (categoria
`feedback`) lista cada grandeza não calculada com o motivo devolvido pelo servidor. Nada aparece em
branco e nada é estimado no cliente.

## 3. Componentes

| Camada | Componentes |
|---|---|
| Primitivos | `Button`, `IconButton`, `ToggleButton`, `TextInput`, `TextArea`, `Select`, `Checkbox`, `Segmented`, `Slider`, `Tabs`/`TabPanel`, `Dialog`, `Disclosure`, `Menu`, `Tooltip`, `Toast`, `Badge`, `Spinner`, `Kbd`, `VisuallyHidden` |
| Layout | `AppShell` (com link "pular para o conteúdo"), `ModuleNavigation`, `Workbench`, `Panel`, `MetricCard`, `StepPanel`, `SettingsPanel` |
| Utilidades | `Icon` (SVG próprio; o módulo `#/conta` usa `lock`/`unlock`), `announce` (região ao vivo) |

## 4. Acessibilidade

Foco vai para o `<main>` a cada troca de módulo; toda ação tem teclado (paleta Ctrl/⌘K); erros de
campo ficam ligados por `aria-describedby` e anunciados com `role="alert"`; os gráficos SVG têm
descrição textual e tabela de dados. E2E: `tests/e2e/a11y-keyboard.spec.ts`.

## 5. Idiomas

pt-BR (referência), en e es. Tabelas-fonte: `src/i18n/source/*.tsv`. Os catálogos em `src/i18n/locales/`
são gerados por `npm run i18n`. Os testes verificam três coisas: todas as chaves existem nos três idiomas,
os marcadores são os mesmos e nenhuma chave fica sem uso (regra R9 do lint). Hoje: 995 chaves × 3 idiomas.
