"""Casos de uso de cálculo científico (ARQUITETURA_FINAL §2 e §5, Fluxos A e B).

O serviço: injeta dados de referência e política nos motores, completa a ``procedencia``
(data e hora são do serviço, não do motor puro) e, havendo usuário e sessão de banco,
registra a execução em ``execucoes_calculo`` (histórico pessoal, RQ-DAD/HEA-05).
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, Mapping, Optional

from sqlalchemy.orm import Session

from app.engines.crystallography import (
    ESTRUTURAS,
    VERSAO_MOTOR,
    EntradaInvalida,
    calcular_densidade,
    calcular_estrutura,
    calcular_miller,
    gerar_cif,
    gerar_xyz,
    metais_publicos,
    normalizar_estrutura,
    tabela_estruturas,
)
from app.engines.crystallography.geometria import arredondar, vetores_de_rede
from app.engines.crystallography.ligas import calcular_solucao_solida
from app.engines.crystallography.ligas_entrada import EntradaLigaInvalida
from app.engines.crystallography.referencia import RepositorioMateriais
from app.engines.crystallography.supercelula import geometria_supercelula
from app.engines.hea.analitico import VERSAO_MOTOR as VERSAO_HEA
from app.engines.hea.analitico import analisar_liga
from app.engines.hea.analitico import catalogo as catalogo_hea
from app.engines.hea.referencia import Identidades, RepositorioEntalpias
from app.engines.procedencia import (
    ColetorDados,
    PoliticaDados,
    RepositorioPropriedades,
    bloco_procedencia,
    sha256_parametros,
)
from app.engines.thermodynamics.termico import VERSAO_MOTOR as VERSAO_TERMICO
from app.engines.thermodynamics.termico import calcular_termico
from app.repositories.entalpias_json import entalpias_padrao
from app.repositories.execucoes import registrar_execucao
from app.repositories.identidade_elementos import identidades_padrao

logger = logging.getLogger("alloy.historico")

AVISO_HISTORICO_NAO_GRAVADO = ("O resultado foi calculado, mas não foi possível gravá-lo no seu histórico "
                               "pessoal. O cálculo é válido; o registro não ficou salvo.")

AVISO_SEED_BASE = ("Raio, massa atômica e densidade experimental vêm do seed da v1.1.0 e aguardam validação "
                   "(citação do Callister sem edição e página — CR-10).")


def versoes_motores() -> Dict[str, str]:
    return {"crystallography": VERSAO_MOTOR, "thermodynamics": VERSAO_TERMICO, "hea": VERSAO_HEA}


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _recusar_liga_multicomponente(liga: Mapping[str, Any]) -> None:
    """R1 (decisão D-a): o motor térmico não foi especificado para liga com mais de um soluto.

    Em vez de usar só o primeiro soluto em silêncio, a rota recusa o pedido.
    """
    solutos = liga.get("solutos")
    if isinstance(solutos, (list, tuple)) and len(solutos) > 1:
        raise EntradaLigaInvalida([{
            "loc": ["liga", "solutos"], "type": "liga_multicomponente_nao_suportada",
            "msg": "O cálculo térmico não suporta liga com mais de um soluto: o modelo de dilatação e de "
                   "vibração foi especificado para solvente + um soluto. Informe um único soluto.",
        }])


def _json_seguro(valor: Any) -> Any:
    """Torna o resultado serializável em JSON/JSONB (tuplas viram listas)."""
    if isinstance(valor, dict):
        return {str(k): _json_seguro(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(v) for v in valor]
    return valor


class ServicoCalculo:
    def __init__(self, repo: RepositorioMateriais, props: RepositorioPropriedades, politica: PoliticaDados,
                 sessao: Optional[Session] = None, *, identidades: Optional[Identidades] = None,
                 entalpias: Optional[RepositorioEntalpias] = None) -> None:
        self.repo = repo
        self.props = props
        self.politica = politica
        self.sessao = sessao
        # HEA (R1): identidade dos 118 elementos (só símbolos e classificação) e matriz de entalpias por par.
        # Sem injeção, valem os leitores padrão; a matriz padrão está vazia (arquivo de seed inexistente).
        self._identidades = identidades
        self._entalpias = entalpias

    # --- casos de uso --------------------------------------------------------------
    def celula(self, payload: Mapping[str, Any], usuario_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        def executar() -> Dict[str, Any]:
            # QA-R2-02: o coletor registra os dados do repositório que entram no cálculo (raio, massa,
            # a/c medidos, c/a tabelado, densidade experimental) em ``procedencia.dados_usados``.
            coletor = ColetorDados(self.politica)
            resultado = calcular_estrutura(payload, self.repo, coletor)
            fontes = [resultado["fonte"]] if resultado.get("fonte") else []
            avisos = [AVISO_SEED_BASE] if resultado.get("simbolo") and not resultado.get("editado") else []
            resultado["procedencia"] = bloco_procedencia(
                classe="analitico", motor="crystallography", versao_motor=VERSAO_MOTOR,
                versao_dados=self.repo.versao_dados, parametros=dict(payload), coletor=coletor,
                fontes_modelo=fontes, avisos=avisos)
            return resultado
        return self._executar("celula", "crystallography", VERSAO_MOTOR, payload, usuario_id, executar)

    def miller(self, payload: Mapping[str, Any], usuario_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        def executar() -> Dict[str, Any]:
            resultado = calcular_miller(payload)
            resultado["procedencia"] = bloco_procedencia(
                classe="analitico", motor="crystallography", versao_motor=VERSAO_MOTOR,
                versao_dados=self.repo.versao_dados, parametros=dict(payload))
            return resultado
        return self._executar("miller", "crystallography", VERSAO_MOTOR, payload, usuario_id, executar)

    def solucao_solida(self, payload: Mapping[str, Any], usuario_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        return self._executar("solucao_solida", "crystallography", VERSAO_MOTOR, payload, usuario_id,
                              lambda: calcular_solucao_solida(payload, self.repo, self.props, self.politica))

    def termico(self, payload: Mapping[str, Any], usuario_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """``payload``: {material: "Fe", temperatura_c} ou {liga: {...payload de solução sólida...}, temperatura_c}."""
        def executar() -> Dict[str, Any]:
            temperatura = payload.get("temperatura_c")
            if payload.get("liga"):
                _recusar_liga_multicomponente(payload["liga"])
                liga = calcular_solucao_solida(payload["liga"], self.repo, self.props, self.politica)
                x = float(liga["x_pct"]) / 100.0
                if liga["intersticial"]:
                    # A rede é a do solvente: vizinhos a 2R do solvente; α e T_f do solvente.
                    d_nn = 2.0 * liga["raio_relativo"] * liga["a_nm"]
                    mistura = [[liga["base"], 1.0]]
                else:
                    # Vegard: a = k·R̄ → vizinhos a 2R̄; α e T_f pela regra das misturas.
                    d_nn = 2.0 * liga["a_nm"] / float(ESTRUTURAS[liga["estrutura"]]["a_em_R"])
                    mistura = [[liga["base"], 1.0 - x], [liga["soluto"], x]]
                entrada = {"simbolo": liga["base"], "estrutura": liga["estrutura"], "a_nm": liga["a_nm"],
                           "d_nn_nm": d_nn, "densidade": liga["densidade"], "temperatura_c": temperatura,
                           "mistura": mistura}
            else:
                celula = calcular_estrutura({"nome": payload.get("material")}, self.repo)
                entrada = {"simbolo": celula["simbolo"], "estrutura": celula["estrutura"], "a_nm": celula["a_nm"],
                           "d_nn_nm": 2 * celula["raio_nm"], "densidade": celula["densidade"],
                           "temperatura_c": temperatura}
            return calcular_termico(entrada, self.props, self.politica)
        return self._executar("termico", "thermodynamics", VERSAO_TERMICO, payload, usuario_id, executar)

    def hea(self, payload: Mapping[str, Any], usuario_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        return self._executar("hea_analise", "hea", VERSAO_HEA, payload, usuario_id,
                              lambda: analisar_liga(payload, self.repo, self.props, self.politica,
                                                    identidades=self._identidades_hea(),
                                                    entalpias=self._entalpias_hea()))

    def hea_catalogo(self) -> Dict[str, Any]:
        return catalogo_hea(self.repo, self.props, self.politica, identidades=self._identidades_hea(),
                            entalpias=self._entalpias_hea())

    def _identidades_hea(self) -> Identidades:
        return self._identidades if self._identidades is not None else identidades_padrao()

    def _entalpias_hea(self) -> RepositorioEntalpias:
        return self._entalpias if self._entalpias is not None else entalpias_padrao()

    def densidade(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        # QA-R2-02: a densidade usa os mesmos dados do repositório que ``/cells`` e passa a declarar a
        # procedência (bloco aditivo; a data e hora são do serviço, como nas demais rotas).
        coletor = ColetorDados(self.politica)
        resultado = calcular_densidade(payload, self.repo, coletor)
        avisos = [AVISO_SEED_BASE] if resultado.get("simbolo") and not resultado.get("editado") else []
        resultado["procedencia"] = bloco_procedencia(
            classe="analitico", motor="crystallography", versao_motor=VERSAO_MOTOR,
            versao_dados=self.repo.versao_dados, parametros=dict(payload), coletor=coletor, avisos=avisos)
        resultado["procedencia"]["calculado_em"] = _agora_iso()
        return resultado

    def supercelula(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        estrutura = normalizar_estrutura(str(payload.get("estrutura") or ""))
        if not estrutura:
            raise EntradaInvalida("Estrutura desconhecida. Use CS, CCC, CFC ou HC.")
        n = payload.get("n") or 2
        c_a = payload.get("c_a") if estrutura == "HC" else None
        if estrutura == "HC" and c_a is None:
            c_a = float(ESTRUTURAS["HC"]["c_a_ideal"])
        atomos, arestas = geometria_supercelula(estrutura, c_a, n)
        return {"estrutura": estrutura, "n": n, "c_a": c_a,
                "atomos": [{"pos": arredondar(a["pos"]), "frac": arredondar(a["frac"]), "tipo": a["tipo"]}
                           for a in atomos],
                "arestas": [[arredondar(p) for p in aresta] for aresta in arestas],
                "vetores_rede": [arredondar(v) for v in vetores_de_rede(estrutura, 1.0, c_a)]}

    def exportar(self, formato: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return gerar_cif(payload, self.repo) if formato == "cif" else gerar_xyz(payload, self.repo)

    def metais(self) -> Dict[str, Dict[str, Any]]:
        return metais_publicos(self.repo)

    @staticmethod
    def estruturas() -> list:
        return tabela_estruturas()

    def versao_dados(self) -> str:
        return self.repo.versao_dados

    def quantidade_materiais(self) -> int:
        return len(self.repo.listar())

    # --- infraestrutura --------------------------------------------------------------
    def _executar(self, operacao: str, motor: str, versao: str, payload: Mapping[str, Any],
                  usuario_id: Optional[uuid.UUID], executar: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        inicio = time.perf_counter()
        resultado = executar()
        duracao_ms = (time.perf_counter() - inicio) * 1000.0
        resultado["procedencia"]["calculado_em"] = _agora_iso()
        if self.sessao is not None and usuario_id is not None:
            self._gravar_historico(operacao, motor, versao, payload, usuario_id, resultado, duracao_ms)
        return resultado

    def _gravar_historico(self, operacao: str, motor: str, versao: str, payload: Mapping[str, Any],
                          usuario_id: uuid.UUID, resultado: Dict[str, Any], duracao_ms: float) -> None:
        """Efeito secundário do cálculo (R2-BE-03): falhar aqui NÃO pode derrubar o resultado científico.

        O resultado já foi calculado e é devolvido ao usuário de qualquer modo. Uma falha de gravação vai
        para o log (com a operação e a causa, sem dados pessoais) e gera um aviso em ``procedencia.avisos``
        — campo já existente no contrato —, para o usuário não supor que o cálculo está no histórico.
        """
        sessao = self.sessao
        if sessao is None:   # chamado só pelo ramo com sessão; guarda defensiva (sem efeito silencioso)
            return
        erro = registrar_execucao(
            sessao, usuario_id=usuario_id, motor_codigo=motor, motor_versao=versao,
            versao_dados=resultado["procedencia"]["versao_dados"], operacao=operacao,
            parametros=_json_seguro(dict(payload)),
            parametros_sha256=bytes.fromhex(sha256_parametros(payload)),
            resultado=_json_seguro(resultado), classe_resultado=resultado["procedencia"]["classe"],
            duracao_ms=Decimal(f"{duracao_ms:.3f}"))
        if erro is not None:
            logger.error("histórico não gravado (operacao=%s motor=%s/%s): %s", operacao, motor, versao,
                         type(erro).__name__, exc_info=erro)
            resultado["procedencia"]["avisos"].append(AVISO_HISTORICO_NAO_GRAVADO)
