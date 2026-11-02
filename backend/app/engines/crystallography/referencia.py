"""Contrato de dados de referência do motor cristalográfico (puro, sem I/O — ADR-004).

Origem: CrystaLab v1.1.0 ``core/repositorio.py``. O carregador JSON foi para
``app/repositories/materiais_json.py`` e o carregador PostgreSQL para
``app/repositories/materiais_sql.py``: ambos cumprem ``RepositorioMateriais``.

Texto original do módulo:

O motor não lê mais dicionários globais: ele recebe um objeto que segue o
protocolo ``RepositorioMateriais``. Hoje a implementação é ``RepositorioJSON``
(seed versionado em ``core/dados/metais.json``). Quando o banco (PostgreSQL +
SQLAlchemy) entrar, basta criar outra classe com os mesmos métodos e injetá-la
em ``create_app(repositorio=...)`` — motor, API e UI não mudam.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable

from .estruturas import ESTRUTURAS


@dataclass(frozen=True)
class Metal:
    simbolo: str
    nome: str
    estrutura: str
    raio_nm: float
    peso_g_mol: float
    densidade_exp_g_cm3: Optional[float] = None
    c_a: Optional[float] = None
    a_nm: Optional[float] = None
    c_nm: Optional[float] = None
    aliases: Tuple[str, ...] = field(default_factory=tuple)
    fonte: Optional[str] = None
    fonte_rede: Optional[str] = None

    @property
    def tem_rede_medida(self) -> bool:
        if self.a_nm is None:
            return False
        return self.estrutura != "HC" or self.c_nm is not None

    @property
    def c_a_efetivo(self) -> Optional[float]:
        """c/a usado no cálculo: c/a medido (c/a = c/a) quando houver rede medida."""
        if self.estrutura != "HC":
            return None
        if self.a_nm is not None and self.c_nm is not None:
            return self.c_nm / self.a_nm
        return self.c_a

    def publico(self) -> Dict[str, Any]:
        """Formato público estável (mesmas chaves da v1.0 + campos novos opcionais)."""
        return {
            "nome": self.nome,
            "estrutura": self.estrutura,
            "raio": self.raio_nm,
            "peso": self.peso_g_mol,
            "densidade_exp": self.densidade_exp_g_cm3,
            "c_a": self.c_a_efetivo,
            "nc": ESTRUTURAS[self.estrutura]["nc"],
            "a_nm": self.a_nm,
            "c_nm": self.c_nm,
            "fonte": self.fonte,
        }


@runtime_checkable
class RepositorioMateriais(Protocol):
    """Contrato mínimo que qualquer fonte de dados deve cumprir."""

    versao_dados: str

    def listar(self) -> Sequence[Metal]: ...

    def obter(self, simbolo: str) -> Optional[Metal]: ...

    def buscar(self, texto: str) -> Optional[Metal]: ...

    def fonte(self, chave: Optional[str]) -> Optional[Mapping[str, Any]]: ...

    def interpretacoes(self, estrutura: str, locale: str = "pt-BR") -> List[str]: ...
