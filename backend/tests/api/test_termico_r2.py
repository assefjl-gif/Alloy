"""Contrato da rota térmica depois das correções da rodada R2 (cartão R2-BE-01).

Cada teste cita o achado do parecer de termodinâmica (2026-11-13) que fixa o comportamento.
Os campos antigos continuam presentes (mudança aditiva); os que perderam significado acima da T_f
passam a sair como ``null`` com o motivo em ``indisponiveis``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

TERMICO = "/api/v1/thermodynamics/thermal"

CAMPOS_LEGADOS = ("temperatura_c", "temperatura_k", "fusao_c", "homologa", "alfa_1e6_k", "fator", "a_ref_nm",
                  "a_nm", "delta_a_pct", "densidade", "delta_v_pct", "u_nm", "razao_lindemann",
                  "amplitude_rel", "lindemann", "fundido", "curva", "notas", "procedencia")
CAMPOS_NOVOS = ("acima_da_tf_nominal", "tf_natureza", "tf_rotulo", "mistura_base", "dilatacao_isotropica",
                "u_natureza", "u_rotulo", "lindemann_natureza", "curva_dominio", "alotropia", "hipoteses",
                "indisponiveis", "extrapolacao")


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(Settings(_env_file=None)), raise_server_exceptions=False)


def _resultado(client, corpo):
    resposta = client.post(TERMICO, json=corpo)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["result"]


def test_campos_legados_e_novos_saem_na_resposta(client):
    r = _resultado(client, {"material": "Fe", "temperatura_c": 500})
    for campo in CAMPOS_LEGADOS + CAMPOS_NOVOS:
        assert campo in r, campo
    assert r["procedencia"]["versao_motor"] == "2.0.0"


def test_acima_da_fusao_a_rede_sai_nula_com_motivo(client):
    """T-1: parâmetro de rede e densidade de líquido não têm significado."""
    r = _resultado(client, {"material": "Fe", "temperatura_c": 1700})
    assert r["acima_da_tf_nominal"] is True and r["fundido"] is True
    for campo in ("a_nm", "fator", "delta_a_pct", "delta_v_pct", "densidade"):
        assert r[campo] is None and campo in r["indisponiveis"]
    assert r["curva"][-1][0] == pytest.approx(r["fusao_c"], abs=0.01)


def test_liga_nao_e_declarada_liquida_e_a_tf_e_nominal(client):
    """T-6: a T_f da regra das misturas não é solidus nem liquidus."""
    r = _resultado(client, {"liga": {"base": "Cu", "soluto": "Ni", "x": 30}, "temperatura_c": 1600})
    assert r["acima_da_tf_nominal"] is True
    assert r["fundido"] is False
    assert r["tf_natureza"] == "nominal_regra_das_misturas"
    assert "não é solidus nem liquidus" in r["tf_rotulo"]
    assert r["mistura_base"] == "atomica"
    assert "não avalia alotropia de liga" in r["indisponiveis"]["alotropia"]


def test_alotropia_vem_com_estado_e_entra_na_procedencia(client):
    """T-8 e T-9: em desenvolvimento a faixa é usada, mas com estado, motivo e rastro."""
    r = _resultado(client, {"material": "Fe", "temperatura_c": 1000})
    assert r["alotropia"]["fase"] == "γ" and r["alotropia"]["estado"] == "rascunho"
    assert r["alotropia"]["pressao"] == "nao_modelada"
    assert any(u["codigo"] == "transicao_alotropica" for u in r["procedencia"]["dados_usados"])


def test_curva_fica_no_dominio_do_modelo(client):
    """T-4: abaixo de 100 K o regime clássico não vale; acima da T_f não há cristal."""
    r = _resultado(client, {"material": "Fe", "temperatura_c": 20})
    assert r["curva"][0][0] == pytest.approx(-173.15, abs=0.01)
    assert r["curva_dominio"]["de_c"] == pytest.approx(-173.15, abs=0.01)
    assert "ponto zero" in r["curva_dominio"]["limite_inferior"]


def test_hipoteses_declaradas_na_resposta(client):
    """T-2, T-11 e pressão: hipóteses do modelo vão no resultado, não só no código."""
    r = _resultado(client, {"material": "Fe", "temperatura_c": 500})
    hipoteses = " ".join(r["hipoteses"])
    assert "isotrópica" in hipoteses and "Pressão não modelada" in hipoteses
    assert "ordem de grandeza" in hipoteses
    assert r["dilatacao_isotropica"] is True
    assert r["u_natureza"] == "deslocamento_quadratico_medio_estimado"


# T-3 (produção recusa o cálculo térmico inteiro, porque α e T_f estão em rascunho) já está coberto por
# tests/api/test_api.py::test_producao_recusa_dado_em_rascunho_com_422, que monta o banco migrado com o seed.
# A política aplicada só às faixas de alotropia (T-8), com α e T_f validados, está em
# tests/unit/engines/test_termico.py::test_t8_em_producao_a_fase_estavel_nao_e_afirmada_sem_procedencia.
