"""Efeito da temperatura na rede (portado da v1.4 — RQ-CIE-12).

Modelos (todos aproximações declaradas → classe ``estimativa_modelo``):
* Dilatação linear com α constante: a(T) = a(20 °C)·[1 + α·(T − 20)] (Callister, seção 19.3).
  O α real cai a baixas temperaturas; abaixo da ambiente o valor é extrapolação. A dilatação é
  tratada como ISOTRÓPICA — hipótese declarada em ``hipoteses`` (achado T-2).
* Vibração pelo critério de Lindemann (Lindemann, Phys. Z. 11, 609, 1910): u/d = f·√(T/T_f), com
  f = 0,10 (valores da literatura ficam em ~0,1–0,15; usamos o limite inferior). ``u`` é o
  DESLOCAMENTO QUADRÁTICO MÉDIO estimado, não uma amplitude de oscilação (T-4, T-11).
* Alotropia: faixas de estabilidade cadastradas por elemento, submetidas à ``PoliticaDados`` e
  registradas na procedência (T-8, T-9): sem dado validado, a afirmação de fase NÃO é feita.

Correções da rodada R2 (cartão R2-BE-01), conforme o parecer de termodinâmica de 2026-11-13 (§2.2 a §2.6):
T-1 (domínio acima da T_f), T-2 (isotropia declarada), T-4/T-11 (limite clássico e nome da grandeza),
T-5/T-7 (textos condicionais e sem fonte verificada), T-6 (T_f nominal da mistura), T-8/T-9 (alotropia).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Tuple

from ..crystallography.entradas import numero_opcional
from ..crystallography.erros import EntradaInvalida
from ..crystallography.formatacao import txt
from ..procedencia import (
    ColetorDados,
    PoliticaDados,
    RepositorioPropriedades,
    TransicaoAlotropica,
    ValorReferencia,
    bloco_procedencia,
)

VERSAO_MOTOR = "2.0.0"
LINDEMANN = 0.10
T_REFERENCIA_C = 20.0
PONTOS_CURVA = 60
#: Abaixo desta temperatura o modelo harmônico clássico (⟨u²⟩ ∝ T) não vale e α → 0 (3ª lei):
#: 100 K é o corte adotado na falta de θ_D no repositório (parecer §2.3, item 1).
T_LIMITE_CLASSICO_K = 100.0
T_LIMITE_CLASSICO_C = T_LIMITE_CLASSICO_K - 273.15

CODIGO_TRANSICAO = "transicao_alotropica"

FONTES_MODELO = (
    "Callister & Rethwisch, Ciência e Engenharia de Materiais, seção 19.3 — dilatação térmica",
    "Lindemann, F. A. Phys. Z. 11, 609–612 (1910) — critério de fusão",
)

SEM_FONTE_HOMOLOGA = ("sem fonte verificada neste repositório (faixas de temperatura homóloga: "
                      "consulta C-07-D ao auditor bibliográfico)")

ROTULO_TF_ELEMENTO = "T_f tabelada do elemento"
ROTULO_TF_NOMINAL = "T_f nominal (regra das misturas) — não é solidus nem liquidus"

AVISO_HOMOLOGA_SEM_FONTE = (
    "As faixas de temperatura homóloga (0,3 e 0,5·T_f) são regras de ordem de grandeza da metalurgia física e "
    "não têm fonte verificada neste repositório; recuperação, recristalização e fluência são fenômenos "
    "cinéticos (dependem de tempo, deformação prévia, liga e tamanho de grão).")
AVISO_LINDEMANN = (
    "u é o deslocamento quadrático médio estimado por inversão do critério de Lindemann (um critério de FUSÃO "
    "usado aqui para estimar u): estimativa de ordem de grandeza, não medida. f = 0,10 é o limite INFERIOR da "
    "faixa de 0,10 a 0,15 da literatura, o que enviesa u sistematicamente para baixo; a convenção de f "
    "(√⟨u²⟩ 1D ou 3D) não foi verificada na fonte (consulta C-07-A).")
AVISO_ISOTROPIA = (
    "A dilatação é tratada como isotrópica: um único α para todas as direções. Em estruturas não cúbicas (HC, "
    "por exemplo Mg, Ti, Zn e Co) a dilatação real é anisotrópica (α_a ≠ α_c) e a célula exibida não se deforma "
    "como no cristal real; o α tabelado é, na melhor hipótese, a média policristalina. Não há coeficientes por "
    "eixo neste repositório.")
AVISO_PRESSAO = "Pressão não modelada (fase condensada); os dados de referência são de ~1 bar."
AVISO_MISTURA_BASE = (
    "Na mistura, α e T_f são interpolados linearmente em fração ATÔMICA (α = Σ xᵢαᵢ, T_f = Σ xᵢT_f,ᵢ): "
    "interpolação empírica, convenção deste software, sem lei de base. Para liga intersticial o motor usa "
    "apenas o solvente.")

MOTIVO_ACIMA_TF = ("acima da T_f do modelo não há ordem cristalina de longo alcance: parâmetro de rede, "
                   "densidade cristalina e dilatação da célula não têm significado físico")
MOTIVO_DENSIDADE_AUSENTE = "a densidade não veio do cálculo da célula (sem massa atômica ou sem volume)"


def _mistura(entrada: Mapping[str, Any]) -> List[Tuple[str, float]]:
    bruto = entrada.get("mistura")
    if not bruto:
        return [(str(entrada.get("simbolo") or ""), 1.0)]
    itens = [(str(s), float(f)) for s, f in bruto]
    total = sum(f for _, f in itens)
    if not itens or abs(total - 1.0) > 1e-6 or any(f < 0 for _, f in itens):
        raise EntradaInvalida("As frações da mistura devem ser positivas e somar 1.")
    return itens


def _faixa_alotropica(props: RepositorioPropriedades, simbolo: str,
                      temperatura: float) -> Tuple[Optional[TransicaoAlotropica], Optional[str]]:
    """Escolhe a faixa cadastrada que cobre ``temperatura``; devolve (faixa, motivo de indisponibilidade)."""
    faixas = list(props.transicoes(simbolo))
    if not faixas:
        return None, f"não há faixas de alotropia cadastradas para {simbolo}"
    for faixa in faixas:
        if faixa.de_c <= temperatura < faixa.ate_c:
            return faixa, None
    return None, (f"nenhuma faixa de alotropia cadastrada para {simbolo} cobre {txt(temperatura, 1)} °C")


def _alotropia(props: RepositorioPropriedades, politica: PoliticaDados, coletor: ColetorDados,
               itens: List[Tuple[str, float]], temperatura: float, acima_da_tf: bool,
               estrutura: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], List[Dict[str, Any]]]:
    """Faixa de alotropia sob a política de dados (T-8) e registrada na procedência (T-9).

    Em produção (dado não validado) nenhuma afirmação de fase é feita: devolve (None, motivo, []).
    """
    if len(itens) > 1:
        return None, ("o motor não avalia alotropia de liga: as faixas cadastradas são de elementos puros e o "
                      "equilíbrio de fases da liga exigiria diagrama de fases, que o motor não tem"), []
    if acima_da_tf:
        return None, ("acima da T_f do modelo não há fase cristalina de equilíbrio a declarar"), []
    simbolo = itens[0][0]
    faixa, motivo = _faixa_alotropica(props, simbolo, temperatura)
    if faixa is None:
        return None, motivo, []
    validado = faixa.estado == "validado" and faixa.fonte is not None
    if not validado and not politica.permitir_nao_validado:
        return None, (f"a faixa de alotropia de {simbolo} ainda não foi validada com fonte "
                      f"(estado: {faixa.estado}): a fase estável não é afirmada neste ambiente"), []
    coletor.registrar(ValorReferencia(simbolo=simbolo, codigo=CODIGO_TRANSICAO, valor=faixa.de_c,
                                      unidade="°C (início da faixa de estabilidade)", estado=faixa.estado,
                                      fonte=faixa.fonte))
    bloco = {"simbolo": faixa.simbolo, "fase": faixa.fase, "estrutura": faixa.estrutura,
             "de_c": faixa.de_c, "ate_c": faixa.ate_c, "estado": faixa.estado, "fonte": faixa.fonte,
             "pressao": "nao_modelada"}
    texto = (f"Entre {txt(faixa.de_c, 0)} e {txt(faixa.ate_c, 0)} °C, à pressão ambiente (pressão não "
             f"modelada), a fase estável cadastrada é {faixa.simbolo}-{faixa.fase} ({faixa.estrutura})")
    if not validado:
        texto += " [faixa ainda sem validação com fonte]"
    if faixa.estrutura != estrutura:
        notas = [{"tipo": "alerta", "texto": texto + f". A célula exibida ({estrutura}) não é a de equilíbrio "
                                                     "nessa temperatura.", "fonte": faixa.fonte}]
    else:
        notas = [{"tipo": "info", "texto": texto + ".", "fonte": faixa.fonte}]
    return bloco, None, notas


def _curva_lindemann(tf_k: float, fusao: float) -> Tuple[List[List[float]], Dict[str, Any], Optional[str]]:
    """Curva u/d × T limitada ao domínio do modelo: de 100 K (limite clássico) até a T_f do modelo (T-1, T-4)."""
    inicio, fim = T_LIMITE_CLASSICO_C, fusao
    dominio = {
        "de_c": inicio, "ate_c": fim,
        "limite_inferior": (f"abaixo de {txt(T_LIMITE_CLASSICO_K, 0)} K o modelo harmônico clássico "
                            "(⟨u²⟩ ∝ T) não vale e o movimento de ponto zero, não modelado, domina: "
                            "u = 0 em 0 K é fisicamente errado"),
        "limite_superior": ("acima da T_f do modelo não há cristal: o critério de Lindemann não se aplica"),
    }
    if fim <= inicio:
        return [], dominio, ("a T_f do modelo está abaixo do limite inferior de validade "
                             f"({txt(T_LIMITE_CLASSICO_K, 0)} K): não há domínio em que a curva valha")
    curva = [[round(inicio + (fim - inicio) * i / PONTOS_CURVA, 2),
              LINDEMANN * math.sqrt(max(inicio + (fim - inicio) * i / PONTOS_CURVA + 273.15, 0.0) / tf_k)]
             for i in range(PONTOS_CURVA + 1)]
    return curva, dominio, None


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

    mistura = len(itens) > 1
    t_k = temperatura + 273.15
    tf_k = fusao + 273.15
    fator = 1.0 + alfa * 1e-6 * (temperatura - T_REFERENCIA_C)
    razao = LINDEMANN * math.sqrt(max(t_k, 0.0) / tf_k)
    homologa = t_k / tf_k
    # T-6: com mistura, T_f é uma média ponderada dos puros — não é solidus nem liquidus; o estado líquido
    # NÃO é afirmado. ``fundido`` só é verdadeiro quando a T_f é a do elemento (semântica revista em R2-BE-01).
    acima_da_tf = temperatura >= fusao
    tf_natureza = "nominal_regra_das_misturas" if mistura else "tabelada_do_elemento"
    tf_rotulo = ROTULO_TF_NOMINAL if mistura else ROTULO_TF_ELEMENTO
    fundido = acima_da_tf and not mistura

    curva, curva_dominio, curva_motivo = _curva_lindemann(tf_k, fusao)
    estrutura = str(entrada.get("estrutura") or "")

    indisponiveis: Dict[str, str] = {}
    extrapolacao: Dict[str, str] = {}
    notas: List[Dict[str, Any]] = []

    if acima_da_tf:
        if mistura:
            notas.append({"tipo": "alerta", "fonte": None, "texto":
                          f"A temperatura está acima da T_f calculada pela regra das misturas ({ROTULO_TF_NOMINAL}): "
                          "ligas fundem num intervalo solidus–liquidus, que o motor não calcula (exigiria diagrama "
                          "de fases). Não se afirma que o material está líquido; apenas que o modelo de rede "
                          "cristalina deixou de ser aplicável."})
        else:
            notas.append({"tipo": "alerta", "fonte": None, "texto":
                          "Acima da temperatura de fusão a ordem cristalina de longo alcance desaparece: o "
                          "material é líquido. Parâmetro de rede, densidade cristalina e dilatação da célula "
                          "não são calculados nessa faixa."})
    elif homologa >= 0.5:
        notas.append({"tipo": "info", "fonte": SEM_FONTE_HOMOLOGA, "texto":
                      "Acima de ~0,5·T_f (em kelvin) a difusão é intensa: é a faixa típica de trabalho a quente e "
                      "de fluência e, em metal previamente deformado a frio, a recristalização é rápida. Faixa de "
                      "ordem de grandeza: depende de tempo, deformação prévia, liga e tamanho de grão."})
    elif homologa >= 0.3:
        notas.append({"tipo": "info", "fonte": SEM_FONTE_HOMOLOGA, "texto":
                      "Entre 0,3 e 0,5·T_f (em kelvin), em metal PREVIAMENTE DEFORMADO A FRIO, ocorrem "
                      "recuperação e recristalização (faixa típica de recozimento). Sem deformação prévia não há "
                      "recristalização; é fenômeno cinético, e a temperatura depende de tempo, grau de "
                      "deformação, solutos, pureza e tamanho de grão. Faixa de ordem de grandeza."})
    else:
        notas.append({"tipo": "info", "fonte": SEM_FONTE_HOMOLOGA, "texto":
                      "Abaixo de ~0,3·T_f (em kelvin) a difusão é lenta: a deformação plástica, quando aplicada, "
                      "encrua o metal (trabalho a frio). Faixa de ordem de grandeza."})

    if temperatura < T_LIMITE_CLASSICO_C:
        extrapolacao["razao_lindemann"] = curva_dominio["limite_inferior"]
        extrapolacao["u_nm"] = curva_dominio["limite_inferior"]
        notas.append({"tipo": "alerta", "fonte": None, "texto":
                      f"Abaixo de {txt(T_LIMITE_CLASSICO_K, 0)} K (≈ {txt(T_LIMITE_CLASSICO_C, 1)} °C) os dois "
                      "modelos saem do domínio: α → 0 pela terceira lei (a dilatação linear com α constante "
                      "superestima a contração) e o regime clássico ⟨u²⟩ ∝ T não vale, porque o movimento de "
                      "ponto zero, não modelado, domina. Os valores desta faixa são extrapolação."})
    elif temperatura < T_REFERENCIA_C:
        notas.append({"tipo": "alerta", "fonte": None, "texto":
                      "Abaixo da temperatura ambiente o α real diminui; a dilatação linear aqui é extrapolação "
                      "(α tabelado é um valor médio de engenharia, tipicamente de 20 a 100 °C)."})

    if mistura:
        notas.append({"tipo": "info", "fonte": None, "texto":
                      f"Na liga, α e T_f vêm da regra das misturas em fração atômica: {ROTULO_TF_NOMINAL}. "
                      "O solidus real vem do diagrama de fases, que o motor não tem; toda a interpretação "
                      "térmica da liga (temperatura homóloga, faixas de 0,3 e 0,5·T_f, curva de Lindemann) "
                      "herda essa incerteza."})

    bloco_alotropia, motivo_alotropia, notas_alotropia = _alotropia(
        props, politica, coletor, itens, temperatura, acima_da_tf, estrutura)
    notas.extend(notas_alotropia)
    if motivo_alotropia:
        indisponiveis["alotropia"] = motivo_alotropia
    if curva_motivo:
        indisponiveis["curva"] = curva_motivo

    # T-2: a hipótese de isotropia vale sempre (está em ``hipoteses``); em estrutura não cúbica é alerta.
    if estrutura == "HC":
        notas.append({"tipo": "alerta", "fonte": None, "texto":
                      "Estrutura hexagonal compacta: a dilatação real é anisotrópica (α_a ≠ α_c), e o motor "
                      "aplica um único α isotrópico (média policristalina). A deformação da célula exibida "
                      "não corresponde à do cristal real."})

    # T-1: acima da T_f do modelo os campos da dilatação não têm significado → null com motivo.
    if acima_da_tf:
        for campo in ("fator", "a_nm", "delta_a_pct", "delta_v_pct", "densidade"):
            indisponiveis[campo] = MOTIVO_ACIMA_TF
        fator_saida: Optional[float] = None
        a_saida: Optional[float] = None
        delta_a: Optional[float] = None
        delta_v: Optional[float] = None
        densidade_saida: Optional[float] = None
        extrapolacao["razao_lindemann"] = ("acima da T_f do modelo não há cristal: o critério de Lindemann não "
                                           "se aplica e o valor é extrapolação do modelo")
        extrapolacao["u_nm"] = extrapolacao["razao_lindemann"]
    else:
        fator_saida = fator
        a_saida = a_nm * fator
        delta_a = (fator - 1.0) * 100.0
        delta_v = (fator ** 3 - 1.0) * 100.0
        densidade_saida = densidade / fator ** 3 if densidade else None
        if densidade is None:
            indisponiveis["densidade"] = MOTIVO_DENSIDADE_AUSENTE

    hipoteses = [AVISO_ISOTROPIA, AVISO_LINDEMANN, AVISO_PRESSAO]
    if mistura:
        hipoteses.append(AVISO_MISTURA_BASE)

    parametros = {"itens": itens, "estrutura": estrutura, "a_nm": a_nm, "d_nn_nm": d_nn,
                  "densidade": densidade, "temperatura_c": temperatura}
    return {
        "temperatura_c": temperatura, "temperatura_k": t_k, "fusao_c": fusao, "homologa": homologa,
        "alfa_1e6_k": alfa, "fator": fator_saida,
        "a_ref_nm": a_nm, "a_nm": a_saida, "delta_a_pct": delta_a,
        "densidade": densidade_saida,
        "delta_v_pct": delta_v,
        "u_nm": razao * d_nn, "razao_lindemann": razao, "amplitude_rel": razao * d_nn / a_nm,
        "lindemann": LINDEMANN, "fundido": fundido, "curva": curva, "notas": notas,
        # Campos aditivos da rodada R2 (cartão R2-BE-01)
        "acima_da_tf_nominal": acima_da_tf,
        "tf_natureza": tf_natureza, "tf_rotulo": tf_rotulo,
        "mistura_base": "atomica" if mistura else None,
        "dilatacao_isotropica": True,
        "u_natureza": "deslocamento_quadratico_medio_estimado",
        "u_rotulo": "deslocamento quadrático médio estimado √⟨u²⟩ (não é amplitude de oscilação)",
        "lindemann_natureza": "limite_inferior_da_faixa_0_10_a_0_15",
        "curva_dominio": curva_dominio,
        "alotropia": bloco_alotropia,
        "hipoteses": hipoteses,
        "indisponiveis": indisponiveis,
        "extrapolacao": extrapolacao,
        "procedencia": bloco_procedencia(classe="estimativa_modelo", motor="thermodynamics",
                                         versao_motor=VERSAO_MOTOR, versao_dados=props.versao_dados,
                                         parametros=parametros, coletor=coletor, fontes_modelo=FONTES_MODELO,
                                         avisos=(AVISO_HOMOLOGA_SEM_FONTE,)),
    }
