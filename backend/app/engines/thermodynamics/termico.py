"""Efeito da temperatura na rede (portado da v1.4 — RQ-CIE-12).

Modelos (todos aproximações declaradas → classe ``estimativa_modelo``):
* Dilatação linear com α constante: a(T) = a(20 °C)·[1 + α·(T − 20)] (Callister, seção 19.3).
  O α real cai a baixas temperaturas; abaixo da ambiente o valor é extrapolação.
* Vibração pelo critério de Lindemann (Lindemann, Phys. Z. 11, 609, 1910): u/d = f·√(T/T_f), com
  f = 0,10 (valores da literatura ficam em ~0,1–0,15; usamos o limite inferior).
* Alotropia: faixas de estabilidade cadastradas por elemento.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Tuple

from ..crystallography.entradas import numero_opcional
from ..crystallography.erros import EntradaInvalida
from ..crystallography.formatacao import txt
from ..procedencia import ColetorDados, PoliticaDados, RepositorioPropriedades, bloco_procedencia

VERSAO_MOTOR = "1.0.0"
LINDEMANN = 0.10
T_REFERENCIA_C = 20.0
PONTOS_CURVA = 60
FONTES_MODELO = (
    "Callister & Rethwisch, Ciência e Engenharia de Materiais, seção 19.3 — dilatação térmica",
    "Lindemann, F. A. Phys. Z. 11, 609–612 (1910) — critério de fusão",
)


def _mistura(entrada: Mapping[str, Any]) -> List[Tuple[str, float]]:
    bruto = entrada.get("mistura")
    if not bruto:
        return [(str(entrada.get("simbolo") or ""), 1.0)]
    itens = [(str(s), float(f)) for s, f in bruto]
    total = sum(f for _, f in itens)
    if not itens or abs(total - 1.0) > 1e-6 or any(f < 0 for _, f in itens):
        raise EntradaInvalida("As frações da mistura devem ser positivas e somar 1.")
    return itens


def calcular_termico(entrada: Mapping[str, Any], props: RepositorioPropriedades,
                     politica: PoliticaDados) -> Dict[str, Any]:
    """``entrada``: simbolo (ou mistura [[símbolo, fração]]), estrutura, a_nm, d_nn_nm, densidade, temperatura_c."""
    coletor = ColetorDados(politica)
    itens = _mistura(entrada)
    a_nm = numero_opcional(entrada, "a_nm", (0.05, 2.0), "parâmetro de rede (nm)")
    d_nn = numero_opcional(entrada, "d_nn_nm", (0.02, 1.5), "distância entre vizinhos (nm)")
    densidade = numero_opcional(entrada, "densidade", (0.1, 30.0), "densidade (g/cm³)")
    temperatura = numero_opcional(entrada, "temperatura_c", (-273.15, 5000.0), "temperatura (°C)")
    if a_nm is None or d_nn is None:
        raise EntradaInvalida("Informe a_nm e d_nn_nm (vêm do cálculo da célula).")
    temperatura = T_REFERENCIA_C if temperatura is None else temperatura

    alfa = sum(f * coletor.exigir(props, s, "coef_dilatacao_linear", "coeficiente de dilatação linear")
               for s, f in itens)
    fusao = sum(f * coletor.exigir(props, s, "temperatura_fusao", "temperatura de fusão") for s, f in itens)

    t_k = temperatura + 273.15
    tf_k = fusao + 273.15
    fator = 1.0 + alfa * 1e-6 * (temperatura - T_REFERENCIA_C)
    razao = LINDEMANN * math.sqrt(max(t_k, 0.0) / tf_k)
    homologa = t_k / tf_k
    fundido = temperatura >= fusao

    inicio, fim = -273.15, fusao + 200.0
    curva = [[round(inicio + (fim - inicio) * i / PONTOS_CURVA, 2),
              LINDEMANN * math.sqrt(max(inicio + (fim - inicio) * i / PONTOS_CURVA + 273.15, 0.0) / tf_k)]
             for i in range(PONTOS_CURVA + 1)]

    notas: List[Dict[str, str]] = []
    if fundido:
        notas.append({"tipo": "alerta", "texto": "Acima da temperatura de fusão a ordem cristalina de longo "
                                                 "alcance desaparece: o material é líquido."})
    elif homologa >= 0.5:
        notas.append({"tipo": "info", "texto": "Acima de ~0,5·T_f (em kelvin) a difusão é intensa: trabalho a "
                                               "quente, fluência e recristalização rápida."})
    elif homologa >= 0.3:
        notas.append({"tipo": "info", "texto": "Entre 0,3 e 0,5·T_f ocorrem recuperação e recristalização "
                                               "(faixa típica de recozimento)."})
    else:
        notas.append({"tipo": "info", "texto": "Abaixo de ~0,3·T_f a difusão é lenta: a deformação plástica "
                                               "encrua o metal (trabalho a frio)."})
    if temperatura < T_REFERENCIA_C:
        notas.append({"tipo": "info", "texto": "Abaixo da temperatura ambiente o α real diminui; a dilatação "
                                               "linear aqui é extrapolação."})
    if len(itens) > 1:
        notas.append({"tipo": "info", "texto": "Na liga, α e T_f são estimados pela regra das misturas; o solidus "
                                               "real vem do diagrama de fases."})
    estrutura = str(entrada.get("estrutura") or "")
    if len(itens) == 1 and not fundido:
        for faixa in props.transicoes(itens[0][0]):
            if faixa.de_c <= temperatura < faixa.ate_c:
                texto = (f"Entre {txt(faixa.de_c, 0)} e {txt(faixa.ate_c, 0)} °C a fase estável é "
                         f"{faixa.simbolo}-{faixa.fase} ({faixa.estrutura})")
                if faixa.estado != "validado":
                    texto += " [faixa ainda sem validação]"
                if faixa.estrutura != estrutura:
                    notas.append({"tipo": "alerta", "texto": texto + f". A célula exibida ({estrutura}) não é a "
                                                                    "de equilíbrio nessa temperatura."})
                else:
                    notas.append({"tipo": "info", "texto": texto + "."})

    parametros = {"itens": itens, "estrutura": estrutura, "a_nm": a_nm, "d_nn_nm": d_nn,
                  "densidade": densidade, "temperatura_c": temperatura}
    return {
        "temperatura_c": temperatura, "temperatura_k": t_k, "fusao_c": fusao, "homologa": homologa,
        "alfa_1e6_k": alfa, "fator": fator,
        "a_ref_nm": a_nm, "a_nm": a_nm * fator, "delta_a_pct": (fator - 1.0) * 100.0,
        "densidade": densidade / fator ** 3 if densidade else None,
        "delta_v_pct": (fator ** 3 - 1.0) * 100.0,
        "u_nm": razao * d_nn, "razao_lindemann": razao, "amplitude_rel": razao * d_nn / a_nm,
        "lindemann": LINDEMANN, "fundido": fundido, "curva": curva, "notas": notas,
        "procedencia": bloco_procedencia(classe="estimativa_modelo", motor="thermodynamics",
                                         versao_motor=VERSAO_MOTOR, versao_dados=props.versao_dados,
                                         parametros=parametros, coletor=coletor, fontes_modelo=FONTES_MODELO),
    }
