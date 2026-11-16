"""Leitor da matriz de entalpias de mistura por par do HEA (auditoria R1-HEA-01, seção 2.4.5).

Formato esperado (seed sugerido: ``database/seeds/hea/entalpias_binarias.json``)::

    {"versao_dados": "...", "grandeza": "...", "unidade": "kJ/mol",
     "fontes": {"chave": {"citacao": "...", ...}},
     "pares": [{"a": "Co", "b": "Cr", "valor": <número>, "unidade": "kJ/mol",
                "estado": "aguardando_validacao", "fonte": "chave", "origem": "..."}]}

Arquivo AUSENTE ou sem pares = nenhuma matriz: todo par devolve ``None`` e o motor deixa ΔH_mix e Ω
indisponíveis, com o motivo. Nesta rodada (R1) o arquivo NÃO existe no repositório: nenhum valor de
entalpia binária foi cadastrado (questão Q-01 aberta; decisão D-1.3 do portão G1).

Regras de carga (violação = ``ErroDeDados``): par não ordenado e único, com ``a < b`` em ordem alfabética;
``a`` e ``b`` existem na tabela periódica; valor finito em kJ/mol; estado conhecido; ``validado`` exige
fonte; fonte citada existe em ``fontes``. Pares ausentes NÃO são preenchidos e não há diagonal.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Collection, Dict, Mapping, Optional, Tuple

from app.engines.crystallography.erros import ErroDeDados
from app.engines.hea.referencia import CODIGO_PAR, UNIDADE_PAR, chave_par, rotulo_par
from app.engines.procedencia import ESTADOS, ValorReferencia

from .identidade_elementos import identidades_padrao
from .materiais_json import PASTA_SEEDS

CAMINHO_ENTALPIAS = PASTA_SEEDS.parent / "hea" / "entalpias_binarias.json"


class RepositorioEntalpiasMemoria:
    """Matriz de pares já validada, em memória. Cumpre ``RepositorioEntalpias`` do motor HEA."""

    def __init__(self, bruto: Optional[Mapping[str, Any]] = None, *, simbolos: Optional[Collection[str]] = None,
                 origem: str = "entalpias_binarias.json") -> None:
        self.versao_dados: Optional[str] = None
        self._pares: Dict[Tuple[str, str], ValorReferencia] = {}
        self._fontes: Dict[str, Mapping[str, Any]] = {}
        if not bruto:
            return
        if not isinstance(bruto, Mapping):
            raise ErroDeDados(f"{origem}: o conteúdo deve ser um objeto JSON.")
        registros = bruto.get("pares") or []
        if not registros:
            return
        unidade_arquivo = bruto.get("unidade")
        if unidade_arquivo != UNIDADE_PAR:
            raise ErroDeDados(f"{origem}: unidade deve ser '{UNIDADE_PAR}' (recebido {unidade_arquivo!r}).")
        self.versao_dados = str(bruto.get("versao_dados") or "desconhecida")
        self._fontes = dict(bruto.get("fontes") or {})
        for registro in registros:
            self._adicionar(registro, simbolos, origem)

    def _adicionar(self, registro: Mapping[str, Any], simbolos: Optional[Collection[str]], origem: str) -> None:
        a, b = str(registro.get("a") or ""), str(registro.get("b") or "")
        if not a or not b or a == b:
            raise ErroDeDados(f"{origem}: par inválido ({a!r}, {b!r}); não há valor na diagonal.")
        if a > b:
            raise ErroDeDados(f"{origem}: par '{a}-{b}' fora de ordem alfabética (use '{b}-{a}').")
        if simbolos is not None and (a not in simbolos or b not in simbolos):
            raise ErroDeDados(f"{origem}: par '{a}-{b}' cita símbolo que não existe na tabela periódica.")
        if (a, b) in self._pares:
            raise ErroDeDados(f"{origem}: par duplicado '{a}-{b}'.")
        valor = registro.get("valor")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
            raise ErroDeDados(f"{origem}: valor do par '{a}-{b}' deve ser número finito (recebido {valor!r}).")
        if registro.get("unidade", UNIDADE_PAR) != UNIDADE_PAR:
            raise ErroDeDados(f"{origem}: par '{a}-{b}' com unidade diferente de '{UNIDADE_PAR}'.")
        estado = registro.get("estado")
        if estado not in ESTADOS:
            raise ErroDeDados(f"{origem}: estado inválido {estado!r} no par '{a}-{b}'.")
        fonte = registro.get("fonte")
        if estado == "validado" and not fonte:
            raise ErroDeDados(f"{origem}: par validado sem fonte ('{a}-{b}').")
        if fonte is not None and fonte not in self._fontes:
            raise ErroDeDados(f"{origem}: par '{a}-{b}' cita fonte inexistente {fonte!r}.")
        self._pares[(a, b)] = ValorReferencia(simbolo=rotulo_par(a, b), codigo=CODIGO_PAR, valor=float(valor),
                                              unidade=UNIDADE_PAR, estado=str(estado), fonte=fonte)

    # --- RepositorioEntalpias ----------------------------------------------------
    def entalpia_par(self, a: str, b: str) -> Optional[ValorReferencia]:
        return self._pares.get(chave_par(a, b))

    def resumo(self) -> Dict[str, Any]:
        """Situação da matriz para o bootstrap. ``fonte``/``estado`` só são texto único se todos os pares coincidem."""
        if not self._pares:
            return {"disponivel": False, "n_pares": 0, "fonte": None, "estado": None}
        fontes = sorted({p.fonte for p in self._pares.values() if p.fonte})
        estados = sorted({p.estado for p in self._pares.values()})
        return {"disponivel": True, "n_pares": len(self._pares),
                "fonte": ", ".join(fontes) if fontes else None,
                "estado": estados[0] if len(estados) == 1 else "misto"}


def carregar_entalpias(caminho: Path = CAMINHO_ENTALPIAS) -> RepositorioEntalpiasMemoria:
    """Arquivo ausente ou vazio → repositório sem pares (não é erro: a matriz ainda não foi cadastrada)."""
    caminho = Path(caminho)
    if not caminho.exists():
        return RepositorioEntalpiasMemoria()
    try:
        texto = caminho.read_text(encoding="utf-8")
    except OSError as exc:
        raise ErroDeDados(f"Não foi possível ler {caminho.name}: {exc}") from exc
    if not texto.strip():
        return RepositorioEntalpiasMemoria()
    try:
        bruto = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ErroDeDados(f"{caminho.name}: JSON inválido: {exc}") from exc
    return RepositorioEntalpiasMemoria(bruto, simbolos=set(identidades_padrao()), origem=caminho.name)


@lru_cache(maxsize=1)
def entalpias_padrao() -> RepositorioEntalpiasMemoria:
    return carregar_entalpias()
