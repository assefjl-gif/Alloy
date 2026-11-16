"""Descritores de ligas de alta entropia (HEA) — motor 2.0.0 (RQ-HEA-01..04, PI-02; contrato R1, seção 1).

Calculado (sempre com frações ATÔMICAS xᵢ; a entrada em massa é convertida antes de qualquer cálculo):
* ΔS_mix ideal = −R·Σ xᵢ·ln xᵢ — analítico; só depende da composição.
* −T·ΔS_mix(T), de 300 K a T_sup — analítico; sai em qualquer ambiente.
* δ = 100·√(Σ xᵢ·(1 − rᵢ/r̄)²), r̄ = Σ xᵢ·rᵢ — descompasso de raios (Zhang et al., 2008).
* T_m = Σ xᵢ·T_f,ᵢ — regra das misturas (não é solidus nem liquidus).
* VEC = Σ xᵢ·VECᵢ; a sugestão de estrutura (Guo et al., 2011) só sai DENTRO do domínio de aplicação.
* wᵢ = xᵢ·Mᵢ/Σ xⱼ·Mⱼ e M̄ = Σ xᵢ·Mᵢ, com as massas do repositório de materiais.

Condicional (só com TODOS os pares da liga na matriz de entalpias, que hoje não existe no repositório):
* ΔH_mix = Σ_{i<j} 4·ΔH_ij·xᵢ·xⱼ (kJ/mol); Ω = T_m·ΔS_mix/(1000·|ΔH_mix|); ΔG_mix(T) = ΔH_mix − T·ΔS_mix.
  Faltando um par, NÃO há soma parcial nem ΔH_ij = 0 presumido: o resultado é ``None`` com o motivo.

NÃO calculado: energia de formação, dureza, ductilidade. Toda grandeza nula tem motivo em ``indisponiveis``.
Nenhuma referência bibliográfica foi conferida na fonte: todo critério sai com ``verificada: False``.

Dados de elemento passam pela PoliticaDados: em produção, só valores validados são usados; a grandeza que
dependeria de um dado não validado fica indisponível, com o motivo e a entrada em ``dados_faltantes``.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ..crystallography.formatacao import sci, txt
from ..crystallography.referencia import RepositorioMateriais
from ..procedencia import ColetorDados, PoliticaDados, RepositorioPropriedades, ValorReferencia, bloco_procedencia
from .entrada import FRACAO_MINIMA, MAX_ELEMENTOS, validar_base, validar_composicao
from .erros import EntradaHeaInvalida, MassaNaoValidada, detalhe, eco
from .referencia import CODIGO_PAR, Identidades, RepositorioEntalpias, SemEntalpias, rotulo_par
from .textos import (
    AVISO_DH_PROXIMO_DE_ZERO,
    AVISO_TM_NOMINAL,
    AVISO_VEC_SEM_FONTE,
    AVISOS_FIXOS,
    CLASSES,
    CRITERIOS,
    DELTA_SOLUCAO_SOLIDA,
    DS_ALTA_R,
    DS_MEDIA_R,
    MOTIVO_DH_SEM_MATRIZ,
    MOTIVO_ENERGIA_FORMACAO,
    MOTIVO_OMEGA_DH_ZERO,
    MOTIVO_OMEGA_SEM_DH,
    MOTIVO_OMEGA_SEM_TM,
    MOTIVO_SEM_MODELO,
    OMEGA_SOLUCAO_SOLIDA,
    VEC_CCC,
    VEC_CFC,
    criterios_definicao,
    definicoes,
)

VERSAO_MOTOR = "2.0.0"
R_GASES = 8.314462618  # J/(mol·K), CODATA 2018 (valor exato pela redefinição do SI)
DS_ALTA_ENTROPIA = DS_ALTA_R * R_GASES  # ΔS_mix ≥ 1,5R: definição por entropia

EPS = 1e-9                 # tolerância nas comparações com limiares (valor não arredondado)
MARGEM_LIMIAR = 0.02       # "próximo do limiar": |valor − limiar| ≤ 2 % do limiar (heurística do especialista)
DH_NULO = 1e-9             # kJ/mol: abaixo disso Ω não é definido
DH_PEQUENO = 1.0           # kJ/mol: abaixo disso Ω é devolvido com aviso (heurística do especialista)
T_INICIAL_K = 300.0
PASSO_T_K = 50.0
T_SUP_NOMINAL_K = 2000.0
T_SUP_MAXIMO_K = 6000.0
CATEGORIAS_NAO_METAL = ("gás nobre", "halogênio", "não metal")
GRUPOS_VEC = range(4, 12)  # metais de transição dos grupos 4 a 11 (mais o Al): regra conservadora, sem fonte

FONTES_MODELO = (
    "ΔS_mix ideal: −R·Σ xᵢ ln xᵢ (entropia configuracional de Boltzmann para solução ideal)",
    "Zhang, Y. et al. Adv. Eng. Mater. 10, 534–538 (2008) — parâmetro δ",
    "Yang, X.; Zhang, Y. Mater. Chem. Phys. 132, 233–238 (2012) — critério δ ≤ 6,6 % e Ω ≥ 1,1",
    "Guo, S. et al. J. Appl. Phys. 109, 103505 (2011) — critério de fases por VEC",
)
FONTE_MIEDEMA = ("Takeuchi, A.; Inoue, A. Mater. Trans. 46, 2817 (2005) — entalpias de mistura por par "
                 "(modelo de Miedema), usadas em ΔH_mix")

Fracoes = List[Tuple[str, float]]
Faltas = List[Tuple[str, str]]  # (símbolo, "ausente" | "nao_validado")


def entropia_mistura(fracoes: Sequence[Tuple[str, float]]) -> float:
    return -R_GASES * math.fsum(x * math.log(x) for _, x in fracoes)


# ------------------------------------------------------------------------- dados elementares
def _utilizavel(dado: Optional[ValorReferencia], politica: PoliticaDados) -> Optional[str]:
    """``None`` se o dado pode ser usado; senão a situação (``ausente`` ou ``nao_validado``)."""
    if dado is None:
        return "ausente"
    if not dado.validado and not politica.permitir_nao_validado:
        return "nao_validado"
    return None


def _dado_raio(repo: RepositorioMateriais, simbolo: str) -> Optional[ValorReferencia]:
    metal = repo.obter(simbolo)
    if metal is None:
        return None
    # O seed base aguarda validação (CR-10): estado fixado aqui, como no motor 1.0.0 (achado A-13, em aberto).
    return ValorReferencia(simbolo=simbolo, codigo="raio_atomico", valor=metal.raio_nm, unidade="nm",
                           estado="aguardando_validacao", fonte=metal.fonte)


def _dado_massa(repo: RepositorioMateriais, simbolo: str) -> Optional[ValorReferencia]:
    """Massa que os motores JÁ leem do repositório de materiais (decisão D-1.7). Não é a tabela periódica."""
    metal = repo.obter(simbolo)
    if metal is None:
        return None
    return ValorReferencia(simbolo=simbolo, codigo="massa_atomica", valor=metal.peso_g_mol, unidade="g/mol",
                           estado="aguardando_validacao", fonte=metal.fonte)


def _coletar(simbolos: Sequence[str], obter: Callable[[str], Optional[ValorReferencia]],
             politica: PoliticaDados) -> Tuple[Optional[Dict[str, ValorReferencia]], Faltas]:
    """Todos os dados ou nenhum: devolve os dados (se completos) e a lista COMPLETA do que faltou."""
    dados: Dict[str, ValorReferencia] = {}
    faltas: Faltas = []
    for simbolo in simbolos:
        dado = obter(simbolo)
        situacao = _utilizavel(dado, politica)
        if situacao is None and dado is not None:
            dados[simbolo] = dado
        else:
            faltas.append((simbolo, situacao or "ausente"))
    return (None, faltas) if faltas else (dados, faltas)


def _texto_faltas(descricao: str, faltas: Faltas) -> str:
    ausentes = [s for s, situacao in faltas if situacao == "ausente"]
    pendentes = [s for s, situacao in faltas if situacao == "nao_validado"]
    partes = []
    if ausentes:
        partes.append(f"falta {descricao} no repositório de materiais para {', '.join(ausentes)}")
    if pendentes:
        partes.append(f"{descricao} de {', '.join(pendentes)} sem validação com fonte "
                      "(este ambiente só usa dados validados)")
    return "; ".join(partes)


# ------------------------------------------------------------------------- composição
def _fracoes_atomicas(payload: Mapping[str, Any], repo: RepositorioMateriais, politica: PoliticaDados,
                      identidades: Identidades) -> Tuple[Fracoes, str, float, Tuple[str, ...]]:
    base = validar_base(payload.get("base"))
    comp = validar_composicao(payload.get("composicao"), identidades)
    partes = [(simbolo, quantidade) for simbolo, quantidade, _ in comp.itens]
    chaves = {simbolo: chave for simbolo, _, chave in comp.itens}

    if base == "massica":
        # 7. toda massa precisa ser utilizável: sem a conversão nenhuma grandeza (nem ΔS_mix) pode ser calculada.
        massas, faltas = _coletar([s for s, _ in partes], lambda s: _dado_massa(repo, s), politica)
        if massas is None:
            lista = ", ".join(s for s, _ in faltas)
            mensagem = f"Não é possível converter de % em massa: falta massa atômica utilizável para {lista}."
            detalhes = [detalhe(chaves[s], "massa_indisponivel", mensagem) for s, _ in faltas]
            if any(situacao == "ausente" for _, situacao in faltas):
                raise EntradaHeaInvalida(detalhes)
            raise MassaNaoValidada(detalhes)
        partes = [(s, q / massas[s].valor) for s, q in partes]

    total = math.fsum(q for _, q in partes)
    fracoes = [(s, q / total) for s, q in partes]
    # 8. fração mínima: abaixo da resolução da saída o elemento apareceria como "0,0000 %".
    erros = [detalhe(chaves[s], "fracao_abaixo_do_minimo",
                     f"A fração de {s} ({sci(100.0 * x, 2)} at.%) está abaixo do mínimo aceito "
                     "(0,0001 at.%). Remova o elemento ou aumente a quantidade.")
             for s, x in fracoes if x < FRACAO_MINIMA]
    if erros:
        raise EntradaHeaInvalida(erros)
    return fracoes, base, comp.soma, comp.zeros


# ------------------------------------------------------------------------- critérios e triagem
def _compara(valor: float, operador: str, limiar: float) -> bool:
    if operador == "<=":
        return valor <= limiar + EPS
    if operador == ">=":
        return valor >= limiar - EPS
    if operador == "<":
        return valor < limiar - EPS
    return valor > limiar + EPS


def _triagem(delta: Optional[float], omega: Optional[float], motivo_delta: Optional[str],
             motivo_omega: Optional[str], nao_metais: Sequence[str]) -> Dict[str, str]:
    """Critério conjunto Ω ≥ 1,1 E δ ≤ 6,6 % (Yang & Zhang, 2012; não verificada). Nunca "estável"."""
    delta_ok = None if delta is None else _compara(delta, "<=", DELTA_SOLUCAO_SOLIDA)
    omega_ok = None if omega is None else _compara(omega, ">=", OMEGA_SOLUCAO_SOLIDA)
    lim_delta, lim_omega = txt(DELTA_SOLUCAO_SOLIDA, 1), txt(OMEGA_SOLUCAO_SOLIDA, 1)
    t_delta = None if delta is None else f"δ = {txt(delta, 2)} %"
    t_omega = None if omega is None else f"Ω = {txt(omega, 2)}"

    if nao_metais:
        return {"estado": "inconclusiva", "texto": (
            f"TRIAGEM INCONCLUSIVA: a liga contém elemento não metálico ({', '.join(nao_metais)}). Os descritores "
            "δ, VEC, ΔH_mix e Ω foram propostos para ligas metálicas substitucionais; a interpretação está fora "
            "do domínio de validade.")}
    if delta_ok and omega_ok:
        return {"estado": "favoravel", "texto": (
            f"TRIAGEM FAVORÁVEL à solução sólida desordenada: {t_omega} ≥ {lim_omega} e {t_delta} ≤ {lim_delta} % "
            "(critério empírico de Yang & Zhang, 2012). É um indicador de triagem: não comprova fase única nem "
            "estabilidade.")}
    if delta_ok is False or omega_ok is False:
        falhas = []
        if delta_ok is False:
            falhas.append(f"{t_delta} > {lim_delta} %")
        if omega_ok is False:
            falhas.append(f"{t_omega} < {lim_omega}")
        pendente = ""
        if omega_ok is None:
            pendente = f"; Ω não foi avaliado ({motivo_omega})"
        elif delta_ok is None:
            pendente = f"; δ não foi avaliado ({motivo_delta})"
        return {"estado": "desfavoravel", "texto": (
            f"TRIAGEM DESFAVORÁVEL à solução sólida desordenada: {'; '.join(falhas)}. O critério empírico de "
            f"Yang & Zhang (2012) não é atendido{pendente}. É um indicador de triagem: não comprova a formação de "
            "intermetálicos nem de fase amorfa.")}
    partes = []
    if delta_ok:
        partes.append(f"{t_delta} ≤ {lim_delta} % (atendido)")
    if omega_ok:
        partes.append(f"{t_omega} ≥ {lim_omega} (atendido)")
    if delta_ok is None and omega_ok is None:
        partes.append(f"δ e Ω não puderam ser avaliados (δ: {motivo_delta}; Ω: {motivo_omega})")
    elif omega_ok is None:
        partes.append(f"Ω não pôde ser avaliado ({motivo_omega})")
    elif delta_ok is None:
        partes.append(f"δ não pôde ser avaliado ({motivo_delta})")
    return {"estado": "inconclusiva", "texto": (
        f"TRIAGEM INCONCLUSIVA: {'; '.join(partes)}. O critério empírico de Yang & Zhang (2012) exige os dois "
        "indicadores.")}


def _dominio_vec(vec: Optional[float], ds: float, simbolos: Sequence[str], identidades: Identidades,
                 estado_triagem: str) -> Tuple[bool, List[str], List[str]]:
    """Domínio de aplicação do critério de VEC (auditoria 2.7.2; regra conservadora SEM fonte, D-1.6).

    Devolve (aplicável, motivos sem símbolos — usados em ``fase`` —, elementos fora do conjunto).
    Os motivos não podem conter siglas de estrutura nem símbolos de elemento: a interface procura as
    siglas no texto de ``fase`` sem diferenciar maiúsculas ("Sc" e "Cs" seriam lidos como estrutura).
    """
    if vec is None:
        return False, ["VEC indisponível"], []
    motivos: List[str] = []
    if ds < DS_MEDIA_R * R_GASES - EPS:
        motivos.append("ΔS_mix abaixo de 1R: liga diluída ou com poucos elementos principais")
    fora = [s for s in simbolos if s != "Al" and identidades[s].grupo not in GRUPOS_VEC]
    if fora:
        motivos.append("há elemento fora do conjunto considerado (metais de transição dos grupos 4 a 11 e alumínio)")
    if estado_triagem == "desfavoravel":
        motivos.append("a triagem de solução sólida é desfavorável")
    return not motivos, motivos, fora


def _fase(vec: Optional[float], aplicavel: bool, motivos: Sequence[str]) -> Tuple[str, Optional[str], Optional[str]]:
    """(texto de ``fase``, ``estrutura_sugerida``, motivo de não haver sugestão única)."""
    if vec is None:
        return "não avaliada: VEC indisponível", None, "Sem VEC não há sugestão de estrutura."
    if not aplicavel:
        motivo = "; ".join(motivos)
        return (f"não avaliada: critério de VEC fora do domínio de validade ({motivo})", None,
                f"O critério empírico de VEC não foi aplicado: {motivo}.")
    fonte = "Guo et al., 2011"
    if _compara(vec, ">=", VEC_CFC):
        return f"CFC sugerida pelo critério empírico de VEC (VEC ≥ {txt(VEC_CFC, 1)}; {fonte})", "CFC", None
    if _compara(vec, "<", VEC_CCC):
        return f"CCC sugerida pelo critério empírico de VEC (VEC < {txt(VEC_CCC, 2)}; {fonte})", "CCC", None
    return (f"CFC + CCC sugeridas pelo critério empírico de VEC ({txt(VEC_CCC, 2)} ≤ VEC < {txt(VEC_CFC, 1)}; "
            f"{fonte})", None,
            "O critério empírico de VEC indica a faixa em que as duas estruturas cúbicas são sugeridas: não há "
            "sugestão única de estrutura.")


def _criterios(valores: Mapping[str, Optional[float]], motivos: Mapping[str, Optional[str]],
               vec_aplicavel: bool, motivo_vec: Optional[str]) -> List[Dict[str, Any]]:
    """``valores``: grandeza → valor NÃO arredondado (a comparação não usa o valor arredondado da saída)."""
    saida: List[Dict[str, Any]] = []
    for definicao, (_, grandeza, operador, limiar, _, _, _) in zip(criterios_definicao(), CRITERIOS, strict=True):
        valor = valores.get(grandeza)
        aplicavel = vec_aplicavel if grandeza == "VEC" else True
        avaliado = valor is not None and aplicavel
        motivo: Optional[str] = None
        if valor is None:
            motivo = motivos.get(grandeza)
        elif not aplicavel:
            motivo = motivo_vec
        definicao.update({
            "valor": None if valor is None else round(valor, 4),
            "atende": _compara(valor, operador, limiar) if avaliado and valor is not None else None,
            "aplicavel": aplicavel,
            "proximo_do_limiar": valor is not None and abs(valor - limiar) <= MARGEM_LIMIAR * abs(limiar),
            "motivo": motivo,
        })
        saida.append(definicao)
    return saida


# ------------------------------------------------------------------------- análise
def analisar_liga(payload: Mapping[str, Any], repo: RepositorioMateriais, props: RepositorioPropriedades,
                  politica: PoliticaDados, *, identidades: Identidades,
                  entalpias: Optional[RepositorioEntalpias] = None) -> Dict[str, Any]:
    """``identidades``: os 118 elementos (só identidade). ``entalpias``: matriz de pares; ``None`` = nenhuma."""
    entalpias = entalpias if entalpias is not None else SemEntalpias()
    nome = str(payload.get("nome") or "").strip() or "Liga sem nome"
    fracoes, base, soma_informada, zeros = _fracoes_atomicas(payload, repo, politica, identidades)
    simbolos = [s for s, _ in fracoes]
    coletor = ColetorDados(politica)
    indisponiveis: Dict[str, str] = {}
    dados_faltantes: List[Dict[str, str]] = []
    avisos: List[str] = []

    def faltou(codigo: str, faltas: Faltas) -> None:
        dados_faltantes.extend({"simbolo": s, "codigo": codigo, "situacao": situacao} for s, situacao in faltas)

    def usar(dados: Mapping[str, ValorReferencia]) -> Dict[str, float]:
        for dado in dados.values():
            coletor.registrar(dado)
        return {s: float(d.valor) for s, d in dados.items()}

    ds = entropia_mistura(fracoes)
    ds_r = ds / R_GASES

    # δ e raio médio
    delta: Optional[float] = None
    raio_medio: Optional[float] = None
    motivo_delta: Optional[str] = None
    dados, faltas = _coletar(simbolos, lambda s: _dado_raio(repo, s), politica)
    if dados is None:
        faltou("raio_atomico", faltas)
        motivo_delta = _texto_faltas("raio atômico", faltas)
        indisponiveis["delta"] = f"δ indisponível: {motivo_delta}."
        indisponiveis["raio_medio_nm"] = f"Raio médio indisponível: {motivo_delta}."
    else:
        raios = usar(dados)
        raio_medio = math.fsum(x * raios[s] for s, x in fracoes)
        delta = 100.0 * math.sqrt(math.fsum(x * (1.0 - raios[s] / raio_medio) ** 2 for s, x in fracoes))

    # T_m (regra das misturas; T_f do repositório em °C)
    tm: Optional[float] = None
    dados, faltas = _coletar(simbolos, lambda s: props.propriedade(s, "temperatura_fusao"), politica)
    if dados is None:
        faltou("temperatura_fusao", faltas)
        indisponiveis["Tm"] = f"T_m indisponível: {_texto_faltas('temperatura de fusão', faltas)}."
    else:
        fusao = usar(dados)
        tm = math.fsum(x * (fusao[s] + 273.15) for s, x in fracoes)

    # VEC
    vec: Optional[float] = None
    dados, faltas = _coletar(simbolos, lambda s: props.propriedade(s, "vec"), politica)
    if dados is None:
        faltou("vec", faltas)
        indisponiveis["VEC"] = f"VEC indisponível: {_texto_faltas('VEC', faltas)}."
    else:
        vecs = usar(dados)
        vec = math.fsum(x * vecs[s] for s, x in fracoes)

    # composição em massa (as duas bases sempre que possível)
    fracoes_massa: Optional[Dict[str, float]] = None
    massa_media: Optional[float] = None
    dados, faltas = _coletar(simbolos, lambda s: _dado_massa(repo, s), politica)
    if dados is None:
        faltou("massa_atomica", faltas)
        motivo = f"Composição em massa indisponível: {_texto_faltas('massa atômica', faltas)}."
        indisponiveis.update({"fracoes_massa": motivo, "comp_massa_pct": motivo,
                              "massa_molar_media": motivo.replace("Composição em massa", "Massa molar média")})
    else:
        massas = usar(dados)
        massa_media = math.fsum(x * massas[s] for s, x in fracoes)
        fracoes_massa = {s: x * massas[s] / massa_media for s, x in fracoes}

    # ΔH_mix: só com TODOS os pares utilizáveis (nunca soma parcial, nunca ΔH_ij = 0 presumido)
    pares = [(simbolos[i], simbolos[j]) for i in range(len(simbolos)) for j in range(i + 1, len(simbolos))]
    dh: Optional[float] = None
    valores_par: Dict[Tuple[str, str], ValorReferencia] = {}
    pares_faltantes: List[str] = []
    for a, b in pares:
        dado = entalpias.entalpia_par(a, b)
        situacao = _utilizavel(dado, politica)
        if situacao is None and dado is not None:
            valores_par[(a, b)] = dado
        else:
            pares_faltantes.append(rotulo_par(a, b))
            dados_faltantes.append({"simbolo": rotulo_par(a, b), "codigo": CODIGO_PAR,
                                    "situacao": situacao or "ausente"})
    pares_faltantes.sort()
    x_de = dict(fracoes)
    if pares_faltantes:
        if not entalpias.resumo().get("disponivel"):
            indisponiveis["dH"] = MOTIVO_DH_SEM_MATRIZ
        else:
            indisponiveis["dH"] = (f"ΔH_mix indisponível: faltam entalpias de mistura com fonte para "
                                   f"{len(pares_faltantes)} de {len(pares)} pares: {', '.join(pares_faltantes)}.")
    else:
        for dado in valores_par.values():
            coletor.registrar(dado)
        dh = math.fsum(4.0 * dado.valor * x_de[a] * x_de[b] for (a, b), dado in valores_par.items())

    # Ω
    omega: Optional[float] = None
    motivo_omega: Optional[str] = None
    if dh is None:
        indisponiveis["omega"], motivo_omega = MOTIVO_OMEGA_SEM_DH, "ΔH_mix indisponível"
    elif tm is None:
        indisponiveis["omega"], motivo_omega = MOTIVO_OMEGA_SEM_TM, "T_m indisponível"
    elif abs(dh) < DH_NULO:
        indisponiveis["omega"], motivo_omega = MOTIVO_OMEGA_DH_ZERO, "ΔH_mix = 0"
    else:
        omega = tm * ds / (1000.0 * abs(dh))
        if abs(dh) < DH_PEQUENO:
            avisos.append(AVISO_DH_PROXIMO_DE_ZERO)

    # curva −T·ΔS_mix × T (analítica, sempre) e ΔG_mix do modelo (só com ΔH_mix)
    if tm is None:
        t_sup = T_SUP_NOMINAL_K
        avisos.append(AVISO_TM_NOMINAL)
    else:
        t_sup = min(max(math.ceil(tm / 100.0 - EPS) * 100.0, T_INICIAL_K), T_SUP_MAXIMO_K)
    curva: List[Dict[str, Any]] = []
    for k in range(int(round((t_sup - T_INICIAL_K) / PASSO_T_K)) + 1):
        t = T_INICIAL_K + k * PASSO_T_K
        menos_tds = -t * ds / 1000.0
        curva.append({"T": t, "menos_TdS": round(menos_tds, 4),
                      "dG": None if dh is None else round(dh + menos_tds, 4)})
    gibbs: List[Dict[str, float]] = []
    dg_tm: Optional[float] = None
    t_cruzamento: Optional[float] = None
    if dh is None:
        sem_dh = "depende de ΔH_mix, que está indisponível."
        indisponiveis["gibbs"] = f"A curva de ΔG_mix do modelo {sem_dh} A curva de −T·ΔS_mix está em curva_T."
        indisponiveis["dG_Tm"] = f"ΔG_mix do modelo em T_m {sem_dh}"
        indisponiveis["T_cruzamento_k"] = f"A temperatura de cruzamento {sem_dh}"
    else:
        gibbs = [{"T": p["T"], "G": round(1000.0 * p["dG"], 1)} for p in curva]  # J/mol = 1000·dG (obsoleto)
        if tm is None:
            indisponiveis["dG_Tm"] = "ΔG_mix do modelo em T_m depende de T_m, que está indisponível."
        else:
            dg_tm = dh - tm * ds / 1000.0
        if dh > DH_NULO:
            t_cruzamento = 1000.0 * dh / ds
        else:
            indisponiveis["T_cruzamento_k"] = ("Não se aplica: ΔH_mix ≤ 0; ΔG_mix do modelo é negativo em toda "
                                               "temperatura acima de 0 K.")

    # triagem, domínio do VEC e critérios
    nao_metais = [s for s in simbolos if identidades[s].categoria in CATEGORIAS_NAO_METAL]
    triagem = _triagem(delta, omega, motivo_delta, motivo_omega, nao_metais)
    vec_aplicavel, motivos_vec, fora_vec = _dominio_vec(vec, ds, simbolos, identidades, triagem["estado"])
    fase, estrutura, motivo_estrutura = _fase(vec, vec_aplicavel, motivos_vec)
    if motivo_estrutura:
        indisponiveis["estrutura_sugerida"] = motivo_estrutura + (
            f" Elementos fora do conjunto: {', '.join(fora_vec)}." if fora_vec else "")
    motivo_vec_criterio = None if vec_aplicavel else "Critério fora do domínio de validade: " + "; ".join(motivos_vec)
    criterios = _criterios(
        {"delta": delta, "omega": omega, "VEC": vec, "dS_R": ds_r},
        {"delta": indisponiveis.get("delta"), "omega": indisponiveis.get("omega"), "VEC": indisponiveis.get("VEC")},
        vec_aplicavel, motivo_vec_criterio)

    for grandeza, rotulo in (("dureza", "dureza"), ("dureza_indice", "índice de dureza"),
                             ("ductilidade", "ductilidade"), ("fragilidade", "fragilidade")):
        indisponiveis[grandeza] = MOTIVO_SEM_MODELO.format(grandeza=rotulo)
    indisponiveis["energia_formacao"] = MOTIVO_ENERGIA_FORMACAO

    # avisos condicionais (procedência)
    if zeros:
        avisos.append(f"Elementos com quantidade zero foram ignorados: {', '.join(zeros)}.")
    if len(fracoes) < 5:
        avisos.append("Menos de 5 elementos: pela definição por composição (Yeh, 2004), não é uma HEA; "
                      "as grandezas continuam válidas como descritores da mistura.")
    for s in nao_metais:
        avisos.append(f"{s} não é metal: os descritores δ, VEC, ΔH_mix e Ω foram propostos para ligas metálicas "
                      "substitucionais; a interpretação está fora do domínio de validade.")
    if vec is not None and not vec_aplicavel:
        avisos.append("Critério de VEC (Guo et al., 2011) não aplicado: " + "; ".join(motivos_vec)
                      + (f" ({', '.join(fora_vec)})" if fora_vec else "") + ". " + AVISO_VEC_SEM_FONTE)
    elif vec_aplicavel:
        avisos.append("A estrutura indicada pelo critério de VEC é sugestão empírica, não previsão de fase. "
                      + AVISO_VEC_SEM_FONTE)
    nomes = {"delta": "δ", "omega": "Ω", "VEC": "VEC", "dS_R": "ΔS_mix"}
    for criterio in criterios:
        if criterio["proximo_do_limiar"] and criterio["aplicavel"]:
            avisos.append(f"{nomes[criterio['grandeza']]} está a menos de 2 % do limiar "
                          f"({txt(criterio['limiar'], 2)} {criterio['unidade']}): a classificação pode mudar com a "
                          "incerteza dos dados de entrada.")
    conjunto = {c["codigo"]: c["atende"] for c in criterios if c["codigo"] in ("delta_yang_zhang", "omega_yang_zhang")}
    if set(conjunto.values()) == {True, False}:
        avisos.append("Os critérios discordam: "
                      + "; ".join(f"{'δ' if c == 'delta_yang_zhang' else 'Ω'} "
                                  f"{'atende' if ok else 'não atende'}" for c, ok in conjunto.items()) + ".")

    # interpretação (vocabulário de triagem: sem "fase prevista", sem "mais prováveis")
    interpretacao = [
        f"ΔS_mix = {txt(ds, 2)} J/(mol·K) = {txt(ds_r, 3)}·R "
        + ("(≥ 1,5R: alta entropia pela definição por entropia)." if ds_r >= DS_ALTA_R - EPS
           else "(< 1,5R: não é alta entropia pela definição por entropia)."),
    ]
    if delta is not None:
        atende = _compara(delta, "<=", DELTA_SOLUCAO_SOLIDA)
        interpretacao.append(
            f"δ = {txt(delta, 2)} % {'≤' if atende else '>'} {txt(DELTA_SOLUCAO_SOLIDA, 1)} %: "
            + ("atende" if atende else "não atende")
            + " ao critério empírico de descompasso de raios (Yang & Zhang, 2012).")
    if vec is not None:
        interpretacao.append(f"VEC = {txt(vec, 2)} e/átomo. Estrutura: {fase}.")
    if dh is None:
        interpretacao.append("Ω e ΔH_mix indisponíveis: o critério completo de Yang & Zhang (Ω ≥ 1,1 e δ ≤ 6,6 %) "
                             "não pode ser avaliado.")
    else:
        interpretacao.append(f"ΔH_mix (modelo de Miedema, solução regular) = {txt(dh, 2)} kJ/mol"
                             + ("." if omega is None else f"; Ω = {txt(omega, 2)}."))

    resultado: Dict[str, Any] = {
        "nome": nome,
        "veredito": triagem["texto"],
        "fase": fase,
        "estrutura_sugerida": estrutura,
        "ductilidade": None,
        "dureza": None,
        "dureza_indice": None,
        "dS": round(ds, 4),
        "dS_R": round(ds_r, 4),
        "classe_entropia": ("alta" if ds_r >= DS_ALTA_R - EPS else "media" if ds_r >= DS_MEDIA_R - EPS else "baixa"),
        "dH": None if dh is None else round(dh, 4),
        "delta": None if delta is None else round(delta, 4),
        "omega": None if omega is None else round(omega, 4),
        "VEC": None if vec is None else round(vec, 4),
        "Tm": None if tm is None else round(tm, 1),
        "raio_medio_nm": raio_medio,
        "base_entrada": base,
        "soma_informada": soma_informada,
        "comp_percent": {s: round(100.0 * x, 4) for s, x in fracoes},
        "fracoes": {s: x for s, x in fracoes},
        "fracoes_massa": fracoes_massa,
        "comp_massa_pct": (None if fracoes_massa is None
                           else {s: round(100.0 * w, 4) for s, w in fracoes_massa.items()}),
        "massa_molar_media": None if massa_media is None else round(massa_media, 4),
        "pares_faltantes": pares_faltantes,
        "dados_faltantes": dados_faltantes,
        "T_sup_k": t_sup,
        "curva_T": curva,
        "dG_Tm": None if dg_tm is None else round(dg_tm, 4),
        "T_cruzamento_k": None if t_cruzamento is None else round(t_cruzamento, 3),
        "energia_formacao": None,
        "criterios": criterios,
        "triagem": triagem,
        "vec_aplicavel": vec_aplicavel,
        "classes": dict(CLASSES),
        "interpretacao": interpretacao,
        "fragilidade": None,
        "gibbs": gibbs,
        "indisponiveis": indisponiveis,
    }
    versao_dados = props.versao_dados
    fontes_modelo = FONTES_MODELO
    if dh is not None:
        fontes_modelo = (*FONTES_MODELO, FONTE_MIEDEMA)
        if entalpias.versao_dados:
            versao_dados = f"{versao_dados}+{entalpias.versao_dados}"
    resultado["procedencia"] = bloco_procedencia(
        classe="estimativa_modelo", motor="hea", versao_motor=VERSAO_MOTOR, versao_dados=versao_dados,
        parametros={"nome": nome, "composicao": {eco(k): v for k, v in dict(payload.get("composicao") or {}).items()},
                    "base": base},
        coletor=coletor, fontes_modelo=fontes_modelo, avisos=avisos)
    return resultado


# ------------------------------------------------------------------------- catálogo (bootstrap)
#: Composições equimolares clássicas da literatura usadas como exemplos (só elementos cadastrados).
def _equimolar(nome: str, grupo: str, *elementos: str) -> Dict[str, Any]:
    return {"nome": nome, "grupo": grupo, "composicao": dict.fromkeys(elementos, 1.0)}


#: O primeiro é o carregado por padrão no front.
EXEMPLOS = {
    "CoCrFeNi": _equimolar("CoCrFeNi", "CFC (literatura)", "Co", "Cr", "Fe", "Ni"),
    "AlCoCrFeNi": _equimolar("AlCoCrFeNi", "CCC/B2 (literatura)", "Al", "Co", "Cr", "Fe", "Ni"),
    "CoCrCuFeNi": _equimolar("CoCrCuFeNi", "CFC (literatura)", "Co", "Cr", "Cu", "Fe", "Ni"),
    "Al0.5CoCrCuFeNi": {"nome": "Al0.5CoCrCuFeNi", "grupo": "CFC (Yeh 2004)",
                        "composicao": {"Al": 0.5, "Co": 1.0, "Cr": 1.0, "Cu": 1.0, "Fe": 1.0, "Ni": 1.0}},
}

#: OBSOLETO (mantido por compatibilidade): limiares dos critérios, não uma "liga de referência".
#: Substituto: ``criterios`` do bootstrap, com fonte e marca de verificação.
REFERENCIA = {"dS": round(DS_ALTA_ENTROPIA, 3), "omega": OMEGA_SOLUCAO_SOLIDA, "delta": DELTA_SOLUCAO_SOLIDA,
              "VEC": VEC_CFC, "dH": None, "T_padrao": "não se aplica (ΔS_mix ideal)", "P_padrao": "não se aplica"}


def catalogo(repo: RepositorioMateriais, props: RepositorioPropriedades, politica: PoliticaDados, *,
             identidades: Identidades, entalpias: Optional[RepositorioEntalpias] = None) -> Dict[str, Any]:
    entalpias = entalpias if entalpias is not None else SemEntalpias()

    def usavel(dado: Optional[ValorReferencia]) -> bool:
        return _utilizavel(dado, politica) is None

    elementos = {}
    for metal in repo.listar():
        elementos[metal.simbolo] = {
            "simbolo": metal.simbolo, "nome": metal.nome, "raio_nm": metal.raio_nm,
            "tem_fusao": props.propriedade(metal.simbolo, "temperatura_fusao") is not None,
            "tem_vec": props.propriedade(metal.simbolo, "vec") is not None,
            "tem_massa": usavel(_dado_massa(repo, metal.simbolo)),
        }
    # Os 118 símbolos aceitos na entrada, com o que ESTE ambiente consegue usar de cada um (sem valores).
    aceitos = [{
        "simbolo": e.simbolo, "nome": e.nome, "numero_atomico": e.numero_atomico, "categoria": e.categoria,
        "tem_raio": usavel(_dado_raio(repo, e.simbolo)),
        "tem_fusao": usavel(props.propriedade(e.simbolo, "temperatura_fusao")),
        "tem_vec": usavel(props.propriedade(e.simbolo, "vec")),
        "tem_massa": usavel(_dado_massa(repo, e.simbolo)),
    } for e in sorted(identidades.values(), key=lambda e: e.numero_atomico)]
    resumo = entalpias.resumo()
    amostras = [analisar_liga(exemplo, repo, props, politica, identidades=identidades, entalpias=entalpias)
                for exemplo in EXEMPLOS.values()]
    return {
        "elements": elementos, "alloys": EXEMPLOS, "reference": REFERENCIA, "samples": amostras,
        "versao_motor": VERSAO_MOTOR,
        "elementos_aceitos": aceitos,
        "criterios": criterios_definicao(),
        "entalpias": {"disponivel": bool(resumo.get("disponivel")), "n_pares": int(resumo.get("n_pares") or 0),
                      "fonte": resumo.get("fonte"), "estado": resumo.get("estado")},
        "guias_entropia": [{"n": n, "dS": round(R_GASES * math.log(n), 6), "dS_R": round(math.log(n), 6)}
                           for n in range(2, 7)],
        "definicoes": definicoes(bool(resumo.get("disponivel"))),
        "avisos_fixos": list(AVISOS_FIXOS),
    }


__all__ = ["DS_ALTA_ENTROPIA", "EXEMPLOS", "MAX_ELEMENTOS", "REFERENCIA", "R_GASES", "VERSAO_MOTOR",
           "analisar_liga", "catalogo", "entropia_mistura"]
