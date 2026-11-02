"""Temperatura: dilatação linear, vibração (Lindemann) e alotropia (recurso da v1.4, RQ-CIE-12).

Referências dos MODELOS (os dados de α, T_f e transições da v1.4 ainda estão em rascunho):
* Dilatação linear: ΔL/L₀ = α·ΔT (Callister & Rethwisch, seção 19.3) com α constante (aproximação).
* Critério de Lindemann (Lindemann, Phys. Z. 11, 609, 1910): fusão quando a amplitude rms de
  vibração atinge uma fração ~0,1 da distância entre vizinhos; amplitude ∝ √T (regime clássico).
"""

from __future__ import annotations

import math

import pytest

from app.engines.procedencia import DadoNaoValidado, PoliticaDados
from app.engines.thermodynamics.termico import LINDEMANN, calcular_termico
from app.repositories.materiais_json import repositorio_padrao

REPO = repositorio_padrao()
DEV = PoliticaDados(permitir_nao_validado=True)
PROD = PoliticaDados(permitir_nao_validado=False)
FERRO = {"simbolo": "Fe", "estrutura": "CCC", "a_nm": 0.2866, "d_nn_nm": 0.2482, "densidade": 7.88}


def termico(t, politica=DEV, **extra):
    return calcular_termico({**FERRO, "temperatura_c": t, **extra}, REPO, politica)


def test_dilatacao_linear_e_densidade():
    alfa = REPO.propriedade("Fe", "coef_dilatacao_linear").valor * 1e-6
    r = termico(520)
    fator = 1 + alfa * (520 - 20)
    assert r["a_nm"] == pytest.approx(0.2866 * fator, rel=1e-12)
    assert r["densidade"] == pytest.approx(7.88 / fator ** 3, rel=1e-12)
    assert r["delta_v_pct"] == pytest.approx((fator ** 3 - 1) * 100, rel=1e-12)


def test_lindemann_vale_exatamente_a_fracao_na_fusao():
    fusao = REPO.propriedade("Fe", "temperatura_fusao").valor
    r = termico(fusao)
    assert r["razao_lindemann"] == pytest.approx(LINDEMANN, rel=1e-12)
    assert r["fundido"] is True


def test_amplitude_cresce_com_raiz_de_t_absoluta():
    a = termico(-273.15)["razao_lindemann"]
    b = termico(26.85)["razao_lindemann"]     # 300 K
    c = termico(926.85)["razao_lindemann"]    # 1200 K
    assert a == pytest.approx(0.0, abs=1e-12)
    assert c / b == pytest.approx(math.sqrt(1200 / 300), rel=1e-9)


def test_alotropia_do_ferro_a_1000_c():
    r = termico(1000)
    alertas = [n for n in r["notas"] if n["tipo"] == "alerta"]
    assert any("γ" in n["texto"] and "CFC" in n["texto"] for n in alertas)


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


def test_curva_tem_limites_de_zero_kelvin_ate_acima_da_fusao():
    r = termico(20)
    fusao = REPO.propriedade("Fe", "temperatura_fusao").valor
    assert r["curva"][0][0] == pytest.approx(-273.15, abs=0.1)
    assert r["curva"][-1][0] == pytest.approx(fusao + 200, abs=0.1)
