"""Exportadores CIF e XYZ (achados EX-01 a EX-07).

Correções da v1.1:
* EX-01 comprimentos em ångström (antes nm);
* EX-02 coordenadas realmente fracionárias em [0,1) (antes cartesianas no HC);
* EX-03 apenas a base cristalográfica — sem réplicas de fronteira (Fe: 2 átomos, não 9);
* EX-04 grupo espacial real + sítio de Wyckoff + operações de simetria explícitas;
* EX-05 pseudo-átomo ``X`` para células genéricas (antes ``XCFC``);
* EX-06 ``_cell_volume``, ``_cell_formula_units_Z`` e densidade calculada no cabeçalho;
* EX-07 versão lida de ``crystalab.__version__``.
"""

from __future__ import annotations

import datetime as _dt
import itertools
import unicodedata
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .. import __version__
from .celula import calcular_estrutura
from .constantes import NM_PARA_ANGSTROM, SQRT3
from .erros import DadosInsuficientes
from .estruturas import ESTRUTURAS
from .geometria import frac_para_cart, vetores_de_rede
from .repositorio import RepositorioMateriais

PSEUDO_ATOMO = "X"

_CENTRAGENS: Dict[str, List[Tuple[str, str, str]]] = {
    "P": [("", "", "")],
    "I": [("", "", ""), ("+1/2", "+1/2", "+1/2")],
    "F": [("", "", ""), ("", "+1/2", "+1/2"), ("+1/2", "", "+1/2"), ("+1/2", "+1/2", "")],
}

# Operações do grupo P 63/m m c (nº 194), International Tables for Crystallography, Vol. A.
_OPS_194: Tuple[str, ...] = (
    "x,y,z", "-y,x-y,z", "-x+y,-x,z", "-x,-y,z+1/2", "y,-x+y,z+1/2", "x-y,x,z+1/2",
    "y,x,-z", "x-y,-y,-z", "-x,-x+y,-z", "-y,-x,-z+1/2", "-x+y,y,-z+1/2", "x,x-y,-z+1/2",
    "-x,-y,-z", "y,-x+y,-z", "x-y,x,-z", "x,y,-z+1/2", "-y,x-y,-z+1/2", "-x+y,-x,-z+1/2",
    "-y,-x,z", "-x+y,y,z", "x,x-y,z", "y,x,z+1/2", "x-y,-y,z+1/2", "-x,-x+y,z+1/2",
)


def _ops_cubicas(rede: str) -> List[str]:
    """48 operações de m-3m (permutações com sinais) × translações de centragem."""
    eixos = "xyz"
    rotacoes = []
    for perm in itertools.permutations(range(3)):
        for sinais in itertools.product(("", "-"), repeat=3):
            rotacoes.append([sinais[i] + eixos[perm[i]] for i in range(3)])
    ops = []
    for translacao in _CENTRAGENS[rede]:
        for rot in rotacoes:
            ops.append(",".join(rot[i] + translacao[i] for i in range(3)))
    return ops


def operacoes_simetria(estrutura: str) -> List[str]:
    grupo = ESTRUTURAS[estrutura]["grupo_espacial"]
    if estrutura == "HC":
        return list(_OPS_194)
    return _ops_cubicas(grupo["rede"])


def _ascii(texto: str) -> str:
    """CIF 1.1 é ASCII: translitera acentos e letras gregas usadas nos nomes."""
    gregas = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon"}
    for letra, nome in gregas.items():
        texto = texto.replace(letra, nome)
    decomposto = unicodedata.normalize("NFD", texto)
    limpo = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return limpo.encode("ascii", "ignore").decode("ascii").replace("'", "")


def _simbolo(resultado: Mapping[str, Any]) -> str:
    return resultado.get("simbolo") or PSEUDO_ATOMO


def _celula_angstrom(resultado: Mapping[str, Any]) -> Tuple[float, float, float, Tuple[float, float, float]]:
    if resultado["a_nm"] is None:
        raise DadosInsuficientes("Informe o raio atômico para exportar com parâmetros de rede absolutos.")
    a = resultado["a_nm"] * NM_PARA_ANGSTROM
    if resultado["estrutura"] == "HC":
        return a, a, resultado["c_nm"] * NM_PARA_ANGSTROM, (90.0, 90.0, 120.0)
    return a, a, a, (90.0, 90.0, 90.0)


def _volume_celula_cristalografica(estrutura: str, a: float, c: float) -> float:
    if estrutura == "HC":
        return SQRT3 / 2.0 * a * a * c
    return a ** 3


def _nome_arquivo(simbolo: str, estrutura: str, extensao: str) -> str:
    return f"crystalab_{simbolo.lower()}_{estrutura.lower()}.{extensao}"


def gerar_cif(payload: Mapping[str, Any], repo: Optional[RepositorioMateriais] = None) -> Dict[str, Any]:
    resultado = calcular_estrutura(payload, repo)
    estrutura = resultado["estrutura"]
    info = ESTRUTURAS[estrutura]
    grupo = info["grupo_espacial"]
    simbolo = _simbolo(resultado)
    formula = _ascii(str(payload.get("formula") or simbolo))
    a, b, c, (alpha, beta, gamma) = _celula_angstrom(resultado)
    volume = _volume_celula_cristalografica(estrutura, a, c)
    z = info["z"]

    linhas: List[str] = [
        "#\\#CIF_1.1",
        f"# Gerado pelo CrystaLab {__version__} (Alloy) - modelo de esferas rigidas.",
        f"# Estrutura: {_ascii(resultado['estrutura_nome'])} ({estrutura}); "
        f"parametro de rede: {'medido' if resultado['a_fonte'] == 'medido' else 'derivado do raio atomico'}.",
    ]
    if resultado.get("fonte"):
        linhas.append(f"# Fonte dos dados: {_ascii(resultado['fonte'])}")
    if resultado["editado"]:
        linhas.append("# ATENCAO: parametros editados pelo usuario; estrutura hipotetica.")
    linhas += [
        f"data_crystalab_{simbolo.lower()}_{estrutura.lower()}",
        f"_audit_creation_method            'CrystaLab {__version__} (Alloy)'",
        f"_audit_creation_date              {_dt.date.today().isoformat()}",
        f"_chemical_name_common             '{_ascii(resultado['rotulo'])}'",
        f"_chemical_formula_sum             '{formula}'",
    ]
    if resultado["peso"] is not None:
        linhas.append(f"_chemical_formula_weight          {resultado['peso']:.4f}")
    linhas += [
        f"_cell_length_a                    {a:.6f}",
        f"_cell_length_b                    {b:.6f}",
        f"_cell_length_c                    {c:.6f}",
        f"_cell_angle_alpha                 {alpha:.4f}",
        f"_cell_angle_beta                  {beta:.4f}",
        f"_cell_angle_gamma                 {gamma:.4f}",
        f"_cell_volume                      {volume:.4f}",
        f"_cell_formula_units_Z             {z}",
    ]
    if resultado["densidade"] is not None:
        linhas.append(f"_exptl_crystal_density_diffrn     {resultado['densidade']:.4f}")
    linhas += [
        f"_symmetry_cell_setting            {'hexagonal' if estrutura == 'HC' else 'cubic'}",
        f"_symmetry_space_group_name_H-M    '{grupo['hm']}'",
        f"_symmetry_Int_Tables_number       {grupo['numero']}",
        f"_space_group_name_H-M_alt         '{grupo['hm']}'",
        f"_space_group_IT_number            {grupo['numero']}",
        "",
        "loop_",
        "_symmetry_equiv_pos_as_xyz",
        *operacoes_simetria(estrutura),
        "",
        "loop_",
        "_atom_site_label",
        "_atom_site_type_symbol",
        "_atom_site_Wyckoff_symbol",
        "_atom_site_fract_x",
        "_atom_site_fract_y",
        "_atom_site_fract_z",
        "_atom_site_occupancy",
    ]
    x, y, zz = grupo["sitio"]
    linhas.append(f"{simbolo}1 {simbolo} {grupo['wyckoff']} {x:.6f} {y:.6f} {zz:.6f} 1.0")
    linhas.append("")
    return {
        "formato": "cif",
        "filename": _nome_arquivo(simbolo, estrutura, "cif"),
        "content": "\n".join(linhas),
        "content_type": "chemical/x-cif",
    }


def _texto_extxyz(texto: str) -> str:
    return " ".join(str(texto).replace('"', "'").split())


def gerar_xyz(payload: Mapping[str, Any], repo: Optional[RepositorioMateriais] = None) -> Dict[str, Any]:
    """XYZ estendido (extXYZ): base cristalográfica em Å + vetores de rede no comentário."""
    resultado = calcular_estrutura(payload, repo)
    estrutura = resultado["estrutura"]
    simbolo = _simbolo(resultado)
    a, _, c, _ = _celula_angstrom(resultado)
    vetores = vetores_de_rede(estrutura, a, c)
    c_a = resultado["c_a"]

    comentario = payload.get("comentario") or \
        f"CrystaLab {__version__} - {resultado['rotulo']} - {estrutura}"
    lattice = " ".join(f"{v:.6f}" for vetor in vetores for v in vetor)
    cabecalho = (f'Lattice="{lattice}" Properties=species:S:1:pos:R:3 pbc="T T T" '
                 f'comment="{_texto_extxyz(comentario)}"')

    linhas = [str(len(resultado["base"])), cabecalho]
    for sitio in resultado["base"]:
        cart = frac_para_cart(estrutura, sitio["frac"], c_a)
        linhas.append(f"{simbolo} {cart[0] * a:.6f} {cart[1] * a:.6f} {cart[2] * a:.6f}")
    return {
        "formato": "xyz",
        "filename": _nome_arquivo(simbolo, estrutura, "xyz"),
        "content": "\n".join(linhas) + "\n",
        "content_type": "chemical/x-xyz",
    }

