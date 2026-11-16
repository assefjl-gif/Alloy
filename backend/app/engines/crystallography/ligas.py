"""Soluções sólidas substitucionais e intersticiais, multicomponentes (R1; portado da v1.4 — RQ-CIE-11).

Modelos e fontes:
* Parâmetro de rede por interpolação linear de raios tabelados na estrutura do solvente (extensão da
  regra de Vegard, Z. Phys. 5, 17–26, 1921, a vários solutos) — empírica, por isso a classe do
  resultado é ``estimativa_modelo``. Intersticiais não dilatam a rede neste modelo.
* % atômica ↔ % em massa: Callister & Rethwisch, eq. 4.6–4.7.
* Regras de Hume-Rothery (Callister, seção 4.3), com o critério de ±0,4 de eletronegatividade
  de Darken & Gurry (Physical Chemistry of Metals, 1953) e a regra de Hägg (r/R < 0,59). São critérios
  empíricos de favorabilidade, NÃO previsão de limite de solubilidade.
* Raio livre dos sítios: geometria das esferas rígidas (``sitios.py``).
* Superestruturas por PROTÓTIPO geométrico (L1₂, L1₀, B2): o motor não sabe se o par real
  ordena assim — sempre avisa que o arranjo é hipotético.
* Distorção local: ilustrativa (``simulacao_ilustrativa``), não é relaxação elástica.

Correções da rodada R1 (parecer R1-CRI-01 §3; decisões G1 D-2):
* a unidade de amostragem é a SUPERCÉLULA PERIÓDICA: o sorteio e todas as contagens usam os Z·n³
  átomos ÚNICOS; as imagens de fronteira são só desenho, herdam o elemento da origem e nunca são
  contadas (L-1, L-5; V-8, V-9);
* quantidade de intersticiais calculada sobre N_rede, sem mínimo forçado de 1 (V-10);
* ``semente: 0`` é respeitada (V-11);
* vários solutos, substitucionais e/ou intersticiais (L-2), com composição solicitada × representada;
* o motor NÃO verifica limite de solubilidade nem prevê fases secundárias: isso é dito em toda
  resposta, em ``verificacoes`` e em ``procedencia.avisos`` (L-4).
"""

from __future__ import annotations

import math
import random
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ..procedencia import ColetorDados, PoliticaDados, RepositorioPropriedades, bloco_procedencia
from .constantes import EPS, N_AVOGADRO, NM_PARA_CM, SQRT2, SQRT3, TOLERANCIA_EDICAO
from .estruturas import ESTRUTURAS, c_a_ideal
from .formatacao import sci, sinal, txt
from .geometria import frac_para_cart, norma, volume_em_r
from .ligas_entrada import X_MAXIMO_INTERSTICIAL, PedidoLiga, SolutoPedido, erro_capacidade, interpretar
from .referencia import Metal, RepositorioMateriais
from .sitios import SITIOS_INTERSTICIAIS, nc_texto, posicoes, sitios_por_celula
from .sitios import descrever as descrever_sitio
from .supercelula import arestas_da_caixa, sitios_unicos, translacoes_de_imagem
from .versao import VERSAO_MOTOR

#: Compatibilidade: o sítio que o motor usava por padrão em cada rede (hoje em ``sitios.py``).
SITIOS: Dict[str, Dict[str, Any]] = {
    "CS": {"nome": "cúbico", "fator": SQRT3 - 1.0, "nc": 8, "frac": [(0.5, 0.5, 0.5)]},
    "CCC": {"nome": "octaédrico", "fator": 2.0 / SQRT3 - 1.0, "nc": 6, "frac": posicoes("CCC", "octaedrico")},
    "CFC": {"nome": "octaédrico", "fator": SQRT2 - 1.0, "nc": 6, "frac": posicoes("CFC", "octaedrico")},
    "HC": {"nome": "octaédrico", "fator": SQRT2 - 1.0, "nc": 6, "frac": posicoes("HC", "octaedrico")},
}

LIMITE_TAMANHO_PCT = 15.0          # Hume-Rothery
LIMITE_ELETRONEGATIVIDADE = 0.4    # Darken & Gurry (1953)
LIMITE_HAGG = 0.59                 # Hägg
ALGORITMO_SORTEIO = "mt19937-chaves-v1"
FONTES_MODELO = (
    "Vegard, L. Z. Phys. 5, 17–26 (1921) — lei de Vegard",
    "Callister & Rethwisch, Ciência e Engenharia de Materiais, seção 4.3 e eq. 4.6–4.7",
    "Darken, L. S.; Gurry, R. W. Physical Chemistry of Metals (1953) — critério de eletronegatividade",
)

AVISO_ORDENADO = ("Arranjo ordenado hipotético: o motor monta o protótipo geométrico, mas não sabe se este "
                  "par de elementos realmente ordena assim. Confira o diagrama de fases do sistema.")
AVISO_FASE_UNICA = ("Modelo de fase única: todos os solutos foram colocados na matriz. O motor não verifica o "
                    "limite de solubilidade nem prevê fases secundárias. A liga real, nesta composição e "
                    "temperatura, pode ter mais de uma fase.")
AVISO_REALIZACAO = ("Uma realização estatística entre muitas possíveis para esta composição e esta semente. "
                    "Não é a posição real dos átomos na liga; outra semente dá outro arranjo igualmente válido.")
MOTIVO_FRACAO_FASE = "o motor não calcula equilíbrio de fases"
MOTIVO_LIMITE = "não há dados de diagrama de fases no repositório"
MOTIVO_FASES_SECUNDARIAS = ("o motor não prevê fases; a liga real pode ser multifásica nesta composição")
MOTIVO_CONCLUSAO_GLOBAL = ("as regras são binárias; o motor não prevê solubilidade em sistema multicomponente")

#: Rótulo do sítio de rede, por tipo da base cristalográfica.
NOME_SITIO_REDE = {
    "vertice": "vértice", "centro": "centro do cubo", "face": "centro de face",
    "basal": "camada basal (z inteiro)", "interior": "camada intermediária (z semi-inteiro)",
}
#: Abreviação do tipo de sítio no ``id`` do átomo intersticial (contrato R1 §2.3).
ABREV_SITIO = {"octaedrico": "oct", "tetraedrico": "tet", "cubico": "cub"}
#: Ordem de sorteio dos tipos de sítio intersticial (parecer §3.2, passo 4).
ORDEM_TIPOS = ("cubico", "octaedrico", "tetraedrico")

CONVENCOES = [
    "Posições `pos` em unidades do parâmetro de rede `a` da liga; `pos_nm` em nm (herda a natureza de `a_nm`).",
    "`frac` é fracionária na célula replicada (0 a n): cúbicas replicam a célula convencional; "
    "HC replica a célula PRIMITIVA hexagonal (2 átomos).",
    "No HC a origem do motor está deslocada de (1/3, 2/3, 1/4) em relação à posição de Wyckoff 2c do CIF.",
    "Átomos com `imagem: true` são cópias periódicas de fronteira, só para o desenho: não entram em "
    "nenhuma contagem, composição ou massa.",
    "`raio_rel` é raio de DESENHO (raio tabelado do elemento puro / a), não raio do átomo em solução.",
]


# --------------------------------------------------------------------------- regras e textos
def _inteiro(v: float) -> bool:
    return abs(v - round(v)) < EPS


def _regra_ordenada(estrutura: str, x: float) -> Optional[Tuple[Callable[[Sequence[float]], bool], str]]:
    if estrutura == "CFC" and abs(x - 0.25) <= 0.02:
        return (lambda f: all(_inteiro(v) for v in f)), "L1₂ (protótipo Cu₃Au): soluto nos vértices"
    if estrutura == "CFC" and abs(x - 0.75) <= 0.02:
        return (lambda f: not all(_inteiro(v) for v in f)), "L1₂ invertida: soluto nos centros de face"
    if estrutura == "CFC" and abs(x - 0.5) <= 0.02:
        return (lambda f: _inteiro(f[2])), "L1₀ (protótipo CuAu): camadas alternadas ao longo de z"
    if estrutura == "CCC" and abs(x - 0.5) <= 0.02:
        return (lambda f: not _inteiro(f[0])), "B2 (protótipo CuZn β′): soluto nos centros dos cubos"
    return None


def _prototipo(fase: str, solvente: str, soluto: str) -> Dict[str, Any]:
    """Bloco ``prototipo`` (contrato R1 §2.2). Grupos espaciais NÃO conferidos na fonte (parecer §3.6)."""
    if fase.startswith("L1₂ (protótipo"):
        return {"strukturbericht": "L1₂", "prototipo": "Cu₃Au",
                "composicao_ideal_at_pct": {solvente: 75.0, soluto: 25.0},
                "rede_ordenada": "cúbica primitiva na descrição ordenada (grupo espacial não conferido na fonte)",
                "observacao": "O desenho mantém a rede-mãe CFC; a fase ordenada tem outra rede."}
    if fase.startswith("L1₂ invertida"):
        return {"strukturbericht": "L1₂", "prototipo": "Cu₃Au com as ocupações invertidas",
                "composicao_ideal_at_pct": {solvente: 25.0, soluto: 75.0},
                "rede_ordenada": "cúbica primitiva na descrição ordenada (grupo espacial não conferido na fonte)",
                "observacao": "O desenho mantém a rede-mãe CFC; a fase ordenada tem outra rede."}
    if fase.startswith("L1₀"):
        return {"strukturbericht": "L1₀", "prototipo": "CuAu",
                "composicao_ideal_at_pct": {solvente: 50.0, soluto: 50.0},
                "rede_ordenada": "tetragonal na fase real (parâmetros não conferidos na fonte)",
                "observacao": "O motor desenha a célula com c/a = 1 (cúbica): a tetragonalidade não é "
                              "representada."}
    return {"strukturbericht": "B2", "prototipo": "CsCl (CuZn β′)",
            "composicao_ideal_at_pct": {solvente: 50.0, soluto: 50.0},
            "rede_ordenada": "cúbica primitiva na descrição ordenada (grupo espacial não conferido na fonte)",
            "observacao": "O desenho mantém a rede-mãe CCC; a fase ordenada tem outra rede."}


def _metal_do_soluto(soluto: SolutoPedido) -> Metal:
    assert soluto.metal is not None
    return soluto.metal


def _regra(criterio: str, valor: Optional[str], ok: Optional[bool], detalhe: str,
           indisponivel: Optional[str] = None) -> Dict[str, Any]:
    return {"criterio": criterio, "valor": valor, "ok": ok, "detalhe": detalhe, "indisponivel": indisponivel}


def _regras_substitucionais(b: Metal, s: Metal, props: RepositorioPropriedades,
                            coletor: ColetorDados) -> List[Dict[str, Any]]:
    dr = abs(s.raio_nm - b.raio_nm) / b.raio_nm * 100.0
    regras = [
        _regra("Tamanho atômico", f"ΔR = {txt(dr, 1)} %", dr <= LIMITE_TAMANHO_PCT,
               "Raios até ±15 % diferentes permitem substituição extensa."),
        _regra("Estrutura cristalina", f"{b.estrutura} e {s.estrutura}", b.estrutura == s.estrutura,
               "Solubilidade total exige a mesma estrutura nos dois metais puros."),
    ]
    chi_b, motivo_b = coletor.opcional(props, b.simbolo, "eletronegatividade", "eletronegatividade")
    chi_s, motivo_s = coletor.opcional(props, s.simbolo, "eletronegatividade", "eletronegatividade")
    if chi_b is None or chi_s is None:
        regras.append(_regra("Eletronegatividade", None, None, "Critério de Darken & Gurry (±0,4).",
                             motivo_b or motivo_s))
    else:
        dchi = abs(chi_s - chi_b)
        regras.append(_regra("Eletronegatividade", f"Δχ = {txt(dchi, 2)}", dchi <= LIMITE_ELETRONEGATIVIDADE,
                             "Diferença grande favorece compostos intermetálicos (Darken & Gurry: ±0,4)."))
    val_b, motivo_b = coletor.opcional(props, b.simbolo, "valencia", "valência")
    val_s, motivo_s = coletor.opcional(props, s.simbolo, "valencia", "valência")
    if val_b is None or val_s is None:
        regras.append(_regra("Valência", None, None, "Mesma valência favorece a solubilidade.",
                             motivo_b or motivo_s))
    else:
        regras.append(_regra("Valência", f"+{val_b:g} e +{val_s:g}", val_b == val_s,
                             "Mesma valência favorece; um metal dissolve melhor outro de valência maior."))
    return regras


def _conclusao(regras: Sequence[Mapping[str, Any]]) -> str:
    """Redação de CRITÉRIO, não de previsão (V-12; parecer §3.3)."""
    avaliadas = [r for r in regras if r["ok"] is not None]
    atendidas = sum(1 for r in avaliadas if r["ok"])
    sem_previsao = "O limite de solubilidade depende do diagrama de fases e não é previsto por este motor."
    if len(avaliadas) < len(regras):
        return (f"{atendidas} de {len(avaliadas)} regras avaliáveis atendidas; "
                f"{len(regras) - len(avaliadas)} indisponível(is) por falta de dado validado. {sem_previsao}")
    if atendidas == len(regras):
        return ("As quatro regras de Hume-Rothery são atendidas: par favorável à solução substitucional "
                f"(como no Cu–Ni). {sem_previsao}")
    if regras[0]["ok"]:
        return (f"{atendidas} de {len(regras)} regras atendidas: critérios parcialmente favoráveis à solução "
                f"substitucional. {sem_previsao}")
    return ("Diferença de tamanho acima de 15 %: critério de tamanho desfavorável à solução substitucional "
            f"extensa. {sem_previsao}")


def _regras_intersticiais(soluto: SolutoPedido, sitio: Mapping[str, Any], raio_solvente: float,
                          ) -> Tuple[List[Dict[str, Any]], str]:
    razao = soluto.raio_nm / raio_solvente
    cabe = soluto.raio_nm <= sitio["raio_nm"]
    regras = [
        _regra("Razão de raios", f"r/R = {txt(razao, 3)}", razao <= LIMITE_HAGG,
               "Regra de Hägg: soluções intersticiais exigem r/R abaixo de ~0,59. É critério empírico, "
               "não previsão de solubilidade."),
        _regra(f"Sítio {sitio['nome']}", f"r livre = {txt(sitio['raio_nm'], 4)} nm", cabe,
               f"Raio livre = {txt(sitio['fator'], 4)}·R, pela geometria do sítio (NC {sitio['nc_txt']}). "
               f"Soluto maior empurra os vizinhos."),
    ]
    conclusao = ("Critérios geométricos favoráveis à solução intersticial; não é previsão de solubilidade: "
                 "o limite depende do diagrama de fases." if cabe else
                 "O soluto é maior que o raio livre do sítio: a rede se distorce e o critério geométrico é "
                 "desfavorável. Não é previsão de solubilidade.")
    return regras, conclusao


# --------------------------------------------------------------------------- quantidades
def _arredondar_meio(valor: float) -> int:
    """⌊v + ½⌋ explícito: ``round`` do Python arredonda ao par (round(0.5) = 0)."""
    return int(math.floor(valor + 0.5))


def _maior_resto(alvos: Sequence[float], total: int) -> List[int]:
    """Distribui ``total`` unidades pelos alvos, método do maior resto; empate pela ordem canônica."""
    pisos = [int(math.floor(t)) for t in alvos]
    sobra = total - sum(pisos)
    if sobra > 0:
        ordem = sorted(range(len(alvos)), key=lambda i: (-(alvos[i] - pisos[i]), i))
        for i in ordem[:sobra]:
            pisos[i] += 1
    elif sobra < 0:  # pragma: no cover — só por segurança numérica
        ordem = sorted(range(len(alvos)), key=lambda i: (alvos[i] - pisos[i], i))
        for i in ordem[:-sobra]:
            if pisos[i] > 0:
                pisos[i] -= 1
    return pisos


def _quantidades(pedido: PedidoLiga, n_rede: int) -> Tuple[Dict[str, int], int]:
    """Número de átomos ÚNICOS de cada soluto e do solvente (parecer §3.2)."""
    x_i = pedido.x_intersticial
    denominador = 1.0 - x_i
    substitucionais = pedido.substitucionais
    alvos = [s.x / denominador * n_rede for s in substitucionais]
    total = _arredondar_meio(sum(alvos))
    total = min(total, n_rede)
    quantidades = dict(zip([s.simbolo for s in substitucionais], _maior_resto(alvos, total), strict=True))
    for soluto in pedido.intersticiais:
        quantidades[soluto.simbolo] = _arredondar_meio(soluto.x / denominador * n_rede)
    return quantidades, n_rede - total


def _validar_capacidade(pedido: PedidoLiga, quantidades: Mapping[str, int], n: int) -> None:
    por_tipo: Dict[str, int] = {}
    for soluto in pedido.intersticiais:
        por_tipo[str(soluto.sitio)] = por_tipo.get(str(soluto.sitio), 0) + quantidades[soluto.simbolo]
    for soluto in pedido.intersticiais:
        tipo = str(soluto.sitio)
        capacidade = sitios_por_celula(pedido.estrutura, tipo) * n ** 3
        if por_tipo[tipo] > capacidade:
            raise erro_capacidade(soluto.simbolo, por_tipo[tipo], capacidade, tipo,
                                  soluto.indice_pedido, pedido.legado)


# --------------------------------------------------------------------------- composição
def _componentes(pedido: PedidoLiga) -> List[Tuple[str, str, float, float]]:
    """(símbolo, papel, fração atômica solicitada, massa molar), em ordem canônica."""
    itens = [(pedido.solvente.simbolo, "solvente", 1.0 - sum(s.x for s in pedido.solutos),
              float(pedido.solvente.peso_g_mol))]
    for soluto in pedido.solutos:
        itens.append((soluto.simbolo, soluto.modo, soluto.x, soluto.massa_g_mol))
    return itens


def _composicao(pedido: PedidoLiga, quantidades: Mapping[str, int], n_solvente: int,
                n_rede: int, n_desenhados: int) -> Dict[str, Any]:
    componentes = _componentes(pedido)
    massa_total = sum(x * a for _s, _p, x, a in componentes)
    solicitada = [{"elemento": s, "papel": p, "at_pct": x * 100.0,
                   "massa_pct": (x * a / massa_total * 100.0) if massa_total > 0 else 0.0}
                  for s, p, x, a in componentes]

    contagem = {pedido.solvente.simbolo: n_solvente, **{k: v for k, v in quantidades.items()}}
    n_intersticiais = sum(quantidades[s.simbolo] for s in pedido.intersticiais)
    n_unicos = n_rede + n_intersticiais
    massa_rep = sum(contagem[s] * a for s, _p, _x, a in componentes)
    representada = [{"elemento": s, "papel": p, "n_atomos": contagem[s],
                     "at_pct": contagem[s] / n_unicos * 100.0 if n_unicos else 0.0,
                     "massa_pct": (contagem[s] * a / massa_rep * 100.0) if massa_rep > 0 else 0.0}
                    for s, p, _x, a in componentes]
    desvio = max(abs(r["at_pct"] - s["at_pct"]) for r, s in zip(representada, solicitada, strict=True))
    return {
        "base_entrada": pedido.base_composicao,
        "solicitada": solicitada,
        "representada": representada,
        "n_sitios_rede": n_rede,
        "n_intersticiais": n_intersticiais,
        "n_atomos_unicos": n_unicos,
        "n_desenhados": n_desenhados,
        "resolucao_at_pct": 100.0 / n_unicos if n_unicos else 0.0,
        "desvio_maximo_at_pct": desvio,
    }


# --------------------------------------------------------------------------- átomos
def _id_rede(celula: Sequence[int], base: int) -> str:
    return f"r:{celula[0]}.{celula[1]}.{celula[2]}:{base}"


def _id_intersticial(tipo: str, celula: Sequence[int], indice: int) -> str:
    return f"i:{ABREV_SITIO[tipo]}:{celula[0]}.{celula[1]}.{celula[2]}:{indice}"


def _sorteio_chaves(rng: random.Random, quantidade: int) -> List[int]:
    """Índices ordenados por (chave aleatória, índice canônico) — algoritmo ``mt19937-chaves-v1``."""
    chaves = [(rng.random(), i) for i in range(quantidade)]
    return [i for _u, i in sorted(chaves)]


def _distribuir(ordem: Sequence[int], contagens: Sequence[Tuple[str, int]]) -> Dict[int, str]:
    atribuicao: Dict[int, str] = {}
    cursor = 0
    for simbolo, quantidade in contagens:
        for indice in ordem[cursor:cursor + quantidade]:
            atribuicao[indice] = simbolo
        cursor += quantidade
    return atribuicao


def _vetor_minimo(frac_a: Sequence[float], frac_b: Sequence[float], estrutura: str,
                  c_a: Optional[float], n: int) -> Tuple[float, float, float]:
    """Vetor cartesiano de b para a pela convenção de imagem mínima na supercélula n×n×n."""
    delta = []
    for m in range(3):
        d = float(frac_a[m]) - float(frac_b[m])
        d -= n * math.floor(d / n + 0.5)
        delta.append(d)
    return frac_para_cart(estrutura, delta, c_a)


def _aplicar_distorcao(atomos: List[Dict[str, Any]], solvente: str, raios: Mapping[str, float],
                       a_nm: float, estrutura: str, c_a: Optional[float], n: int) -> None:
    """Desloca vizinhos do soluto em metade do desajuste de raios, limitado a 0,12·a (ilustrativo).

    Calculado sobre os átomos ÚNICOS, com imagem mínima: as cópias de fronteira recebem depois o mesmo
    deslocamento da origem (corrige L-12, em que cópias do mesmo átomo iam para lados diferentes).
    """
    hospedeiros = [i for i, a in enumerate(atomos) if a["elemento"] == solvente]
    if not hospedeiros:
        return
    r_base = raios[solvente]
    deslocamentos = {i: [0.0, 0.0, 0.0] for i in hospedeiros}
    for atomo in atomos:
        if atomo["elemento"] == solvente:
            continue
        vizinhos = []
        for i in hospedeiros:
            vetor = _vetor_minimo(atomos[i]["frac"], atomo["frac"], estrutura, c_a, n)
            vizinhos.append((i, vetor, norma(vetor)))
        candidatos = [d for _i, _v, d in vizinhos if d > EPS]
        if not candidatos:
            continue
        minima = min(candidatos)
        for i, vetor, d in vizinhos:
            if d > minima * 1.05 or d < EPS:
                continue
            passo = max(-0.12, min(0.12, 0.5 * (raios[atomo["elemento"]] + r_base - d * a_nm) / a_nm))
            for j in range(3):
                deslocamentos[i][j] += passo * vetor[j] / d
    for i, (dx, dy, dz) in deslocamentos.items():
        total = math.sqrt(dx * dx + dy * dy + dz * dz)
        if total < 1e-12:
            continue
        escala = min(1.0, 0.15 / total)
        p = atomos[i]["pos"]
        atomos[i]["pos_ideal"] = list(p)
        atomos[i]["pos"] = [p[0] + dx * escala, p[1] + dy * escala, p[2] + dz * escala]


def _montar_atomos(pedido: PedidoLiga, c_a: Optional[float], quantidades: Mapping[str, int],
                   rng: random.Random, regra_ordenada: Optional[Tuple[Callable[[Sequence[float]], bool], str]],
                   ) -> Tuple[List[Dict[str, Any]], Dict[str, int], int]:
    """Átomos ÚNICOS da supercélula periódica, já com elemento, sítio e ocupação."""
    estrutura, n = pedido.estrutura, pedido.n
    info = ESTRUTURAS[estrutura]
    base = [frac for frac, _tipo in info["base"]]
    tipos_base = [tipo for _frac, tipo in info["base"]]
    nc_rede, nc_rede_txt = int(info["nc"]), str(info["nc"])
    if estrutura == "HC" and c_a is not None:
        ideal = c_a_ideal()
        if abs(float(c_a) - ideal) > TOLERANCIA_EDICAO * ideal:
            nc_rede_txt = "6 + 6"

    rede = sitios_unicos(base, n)
    ordem = _sorteio_chaves(rng, len(rede))           # consumido sempre, qualquer que seja o arranjo
    substitucionais = pedido.substitucionais
    contagem_final: Dict[str, int] = {s.simbolo: 0 for s in pedido.solutos}

    if regra_ordenada is not None:
        teste, _fase = regra_ordenada
        simbolo = substitucionais[0].simbolo
        atribuicao = {s["indice"]: simbolo for s in rede if teste(s["frac"])}
    else:
        atribuicao = _distribuir(ordem, [(s.simbolo, quantidades[s.simbolo]) for s in substitucionais])

    atomos: List[Dict[str, Any]] = []
    for sitio in rede:
        elemento = atribuicao.get(sitio["indice"], pedido.solvente.simbolo)
        if elemento != pedido.solvente.simbolo:
            contagem_final[elemento] += 1
        atomos.append({
            "id": _id_rede(sitio["celula"], sitio["base"]),
            "imagem": False, "imagem_de": None,
            "pos": list(frac_para_cart(estrutura, sitio["frac"], c_a)),
            "frac": list(sitio["frac"]),
            "celula": list(sitio["celula"]),
            "frac_celula": list(sitio["frac_celula"]),
            "tipo": "rede",
            "ocupacao": "solvente" if elemento == pedido.solvente.simbolo else "substitucional",
            "elemento": elemento,
            "sitio": {"nome": NOME_SITIO_REDE[tipos_base[sitio["base"]]], "wyckoff": None,
                      "nc": nc_rede, "nc_txt": nc_rede_txt},
            "fase": "matriz",
            "pos_ideal": None,
        })

    # intersticiais, por tipo de sítio, na ordem cúbico → octaédrico → tetraédrico
    for tipo in ORDEM_TIPOS:
        usuarios = [s for s in pedido.intersticiais if s.sitio == tipo]
        if not usuarios:
            continue
        pontos = posicoes(estrutura, tipo)
        sitios = sitios_unicos(pontos, n)
        ordem_sitios = _sorteio_chaves(rng, len(sitios))
        atribuicao_i = _distribuir(ordem_sitios, [(s.simbolo, quantidades[s.simbolo]) for s in usuarios])
        nc_sitio, nc_sitio_txt = nc_texto(estrutura, tipo, c_a)
        nome_sitio = str(SITIOS_INTERSTICIAIS[estrutura][tipo]["nome"])
        for sitio in sitios:
            elemento = atribuicao_i.get(sitio["indice"])
            if elemento is None:
                continue
            contagem_final[elemento] += 1
            atomos.append({
                "id": _id_intersticial(tipo, sitio["celula"], sitio["base"]),
                "imagem": False, "imagem_de": None,
                "pos": list(frac_para_cart(estrutura, sitio["frac"], c_a)),
                "frac": list(sitio["frac"]),
                "celula": list(sitio["celula"]),
                "frac_celula": list(sitio["frac_celula"]),
                "tipo": "intersticial",
                "ocupacao": "intersticial",
                "elemento": elemento,
                "sitio": {"nome": nome_sitio, "wyckoff": None, "nc": nc_sitio, "nc_txt": nc_sitio_txt},
                "fase": "matriz",
                "pos_ideal": None,
            })
    n_solvente = sum(1 for a in atomos if a["ocupacao"] == "solvente")
    return atomos, contagem_final, n_solvente


def _gerar_imagens(atomos: Sequence[Dict[str, Any]], estrutura: str, c_a: Optional[float],
                   n: int) -> List[Dict[str, Any]]:
    """Imagens periódicas de fronteira: mesmo elemento, sítio, ocupação e fase do átomo de origem."""
    imagens: List[Dict[str, Any]] = []
    for atomo in atomos:
        for tx, ty, tz in translacoes_de_imagem(atomo["frac"], n):
            deslocamento = frac_para_cart(estrutura, (tx, ty, tz), c_a)
            sufixo = f"+{int(tx > 0)}{int(ty > 0)}{int(tz > 0)}"
            imagem = dict(atomo)
            imagem["id"] = atomo["id"] + sufixo
            imagem["imagem"] = True
            imagem["imagem_de"] = atomo["id"]
            imagem["pos"] = [atomo["pos"][m] + deslocamento[m] for m in range(3)]
            imagem["frac"] = [atomo["frac"][m] + (tx, ty, tz)[m] for m in range(3)]
            imagem["celula"] = [atomo["celula"][m] + (tx, ty, tz)[m] for m in range(3)]
            imagem["frac_celula"] = list(atomo["frac_celula"])
            imagem["sitio"] = dict(atomo["sitio"])
            if atomo.get("pos_ideal") is not None:
                imagem["pos_ideal"] = [atomo["pos_ideal"][m] + deslocamento[m] for m in range(3)]
            imagens.append(imagem)
    return imagens


# --------------------------------------------------------------------------- caso de uso
def calcular_solucao_solida(payload: Mapping[str, Any], repo: RepositorioMateriais,
                            props: RepositorioPropriedades, politica: PoliticaDados) -> Dict[str, Any]:
    coletor = ColetorDados(politica)
    pedido = interpretar(payload, repo, props, coletor)
    solvente = pedido.solvente
    estrutura = pedido.estrutura
    info = ESTRUTURAS[estrutura]
    avisos: List[str] = list(pedido.avisos)
    indisponiveis: Dict[str, str] = {}

    c_a: Optional[float] = None
    c_a_natureza: Optional[str] = None
    if estrutura == "HC":
        if pedido.estrutura_do_solvente and solvente.c_a_efetivo is not None:
            c_a = float(solvente.c_a_efetivo)
            c_a_natureza = ("derivado_de_a_c_medidos"
                            if (solvente.a_nm is not None and solvente.c_nm is not None) else "tabelado")
        else:
            c_a = c_a_ideal()
            c_a_natureza = "ideal"

    k = float(info["a_em_R"])
    n_cel = int(info["n"])
    z_celula = len(info["base"])
    n_rede = z_celula * pedido.n ** 3
    vol_r = volume_em_r(estrutura, c_a)

    # --- quantidades e capacidade
    quantidades, _n_solvente_alvo = _quantidades(pedido, n_rede)
    _validar_capacidade(pedido, quantidades, pedido.n)
    n_unicos = n_rede + sum(quantidades[s.simbolo] for s in pedido.intersticiais)
    for soluto in pedido.solutos:
        if soluto.x > 0 and quantidades[soluto.simbolo] == 0:
            avisos.append(
                f"{soluto.simbolo}: {txt(soluto.x * 100, 4)} at% está abaixo da resolução desta supercélula "
                f"(1 átomo = {txt(100.0 / n_unicos, 4)} at%); nenhum átomo foi colocado. Aumente n.")

    # --- parâmetro de rede e densidade (composição SOLICITADA)
    x_i = pedido.x_intersticial
    y = {s.simbolo: s.x / (1.0 - x_i) for s in pedido.substitucionais}
    y_solvente = 1.0 - sum(y.values())
    r_medio = y_solvente * solvente.raio_nm + sum(y[s.simbolo] * s.raio_nm for s in pedido.substitucionais)
    a_base = k * solvente.raio_nm
    a_nm = k * r_medio
    massa_rede = y_solvente * solvente.peso_g_mol + sum(y[s.simbolo] * s.massa_g_mol
                                                        for s in pedido.substitucionais)
    massa_intersticial = sum(s.x / (1.0 - x_i) * s.massa_g_mol for s in pedido.intersticiais)
    massa_cel = n_cel * (massa_rede + massa_intersticial)
    volume_cm3 = vol_r * (a_nm / k) ** 3 * NM_PARA_CM ** 3
    densidade = massa_cel / (volume_cm3 * N_AVOGADRO)
    densidade_base = n_cel * solvente.peso_g_mol / (vol_r * solvente.raio_nm ** 3 * NM_PARA_CM ** 3 * N_AVOGADRO)
    if solvente.tem_rede_medida:
        avisos.append(
            f"O {solvente.simbolo} tem parâmetro de rede medido no repositório (a = {txt(solvente.a_nm, 4)} nm), "
            f"mas a liga usa a rede derivada do raio (a = {txt(a_base, 4)} nm) pelo modelo de contato. "
            f"Trocar a base da interpolação pelo valor medido depende de aprovação (pendência V-14).")

    # --- arranjo
    notas: List[str] = []
    fase_ordenada: Optional[str] = None
    regra = None
    if pedido.arranjo == "ordenado":
        if len(pedido.substitucionais) == 1:
            regra = _regra_ordenada(estrutura, y[pedido.substitucionais[0].simbolo])
        elif len(pedido.substitucionais) > 1:
            notas.append("Mais de um soluto substitucional: não há protótipo ordenado; usada distribuição "
                         "aleatória sobre os sítios de rede.")
        if regra is None and not notas:
            notas.append("Sem superestrutura de protótipo para essa composição; usada distribuição aleatória. "
                         "Protótipos disponíveis: CFC com 25, 50 ou 75 % e CCC com 50 %.")
        if regra is not None:
            fase_ordenada = regra[1]
            notas.append(AVISO_ORDENADO)
        if pedido.intersticiais:
            notas.append("Intersticiais são distribuídos ao acaso entre os sítios livres.")

    rng = random.Random(pedido.semente)  # noqa: S311 — sorteio didático reprodutível, sem uso criptográfico
    atomos, contagem, n_solvente = _montar_atomos(pedido, c_a, quantidades, rng, regra)
    if fase_ordenada is not None:
        quantidades = dict(contagem)
        solicitado = pedido.substitucionais[0]
        if abs(contagem[solicitado.simbolo] / n_rede - y[solicitado.simbolo]) > 1e-9:
            avisos.append(
                "O desenho tem a estequiometria ideal do protótipo; % em massa, parâmetro de rede e densidade "
                "foram calculados para a composição solicitada.")
    else:
        quantidades = dict(contagem)

    raios = {solvente.simbolo: float(solvente.raio_nm), **{s.simbolo: s.raio_nm for s in pedido.solutos}}
    distorcao = None
    if pedido.distorcer:
        _aplicar_distorcao(atomos, solvente.simbolo, raios, a_nm, estrutura, c_a, pedido.n)
        distorcao = {"classe": "simulacao_ilustrativa",
                     "descricao": "Vizinhos do soluto deslocados em metade do desajuste de raios, "
                                  "limitado a 0,12·a. Não é relaxação elástica."}
    atomos.extend(_gerar_imagens(atomos, estrutura, c_a, pedido.n))
    for atomo in atomos:
        atomo["raio_rel"] = raios[atomo["elemento"]] / a_nm
        atomo["pos_nm"] = [v * a_nm for v in atomo["pos"]]
    arestas = [[list(p) for p in aresta] for aresta in arestas_da_caixa(estrutura, c_a, pedido.n)]

    composicao = _composicao(pedido, quantidades, n_solvente, n_rede, len(atomos))

    # --- sítios, regras e elementos
    sitios: List[Dict[str, Any]] = []
    for soluto in pedido.intersticiais:
        sitios.append(descrever_sitio(estrutura, str(soluto.sitio), c_a=c_a,
                                      raio_solvente_nm=float(solvente.raio_nm), elemento=soluto.simbolo,
                                      escolha=soluto.escolha_sitio))
    sitio_por_soluto = {s["elemento"]: s for s in sitios}

    regras_por_soluto: List[Dict[str, Any]] = []
    for soluto in pedido.solutos:
        if soluto.intersticial:
            regras, conclusao = _regras_intersticiais(soluto, sitio_por_soluto[soluto.simbolo],
                                                      float(solvente.raio_nm))
        else:
            regras = _regras_substitucionais(solvente, _metal_do_soluto(soluto), props, coletor)
            conclusao = _conclusao(regras)
        regras_por_soluto.append({"soluto": soluto.simbolo, "modo": soluto.modo,
                                  "regras": regras, "conclusao": conclusao})

    elementos: List[Dict[str, Any]] = []
    citacao = repo.fonte(solvente.fonte)
    for simbolo, papel, dados in [
        (solvente.simbolo, "solvente",
         {"raio_nm": float(solvente.raio_nm), "massa_g_mol": float(solvente.peso_g_mol),
          "estrutura_elemento_puro": solvente.estrutura, "estado_do_dado": "aguardando_validacao",
          "fonte": citacao.get("citacao") if citacao else None}),
        *[(s.simbolo, s.modo,
           {"raio_nm": s.raio_nm, "massa_g_mol": s.massa_g_mol,
            "estrutura_elemento_puro": s.estrutura_pura, "estado_do_dado": s.estado_do_dado,
            "fonte": s.fonte}) for s in pedido.solutos],
    ]:
        elementos.append({"simbolo": simbolo, "papel": papel, **dados})
        for campo in ("raio_nm", "massa_g_mol", "estrutura_elemento_puro", "fonte"):
            if dados[campo] is None:
                indisponiveis[f"elementos.{simbolo}.{campo}"] = (
                    "o repositório não cadastra este dado para o elemento "
                    f"(estado: {dados['estado_do_dado']})")

    # --- blocos de natureza, fases e verificações
    tem_subst = bool(pedido.substitucionais)
    tem_inters = bool(pedido.intersticiais)
    hipoteses = ["todos os sítios de rede ocupados (sem lacunas)", "fase única imposta",
                 "posições ideais de rede, sem relaxação estrutural"]
    if fase_ordenada is None:
        hipoteses.append("ocupação aleatória sem interação soluto–soluto")
    if tem_inters:
        hipoteses.append("intersticiais não dilatam a rede")
    if estrutura == "HC":
        hipoteses.append("c/a do solvente mantido")
    modelo = {
        "tipo_solucao": "mista" if (tem_subst and tem_inters) else ("intersticial" if tem_inters
                                                                    else "substitucional"),
        "ordenacao": "ordenada_prototipo" if fase_ordenada else "desordenada",
        "fases": "monofasica_imposta",
        "geometria": "idealizada",
        "parametro_rede": "estimativa_vegard_sobre_raios",
        "parametro_rede_solvente": "derivado_de_R",
        "c_a": c_a_natureza,
        "hipoteses": hipoteses,
    }
    prototipo = (_prototipo(fase_ordenada, solvente.simbolo, pedido.substitucionais[0].simbolo)
                 if fase_ordenada else None)
    fases = [{"id": "matriz", "nome": "solução sólida na estrutura do solvente", "estrutura": estrutura,
              "origem": "imposta_pelo_modelo", "composicao": composicao["representada"],
              "fracao": None, "fracao_motivo": MOTIVO_FRACAO_FASE}]
    verificacoes = {
        "limite_solubilidade": {"verificado": False, "valor": None, "motivo": MOTIVO_LIMITE},
        "fases_secundarias": {"previstas": None, "motivo": MOTIVO_FASES_SECUNDARIAS},
    }

    avisos.append(AVISO_FASE_UNICA)
    for soluto in pedido.intersticiais:
        avisos.append(
            f"Nem todo o {soluto.simbolo} de uma liga real está dissolvido na matriz: acima do limite de "
            f"solubilidade ele forma outras fases (por exemplo, carbonetos ou nitretos), que não são "
            f"representadas aqui.")
    if tem_inters:
        avisos.append("A densidade foi calculada com a rede do solvente NÃO dilatada pelos intersticiais: "
                      "nessa hipótese o valor tende a superestimar a densidade real.")

    conclusao_global: Optional[str] = regras_por_soluto[0]["conclusao"]
    if len(pedido.solutos) > 1:
        conclusao_global = None
        indisponiveis["conclusao_global"] = MOTIVO_CONCLUSAO_GLOBAL

    # --- campos legados (referem-se ao primeiro soluto da ordem canônica)
    primeiro = pedido.solutos[0]
    solicitada_por_simbolo = {c["elemento"]: c for c in composicao["solicitada"]}
    x_pct = solicitada_por_simbolo[primeiro.simbolo]["at_pct"]
    pct_peso = solicitada_por_simbolo[primeiro.simbolo]["massa_pct"]
    n_soluto = sum(quantidades[s.simbolo] for s in pedido.solutos)
    simbolos = "–".join([solvente.simbolo] + [s.simbolo for s in pedido.solutos])

    passos = _passos(pedido, solvente, r_medio, a_base, a_nm, massa_cel, volume_cm3, densidade,
                     densidade_base, pct_peso, composicao)
    parametros = {"base": solvente.simbolo,
                  "solutos": [{"elemento": s.simbolo, "x": s.x * 100.0, "modo": s.modo, "sitio": s.sitio}
                              for s in pedido.solutos],
                  "base_composicao": pedido.base_composicao, "estrutura_matriz": estrutura,
                  "n": pedido.n, "semente": pedido.semente, "arranjo": pedido.arranjo,
                  "distorcer": pedido.distorcer}
    return {
        "rotulo": f"Liga {simbolos}",
        "base": solvente.simbolo, "soluto": primeiro.simbolo, "intersticial": primeiro.intersticial,
        "estrutura": estrutura, "estrutura_nome": info["nome"], "nc": info["nc"], "c_a": c_a,
        "supercelula": pedido.n, "semente": pedido.semente, "x_pct": x_pct, "pct_peso": pct_peso,
        "a_nm": a_nm, "c_nm": a_nm * c_a if c_a else None, "a_base_nm": a_base,
        "raio_relativo": float(solvente.raio_nm) / a_nm, "densidade": densidade,
        "densidade_base": densidade_base,
        "n_soluto": n_soluto, "n_solvente": n_solvente,
        "fase_ordenada": fase_ordenada, "nota_arranjo": " ".join(notas) or None,
        "sitio": sitios[0] if sitios else None,
        "regras": regras_por_soluto[0]["regras"], "conclusao": regras_por_soluto[0]["conclusao"],
        "passos": passos,
        "distorcao": distorcao, "atomos": atomos, "arestas": arestas,
        # --- campos novos (contrato R1 §2.2)
        "composicao": composicao,
        "realizacao": {
            "tipo": ("ordenada_prototipo" if fase_ordenada else
                     ("sem_soluto" if n_soluto == 0 else "estatistica")),
            "semente": pedido.semente, "algoritmo": ALGORITMO_SORTEIO, "n": pedido.n,
            "aviso": AVISO_REALIZACAO,
        },
        "modelo": modelo,
        "prototipo": prototipo,
        "fases": fases,
        "verificacoes": verificacoes,
        "regras_por_soluto": regras_por_soluto,
        "conclusao_global": conclusao_global,
        "sitios": sitios,
        "elementos": elementos,
        "convencoes": list(CONVENCOES),
        "indisponiveis": indisponiveis,
        "procedencia": bloco_procedencia(
            classe="estimativa_modelo", motor="crystallography", versao_motor=VERSAO_MOTOR,
            versao_dados=f"{repo.versao_dados}+{props.versao_dados}" if props is not repo else repo.versao_dados,
            parametros=parametros, coletor=coletor, fontes_modelo=FONTES_MODELO, avisos=avisos),
    }


def _passos(pedido: PedidoLiga, solvente: Metal, r_medio: float, a_base: float, a_nm: float,
            massa_cel: float, volume_cm3: float, densidade: float, densidade_base: float,
            pct_peso: float, composicao: Mapping[str, Any]) -> List[Dict[str, str]]:
    info = ESTRUTURAS[pedido.estrutura]
    primeiro = pedido.solutos[0]
    massas = ", ".join(f"A({c['elemento']}) = {txt(a, 3)}" for c, a in
                       zip(composicao["solicitada"],
                           [float(solvente.peso_g_mol)] + [s.massa_g_mol for s in pedido.solutos],
                           strict=True))
    passos = [{
        "titulo": "Composição em massa",
        "formula": (f"C({primeiro.simbolo}) = x·A / Σ(x·A) = {txt(pct_peso, 2)} % em massa"),
        "detalhe": ("Composição solicitada: "
                    + "; ".join(f"{c['elemento']} {txt(c['at_pct'], 3)} at% = {txt(c['massa_pct'], 3)} % em massa"
                                for c in composicao["solicitada"])
                    + f". Massas molares (g/mol): {massas}."),
    }]
    if pedido.substitucionais:
        denominador = 1.0 - pedido.x_intersticial
        y_solvente = 1.0 - sum(s.x for s in pedido.substitucionais) / denominador
        termos = " + ".join([f"{txt(y_solvente, 3)}·R({solvente.simbolo})"]
                            + [f"{txt(s.x / denominador, 3)}·R({s.simbolo})"
                               for s in pedido.substitucionais])
        passos.append({
            "titulo": "Lei de Vegard (interpolação de raios)",
            "formula": (f"R̄ = {termos} = {txt(r_medio, 4)} nm\n"
                        f"a = {info['substituicao'].format(R=txt(r_medio, 4))} = {txt(a_nm, 4)} nm "
                        f"({sinal((a_nm / a_base - 1) * 100)}{txt((a_nm / a_base - 1) * 100, 2)} % em relação ao "
                        f"{solvente.simbolo} puro)"),
            "detalhe": ("Relação empírica: o parâmetro de rede varia linearmente com o raio médio dos átomos "
                        "DE REDE, na estrutura do solvente. Intersticiais não entram nesta média e, neste "
                        "modelo, não dilatam a rede."),
        })
    passos.append({
        "titulo": "Densidade da liga",
        "formula": (f"ρ = m(célula) / (Vc·N_A) = {txt(massa_cel, 3)} / ({sci(volume_cm3)} × 6,022 × 10²³) "
                    f"= {txt(densidade, 3)} g/cm³"),
        "detalhe": f"{solvente.simbolo} puro: {txt(densidade_base, 3)} g/cm³.",
    })
    return passos


__all__ = ["SITIOS", "X_MAXIMO_INTERSTICIAL", "calcular_solucao_solida"]
