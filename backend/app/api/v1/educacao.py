"""Rotas educacionais (/api/v1/edu, /api/v1/me/progress — RQ-EDU-01..04). Correção no servidor."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Response

from app.services.autenticacao import Autenticado
from app.services.educacao import ServicoEducacao

from ..dependencias import get_autenticado, get_servico_educacao
from .schemas import (
    AttemptRequest,
    AttemptResult,
    ErroEnvelope,
    GeneratorInfo,
    OkEnvelope,
    Progress,
    QuestionCreate,
    QuestionInfo,
    QuestionInstance,
)

_ERROS = {401: {"model": ErroEnvelope}, 403: {"model": ErroEnvelope}, 404: {"model": ErroEnvelope},
          409: {"model": ErroEnvelope}, 422: {"model": ErroEnvelope}, 503: {"model": ErroEnvelope}}

router = APIRouter(prefix="/api/v1", responses=_ERROS, tags=["educacional"])


def _ok(resultado):
    return {"ok": True, "result": resultado}


@router.get("/edu/generators", response_model=OkEnvelope[List[GeneratorInfo]], summary="Geradores de questões")
def listar_geradores():
    return _ok(ServicoEducacao.geradores())


@router.post("/edu/questions", response_model=OkEnvelope[QuestionInfo], status_code=201,
             summary="Cria questão parametrizada (professor/pesquisador da instituição)")
def criar_questao(payload: QuestionCreate, autenticado: Autenticado = Depends(get_autenticado),
                  servico: ServicoEducacao = Depends(get_servico_educacao)):
    return _ok(servico.criar_questao(autenticado.ator, payload.model_dump()))


@router.get("/edu/questions", response_model=OkEnvelope[List[QuestionInfo]], summary="Questões visíveis para mim")
def listar_questoes(autenticado: Autenticado = Depends(get_autenticado),
                    servico: ServicoEducacao = Depends(get_servico_educacao)):
    return _ok(servico.listar_questoes(autenticado.ator))


@router.post("/edu/questions/{questao_id}/instances", response_model=OkEnvelope[QuestionInstance], status_code=201,
             summary="Sorteia uma instância (o gabarito fica no servidor)")
def nova_instancia(questao_id: str, response: Response, autenticado: Autenticado = Depends(get_autenticado),
                   servico: ServicoEducacao = Depends(get_servico_educacao)):
    response.headers["Cache-Control"] = "no-store"
    return _ok(servico.nova_instancia(autenticado.ator, questao_id))


@router.post("/edu/instances/{instancia_id}/attempts", response_model=OkEnvelope[AttemptResult],
             summary="Envia uma resposta; a correção é feita no servidor")
def responder(instancia_id: str, payload: AttemptRequest, response: Response,
              autenticado: Autenticado = Depends(get_autenticado),
              servico: ServicoEducacao = Depends(get_servico_educacao)):
    response.headers["Cache-Control"] = "no-store"
    return _ok(servico.responder(autenticado.ator, instancia_id, payload.resposta, payload.tempo_ms))


@router.get("/me/progress", response_model=OkEnvelope[Progress], summary="Meu progresso por tópico")
def progresso(autenticado: Autenticado = Depends(get_autenticado),
              servico: ServicoEducacao = Depends(get_servico_educacao)):
    return _ok(servico.progresso(autenticado.ator))
