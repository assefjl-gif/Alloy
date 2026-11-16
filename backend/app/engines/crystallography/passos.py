"""Passo a passo do parâmetro de rede e do FEA (portado da v1.4 — RQ-CIE-10; fecha D-12 do frontend).

Os valores intermediários vêm do resultado do motor: nada é recalculado por outra fórmula.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional

from .constantes import SQRT3
from .estruturas import ESTRUTURAS
from .formatacao import sinal, txt
from .geometria import (
    c_a_ideal_hc,
    contato_tipo_hc,
    distancia_entre_planos_hc,
    raio_contato_rel_hc,
    volume_em_r,
)

#: Condição de contato das esferas rígidas (Callister & Rethwisch, seções 3.4 e 3.5).
CONTATO = {"CS": "a = 2R", "CCC": "a√3 = 4R", "CFC": "a√2 = 4R", "HC": "a = 2R"}

Passo = Dict[str, Optional[str]]


def passos_parametro(r: Mapping[str, Any]) -> List[Passo]:
    estrutura = r["estrutura"]
    info = ESTRUTURAS[estrutura]
    k = float(info["a_em_R"])
    raio, a_nm, c_nm, c_a = r.get("raio_nm"), r.get("a_nm"), r.get("c_nm"), r.get("c_a")
    fonte = r.get("a_fonte")
    passos: List[Passo] = [{
        "titulo": "Condição de contato",
        "formula": f"{CONTATO[estrutura]}  →  {info['relacao']}",
        "detalhe": f"As esferas rígidas se tocam ao longo da {info['contato']}.",
    }]
    if fonte == "relativo" or a_nm is None:
        passos.append({"titulo": "Em unidades de R", "formula": f"a = {txt(k, 4)}·R",
                       "detalhe": "Informe o raio atômico ou o parâmetro a para obter valores em nm."})
        return passos
    if fonte == "medido":
        modelo = k * raio if raio is not None else None
        detalhe = "Valor de difração de raios X tabelado; tem prioridade sobre o modelo de contato (ADR-005)."
        if modelo is not None:
            detalhe += (f" O modelo daria a = {txt(k, 4)} × {txt(raio, 4)} = {txt(modelo, 4)} nm "
                        f"({sinal((modelo / a_nm - 1) * 100)}{txt((modelo / a_nm - 1) * 100, 2)} %).")
        passos.append({"titulo": "Parâmetro de rede medido",
                       "formula": f"a = {txt(a_nm, 4)} nm = {txt(a_nm * 10, 3)} Å", "detalhe": detalhe})
    elif fonte == "informado":
        passos.append({"titulo": "Raio a partir de a informado",
                       "formula": f"R = a / {txt(k, 4)} = {txt(a_nm, 4)} / {txt(k, 4)} = {txt(raio, 4)} nm",
                       "detalhe": "Caminho inverso: o parâmetro de rede define o raio pela condição de contato."})
    else:
        passos.append({"titulo": "Substituição numérica",
                       "formula": f"a = {info['substituicao'].format(R=txt(raio, 4))} = {txt(a_nm, 4)} nm "
                                  f"= {txt(a_nm * 10, 3)} Å",
                       "detalhe": None})
    if raio is not None:
        fora_do_ideal = estrutura == "HC" and c_a is not None and contato_tipo_hc(float(c_a)) != "ambos"
        if fora_do_ideal and a_nm is not None:
            d_fora = distancia_entre_planos_hc(float(c_a))
            passos.append({
                "titulo": "Vizinhos mais próximos",
                "formula": (f"6 vizinhos no plano basal a d = a = {txt(a_nm, 4)} nm\n"
                            f"6 vizinhos entre planos a d = √(1/3 + (c/a)²/4)·a = {txt(d_fora, 4)}·a "
                            f"= {txt(d_fora * a_nm, 4)} nm"),
                "detalhe": (f"Com c/a = {txt(float(c_a), 4)} ≠ √(8/3) os 12 vizinhos não são equidistantes "
                            f"(NC = 12, descrito como 6 + 6); a relação d = 2R vale só no c/a ideal."),
            })
        else:
            passos.append({"titulo": "Vizinhos mais próximos", "formula": f"d = 2R = {txt(2 * raio, 4)} nm",
                           "detalhe": f"Cada átomo tem {info['nc']} vizinhos a essa distância "
                                      f"(NC = {info['nc']})."})
    if estrutura == "HC" and c_nm is not None and c_a is not None:
        passos.append({"titulo": "Altura da célula",
                       "formula": f"c = (c/a)·a = {txt(c_a, 4)} × {txt(a_nm, 4)} = {txt(c_nm, 4)} nm",
                       "detalhe": "Com c/a ideal = √(8/3) ≈ 1,633 os planos basais se empilham sem folga."})
    return passos


def _passos_fea_hc(c_a: float, fea: float) -> List[Passo]:
    """FEA do HC pelo raio de contato (parecer R1-CRI-01 §1.4): sem sobreposição em nenhum c/a."""
    d_fora = distancia_entre_planos_hc(c_a)
    raio_c = raio_contato_rel_hc(c_a)
    vs = 2.0 * (4.0 / 3.0) * math.pi * raio_c ** 3
    vc = (SQRT3 / 2.0) * c_a
    menor = "entre planos basais" if d_fora < 1.0 else "na aresta do hexágono basal"
    return [
        {"titulo": "Menor distância entre vizinhos",
         "formula": (f"d(basal) = a;   d(entre planos) = √(1/3 + (c/a)²/4)·a = {txt(d_fora, 6)}·a\n"
                     f"R_c = ½·mín(a; d entre planos) = {txt(raio_c, 6)}·a"),
         "detalhe": (f"Esferas rígidas não se sobrepõem: o raio é metade da MENOR distância entre vizinhos. "
                     f"Com c/a = {txt(c_a, 4)} essa distância é {menor}.")},
        {"titulo": "Volume ocupado pelas esferas",
         "formula": f"Vs = z·(4/3)π·R_c³ = 2 × (4/3)π × ({txt(raio_c, 6)}·a)³ = {txt(vs, 4)}·a³",
         "detalhe": "A célula primitiva hexagonal contém z = 2 átomos."},
        {"titulo": "Volume da célula",
         "formula": f"Vc = (√3/2)·a²·c = (√3/2)·{txt(c_a, 4)}·a³ = {txt(vc, 4)}·a³",
         "detalhe": "O prisma hexagonal desenhado tem 3 vezes esse volume e 3 vezes os átomos: o FEA é o mesmo."},
        {"titulo": "Fator de empacotamento",
         "formula": (f"FEA = Vs / Vc = (2π/3√3)·(2R_c/a)³/(c/a) = {txt(vs, 4)} / {txt(vc, 4)} = {txt(fea, 4)}"),
         "detalhe": (f"{txt((1 - fea) * 100, 1)} % do volume é vazio. O máximo é π/(3√2) ≈ 0,7405, atingido só no "
                     f"c/a ideal √(8/3) ≈ {txt(c_a_ideal_hc(), 4)}; qualquer outro c/a reduz o FEA. "
                     f"É o FEA do modelo de esferas rígidas, não um empacotamento medido.")},
    ]


def passos_fea(r: Mapping[str, Any]) -> List[Passo]:
    estrutura = r["estrutura"]
    info = ESTRUTURAS[estrutura]
    n = int(info["n"])
    c_a = r.get("c_a")
    fea = float(r["fea"])
    vol_r = volume_em_r(estrutura, c_a)
    esferas_r = n * 4.0 / 3.0 * math.pi
    if estrutura == "HC":
        passos: List[Passo] = _passos_fea_hc(float(c_a if c_a is not None else c_a_ideal_hc()), fea)
    else:
        passos = [
            {"titulo": "Volume ocupado pelas esferas",
             "formula": f"Vs = n·(4/3)πR³ = {n} × 4,189·R³ = {txt(esferas_r, 3)}·R³",
             "detalhe": f"A célula contém {n} átomo(s) inteiro(s), somando as frações de vértices, "
                        f"faces e interior."},
            {"titulo": "Volume da célula",
             "formula": f"Vc = a³ = ({info['relacao'].split('= ')[1]})³ = {txt(vol_r, 3)}·R³",
             "detalhe": "Escrever Vc em função de R faz o raio se cancelar: o FEA depende só da geometria."},
            {"titulo": "Fator de empacotamento",
             "formula": f"FEA = Vs / Vc = {txt(esferas_r, 3)} / {txt(vol_r, 3)} = {txt(fea, 4)}",
             "detalhe": f"{txt((1 - fea) * 100, 1)} % do volume é vazio (sítios intersticiais)."},
        ]
    raio, a_nm, c_nm = r.get("raio_nm"), r.get("a_nm"), r.get("c_nm")
    if r.get("a_fonte") == "medido" and raio is not None and a_nm is not None:
        vc = (3.0 * SQRT3 / 2.0) * a_nm ** 2 * float(c_nm) if estrutura == "HC" else a_nm ** 3
        fea_medido = esferas_r * raio ** 3 / vc
        passos.append({"titulo": "Com a rede medida",
                       "formula": f"FEA = n·(4/3)πR³ / Vc(medido) = {txt(fea_medido, 4)}",
                       "detalhe": "A diferença mostra o limite do modelo de esferas rígidas com o raio tabelado."})
    return passos
