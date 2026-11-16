"""Temperatura: dilatação linear, vibração (Lindemann) e alotropia (recurso da v1.4, RQ-CIE-12).

Referências dos MODELOS (os dados de α, T_f e transições da v1.4 ainda estão em rascunho):
* Dilatação linear: ΔL/L₀ = α·ΔT (Callister & Rethwisch, seção 19.3) com α constante (aproximação).
* Critério de Lindemann (Lindemann, Phys. Z. 11, 609, 1910): fusão quando o deslocamento quadrático
  médio atinge uma fração ~0,1 da distância entre vizinhos; √⟨u²⟩ ∝ √T (regime clássico).

Regressão da rodada R2 (cartão R2-BE-01) sobre o parecer de termodinâmica de 2026-11-13 §2.2 a §2.6.
Os testes marcados com o ID do achado fixam o comportamento NOVO; o antigo está descrito em cada um.
"""

from __future__ import annotations

import math

import pytest

from app.engines.procedencia import (
    DadoNaoValidado,
    PoliticaDados,
    TransicaoAlotropica,
    ValorReferencia,
)
from app.engines.thermodynamics.termico import (
    LINDEMANN,
    ROTULO_TF_NOMINAL,
    T_LIMITE_CLASSICO_C,
    calcular_termico,
)
from app.repositories.materiais_json import repositorio_padrao

REPO = repositorio_padrao()
DEV = PoliticaDados(permitir_nao_validado=True)
PROD = PoliticaDados(permitir_nao_validado=False)
FERRO = {"simbolo": "Fe", "estrutura": "CCC", "a_nm": 0.2866, "d_nn_nm": 0.2482, "densidade": 7.88}
FUSAO_FE = REPO.propriedade("Fe", "temperatura_fusao").valor


def termico(t, politica=DEV, **extra):
    return calcular_termico({**FERRO, "temperatura_c": t, **extra}, REPO, politica)


class RepoFalso:
    """Repositório com α e T_f VALIDADOS e transições em rascunho: isola a política das transições (T-8)."""

    versao_dados = "teste"

    def __init__(self, estado_transicao="rascunho", fonte_transicao=None, transicoes=True):
        self._estado = estado_transicao
        self._fonte = fonte_transicao
        self._tem = transicoes

    def propriedade(self, simbolo, codigo):
        valores = {"coef_dilatacao_linear": 11.8, "temperatura_fusao": 1538.0}
        if codigo not in valores:
            return None
        return ValorReferencia(simbolo=simbolo, codigo=codigo, valor=valores[codigo], unidade="x",
                               estado="validado", fonte="fonte de teste")

    def intersticial(self, simbolo):
        return None

    def buscar_intersticial(self, texto):
        return None

    def transicoes(self, simbolo):
        if not self._tem:
            return []
        return [TransicaoAlotropica(simbolo=simbolo, de_c=912.0, ate_c=1394.0, fase="γ", estrutura="CFC",
                                    estado=self._estado, fonte=self._fonte)]


def termico_falso(t, politica=DEV, repo=None, **extra):
    repo = repo or RepoFalso()
    return calcular_termico({**FERRO, "temperatura_c": t, **extra}, repo, politica)


# --------------------------------------------------------------------------- comportamento preservado
def test_dilatacao_linear_e_densidade():
    alfa = REPO.propriedade("Fe", "coef_dilatacao_linear").valor * 1e-6
    r = termico(520)
    fator = 1 + alfa * (520 - 20)
    assert r["a_nm"] == pytest.approx(0.2866 * fator, rel=1e-12)
    assert r["densidade"] == pytest.approx(7.88 / fator ** 3, rel=1e-12)
    assert r["delta_v_pct"] == pytest.approx((fator ** 3 - 1) * 100, rel=1e-12)
    assert r["indisponiveis"] == {} and r["extrapolacao"] == {}


def test_lindemann_vale_exatamente_a_fracao_na_fusao():
    r = termico(FUSAO_FE)
    assert r["razao_lindemann"] == pytest.approx(LINDEMANN, rel=1e-12)
    assert r["fundido"] is True and r["acima_da_tf_nominal"] is True


def test_amplitude_cresce_com_raiz_de_t_absoluta():
    b = termico(26.85)["razao_lindemann"]     # 300 K
    c = termico(926.85)["razao_lindemann"]    # 1200 K
    assert c / b == pytest.approx(math.sqrt(1200 / 300), rel=1e-9)
    assert termico(-273.15)["razao_lindemann"] == pytest.approx(0.0, abs=1e-12)


def test_mistura_pondera_alfa_e_fusao():
    r = calcular_termico({**FERRO, "temperatura_c": 300, "mistura": [["Fe", 0.7], ["Ni", 0.3]]}, REPO, DEV)
    alfa = (0.7 * REPO.propriedade("Fe", "coef_dilatacao_linear").valor
            + 0.3 * REPO.propriedade("Ni", "coef_dilatacao_linear").valor)
    assert r["alfa_1e6_k"] == pytest.approx(alfa, rel=1e-12)
    assert any("regra das misturas" in n["texto"] for n in r["notas"])


def test_resultado_e_estimativa_de_modelo_com_dados_rastreados():
    r = termico(500)
    assert r["procedencia"]["classe"] == "estimativa_modelo"
    codigos = {u["codigo"] for u in r["procedencia"]["dados_usados"]}
    assert {"coef_dilatacao_linear", "temperatura_fusao"} <= codigos


def test_em_producao_sem_dado_validado_o_calculo_fica_indisponivel():
    with pytest.raises(DadoNaoValidado):
        termico(500, PROD)


# --------------------------------------------------------------------------- T-8 e T-9 (alotropia)
def test_t8_t9_alotropia_entra_na_procedencia_quando_o_dado_e_aceito():
    """Antes: a faixa era lida direto de props.transicoes(), sem política e sem registro na procedência."""
    r = termico(1000)
    usados = {(u["codigo"], u["estado"]) for u in r["procedencia"]["dados_usados"]}
    assert ("transicao_alotropica", "rascunho") in usados
    assert r["alotropia"]["fase"] == "γ" and r["alotropia"]["estrutura"] == "CFC"
    assert r["alotropia"]["pressao"] == "nao_modelada"
    assert "alotropia" not in r["indisponiveis"]
    assert any("γ" in n["texto"] and "CFC" in n["texto"] for n in r["notas"] if n["tipo"] == "alerta")
    assert any("pressão não modelada" in n["texto"] for n in r["notas"])
    assert any("transicao_alotropica de Fe" in a for a in r["procedencia"]["avisos"])


def test_t8_em_producao_a_fase_estavel_nao_e_afirmada_sem_procedencia():
    """CRÍTICO: com α e T_f validados mas a faixa em rascunho, nada de fase estável sai em produção."""
    r = termico_falso(1000, PROD)
    assert r["alotropia"] is None
    assert "não foi validada com fonte" in r["indisponiveis"]["alotropia"]
    assert "rascunho" in r["indisponiveis"]["alotropia"]
    assert not any("fase estável" in n["texto"] for n in r["notas"])
    assert not any("γ" in n["texto"] for n in r["notas"])
    assert all(u["codigo"] != "transicao_alotropica" for u in r["procedencia"]["dados_usados"])


def test_t8_em_producao_a_faixa_validada_com_fonte_e_usada_e_rastreada():
    repo = RepoFalso(estado_transicao="validado", fonte_transicao="fonte conferida")
    r = termico_falso(1000, PROD, repo=repo)
    assert r["alotropia"]["estado"] == "validado" and r["alotropia"]["fonte"] == "fonte conferida"
    assert "fonte conferida" in r["procedencia"]["fontes_dados"]
    assert "[faixa ainda sem validação" not in "".join(n["texto"] for n in r["notas"])


def test_t9_sem_faixa_cadastrada_o_motivo_aparece_em_vez_de_silencio():
    r = termico_falso(1000, DEV, repo=RepoFalso(transicoes=False))
    assert r["alotropia"] is None
    assert "não há faixas de alotropia cadastradas" in r["indisponiveis"]["alotropia"]


def test_t9_temperatura_fora_das_faixas_cadastradas_tem_motivo():
    r = termico_falso(500)       # a única faixa do repositório falso cobre 912 a 1394 °C
    assert r["alotropia"] is None
    assert "nenhuma faixa de alotropia cadastrada" in r["indisponiveis"]["alotropia"]


def test_alotropia_de_liga_nao_e_avaliada_e_diz_por_que():
    r = calcular_termico({**FERRO, "temperatura_c": 1000, "mistura": [["Fe", 0.7], ["Ni", 0.3]]}, REPO, DEV)
    assert r["alotropia"] is None
    assert "não avalia alotropia de liga" in r["indisponiveis"]["alotropia"]


# --------------------------------------------------------------------------- T-1 (domínio acima da T_f)
def test_t1_acima_da_fusao_a_rede_e_a_densidade_ficam_nulas_com_motivo():
    """Antes: a_nm, densidade, delta_a_pct e delta_v_pct eram devolvidos para um líquido."""
    r = termico(FUSAO_FE + 100)
    for campo in ("fator", "a_nm", "delta_a_pct", "delta_v_pct", "densidade"):
        assert r[campo] is None, campo
        assert "não há ordem cristalina" in r["indisponiveis"][campo], campo
    assert r["a_ref_nm"] == 0.2866                     # a referência a 20 °C continua
    assert "não há cristal" in r["extrapolacao"]["razao_lindemann"]
    assert any("líquido" in n["texto"] for n in r["notas"] if n["tipo"] == "alerta")


def test_t1_a_curva_termina_na_fusao_e_comeca_no_limite_classico():
    """Antes: a curva ia de −273,15 °C até T_f + 200 °C."""
    r = termico(20)
    assert r["curva"][0][0] == pytest.approx(T_LIMITE_CLASSICO_C, abs=0.01)
    assert r["curva"][-1][0] == pytest.approx(FUSAO_FE, abs=0.01)
    assert r["curva_dominio"]["de_c"] == pytest.approx(T_LIMITE_CLASSICO_C)
    assert r["curva_dominio"]["ate_c"] == pytest.approx(FUSAO_FE)
    assert max(p[1] for p in r["curva"]) <= LINDEMANN * (1 + 1e-12)
    assert "não há cristal" in r["curva_dominio"]["limite_superior"]


# --------------------------------------------------------------------------- T-6 (T_f nominal da mistura)
def test_t6_mistura_nao_afirma_liquido_e_rotula_a_tf_como_nominal():
    """Antes: com mistura acima da T_f média o texto afirmava 'o material é líquido'."""
    r = calcular_termico({**FERRO, "temperatura_c": 1600, "mistura": [["Fe", 0.7], ["Ni", 0.3]]}, REPO, DEV)
    assert r["acima_da_tf_nominal"] is True
    assert r["fundido"] is False                       # semântica revista: nunca se afirma líquido em mistura
    assert r["tf_natureza"] == "nominal_regra_das_misturas"
    assert r["tf_rotulo"] == ROTULO_TF_NOMINAL
    assert r["mistura_base"] == "atomica"
    textos = " ".join(n["texto"] for n in r["notas"])
    assert "não é solidus nem liquidus" in textos
    assert "Não se afirma que o material está líquido" in textos
    assert "o material é líquido" not in textos
    assert any("fração ATÔMICA" in h for h in r["hipoteses"])


def test_t6_elemento_puro_continua_declarando_a_tf_tabelada():
    r = termico(500)
    assert r["tf_natureza"] == "tabelada_do_elemento" and r["mistura_base"] is None
    assert "não é solidus" not in r["tf_rotulo"]


# --------------------------------------------------------------------------- T-2 (isotropia)
def test_t2_isotropia_e_declarada_sempre_e_alertada_no_hc():
    r = termico(500)
    assert r["dilatacao_isotropica"] is True
    assert any("isotrópica" in h for h in r["hipoteses"])
    assert any("coeficientes por eixo" in h for h in r["hipoteses"])
    hc = calcular_termico({"simbolo": "Mg", "estrutura": "HC", "a_nm": 0.32, "d_nn_nm": 0.32,
                           "densidade": 1.74, "temperatura_c": 300}, REPO, DEV)
    assert any("anisotrópica" in n["texto"] for n in hc["notas"] if n["tipo"] == "alerta")
    assert not any("anisotrópica" in n["texto"] for n in r["notas"])


# --------------------------------------------------------------------------- T-4 e T-11 (Lindemann)
def test_t4_abaixo_de_100_k_o_valor_e_extrapolacao_com_alerta():
    """Antes: u = 0 em 0 K saía como resultado normal, sem aviso (energia de ponto zero ignorada)."""
    r = termico(-250)
    assert "razao_lindemann" in r["extrapolacao"] and "u_nm" in r["extrapolacao"]
    assert "ponto zero" in r["extrapolacao"]["u_nm"]
    assert any("ponto zero" in n["texto"] for n in r["notas"] if n["tipo"] == "alerta")
    assert "razao_lindemann" not in termico(500)["extrapolacao"]


def test_t11_u_e_rotulado_como_deslocamento_quadratico_medio():
    r = termico(500)
    assert r["u_natureza"] == "deslocamento_quadratico_medio_estimado"
    assert "amplitude" in r["u_rotulo"] and "deslocamento quadrático médio" in r["u_rotulo"]
    assert r["lindemann_natureza"] == "limite_inferior_da_faixa_0_10_a_0_15"
    hipoteses = " ".join(r["hipoteses"])
    assert "limite INFERIOR" in hipoteses and "ordem de grandeza" in hipoteses
    assert "critério de FUSÃO" in hipoteses


# --------------------------------------------------------------------------- T-5 e T-7 (temperatura homóloga)
@pytest.mark.parametrize("temperatura", [100.0, 500.0, 1000.0])
def test_t5_t7_notas_de_temperatura_homologa_sao_condicionais_e_sem_fonte(temperatura):
    """Antes: 'Entre 0,3 e 0,5·T_f ocorrem recuperação e recristalização', incondicional e sem fonte."""
    r = termico(temperatura)
    nota = next(n for n in r["notas"] if "T_f" in n["texto"] and "kelvin" in n["texto"])
    assert "sem fonte verificada" in (nota["fonte"] or "")
    assert "ordem de grandeza" in nota["texto"]
    assert any("não têm fonte verificada" in a for a in r["procedencia"]["avisos"])


def test_t5_recristalizacao_exige_deformacao_previa():
    r = termico(500)                                   # 0,3 ≤ T/T_f < 0,5 para o Fe
    assert 0.3 <= r["homologa"] < 0.5
    nota = next(n for n in r["notas"] if "recristalização" in n["texto"])
    assert "PREVIAMENTE DEFORMADO A FRIO" in nota["texto"]
    assert "Sem deformação prévia não há recristalização" in nota["texto"]


# --------------------------------------------------------------------------- hipóteses gerais
def test_pressao_nao_modelada_e_declarada():
    assert any("Pressão não modelada" in h for h in termico(500)["hipoteses"])
