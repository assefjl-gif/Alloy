"""Tabelas públicas e payload de inicialização da UI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .celula import calcular_estrutura
from .estruturas import ESTRUTURAS
from .geometria import fator_empacotamento
from .repositorio import RepositorioMateriais, repositorio_padrao


def tabela_estruturas() -> List[Dict[str, Any]]:
    return [
        {
            "sigla": sigla, "nome": info["nome"],
            "n": info["n"], "nc": info["nc"],
            "a_em_R": info["a_em_R"], "relacao": info["relacao"],
            "fea": fator_empacotamento(sigla, info.get("c_a_ideal")),
        }
        for sigla, info in ESTRUTURAS.items()
    ]


def metais_publicos(repo: Optional[RepositorioMateriais] = None) -> Dict[str, Dict[str, Any]]:
    repo = repo or repositorio_padrao()
    return {metal.simbolo: metal.publico() for metal in repo.listar()}


def bootstrap(repo: Optional[RepositorioMateriais] = None) -> Dict[str, Any]:
    repo = repo or repositorio_padrao()
    return {
        "metais": metais_publicos(repo),
        "estruturas": tabela_estruturas(),
        "inicial": calcular_estrutura({"nome": "Fe"}, repo),
        "versao_dados": repo.versao_dados,
    }
