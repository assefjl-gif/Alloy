"""Grandezas de ligas de alta entropia (HEA) que têm base citável (RQ-HEA-01..04, PI-02).

Calculado:
* ΔS_mix ideal = −R·Σ xᵢ·ln xᵢ — exato para solução ideal; só depende da composição (analítico).
* δ = 100·√(Σ xᵢ·(1 − rᵢ/r̄)²), r̄ = Σ xᵢ·rᵢ — descompasso de raios (Zhang et al., 2008).
* T_m = Σ xᵢ·T_f,ᵢ — regra das misturas (aproximação usual na literatura de HEA).
* VEC = Σ xᵢ·VECᵢ e o critério de fases de Guo et al. (2011): VEC ≥ 8,0 → CFC; VEC < 6,87 → CCC.

NÃO calculado (devolvido como ``None`` com o motivo): ΔH_mix exige entalpias binárias de Miedema
com fonte, ainda inexistentes no banco (Q-01); Ω = T_m·ΔS_mix/|ΔH_mix| depende dele. Nenhum valor
é inventado para preencher a tela: dureza, ductilidade e curva de Gibbs também ficam indisponíveis.

Dados de elemento passam pela PoliticaDados: em produção, só valores validados são usados; a
grandeza que dependeria de um dado não validado fica indisponível (e o motivo é informado).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Tuple

from ..crystallography.erros import EntradaInvalida
from ..crystallography.formatacao import txt
from ..crystallography.referencia import RepositorioMateriais
from ..procedencia import ColetorDados, PoliticaDados, RepositorioPropriedades, ValorReferencia, bloco_procedencia

VERSAO_MOTOR = "1.0.0"
R_GASES = 8.314462618  # J/(mol·K), CODATA 2018 (valor exato pela redefinição do SI)
MAX_ELEMENTOS = 12
VEC_CFC = 8.0
VEC_CCC = 6.87
DELTA_SOLUCAO_SOLIDA = 6.6  # %
OMEGA_SOLUCAO_SOLIDA = 1.1
DS_ALTA_ENTROPIA = 1.5 * R_GASES  # ΔS_mix ≥ 1,5R: definição por entropia (Yeh 2006; Miracle & Senkov 2017)

FONTES_MODELO = (
    "ΔS_mix ideal: −R·Σ xᵢ ln xᵢ (entropia configuracional de Boltzmann para solução ideal)",
    "Zhang, Y. et al. Adv. Eng. Mater. 10, 534–538 (2008) — parâmetro δ",
    "Yang, X.; Zhang, Y. Mater. Chem. Phys. 132, 233–238 (2012) — critério δ ≤ 6,6 % e Ω ≥ 1,1",
    "Guo, S. et al. J. Appl. Phys. 109, 103505 (2011) — critério de fases por VEC",
)
MOTIVO_DH = ("ΔH_mix exige entalpias binárias de Miedema com fonte, ainda não cadastradas (questão Q-01). "
             "Nenhum valor é estimado.")


def _composicao(bruta: Any) -> List[Tuple[str, float]]:
    if not isinstance(bruta, Mapping) or not bruta:
        raise EntradaInvalida("Informe a composição como {elemento: quantidade}, ex.: {\"Co\": 1, \"Cr\": 1}.")
    itens: List[Tuple[str, float]] = []
    for simbolo, quantidade in bruta.items():
        try:
            q = float(quantidade)
        except (TypeError, ValueError):
            raise EntradaInvalida(f"Quantidade inválida para {simbolo}: {quantidade!r}.") from None
        if not math.isfinite(q) or q < 0:
            raise EntradaInvalida(f"A quantidade de {simbolo} deve ser um número ≥ 0.")
        if q > 0:
            itens.append((str(simbolo).strip(), q))
    if len(itens) < 2:
        raise EntradaInvalida("Uma liga precisa de pelo menos 2 elementos com quantidade > 0.")
    if len(itens) > MAX_ELEMENTOS:
        raise EntradaInvalida(f"No máximo {MAX_ELEMENTOS} elementos por liga.")
    if len({s for s, _ in itens}) != len(itens):
        raise EntradaInvalida("Elemento repetido na composição.")
    total = sum(q for _, q in itens)
    return sorted(((s, q / total) for s, q in itens), key=lambda par: par[0])


def entropia_mistura(fracoes: List[Tuple[str, float]]) -> float:
    return -R_GASES * sum(x * math.log(x) for _, x in fracoes)


def _raio(repo: RepositorioMateriais, simbolo: str, coletor: ColetorDados) -> Tuple[Optional[float], Optional[str]]:
    metal = repo.obter(simbolo)
    if metal is None:
        return None, f"Não há raio atômico cadastrado para {simbolo}."
    # O seed base aguarda validação (CR-10): sob a política de produção, δ fica indisponível.
    dado = ValorReferencia(simbolo=simbolo, codigo="raio_atomico", valor=metal.raio_nm, unidade="nm",
                           estado="aguardando_validacao", fonte=metal.fonte)
    if not coletor.politica.permitir_nao_validado:
        return None, f"Raio atômico de {simbolo} ainda não foi validado com fonte. δ indisponível neste ambiente."
    coletor.registrar(dado)
    return metal.raio_nm, None


def _media(fracoes: List[Tuple[str, float]], obter) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    valores: Dict[str, float] = {}
    for simbolo, _ in fracoes:
        valor, motivo = obter(simbolo)
        if valor is None:
            return None, motivo
        valores[simbolo] = valor
    return valores, None


def _fase_por_vec(vec: Optional[float]) -> Tuple[str, Optional[str]]:
    if vec is None:
        return "indeterminada (VEC indisponível)", None
    if vec >= VEC_CFC:
        return f"CFC (critério VEC ≥ {txt(VEC_CFC, 1)})", "CFC"
    if vec < VEC_CCC:
        return f"CCC (critério VEC < {txt(VEC_CCC, 2)})", "CCC"
    return f"CFC + CCC ({txt(VEC_CCC, 2)} ≤ VEC < {txt(VEC_CFC, 1)})", None


def analisar_liga(payload: Mapping[str, Any], repo: RepositorioMateriais, props: RepositorioPropriedades,
                  politica: PoliticaDados) -> Dict[str, Any]:
    nome = str(payload.get("nome") or "").strip() or "Liga sem nome"
    fracoes = _composicao(payload.get("composicao"))
    coletor = ColetorDados(politica)
    indisponiveis: Dict[str, str] = {"dH": MOTIVO_DH, "omega": "Ω depende de ΔH_mix (indisponível)."}

    ds = entropia_mistura(fracoes)

    raios, motivo = _media(fracoes, lambda s: _raio(repo, s, coletor))
    delta: Optional[float] = None
    if raios is None:
        indisponiveis["delta"] = motivo or "raio indisponível"
    else:
        r_medio = sum(x * raios[s] for s, x in fracoes)
        delta = 100.0 * math.sqrt(sum(x * (1.0 - raios[s] / r_medio) ** 2 for s, x in fracoes))

    fusao, motivo = _media(fracoes, lambda s: coletor.opcional(props, s, "temperatura_fusao", "temperatura de fusão"))
    tm: Optional[float] = None
    if fusao is None:
        indisponiveis["Tm"] = motivo or "temperatura de fusão indisponível"
    else:
        tm = sum(x * (fusao[s] + 273.15) for s, x in fracoes)

    vecs, motivo = _media(fracoes, lambda s: coletor.opcional(props, s, "vec", "VEC"))
    vec: Optional[float] = None
    if vecs is None:
        indisponiveis["VEC"] = motivo or "VEC indisponível"
    else:
        vec = sum(x * vecs[s] for s, x in fracoes)

    fase, estrutura = _fase_por_vec(vec)
    interpretacao = [
        f"ΔS_mix = {txt(ds, 2)} J/(mol·K) = {txt(ds / R_GASES, 3)}·R "
        + ("(≥ 1,5R: alta entropia pela definição por entropia)." if ds >= DS_ALTA_ENTROPIA - 1e-9
           else "(< 1,5R: não é alta entropia pela definição por entropia)."),
    ]
    if delta is not None:
        interpretacao.append(f"δ = {txt(delta, 2)} % "
                             + (f"≤ {txt(DELTA_SOLUCAO_SOLIDA, 1)} %: o descompasso de raios favorece solução sólida."
                                if delta <= DELTA_SOLUCAO_SOLIDA else
                                f"> {txt(DELTA_SOLUCAO_SOLIDA, 1)} %: descompasso alto; "
                                "intermetálicos/amorfo mais prováveis."))
    if vec is not None:
        interpretacao.append(f"VEC = {txt(vec, 2)} → fase prevista pelo critério de Guo: {fase}.")
    interpretacao.append("Ω e ΔH_mix indisponíveis: o critério completo de Yang & Zhang (Ω ≥ 1,1 e δ ≤ 6,6 %) "
                         "não pode ser avaliado.")
    veredito = ("INCONCLUSIVO — critérios parciais: "
                + ("δ favorável" if delta is not None and delta <= DELTA_SOLUCAO_SOLIDA else
                   "δ desfavorável" if delta is not None else "δ indisponível")
                + "; Ω indisponível sem ΔH_mix.")

    resultado: Dict[str, Any] = {
        "nome": nome,
        "veredito": veredito,
        "fase": fase,
        "estrutura_sugerida": estrutura,
        "ductilidade": None,
        "dureza": None,
        "dureza_indice": None,
        "dS": round(ds, 4),
        "dH": None,
        "delta": None if delta is None else round(delta, 4),
        "omega": None,
        "VEC": None if vec is None else round(vec, 4),
        "Tm": None if tm is None else round(tm, 1),
        "comp_percent": {s: round(100.0 * x, 4) for s, x in fracoes},
        "fracoes": {s: x for s, x in fracoes},
        "interpretacao": interpretacao,
        "fragilidade": None,
        "gibbs": [],
        "indisponiveis": indisponiveis,
    }
    if estrutura is None:
        del resultado["estrutura_sugerida"]
    avisos = []
    if len(fracoes) < 5:
        avisos.append("Menos de 5 elementos: pela definição por composição (Yeh, 2004), não é uma HEA; "
                      "as grandezas continuam válidas como descritores da mistura.")
    resultado["procedencia"] = bloco_procedencia(
        classe="estimativa_modelo", motor="hea", versao_motor=VERSAO_MOTOR,
        versao_dados=props.versao_dados,
        parametros={"nome": nome, "composicao": dict(payload.get("composicao") or {})},
        coletor=coletor, fontes_modelo=FONTES_MODELO, avisos=avisos)
    return resultado


#: Composições equimolares clássicas da literatura usadas como exemplos (só elementos cadastrados).
def _equimolar(nome: str, grupo: str, *elementos: str) -> Dict[str, Any]:
    return {"nome": nome, "grupo": grupo, "composicao": dict.fromkeys(elementos, 1.0)}


#: O primeiro é o carregado por padrão no front: CoCrFeNi tem fase única pelo critério (VEC 8,25 → CFC).
EXEMPLOS = {
    "CoCrFeNi": _equimolar("CoCrFeNi", "CFC (literatura)", "Co", "Cr", "Fe", "Ni"),
    "AlCoCrFeNi": _equimolar("AlCoCrFeNi", "CCC/B2 (literatura)", "Al", "Co", "Cr", "Fe", "Ni"),
    "CoCrCuFeNi": _equimolar("CoCrCuFeNi", "CFC (literatura)", "Co", "Cr", "Cu", "Fe", "Ni"),
    "Al0.5CoCrCuFeNi": {"nome": "Al0.5CoCrCuFeNi", "grupo": "CFC (Yeh 2004)",
                        "composicao": {"Al": 0.5, "Co": 1.0, "Cr": 1.0, "Cu": 1.0, "Fe": 1.0, "Ni": 1.0}},
}

#: Limiares dos critérios (não são dados de material): exibidos ao lado do resultado.
REFERENCIA = {"dS": round(DS_ALTA_ENTROPIA, 3), "omega": OMEGA_SOLUCAO_SOLIDA, "delta": DELTA_SOLUCAO_SOLIDA,
              "VEC": VEC_CFC, "dH": None, "T_padrao": "não se aplica (ΔS_mix ideal)", "P_padrao": "não se aplica"}


def catalogo(repo: RepositorioMateriais, props: RepositorioPropriedades) -> Dict[str, Any]:
    elementos = {}
    for metal in repo.listar():
        elementos[metal.simbolo] = {
            "simbolo": metal.simbolo, "nome": metal.nome, "raio_nm": metal.raio_nm,
            "tem_fusao": props.propriedade(metal.simbolo, "temperatura_fusao") is not None,
            "tem_vec": props.propriedade(metal.simbolo, "vec") is not None,
        }
    return {"elements": elementos, "alloys": EXEMPLOS, "reference": REFERENCIA, "samples": [],
            "versao_motor": VERSAO_MOTOR}
