"""Identidade dos 118 elementos para a validação de entrada do motor HEA (decisão D-1 do portão G1).

Lê do seed da tabela periódica SOMENTE identidade e classificação: símbolo, nome, número atômico,
categoria e grupo. Nenhum valor de propriedade (massa, raio, temperatura de fusão) é lido aqui: o
motor HEA continua usando só o repositório de materiais (ADR-018 mantido).

A lista de símbolos é a mesma em qualquer ambiente (com ou sem banco): identidade não é dado versionado
por validação. Por isso o leitor usa o seed embutido, como já se faz com os textos de interpretação.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Mapping

from app.engines.crystallography.erros import ErroDeDados
from app.engines.hea.referencia import IdentidadeElemento

from .materiais_json import PASTA_SEEDS

CAMINHO_TABELA = PASTA_SEEDS.parent / "tabela_periodica" / "elementos.json"
TOTAL_ELEMENTOS = 118


def carregar_identidades(caminho: Path = CAMINHO_TABELA) -> Mapping[str, IdentidadeElemento]:
    try:
        bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ErroDeDados(f"Não foi possível ler a tabela periódica ({Path(caminho).name}): {exc}") from exc
    identidades: Dict[str, IdentidadeElemento] = {}
    for registro in sorted(bruto.get("elementos") or [], key=lambda e: e["numero_atomico"]):
        simbolo = str(registro["simbolo"])
        if simbolo in identidades:
            raise ErroDeDados(f"{Path(caminho).name}: símbolo duplicado '{simbolo}'.")
        grupo = registro.get("grupo")
        identidades[simbolo] = IdentidadeElemento(
            simbolo=simbolo, nome=str(registro["nome"]), numero_atomico=int(registro["numero_atomico"]),
            categoria=str(registro["categoria"]), grupo=None if grupo is None else int(grupo))
    if len(identidades) != TOTAL_ELEMENTOS:
        raise ErroDeDados(f"{Path(caminho).name}: esperados {TOTAL_ELEMENTOS} elementos, lidos {len(identidades)}.")
    return MappingProxyType(identidades)


@lru_cache(maxsize=1)
def identidades_padrao() -> Mapping[str, IdentidadeElemento]:
    """Instância compartilhada (carregada e conferida uma única vez)."""
    return carregar_identidades()
