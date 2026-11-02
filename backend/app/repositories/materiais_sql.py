"""Repositório de materiais lido do banco (PostgreSQL em produção).

Cumpre ``RepositorioMateriais`` (motor cristalográfico) e ``RepositorioPropriedades``
(ligas, temperatura). Lê um RETRATO consistente dos valores vigentes numa única transação
e o mantém em memória: o catálogo é pequeno e os motores fazem muitas consultas por cálculo.
Textos didáticos de interpretação (não são dado científico) continuam no seed JSON.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.crystallography.estruturas import sem_acentos
from app.engines.crystallography.referencia import Metal
from app.engines.procedencia import TransicaoAlotropica, ValorReferencia
from app.models import Fonte, Material, MaterialEstrutura, ValorPropriedade, VersaoDados

from .materiais_json import CAMINHO_INTERPRETACOES


def _f(valor: Any) -> Optional[float]:
    return None if valor is None else float(valor)


class RepositorioSQL:
    def __init__(self, sessao: Session, caminho_interpretacoes: Path = CAMINHO_INTERPRETACOES) -> None:
        versoes = {v.conjunto: v.versao for v in sessao.scalars(select(VersaoDados))}
        self.versao_dados = "+".join(versoes[c] for c in ("cristalografia", "propriedades_v14") if c in versoes)
        self._textos: Dict[str, Dict[str, List[str]]] = json.loads(
            Path(caminho_interpretacoes).read_text(encoding="utf-8"))
        self._fontes = {f.id: {"citacao": f.citacao, "observacao": f.observacao} for f in sessao.scalars(select(Fonte))}

        materiais = {m.id: m for m in sessao.scalars(
            select(Material).where(Material.tipo.in_(("elemento_puro", "intersticial")),
                                   Material.estado != "arquivado"))}
        valores: Dict[str, Dict[str, ValorPropriedade]] = defaultdict(dict)
        for v in sessao.scalars(select(ValorPropriedade).where(ValorPropriedade.vigente.is_(True),
                                                               ValorPropriedade.material_id.in_(materiais))):
            valores[materiais[v.material_id].elemento_simbolo][v.propriedade_codigo] = v
        estruturas: Dict[str, List[MaterialEstrutura]] = defaultdict(list)
        for e in sessao.scalars(select(MaterialEstrutura).where(MaterialEstrutura.material_id.in_(materiais))):
            estruturas[materiais[e.material_id].elemento_simbolo].append(e)

        self._metais: Dict[str, Metal] = {}
        self._intersticiais: Dict[str, Mapping[str, Any]] = {}
        self._valores: Dict[Tuple[str, str], ValorReferencia] = {}
        self._transicoes: Dict[str, List[TransicaoAlotropica]] = defaultdict(list)
        for material in materiais.values():
            simbolo = material.elemento_simbolo
            vals = valores[simbolo]
            for codigo, v in vals.items():
                self._valores[(simbolo, codigo)] = ValorReferencia(simbolo=simbolo, codigo=codigo, valor=float(v.valor),
                                                                   unidade=v.unidade, estado=v.estado, fonte=v.fonte_id)
            for e in estruturas[simbolo]:
                if not e.referencia_ambiente:
                    self._transicoes[simbolo].append(TransicaoAlotropica(
                        simbolo=simbolo, de_c=float(e.temperatura_min_c), ate_c=float(e.temperatura_max_c),
                        fase=e.fase or "", estrutura=e.estrutura_codigo, estado=e.estado, fonte=e.fonte_id))
            if material.tipo == "intersticial":
                self._intersticiais[simbolo] = {"simbolo": simbolo, "nome": material.nome,
                                                "aliases": list(material.aliases or [])}
                continue
            ambiente = next(e for e in estruturas[simbolo] if e.referencia_ambiente)
            densidade = vals.get("densidade")
            self._metais[simbolo] = Metal(
                simbolo=simbolo, nome=material.nome, estrutura=ambiente.estrutura_codigo,
                raio_nm=float(vals["raio_atomico"].valor), peso_g_mol=float(vals["massa_atomica"].valor),
                densidade_exp_g_cm3=_f(densidade.valor) if densidade else None,
                c_a=_f(ambiente.c_a), a_nm=_f(ambiente.a_nm), c_nm=_f(ambiente.c_nm),
                aliases=tuple(sem_acentos(a) for a in material.aliases or []),
                fonte=ambiente.fonte_id, fonte_rede=ambiente.fonte_rede_id)
        for lista in self._transicoes.values():
            lista.sort(key=lambda t: t.de_c)
        self._por_minusculo = {s.lower(): s for s in self._metais}
        self._por_alias: Dict[str, str] = {}
        for simbolo, metal in self._metais.items():
            for alias in (*metal.aliases, metal.nome):
                self._por_alias[sem_acentos(alias)] = simbolo

    # --- RepositorioMateriais -----------------------------------------------------
    def listar(self) -> Sequence[Metal]:
        return tuple(self._metais[s] for s in sorted(self._metais))

    def obter(self, simbolo: str) -> Optional[Metal]:
        return self._metais.get(simbolo)

    def buscar(self, texto: str) -> Optional[Metal]:
        alvo = (texto or "").strip()
        if not alvo:
            return None
        if alvo in self._metais:
            return self._metais[alvo]
        simbolo = self._por_minusculo.get(alvo.lower()) or self._por_alias.get(sem_acentos(alvo))
        return self._metais.get(simbolo) if simbolo else None

    def fonte(self, chave: Optional[str]) -> Optional[Mapping[str, Any]]:
        return self._fontes.get(chave) if chave else None

    def interpretacoes(self, estrutura: str, locale: str = "pt-BR") -> List[str]:
        textos = self._textos.get(locale) or self._textos["pt-BR"]
        return list(textos.get(estrutura, []))

    # --- RepositorioPropriedades --------------------------------------------------
    def propriedade(self, simbolo: str, codigo: str) -> Optional[ValorReferencia]:
        return self._valores.get((simbolo, codigo))

    def intersticial(self, simbolo: str) -> Optional[Mapping[str, Any]]:
        return self._intersticiais.get(simbolo)

    def buscar_intersticial(self, texto: str) -> Optional[str]:
        alvo = sem_acentos(texto or "")
        for simbolo, dados in self._intersticiais.items():
            if alvo == simbolo.lower() or alvo in dados.get("aliases", []):
                return simbolo
        return None

    def transicoes(self, simbolo: str) -> Sequence[TransicaoAlotropica]:
        return tuple(self._transicoes.get(simbolo, ()))
