"""Validação e normalização do pedido de solução sólida (contrato R1 §2.1 e §4.2; parecer §3.3).

Resolve o solvente e a lista de solutos (forma binária legada ``soluto``/``x`` ou ``solutos``), decide
modo (substitucional/intersticial) e sítio, converte a base de composição (atômica ↔ mássica) e aplica
as regras de domínio. Nenhuma correção silenciosa: cada recusa é um erro de domínio com subtipo estável
em ``details[].type`` (mesmo formato do 422 de esquema, como no motor HEA).

Ordem canônica (saída e sorteio): solvente; substitucionais em ordem crescente de símbolo; intersticiais
em ordem crescente de símbolo. O resultado não depende da ordem do pedido.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..procedencia import ColetorDados, RepositorioPropriedades
from .constantes import MAX_SOLUTOS
from .entradas import numero_opcional
from .erros import EntradaInvalida, MaterialDesconhecido
from .estruturas import ESTRUTURAS, normalizar_estrutura
from .referencia import Metal, RepositorioMateriais
from .sitios import sitio_padrao, tipos_de_sitio
from .supercelula import validar_tamanho

#: Texto do usuário ecoado em mensagem de erro é truncado (contrato R1 §4).
MAX_ECO = 16

X_MAXIMO_INTERSTICIAL = 20.0
MODOS = ("auto", "substitucional", "intersticial")
SITIOS_ACEITOS = ("auto", "octaedrico", "tetraedrico", "cubico")
BASES_COMPOSICAO = ("atomica", "massica")


def eco(texto: Any) -> str:
    bruto = str(texto)
    return bruto if len(bruto) <= MAX_ECO else bruto[:MAX_ECO] + "…"


class EntradaLigaInvalida(EntradaInvalida):
    """400 ``ENTRADA_INVALIDA`` com ``detalhes``; a mensagem do erro é a do primeiro item."""

    def __init__(self, detalhes: Sequence[Dict[str, Any]]) -> None:
        super().__init__(str(detalhes[0]["msg"]))
        self.detalhes: List[Dict[str, Any]] = list(detalhes)


class MaterialDesconhecidoLiga(MaterialDesconhecido):
    """400 ``MATERIAL_DESCONHECIDO`` (status e código de hoje) com ``detalhes``."""

    def __init__(self, detalhes: Sequence[Dict[str, Any]]) -> None:
        super().__init__(str(detalhes[0]["msg"]))
        self.detalhes: List[Dict[str, Any]] = list(detalhes)


def _detalhe(loc: Sequence[Any], subtipo: str, mensagem: str) -> Dict[str, Any]:
    return {"loc": [str(p) for p in loc], "type": subtipo, "msg": mensagem}


def _erro(loc: Sequence[Any], subtipo: str, mensagem: str) -> EntradaLigaInvalida:
    return EntradaLigaInvalida([_detalhe(loc, subtipo, mensagem)])


@dataclass
class SolutoPedido:
    """Um soluto já resolvido: símbolo canônico, fração atômica, modo e sítio efetivos."""

    simbolo: str
    x: float                      # fração ATÔMICA sobre todos os átomos (0 a 1)
    modo: str                     # "substitucional" | "intersticial"
    sitio: Optional[str]          # tipo de sítio (só intersticial)
    escolha_sitio: str            # "padrao" | "informado"
    metal: Optional[Metal]
    raio_nm: float
    massa_g_mol: float
    estado_do_dado: str
    fonte: Optional[str]
    estrutura_pura: Optional[str]
    indice_pedido: int

    @property
    def intersticial(self) -> bool:
        return self.modo == "intersticial"


@dataclass
class PedidoLiga:
    solvente: Metal
    solutos: List[SolutoPedido]   # em ordem canônica
    estrutura: str
    estrutura_do_solvente: bool
    base_composicao: str
    n: int
    arranjo: str
    distorcer: bool
    semente: int
    legado: bool                  # pedido na forma binária (``soluto``/``x``)
    x_pedido_pct: float           # x como veio no pedido (primeiro soluto)
    avisos: List[str]

    @property
    def substitucionais(self) -> List[SolutoPedido]:
        return [s for s in self.solutos if not s.intersticial]

    @property
    def intersticiais(self) -> List[SolutoPedido]:
        return [s for s in self.solutos if s.intersticial]

    @property
    def x_intersticial(self) -> float:
        return sum(s.x for s in self.intersticiais)


def _metal(repo: RepositorioMateriais, texto: str, loc: Sequence[Any], papel: str) -> Metal:
    metal = repo.obter(texto) or repo.buscar(texto)
    if metal is None:
        raise MaterialDesconhecidoLiga([_detalhe(
            loc, "material_desconhecido", f"{papel} '{eco(texto)}' não é um metal cadastrado.")])
    return metal


def _semente(bruta: Any) -> int:
    """``semente: 0`` é semente válida e respeitada (corrige L-11; V-11)."""
    if bruta is None or (isinstance(bruta, str) and not str(bruta).strip()):
        return 1
    if isinstance(bruta, bool):
        raise _erro(["semente"], "semente_invalida", "A semente deve ser um número inteiro.")
    try:
        return int(bruta)
    except (TypeError, ValueError):
        raise _erro(["semente"], "semente_invalida", "A semente deve ser um número inteiro.") from None


def _itens_do_pedido(payload: Mapping[str, Any]) -> Tuple[List[Mapping[str, Any]], bool]:
    """Lista de itens de soluto (forma legada ou ``solutos``) e se o pedido é legado."""
    bruta = payload.get("solutos")
    legado_txt = payload.get("soluto")
    tem_legado = legado_txt not in (None, "")
    if bruta is not None and tem_legado:
        raise EntradaLigaInvalida([_detalhe([], "soluto_ou_solutos",
                                            "Informe 'soluto' ou 'solutos', não os dois.")])
    if bruta is None and not tem_legado:
        raise EntradaLigaInvalida([_detalhe([], "soluto_ou_solutos",
                                            "Informe 'soluto' ou 'solutos', não os dois.")])
    if bruta is not None:
        if payload.get("x") is not None:
            raise EntradaLigaInvalida([_detalhe(
                ["x"], "x_com_solutos", "Com 'solutos', informe o x de cada item, não o x do pedido.")])
        if not isinstance(bruta, Sequence) or isinstance(bruta, (str, bytes)):
            raise _erro(["solutos"], "solutos_invalido", "'solutos' deve ser uma lista de solutos.")
        if not 1 <= len(bruta) <= MAX_SOLUTOS:
            subtipo = "too_short" if len(bruta) < 1 else "too_long"
            raise EntradaLigaInvalida([_detalhe(
                ["solutos"], subtipo, f"'solutos' deve ter de 1 a {MAX_SOLUTOS} itens.")])
        itens: List[Mapping[str, Any]] = []
        for i, item in enumerate(bruta):
            if not isinstance(item, Mapping):
                raise _erro(["solutos", i], "solutos_invalido",
                            "Cada item de 'solutos' deve ser um objeto com 'elemento' e 'x'.")
            itens.append(item)
        return itens, False
    return [{"elemento": legado_txt, "x": payload.get("x")}], True


def _modo_e_sitio(item: Mapping[str, Any], i: int, loc_base: Sequence[Any], estrutura: str,
                  simbolo_intersticial: Optional[str], tem_metal: bool,
                  texto: str) -> Tuple[str, Optional[str], str]:
    modo = str(item.get("modo") or "auto")
    if modo not in MODOS:
        raise EntradaLigaInvalida([_detalhe([*loc_base, "modo"], "literal_error",
                                            f"deve ser um de: {', '.join(repr(m) for m in MODOS)}")])
    if modo == "auto":
        modo = "intersticial" if simbolo_intersticial else "substitucional"
    if modo == "intersticial" and not simbolo_intersticial:
        raise _erro([*loc_base, "modo"], "modo_sem_dados", f"Sem dados para {eco(texto)} como intersticial.")
    if modo == "substitucional" and simbolo_intersticial and not tem_metal:
        raise _erro([*loc_base, "modo"], "modo_sem_dados",
                    f"Sem dados para {simbolo_intersticial} como substitucional.")

    bruto_sitio = item.get("sitio")
    sitio = str(bruto_sitio or "auto")
    if sitio not in SITIOS_ACEITOS:
        raise EntradaLigaInvalida([_detalhe([*loc_base, "sitio"], "literal_error",
                                            f"deve ser um de: {', '.join(repr(s) for s in SITIOS_ACEITOS)}")])
    informado = bruto_sitio not in (None, "", "auto")
    if modo == "substitucional":
        if informado:
            raise _erro([*loc_base, "sitio"], "sitio_incompativel",
                        "Sítio só se aplica a soluto intersticial.")
        return modo, None, "padrao"
    if informado:
        if sitio not in tipos_de_sitio(estrutura):
            raise _erro([*loc_base, "sitio"], "sitio_incompativel",
                        f"O sítio {sitio} não existe na estrutura {estrutura}.")
        return modo, sitio, "informado"
    return modo, sitio_padrao(estrutura), "padrao"


def _converter_massica(solutos: List[SolutoPedido], solvente: Metal) -> None:
    """Converte x em % em massa para fração atômica (parecer §3.2): x_i = (w_i/A_i)/Σ(w_k/A_k)."""
    soma_w = sum(s.x for s in solutos)
    if soma_w >= 1.0:
        raise EntradaLigaInvalida([_detalhe(
            ["solutos"], "soma_solutos_invalida",
            "A soma dos solutos deve ser menor que 100 %: o solvente ficaria sem átomos.")])
    moles = [(s, s.x / s.massa_g_mol) for s in solutos]
    total = (1.0 - soma_w) / solvente.peso_g_mol + sum(m for _s, m in moles)
    for soluto, mol in moles:
        soluto.x = mol / total


def interpretar(payload: Mapping[str, Any], repo: RepositorioMateriais, props: RepositorioPropriedades,
                coletor: ColetorDados) -> PedidoLiga:
    """Pedido validado e normalizado. Lança erro de domínio com ``detalhes`` em qualquer recusa."""
    avisos: List[str] = []
    solvente = _metal(repo, str(payload.get("base") or ""), ["base"], "Solvente")

    estrutura_pedida = payload.get("estrutura_matriz")
    estrutura = solvente.estrutura
    estrutura_do_solvente = True
    if estrutura_pedida not in (None, ""):
        nova = normalizar_estrutura(str(estrutura_pedida))
        if nova is None:
            raise EntradaLigaInvalida([_detalhe(
                ["estrutura_matriz"], "literal_error",
                f"deve ser um de: {', '.join(repr(s) for s in ESTRUTURAS)}")])
        if nova != estrutura:
            estrutura_do_solvente = False
            avisos.append(
                f"{solvente.simbolo} é {estrutura} no repositório; a estrutura {nova} foi imposta à matriz com o "
                f"mesmo raio tabelado. Como o raio metálico depende do número de coordenação (correção de "
                f"Goldschmidt), parâmetro de rede e densidade são hipotéticos.")
        estrutura = nova

    base_composicao = str(payload.get("base_composicao") or "atomica")
    if base_composicao not in BASES_COMPOSICAO:
        raise EntradaLigaInvalida([_detalhe(
            ["base_composicao"], "literal_error",
            f"deve ser um de: {', '.join(repr(b) for b in BASES_COMPOSICAO)}")])

    itens, legado = _itens_do_pedido(payload)
    solutos: List[SolutoPedido] = []
    vistos: Dict[str, int] = {}
    x_pedido_pct = 0.0

    for i, item in enumerate(itens):
        loc_base: List[Any] = ["soluto"] if legado else ["solutos", i]
        texto = str(item.get("elemento") or "").strip()
        if not texto:
            raise EntradaLigaInvalida([_detalhe([*loc_base, "elemento"] if not legado else loc_base,
                                                "missing", "campo obrigatório")])
        simbolo_intersticial = props.buscar_intersticial(texto)
        metal = repo.obter(texto) or repo.buscar(texto)
        if simbolo_intersticial is None and metal is None:
            loc = loc_base if legado else [*loc_base, "elemento"]
            raise MaterialDesconhecidoLiga([_detalhe(
                loc, "material_desconhecido", f"Soluto '{eco(texto)}' não é um metal cadastrado.")])
        modo, sitio, escolha = _modo_e_sitio(item, i, loc_base, estrutura, simbolo_intersticial,
                                             metal is not None, texto)
        simbolo = simbolo_intersticial if modo == "intersticial" else str(metal.simbolo)

        if simbolo == solvente.simbolo:
            loc = loc_base if legado else [*loc_base, "elemento"]
            raise _erro(loc, "soluto_igual_ao_solvente", f"{simbolo} já é o solvente.")
        if simbolo in vistos:
            loc = loc_base if legado else [*loc_base, "elemento"]
            raise _erro(loc, "soluto_repetido",
                        f"Soluto repetido: {simbolo}. Informe cada elemento uma única vez.")
        vistos[simbolo] = i

        # A faixa é 0 a 100 em qualquer modo; o limite operacional dos intersticiais (20 at%) é
        # conferido depois, para que o erro tenha o subtipo ``intersticial_acima_do_limite``.
        x_max = 100.0
        descricao = (f"composição ({'% em massa' if base_composicao == 'massica' else '% atômica'}, "
                     f"0 a {x_max:g})")
        bruto = {"x": item.get("x")}
        valor = numero_opcional(bruto, "x", (0.0, x_max), descricao)
        if valor is None:
            if not legado:
                raise EntradaLigaInvalida([_detalhe([*loc_base, "x"], "missing", "campo obrigatório")])
            valor = 10.0
        if i == 0:
            x_pedido_pct = valor

        if modo == "intersticial":
            raio = coletor.exigir(props, simbolo, "raio_atomico", "raio atômico")
            massa = coletor.exigir(props, simbolo, "massa_atomica", "massa atômica")
            dado = props.propriedade(simbolo, "raio_atomico")
            estado, fonte, estrutura_pura = (dado.estado if dado else "ausente"), (dado.fonte if dado else None), None
        else:
            raio, massa = float(metal.raio_nm), float(metal.peso_g_mol)
            citacao = repo.fonte(metal.fonte)
            estado = "aguardando_validacao"
            fonte = citacao.get("citacao") if citacao else None
            estrutura_pura = metal.estrutura

        solutos.append(SolutoPedido(simbolo=simbolo, x=valor / 100.0, modo=modo, sitio=sitio,
                                    escolha_sitio=escolha, metal=metal if modo != "intersticial" else None,
                                    raio_nm=raio, massa_g_mol=massa, estado_do_dado=estado, fonte=fonte,
                                    estrutura_pura=estrutura_pura, indice_pedido=i))

    if base_composicao == "massica":
        _converter_massica(solutos, solvente)

    # ordem canônica: substitucionais por símbolo, depois intersticiais por símbolo
    solutos.sort(key=lambda s: (s.intersticial, s.simbolo))

    soma = sum(s.x for s in solutos)
    x_intersticial = sum(s.x for s in solutos if s.intersticial)
    legado_100 = legado and len(solutos) == 1 and abs(soma - 1.0) < 1e-12 and not solutos[0].intersticial
    if legado_100:
        avisos.append("x = 100 % deixa a liga sem solvente: o desenho é só do soluto. Caso aceito por "
                      "compatibilidade com a versão anterior.")
    elif soma >= 1.0:
        raise EntradaLigaInvalida([_detalhe(
            ["solutos"] if not legado else ["x"], "soma_solutos_invalida",
            "A soma dos solutos deve ser menor que 100 %: o solvente ficaria sem átomos.")])
    if x_intersticial > X_MAXIMO_INTERSTICIAL / 100.0 + 1e-12:
        raise EntradaLigaInvalida([_detalhe(
            ["solutos"] if not legado else ["x"], "intersticial_acima_do_limite",
            f"Intersticiais limitados a {X_MAXIMO_INTERSTICIAL:g} % atômica neste modelo "
            f"(limite operacional, não físico).")])
    if soma > 0.5 and not legado_100:
        avisos.append(f"O solvente {solvente.simbolo} não é o componente majoritário em átomos "
                      f"({(1.0 - soma) * 100:.2f} at%), mas a estrutura da matriz continua sendo a dele.")

    arranjo = "ordenado" if str(payload.get("arranjo") or "") == "ordenado" else "aleatorio"
    return PedidoLiga(solvente=solvente, solutos=solutos, estrutura=estrutura,
                      estrutura_do_solvente=estrutura_do_solvente, base_composicao=base_composicao,
                      n=validar_tamanho(payload.get("n") or 3), arranjo=arranjo,
                      distorcer=bool(payload.get("distorcer")), semente=_semente(payload.get("semente")),
                      legado=legado, x_pedido_pct=x_pedido_pct, avisos=avisos)


#: Nome do tipo de sítio no plural, para mensagens de erro.
NOME_PLURAL_SITIO = {"octaedrico": "octaédricos", "tetraedrico": "tetraédricos", "cubico": "cúbicos"}


def erro_capacidade(simbolo: str, quantidade: int, sitios: int, tipo: str,
                    indice: int, legado: bool) -> EntradaLigaInvalida:
    loc = ["x"] if legado else ["solutos", indice, "x"]
    nome = NOME_PLURAL_SITIO.get(tipo, tipo)
    return EntradaLigaInvalida([_detalhe(
        loc, "capacidade_sitios_excedida",
        f"{quantidade} átomos de {simbolo} não cabem nos {sitios} sítios {nome} desta supercélula. "
        f"Reduza x ou escolha outro sítio.")])
