"""Soluções sólidas substitucionais e intersticiais (portado da v1.4 — RQ-CIE-11).

Modelos e fontes:
* Parâmetro de rede pela lei de Vegard (Vegard, Z. Phys. 5, 17–26, 1921) aplicada ao raio médio
  na estrutura do solvente — empírica, por isso a classe do resultado é ``estimativa_modelo``.
* % atômica ↔ % em peso: Callister & Rethwisch, eq. 4.6–4.7.
* Regras de Hume-Rothery (Callister, seção 4.3), com o critério de ±0,4 de eletronegatividade
  de Darken & Gurry (Physical Chemistry of Metals, 1953) e a regra de Hägg (r/R < 0,59).
* Raio livre dos sítios: geometria das esferas rígidas (fatores analíticos abaixo).
* Superestruturas por PROTÓTIPO geométrico (L1₂, L1₀, B2): o motor não sabe se o par real
  ordena assim — sempre avisa que o arranjo é hipotético.
* Distorção local: ilustrativa (``simulacao_ilustrativa``), não é relaxação elástica.
"""

from __future__ import annotations

import math
import random
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ..procedencia import ColetorDados, PoliticaDados, RepositorioPropriedades, bloco_procedencia
from .constantes import EPS, N_AVOGADRO, NM_PARA_CM, SQRT2, SQRT3
from .entradas import numero_opcional
from .erros import EntradaInvalida, MaterialDesconhecido
from .estruturas import ESTRUTURAS, c_a_ideal
from .formatacao import sci, sinal, txt
from .geometria import frac_para_cart, norma, sub, volume_em_r
from .referencia import Metal, RepositorioMateriais
from .supercelula import geometria_supercelula, pontos_na_caixa, validar_tamanho
from .versao import VERSAO_MOTOR

#: Maior sítio intersticial de cada rede: raio livre = fator·R e posições fracionárias representativas.
SITIOS: Dict[str, Dict[str, Any]] = {
    "CS": {"nome": "cúbico", "fator": SQRT3 - 1.0, "nc": 8, "frac": [(0.5, 0.5, 0.5)]},
    "CCC": {"nome": "octaédrico", "fator": 2.0 / SQRT3 - 1.0, "nc": 6,
            "frac": [(0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5),
                     (0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, 0.5)]},
    "CFC": {"nome": "octaédrico", "fator": SQRT2 - 1.0, "nc": 6,
            "frac": [(0.5, 0.5, 0.5), (0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, 0.5)]},
    # Base HC do motor: (0,0,0) e (2/3,1/3,1/2) → sítios octaédricos em (1/3,2/3,1/4) e (1/3,2/3,3/4).
    "HC": {"nome": "octaédrico", "fator": SQRT2 - 1.0, "nc": 6, "frac": [(1 / 3, 2 / 3, 0.25), (1 / 3, 2 / 3, 0.75)]},
}

LIMITE_TAMANHO_PCT = 15.0          # Hume-Rothery
LIMITE_ELETRONEGATIVIDADE = 0.4    # Darken & Gurry (1953)
LIMITE_HAGG = 0.59                 # Hägg
X_MAXIMO_INTERSTICIAL = 20.0
FONTES_MODELO = (
    "Vegard, L. Z. Phys. 5, 17–26 (1921) — lei de Vegard",
    "Callister & Rethwisch, Ciência e Engenharia de Materiais, seção 4.3 e eq. 4.6–4.7",
    "Darken, L. S.; Gurry, R. W. Physical Chemistry of Metals (1953) — critério de eletronegatividade",
)

AVISO_ORDENADO = ("Arranjo ordenado hipotético: o motor monta o protótipo geométrico, mas não sabe se este "
                  "par de elementos realmente ordena assim. Confira o diagrama de fases do sistema.")


def _inteiro(v: float) -> bool:
    return abs(v - round(v)) < EPS


def _regra_ordenada(estrutura: str, x: float) -> Optional[Tuple[Callable[[Sequence[float]], bool], str]]:
    if estrutura == "CFC" and abs(x - 0.25) <= 0.02:
        return (lambda f: all(_inteiro(v) for v in f)), "L1₂ (protótipo Cu₃Au): soluto nos vértices"
    if estrutura == "CFC" and abs(x - 0.75) <= 0.02:
        return (lambda f: not all(_inteiro(v) for v in f)), "L1₂ invertida: soluto nos centros de face"
    if estrutura == "CFC" and abs(x - 0.5) <= 0.02:
        return (lambda f: _inteiro(f[2])), "L1₀ (protótipo CuAu): camadas alternadas ao longo de z"
    if estrutura == "CCC" and abs(x - 0.5) <= 0.02:
        return (lambda f: not _inteiro(f[0])), "B2 (protótipo CuZn β′): soluto nos centros dos cubos"
    return None


def _metal(repo: RepositorioMateriais, texto: str, papel: str) -> Metal:
    metal = repo.obter(texto) or repo.buscar(texto)
    if metal is None:
        raise MaterialDesconhecido(f"{papel} '{texto}' não é um metal cadastrado.")
    return metal


def _regra(criterio: str, valor: Optional[str], ok: Optional[bool], detalhe: str,
           indisponivel: Optional[str] = None) -> Dict[str, Any]:
    return {"criterio": criterio, "valor": valor, "ok": ok, "detalhe": detalhe, "indisponivel": indisponivel}


def _regras_substitucionais(b: Metal, s: Metal, props: RepositorioPropriedades,
                            coletor: ColetorDados) -> List[Dict[str, Any]]:
    dr = abs(s.raio_nm - b.raio_nm) / b.raio_nm * 100.0
    regras = [
        _regra("Tamanho atômico", f"ΔR = {txt(dr, 1)} %", dr <= LIMITE_TAMANHO_PCT,
               "Raios até ±15 % diferentes permitem substituição extensa."),
        _regra("Estrutura cristalina", f"{b.estrutura} e {s.estrutura}", b.estrutura == s.estrutura,
               "Solubilidade total exige a mesma estrutura nos dois metais puros."),
    ]
    chi_b, motivo_b = coletor.opcional(props, b.simbolo, "eletronegatividade", "eletronegatividade")
    chi_s, motivo_s = coletor.opcional(props, s.simbolo, "eletronegatividade", "eletronegatividade")
    if chi_b is None or chi_s is None:
        regras.append(_regra("Eletronegatividade", None, None, "Critério de Darken & Gurry (±0,4).",
                             motivo_b or motivo_s))
    else:
        dchi = abs(chi_s - chi_b)
        regras.append(_regra("Eletronegatividade", f"Δχ = {txt(dchi, 2)}", dchi <= LIMITE_ELETRONEGATIVIDADE,
                             "Diferença grande favorece compostos intermetálicos (Darken & Gurry: ±0,4)."))
    val_b, motivo_b = coletor.opcional(props, b.simbolo, "valencia", "valência")
    val_s, motivo_s = coletor.opcional(props, s.simbolo, "valencia", "valência")
    if val_b is None or val_s is None:
        regras.append(_regra("Valência", None, None, "Mesma valência favorece a solubilidade.",
                             motivo_b or motivo_s))
    else:
        regras.append(_regra("Valência", f"+{val_b:g} e +{val_s:g}", val_b == val_s,
                             "Mesma valência favorece; um metal dissolve melhor outro de valência maior."))
    return regras


def _conclusao(regras: Sequence[Mapping[str, Any]]) -> str:
    avaliadas = [r for r in regras if r["ok"] is not None]
    atendidas = sum(1 for r in avaliadas if r["ok"])
    if len(avaliadas) < len(regras):
        return (f"{atendidas} de {len(avaliadas)} regras avaliáveis atendidas; "
                f"{len(regras) - len(avaliadas)} indisponível(is) por falta de dado validado.")
    if atendidas == len(regras):
        return "Todas as regras atendidas: solubilidade sólida extensa, possivelmente completa (como no Cu–Ni)."
    if regras[0]["ok"]:
        return (f"{atendidas} de {len(regras)} regras atendidas: solubilidade parcial; "
                "acima do limite surgem outras fases.")
    return "Diferença de tamanho acima de 15 %: solubilidade substitucional muito limitada."


def _aplicar_distorcao(atomos: List[Dict[str, Any]], base: str, raios: Mapping[str, float], a_nm: float) -> None:
    """Desloca vizinhos do soluto em metade do desajuste de raios, limitado a 0,12·a (ilustrativo)."""
    r_base = raios[base]
    hospedeiros = [i for i, a in enumerate(atomos) if a["elemento"] == base]
    deslocamentos = {i: [0.0, 0.0, 0.0] for i in hospedeiros}
    for atomo in atomos:
        if atomo["elemento"] == base:
            continue
        distancias = [(i, norma(sub(atomos[i]["pos"], atomo["pos"]))) for i in hospedeiros]
        if not distancias:
            continue
        minima = min(d for _, d in distancias)
        for i, d in distancias:
            if d > minima * 1.05 or d < EPS:
                continue
            passo = max(-0.12, min(0.12, 0.5 * (raios[atomo["elemento"]] + r_base - d * a_nm) / a_nm))
            direcao = sub(atomos[i]["pos"], atomo["pos"])
            for j in range(3):
                deslocamentos[i][j] += passo * direcao[j] / d
    for i, (dx, dy, dz) in deslocamentos.items():
        total = math.sqrt(dx * dx + dy * dy + dz * dz)
        if total < 1e-12:
            continue
        escala = min(1.0, 0.15 / total)
        p = atomos[i]["pos"]
        atomos[i]["pos"] = [p[0] + dx * escala, p[1] + dy * escala, p[2] + dz * escala]


def calcular_solucao_solida(payload: Mapping[str, Any], repo: RepositorioMateriais,
                            props: RepositorioPropriedades, politica: PoliticaDados) -> Dict[str, Any]:
    coletor = ColetorDados(politica)
    base = _metal(repo, str(payload.get("base") or ""), "Solvente")
    texto_soluto = str(payload.get("soluto") or "").strip()
    simbolo_intersticial = props.buscar_intersticial(texto_soluto)
    intersticial = bool(simbolo_intersticial)
    soluto_metal: Optional[Metal] = None if intersticial else _metal(repo, texto_soluto, "Soluto")
    soluto = simbolo_intersticial if intersticial else soluto_metal.simbolo
    if soluto == base.simbolo:
        raise EntradaInvalida("O soluto precisa ser diferente do solvente.")

    x_max = X_MAXIMO_INTERSTICIAL if intersticial else 100.0
    x_pct = numero_opcional(payload, "x", (0.0, x_max), f"composição (% atômica, 0 a {txt(x_max, 0)})")
    x_pct = 10.0 if x_pct is None else x_pct
    x = x_pct / 100.0
    n = validar_tamanho(payload.get("n") or 3)
    try:
        semente = int(payload.get("semente") or 1)
    except (TypeError, ValueError):
        raise EntradaInvalida("A semente deve ser um número inteiro.") from None
    arranjo = "ordenado" if str(payload.get("arranjo") or "") == "ordenado" else "aleatorio"
    distorcer = bool(payload.get("distorcer"))

    estrutura = base.estrutura
    info = ESTRUTURAS[estrutura]
    c_a = base.c_a_efetivo if estrutura == "HC" else None
    if estrutura == "HC" and c_a is None:
        c_a = c_a_ideal()
    k = float(info["a_em_R"])
    n_cel = int(info["n"])
    a_base = k * base.raio_nm
    vol_r = volume_em_r(estrutura, c_a)

    sitio: Optional[Dict[str, Any]] = None
    if intersticial:
        r_soluto = coletor.exigir(props, soluto, "raio_atomico", "raio atômico")
        a_soluto = coletor.exigir(props, soluto, "massa_atomica", "massa atômica")
        r_ef = base.raio_nm
        a_nm = a_base
        solutos_cel = n_cel * x / (1.0 - x) if x < 1 else 0.0
        massa_cel = n_cel * base.peso_g_mol + solutos_cel * a_soluto
        pct_peso = solutos_cel * a_soluto / massa_cel * 100.0
        dados_sitio = SITIOS[estrutura]
        r_sitio = dados_sitio["fator"] * base.raio_nm
        razao = r_soluto / base.raio_nm
        sitio = {"nome": dados_sitio["nome"], "fator": dados_sitio["fator"], "raio_nm": r_sitio,
                 "nc": dados_sitio["nc"]}
        regras = [
            _regra("Razão de raios", f"r/R = {txt(razao, 3)}", razao <= LIMITE_HAGG,
                   "Regra de Hägg: soluções intersticiais exigem r/R abaixo de ~0,59."),
            _regra(f"Sítio {dados_sitio['nome']}", f"r livre = {txt(r_sitio, 4)} nm", r_soluto <= r_sitio,
                   f"Raio livre = {txt(dados_sitio['fator'], 4)}·R. Soluto maior empurra os vizinhos."),
        ]
        conclusao = ("O soluto é maior que o sítio: a rede se distorce e a solubilidade é baixa."
                     if r_soluto > r_sitio else "O soluto cabe no sítio sem distorção: solubilidade intersticial alta.")
        raios = {base.simbolo: base.raio_nm, soluto: r_soluto}
    else:
        r_soluto, a_soluto = soluto_metal.raio_nm, soluto_metal.peso_g_mol
        r_ef = (1.0 - x) * base.raio_nm + x * r_soluto
        a_nm = k * r_ef
        massa_cel = n_cel * ((1.0 - x) * base.peso_g_mol + x * a_soluto)
        pct_peso = x * a_soluto / (x * a_soluto + (1.0 - x) * base.peso_g_mol) * 100.0 if x > 0 else 0.0
        regras = _regras_substitucionais(base, soluto_metal, props, coletor)
        conclusao = _conclusao(regras)
        raios = {base.simbolo: base.raio_nm, soluto: r_soluto}

    volume_cm3 = vol_r * (a_nm / k) ** 3 * NM_PARA_CM ** 3
    densidade = massa_cel / (volume_cm3 * N_AVOGADRO)
    densidade_base = n_cel * base.peso_g_mol / (vol_r * base.raio_nm ** 3 * NM_PARA_CM ** 3 * N_AVOGADRO)

    atomos, arestas = geometria_supercelula(estrutura, c_a, n)
    for atomo in atomos:
        atomo["elemento"] = base.simbolo
    rng = random.Random(semente)  # noqa: S311 — sorteio didático reprodutível, sem uso criptográfico
    fase_ordenada: Optional[str] = None
    notas: List[str] = []
    if intersticial:
        sitios = pontos_na_caixa(SITIOS[estrutura]["frac"], n)
        quantidade = 0 if x == 0 else min(len(sitios), max(1, round(len(atomos) * x / (1.0 - x))))
        for f in sorted(rng.sample(sitios, quantidade)):
            atomos.append({"pos": list(frac_para_cart(estrutura, f, c_a)), "frac": list(f),
                           "tipo": "intersticial", "elemento": soluto})
        if arranjo == "ordenado":
            notas.append("Intersticiais são distribuídos ao acaso entre os sítios livres.")
    else:
        regra = _regra_ordenada(estrutura, x) if arranjo == "ordenado" else None
        if regra:
            teste, fase_ordenada = regra
            for atomo in atomos:
                if teste(atomo["frac"]):
                    atomo["elemento"] = soluto
            notas.append(AVISO_ORDENADO)
        else:
            if arranjo == "ordenado":
                notas.append("Sem superestrutura de protótipo para essa composição; usada distribuição aleatória. "
                             "Protótipos disponíveis: CFC com 25, 50 ou 75 % e CCC com 50 %.")
            for idx in rng.sample(range(len(atomos)), round(x * len(atomos))):
                atomos[idx]["elemento"] = soluto
    for atomo in atomos:
        atomo["raio_rel"] = raios[atomo["elemento"]] / a_nm

    distorcao = None
    if distorcer:
        _aplicar_distorcao(atomos, base.simbolo, raios, a_nm)
        distorcao = {"classe": "simulacao_ilustrativa",
                     "descricao": "Vizinhos do soluto deslocados em metade do desajuste de raios, "
                                  "limitado a 0,12·a. Não é relaxação elástica."}

    n_soluto = sum(1 for a in atomos if a["elemento"] == soluto)
    passos = [{
        "titulo": "Composição em peso",
        "formula": (f"C({soluto}) = x·A({soluto}) / [x·A({soluto}) + (1 − x)·A({base.simbolo})] "
                    f"= {txt(pct_peso, 2)} % em peso"),
        "detalhe": (f"x = {txt(x, 3)}; A({soluto}) = {txt(a_soluto, 3)} e "
                    f"A({base.simbolo}) = {txt(base.peso_g_mol, 2)} g/mol."),
    }]
    if not intersticial:
        passos.append({
            "titulo": "Lei de Vegard",
            "formula": (f"R̄ = (1 − x)·R({base.simbolo}) + x·R({soluto}) = {txt(r_ef, 4)} nm\n"
                        f"a = {info['substituicao'].format(R=txt(r_ef, 4))} = {txt(a_nm, 4)} nm "
                        f"({sinal((a_nm / a_base - 1) * 100)}{txt((a_nm / a_base - 1) * 100, 2)} % em relação ao "
                        f"{base.simbolo} puro)"),
            "detalhe": "Relação empírica: o parâmetro de rede varia linearmente na estrutura do solvente.",
        })
    passos.append({
        "titulo": "Densidade da liga",
        "formula": (f"ρ = m(célula) / (Vc·N_A) = {txt(massa_cel, 3)} / ({sci(volume_cm3)} × 6,022 × 10²³) "
                    f"= {txt(densidade, 3)} g/cm³"),
        "detalhe": f"{base.simbolo} puro: {txt(densidade_base, 3)} g/cm³.",
    })

    parametros = {"base": base.simbolo, "soluto": soluto, "x": x_pct, "n": n, "semente": semente,
                  "arranjo": arranjo, "distorcer": distorcer}
    return {
        "rotulo": f"Liga {base.simbolo}–{soluto}",
        "base": base.simbolo, "soluto": soluto, "intersticial": intersticial,
        "estrutura": estrutura, "estrutura_nome": info["nome"], "nc": info["nc"], "c_a": c_a,
        "supercelula": n, "semente": semente, "x_pct": x_pct, "pct_peso": pct_peso,
        "a_nm": a_nm, "c_nm": a_nm * c_a if c_a else None, "a_base_nm": a_base,
        "raio_relativo": base.raio_nm / a_nm, "densidade": densidade, "densidade_base": densidade_base,
        "n_soluto": n_soluto, "n_solvente": len(atomos) - n_soluto,
        "fase_ordenada": fase_ordenada, "nota_arranjo": " ".join(notas) or None,
        "sitio": sitio, "regras": regras, "conclusao": conclusao, "passos": passos,
        "distorcao": distorcao, "atomos": atomos, "arestas": arestas,
        "procedencia": bloco_procedencia(
            classe="estimativa_modelo", motor="crystallography", versao_motor=VERSAO_MOTOR,
            versao_dados=f"{repo.versao_dados}+{props.versao_dados}" if props is not repo else repo.versao_dados,
            parametros=parametros, coletor=coletor, fontes_modelo=FONTES_MODELO),
    }
