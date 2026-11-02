"""Constantes físicas e numéricas centralizadas (achados CR-08 e CR-09)."""

from __future__ import annotations

import math
from typing import Tuple

#: Constante de Avogadro — CODATA 2018, valor exato por definição do SI (mol⁻¹).
N_AVOGADRO: float = 6.02214076e23

SQRT2: float = math.sqrt(2.0)
SQRT3: float = math.sqrt(3.0)

#: Tolerância geométrica. Os cálculos internos usam coordenadas SEM arredondamento;
#: o arredondamento (6 casas) só acontece na serialização da resposta.
EPS: float = 1e-9

#: Casas decimais usadas apenas na saída (JSON para a UI).
CASAS_SAIDA: int = 6

NM_PARA_CM: float = 1e-7
NM_PARA_ANGSTROM: float = 10.0

#: Acima deste desvio (|ρ_teórica/ρ_exp − 1|) o motor emite um aviso (achado CR-01).
LIMITE_DESVIO_PERCENT: float = 3.0

#: Tolerância relativa para decidir se o usuário "editou" um parâmetro tabelado.
#: O editor da UI exibe c/a com 4 casas, então diferenças menores que isso não contam.
TOLERANCIA_EDICAO: float = 1e-4

#: Faixas aceitas para entradas do usuário (mesmas da versão 1.0).
FAIXA_RAIO_NM: Tuple[float, float] = (0.02, 0.5)
FAIXA_PESO: Tuple[float, float] = (1.0, 300.0)
FAIXA_C_A: Tuple[float, float] = (1.0, 2.5)
FAIXA_A_NM: Tuple[float, float] = (0.01, 2.0)
INDICE_MAXIMO: int = 9

Vetor = Tuple[float, float, float]
