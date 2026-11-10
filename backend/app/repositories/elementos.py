"""Tabela periódica: leitura dos 118 elementos e das propriedades atômicas (ADR-018).

Dois repositórios com a MESMA saída (testado campo a campo):
* ``RepositorioElementosJSON`` — seed embutido (ambiente sem banco);
* ``RepositorioElementosSQL`` — banco; duas consultas por chamada (elementos + propriedades vigentes),
  sem N+1, independentemente do número de elementos pedidos.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Elemento, Fonte, Propriedade, PropriedadeElemento, VersaoDados

from .materiais_json import PASTA_SEEDS

CAMINHO_TABELA = PASTA_SEEDS.parent / "tabela_periodica" / "elementos.json"
CAMPOS = ("numero_atomico", "simbolo", "nome", "nome_en", "periodo", "grupo", "bloco", "categoria",
          "configuracao_eletronica", "estados_oxidacao", "estado_padrao", "ano_descoberta", "conhecido_antiguidade")


class RepositorioElementos(Protocol):
    versao_dados: str

    def listar(self) -> List[Dict[str, Any]]: ...

    def fontes(self) -> Dict[str, Dict[str, Any]]: ...


def _f(valor: Any) -> Optional[float]:
    return None if valor is None else float(valor)


def _propriedade(codigo: str, nome: str, valor: Any, incerteza: Any, vmin: Any, vmax: Any, unidade: str,
                 fonte: str, estado: str, nota: Optional[str]) -> Dict[str, Any]:
    return {"codigo": codigo, "nome": nome, "valor": _f(valor), "incerteza": _f(incerteza),
            "intervalo": [_f(vmin), _f(vmax)] if vmin is not None and vmax is not None else None,
            "unidade": unidade, "fonte": fonte, "estado": estado, "nota": nota}


class RepositorioElementosJSON:
    def __init__(self, caminho: Path = CAMINHO_TABELA) -> None:
        bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
        from .seed_sql import CATALOGO_PROPRIEDADES  # nomes legíveis das propriedades (mesmo catálogo do banco)

        self.versao_dados: str = str(bruto["versao_dados"])
        chaves = ("tipo", "citacao", "doi", "url", "licenca", "versao_fonte", "acessado_em")
        self._fontes = {k: {c: v.get(c) for c in chaves} for k, v in bruto["fontes"].items()}
        self._elementos = []
        for e in sorted(bruto["elementos"], key=lambda x: x["numero_atomico"]):
            item = {c: e[c] for c in CAMPOS}
            item["propriedades"] = sorted((
                _propriedade(p["codigo"], CATALOGO_PROPRIEDADES[p["codigo"]][0], p["valor"], p.get("incerteza"),
                             p.get("intervalo_min"), p.get("intervalo_max"), p["unidade"], p["fonte"],
                             "aguardando_validacao", p.get("nota"))
                for p in e["propriedades"]), key=lambda p: p["codigo"])
            self._elementos.append(item)

    def listar(self) -> List[Dict[str, Any]]:
        return self._elementos

    def fontes(self) -> Dict[str, Dict[str, Any]]:
        return self._fontes


@lru_cache(maxsize=1)
def repositorio_elementos_padrao() -> RepositorioElementosJSON:
    return RepositorioElementosJSON()


class RepositorioElementosSQL:
    def __init__(self, sessao: Session) -> None:
        self.sessao = sessao
        versao = sessao.get(VersaoDados, "tabela_periodica")
        self.versao_dados = versao.versao if versao else "não carregada"

    def listar(self) -> List[Dict[str, Any]]:
        nomes = dict(self.sessao.execute(select(Propriedade.codigo, Propriedade.nome)).all())
        props: Dict[str, List[Dict[str, Any]]] = {}
        for p in self.sessao.scalars(select(PropriedadeElemento).where(PropriedadeElemento.vigente.is_(True))
                                     .order_by(PropriedadeElemento.elemento_simbolo,
                                               PropriedadeElemento.propriedade_codigo)):
            props.setdefault(p.elemento_simbolo, []).append(_propriedade(
                p.propriedade_codigo, nomes.get(p.propriedade_codigo, p.propriedade_codigo), p.valor, p.incerteza,
                p.intervalo_min, p.intervalo_max, p.unidade, p.fonte_id, p.estado, p.nota))
        out = []
        for e in self.sessao.scalars(select(Elemento).where(Elemento.numero_atomico.is_not(None))
                                     .order_by(Elemento.numero_atomico)):
            item = {c: getattr(e, c) for c in CAMPOS}
            item["propriedades"] = props.get(e.simbolo, [])
            out.append(item)
        return out

    def fontes(self) -> Dict[str, Dict[str, Any]]:
        usadas = set(self.sessao.scalars(select(PropriedadeElemento.fonte_id).distinct()))
        return {f.id: {"tipo": f.tipo, "citacao": f.citacao, "doi": f.doi, "url": f.url, "licenca": f.licenca,
                       "versao_fonte": f.versao_fonte,
                       "acessado_em": f.acessado_em.isoformat() if f.acessado_em else None}
                for f in self.sessao.scalars(select(Fonte).where(Fonte.id.in_(usadas | {"wikipedia_pt_elementos"})))}


class RetratoElementos:
    """Cópia imutável da tabela periódica lida do banco (para o cache de retratos)."""

    def __init__(self, repo: RepositorioElementos) -> None:
        self.versao_dados = repo.versao_dados
        self._elementos = repo.listar()
        self._fontes = repo.fontes()

    def listar(self) -> List[Dict[str, Any]]:
        return self._elementos

    def fontes(self) -> Dict[str, Dict[str, Any]]:
        return self._fontes


def retrato_elementos(sessao: Session) -> RetratoElementos:
    """Retrato em cache, conferido pela versão dos dados a cada chamada (ver ``cache_dados``)."""
    from .cache_dados import cache_retratos, chave_retrato

    return cache_retratos.obter(chave_retrato(sessao, "elementos"),
                                lambda: RetratoElementos(RepositorioElementosSQL(sessao)))
