"""Questões, instâncias, tentativas e progresso com correção NO SERVIDOR (RQ-EDU-01..04, ADR-009).

Regras:
* o gabarito (``instancias_questao.gabarito_calculado``) nunca sai na criação da instância; só na
  resposta de uma tentativa, quando a política libera (acertou ou esgotou as tentativas);
* questão de instituição só é visível para quem tem vínculo nela — os demais recebem 404;
* instância é do usuário que a pediu: tentativa em instância alheia → 404 (teste de IDOR);
* a semente é sorteada no servidor e registrada: a mesma instância reproduz a mesma questão.
"""

from __future__ import annotations

import secrets
import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.educational import geradores
from app.engines.crystallography.erros import EntradaInvalida
from app.engines.crystallography.referencia import RepositorioMateriais
from app.models import InstanciaQuestao, Questao, Tentativa
from app.security.rbac import Ator, Contexto, autorizar, enxerga_instituicao

from .erros import Conflito, NaoEncontrado, Proibido

MAX_TENTATIVAS_PADRAO = 3


def _uuid(valor: Any) -> uuid.UUID:
    try:
        return valor if isinstance(valor, uuid.UUID) else uuid.UUID(str(valor))
    except ValueError:
        raise NaoEncontrado("Recurso não encontrado.") from None


def _questao_publica(q: Questao) -> Dict[str, Any]:
    return {"id": str(q.id), "titulo": q.titulo, "enunciado": q.enunciado, "tipo": q.tipo,
            "gerador": (q.parametros or {}).get("gerador"), "topicos": list(q.topicos or []),
            "dificuldade": q.dificuldade, "instituicao_id": str(q.instituicao_id) if q.instituicao_id else None,
            "max_tentativas": int((q.politica or {}).get("max_tentativas", MAX_TENTATIVAS_PADRAO)),
            "publicada": q.publicada}


class ServicoEducacao:
    def __init__(self, db: Session, repo: RepositorioMateriais) -> None:
        self.db = db
        self.repo = repo

    @staticmethod
    def geradores() -> List[Dict[str, Any]]:
        return [{"codigo": c, "titulo": t, "topicos": list(tp)} for c, (t, tp, _) in geradores.GERADORES.items()]

    # --- questões ------------------------------------------------------------------
    def criar_questao(self, ator: Ator, dados: Mapping[str, Any]) -> Dict[str, Any]:
        gerador = dados["gerador"]
        if gerador not in geradores.GERADORES:
            raise EntradaInvalida(f"Gerador desconhecido: {gerador}. Use GET /api/v1/edu/generators.")
        instituicao = _uuid(dados["instituicao_id"]) if dados.get("instituicao_id") else None
        if instituicao is None and not ator.admin_geral:
            raise Proibido("Questão pública (sem instituição) só pode ser criada pela administração geral.")
        if not autorizar(ator, "questao.criar", Contexto(instituicao_id=instituicao)):
            if instituicao and not enxerga_instituicao(ator, instituicao):
                raise NaoEncontrado("Instituição não encontrada.")
            raise Proibido("Seu papel nesta instituição não permite criar questões.")
        titulo, topicos, _ = geradores.GERADORES[gerador]
        q = Questao(instituicao_id=instituicao, autor_id=ator.usuario_id, tipo="numerico",
                    titulo=dados.get("titulo") or titulo, enunciado=dados.get("enunciado") or titulo,
                    gabarito={"gerador": gerador, "calculado_no_servidor": True}, parametros={"gerador": gerador},
                    politica={"max_tentativas": int(dados.get("max_tentativas") or MAX_TENTATIVAS_PADRAO)},
                    topicos=list(dados.get("topicos") or topicos), dificuldade=int(dados.get("dificuldade") or 2),
                    publicada=bool(dados.get("publicada", True)))
        self.db.add(q)
        self.db.flush()
        return _questao_publica(q)

    def _visivel(self, ator: Ator):
        filtro = Questao.publicada.is_(True)
        if ator.admin_geral:
            return filtro
        return filtro & or_(Questao.instituicao_id.is_(None), Questao.instituicao_id.in_(list(ator.papeis_instituicao)))

    def listar_questoes(self, ator: Ator) -> List[Dict[str, Any]]:
        return [_questao_publica(q) for q in self.db.scalars(
            select(Questao).where(self._visivel(ator)).order_by(Questao.titulo, Questao.id))]

    # --- instâncias e tentativas ---------------------------------------------------
    def nova_instancia(self, ator: Ator, questao_id: Any) -> Dict[str, Any]:
        q = self.db.scalar(select(Questao).where(Questao.id == _uuid(questao_id), self._visivel(ator)))
        if q is None:
            raise NaoEncontrado("Questão não encontrada.")
        semente = secrets.randbelow(2 ** 31)
        gerada = geradores.gerar(q.parametros["gerador"], semente, self.repo)
        inst = InstanciaQuestao(questao_id=q.id, questao_versao=q.versao, usuario_id=ator.usuario_id, semente=semente,
                                parametros_sorteados=gerada.publico["parametros"], gabarito_calculado=gerada.gabarito,
                                versao_motor=gerada.versao_motor)
        self.db.add(inst)
        self.db.flush()
        return {"id": str(inst.id), "questao_id": str(q.id), "titulo": q.titulo,
                "enunciado": gerada.publico["enunciado"], "parametros": gerada.publico["parametros"],
                "unidade": gerada.publico["unidade"], "max_tentativas": _questao_publica(q)["max_tentativas"],
                "semente": semente}

    def responder(self, ator: Ator, instancia_id: Any, resposta: float,
                  tempo_ms: Optional[int] = None) -> Dict[str, Any]:
        inst = self.db.get(InstanciaQuestao, _uuid(instancia_id))
        if inst is None or inst.usuario_id != ator.usuario_id:
            raise NaoEncontrado("Instância não encontrada.")
        questao = self.db.get(Questao, inst.questao_id)
        maximo = int((questao.politica or {}).get("max_tentativas", MAX_TENTATIVAS_PADRAO))
        anteriores = list(self.db.scalars(select(Tentativa).where(Tentativa.instancia_id == inst.id)
                                          .order_by(Tentativa.n)))
        if any(t.correta for t in anteriores):
            raise Conflito("Esta questão já foi resolvida. Peça uma nova instância para praticar de novo.")
        if len(anteriores) >= maximo:
            raise Conflito(f"Tentativas esgotadas ({maximo}).")
        correta, tipo_erro = geradores.corrigir(float(resposta), inst.gabarito_calculado)
        n = len(anteriores) + 1
        libera = correta or n >= maximo
        self.db.add(Tentativa(instancia_id=inst.id, n=n, resposta={"valor": resposta},
                              correta=correta, pontuacao=Decimal(1 if correta else 0), tipo_erro=tipo_erro,
                              tempo_ms=tempo_ms, gabarito_visto=libera))
        self.db.flush()
        retorno: Dict[str, Any] = {"correta": correta, "tentativa": n, "restantes": maximo - n, "tipo_erro": tipo_erro,
                                   "gabarito": None}
        if libera:
            g = inst.gabarito_calculado
            retorno["gabarito"] = {"valor": g["valor"], "unidade": g["unidade"], "resolucao": g.get("resolucao", [])}
        return retorno

    # --- progresso -----------------------------------------------------------------
    def progresso(self, ator: Ator) -> Dict[str, Any]:
        linhas = self.db.execute(
            # max(boolean) não existe no PostgreSQL: CASE → 0/1 é portável.
            select(Questao.topicos, InstanciaQuestao.id, func.count(Tentativa.id),
                   func.max(case((Tentativa.correta.is_(True), 1), else_=0)))
            .join(InstanciaQuestao, InstanciaQuestao.questao_id == Questao.id)
            .outerjoin(Tentativa, Tentativa.instancia_id == InstanciaQuestao.id)
            .where(InstanciaQuestao.usuario_id == ator.usuario_id)
            .group_by(InstanciaQuestao.id, Questao.id)).all()
        por_topico: Dict[str, Dict[str, int]] = defaultdict(lambda: {"instancias": 0, "tentativas": 0, "resolvidas": 0})
        for topicos, _, tentativas, acertou in linhas:
            for topico in topicos or ["geral"]:
                p = por_topico[topico]
                p["instancias"] += 1
                p["tentativas"] += int(tentativas or 0)
                p["resolvidas"] += 1 if acertou else 0
        return {"topicos": [{"topico": k, **v} for k, v in sorted(por_topico.items())],
                "resolvidas": sum(1 for *_, acertou in linhas if acertou), "instancias": len(linhas)}
