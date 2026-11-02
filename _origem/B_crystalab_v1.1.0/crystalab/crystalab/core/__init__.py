"""Núcleo cristalográfico puro do CrystaLab (sem dependência de FastAPI).

Esta é a ÚNICA cópia do motor (achado BE-08). API, UI, testes e futuros módulos
do Alloy devem importar daqui, nunca duplicar as funções.
"""

from .celula import calcular_densidade, calcular_estrutura, resolver_alvo
from .erros import (
    DadosInsuficientes,
    EntradaInvalida,
    ErroDeDados,
    ErroDominio,
    IndiceMillerInvalido,
    MaterialDesconhecido,
    PlanoForaDaCelula,
)
from .estruturas import ESTRUTURAS, normalizar_estrutura
from .exportacao import gerar_cif, gerar_xyz, operacoes_simetria
from .geometria import cart_para_frac, fator_empacotamento, frac_para_cart, geometria_celula
from .miller import calcular_miller, reduzir
from .repositorio import Metal, RepositorioJSON, RepositorioMateriais, repositorio_padrao
from .tabelas import bootstrap, metais_publicos, tabela_estruturas

__all__ = [
    "ESTRUTURAS", "DadosInsuficientes", "EntradaInvalida", "ErroDeDados", "ErroDominio",
    "IndiceMillerInvalido", "MaterialDesconhecido", "Metal", "PlanoForaDaCelula",
    "RepositorioJSON", "RepositorioMateriais", "bootstrap", "calcular_densidade",
    "calcular_estrutura", "calcular_miller", "cart_para_frac", "fator_empacotamento",
    "frac_para_cart", "geometria_celula", "gerar_cif", "gerar_xyz", "metais_publicos",
    "normalizar_estrutura", "operacoes_simetria", "reduzir", "repositorio_padrao",
    "resolver_alvo", "tabela_estruturas",
]
