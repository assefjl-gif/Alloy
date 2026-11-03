"""Senhas (ADR-008): Argon2id via argon2-cffi e política mínima.

Parâmetros: os padrões do ``PasswordHasher`` (Argon2id, RFC 9106 "low memory": t=3, m=64 MiB, p=4).
``precisa_rehash`` permite subir o custo no futuro sem invalidar senhas existentes.
"""

from __future__ import annotations

from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

TAMANHO_MINIMO = 10
TAMANHO_MAXIMO = 256  # evita custo de hashing arbitrário (o Argon2 aceita qualquer tamanho)

#: Amostra das senhas mais comuns em vazamentos públicos (listas do tipo "top 100"), já com ≥ 10 caracteres
#: ou que viram ≥ 10 com sufixos óbvios. A verificação também recusa senha igual ao e-mail ou ao nome.
SENHAS_COMUNS = frozenset({
    "1234567890", "12345678910", "0123456789", "1111111111", "0000000000", "123456789a", "qwertyuiop",
    "1q2w3e4r5t", "password12", "password123", "senha12345", "senha123456", "iloveyou12", "abcdefghij",
    "asdfghjkl1", "qwerty1234", "1234qwerty", "aaaaaaaaaa", "123123123123", "minhasenha", "trocar1234",
    "admin12345", "administrador", "estudante1", "professor1", "brasil2026", "12345678abc",
})

_hasher = PasswordHasher()


def problema_na_senha(senha: str, *, email: str = "", nome: str = "") -> Optional[str]:
    """Devolve a mensagem do primeiro problema encontrado, ou ``None`` se a senha é aceitável."""
    if len(senha) < TAMANHO_MINIMO:
        return f"A senha precisa de pelo menos {TAMANHO_MINIMO} caracteres."
    if len(senha) > TAMANHO_MAXIMO:
        return f"A senha pode ter no máximo {TAMANHO_MAXIMO} caracteres."
    normalizada = senha.strip().lower()
    if normalizada in SENHAS_COMUNS or len(set(normalizada)) <= 2:
        return "Essa senha é comum demais. Escolha outra."
    local = email.split("@", 1)[0].lower()
    if (local and len(local) >= 4 and local in normalizada) or (nome and normalizada == nome.strip().lower()):
        return "A senha não pode conter o seu e-mail nem ser igual ao seu nome."
    return None


def gerar_hash(senha: str) -> str:
    return _hasher.hash(senha)


def verificar(hash_armazenado: Optional[str], senha: str) -> bool:
    """Compara em tempo constante. Sem hash (conta sem senha) também faz o trabalho, para não vazar tempo."""
    if not hash_armazenado:
        _hasher.hash(senha)
        return False
    try:
        return _hasher.verify(hash_armazenado, senha)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def precisa_rehash(hash_armazenado: str) -> bool:
    return _hasher.check_needs_rehash(hash_armazenado)
