"""Gera o seed da tabela periódica completa (118 elementos) a partir de fontes externas citadas.

    python scripts/importar_tabela_periodica.py            # baixa as fontes (ou usa o cache) e gera o seed
    python scripts/importar_tabela_periodica.py --offline  # só usa o cache (falha se faltar arquivo)

Fontes (ver database/seeds/tabela_periodica/FONTES.txt):
* CIAAW/IUPAC — pesos atômicos padrão (2021 + revisões de 2024): valores padrão e abreviados.
* PubChem (NCBI/NIH) — tabela periódica (configuração eletrônica, eletronegatividade de Pauling, raio de
  van der Waals, 1ª energia de ionização, afinidade eletrônica, estados de oxidação, estado padrão,
  fusão, ebulição, densidade, categoria e ano de descoberta), que agrega CIAAW, NIST, LANL e Jefferson Lab.
* Wikipédia em português — "Lista de elementos químicos" (nomes em português), com a grafia
  normalizada para o português do Brasil (tabela PT_BR abaixo).

Regras: nenhum valor é inventado. Campo vazio na fonte → propriedade ausente. O peso atômico padrão vem
SÓ da CIAAW; para elementos sem peso padrão, a massa informada pela PubChem entra com outro código
(``massa_isotopica_referencia``). Período, grupo e bloco são derivados do número atômico pela regra da tabela
de 18 colunas da IUPAC (2022) e conferidos contra a Wikipédia. Tudo entra como ``aguardando_validacao``.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import urllib.request
from datetime import date
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / "var" / "fontes_tabela_periodica"
SAIDA = RAIZ / "database" / "seeds" / "tabela_periodica" / "elementos.json"
VERSAO = "2026.11.3-tp"

FONTES_BRUTAS = {
    "pubchem.json": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON",
    "ciaaw_padrao.htm": "https://www.ciaaw.org/atomic-weights.htm",
    "ciaaw_abreviado.htm": "https://www.ciaaw.org/abridged-atomic-weights.htm",
    "wikipedia_pt.txt": "https://pt.wikipedia.org/w/index.php?title=Lista_de_elementos_qu%C3%ADmicos&action=raw",
}

FONTES = {
    "ciaaw_2024": {
        "tipo": "base_dados",
        "citacao": ("IUPAC Commission on Isotopic Abundances and Atomic Weights (CIAAW). Standard Atomic Weights "
                    "e Abridged Standard Atomic Weights (Atomic Weights 2021, com as revisões de 2024 de Gd, Lu e Zr). "
                    "Base: Prohaska, T. et al. Standard atomic weights of the elements 2021 (IUPAC Technical Report). "
                    "Pure Appl. Chem. 94(5), 573–600 (2022)."),
        "doi": "10.1515/pac-2019-0603",
        "url": "https://www.ciaaw.org/atomic-weights.htm",
        "versao_fonte": "Atomic Weights 2021 + revisões 2024",
        "licenca": "Dados de referência públicos da IUPAC; citar a fonte",
    },
    "pubchem_tabela_periodica": {
        "tipo": "base_dados",
        "citacao": ("Kim, S. et al. PubChem 2025 update. Nucleic Acids Res. 53(D1), D1516–D1525 (2025). "
                    "PubChem Periodic Table (National Center for Biotechnology Information), que agrega CIAAW, "
                    "NIST Physical Measurement Laboratory, Los Alamos National Laboratory e Jefferson Lab."),
        "doi": "10.1093/nar/gkae1059",
        "url": "https://pubchem.ncbi.nlm.nih.gov/periodic-table/",
        "versao_fonte": "PUG REST periodictable/JSON",
        "licenca": "Dados do NCBI/NIH de domínio público (EUA); citar a fonte",
    },
    "wikipedia_pt_elementos": {
        "tipo": "base_dados",
        "citacao": "Wikipédia em português. Lista de elementos químicos (nomes em português).",
        "url": "https://pt.wikipedia.org/wiki/Lista_de_elementos_qu%C3%ADmicos",
        "versao_fonte": "texto bruto (action=raw)",
        "licenca": "CC BY-SA 4.0",
    },
}

#: Grafia de Portugal → Brasil (Acordo Ortográfico: nos dois países valem as duas formas, mas o uso no Brasil é este).
PT_BR = {
    "Arsénio": "Arsênio", "Selénio": "Selênio", "Molibdénio": "Molibdênio", "Einsténio": "Einstênio",
    "Roentgénio": "Roentgênio", "Ne(p)túnio": "Netúnio", "Oganésson": "Oganessônio",
}

CATEGORIAS = {
    "Alkali metal": "metal alcalino", "Alkaline earth metal": "metal alcalinoterroso",
    "Transition metal": "metal de transição", "Post-transition metal": "metal pós-transição",
    "Metalloid": "semimetal", "Nonmetal": "não metal", "Halogen": "halogênio", "Noble gas": "gás nobre",
    "Lanthanide": "lantanídeo", "Actinide": "actinídeo",
}
ESTADOS = {"Solid": "solido", "Liquid": "liquido", "Gas": "gas",
           "Expected to be a Solid": "solido_previsto", "Expected to be a Gas": "gas_previsto"}

#: coluna da PubChem → (código da propriedade, unidade). Unidades conferidas no registro detalhado do Fe.
PROPRIEDADES_PUBCHEM = {
    "Electronegativity": ("eletronegatividade", "Pauling"),
    "AtomicRadius": ("raio_van_der_waals", "pm"),
    "IonizationEnergy": ("energia_ionizacao_1", "eV"),
    "ElectronAffinity": ("afinidade_eletronica", "eV"),
    "MeltingPoint": ("temperatura_fusao", "K"),
    "BoilingPoint": ("temperatura_ebulicao", "K"),
    "Density": ("densidade", "g/cm³"),
}

PERIODOS = [(1, 1, 2), (2, 3, 10), (3, 11, 18), (4, 19, 36), (5, 37, 54), (6, 55, 86), (7, 87, 118)]


def baixar(offline: bool) -> dict[str, dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    meta = {}
    for nome, url in FONTES_BRUTAS.items():
        caminho = CACHE / nome
        if not caminho.exists():
            if offline:
                sys.exit(f"faltando no cache: {caminho}")
            req = urllib.request.Request(url, headers={"User-Agent": "AlloyVirtualLab-importador/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                caminho.write_bytes(r.read())
        dados = caminho.read_bytes()
        meta[nome] = {"url": url, "sha256": hashlib.sha256(dados).hexdigest(), "bytes": len(dados)}
    return meta


def classificar(z: int) -> tuple[int, int | None, str]:
    """(período, grupo, bloco) pela tabela de 18 colunas; bloco f (57–71, 89–103) sem grupo."""
    for periodo, inicio, fim in PERIODOS:
        if inicio <= z <= fim:
            pos = z - inicio + 1
            break
    if periodo == 1:
        return 1, (1 if z == 1 else 18), "s"
    if periodo in (2, 3):
        return (periodo, pos, "s") if pos <= 2 else (periodo, pos + 10, "p")
    if periodo in (4, 5):
        grupo = pos
    else:  # 6 e 7: 2 (s) + 15 (f) + 15 (d e p)
        if pos <= 2:
            return periodo, pos, "s"
        if pos <= 17:
            return periodo, None, "f"
        grupo = pos - 14
    bloco = "s" if grupo <= 2 else "d" if grupo <= 12 else "p"
    return periodo, grupo, bloco


def _num(texto: str) -> Decimal:
    return Decimal(texto.replace(" ", "").replace(" ", ""))


def ler_ciaaw(arquivo: Path) -> dict[int, list[str]]:
    s = arquivo.read_text(encoding="utf-8", errors="replace")
    linhas = {}
    for tr in re.findall(r"<tr>(.*?)</tr>", s, flags=re.DOTALL):
        cel = [html.unescape(re.sub(r"<.*?>", "", c)).replace("\xa0", " ").strip()
               for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.DOTALL)]
        if cel and cel[0].isdigit():
            linhas[int(cel[0])] = cel
    return linhas


def peso_padrao(padrao: str, abreviado: str) -> dict | None:
    if padrao in ("—", "", "-") or abreviado in ("—", "", "-"):
        return None
    m = re.fullmatch(r"([\d. ]+)\s*±\s*([\d. ]+)", abreviado)
    if not m:
        raise ValueError(f"valor abreviado inesperado: {abreviado!r}")
    out = {"valor": str(_num(m.group(1))), "incerteza": str(_num(m.group(2)))}
    iv = re.fullmatch(r"\[\s*([\d. ]+),\s*([\d. ]+)\]", padrao)
    if iv:
        out["intervalo_min"], out["intervalo_max"] = str(_num(iv.group(1))), str(_num(iv.group(2)))
    out["nota"] = f"Valor abreviado CIAAW; valor padrão: {padrao}"
    return out


def ler_wikipedia(arquivo: Path) -> dict[int, dict]:
    s = arquivo.read_text(encoding="utf-8")
    out = {}
    padrao = (r"^\|\s*(\d+)\s*\|\|[^|]*\|\s*([A-Z][a-z]{0,2})\s*\|\|\s*\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"
              r"(?P<resto>.*?)(?=^\|-|\Z)")
    for m in re.finditer(padrao, s, flags=re.MULTILINE | re.DOTALL):
        z, simbolo, nome, apelido = int(m.group(1)), m.group(2), m.group(3), m.group(4)
        resto = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", m.group("resto"), flags=re.DOTALL)
        celulas = [c.strip() for c in re.split(r"\|\||\n\|", resto)]  # células: "||" ou nova linha com "|"
        # colunas restantes: latim, origem, massa, grupo, período
        grupo_txt = celulas[4] if len(celulas) > 4 else ""
        periodo_txt = celulas[5] if len(celulas) > 5 else ""
        g = re.match(r"\s*(\d{1,2})\b", grupo_txt)
        p = re.match(r"\s*(\d)\b", periodo_txt)
        out[z] = {"simbolo": simbolo, "nome": (apelido or nome).strip(),
                  "grupo": int(g.group(1)) if g else None, "periodo": int(p.group(1)) if p else None}
    return out


def gerar(offline: bool) -> dict:
    meta = baixar(offline)
    pub = json.loads((CACHE / "pubchem.json").read_text(encoding="utf-8"))
    colunas = pub["Table"]["Columns"]["Column"]
    linhas = [dict(zip(colunas, r["Cell"])) for r in pub["Table"]["Row"]]
    padrao, abreviado = ler_ciaaw(CACHE / "ciaaw_padrao.htm"), ler_ciaaw(CACHE / "ciaaw_abreviado.htm")
    wiki = ler_wikipedia(CACHE / "wikipedia_pt.txt")
    assert len(linhas) == 118 and len(padrao) == 118 and len(abreviado) == 118 and len(wiki) == 118, "fontes incompletas"

    fe = next(r for r in linhas if r["Symbol"] == "Fe")  # conferência de unidades (registro detalhado do Fe)
    assert (fe["Density"], fe["MeltingPoint"], fe["AtomicRadius"]) == ("7.874", "1811", "194"), "unidades da PubChem mudaram"

    avisos, elementos = [], []
    for r in linhas:
        z, simbolo = int(r["AtomicNumber"]), r["Symbol"]
        assert padrao[z][1] == simbolo == abreviado[z][1] == wiki[z]["simbolo"], f"símbolo divergente em Z={z}"
        periodo, grupo, bloco = classificar(z)
        w = wiki[z]
        if w["periodo"] is not None and w["periodo"] != periodo:
            avisos.append(f"{simbolo}: período {periodo} (regra) × {w['periodo']} (Wikipédia)")
        if grupo is not None and w["grupo"] is not None and w["grupo"] != grupo:
            avisos.append(f"{simbolo}: grupo {grupo} (regra) × {w['grupo']} (Wikipédia)")
        nome = PT_BR.get(w["nome"], w["nome"])
        ano = r["YearDiscovered"]
        props = []
        peso = peso_padrao(padrao[z][3], abreviado[z][3])
        if peso:
            props.append({"codigo": "peso_atomico_padrao", "unidade": "adimensional", "fonte": "ciaaw_2024", **peso})
        else:
            props.append({"codigo": "massa_isotopica_referencia", "valor": str(_num(r["AtomicMass"])), "unidade": "u",
                          "fonte": "pubchem_tabela_periodica",
                          "nota": "Sem peso atômico padrão na CIAAW (sem composição isotópica terrestre característica). "
                                  "Massa atômica informada pela PubChem; não é peso atômico padrão."})
        for coluna, (codigo, unidade) in PROPRIEDADES_PUBCHEM.items():
            if r[coluna]:
                props.append({"codigo": codigo, "valor": str(_num(r[coluna])), "unidade": unidade,
                              "fonte": "pubchem_tabela_periodica"})
        elementos.append({
            "numero_atomico": z, "simbolo": simbolo, "nome": nome, "nome_en": padrao[z][2],
            "periodo": periodo, "grupo": grupo, "bloco": bloco,
            "categoria": CATEGORIAS[r["GroupBlock"]],
            "configuracao_eletronica": r["ElectronConfiguration"] or None,
            "estados_oxidacao": r["OxidationStates"] or None,
            "estado_padrao": ESTADOS[r["StandardState"]],
            "ano_descoberta": int(ano) if ano.isdigit() else None,
            "conhecido_antiguidade": ano == "Ancient",
            "propriedades": props,
        })
    hoje = date.today().isoformat()
    return {
        "versao_dados": VERSAO,
        "descricao": ("Tabela periódica completa (118 elementos): identidade, classificação e propriedades atômicas. "
                      "Estado inicial aguardando_validacao: fontes de referência citadas, sem revisão humana registrada (ADR-014)."),
        "convencoes": {
            "grupos": "IUPAC, 18 colunas (2022). Lantanídeos 57–71 e actinídeos 89–103 no bloco f, sem número de grupo.",
            "peso_atomico_padrao": "Valor abreviado da CIAAW (±incerteza); intervalo do valor padrão quando houver.",
            "nomes": "pt-BR: Wikipédia em português, com a grafia normalizada para o Brasil (mapa PT_BR do importador).",
        },
        "fontes": {k: {**v, "acessado_em": hoje} for k, v in FONTES.items()},
        "fontes_brutas": meta,
        "conferencias": avisos,
        "elementos": elementos,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    dados = gerar(args.offline)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = sum(len(e["propriedades"]) for e in dados["elementos"])
    print(f"{len(dados['elementos'])} elementos, {n} valores → {SAIDA.relative_to(RAIZ)}")
    for a in dados["conferencias"]:
        print("  conferência:", a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
