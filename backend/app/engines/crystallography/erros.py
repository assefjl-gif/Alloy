"""Exceções de domínio (achado BE-06).

Somente ``ErroDominio`` (e subclasses) vira HTTP 400. Um ``ValueError`` comum,
vindo de um bug interno, volta a ser HTTP 500 — não é mais mascarado como erro
do usuário. ``ErroDominio`` herda de ``ValueError`` para que código antigo que
fazia ``except ValueError`` continue funcionando.
"""

from __future__ import annotations

from typing import Optional


class ErroDominio(ValueError):
    """Erro causado pela entrada do usuário ou por uma regra do domínio."""

    codigo: str = "ERRO_DOMINIO"

    def __init__(self, mensagem: str, *, codigo: Optional[str] = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        if codigo:
            self.codigo = codigo


class EntradaInvalida(ErroDominio):
    codigo = "ENTRADA_INVALIDA"


class MaterialDesconhecido(ErroDominio):
    codigo = "MATERIAL_DESCONHECIDO"


class IndiceMillerInvalido(ErroDominio):
    codigo = "INDICE_MILLER_INVALIDO"


class PlanoForaDaCelula(ErroDominio):
    codigo = "PLANO_FORA_DA_CELULA"


class DadosInsuficientes(ErroDominio):
    codigo = "DADOS_INSUFICIENTES"


class ErroDeDados(RuntimeError):
    """Arquivo de dados (seed) inválido. Falha na inicialização, nunca em uma requisição."""
