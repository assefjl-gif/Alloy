"""QA-R2-02: `/crystallography/cells` e `/density` declaram os dados do repositório que usaram.

Contrato R1 §0/§1.2 e princípio 1 do CLAUDE.md: todo dado de material que entra no resultado aparece em
``procedencia.dados_usados`` com estado de validação e fonte, e a fonte entra em ``procedencia.fontes_dados``.
Os payloads são os do relatório ``docs/agent_reports/2026-11-15_qa_R2.md``.

Nenhum valor científico mudou nesta correção: os testes de valor usam como âncora os números que o próprio
QA observou ANTES da mudança (Mg: ``fea`` 0,7364175322689442 e ``densidade`` 1,7518521906200983).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.engines.procedencia import ESTADOS
from app.main import create_app

CELULAS = "/api/v1/crystallography/cells"
DENSIDADE = "/api/v1/crystallography/density"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(Settings(_env_file=None)), raise_server_exceptions=False)


def _resultado(client, rota, payload):
    resposta = client.post(rota, json=payload)
    corpo = resposta.json()
    assert resposta.status_code == 200, corpo
    return corpo["result"]


def _por_codigo(procedencia):
    return {d["codigo"]: d for d in procedencia["dados_usados"]}


def test_qa_r2_02_cells_registra_raio_massa_c_a_e_densidade(client):
    r = _resultado(client, CELULAS, {"nome": "Mg"})
    p = r["procedencia"]
    dados = _por_codigo(p)
    assert set(dados) == {"raio_atomico", "massa_atomica", "razao_c_a", "densidade"}
    assert dados["raio_atomico"]["valor"] == r["raio_nm"]
    assert dados["massa_atomica"]["valor"] == r["peso"]
    assert dados["razao_c_a"]["valor"] == pytest.approx(r["c_a"])
    assert dados["densidade"]["valor"] == r["densidade_exp"]
    for dado in dados.values():
        assert dado["simbolo"] == "Mg"
        assert dado["estado"] in ESTADOS and dado["estado"] != "validado"
        assert dado["fonte"] == "callister"
    assert dados["raio_atomico"]["unidade"] == "nm"
    assert dados["massa_atomica"]["unidade"] == "g/mol"
    assert p["fontes_dados"] == ["callister"]


def test_qa_r2_02_cells_registra_rede_medida_com_a_fonte_da_rede(client):
    """Ti tem a e c medidos com fonte própria (``fonte_rede``): ela precisa aparecer na procedência."""
    r = _resultado(client, CELULAS, {"nome": "Ti"})
    dados = _por_codigo(r["procedencia"])
    assert r["a_fonte"] == "medido"
    assert dados["parametro_rede_a"]["valor"] == r["a_nm"]
    assert dados["parametro_rede_c"]["valor"] == r["c_nm"]
    assert dados["parametro_rede_a"]["fonte"] == "auditoria_cr01"
    assert dados["parametro_rede_c"]["fonte"] == "auditoria_cr01"
    assert dados["raio_atomico"]["fonte"] == "callister"
    assert r["procedencia"]["fontes_dados"] == ["auditoria_cr01", "callister"]


def test_qa_r2_02_density_tem_a_mesma_procedencia_da_celula(client):
    celula = _resultado(client, CELULAS, {"nome": "Mg"})
    densidade = _resultado(client, DENSIDADE, {"nome": "Mg"})
    assert densidade["procedencia"] is not None
    assert densidade["procedencia"]["dados_usados"] == celula["procedencia"]["dados_usados"]
    assert densidade["procedencia"]["fontes_dados"] == ["callister"]
    assert densidade["procedencia"]["motor"] == "crystallography"
    assert densidade["procedencia"]["calculado_em"]
    assert densidade["procedencia"]["avisos"] == celula["procedencia"]["avisos"]


def test_qa_r2_02_dado_editado_pelo_usuario_nao_e_atribuido_ao_repositorio(client):
    r = _resultado(client, CELULAS, {"nome": "Fe", "raio": 0.2})
    dados = _por_codigo(r["procedencia"])
    assert "raio_atomico" not in dados, "o raio foi informado pelo usuário"
    assert "densidade" not in dados, "a densidade experimental é descartada quando há edição"
    assert dados["massa_atomica"]["valor"] == r["peso"]


def test_qa_r2_02_celula_generica_nao_declara_dado_de_repositorio(client):
    r = _resultado(client, CELULAS, {"nome": "CFC", "raio": 0.128, "peso": 63.55})
    assert r["procedencia"]["dados_usados"] == []
    assert r["procedencia"]["fontes_dados"] == []


def test_qa_r2_02_c_a_ideal_nao_e_declarado_como_dado_de_repositorio(client):
    """c/a ideal é do modelo (√(8/3)), não do seed: não pode entrar como dado de material."""
    r = _resultado(client, CELULAS, {"nome": "HC", "raio": 0.16})
    assert r["c_a_natureza"] == "ideal"
    assert r["procedencia"]["dados_usados"] == []


def test_qa_r2_02_c_a_informado_nao_e_declarado_como_dado_de_repositorio(client):
    r = _resultado(client, CELULAS, {"nome": "Mg", "c_a": 1.7})
    dados = _por_codigo(r["procedencia"])
    assert r["c_a_natureza"] == "informado"
    assert "razao_c_a" not in dados


def test_qa_r2_02_nenhum_valor_cientifico_mudou(client):
    """Âncora: números observados pelo QA antes da correção (relatório R2-QA-01, seções 2 e 3.1)."""
    r = _resultado(client, CELULAS, {"nome": "Mg"})
    assert r["fea"] == pytest.approx(0.7364175322689442, rel=0, abs=1e-15)
    assert r["densidade"] == pytest.approx(1.7518521906200983, rel=0, abs=1e-15)
    assert r["a_nm"] == pytest.approx(0.32)
    assert r["c_a"] == pytest.approx(1.624)
    d = _resultado(client, DENSIDADE, {"nome": "Mg"})
    assert d["densidade"] == pytest.approx(1.7518521906200983, rel=0, abs=1e-15)
    assert d["fea"] == pytest.approx(0.7364175322689442, rel=0, abs=1e-15)


# --------------------------------------------------------------------------- política inalterada
def test_qa_r2_02_em_producao_a_politica_de_dados_nao_mudou(tmp_path_factory):
    """R2-BE-02 só acrescenta rastreabilidade: a política de QA-R2-01 (decisão pendente) fica como estava.

    Em produção estrita ``/cells`` continua respondendo 200 para o Mg (dado do seed aguardando validação) —
    agora com ``dados_usados`` preenchido, declarando estado e fonte de cada valor.
    """
    from .banco import motor_de_teste, preparar_banco

    url = f"sqlite:///{tmp_path_factory.mktemp('prod_proc') / 'alloy.db'}"
    preparar_banco(url)
    ajustes = Settings(_env_file=None, env="prod", demo="proibido", rate_limit=False,
                       session_secret="s" * 40, csrf_secret="c" * 40, database_url=url)
    cliente = TestClient(create_app(ajustes, motor_banco=motor_de_teste(url)),
                         base_url="https://testserver", raise_server_exceptions=False)
    r = _resultado(cliente, CELULAS, {"nome": "Mg"})
    dados = _por_codigo(r["procedencia"])
    assert set(dados) == {"raio_atomico", "massa_atomica", "razao_c_a", "densidade"}
    assert all(d["estado"] != "validado" for d in dados.values())
    assert r["procedencia"]["fontes_dados"] == ["callister"]
    assert r["densidade"] == pytest.approx(1.7518521906200983, rel=0, abs=1e-15)
