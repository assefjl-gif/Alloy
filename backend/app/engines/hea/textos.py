"""Textos fixos e definições de critérios do motor HEA (auditoria R1-HEA-01, seções 2.4 a 2.7).

Nada aqui é dado de material. Os LIMIARES são os que o motor 1.0.0 já usava; as FONTES são as citadas
na auditoria e no contrato R1. NENHUMA foi conferida na fonte nesta rodada: todo critério sai com
``verificada: False`` (decisão D-1.4 do portão G1).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

VEC_CFC = 8.0
VEC_CCC = 6.87
DELTA_SOLUCAO_SOLIDA = 6.6  # %
OMEGA_SOLUCAO_SOLIDA = 1.1
DS_ALTA_R = 1.5   # ΔS_mix ≥ 1,5R: definição por entropia
DS_MEDIA_R = 1.0  # 1R ≤ ΔS_mix < 1,5R: média entropia

FONTE_YANG_ZHANG = "Yang, X.; Zhang, Y. Mater. Chem. Phys. 132, 233–238 (2012)"
FONTE_GUO = "Guo, S. et al. J. Appl. Phys. 109, 103505 (2011)"
FONTE_ENTROPIA = "Yeh (2006); Miracle & Senkov, Acta Mater. 122, 448 (2017)"

#: (codigo, grandeza, operador, limiar, unidade, natureza, fonte)
CRITERIOS: Tuple[Tuple[str, str, str, float, str, str, str], ...] = (
    ("delta_yang_zhang", "delta", "<=", DELTA_SOLUCAO_SOLIDA, "%", "empirico", FONTE_YANG_ZHANG),
    ("omega_yang_zhang", "omega", ">=", OMEGA_SOLUCAO_SOLIDA, "adimensional", "empirico", FONTE_YANG_ZHANG),
    ("vec_cfc_guo", "VEC", ">=", VEC_CFC, "e/átomo", "empirico", FONTE_GUO),
    ("vec_ccc_guo", "VEC", "<", VEC_CCC, "e/átomo", "empirico", FONTE_GUO),
    ("ds_alta_entropia", "dS_R", ">=", DS_ALTA_R, "R", "definicao", FONTE_ENTROPIA),
)


def criterios_definicao() -> List[Dict[str, Any]]:
    """Limiares e fontes para as faixas dos gráficos (bootstrap). ``verificada`` é sempre falso em R1."""
    return [{"codigo": codigo, "grandeza": grandeza, "operador": operador, "limiar": limiar, "unidade": unidade,
             "natureza": natureza, "fonte": fonte, "verificada": False}
            for codigo, grandeza, operador, limiar, unidade, natureza, fonte in CRITERIOS]


MOTIVO_ENERGIA_FORMACAO = (
    "Este sistema não calcula energia de formação: exige cálculo de primeiros princípios (DFT), CALPHAD ou "
    "medida calorimétrica da fase. ΔH_mix e ΔG_mix do modelo não a substituem.")
MOTIVO_DH_SEM_MATRIZ = (
    "ΔH_mix indisponível: a tabela de entalpias de mistura por par (modelo de Miedema) ainda não foi cadastrada "
    "com fonte. Nenhum valor é estimado.")
MOTIVO_OMEGA_SEM_DH = "Ω depende de ΔH_mix, que está indisponível."
MOTIVO_OMEGA_SEM_TM = "Ω depende de T_m, que está indisponível."
MOTIVO_OMEGA_DH_ZERO = (
    "Ω não é definido para ΔH_mix = 0 (divisão por zero). No modelo, a mistura é atérmica e o termo entrópico "
    "domina em qualquer temperatura.")
AVISO_DH_PROXIMO_DE_ZERO = (
    "ΔH_mix próximo de zero: Ω fica muito grande e muito sensível à incerteza das entalpias binárias; "
    "não compare valores de Ω nessa faixa.")
MOTIVO_SEM_MODELO = ("Este sistema não estima {grandeza}: não há modelo com fonte e dados validados para isso. "
                     "Nenhum valor é estimado.")
AVISO_TM_NOMINAL = "T_m indisponível: faixa de temperatura nominal (300 K a 2000 K) na curva de −T·ΔS_mix."
AVISO_VEC_SEM_FONTE = (
    "O domínio de aplicação do critério de VEC usado aqui (ΔS_mix ≥ 1R; só metais de transição dos grupos 4 a 11 "
    "e Al; triagem não desfavorável) é uma delimitação conservadora do especialista, sem fonte bibliográfica, "
    "pendente de parecer.")

AVISOS_FIXOS: Tuple[str, ...] = (
    "ΔS_mix, δ, ΔH_mix, Ω e VEC são critérios empíricos de triagem, ajustados a conjuntos limitados de ligas, em "
    "geral no estado bruto de fusão. Não são prova de estabilidade termodinâmica nem de fase única.",
    "A fase real depende de processamento, temperatura, tempo e taxa de resfriamento. A confirmação exige "
    "experimento (difração de raios X, microscopia) ou cálculo termodinâmico (CALPHAD, DFT), que este sistema "
    "não realiza.",
    "Critérios diferentes podem discordar entre si; quando isso acontece, a discordância é mostrada, não resolvida.",
)

CLASSES: Dict[str, str] = {
    "dS": "analitico", "delta": "estimativa_modelo", "VEC": "estimativa_modelo", "Tm": "estimativa_modelo",
    "dH": "estimativa_modelo", "omega": "estimativa_modelo", "curva_T.menos_TdS": "analitico",
    "curva_T.dG": "estimativa_modelo", "comp_massa_pct": "analitico",
}

_REF_PUROS = "componentes puros, não misturados"
_GERAL = ("Os critérios foram ajustados sobretudo a ligas brutas de fusão; não descrevem cinética, tratamento "
          "térmico nem decomposição em recozimentos longos.")


def definicoes(tem_entalpias: bool) -> List[Dict[str, Any]]:
    """Glossário do módulo (auditoria 2.5 e 2.7.4). ``disponivel``: o sistema calcula a grandeza?"""
    def item(codigo: str, nome: str, simbolo: str, unidade: str, referencia: str, condicoes: str,
             significado: str, nao_e: str, natureza: str, disponivel: bool) -> Dict[str, Any]:
        return {"codigo": codigo, "nome": nome, "simbolo": simbolo, "unidade": unidade, "referencia": referencia,
                "condicoes": condicoes, "significado": significado, "nao_e": nao_e, "natureza": natureza,
                "disponivel": disponivel}

    return [
        item("dS", "Entropia de mistura ideal", "ΔS_mix", "J/(mol·K)", _REF_PUROS,
             "só composição (frações atômicas); solução aleatória ideal, uma única sub-rede",
             "entropia configuracional de uma solução desordenada ideal: −R·Σ xᵢ ln xᵢ",
             "superestima a entropia quando há ordem (fases ordenadas, ordem de curto alcance, várias sub-redes); "
             "não inclui termos vibracional, magnético e eletrônico; não depende de quais são os elementos; o "
             "limite 1,5R é definição, não critério de fase",
             "analítico (exato na hipótese de solução ideal)", True),
        item("delta", "Descompasso de raios atômicos", "δ", "%", "não se aplica",
             "frações atômicas; raios atômicos fixos por elemento",
             "dispersão relativa dos raios em torno do raio médio: 100·√(Σ xᵢ(1 − rᵢ/r̄)²)",
             "o valor depende da tabela de raios (o raio muda com coordenação e vizinhança); só é comparável "
             "entre cálculos com a mesma tabela; δ pequeno não garante solução sólida",
             "estimativa por modelo", True),
        item("VEC", "Concentração de elétrons de valência", "VEC", "e/átomo", "não se aplica",
             "frações atômicas; contagem s + d por elemento (convenção de Guo et al.)",
             "média dos elétrons de valência por átomo: Σ xᵢ·VECᵢ",
             "critério estatístico para ligas que JÁ formam solução sólida; não indica fase hexagonal, "
             "intermetálicos nem fases ordenadas; há exceções relatadas",
             "estimativa por modelo", True),
        item("Tm", "Temperatura de fusão pela regra das misturas", "T_m", "K", "não se aplica",
             "frações atômicas; média linear das temperaturas de fusão dos elementos",
             "escala de temperatura usada em Ω: Σ xᵢ·T_f,ᵢ",
             "não é solidus nem liquidus; pode errar por centenas de kelvins (por exemplo, em sistemas com "
             "eutético); serve só como escala de temperatura em Ω",
             "estimativa por modelo", True),
        item("dH", "Entalpia de mistura do modelo", "ΔH_mix", "kJ/mol", _REF_PUROS,
             "só composição; sem dependência de T nem de P no modelo; solução regular, só interações de pares, "
             "parâmetros de Miedema constantes",
             "sinal e intensidade da afinidade química média entre os componentes (Σ 4·ΔH_ij·xᵢxⱼ): muito "
             "negativa sugere tendência a ordenação ou compostos; positiva, tendência à separação",
             "não é entalpia medida por calorimetria; não é a entalpia de formação de nenhuma fase; não é "
             "CALPHAD; modelo semiempírico, sem termos ternários",
             "estimativa por modelo", tem_entalpias),
        item("omega", "Parâmetro Ω", "Ω", "adimensional", "não se aplica",
             "herda T_m (regra das misturas), ΔS_mix ideal e ΔH_mix do modelo",
             "razão entre o termo entrópico em T_m e o módulo da entalpia de mistura: T_m·ΔS_mix/|ΔH_mix|",
             "diverge quando ΔH_mix tende a zero; o limiar 1,1 é estatístico",
             "estimativa por modelo", tem_entalpias),
        item("menos_TdS", "Termo entrópico ideal", "−T·ΔS_mix", "kJ/mol", _REF_PUROS,
             "composição e T; pressão não modelada (fases condensadas)",
             "quanto a entropia configuracional ideal reduz a energia livre a cada T",
             "não é ΔG; não inclui entropia vibracional, magnética nem eletrônica; ignora ordem de curto alcance",
             "analítico (exato na hipótese de solução ideal)", True),
        item("dG", "Energia livre de Gibbs de mistura do modelo", "ΔG_mix", "kJ/mol", _REF_PUROS,
             "composição e T; parâmetros constantes em T; pressão não modelada (fases condensadas)",
             "balanço, dentro do modelo, entre afinidade química e entropia de uma solução desordenada "
             "hipotética: ΔH_mix − T·ΔS_mix",
             "ΔG_mix < 0 NÃO prova fase única nem estabilidade: a estabilidade exige comparar com a energia de "
             "Gibbs das fases concorrentes (intermetálicos, separação de fases); não é energia de formação; não "
             "é diagrama de fases",
             "estimativa por modelo", tem_entalpias),
        item("energia_formacao", "Energia de formação", "ΔH_f / ΔG_f", "kJ/mol ou eV/átomo",
             "elementos na fase estável de referência",
             "T, P e estrutura da fase",
             "estabilidade de uma fase específica, com estrutura cristalina definida, em relação aos elementos; "
             "base de diagramas de fases",
             "não é ΔH_mix nem ΔG_mix do modelo. " + _GERAL,
             "cálculo de primeiros princípios, CALPHAD ou medida (este sistema não realiza)", False),
    ]
