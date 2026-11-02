"""Casos de uso de cálculo científico (ARQUITETURA_FINAL §2 e §5, Fluxos A e B).

O serviço: injeta dados de referência e política nos motores, completa a ``procedencia``
(data e hora são do serviço, não do motor puro) e, havendo usuário e sessão de banco,
registra a execução em ``execucoes_calculo`` (histórico pessoal, RQ-DAD/HEA-05).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, Mapping, Optional

from sqlalchemy.orm import Session

from app.engines.crystallography import ESTRUTURAS, VERSAO_MOTOR, calcular_estrutura, calcular_miller
from app.engines.crystallography.ligas import calcular_solucao_solida
from app.engines.crystallography.referencia import RepositorioMateriais
from app.engines.procedencia import PoliticaDados, RepositorioPropriedades, bloco_procedencia, sha256_parametros
from app.engines.thermodynamics.termico import VERSAO_MOTOR as VERSAO_TERMICO
from app.engines.thermodynamics.termico import calcular_termico
from app.models import ExecucaoCalculo

AVISO_SEED_BASE = ("Raio, massa atômica e densidade experimental vêm do seed da v1.1.0 e aguardam validação "
                   "(citação do Callister sem edição e página — CR-10).")


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_seguro(valor: Any) -> Any:
    """Torna o resultado serializável em JSON/JSONB (tuplas viram listas)."""
    if isinstance(valor, dict):
        return {str(k): _json_seguro(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(v) for v in valor]
    return valor


class ServicoCalculo:
    def __init__(self, repo: RepositorioMateriais, props: RepositorioPropriedades, politica: PoliticaDados,
                 sessao: Optional[Session] = None) -> None:
        self.repo = repo
        self.props = props
        self.politica = politica
        self.sessao = sessao

    # --- casos de uso --------------------------------------------------------------
    def celula(self, payload: Mapping[str, Any], usuario_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        def executar() -> Dict[str, Any]:
            resultado = calcular_estrutura(payload, self.repo)
            fontes = [resultado["fonte"]] if resultado.get("fonte") else []
            avisos = [AVISO_SEED_BASE] if resultado.get("simbolo") and not resultado.get("editado") else []
            resultado["procedencia"] = bloco_procedencia(
                classe="analitico", motor="crystallography", versao_motor=VERSAO_MOTOR,
                versao_dados=self.repo.versao_dados, parametros=dict(payload), fontes_modelo=fontes, avisos=avisos)
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

    # --- infraestrutura --------------------------------------------------------------
    def _executar(self, operacao: str, motor: str, versao: str, payload: Mapping[str, Any],
                  usuario_id: Optional[uuid.UUID], executar: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        inicio = time.perf_counter()
        resultado = executar()
        duracao_ms = (time.perf_counter() - inicio) * 1000.0
        resultado["procedencia"]["calculado_em"] = _agora_iso()
        if self.sessao is not None and usuario_id is not None:
            self.sessao.add(ExecucaoCalculo(
                usuario_id=usuario_id, motor_codigo=motor, motor_versao=versao,
                versao_dados=resultado["procedencia"]["versao_dados"], operacao=operacao,
                parametros=_json_seguro(dict(payload)),
                parametros_sha256=bytes.fromhex(sha256_parametros(payload)),
                resultado=_json_seguro(resultado), classe_resultado=resultado["procedencia"]["classe"],
                status="concluido", duracao_ms=Decimal(f"{duracao_ms:.3f}")))
            self.sessao.flush()
        return resultado
