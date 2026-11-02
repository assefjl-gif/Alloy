"""Serviço de índices de Miller: planos (hkl)/(hkil) e direções [uvw]/[uvtw].

O algoritmo é o da v1.0. Mudanças da v1.1:
* usa geometria sem arredondamento (CR-08) e arredonda só na saída;
* sinaliza índices não reduzidos — ``ordem`` e ``indices_reduzidos`` (CR-03);
* erros são ``ErroDominio`` (BE-06) e os resultados trazem ``avisos``.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .constantes import EPS, FAIXA_A_NM, FAIXA_C_A, FAMILIA_MAXIMA, INDICE_MAXIMO, Vetor
from .entradas import numero_opcional
from .erros import EntradaInvalida, IndiceMillerInvalido, PlanoForaDaCelula
from .estruturas import c_a_ideal, normalizar_estrutura, sem_acentos
from .formatacao import notacao
from .geometria import (
    arredondar,
    cart_para_frac,
    cross,
    dot,
    frac_para_cart,
    geometria_celula,
    gradiente_plano,
    norma,
    sub,
)
from .planar import calcular_planar
from .supercelula import cantos_da_caixa, geometria_supercelula, validar_tamanho


def reduzir(indices: Sequence[int]) -> List[int]:
    divisor = 0
    for valor in indices:
        divisor = math.gcd(divisor, abs(int(valor)))
    return [int(v) // divisor for v in indices] if divisor > 1 else [int(v) for v in indices]


def _mdc(indices: Sequence[int]) -> int:
    divisor = 0
    for valor in indices:
        divisor = math.gcd(divisor, abs(int(valor)))
    return divisor or 1


def _calcular_plano(estrutura: str, indices: List[int], c_a: Optional[float],
                    a_nm: Optional[float], atomos: List[Dict[str, Any]],
                    arestas: List[List[List[float]]], supercelula: int = 1) -> Dict[str, Any]:
    bravais = None
    if estrutura == "HC":
        if len(indices) == 4:
            h, k, i, l = indices  # noqa: E741
            if i != -(h + k):
                raise IndiceMillerInvalido(f"Em Miller-Bravais, i = -(h + k). "
                                           f"Para h={h} e k={k}, use i={-(h + k)}.")
        else:
            h, k, l = indices  # noqa: E741
            i = -(h + k)
        bravais = (h, k, i, l)
        deslocamento = 1.0 + (l if l < 0 else 0)
    else:
        h, k, l = indices  # noqa: E741
        deslocamento = 1.0 + sum(v for v in (h, k, l) if v < 0)

    def valor(p: Sequence[float]) -> float:
        f = cart_para_frac(estrutura, p, c_a)
        return h * f[0] + k * f[1] + l * f[2]

    def funcao(p: Sequence[float]) -> float:
        return valor(p) - deslocamento

    gradiente = gradiente_plano(estrutura, h, k, l, c_a)
    modulo = norma(gradiente)
    normal = (gradiente[0] / modulo, gradiente[1] / modulo, gradiente[2] / modulo)
    corte = _poligono_de_corte(funcao, arestas, normal)
    if corte is None:
        raise PlanoForaDaCelula("Com a origem padrão, esse plano não intercepta a célula unitária desenhada.")
    pontos, centro, area = corte

    d_rel = 1.0 / modulo
    no_plano = [idx for idx, atomo in enumerate(atomos) if abs(funcao(atomo["pos"])) < 1e-7]

    exibidos = list(bravais) if bravais else [h, k, l]
    ordem = _mdc((h, k, l))
    planar = calcular_planar(estrutura, (h, k, l), ordem, pontos,
                             [atomos[i]["pos"] for i in no_plano], area, a_nm)

    familia: Optional[List[Dict[str, Any]]] = None
    if supercelula > 1:
        # Todos os planos paralelos h·x + k·y + l·z = m que cortam a supercélula; destaca o do meio
        # (em várias redes TODO átomo pertence a algum plano da família, então destacar todos não informa).
        atomos_sc, arestas_sc = geometria_supercelula(estrutura, c_a, supercelula)
        valores = [valor(p) for p in cantos_da_caixa(estrutura, c_a, supercelula)]
        familia = []
        for m in range(math.ceil(min(valores) - EPS), math.floor(max(valores) + EPS) + 1):
            corte_m = _poligono_de_corte(lambda p, m=m: valor(p) - m, arestas_sc, normal)
            if corte_m:
                familia.append({"m": m, "poligono": [arredondar(p) for p in corte_m[0]],
                                "centro": arredondar(corte_m[1])})
        familia = familia[:FAMILIA_MAXIMA]
        no_plano = []
        if familia:
            meio = familia[len(familia) // 2]
            centro = tuple(meio["centro"])
            no_plano = [idx for idx, atomo in enumerate(atomos_sc) if abs(valor(atomo["pos"]) - meio["m"]) < 1e-7]
    reduzidos = reduzir(exibidos)
    avisos: List[str] = []
    if ordem > 1:
        avisos.append(
            f"{notacao(exibidos, '(', ')')} tem fator comum {ordem}: é paralelo a "
            f"{notacao(reduzidos, '(', ')')} com espaçamento d/{ordem} (em difração, reflexão de "
            f"{ordem}ª ordem). A contagem de átomos acima vale só para o plano desenhado.")

    return {
        "tipo": "plano", "estrutura": estrutura, "indices": indices,
        "notacao": notacao(exibidos, "(", ")"),
        "notacao_alternativa": (notacao((h, k, l), "(", ")") + " em 3 índices") if bravais else None,
        "poligono": [arredondar(p) for p in pontos],
        "centro": arredondar(centro),
        "normal": arredondar(normal),
        "area_rel": area,
        "area_nm2": area * a_nm ** 2 if a_nm else None,
        "d_rel": d_rel,
        "d_nm": d_rel * a_nm if a_nm else None,
        "atomos": no_plano,
        "ordem": ordem,
        "indices_reduzidos": reduzidos,
        "planar": planar,
        "supercelula": supercelula,
        "familia": familia,
        "avisos": avisos,
    }


def _poligono_de_corte(funcao: Callable[[Sequence[float]], float], arestas: Sequence[Sequence[Sequence[float]]],
                       normal: Vetor) -> Optional[Tuple[List[Vetor], Vetor, float]]:
    """Polígono ordenado, centro e área da interseção do plano ``funcao(p) = 0`` com as arestas da caixa."""
    pontos: List[Vetor] = []

    def adicionar(p: Sequence[float]) -> None:
        candidato = (float(p[0]), float(p[1]), float(p[2]))
        if not any(norma(sub(candidato, q)) < 1e-7 for q in pontos):
            pontos.append(candidato)

    for a, b in arestas:
        fa, fb = funcao(a), funcao(b)
        if abs(fa) < EPS:
            adicionar(a)
        if abs(fb) < EPS:
            adicionar(b)
        if abs(fa) >= EPS and abs(fb) >= EPS and fa * fb < 0:
            t = fa / (fa - fb)
            adicionar((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2])))

    if len(pontos) < 3:
        return None
    centro = (sum(p[0] for p in pontos) / len(pontos), sum(p[1] for p in pontos) / len(pontos),
              sum(p[2] for p in pontos) / len(pontos))
    eixo_u = sub(pontos[0], centro)
    if norma(eixo_u) < EPS:
        return None
    eixo_u = tuple(v / norma(eixo_u) for v in eixo_u)
    eixo_v = cross(normal, eixo_u)
    pontos.sort(key=lambda p: math.atan2(dot(sub(p, centro), eixo_v), dot(sub(p, centro), eixo_u)))

    area_vetor = (0.0, 0.0, 0.0)
    for idx, p in enumerate(pontos):
        c = cross(p, pontos[(idx + 1) % len(pontos)])
        area_vetor = (area_vetor[0] + c[0], area_vetor[1] + c[1], area_vetor[2] + c[2])
    area = abs(dot(area_vetor, normal)) / 2.0
    if area < EPS:
        return None
    return pontos, centro, area


def _calcular_direcao(estrutura: str, indices: List[int], c_a: Optional[float],
                      a_nm: Optional[float], atomos: List[Dict[str, Any]]) -> Dict[str, Any]:
    alternativa = None
    inicio_frac: Vetor
    if estrutura == "HC":
        if len(indices) == 4:
            u, v, t, w = indices
            if t != -(u + v):
                raise IndiceMillerInvalido(f"Em Miller-Bravais, t = -(u + v). "
                                           f"Para u={u} e v={v}, use t={-(u + v)}.")
            U, V, W = reduzir([u - t, v - t, w])
            texto = notacao((u, v, t, w), "[", "]")
            alternativa = notacao((U, V, W), "[", "]") + " em 3 índices"
        else:
            U, V, W = reduzir(indices)
            quatro = reduzir([2 * U - V, 2 * V - U, -(U + V), 3 * W])
            texto = notacao((U, V, W), "[", "]")
            alternativa = notacao(quatro, "[", "]") + " em Miller-Bravais"
        inicio_frac = (0.0, 0.0, 1.0 if W < 0 else 0.0)
    else:
        U, V, W = reduzir(indices)
        texto = notacao((U, V, W), "[", "]")
        inicio_frac = (1.0 if U < 0 else 0.0, 1.0 if V < 0 else 0.0, 1.0 if W < 0 else 0.0)

    maior = max(abs(U), abs(V), abs(W))
    fim_frac = (inicio_frac[0] + U / maior, inicio_frac[1] + V / maior, inicio_frac[2] + W / maior)
    inicio = frac_para_cart(estrutura, inicio_frac, c_a)
    fim = frac_para_cart(estrutura, fim_frac, c_a)
    vetor = sub(fim, inicio)
    comprimento = norma(vetor)

    na_direcao: List[int] = []
    contagem = 0.0
    tol = 1e-7
    for idx, atomo in enumerate(atomos):
        t = dot(sub(atomo["pos"], inicio), vetor) / comprimento ** 2
        projecao = (inicio[0] + t * vetor[0], inicio[1] + t * vetor[1], inicio[2] + t * vetor[2])
        if -tol <= t <= 1 + tol and norma(sub(projecao, atomo["pos"])) < tol:
            na_direcao.append(idx)
            contagem += 0.5 if (abs(t) < tol or abs(t - 1) < tol) else 1.0

    ponto_de_rede = maior == 1
    densidade_rel = contagem / comprimento if ponto_de_rede else None

    return {
        "tipo": "direcao", "estrutura": estrutura, "indices": indices,
        "notacao": texto, "notacao_alternativa": alternativa,
        "inicio": arredondar(inicio), "fim": arredondar(fim),
        "comprimento_rel": comprimento,
        "comprimento_nm": comprimento * a_nm if a_nm else None,
        "atomos_contados": contagem if ponto_de_rede else None,
        "densidade_linear_rel": densidade_rel,
        "densidade_linear_nm": densidade_rel / a_nm if (densidade_rel is not None and a_nm) else None,
        "atomos": na_direcao,
        "ordem": _mdc(indices),
        "indices_reduzidos": [U, V, W],
        "avisos": [],
    }


_TIPOS = {"direcao": "direcao", "direction": "direcao", "dir": "direcao",
          "plano": "plano", "plane": "plano"}


def normalizar_tipo(bruto: Any) -> str:
    tipo = _TIPOS.get(sem_acentos(str(bruto or "plano")))
    if not tipo:
        raise EntradaInvalida("Tipo deve ser 'plano' ou 'direcao'.")
    return tipo


def calcular_miller(payload: Mapping[str, Any]) -> Dict[str, Any]:
    estrutura = normalizar_estrutura(str(payload.get("estrutura") or ""))
    if not estrutura:
        raise EntradaInvalida("Carregue uma estrutura (CS, CCC, CFC ou HC) antes de desenhar índices.")
    tipo = normalizar_tipo(payload.get("tipo"))

    brutos = payload.get("indices")
    if not isinstance(brutos, (list, tuple)):
        raise IndiceMillerInvalido("Envie os índices como lista, ex.: [1, 1, 1].")
    try:
        if any(isinstance(v, bool) for v in brutos):
            raise ValueError
        indices = [int(round(float(v))) for v in brutos]
        if any(abs(float(v) - i) > 1e-9 for v, i in zip(brutos, indices, strict=True)):
            raise ValueError
    except (TypeError, ValueError):
        raise IndiceMillerInvalido("Índices de Miller devem ser números inteiros.") from None

    hexagonal = estrutura == "HC"
    if not hexagonal and len(indices) != 3:
        raise IndiceMillerInvalido("Sistemas cúbicos usam 3 índices, ex.: plano 1 1 0.")
    if hexagonal and len(indices) not in (3, 4):
        raise IndiceMillerInvalido("Na HC use 3 índices ou 4 (Miller-Bravais), ex.: plano 1 0 -1 1.")
    if all(v == 0 for v in indices):
        raise IndiceMillerInvalido("Os índices não podem ser todos nulos.")
    if any(abs(v) > INDICE_MAXIMO for v in indices):
        raise IndiceMillerInvalido(f"Use índices entre -{INDICE_MAXIMO} e {INDICE_MAXIMO}.")

    c_a = None
    if hexagonal:
        c_a = numero_opcional(payload, "c_a", FAIXA_C_A, "razão c/a") or c_a_ideal()
    a_nm = numero_opcional(payload, "a_nm", FAIXA_A_NM, "parâmetro de rede (nm)")
    supercelula = validar_tamanho(payload.get("supercelula") or 1)
    atomos, arestas = geometria_celula(estrutura, c_a)

    if tipo == "plano":
        return _calcular_plano(estrutura, indices, c_a, a_nm, atomos, arestas, supercelula)
    if supercelula > 1:
        atomos = geometria_supercelula(estrutura, c_a, supercelula)[0]
    resultado = _calcular_direcao(estrutura, indices, c_a, a_nm, atomos)
    resultado["supercelula"] = supercelula
    return resultado
