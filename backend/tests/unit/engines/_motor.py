"""Acesso ao motor nos testes migrados do B: injeta o repositório do seed (ADR-004).

O motor não tem mais repositório implícito; aqui ele é fornecido explicitamente,
mantendo as chamadas dos testes originais iguais.
"""

from __future__ import annotations

from functools import partial

from app.engines import crystallography as motor
from app.repositories.materiais_json import repositorio_padrao

REPO = repositorio_padrao()

calcular_estrutura = partial(motor.calcular_estrutura, repo=REPO)
calcular_densidade = partial(motor.calcular_densidade, repo=REPO)
gerar_cif = partial(motor.gerar_cif, repo=REPO)
gerar_xyz = partial(motor.gerar_xyz, repo=REPO)
metais_publicos = partial(motor.metais_publicos, repo=REPO)
bootstrap = partial(motor.bootstrap, repo=REPO)
