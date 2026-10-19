# Changelog — CrystaLab (Módulo 1 do Alloy)

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) · versionamento semântico.
Os identificadores (EX-01, CR-03…) são os do *Relatório Técnico de Auditoria* de 18/10/2026.

## [1.1.0] — 2026-10-18 · Estabilização (fase 0 do plano de execução)

Versão de **correção e preparação**. Nenhuma funcionalidade didática nova; a interface
tem o mesmo layout, os mesmos comandos e os mesmos `data-testid` da v1.0.
Linha-base: `deepseek_python_20261012_784017.py` [D]. O rascunho truncado [C] foi descartado (QA-01).

### Corrigido — resultados errados
| Achado | O que era | O que é agora |
|---|---|---|
| EX-01 | CIF com comprimentos em nm | Å (Fe: `_cell_length_a 2.865967`) |
| EX-02 | HC com coordenadas cartesianas na coluna `fract` | frações reais em [0,1) |
| EX-03 | réplicas de fronteira exportadas (Fe 9 átomos, Cu 14, Mg 17) | só a base (Fe 2, Cu 4, Mg 2); Z correto |
| EX-04 | sempre `P 1` | Im-3m / Fm-3m / Pm-3m / P6₃/mmc + Wyckoff (2a, 4a, 1a, 2c) + operações de simetria explícitas |
| EX-05 | símbolo `XCFC` em células genéricas | pseudo-átomo `X` |
| EX-06 | cabeçalho incompleto | `_cell_volume`, `_cell_formula_units_Z`, densidade calculada, fórmula, peso, fonte |
| EX-07 | versão fixa no texto | lida de `crystalab.__version__` |
| CR-01 | Ti com +6,26 % de desvio | Ti usa a = 0,2951 nm e c = 0,4684 nm → 4,500 g/cm³ (−0,21 %); aviso automático se \|desvio\| > 3 % |
| CR-02 | Fe→CFC rotulado só como “editado”; c/a descartado em silêncio | avisos explícitos (Goldschmidt, c/a descartado/ignorado/ideal assumido) |
| CR-03 | (222) sem indicação de ordem | campos `ordem`, `indices_reduzidos` e aviso |
| CR-07 | base e réplicas misturadas | `base` (sítios únicos) separada de `atomos` (desenho) |
| CR-08 | arredondamento antes do cálculo (risco latente) | cálculo sem arredondar; **reproduzido**: 30 planos HC em −3…3 perdiam átomos ou tinham vértices duplicados na v1.0 |
| CR-09 | N_A = 6,022e23 | 6,02214076e23 (CODATA, exato) — Fe passa de 7,880 para 7,879 g/cm³ |
| — | `ValueError` de validador gerava resposta não serializável (500) | erro 422 serializável |
| — | editor da UI marcava Ti como “editado” ao re-renderizar (c/a com 4 casas) | tolerância relativa de 1e-4 |

### Corrigido — API e segurança
- BE-01 / FE-02: a UI usa somente `/v1/*`. `/api/*` congelada, validada pelos mesmos schemas e com cabeçalhos `Deprecation`, `Sunset` (30/06/2027) e `Link`.
- BE-02: handlers síncronos (`def`) → rodam no threadpool, sem bloquear o event loop.
- BE-03: página inicial montada uma vez na criação do app.
- BE-04 / BE-05 / BE-06: envelope de erro único `{ok, error, code, status, correlation_id?, details?}`; exceções de domínio (`ErroDominio`) → 400; `ValueError` interno → 500 sem vazar a mensagem (detalhe só no log, com correlation_id); mensagens de validação em português.
- BE-07: `atomos`, `base`, `grupo_espacial` tipados no OpenAPI.
- BE-09: rate limit ASGI puro, sem crescimento ilimitado (baldes limpos, LRU de clientes).
- BE-10 / SE-06: `CRYSTALAB_JWT_ENABLED=true` agora impede a inicialização com mensagem clara (antes derrubava a API); sem segredo padrão no código.
- BE-11: `uvicorn.run("crystalab.api.app:create_app", factory=True)` (permite `--reload`); navegador abre só quando o servidor aceita conexões.
- BE-12: CORS desligado por padrão (mesma origem); `*` proibido em produção; `/docs` só em desenvolvimento.
- BE-13: `Cache-Control` nas tabelas; ETag nos estáticos.
- BE-14: `/health/live` e `/health/ready` (mantido `/health`).
- BE-15: limite de corpo de 1 MB → HTTP 413 (com e sem Content-Length). Os servidores stdlib [B] deixam de ser usados.
- SE-01: Three.js r128 servido localmente (`web/static/vendor/three`, licença MIT incluída) — funciona sem internet.
- SE-02: nenhum `innerHTML` com dados; DOM montado com `h()` (texto sempre escapado).
- SE-03: bootstrap em `<script type="application/json">` com `<`, `>`, `&`, U+2028/2029 escapados.
- SE-04: CSP estrita (`script-src 'self'`, sem inline), `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `X-Frame-Options`.
- SE-05: entradas validadas por schema (faixas, NaN/∞ rejeitados, vírgula decimal aceita).

### Corrigido — front-end
- FE-01: HTML/CSS/JS fora da string Python, em `crystalab/web/`; JS em módulos ES.
- FE-03: renderização 3D sob demanda e pausada com a aba oculta.
- FE-07: aviso no terminal quando um resultado é descartado porque a estrutura mudou.
- FE-09 (parcial): `aria-live` no terminal, `aria-pressed` nos botões de alternância, foco visível, `prefers-reduced-motion`.

### Preparado para as próximas etapas (sem mudar comportamento)
- BE-08: motor único em `crystalab.core`, sem dependência de FastAPI.
- DB-01 / DB-03 / DB-05: dados em `core/dados/metais.json` (seed versionado, com unidades, fontes e validação na carga); acesso via protocolo `RepositorioMateriais` injetado por `Depends` — o futuro repositório PostgreSQL só precisa implementar os mesmos métodos.
- DB-04 (parcial): campos `a_nm`/`c_nm` (rede medida) com prioridade sobre a = k·R.
- Resolução de nomes à prova de choque: símbolo exato → sigla de estrutura → alias (um futuro “Cs” não captura a estrutura “CS”).
- Terminal com registro de comandos (`registrarComando`) — novos comandos não editam a função central.
- Manifesto do módulo (`crystalab/modulo.py`): prefixo `/crystalab`, porta 8010 (a matriz HEA usa 8000), comandos e prefixo de `localStorage`; `montar_em()` monta o módulo dentro da plataforma Alloy. A UI usa URLs relativas.
- QA-02 / QA-03 / QA-04 / QA-05 / BE-17: 72 testes (pytest + Playwright), `pyproject.toml`, ruff, `.editorconfig`, `.gitattributes` (LF), README e este CHANGELOG.

### Mudanças de contrato (todas aditivas)
- Respostas ganharam campos opcionais: `base`, `z`, `grupo_espacial`, `a_fonte`, `avisos`, `fonte` (célula); `ordem`, `indices_reduzidos`, `avisos` (Miller); `a_nm`, `c_nm`, `a_fonte`, `avisos` (densidade).
- Erros ganharam `code` e `status` (e `correlation_id` em 500). `error` continua presente.
- `content_type` do XYZ passou de `text/plain` para `chemical/x-xyz`; o XYZ agora é extXYZ (linha 2 com `Lattice=`).

### Fora do escopo desta versão (próximas etapas do relatório)
EX-08 (endpoint/botão de download), CR-04 (densidade linear por vetor de translação), CR-05 (d_rede × d_atômico),
CR-10 (edição/página das fontes), DB-02/06/07 (banco, usuários, importadores, cache), FE-04/05/06/08/10–14,
autenticação real (BE-10), observabilidade (métricas/tracing), Docker/CI.
