"""Cache, por processo, dos retratos de dados científicos lidos do banco (auditoria de latência, ADR-018).

Antes: cada requisição remontava o retrato inteiro (5 consultas + leitura de ``interpretacoes.json`` para o
``RepositorioSQL``; 3 consultas + montagem de 763 valores para a tabela periódica). Agora o retrato é montado
uma vez e reutilizado enquanto for válido. Cada requisição faz UMA consulta curta (``versoes_dados``) para
conferir a versão dos conjuntos.

Quando o retrato deixa de valer:
* a versão de algum conjunto em ``versoes_dados`` mudou (seed recarregado, em qualquer processo);
* um commit NESTE processo gravou linhas científicas (valores, materiais, estruturas, elementos, fontes,
  propriedades atômicas) — ex.: validação de um valor por um revisor (ADR-014);
* passou ``TTL_SEGUNDOS`` — limite superior de defasagem para mudanças feitas por OUTRO processo/worker
  sem trocar a versão (ex.: validação em outro worker ou SQL manual).

Os retratos são imutáveis depois de montados (só leitura), então podem ser compartilhados entre threads.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, Hashable, Tuple, TypeVar

from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.models import (
    Elemento,
    Estrutura,
    Fonte,
    Material,
    MaterialEstrutura,
    Propriedade,
    PropriedadeElemento,
    ValorPropriedade,
    VersaoDados,
)

TTL_SEGUNDOS = 60.0
MODELOS_CIENTIFICOS = (Elemento, Estrutura, Fonte, Material, MaterialEstrutura, Propriedade, PropriedadeElemento,
                       ValorPropriedade, VersaoDados)
T = TypeVar("T")


class CacheRetratos:
    def __init__(self, ttl: float = TTL_SEGUNDOS) -> None:
        self.ttl = ttl
        self._itens: Dict[Hashable, Tuple[float, Any]] = {}
        self._geracao = 0
        self._trava = threading.Lock()
        self.acertos = 0
        self.faltas = 0

    def obter(self, chave: Hashable, montar: Callable[[], T]) -> T:
        agora = time.monotonic()
        with self._trava:
            item = self._itens.get(chave)
            if item is not None and agora - item[0] < self.ttl:
                self.acertos += 1
                return item[1]
            geracao = self._geracao
            self.faltas += 1
        valor = montar()   # fora da trava: montar consulta o banco
        with self._trava:
            if geracao == self._geracao:   # ninguém invalidou enquanto montávamos
                self._itens[chave] = (agora, valor)
        return valor

    def invalidar(self) -> None:
        with self._trava:
            self._itens.clear()
            self._geracao += 1


cache_retratos = CacheRetratos()


def chave_retrato(sessao: Session, tipo: str) -> Tuple[Any, str, Tuple[Tuple[str, str], ...]]:
    """Banco + tipo de retrato + versões de todos os conjuntos (uma consulta curta)."""
    versoes = tuple(sorted((c, v) for c, v in sessao.execute(select(VersaoDados.conjunto, VersaoDados.versao))))
    return (sessao.get_bind(), tipo, versoes)


@event.listens_for(Session, "after_flush")
def _marcar_mudanca_cientifica(sessao: Session, _contexto: Any) -> None:
    if any(isinstance(obj, MODELOS_CIENTIFICOS) for obj in (*sessao.new, *sessao.dirty, *sessao.deleted)):
        sessao.info["retratos_sujos"] = True


@event.listens_for(Session, "after_commit")
def _invalidar_apos_commit(sessao: Session) -> None:
    if sessao.info.pop("retratos_sujos", False):
        cache_retratos.invalidar()


@event.listens_for(Session, "after_rollback")
def _descartar_marca(sessao: Session) -> None:
    sessao.info.pop("retratos_sujos", None)
