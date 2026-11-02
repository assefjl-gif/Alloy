# Alloy Virtual Lab — front-end (HEA Virtual Lab + CrystaLab)

Plataforma única onde o HEA Virtual Lab e o CrystaLab convivem sem recarga. Todo valor científico vem dos motores; o front-end só exibe, organiza e valida.

Todas as 8 etapas do plano foram executadas — ver `docs/relatorio-conclusao.md` (resumo, metas medidas, pendências) e os relatórios por etapa em `docs/`.

## Requisitos

Node 22, Python 3.10+ (motor CrystaLab v1.0, só biblioteca padrão) e Chromium para os testes.

## Instalação

```bash
npm ci                     # com acesso ao registro npm
node scripts/link-deps.mjs # alternativa usada neste ambiente (dependências locais + vendor/)
```

## Execução

**Um comando só (recomendado):**

```bash
npm install      # uma vez (no PowerShell: npm.cmd install)
npm start        # compila, sobe CrystaLab (:8010) e HEA (:8000, se completo), serve em http://127.0.0.1:5173 e abre o navegador
```

`npm start` localiza o Python sozinho (`py -3`, `python` ou `python3`), reaproveita motores já abertos em outro terminal e encerra tudo com Ctrl+C. Opções: `npm run start:fast` (pula a compilação, usa `dist/`), `npm run dev:all` (recompila ao salvar), `--no-open` (não abre o navegador: `npm start -- --no-open`). Portas por variável: `PORT`, `CRYSTALAB_PORT`, `HEA_PORT`; interpretador específico: `PYTHON`.

**Motor HEA:** precisa de `legacy/pesquisa_front1.17.py` **e** `legacy/hea_engine.py` (pendência D-01: o `hea_engine.py` não está no repositório). Sem eles, o módulo HEA abre em modo demonstrativo rotulado; nada é inventado em silêncio.

**Passo a passo manual (3 terminais), se preferir:**

```bash
npm run engine   # motor CrystaLab v1.0 em :8010 (legacy/crystalab_modulo1.py)
npm run hea      # motor HEA em :8000 (precisa de legacy/hea_engine.py)
npm run build && npm run serve   # http://127.0.0.1:5173 — proxy /engines/crystalab → :8010, /engines/hea → :8000
```

Configuração sem recompilar em `dist/config.js` (`crystalabBase`, `heaBase`, `demo: auto|on|off`). `?demo=1` força o modo demonstrativo. A interface legada continua em `/legacy/crystalab/`.

## Qualidade

```bash
npm run typecheck   # TypeScript estrito (app, service worker, testes)
npm run lint        # regras do projeto (scripts/lint.mjs)
npm test            # testes unitários e de adaptadores (sobem o motor real)
npm run measure     # orçamento do bundle inicial (< 300 kB gzip, sem Three.js)
npm run e2e:etapa2  # Playwright: troca de módulo sem recarga, tema, idioma, data-testid
npm run e2e:etapa3  # viewer 3D + métricas (reports/metrics.json)
npm run e2e:etapa4  # terminal, paleta, modo guiado, Fluxos A e B, acessibilidade/teclado
npm run e2e:etapas5-7  # Fluxos C, D, E, didática, acessibilidade, PWA offline
npm run e2e         # todos os fluxos (54 testes)
npm run i18n        # regenera src/i18n/locales/ a partir de src/i18n/source/*.tsv
```

## Estrutura

```
src/app            shell, roteador por hash, inicialização
src/design-system  tokens, temas, primitivos acessíveis, layout (alloy-ui)
src/services       api/ (HTTP, contratos zod, cancelamento) · adapters/ (modo demonstrativo)
src/stores         estado por domínio (Zustand) com histórico
src/modules        crystalab, hea, didactics, notebook, instructor, catalog, about
src/features       viewer 3D, terminal, paleta, URL de cena, exportação, PWA
src/i18n           pt-BR (referência), en, es — gerados de source/*.tsv
legacy/            motor e interface CrystaLab v1.0 (preservados)
engine-stub/       servidor de contrato /v1 (somente testes)
docs/              relatórios por etapa
```

## Desvios registrados

esbuild no lugar do Vite e lint próprio no lugar do ESLint (registro npm bloqueado — D-19); contratos TypeScript manuais (sem OpenAPI executável — D-15); HEA em modo demonstrativo (motor ausente — D-01). Lista completa em `docs/etapa-1/registro-dependencias.md`.
