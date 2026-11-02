"""Procedência e política de uso de dados de referência, comuns a todos os motores (PI-06, PI-07, ADR-014).

Puro: não lê arquivos nem banco. O serviço injeta um ``RepositorioPropriedades`` e uma
``PoliticaDados``; o motor registra cada valor usado num ``ColetorDados`` e devolve o bloco
``procedencia`` (o serviço só acrescenta ``calculado_em``).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable

from .crystallography.erros import ErroDominio

CLASSES = ("analitico", "estimativa_modelo", "experimental", "simulacao_ilustrativa", "demonstrativo")
ESTADOS = ("rascunho", "aguardando_validacao", "validado", "rejeitado", "arquivado")


class DadoNaoValidado(ErroDominio):
    codigo = "DADO_NAO_VALIDADO"


@dataclass(frozen=True)
class ValorReferencia:
    simbolo: str
    codigo: str
    valor: float
    unidade: str
    estado: str
    fonte: Optional[str] = None

    @property
    def validado(self) -> bool:
        return self.estado == "validado" and self.fonte is not None


@dataclass(frozen=True)
class TransicaoAlotropica:
    simbolo: str
    de_c: float
    ate_c: float
    fase: str
    estrutura: str
    estado: str
    fonte: Optional[str] = None


@runtime_checkable
class RepositorioPropriedades(Protocol):
    """Propriedades além das do ``Metal`` (eletronegatividade, valência, fusão, dilatação, intersticiais)."""

    versao_dados: str

    def propriedade(self, simbolo: str, codigo: str) -> Optional[ValorReferencia]: ...

    def intersticial(self, simbolo: str) -> Optional[Mapping[str, Any]]: ...

    def buscar_intersticial(self, texto: str) -> Optional[str]: ...

    def transicoes(self, simbolo: str) -> Sequence[TransicaoAlotropica]: ...


@dataclass(frozen=True)
class PoliticaDados:
    """``permitir_nao_validado`` é decidido pelo serviço conforme o ambiente (falso em produção)."""

    permitir_nao_validado: bool = False


@dataclass
class ColetorDados:
    politica: PoliticaDados
    usados: List[Dict[str, Any]] = field(default_factory=list)

    def exigir(self, repo: RepositorioPropriedades, simbolo: str, codigo: str, descricao: str) -> float:
        dado = repo.propriedade(simbolo, codigo)
        if dado is None:
            raise DadoNaoValidado(f"Não há {descricao} cadastrado para {simbolo}.")
        if not dado.validado and not self.politica.permitir_nao_validado:
            raise DadoNaoValidado(
                f"{descricao[:1].upper()}{descricao[1:]} de {simbolo} ainda não foi validado com fonte "
                f"(estado: {dado.estado}). Cálculo indisponível neste ambiente.")
        self.registrar(dado)
        return float(dado.valor)

    def opcional(self, repo: RepositorioPropriedades, simbolo: str, codigo: str,
                 descricao: str) -> Tuple[Optional[float], Optional[str]]:
        """Como ``exigir``, mas devolve ``(None, motivo)`` em vez de lançar: para partes dispensáveis."""
        try:
            return self.exigir(repo, simbolo, codigo, descricao), None
        except DadoNaoValidado as erro:
            return None, erro.mensagem

    def registrar(self, dado: ValorReferencia) -> None:
        chave = (dado.simbolo, dado.codigo)
        if not any((u["simbolo"], u["codigo"]) == chave for u in self.usados):
            self.usados.append({"simbolo": dado.simbolo, "codigo": dado.codigo, "valor": dado.valor,
                                "unidade": dado.unidade, "estado": dado.estado, "fonte": dado.fonte})

    def avisos(self) -> List[str]:
        pendentes = sorted({f"{u['codigo']} de {u['simbolo']}" for u in self.usados
                            if u["estado"] != "validado" or u["fonte"] is None})
        if not pendentes:
            return []
        return [f"Dados ainda sem validação usados neste cálculo (ambiente de desenvolvimento): "
                f"{', '.join(pendentes)}. Não use o resultado como referência."]


def sha256_parametros(parametros: Mapping[str, Any]) -> str:
    texto = json.dumps(parametros, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def bloco_procedencia(*, classe: str, motor: str, versao_motor: str, versao_dados: str,
                      parametros: Mapping[str, Any], coletor: Optional[ColetorDados] = None,
                      fontes_modelo: Sequence[str] = (), avisos: Sequence[str] = ()) -> Dict[str, Any]:
    if classe not in CLASSES:
        raise ValueError(f"classe de resultado desconhecida: {classe}")
    usados = list(coletor.usados) if coletor else []
    fontes_dados = sorted({u["fonte"] for u in usados if u["fonte"]})
    return {
        "classe": classe,
        "motor": motor,
        "versao_motor": versao_motor,
        "versao_dados": versao_dados,
        "fontes_modelo": list(fontes_modelo),
        "fontes_dados": fontes_dados,
        "dados_usados": usados,
        "parametros_sha256": sha256_parametros(parametros),
        "avisos": list(avisos) + (coletor.avisos() if coletor else []),
    }
