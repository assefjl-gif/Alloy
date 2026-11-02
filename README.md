# Alloy Virtual Lab — consolidação

Workspace da versão unificada do Alloy Virtual Lab (CrystaLab + HEA + módulos educacionais).

**Estado atual: Fase 1 (auditoria) concluída; aguardando o Gate 0.** Ainda não há código consolidado.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `_origem/` | As quatro bases recebidas, **intactas** (commit inicial `2a6f79a`). Não editar. |
| `_auditoria/` | Scripts e dados reproduzíveis da auditoria |
| `docs/` | `REQUISITOS_BASE.md` (requisitos derivados do Prompt Mestre) e `RELATORIO_AUDITORIA_GERAL.md` |

## Reproduzir a auditoria (Windows, Git Bash)

```bash
python -m venv .venv
.venv/Scripts/python -m pip install "fastapi>=0.110" "uvicorn>=0.29" "pydantic>=2.6" "pydantic-settings>=2.2" pytest httpx ruff
.venv/Scripts/python -X utf8 _auditoria/comparar_motores.py
```

Testes da base B:

```bash
cd _origem/B_crystalab_v1.1.0/crystalab && ../../../.venv/Scripts/python -m pytest -q --ignore=tests/test_ui_e2e.py
```

Contrato B ↔ C (com a API B rodando na porta 8120):

```bash
cd _origem/C_alloy_frontend/alloy-frontend && npm install && cd ../../..
_origem/C_alloy_frontend/alloy-frontend/node_modules/.bin/tsx _auditoria/contrato_b_c.mts http://127.0.0.1:8120
```
