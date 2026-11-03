"""Cadastro, login, sessões e histórico pessoal (ADR-008, ADR-009, RQ-SEG-01..06).

* Sessão: token opaco no cookie; o banco guarda o SHA-256. Expira por inatividade e por idade
  absoluta; cada uso desliza a inatividade (no máximo uma escrita por minuto).
* CSRF: token próprio, também só em hash; renovado a cada ``GET /auth/me`` e exigido em métodos de
  escrita sempre que a requisição traz cookie de sessão.
* Tentativas de login: bloqueio progressivo por e-mail e por IP (memória do processo — com várias
  réplicas, mover para o banco/Redis; registrado em PENDENCIAS).
* E-mail: o envio do link de verificação depende de SMTP (pendência); a conta nasce ``ativo`` com
  ``email_verificado_em`` vazio, e nada no sistema depende ainda de e-mail verificado.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.engines.crystallography.erros import EntradaInvalida
from app.models import ExecucaoCalculo, Matricula, Sessao, Turma, Usuario, VinculoInstitucional
from app.security import senhas, tokens
from app.security.rbac import Ator

from .erros import Conflito, CsrfInvalido, MuitasTentativas, NaoAutenticado

INATIVIDADE = timedelta(days=7)
VIDA_MAXIMA = timedelta(days=30)
INTERVALO_TOQUE = timedelta(minutes=1)
LIMITE_TENTATIVAS = 5
JANELA_TENTATIVAS_S = 15 * 60
MENSAGEM_LOGIN = "E-mail ou senha incorretos."  # mesma mensagem para conta inexistente (não enumera contas)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _utc(momento: datetime) -> datetime:
    """SQLite devolve datetimes sem fuso; o PostgreSQL, com. Tudo é gravado em UTC."""
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


def normalizar_email(email: str) -> str:
    return email.strip().lower()


class LimitadorLogin:
    """Falhas recentes por chave; após ``LIMITE_TENTATIVAS`` o bloqueio dobra a cada nova falha."""

    def __init__(self) -> None:
        self._falhas: Dict[str, List[float]] = {}
        self._trava = threading.Lock()

    def _recentes(self, chave: str, agora: float) -> List[float]:
        return [t for t in self._falhas.get(chave, []) if agora - t < JANELA_TENTATIVAS_S]

    def espera_s(self, *chaves: str) -> int:
        agora = time.monotonic()
        with self._trava:
            pior = 0.0
            for chave in chaves:
                recentes = self._recentes(chave, agora)
                if len(recentes) >= LIMITE_TENTATIVAS:
                    bloqueio = 30 * 2 ** (len(recentes) - LIMITE_TENTATIVAS)
                    pior = max(pior, recentes[-1] + bloqueio - agora)
            return max(0, int(pior + 0.999))

    def falhou(self, *chaves: str) -> None:
        agora = time.monotonic()
        with self._trava:
            for chave in chaves:
                self._falhas[chave] = self._recentes(chave, agora) + [agora]

    def sucesso(self, chave: str) -> None:
        with self._trava:
            self._falhas.pop(chave, None)


@dataclass(frozen=True)
class SessaoAberta:
    usuario: Dict[str, Any]
    token: str
    csrf: str
    expira_em: datetime


@dataclass(frozen=True)
class Autenticado:
    ator: Ator
    usuario: Usuario
    sessao: Sessao


def _usuario_publico(u: Usuario) -> Dict[str, Any]:
    return {"id": str(u.id), "nome": u.nome, "email": u.email, "admin_geral": u.admin_geral,
            "email_verificado": u.email_verificado_em is not None}


def carregar_ator(sessao_db: Session, usuario: Usuario) -> Ator:
    institucionais: Dict[uuid.UUID, set] = {}
    for v in sessao_db.scalars(select(VinculoInstitucional).where(VinculoInstitucional.usuario_id == usuario.id)):
        institucionais.setdefault(v.instituicao_id, set()).add(v.papel)
    por_turma: Dict[uuid.UUID, set] = {}
    for m in sessao_db.scalars(select(Matricula).where(Matricula.usuario_id == usuario.id,
                                                       Matricula.status == "ativa")):
        por_turma.setdefault(m.turma_id, set()).add(
            "estudante_matriculado" if m.papel_turma == "estudante" else m.papel_turma)
    for t in sessao_db.scalars(select(Turma).where(Turma.professor_responsavel_id == usuario.id)):
        por_turma.setdefault(t.id, set()).add("professor_responsavel")
    return Ator(usuario_id=usuario.id, admin_geral=usuario.admin_geral,
                papeis_instituicao={k: frozenset(v) for k, v in institucionais.items()},
                papeis_turma={k: frozenset(v) for k, v in por_turma.items()})


class ServicoAutenticacao:
    def __init__(self, sessao_db: Session, limitador: LimitadorLogin) -> None:
        self.db = sessao_db
        self.limitador = limitador

    # --- cadastro e login ------------------------------------------------------------
    def registrar(self, nome: str, email: str, senha: str) -> Dict[str, Any]:
        email = normalizar_email(email)
        problema = senhas.problema_na_senha(senha, email=email, nome=nome)
        if problema:
            raise EntradaInvalida(problema)
        if self.db.scalar(select(Usuario.id).where(Usuario.email == email)) is not None:
            raise Conflito("Já existe uma conta com esse e-mail.")
        usuario = Usuario(nome=nome.strip(), email=email, senha_hash=senhas.gerar_hash(senha), status="ativo")
        self.db.add(usuario)
        self.db.flush()
        return _usuario_publico(usuario)

    def entrar(self, email: str, senha: str, ip: Optional[str], agente: Optional[str]) -> SessaoAberta:
        email = normalizar_email(email)
        chaves = (f"email:{email}", f"ip:{ip or '?'}")
        espera = self.limitador.espera_s(*chaves)
        if espera:
            raise MuitasTentativas(f"Muitas tentativas de login. Tente de novo em {espera} s.")
        usuario = self.db.scalar(select(Usuario).where(Usuario.email == email))
        valido = senhas.verificar(usuario.senha_hash if usuario else None, senha)
        if not valido or usuario is None or usuario.status != "ativo":
            self.limitador.falhou(*chaves)
            raise NaoAutenticado(MENSAGEM_LOGIN)
        self.limitador.sucesso(chaves[0])
        if senhas.precisa_rehash(usuario.senha_hash or ""):
            usuario.senha_hash = senhas.gerar_hash(senha)
        agora = _agora()
        token, csrf = tokens.novo_token(), tokens.novo_token()
        registro = Sessao(usuario_id=usuario.id, token_sha256=tokens.sha256(token), csrf_sha256=tokens.sha256(csrf),
                          criada_em=agora, ultimo_uso_em=agora, expira_em=agora + VIDA_MAXIMA,
                          ip_criacao=(ip or None) and ip[:45], agente_usuario=(agente or None) and agente[:200])
        usuario.ultimo_acesso_em = agora
        self.db.add(registro)
        self.db.flush()
        return SessaoAberta(usuario=_usuario_publico(usuario), token=token, csrf=csrf, expira_em=registro.expira_em)

    # --- sessão --------------------------------------------------------------------
    def autenticar(self, token: Optional[str], *, csrf: Optional[str] = None,
                   exigir_csrf: bool = False) -> Optional[Autenticado]:
        """``None`` sem cookie; ``NaoAutenticado`` se o cookie não vale; ``CsrfInvalido`` se faltar o cabeçalho."""
        if not token:
            return None
        registro = self.db.scalar(select(Sessao).where(Sessao.token_sha256 == tokens.sha256(token)))
        agora = _agora()
        if (registro is None or registro.revogada_em is not None or _utc(registro.expira_em) <= agora
                or _utc(registro.ultimo_uso_em) + INATIVIDADE <= agora):
            raise NaoAutenticado("Sessão expirada ou inválida. Entre novamente.")
        if exigir_csrf and (not csrf or not tokens.confere(csrf, registro.csrf_sha256)):
            raise CsrfInvalido("Cabeçalho anti-CSRF ausente ou inválido.")
        usuario = self.db.get(Usuario, registro.usuario_id)
        if usuario is None or usuario.status != "ativo":
            raise NaoAutenticado("Conta indisponível.")
        if agora - _utc(registro.ultimo_uso_em) >= INTERVALO_TOQUE:
            registro.ultimo_uso_em = agora
        return Autenticado(ator=carregar_ator(self.db, usuario), usuario=usuario, sessao=registro)

    def eu(self, autenticado: Autenticado) -> Tuple[Dict[str, Any], str]:
        """Dados do usuário + CSRF novo (o anterior deixa de valer)."""
        csrf = tokens.novo_token()
        autenticado.sessao.csrf_sha256 = tokens.sha256(csrf)
        self.db.flush()
        return _usuario_publico(autenticado.usuario), csrf

    def sair(self, autenticado: Autenticado) -> None:
        autenticado.sessao.revogada_em = _agora()
        self.db.flush()

    def sair_de_todos(self, autenticado: Autenticado) -> int:
        resultado = self.db.execute(update(Sessao).where(Sessao.usuario_id == autenticado.usuario.id,
                                                         Sessao.revogada_em.is_(None))
                                    .values(revogada_em=_agora()))
        self.db.flush()
        return int(resultado.rowcount or 0)

    # --- histórico pessoal (RQ-DAD-05) ----------------------------------------------
    def historico(self, autenticado: Autenticado, limite: int = 20, pagina: int = 1) -> Dict[str, Any]:
        filtro = ExecucaoCalculo.usuario_id == autenticado.usuario.id
        total = self.db.scalar(select(func.count()).select_from(ExecucaoCalculo).where(filtro)) or 0
        itens = self.db.scalars(select(ExecucaoCalculo).where(filtro)
                                .order_by(ExecucaoCalculo.criado_em.desc(), ExecucaoCalculo.id)
                                .limit(limite).offset((pagina - 1) * limite))
        return {"total": total, "pagina": pagina, "limite": limite, "itens": [
            {"id": str(e.id), "operacao": e.operacao, "motor": e.motor_codigo, "versao_motor": e.motor_versao,
             "versao_dados": e.versao_dados, "classe": e.classe_resultado, "parametros": e.parametros,
             "criado_em": _utc(e.criado_em).isoformat(timespec="seconds")} for e in itens]}
