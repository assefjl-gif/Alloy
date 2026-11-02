"""Camada de acesso a dados (preparação para DB-01 / DB-05 / DB-08).

O motor não lê mais dicionários globais: ele recebe um objeto que segue o
protocolo ``RepositorioMateriais``. Hoje a implementação é ``RepositorioJSON``
(seed versionado em ``core/dados/metais.json``). Quando o banco (PostgreSQL +
SQLAlchemy) entrar, basta criar outra classe com os mesmos métodos e injetá-la
em ``create_app(repositorio=...)`` — motor, API e UI não mudam.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable

from .erros import ErroDeDados
from .estruturas import ESTRUTURAS, normalizar_estrutura, sem_acentos

CAMINHO_PADRAO = Path(__file__).with_name("dados") / "metais.json"
CAMINHO_INTERPRETACOES = Path(__file__).with_name("dados") / "interpretacoes.json"


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


def _numero(bruto: Any, campo: str, simbolo: str, obrigatorio: bool = True) -> Optional[float]:
    if bruto is None:
        if obrigatorio:
            raise ErroDeDados(f"metais.json: '{simbolo}' sem o campo obrigatório '{campo}'.")
        return None
    if isinstance(bruto, bool) or not isinstance(bruto, (int, float)) or bruto <= 0:
        raise ErroDeDados(f"metais.json: '{simbolo}.{campo}' deve ser número positivo (recebido {bruto!r}).")
    return float(bruto)


class RepositorioJSON:
    """Repositório somente-leitura carregado de um seed JSON validado na carga."""

    def __init__(self, caminho: Path = CAMINHO_PADRAO,
                 caminho_interpretacoes: Path = CAMINHO_INTERPRETACOES) -> None:
        try:
            bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
            textos = json.loads(Path(caminho_interpretacoes).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ErroDeDados(f"Não foi possível ler os dados do CrystaLab: {exc}") from exc

        self.versao_dados: str = str(bruto.get("versao_dados", "desconhecida"))
        self._fontes: Dict[str, Mapping[str, Any]] = dict(bruto.get("fontes") or {})
        self._textos: Dict[str, Dict[str, List[str]]] = textos
        self._metais: Dict[str, Metal] = {}
        self._por_simbolo_minusculo: Dict[str, str] = {}
        self._por_alias: Dict[str, str] = {}

        for registro in bruto.get("metais") or []:
            metal = self._validar(registro)
            if metal.simbolo in self._metais:
                raise ErroDeDados(f"metais.json: símbolo duplicado '{metal.simbolo}'.")
            self._metais[metal.simbolo] = metal

        # Índices construídos UMA vez (DB-05: antes era busca linear a cada consulta).
        for simbolo in self._metais:
            self._por_simbolo_minusculo[simbolo.lower()] = simbolo
        for simbolo, metal in self._metais.items():
            for alias in (*metal.aliases, metal.nome):
                chave = sem_acentos(alias)
                anterior = self._por_alias.get(chave)
                if anterior and anterior != simbolo:
                    raise ErroDeDados(f"metais.json: alias '{alias}' usado por {anterior} e {simbolo}.")
                self._por_alias[chave] = simbolo

        for estrutura in ESTRUTURAS:
            if estrutura not in self._textos.get("pt-BR", {}):
                raise ErroDeDados(f"interpretacoes.json: faltam textos pt-BR para {estrutura}.")

    def _validar(self, registro: Mapping[str, Any]) -> Metal:
        simbolo = str(registro.get("simbolo") or "").strip()
        if not simbolo or not simbolo[0].isupper() or len(simbolo) > 3:
            raise ErroDeDados(f"metais.json: símbolo inválido {simbolo!r}.")
        estrutura = normalizar_estrutura(registro.get("estrutura"))
        if not estrutura:
            raise ErroDeDados(f"metais.json: '{simbolo}' com estrutura desconhecida {registro.get('estrutura')!r}.")
        fonte = registro.get("fonte")
        for chave in (fonte, registro.get("fonte_rede")):
            if chave is not None and chave not in self._fontes:
                raise ErroDeDados(f"metais.json: '{simbolo}' cita fonte inexistente {chave!r}.")
        c_a = _numero(registro.get("c_a"), "c_a", simbolo, obrigatorio=False)
        a_nm = _numero(registro.get("a_nm"), "a_nm", simbolo, obrigatorio=False)
        c_nm = _numero(registro.get("c_nm"), "c_nm", simbolo, obrigatorio=False)
        if estrutura != "HC" and (c_a is not None or c_nm is not None):
            raise ErroDeDados(f"metais.json: '{simbolo}' é {estrutura} e não pode ter c/a ou c.")
        if c_nm is not None and a_nm is None:
            raise ErroDeDados(f"metais.json: '{simbolo}' tem c_nm sem a_nm.")
        if c_a is not None and a_nm is not None and c_nm is not None and abs(c_nm / a_nm - c_a) > 0.01:
            raise ErroDeDados(f"metais.json: '{simbolo}' com c/a ({c_a}) incoerente "
                              f"com c/a medidos ({c_nm / a_nm:.4f}).")
        return Metal(
            simbolo=simbolo,
            nome=str(registro.get("nome") or simbolo),
            estrutura=estrutura,
            raio_nm=_numero(registro.get("raio_nm"), "raio_nm", simbolo) or 0.0,
            peso_g_mol=_numero(registro.get("peso_g_mol"), "peso_g_mol", simbolo) or 0.0,
            densidade_exp_g_cm3=_numero(registro.get("densidade_exp_g_cm3"), "densidade_exp_g_cm3",
                                        simbolo, obrigatorio=False),
            c_a=c_a, a_nm=a_nm, c_nm=c_nm,
            aliases=tuple(sem_acentos(a) for a in registro.get("aliases") or []),
            fonte=fonte, fonte_rede=registro.get("fonte_rede"),
        )

    # --- protocolo -----------------------------------------------------------------
    def listar(self) -> Sequence[Metal]:
        return tuple(self._metais.values())

    def obter(self, simbolo: str) -> Optional[Metal]:
        return self._metais.get(simbolo)

    def buscar(self, texto: str) -> Optional[Metal]:
        """Busca por símbolo exato, depois símbolo sem caixa, depois aliases/nome."""
        alvo = (texto or "").strip()
        if not alvo:
            return None
        if alvo in self._metais:
            return self._metais[alvo]
        simbolo = self._por_simbolo_minusculo.get(alvo.lower()) or self._por_alias.get(sem_acentos(alvo))
        return self._metais.get(simbolo) if simbolo else None

    def fonte(self, chave: Optional[str]) -> Optional[Mapping[str, Any]]:
        return self._fontes.get(chave) if chave else None

    def interpretacoes(self, estrutura: str, locale: str = "pt-BR") -> List[str]:
        textos = self._textos.get(locale) or self._textos["pt-BR"]
        return list(textos.get(estrutura, []))


@lru_cache(maxsize=1)
def repositorio_padrao() -> RepositorioJSON:
    """Instância compartilhada do seed embutido (carregada e validada uma única vez)."""
    return RepositorioJSON()
