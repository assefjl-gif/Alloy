"""R2-BE-03 (defeito F-1 da integração): gravar o histórico não pode derrubar o cálculo.

Cenários:
* banco PREEXISTENTE — carregado antes desta rodada, sem a linha de ``motores`` da versão corrente:
  o cálculo autenticado precisa concluir e o motor precisa ser registrado (get-or-create);
* gravação impossível (usuário inexistente, chave estrangeira de ``usuarios``): o resultado científico é
  devolvido, com aviso em ``procedencia.avisos`` e NADA no histórico;
* get-or-create sob concorrência (duas gravações simultâneas da mesma versão);
* ``PRAGMA foreign_keys`` ligado nas conexões SQLite criadas pela aplicação (achado F-2).
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.engines.procedencia import PoliticaDados
from app.models import ExecucaoCalculo, Motor, Usuario
from app.repositories.materiais_sql import RepositorioSQL
from app.repositories.motores import garantir_motor, motores_do_catalogo
from app.repositories.seed_sql import carregar_seeds
from app.services.calculo import AVISO_HISTORICO_NAO_GRAVADO, ServicoCalculo
from app.services.provedor import ativar_chaves_estrangeiras, criar_motor_banco

VERSAO_ANTIGA = "0.0.1-antes-R2"


def _novo_usuario(sessao) -> uuid.UUID:
    usuario = Usuario(nome="Estudante R2", email=f"r2.{uuid.uuid4().hex[:8]}@exemplo.test", status="ativo",
                      email_verificado_em=datetime.now(timezone.utc))
    sessao.add(usuario)
    sessao.commit()
    return usuario.id


def _servico(sessao):
    carregar_seeds(sessao)
    usuario_id = _novo_usuario(sessao)
    repo = RepositorioSQL(sessao)
    return ServicoCalculo(repo, repo, PoliticaDados(permitir_nao_validado=True), sessao), usuario_id


def _simular_banco_preexistente(sessao) -> None:
    """Deixa ``motores`` só com versões ANTIGAS, como um banco carregado antes destas entregas."""
    sessao.execute(delete(Motor))
    for codigo, _versao in motores_do_catalogo():
        sessao.add(Motor(codigo=codigo, versao=VERSAO_ANTIGA))
    sessao.commit()


def test_banco_preexistente_sem_a_versao_corrente_nao_derruba_o_calculo(sessao):
    servico, usuario_id = _servico(sessao)
    _simular_banco_preexistente(sessao)

    resultado = servico.celula({"nome": "Cu"}, usuario_id)
    sessao.commit()

    assert resultado["densidade"] > 0
    assert AVISO_HISTORICO_NAO_GRAVADO not in resultado["procedencia"]["avisos"]
    execucao = sessao.scalars(select(ExecucaoCalculo)).one()
    assert (execucao.operacao, execucao.motor_codigo) == ("celula", "crystallography")
    # a linha do motor da versão corrente foi criada no caminho de gravação (get-or-create)
    assert sessao.get(Motor, ("crystallography", resultado["procedencia"]["versao_motor"])) is not None
    # e a versão antiga continua lá: nada foi apagado
    assert sessao.get(Motor, ("crystallography", VERSAO_ANTIGA)) is not None


@pytest.mark.parametrize(("operacao", "payload"), [
    ("celula", {"nome": "Fe"}),
    ("termico", {"material": "Fe", "temperatura_c": 500}),
    ("hea", {"composicao": {"Co": 1, "Ni": 1}}),
])
def test_todos_os_motores_sao_registrados_em_banco_preexistente(sessao, operacao, payload):
    servico, usuario_id = _servico(sessao)
    _simular_banco_preexistente(sessao)
    resultado = getattr(servico, operacao)(payload, usuario_id)
    sessao.commit()
    execucao = sessao.scalars(select(ExecucaoCalculo)).one()
    assert sessao.get(Motor, (execucao.motor_codigo, execucao.motor_versao)) is not None
    assert resultado["procedencia"]["motor"] == execucao.motor_codigo


def test_falha_de_gravacao_devolve_o_resultado_com_aviso_e_sem_registro(sessao, caplog, monkeypatch):
    """Usuário inexistente: a FK de ``usuarios`` reprova a gravação. Antes de R2-BE-03 isto virava 500."""
    servico, _ = _servico(sessao)
    # O ``fileConfig`` do Alembic (rodado pela fixture de banco) desabilita os loggers já existentes;
    # reabilita só este para poder observar o registro da falha.
    monkeypatch.setattr(logging.getLogger("alloy.historico"), "disabled", False)
    with caplog.at_level(logging.ERROR, logger="alloy.historico"):
        resultado = servico.celula({"nome": "Cu"}, uuid.uuid4())
    sessao.commit()

    assert resultado["densidade"] > 0                      # resultado científico preservado
    assert AVISO_HISTORICO_NAO_GRAVADO in resultado["procedencia"]["avisos"]
    assert sessao.scalars(select(ExecucaoCalculo)).first() is None
    assert any("histórico não gravado" in r.getMessage() for r in caplog.records)
    # a sessão continua utilizável depois da falha (o SAVEPOINT isolou o efeito)
    assert servico.celula({"nome": "Fe"})["densidade"] > 0


def test_get_or_create_do_motor_e_idempotente(sessao):
    carregar_seeds(sessao)
    codigo, versao = "crystallography", VERSAO_ANTIGA
    garantir_motor(sessao, codigo, versao)
    garantir_motor(sessao, codigo, versao)
    sessao.commit()
    assert len(sessao.scalars(select(Motor).where(Motor.versao == versao)).all()) == 1


def test_get_or_create_absorve_corrida_de_outra_transacao(sessao, motor_banco):
    """Outra transação insere a mesma chave entre o SELECT e o INSERT desta: não pode quebrar."""
    carregar_seeds(sessao)
    sessao.commit()
    codigo, versao = "hea", VERSAO_ANTIGA
    assert sessao.get(Motor, (codigo, versao)) is None     # esta transação viu "não existe"
    sessao.commit()                                        # encerra a leitura para não travar o SQLite
    with Session(motor_banco) as outra:                    # concorrente insere e confirma
        garantir_motor(outra, codigo, versao)
        outra.commit()
    garantir_motor(sessao, codigo, versao)                 # não lança: absorve a violação de unicidade
    sessao.commit()
    assert len(sessao.scalars(select(Motor).where(Motor.codigo == codigo,
                                                 Motor.versao == versao)).all()) == 1


def _motor_concorrente(url: str):
    """Engine de teste que suporta dois escritores simultâneos em SQLite.

    WAL + ``busy_timeout`` + ``BEGIN IMMEDIATE``: sem isso o SQLite devolve "database is locked" assim que
    duas transações tentam escrever juntas — limitação do SQLite, não do código sob teste (ver L-01: o
    PostgreSQL de teste não está disponível nesta máquina).
    """
    from sqlalchemy import event as _event
    motor = create_engine(url, connect_args={"timeout": 30, "isolation_level": None})
    ativar_chaves_estrangeiras(motor)

    @_event.listens_for(motor, "connect")
    def _wal(conexao_dbapi, _registro):
        cursor = conexao_dbapi.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
        finally:
            cursor.close()

    @_event.listens_for(motor, "begin")
    def _begin_immediate(conexao):
        conexao.exec_driver_sql("BEGIN IMMEDIATE")

    return motor


def test_gravacoes_simultaneas_da_mesma_versao_nao_quebram(sessao, motor_banco):
    """Duas requisições paralelas gravando histórico com a mesma versão nova de motor."""
    if motor_banco.dialect.name == "sqlite":
        motor_concorrente = _motor_concorrente(str(motor_banco.url))
    else:
        motor_concorrente = motor_banco
    carregar_seeds(sessao)
    ids = [_novo_usuario(sessao) for _ in range(2)]
    _simular_banco_preexistente(sessao)
    sessao.close()

    partida = threading.Barrier(2)
    erros: list[BaseException] = []
    avisos: list[str] = []

    def gravar(usuario_id):
        try:
            partida.wait(timeout=30)   # as duas threads entram juntas na unidade de trabalho
            with Session(motor_concorrente) as s:
                repo = RepositorioSQL(s)
                servico = ServicoCalculo(repo, repo, PoliticaDados(permitir_nao_validado=True), s)
                r = servico.celula({"nome": "Cu"}, usuario_id)
                s.commit()
                avisos.extend(a for a in r["procedencia"]["avisos"] if a == AVISO_HISTORICO_NAO_GRAVADO)
        except BaseException as erro:   # noqa: BLE001 - o teste relata qualquer falha das threads
            erros.append(erro)

    threads = [threading.Thread(target=gravar, args=(i,)) for i in ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    try:
        assert erros == [], [repr(e) for e in erros]
        assert avisos == []                                # as duas gravações concluíram
        with Session(motor_concorrente) as s:
            assert len(s.scalars(select(ExecucaoCalculo)).all()) == 2
            # uma única linha de motor para a versão corrente, apesar das duas inserções simultâneas
            versoes = s.scalars(select(Motor.versao).where(Motor.codigo == "crystallography")).all()
            assert sorted(versoes) == sorted({VERSAO_ANTIGA, dict(motores_do_catalogo())["crystallography"]})
    finally:
        if motor_concorrente is not motor_banco:
            motor_concorrente.dispose()


def test_pragma_foreign_keys_ligado_nas_conexoes_sqlite(tmp_path):
    """F-2: sem o PRAGMA o SQLite não impõe chave estrangeira e o defeito só apareceria em produção."""
    url = f"sqlite:///{tmp_path / 'pragma.db'}"
    motor = criar_motor_banco(Settings(_env_file=None, env="test", database_url=url))
    assert motor is not None
    try:
        for _ in range(2):             # vale em toda conexão nova do pool, não só na primeira
            with motor.connect() as conexao:
                assert conexao.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    finally:
        motor.dispose()


def test_ativar_chaves_estrangeiras_nao_mexe_em_dialeto_sem_pragma():
    motor = create_engine("postgresql+psycopg://u:p@localhost/x")   # não conecta
    ativar_chaves_estrangeiras(motor)                               # no-op: nada a registrar
    motor.dispose()


def test_banco_das_suites_impoe_chaves_estrangeiras(sessao):
    if sessao.bind.dialect.name == "sqlite":
        assert sessao.execute(text("PRAGMA foreign_keys")).scalar() == 1
