"""Regras de dependência entre camadas (ARQUITETURA_FINAL §2, ADR-004, RQ-ARQ-02/03).

Análise estática dos imports com ``ast``: não executa o código analisado.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "app"

#: camada → prefixos de import proibidos
PROIBIDOS = {
    "engines": ("app.api", "app.services", "app.repositories", "app.models", "app.security",
                "app.educational", "app.integrations", "app.core", "fastapi", "sqlalchemy", "pydantic"),
    "repositories": ("app.api", "app.services", "app.educational"),
    "models": ("app.api", "app.services", "app.repositories", "app.engines"),
    "services": ("app.api", "fastapi"),
    "api": ("app.repositories", "app.models", "app.engines", "sqlalchemy"),
}
#: Importações de motor aceitas na camada api: só contrato (faixas, tipos de erro, normalização de tipo),
#: nunca funções de cálculo — essas passam pelos serviços.
EXCECOES = {"api": {"app.engines.crystallography.constantes", "app.engines.crystallography.erros",
                    "app.engines.crystallography.miller"}}
#: módulos de I/O vetados dentro dos motores (puros)
IO_PROIBIDO_NOS_MOTORES = ("open", "pathlib", "os", "io", "socket", "urllib", "http", "sqlite3", "subprocess")


def _modulos(camada: str):
    return sorted((APP / camada).rglob("*.py"))


def _imports(arquivo: Path):
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    pacote = ".".join(arquivo.relative_to(APP.parent).with_suffix("").parts[:-1])
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                yield alias.name, no.lineno
        elif isinstance(no, ast.ImportFrom):
            if no.level:
                base = pacote.split(".")
                base = base[: len(base) - (no.level - 1)]
                nome = ".".join(base + ([no.module] if no.module else []))
            else:
                nome = no.module or ""
            yield nome, no.lineno


@pytest.mark.parametrize("camada", list(PROIBIDOS))
def test_camada_nao_importa_o_que_e_proibido(camada):
    violacoes = []
    for arquivo in _modulos(camada):
        for nome, linha in _imports(arquivo):
            if nome in EXCECOES.get(camada, ()):
                continue
            if any(nome == p or nome.startswith(p + ".") for p in PROIBIDOS[camada]):
                violacoes.append(f"{arquivo.relative_to(APP)}:{linha} importa {nome}")
    assert not violacoes, "\n".join(violacoes)


def test_motores_nao_fazem_entrada_e_saida():
    violacoes = []
    for arquivo in _modulos("engines"):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        for nome, linha in _imports(arquivo):
            if nome.split(".")[0] in IO_PROIBIDO_NOS_MOTORES:
                violacoes.append(f"{arquivo.relative_to(APP)}:{linha} importa {nome}")
        for no in ast.walk(arvore):
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == "open":
                violacoes.append(f"{arquivo.relative_to(APP)}:{no.lineno} chama open()")
    assert not violacoes, "\n".join(violacoes)


def test_constante_de_avogadro_so_existe_em_um_lugar():
    """PI-03 / CIE-02: uma única definição de N_A (CODATA 2018)."""
    definicoes = []
    for arquivo in APP.rglob("*.py"):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            alvos = []
            if isinstance(no, ast.Assign):
                alvos = [t.id for t in no.targets if isinstance(t, ast.Name)]
            elif isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
                alvos = [no.target.id]
            if "N_AVOGADRO" in alvos:
                definicoes.append(str(arquivo.relative_to(APP)))
    assert definicoes == [str(Path("engines/crystallography/constantes.py"))]
