"""Testes dos exportadores CIF/XYZ (achados EX-01 a EX-07).

Inclui um leitor de CIF independente (expande as operações de simetria e recalcula
a densidade) e, se o ``gemmi`` estiver instalado, validação com ele.
"""

from __future__ import annotations

import math
import re
from fractions import Fraction

import pytest

from crystalab import __version__
from crystalab.core import calcular_estrutura, gerar_cif, gerar_xyz, operacoes_simetria
from crystalab.core.constantes import N_AVOGADRO


def _parse_op(op: str):
    """'-x+y,y,-z+1/2' → (matriz 3×3 de inteiros, translação em frações)."""
    linhas, trans = [], []
    for parte in op.split(","):
        coef = {"x": 0, "y": 0, "z": 0}
        t = Fraction(0)
        for sinal, termo in re.findall(r"([+-]?)([xyz]|\d+/\d+|\d+)", parte):
            s = -1 if sinal == "-" else 1
            if termo in coef:
                coef[termo] += s
            else:
                t += s * Fraction(termo)
        linhas.append([coef["x"], coef["y"], coef["z"]])
        trans.append(t % 1)
    return linhas, trans


def _aplicar(op, p):
    m, t = op
    return tuple((sum(m[i][j] * p[j] for j in range(3)) + t[i]) % 1 for i in range(3))


def _expandir(ops, sitio):
    sitio = tuple(Fraction(v).limit_denominator(12) for v in sitio)
    return {_aplicar(op, sitio) for op in ops}


def _ler_cif(texto):
    num = lambda chave: float(re.search(rf"^{chave}\s+([\d.]+)", texto, re.M).group(1))  # noqa: E731
    bloco_ops = texto.split("_symmetry_equiv_pos_as_xyz\n")[1].split("\n\n")[0].strip().splitlines()
    linha_atomo = texto.strip().splitlines()[-1].split()
    return {
        "a": num("_cell_length_a"), "c": num("_cell_length_c"), "gamma": num("_cell_angle_gamma"),
        "z": int(num("_cell_formula_units_Z")), "volume": num("_cell_volume"),
        "peso": num("_chemical_formula_weight"),
        "ops": [_parse_op(o) for o in bloco_ops],
        "sitio": [float(v) for v in linha_atomo[3:6]],
        "hm": re.search(r"_symmetry_space_group_name_H-M\s+'([^']+)'", texto).group(1),
    }


@pytest.mark.parametrize("estrutura,ordem", [("CS", 48), ("CCC", 96), ("CFC", 192), ("HC", 24)])
def test_operacoes_formam_grupo(estrutura, ordem):
    ops = [_parse_op(o) for o in operacoes_simetria(estrutura)]
    assert len(ops) == ordem
    chave = lambda op: (tuple(map(tuple, op[0])), tuple(op[1]))  # noqa: E731
    conjunto = {chave(op) for op in ops}
    assert len(conjunto) == ordem
    for a in ops:
        for b in ops:  # composição a∘b deve pertencer ao grupo
            m = [[sum(a[0][i][k] * b[0][k][j] for k in range(3)) for j in range(3)] for i in range(3)]
            t = [(sum(a[0][i][k] * b[1][k] for k in range(3)) + a[1][i]) % 1 for i in range(3)]
            assert (tuple(map(tuple, m)), tuple(t)) in conjunto
    # Rotações preservam a métrica da rede.
    g = [[1, -0.5, 0], [-0.5, 1, 0], [0, 0, 2.6]] if estrutura == "HC" else [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for m, _ in ops:
        gt = [[sum(m[k][i] * g[k][q] * m[q][j] for k in range(3) for q in range(3)) for j in range(3)]
              for i in range(3)]
        assert [v for linha in gt for v in linha] == pytest.approx([v for linha in g for v in linha])


@pytest.mark.parametrize("nome,hm,z", [("Fe", "I m -3 m", 2), ("Cu", "F m -3 m", 4), ("Po", "P m -3 m", 1),
                                       ("Mg", "P 63/m m c", 2), ("Ti", "P 63/m m c", 2)])
def test_cif_reproduz_densidade_do_motor(nome, hm, z):
    texto = gerar_cif({"nome": nome})["content"]
    cif = _ler_cif(texto)
    motor = calcular_estrutura({"nome": nome})
    assert cif["hm"] == hm and cif["z"] == z
    assert cif["a"] == pytest.approx(motor["a_nm"] * 10, abs=1e-5)  # EX-01: Å
    sitios = _expandir(cif["ops"], cif["sitio"])
    assert len(sitios) == z  # EX-03: sem réplicas
    assert all(0 <= float(v) < 1 for s in sitios for v in s)  # EX-02
    if cif["gamma"] == 120:
        volume = math.sqrt(3) / 2 * cif["a"] ** 2 * cif["c"]
    else:
        volume = cif["a"] ** 3
    assert volume == pytest.approx(cif["volume"], rel=1e-4)
    rho = len(sitios) * cif["peso"] / (volume * 1e-24 * N_AVOGADRO)
    assert rho == pytest.approx(motor["densidade"], rel=1e-3)  # critério de aceite: ±0,1 %


def test_cif_mg_sitio_2c_e_versao():
    texto = gerar_cif({"nome": "Mg"})["content"]
    assert "Mg1 Mg 2c 0.333333 0.666667 0.250000" in texto
    assert f"CrystaLab {__version__}" in texto  # EX-07
    assert texto.isascii()


def test_cif_generica_usa_pseudo_atomo():
    texto = gerar_cif({"nome": "CFC", "raio": 0.128, "peso": 63.55})["content"]
    assert "\nX1 X 4a " in texto and "XCFC" not in texto  # EX-05


def test_xyz_base_em_angstrom():
    for nome, n in (("Fe", 2), ("Cu", 4), ("Mg", 2)):
        linhas = gerar_xyz({"nome": nome})["content"].splitlines()
        assert int(linhas[0]) == n == len(linhas) - 2
        assert linhas[1].startswith('Lattice="')
    mg = gerar_xyz({"nome": "Mg"})["content"].splitlines()
    x, y, z = map(float, mg[3].split()[1:])
    assert (x, y, z) == pytest.approx((1.6, 0.92376, 2.5984), abs=1e-4)


def test_gemmi_le_o_cif():
    gemmi = pytest.importorskip("gemmi")
    for nome, z in (("Fe", 2), ("Cu", 4), ("Mg", 2)):
        doc = gemmi.cif.read_string(gerar_cif({"nome": nome})["content"])
        st = gemmi.make_small_structure_from_block(doc.sole_block())
        assert len(st.get_all_unit_cell_sites()) == z
