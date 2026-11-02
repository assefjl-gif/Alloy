"""Repositório de materiais lido de seed JSON (camada repositories — pode fazer I/O).

Usos: testes do motor, ambiente sem banco e geração do seed do PostgreSQL.
Origem: CrystaLab v1.1.0 ``core/repositorio.py`` (``RepositorioJSON``), sem mudança de regra.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from app.engines.crystallography.erros import ErroDeDados
from app.engines.crystallography.estruturas import ESTRUTURAS, normalizar_estrutura, sem_acentos
from app.engines.crystallography.referencia import Metal
from app.engines.procedencia import ESTADOS, TransicaoAlotropica, ValorReferencia

PASTA_SEEDS = Path(__file__).resolve().parents[3] / "database" / "seeds" / "cristalografia"
CAMINHO_PADRAO = PASTA_SEEDS / "metais.json"
CAMINHO_INTERPRETACOES = PASTA_SEEDS / "interpretacoes.json"
CAMINHO_PROPRIEDADES = PASTA_SEEDS / "propriedades_v14.json"


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
                 caminho_interpretacoes: Path = CAMINHO_INTERPRETACOES,
                 caminho_propriedades: Optional[Path] = CAMINHO_PROPRIEDADES) -> None:
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

        self._carregar_propriedades(caminho_propriedades)

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

    # --- RepositorioPropriedades (dados introduzidos pela v1.4) ----------------------
    def _carregar_propriedades(self, caminho: Optional[Path]) -> None:
        self._valores: Dict[tuple, ValorReferencia] = {}
        self._intersticiais: Dict[str, Mapping[str, Any]] = {}
        self._transicoes: Dict[str, List[TransicaoAlotropica]] = {}
        if caminho is None:
            return
        try:
            bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ErroDeDados(f"Não foi possível ler {Path(caminho).name}: {exc}") from exc
        # Mesma convenção do repositório SQL: versão do seed base + versão do seed da v1.4.
        self.versao_dados = f"{self.versao_dados}+{bruto.get('versao_dados', 'desconhecida')}"
        for registro in bruto.get("valores") or []:
            estado = registro.get("estado")
            if estado not in ESTADOS:
                raise ErroDeDados(f"{Path(caminho).name}: estado inválido {estado!r}.")
            if estado == "validado" and not registro.get("fonte"):
                raise ErroDeDados(f"{Path(caminho).name}: valor validado sem fonte ({registro.get('simbolo')}).")
            chave = (registro["simbolo"], registro["codigo"])
            if chave in self._valores:
                raise ErroDeDados(f"{Path(caminho).name}: valor duplicado {chave}.")
            self._valores[chave] = ValorReferencia(
                simbolo=registro["simbolo"], codigo=registro["codigo"], valor=float(registro["valor"]),
                unidade=registro["unidade"], estado=estado, fonte=registro.get("fonte"))
        for registro in bruto.get("intersticiais") or []:
            self._intersticiais[registro["simbolo"]] = registro
        for registro in bruto.get("transicoes_alotropicas") or []:
            self._transicoes.setdefault(registro["simbolo"], []).append(TransicaoAlotropica(
                simbolo=registro["simbolo"], de_c=float(registro["de_c"]), ate_c=float(registro["ate_c"]),
                fase=registro["fase"], estrutura=registro["estrutura"], estado=registro["estado"],
                fonte=registro.get("fonte")))

    def propriedade(self, simbolo: str, codigo: str) -> Optional[ValorReferencia]:
        return self._valores.get((simbolo, codigo))

    def intersticial(self, simbolo: str) -> Optional[Mapping[str, Any]]:
        return self._intersticiais.get(simbolo)

    def buscar_intersticial(self, texto: str) -> Optional[str]:
        alvo = sem_acentos(texto or "")
        for simbolo, dados in self._intersticiais.items():
            if alvo == simbolo.lower() or alvo in dados.get("aliases", []):
                return simbolo
        return None

    def transicoes(self, simbolo: str) -> Sequence[TransicaoAlotropica]:
        return tuple(self._transicoes.get(simbolo, ()))

    def interpretacoes(self, estrutura: str, locale: str = "pt-BR") -> List[str]:
        textos = self._textos.get(locale) or self._textos["pt-BR"]
        return list(textos.get(estrutura, []))


@lru_cache(maxsize=1)
def repositorio_padrao() -> RepositorioJSON:
    """Instância compartilhada do seed embutido (carregada e validada uma única vez)."""
    return RepositorioJSON()
