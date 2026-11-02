"""Motor cristalográfico único do Alloy Virtual Lab (ADR-004).

Funções puras: sem FastAPI, sem banco, sem leitura de arquivos. Os dados de
referência chegam por um objeto que cumpre ``RepositorioMateriais``.
Base: CrystaLab v1.1.0 (``core/``); recursos da v1.4 entram em módulos próprios
(``rede``, ``planar``, ``supercelula``, ``ligas``) sempre com testes de referência.
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
from .referencia import Metal, RepositorioMateriais
from .tabelas import bootstrap, metais_publicos, tabela_estruturas
from .versao import VERSAO_MOTOR

__all__ = [
    "ESTRUTURAS", "VERSAO_MOTOR", "DadosInsuficientes", "EntradaInvalida", "ErroDeDados", "ErroDominio",
    "IndiceMillerInvalido", "MaterialDesconhecido", "Metal", "PlanoForaDaCelula",
    "RepositorioMateriais", "bootstrap", "calcular_densidade",
    "calcular_estrutura", "calcular_miller", "cart_para_frac", "fator_empacotamento",
    "frac_para_cart", "geometria_celula", "gerar_cif", "gerar_xyz", "metais_publicos",
    "normalizar_estrutura", "operacoes_simetria", "reduzir",
    "resolver_alvo", "tabela_estruturas",
]
