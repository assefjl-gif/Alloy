"""Tabelas públicas e payload de inicialização da UI."""

from __future__ import annotations

from typing import Any, Dict, List

from .celula import calcular_estrutura
from .estruturas import ESTRUTURAS
from .geometria import fator_empacotamento
from .referencia import RepositorioMateriais


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


def metais_publicos(repo: RepositorioMateriais) -> Dict[str, Dict[str, Any]]:
    return {metal.simbolo: metal.publico() for metal in repo.listar()}


def bootstrap(repo: RepositorioMateriais) -> Dict[str, Any]:
    return {
        "metais": metais_publicos(repo),
        "estruturas": tabela_estruturas(),
        "inicial": calcular_estrutura({"nome": "Fe"}, repo),
        "versao_dados": repo.versao_dados,
    }
