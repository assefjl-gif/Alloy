"""Senhas, tokens e matriz RBAC (ADR-008/009): testes puros, sem banco."""

from __future__ import annotations

import uuid

import pytest

from app.security import senhas, tokens
from app.security.rbac import MATRIZ, Ator, Contexto, autorizar, enxerga_instituicao


@pytest.mark.parametrize("senha, esperado", [
    ("curta", "pelo menos 10"), ("1234567890", "comum"), ("aaaaaaaaaaaa", "comum"),
    ("joaosilva-2026!", "e-mail"), ("x" * 300, "no máximo"),
])
def test_politica_recusa(senha, esperado):
    assert esperado in (senhas.problema_na_senha(senha, email="joaosilva@exemplo.test") or "")


def test_politica_aceita_e_hash_e_argon2id():
    senha = "cristal-cubico-2026"
    assert senhas.problema_na_senha(senha, email="ana@exemplo.test", nome="Ana") is None
    h = senhas.gerar_hash(senha)
    assert h.startswith("$argon2id$") and senhas.verificar(h, senha) and not senhas.verificar(h, senha + "x")
    assert senhas.gerar_hash(senha) != h   # sal aleatório
    assert not senhas.verificar(None, senha) and not senhas.verificar("lixo", senha)


def test_tokens_tem_256_bits_e_hash_confere():
    t = tokens.novo_token()
    assert len(t) >= 43 and t != tokens.novo_token()
    assert tokens.confere(t, tokens.sha256(t)) and not tokens.confere(t + "x", tokens.sha256(t))


INST, OUTRA, TURMA = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def _ator(**kw) -> Ator:
    return Ator(usuario_id=uuid.uuid4(), **kw)


PROFESSOR = _ator(papeis_instituicao={INST: frozenset({"professor"})},
                  papeis_turma={TURMA: frozenset({"professor_responsavel"})})
ESTUDANTE = _ator(papeis_instituicao={INST: frozenset({"estudante"})},
                  papeis_turma={TURMA: frozenset({"estudante_matriculado"})})
VISITANTE = _ator(papeis_instituicao={OUTRA: frozenset({"professor"})})
ADMIN = _ator(admin_geral=True)
NA_TURMA = Contexto(instituicao_id=INST, turma_id=TURMA)

#: (ator, ação, esperado) — a matriz completa é a referência; isto fixa os casos críticos.
CASOS = [
    (PROFESSOR, "turma.criar", True), (ESTUDANTE, "turma.criar", False), (VISITANTE, "turma.criar", False),
    (PROFESSOR, "turma.editar", True), (ESTUDANTE, "turma.editar", False),
    (PROFESSOR, "turma.matricular", True), (ESTUDANTE, "turma.matricular", False),
    (PROFESSOR, "atividade.publicar", True), (ESTUDANTE, "atividade.publicar", False),
    (ESTUDANTE, "atividade.responder", True), (PROFESSOR, "atividade.responder", False),
    (PROFESSOR, "progresso.ver_turma", True), (ESTUDANTE, "progresso.ver_turma", False),
    (ESTUDANTE, "turma.ver", True), (VISITANTE, "turma.ver", False),
    (ADMIN, "dado.revisar", True), (None, "turma.ver", False),
]


@pytest.mark.parametrize("ator, acao, esperado", CASOS)
def test_matriz_rbac(ator, acao, esperado):
    assert autorizar(ator, acao, NA_TURMA) is esperado


def test_papel_vale_so_no_escopo_da_instituicao():
    assert autorizar(VISITANTE, "turma.criar", Contexto(instituicao_id=OUTRA))
    assert not autorizar(VISITANTE, "turma.criar", Contexto(instituicao_id=INST))
    assert not enxerga_instituicao(VISITANTE, INST) and enxerga_instituicao(ADMIN, INST)


def test_acao_desconhecida_falha_alto():
    with pytest.raises(KeyError):
        autorizar(ADMIN, "turma.apagar_tudo")


def test_toda_acao_da_matriz_tem_ao_menos_um_caso():
    assert {acao for _, acao, _ in CASOS} >= set(MATRIZ) - {"questao.criar"}
    assert autorizar(PROFESSOR, "questao.criar", Contexto(instituicao_id=INST))
