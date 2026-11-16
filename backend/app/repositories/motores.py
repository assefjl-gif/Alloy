"""Linhas da tabela ``motores`` (código + versão) — único lugar que sabe como registrar um motor.

``execucoes_calculo`` referencia ``motores`` pela chave estrangeira composta ``fk_execucoes_calculo_motor``
(migração 0001). Toda gravação de histórico depende da linha do motor existir. O seed (``seed_sql``) e o
caminho de gravação em requisição usam as MESMAS funções daqui, para não duplicar conhecimento da tabela nem
divergir de vocabulário (R2-BE-03, defeito F-1 da integração).
"""

from __future__ import annotations

from typing import Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.engines.crystallography import VERSAO_MOTOR as VERSAO_CRISTALOGRAFIA
from app.engines.hea.analitico import VERSAO_MOTOR as VERSAO_HEA
from app.engines.thermodynamics.termico import VERSAO_MOTOR as VERSAO_TERMICO
from app.models import Motor


def motores_do_catalogo() -> Tuple[Tuple[str, str], ...]:
    """Motores desta build: (código, versão). Mesma fonte usada em ``procedencia.motor``/``versao_motor``."""
    return (("crystallography", VERSAO_CRISTALOGRAFIA), ("thermodynamics", VERSAO_TERMICO), ("hea", VERSAO_HEA))


def garantir_motor(sessao: Session, codigo: str, versao: str) -> None:
    """Get-or-create idempotente da linha ``motores(codigo, versao)``.

    Seguro sob concorrência: a inserção vai em SAVEPOINT e, se outra transação já inseriu a mesma chave
    primária nesse intervalo, a violação de unicidade é absorvida (a linha passou a existir, que é o
    objetivo). Qualquer outro erro de integridade sobe — não é absorvido em silêncio.
    """
    if sessao.get(Motor, (codigo, versao)) is not None:
        return
    registro = Motor(codigo=codigo, versao=versao)
    try:
        with sessao.begin_nested():
            sessao.add(registro)
            sessao.flush()
    except IntegrityError:
        # Corrida com outra requisição/worker: descarta o objeto local e confirma que a linha existe.
        if registro in sessao:
            sessao.expunge(registro)
        if sessao.get(Motor, (codigo, versao)) is None:
            raise
