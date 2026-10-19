# CrystaLab 1.1 — Módulo 1 do Alloy (Fundamentos Estruturais)

Laboratório didático de cristalografia: células unitárias CS/CCC/CFC/HC, índices de Miller
(planos e direções, incluindo Miller-Bravais), fator de empacotamento, densidade teórica
passo a passo e exportação CIF/XYZ.

## Como rodar

```bash
python -m pip install -e .            # instala fastapi, uvicorn, pydantic, pydantic-settings
python -m crystalab --open            # http://127.0.0.1:8010 (busca a próxima porta livre)
```

Opções: `--port`, `--host`, `--reload` (desenvolvimento), `--log-level`.
Documentação interativa da API: `http://127.0.0.1:8010/docs` (só em ambiente de desenvolvimento).
Sem `pip install -e .`, rode a partir desta pasta com `pip install -r requirements.txt`.

## Testes

```bash
python -m pip install -e ".[dev]"     # pytest, httpx, ruff
pytest                                # motor, exportação, API
ruff check .
# opcionais: pip install gemmi  (valida CIF) · pip install playwright && playwright install chromium (UI)
```

## Estrutura

```
crystalab/
  __init__.py        versão única (__version__)
  __main__.py        linha de comando (python -m crystalab)
  modulo.py          manifesto do módulo para a plataforma Alloy
  core/              motor puro — SEM FastAPI (única cópia do motor)
    dados/           metais.json (seed versionado) e interpretacoes.json (textos pt-BR)
    repositorio.py   protocolo RepositorioMateriais + implementação JSON
    estruturas.py    tipos de estrutura, grupos espaciais, base cristalográfica
    geometria.py     vetores, conversões, geometria da célula
    celula.py        célula unitária, densidade, passo a passo, avisos
    miller.py        planos e direções
    exportacao.py    CIF e extXYZ
  api/               FastAPI: app factory, rotas v1, rotas legadas, erros, segurança
  web/               index.html + static/ (css, js em módulos ES, Three.js local)
tests/               pytest (+ Playwright opcional)
```

## Regras para as próximas adições (evitar choques)

1. **Um motor só.** Cálculo novo entra em `crystalab/core/` como função pura e é importado pela API. Nunca copie funções para outro arquivo.
2. **Dados não são código.** Material novo ou correção de valor = editar `core/dados/metais.json` (unidades fixas por campo, fonte obrigatória). O repositório valida o arquivo ao iniciar e recusa dados incoerentes. Quando o banco chegar, crie uma classe que implemente `RepositorioMateriais` e passe em `create_app(repositorio=...)`.
3. **Contrato v1 só cresce.** Campo novo de resposta: opcional ou com valor padrão. Remover/renomear campo exige `/v2`. As rotas `/api/*` estão congeladas — não adicione nada nelas.
4. **Erros de usuário** levantam subclasses de `ErroDominio` (viram 400 com `code`). Qualquer outra exceção é tratada como bug (500, sem detalhe para o cliente).
5. **Front-end:** dados da API entram no DOM só via `h()` (nunca `innerHTML`); novos comandos de terminal com `registrarComando()` em um arquivo próprio; URLs sempre relativas; chaves de `localStorage` com o prefixo `crystalab-`.
6. **Sem CDN.** Bibliotecas de terceiros vão para `web/static/vendor/` com a licença.
7. **Integração com o Alloy:** porta própria (8010), prefixo `/crystalab`. Veja `crystalab/modulo.py`.

## Configuração (variáveis de ambiente `CRYSTALAB_*`)

Veja `crystalab/api/config.py` e `.env.example`. Em produção: `CRYSTALAB_ENVIRONMENT=production`
(desliga `/docs`, proíbe CORS `*`). `CRYSTALAB_JWT_ENABLED` ainda não é suportado e impede a inicialização.

## Dados e fontes

Valores de raio, peso e densidade: Callister & Rethwisch (Tabela 3.1 e apêndices) — edição e página
ainda a registrar. Parâmetros de rede do α-Ti (a = 0,2951 nm; c = 0,4684 nm): indicados pelo relatório
de auditoria (CR-01), **a conferir na fonte primária**.
