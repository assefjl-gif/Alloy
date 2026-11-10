"""Consulta à tabela periódica (ADR-018): filtros, busca por símbolo ou número atômico e procedência.

Dados de REFERÊNCIA (não são entrada de cálculo): ficam disponíveis em todos os ambientes, sempre com o
estado de validação de cada valor e um aviso enquanto nenhum estiver validado (Q-03).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.repositories.elementos import RepositorioElementos

from .erros import NaoEncontrado

AVISO_VALIDACAO = ("Valores importados de fontes de referência (CIAAW, PubChem) e ainda sem revisão humana "
                   "registrada (estado aguardando_validacao).")
FILTROS = ("periodo", "grupo", "bloco", "categoria", "estado_padrao")
CAMPOS_RESUMO = ("numero_atomico", "simbolo", "nome", "nome_en", "periodo", "grupo", "bloco", "categoria",
                 "estado_padrao")


class ServicoElementos:
    def __init__(self, repo: RepositorioElementos) -> None:
        self.repo = repo

    def _procedencia(self, itens: List[Dict[str, Any]]) -> Dict[str, Any]:
        estados = {p["estado"] for e in itens for p in e["propriedades"]}
        usadas = {p["fonte"] for e in itens for p in e["propriedades"]}
        fontes = self.repo.fontes()
        return {"conjunto": "tabela_periodica", "versao_dados": self.repo.versao_dados,
                "fontes": {k: v for k, v in fontes.items() if k in usadas or k == "wikipedia_pt_elementos"},
                "avisos": [AVISO_VALIDACAO] if estados - {"validado"} else []}

    def listar(self, filtros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        filtros = {k: v for k, v in (filtros or {}).items() if k in FILTROS and v is not None}
        itens = [e for e in self.repo.listar() if all(e[k] == v for k, v in filtros.items())]
        resumo = []
        for e in itens:
            r = {c: e[c] for c in CAMPOS_RESUMO}
            peso = next((p for p in e["propriedades"] if p["codigo"] in ("peso_atomico_padrao",
                                                                          "massa_isotopica_referencia")), None)
            r["massa"] = ({"codigo": peso["codigo"], "valor": peso["valor"], "unidade": peso["unidade"]}
                          if peso else None)
            resumo.append(r)
        return {"total": len(resumo), "itens": resumo, "procedencia": self._procedencia(itens)}

    def obter(self, ref: str) -> Dict[str, Any]:
        alvo = ref.strip()
        for e in self.repo.listar():
            if (alvo.isdigit() and e["numero_atomico"] == int(alvo)) or e["simbolo"].lower() == alvo.lower():
                return {**e, "procedencia": self._procedencia([e])}
        raise NaoEncontrado(f"Elemento não encontrado: {ref!r}. Use o símbolo (ex.: Fe) ou o número atômico (1–118).")
