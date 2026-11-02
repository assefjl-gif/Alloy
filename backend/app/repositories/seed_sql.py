"""Carga dos seeds JSON no banco (BANCO_DE_DADOS §6). Idempotente por versão de conjunto.

Estados de partida (ADR-014, Q-03):
* seed do B (metais.json): ``aguardando_validacao`` — citação do Callister sem edição/página (CR-10)
  e rede do α-Ti de relatório interno ("conferir na fonte primária");
* seed da v1.4 (propriedades_v14.json): ``rascunho`` — sem fonte nenhuma (CIE-03).
Nada entra como ``validado``: isso exige revisão humana registrada em ``revisoes_validacao``.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.crystallography import ESTRUTURAS, VERSAO_MOTOR
from app.engines.thermodynamics.termico import VERSAO_MOTOR as VERSAO_TERMICO
from app.models import (
    Elemento,
    Estrutura,
    Fonte,
    Material,
    MaterialEstrutura,
    Motor,
    Propriedade,
    ValorPropriedade,
    VersaoDados,
)

from .materiais_json import PASTA_SEEDS

TIPO_FONTE = {"callister": "livro", "auditoria_cr01": "relatorio"}

#: código → (nome, grupo, unidade SI, unidade de exibição)
CATALOGO_PROPRIEDADES = {
    "raio_atomico": ("Raio atômico metálico", "cristalografica", "m", "nm"),
    "massa_atomica": ("Massa atômica", "quimica", "kg/mol", "g/mol"),
    "densidade": ("Densidade", "fisica", "kg/m³", "g/cm³"),
    "eletronegatividade": ("Eletronegatividade (Pauling)", "quimica", "adimensional", "Pauling"),
    "valencia": ("Valência usual", "quimica", "adimensional", "adimensional"),
    "temperatura_fusao": ("Temperatura de fusão", "termica", "K", "°C"),
    "coef_dilatacao_linear": ("Coeficiente de dilatação linear", "termica", "1/K", "1e-6/K"),
}


class SeedJaCarregadoComOutraVersao(RuntimeError):
    """Seed com versão diferente da que está no banco: atualizar exige migração de dados revisada."""


def _d(valor: Any) -> Optional[Decimal]:
    return None if valor is None else Decimal(str(valor))


def _versao_carregada(sessao: Session, conjunto: str) -> Optional[str]:
    registro = sessao.get(VersaoDados, conjunto)
    return registro.versao if registro else None


def _nome_elemento(nome_material: str) -> str:
    return re.sub(r"\s*\(.*?\)\s*$", "", nome_material).strip()


def _material_do_elemento(sessao: Session, simbolo: str) -> Material:
    return sessao.scalars(select(Material).where(Material.elemento_simbolo == simbolo,
                                                 Material.tipo.in_(("elemento_puro", "intersticial")))).one()


def _valor(material: Material, codigo: str, valor: Any, unidade: str, classe: str, estado: str,
           fonte: Optional[str], origem: str, condicoes: Optional[dict] = None) -> ValorPropriedade:
    return ValorPropriedade(material_id=material.id, propriedade_codigo=codigo, valor=_d(valor), unidade=unidade,
                            classe=classe, estado=estado, fonte_id=fonte, origem=origem, condicoes=condicoes,
                            vigente=True)


def carregar_seeds(sessao: Session, pasta: Path = PASTA_SEEDS) -> Dict[str, int]:
    """Carrega os seeds que ainda não estão no banco. Devolve contagens do que foi inserido."""
    contagem = {"fontes": 0, "elementos": 0, "materiais": 0, "valores": 0, "estruturas_material": 0}
    agora = datetime.now(timezone.utc)

    base = json.loads((pasta / "metais.json").read_text(encoding="utf-8"))
    v14 = json.loads((pasta / "propriedades_v14.json").read_text(encoding="utf-8"))

    for codigo, versao in (("crystallography", VERSAO_MOTOR), ("thermodynamics", VERSAO_TERMICO)):
        if sessao.get(Motor, (codigo, versao)) is None:
            sessao.add(Motor(codigo=codigo, versao=versao))
    for sigla, info in ESTRUTURAS.items():
        if sessao.get(Estrutura, sigla) is None:
            ge = info["grupo_espacial"]
            sessao.add(Estrutura(codigo=sigla, nome=info["nome"], grupo_espacial_hm=ge["hm"],
                                 grupo_espacial_numero=ge["numero"], wyckoff=ge["wyckoff"], n=info["n"], nc=info["nc"]))
    for codigo, (nome, grupo, si, exibicao) in CATALOGO_PROPRIEDADES.items():
        if sessao.get(Propriedade, codigo) is None:
            sessao.add(Propriedade(codigo=codigo, nome=nome, grupo=grupo, unidade_si=si, unidade_exibicao=exibicao))
    sessao.flush()

    versao_base = str(base["versao_dados"])
    carregada = _versao_carregada(sessao, "cristalografia")
    if carregada not in (None, versao_base):
        raise SeedJaCarregadoComOutraVersao(f"cristalografia: banco {carregada}, seed {versao_base}.")
    if carregada is None:
        for chave, fonte in base["fontes"].items():
            sessao.add(Fonte(id=chave, tipo=TIPO_FONTE.get(chave, "outro"), citacao=fonte["citacao"],
                             observacao=fonte.get("observacao")))
            contagem["fontes"] += 1
        sessao.flush()
        for m in base["metais"]:
            sessao.add(Elemento(simbolo=m["simbolo"], nome=_nome_elemento(m["nome"])))
            contagem["elementos"] += 1
        sessao.flush()
        origem = f"metais.json {versao_base} (CrystaLab v1.1.0)"
        for m in base["metais"]:
            material = Material(tipo="elemento_puro", nome=m["nome"], elemento_simbolo=m["simbolo"],
                                aliases=list(m.get("aliases") or []), estado="aguardando_validacao",
                                visibilidade="publico", origem="curado")
            sessao.add(material)
            sessao.flush()
            contagem["materiais"] += 1
            fonte = m.get("fonte")
            novos = [
                _valor(material, "raio_atomico", m["raio_nm"], "nm", "importado", "aguardando_validacao",
                       fonte, origem),
                _valor(material, "massa_atomica", m["peso_g_mol"], "g/mol", "importado", "aguardando_validacao",
                       fonte, origem),
            ]
            if m.get("densidade_exp_g_cm3") is not None:
                novos.append(_valor(material, "densidade", m["densidade_exp_g_cm3"], "g/cm³", "medido",
                                    "aguardando_validacao", fonte, origem, {"temperatura": "ambiente"}))
            sessao.add_all(novos)
            contagem["valores"] += len(novos)
            sessao.add(MaterialEstrutura(material_id=material.id, estrutura_codigo=m["estrutura"],
                                         referencia_ambiente=True, c_a=_d(m.get("c_a")), a_nm=_d(m.get("a_nm")),
                                         c_nm=_d(m.get("c_nm")), fonte_id=fonte, fonte_rede_id=m.get("fonte_rede"),
                                         estado="aguardando_validacao"))
            contagem["estruturas_material"] += 1
        sessao.add(VersaoDados(conjunto="cristalografia", versao=versao_base, carregado_em=agora))
        sessao.flush()

    versao_v14 = str(v14["versao_dados"])
    carregada = _versao_carregada(sessao, "propriedades_v14")
    if carregada not in (None, versao_v14):
        raise SeedJaCarregadoComOutraVersao(f"propriedades_v14: banco {carregada}, seed {versao_v14}.")
    if carregada is None:
        for registro in v14["intersticiais"]:
            sessao.add(Elemento(simbolo=registro["simbolo"], nome=registro["nome"]))
            sessao.flush()
            sessao.add(Material(tipo="intersticial", nome=registro["nome"], elemento_simbolo=registro["simbolo"],
                                aliases=list(registro.get("aliases") or []), estado="rascunho",
                                visibilidade="publico", origem="curado"))
            contagem["elementos"] += 1
            contagem["materiais"] += 1
        sessao.flush()
        for registro in v14["valores"]:
            material = _material_do_elemento(sessao, registro["simbolo"])
            sessao.add(_valor(material, registro["codigo"], registro["valor"], registro["unidade"], "importado",
                              registro["estado"], registro.get("fonte"), registro["origem"]))
            contagem["valores"] += 1
        for registro in v14["transicoes_alotropicas"]:
            material = _material_do_elemento(sessao, registro["simbolo"])
            sessao.add(MaterialEstrutura(material_id=material.id, estrutura_codigo=registro["estrutura"],
                                         fase=registro["fase"], temperatura_min_c=_d(registro["de_c"]),
                                         temperatura_max_c=_d(registro["ate_c"]), referencia_ambiente=False,
                                         fonte_id=registro.get("fonte"), estado=registro["estado"]))
            contagem["estruturas_material"] += 1
        sessao.add(VersaoDados(conjunto="propriedades_v14", versao=versao_v14, carregado_em=agora))
        sessao.flush()
    return contagem
