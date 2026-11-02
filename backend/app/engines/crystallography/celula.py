"""Serviço de célula unitária: parâmetros de rede, FEA, densidade e passo a passo."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .constantes import (
    FAIXA_A_NM,
    FAIXA_C_A,
    FAIXA_PESO,
    FAIXA_RAIO_NM,
    LIMITE_DESVIO_PERCENT,
    N_AVOGADRO,
    NM_PARA_CM,
    SQRT3,
    TOLERANCIA_EDICAO,
)
from .entradas import numero_opcional
from .erros import EntradaInvalida, MaterialDesconhecido
from .estruturas import ESTRUTURAS, ROTULOS_TIPO, c_a_ideal, fracao, normalizar_estrutura
from .formatacao import sci, sinal, txt
from .geometria import arredondar, base_cristalografica, fator_empacotamento, geometria_celula
from .passos import passos_fea, passos_parametro
from .referencia import Metal, RepositorioMateriais


def _mudou(novo: float, atual: Optional[float]) -> bool:
    return atual is not None and not math.isclose(novo, atual, rel_tol=TOLERANCIA_EDICAO, abs_tol=1e-12)


def resolver_alvo(texto: str, repo: RepositorioMateriais) -> Tuple[Optional[Metal], Optional[str]]:
    """Interpreta o campo ``nome``: metal ou estrutura genérica.

    Ordem pensada para não haver choque quando novos elementos entrarem na base
    (ex.: um futuro "Cs" não pode sequestrar a estrutura "CS"):
    1) símbolo exato com caixa (``Cs``); 2) sigla/alias de estrutura (``CS``, ``bcc``);
    3) símbolo sem caixa, alias ou nome do metal (``fe``, ``ferro``).
    """
    alvo = (texto or "").strip()
    if not alvo:
        return None, None
    exato = repo.obter(alvo)
    if exato:
        return exato, None
    estrutura = normalizar_estrutura(alvo)
    if estrutura:
        return None, estrutura
    metal = repo.buscar(alvo)
    if metal:
        return metal, None
    raise MaterialDesconhecido(
        f"'{alvo}' não é um metal cadastrado nem uma estrutura conhecida (CS, CCC, CFC, HC).")


def _passos_densidade(estrutura: str, raio: Optional[float], peso: Optional[float],
                      c_a: Optional[float], a_nm: Optional[float], c_nm: Optional[float],
                      volume_cm3: Optional[float], densidade: Optional[float],
                      densidade_exp: Optional[float], erro: Optional[float],
                      a_fonte: str, c_fonte: Optional[str]) -> List[Dict[str, str]]:
    info = ESTRUTURAS[estrutura]
    n = info["n"]
    if peso is None or a_nm is None or volume_cm3 is None or densidade is None:
        faltando = " e ".join(
            nome for nome, valor in (("o raio atômico", a_nm), ("o peso atômico", peso)) if valor is None
        )
        return [{
            "titulo": "Dados insuficientes",
            "formula": "ρ = n·A / (Vc·N_A)",
            "detalhe": f"Informe {faltando} para calcular a densidade teórica. "
                       f"Ex.: estrutura {estrutura} r=0.128 A=63.55",
        }]

    a_cm = a_nm * NM_PARA_CM
    medido = a_fonte == "medido"
    if medido:
        entrada = (f"a = {txt(a_nm, 4)} nm (medido)   A = {txt(peso, 2)} g/mol   "
                   f"n = {n} átomos/célula   N_A = 6,022 × 10²³ átomos/mol")
        parametro = f"a (parâmetro de rede medido) = {txt(a_nm, 4)} nm = {sci(a_cm)} cm"
        detalhe_parametro = "Usa-se o parâmetro de rede tabelado (difração de raios X)."
        if raio is not None:
            detalhe_parametro += (f" Pelo modelo de contato, {info['relacao']} com R = {txt(raio, 4)} nm "
                                  f"daria {txt(info['a_em_R'] * raio, 4)} nm.")
    else:
        entrada = (f"R = {txt(raio or 0.0, 4)} nm   A = {txt(peso, 2)} g/mol   "
                   f"n = {n} átomos/célula   N_A = 6,022 × 10²³ átomos/mol")
        parametro = (f"{info['relacao']} = {info['substituicao'].format(R=txt(raio or 0.0, 4))} "
                     f"= {txt(a_nm, 4)} nm = {sci(a_cm)} cm")
        detalhe_parametro = f"Os átomos se tocam ao longo da {info['contato']}."

    if estrutura == "HC" and c_nm is not None and c_a is not None:
        if c_fonte == "medido":
            parametro += (f"\nc (medido) = {txt(c_nm, 4)} nm = {sci(c_nm * NM_PARA_CM)} cm "
                          f"→ c/a = {txt(c_a, 4)}")
        else:
            parametro += (f"\nc = (c/a)·a = {txt(c_a, 3)} × {txt(a_nm, 4)} = "
                          f"{txt(c_nm, 4)} nm = {sci(c_nm * NM_PARA_CM)} cm")
        volume = (f"Vc = (3√3/2)·a²·c = 2,598 × ({sci(a_cm)} cm)² × "
                  f"{sci(c_nm * NM_PARA_CM)} cm = {sci(volume_cm3)} cm³")
    else:
        volume = f"Vc = a³ = ({sci(a_cm)} cm)³ = {sci(volume_cm3)} cm³"

    passos = [
        {"titulo": "Dados de entrada", "formula": entrada,
         "detalhe": f"Na estrutura {estrutura} cada célula unitária contém {n} átomo(s) equivalente(s)."},
        {"titulo": "Parâmetro de rede", "formula": parametro, "detalhe": detalhe_parametro},
        {"titulo": "Volume da célula unitária", "formula": volume,
         "detalhe": "1 nm = 10⁻⁷ cm, logo 1 nm³ = 10⁻²¹ cm³."},
        {"titulo": "Densidade teórica",
         "formula": f"ρ = n·A / (Vc·N_A) = ({n} × {txt(peso, 2)}) / "
                    f"({sci(volume_cm3)} × 6,022 × 10²³) = {txt(densidade, 3)} g/cm³",
         "detalhe": "Massa dos átomos contidos na célula dividida pelo volume da célula."},
    ]
    if densidade_exp is not None and erro is not None:
        if abs(erro) > LIMITE_DESVIO_PERCENT:
            detalhe = (f"Desvio acima de {txt(LIMITE_DESVIO_PERCENT, 0)} %: não é arredondamento — "
                       "o dado de entrada (raio ou estrutura) não reproduz a rede real.")
        else:
            detalhe = "Diferenças vêm de raios tabelados arredondados, lacunas e expansão térmica."
        passos.append({
            "titulo": "Comparação experimental",
            "formula": f"ρ exp = {txt(densidade_exp, 2)} g/cm³ → desvio = {sinal(erro)}{txt(erro, 2)} %",
            "detalhe": detalhe,
        })
    return passos


def calcular_estrutura(payload: Mapping[str, Any],
                       repo: RepositorioMateriais) -> Dict[str, Any]:
    """Calcula a célula unitária completa (contrato de saída compatível com a v1.0)."""
    metal, estrutura = resolver_alvo(str(payload.get("nome") or ""), repo)
    avisos: List[str] = []

    raio: Optional[float] = None
    peso: Optional[float] = None
    c_a: Optional[float] = None
    densidade_exp: Optional[float] = None
    a_medido: Optional[float] = None
    c_medido: Optional[float] = None

    if metal:
        estrutura = metal.estrutura
        raio = metal.raio_nm
        peso = metal.peso_g_mol
        c_a = metal.c_a_efetivo
        densidade_exp = metal.densidade_exp_g_cm3
        if metal.tem_rede_medida:
            a_medido, c_medido = metal.a_nm, metal.c_nm

    editado = False
    estrutura_pedida = payload.get("estrutura")
    if estrutura_pedida not in (None, ""):
        nova = normalizar_estrutura(str(estrutura_pedida))
        if not nova:
            raise EntradaInvalida(f"Estrutura desconhecida: {estrutura_pedida}. Use CS, CCC, CFC ou HC.")
        if metal and nova != estrutura:
            editado = True
            original = ESTRUTURAS[metal.estrutura]
            avisos.append(
                f"{metal.simbolo} é {metal.estrutura} (NC {original['nc']}); a estrutura {nova} foi aplicada "
                f"com o mesmo raio tabelado. Como o raio metálico depende do número de coordenação "
                f"(correção de Goldschmidt), a densidade obtida é hipotética e não é comparada "
                f"com o valor experimental.")
            if metal.estrutura == "HC":
                avisos.append(f"O c/a do {metal.simbolo} foi descartado: estruturas cúbicas não usam c/a.")
            c_a = None
            a_medido = c_medido = None
        estrutura = nova
    if not estrutura:
        raise EntradaInvalida("Informe um elemento (ex.: Fe) ou uma estrutura (CS, CCC, CFC, HC).")

    novo_raio = numero_opcional(payload, "raio", FAIXA_RAIO_NM, "raio atômico (nm)")
    novo_peso = numero_opcional(payload, "peso", FAIXA_PESO, "peso atômico (g/mol)")
    novo_c_a = numero_opcional(payload, "c_a", FAIXA_C_A, "razão c/a")
    if novo_raio is not None:
        if _mudou(novo_raio, raio):
            editado = True
            a_medido = c_medido = None
        else:
            novo_raio = raio if raio is not None else novo_raio
        raio = novo_raio
    # Caminho inverso (v1.4): um a informado (ex.: medido por difração) define R pela condição de contato.
    novo_a = numero_opcional(payload, "a", FAIXA_A_NM, "parâmetro de rede a (nm)")
    a_informado = False
    if novo_a is not None:
        k = float(ESTRUTURAS[estrutura]["a_em_R"])
        raio_de_a = novo_a / k
        if not FAIXA_RAIO_NM[0] <= raio_de_a <= FAIXA_RAIO_NM[1]:
            raise EntradaInvalida(
                f"Com a = {txt(novo_a, 4)} nm a estrutura {estrutura} exige R = {txt(raio_de_a, 4)} nm, "
                f"fora da faixa {txt(FAIXA_RAIO_NM[0], 2)}–{txt(FAIXA_RAIO_NM[1], 2)} nm.")
        if novo_raio is not None and _mudou(raio_de_a, novo_raio):
            avisos.append(f"O raio informado foi ignorado: o parâmetro a tem prioridade "
                          f"(R = a/{txt(k, 4)} = {txt(raio_de_a, 4)} nm).")
        if raio is None or _mudou(raio_de_a, raio):
            editado = editado or raio is not None
            a_medido = c_medido = None
            a_informado = True
            raio = raio_de_a
    if novo_peso is not None:
        if _mudou(novo_peso, peso):
            editado = True
        else:
            novo_peso = peso if peso is not None else novo_peso
        peso = novo_peso
    if estrutura == "HC":
        if novo_c_a is not None:
            if _mudou(novo_c_a, c_a):
                editado = True
                c_medido = None
                c_a = novo_c_a
            elif c_a is None:
                c_a = novo_c_a
        if c_a is None:
            c_a = c_a_ideal()
            if metal and metal.estrutura != "HC":
                avisos.append("Sem c/a tabelado para esta combinação: usado o c/a ideal 1,633.")
    else:
        if novo_c_a is not None:
            avisos.append("O c/a informado foi ignorado: estruturas cúbicas não usam c/a.")
        c_a = None
    if editado:
        densidade_exp = None

    info = ESTRUTURAS[estrutura]
    n = info["n"]
    a_em_r = info["a_em_R"]

    a_nm: Optional[float]
    c_nm: Optional[float] = None
    c_fonte: Optional[str] = None
    if a_medido is not None:
        a_fonte = "medido"
        a_nm = a_medido
        if estrutura == "HC":
            if c_medido is not None:
                c_nm, c_fonte = c_medido, "medido"
            else:
                c_nm, c_fonte = a_nm * float(c_a), "c_a"
            c_a = c_nm / a_nm
    elif raio is not None:
        a_fonte = "informado" if a_informado else "derivado_de_R"
        a_nm = float(novo_a) if a_informado else a_em_r * raio
        if estrutura == "HC":
            c_nm, c_fonte = a_nm * float(c_a), "c_a"
    else:
        a_fonte = "relativo"
        a_nm = None

    fea = fator_empacotamento(estrutura, c_a)
    if a_nm is not None:
        volume_nm3 = (3.0 * SQRT3 / 2.0) * a_nm ** 2 * float(c_nm) if estrutura == "HC" else a_nm ** 3
        volume_cm3: Optional[float] = volume_nm3 * NM_PARA_CM ** 3
    else:
        volume_nm3 = None
        volume_cm3 = None
    densidade = n * peso / (volume_cm3 * N_AVOGADRO) if (volume_cm3 and peso is not None) else None
    erro = (densidade / densidade_exp - 1.0) * 100.0 if (densidade and densidade_exp) else None
    if erro is not None and abs(erro) > LIMITE_DESVIO_PERCENT:
        avisos.append(
            f"Desvio de {sinal(erro)}{txt(erro, 2)} % em relação ao valor experimental, acima de "
            f"{txt(LIMITE_DESVIO_PERCENT, 0)} %: não é efeito de arredondamento. Confira o raio, "
            f"o c/a e a estrutura informados.")

    atomos_calc, arestas_calc = geometria_celula(estrutura, c_a)
    contagem: List[Dict[str, Any]] = []
    atomos: List[Dict[str, Any]] = []
    for atomo in atomos_calc:
        valor, valor_txt = fracao(estrutura, atomo["tipo"])
        atomos.append({"pos": arredondar(atomo["pos"]), "tipo": atomo["tipo"],
                       "fracao": valor, "fracao_txt": valor_txt})
        grupo = next((g for g in contagem if g["tipo"] == atomo["tipo"]), None)
        if grupo is None:
            grupo = {"tipo": atomo["tipo"], "rotulo": ROTULOS_TIPO[atomo["tipo"]], "quantidade": 0,
                     "fracao": valor, "fracao_txt": valor_txt, "contribuicao": 0.0}
            contagem.append(grupo)
        grupo["quantidade"] += 1
        grupo["contribuicao"] = round(grupo["quantidade"] * valor, 6)
    arestas = [[arredondar(p) for p in aresta] for aresta in arestas_calc]

    simbolo = metal.simbolo if metal else None
    if metal and not editado:
        rotulo = f"{metal.simbolo} — {metal.nome}"
    elif metal:
        rotulo = f"{metal.simbolo} — parâmetros editados"
    else:
        rotulo = f"Célula genérica {estrutura}" + (f" · R = {txt(raio, 4)} nm" if raio is not None else "")

    interpretacao = repo.interpretacoes(estrutura)
    if estrutura == "HC":
        interpretacao.append(f"c/a usado = {txt(float(c_a), 3)} (ideal 1,633) → FEA = {txt(fea, 4)}.")
    if a_fonte == "medido" and metal and raio is not None:
        interpretacao.append(
            f"Para o {metal.simbolo} o cálculo usa os parâmetros de rede medidos (a = {txt(a_nm, 4)} nm"
            + (f", c = {txt(c_nm, 4)} nm" if c_nm is not None else "")
            + f"). Com o raio tabelado R = {txt(raio, 4)} nm, o modelo {info['relacao']} daria "
              f"a = {txt(a_em_r * raio, 4)} nm.")
    if densidade is not None:
        frase = f"Densidade teórica calculada: {txt(densidade, 3)} g/cm³"
        if erro is not None:
            frase += (f" (experimental {txt(float(densidade_exp), 2)} g/cm³, "
                      f"desvio {sinal(erro)}{txt(erro, 2)}%)")
        interpretacao.append(frase + ".")
    else:
        interpretacao.append("Sem raio e peso atômico a célula é exibida em unidades de R "
                             "e a densidade não pode ser calculada.")

    fonte = repo.fonte(metal.fonte) if metal else None
    grupo_espacial = info["grupo_espacial"]
    resultado = {
        "rotulo": rotulo, "simbolo": simbolo, "nome_metal": metal.nome if metal else None,
        "editado": editado, "generica": metal is None,
        "estrutura": estrutura, "estrutura_nome": info["nome"],
        "relacao_a": info["relacao"], "contato": info["contato"],
        "n": n, "nc": info["nc"], "fea": fea, "vazios": 1.0 - fea,
        "a_em_R": a_em_r, "c_a": c_a,
        "raio_nm": raio, "peso": peso, "a_nm": a_nm, "c_nm": c_nm, "a_fonte": a_fonte,
        "volume_nm3": volume_nm3, "volume_cm3": volume_cm3,
        "densidade": densidade, "densidade_exp": densidade_exp,
        "erro_percent": erro, "raio_relativo": 1.0 / a_em_r,
        "atomos": atomos, "arestas": arestas, "contagem": contagem,
        "base": base_cristalografica(estrutura),
        "z": info["z"],
        "grupo_espacial": {"hm": grupo_espacial["hm"], "numero": grupo_espacial["numero"]},
        "passos_densidade": _passos_densidade(estrutura, raio, peso, c_a, a_nm, c_nm, volume_cm3,
                                              densidade, densidade_exp, erro, a_fonte, c_fonte),
        "interpretacao": interpretacao,
        "avisos": avisos,
        "fonte": fonte.get("citacao") if fonte else None,
    }
    resultado["passos_parametro"] = passos_parametro(resultado)
    resultado["passos_fea"] = passos_fea(resultado)
    return resultado


def calcular_densidade(payload: Mapping[str, Any],
                       repo: RepositorioMateriais) -> Dict[str, Any]:
    resultado = calcular_estrutura(payload, repo)
    chaves = ("rotulo", "estrutura", "n", "nc", "fea", "vazios", "densidade", "densidade_exp",
              "erro_percent", "volume_cm3", "raio_nm", "peso", "a_nm", "c_nm", "a_fonte", "avisos")
    saida = {chave: resultado[chave] for chave in chaves}
    saida["passos"] = resultado["passos_densidade"]
    return saida
