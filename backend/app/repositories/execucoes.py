"""Gravação do histórico pessoal de cálculo (``execucoes_calculo``).

Separação de responsabilidades (R2-BE-03): o histórico é EFEITO SECUNDÁRIO do cálculo. A gravação vai em
SAVEPOINT próprio, com o motor garantido antes de ser referenciado; se falhar, o SAVEPOINT é desfeito, a
transação da requisição continua válida e o erro é devolvido ao chamador — que decide (o serviço registra em
log e avisa o usuário, sem derrubar o resultado científico já calculado).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Mapping, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import ExecucaoCalculo

from .motores import garantir_motor


def registrar_execucao(sessao: Session, *, usuario_id: uuid.UUID, motor_codigo: str, motor_versao: str,
                       versao_dados: str, operacao: str, parametros: Mapping[str, Any],
                       parametros_sha256: bytes, resultado: Mapping[str, Any], classe_resultado: str,
                       duracao_ms: Decimal) -> Optional[SQLAlchemyError]:
    """Grava uma execução. Devolve ``None`` em sucesso ou o erro de banco, sem propagá-lo.

    Em falha, a sessão fica utilizável: o SAVEPOINT é desfeito e o registro pendente é descartado, para que o
    commit da unidade de trabalho não tente inseri-lo outra vez.
    """
    registro = ExecucaoCalculo(
        usuario_id=usuario_id, motor_codigo=motor_codigo, motor_versao=motor_versao,
        versao_dados=versao_dados, operacao=operacao, parametros=dict(parametros),
        parametros_sha256=parametros_sha256, resultado=dict(resultado), classe_resultado=classe_resultado,
        status="concluido", duracao_ms=duracao_ms)
    try:
        with sessao.begin_nested():
            garantir_motor(sessao, motor_codigo, motor_versao)
            sessao.add(registro)
            sessao.flush()
        return None
    except SQLAlchemyError as erro:
        if registro in sessao:
            sessao.expunge(registro)
        return erro
