import math
import csv
import io
import os
import base64
import webbrowser
from itertools import combinations
from typing import Dict, Any, List
import matplotlib.pyplot as plt
from io import BytesIO

# ==========================================
# 1. BASE DE DADOS E CONFIGURAÇÕES
# ==========================================
# Base de dados atualizada com Eletronegatividade (chi)
CSV_MOD = """Elemento,Raio,Tm,VEC,chi
Al,1.43,933.0,3.0,1.61\nCo,1.25,1768.0,9.0,1.88\nCr,1.25,2180.0,6.0,1.66
Cu,1.28,1358.0,11.0,1.90\nFe,1.24,1811.0,8.0,1.83\nMn,1.12,1519.0,7.0,1.55
Ni,1.25,1728.0,10.0,1.91\nMo,1.39,2896.0,6.0,2.16\nNb,1.46,2750.0,5.0,1.60
Ta,1.46,3290.0,5.0,1.50\nW,1.39,3695.0,6.0,2.36\nTi,1.46,1941.0,4.0,1.54
V,1.34,2183.0,5.0,1.63\nZr,1.60,2128.0,4.0,1.33\nHf,1.59,2506.0,4.0,1.30"""


def carregar_elementos(caminho_arquivo: str = "elementos.csv") -> Dict[str, Dict[str, float]]:
    elementos = {}
    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            for linha in leitor:
                elementos[linha['Elemento'].strip()] = {
                    'r': float(linha['Raio']),
                    'Tm': float(linha['Tm']),
                    'VEC': float(linha['VEC']),
                    'chi': float(linha['chi'])
                }
    else:
        print(f"[!] Ficheiro '{caminho_arquivo}' não encontrado. A usar base de dados interna.")
        leitor = csv.DictReader(io.StringIO(CSV_MOD))
        for linha in leitor:
            elementos[linha['Elemento'].strip()] = {
                'r': float(linha['Raio']),
                'Tm': float(linha['Tm']),
                'VEC': float(linha['VEC']),
                'chi': float(linha['chi'])
            }
    return elementos


# Variáveis Globais declaradas na ordem correta
ELEMENTOS = carregar_elementos()

ENTALPIA_MISTURA = {
    ('Al', 'Co'): -19, ('Al', 'Cr'): -10, ('Al', 'Cu'): -1, ('Al', 'Fe'): -11, ('Al', 'Mn'): -19, ('Al', 'Ni'): -22,
    ('Co', 'Cr'): -4, ('Co', 'Cu'): 6, ('Co', 'Fe'): -1, ('Co', 'Mn'): -5, ('Co', 'Ni'): 0,
    ('Cr', 'Cu'): 12, ('Cr', 'Fe'): -1, ('Cr', 'Mn'): 2, ('Cr', 'Ni'): -7,
    ('Cu', 'Fe'): 13, ('Cu', 'Mn'): 4, ('Cu', 'Ni'): 4,
    ('Fe', 'Mn'): 0, ('Fe', 'Ni'): -2, ('Mn', 'Ni'): -8,
    ('Ti', 'Al'): -30, ('Ti', 'V'): 0, ('Mo', 'Nb'): 0, ('Mo', 'Ta'): 0, ('Mo', 'W'): 0,
    ('Nb', 'Ta'): 0, ('Nb', 'W'): 0, ('Ta', 'W'): 0
}


def obter_entalpia(el1, el2):
    return ENTALPIA_MISTURA.get((el1, el2), ENTALPIA_MISTURA.get((el2, el1), 0.0))


REFERENCIA_CANTOR = {
    'dS': 13.38, 'dH': -4.12, 'delta': 1.18, 'omega': 1.1, 'VEC': 8.0,
    'T_padrao': "298.15 K", 'P_padrao': "1 atm"
}


# ==========================================
# 2. MOTOR TERMODINÂMICO E MECÂNICO
# ==========================================
def analisar_liga(nome: str, composicao_bruta: Dict[str, float]) -> Dict[str, Any]:
    R = 8.314
    for el in composicao_bruta.keys():
        if el not in ELEMENTOS: return {'nome': nome, 'erro': f"Elemento '{el}' desconhecido."}

    composicao = {el: qtd for el, qtd in composicao_bruta.items() if qtd > 0}
    total = sum(composicao.values())
    fracoes = {el: (qtd / total) for el, qtd in composicao.items()}
    elementos = list(fracoes.keys())

    if len(elementos) < 2: return {'nome': nome, 'erro': "Precisa de pelo menos 2 elementos."}

    dS_mix = -R * sum(c * math.log(c) for c in fracoes.values())
    Tm_mix = sum(fracoes[el] * ELEMENTOS[el]['Tm'] for el in elementos)
    vec_medio = sum(fracoes[el] * ELEMENTOS[el]['VEC'] for el in elementos)

    dH_mix = 0.0
    for el1, el2 in combinations(elementos, 2):
        hij = obter_entalpia(el1, el2)
        dH_mix += 4 * hij * fracoes[el1] * fracoes[el2]

    raio_medio = sum(fracoes[el] * ELEMENTOS[el]['r'] for el in elementos)
    delta_raio = math.sqrt(sum(fracoes[el] * (1 - (ELEMENTOS[el]['r'] / raio_medio)) ** 2 for el in elementos)) * 100

    omega = (Tm_mix * dS_mix) / abs(dH_mix * 1000) if dH_mix != 0 else float('inf')

    # Cálculos Mecânicos (Ductilidade e Eletronegatividade)
    chi_medio = sum(fracoes[el] * ELEMENTOS[el]['chi'] for el in elementos)
    delta_chi = math.sqrt(sum(fracoes[el] * (ELEMENTOS[el]['chi'] - chi_medio) ** 2 for el in elementos))

    ductilidade = "Desconhecida"
    fase_prevista = "Desconhecida"

    if vec_medio >= 8.0:
        fase_prevista = "CFC (Cúbica Face Centrada)"
        ductilidade = "Alta (Muito Dúctil e Maleável)"
    elif vec_medio <= 6.8:
        fase_prevista = "CCC (Cúbica Corpo Centrado)"
        ductilidade = "Baixa (Dura, mas Quebradiça)"
    else:
        fase_prevista = "Fase Dupla (CFC + CCC)"
        ductilidade = "Média (Balanço Dureza/Maleabilidade)"

    if delta_chi > 0.15:
        ductilidade += " [ALERTA: Risco de Intermetálicos Frágeis]"

    # Regras e Veredito Termodinâmico
    elementos_traco = [k for k, v in fracoes.items() if v < 0.05]
    if elementos_traco:
        veredito = "FALHA: Regra de Yeh (Dopante < 5%)"
    elif max(fracoes.values()) > 0.50:
        veredito = "FALHA: Liga Diluída (> 50%)"
    elif dS_mix < 11.0:
        veredito = "INSTÁVEL: Baixa Entropia (< 11 J/mol.K)"
    elif dH_mix < -15 or dH_mix > 5:
        veredito = "INSTÁVEL: Entalpia Extrema"
    elif delta_raio > 6.6:
        veredito = "INSTÁVEL: Colapso de Rede (δ > 6.6%)"
    elif omega < 1.1:
        veredito = "INSTÁVEL: Ômega baixo (Entalpia domina)"
    else:
        veredito = "ESTÁVEL (HEA): Solução Sólida Confirmada"

    return {
        'nome': nome, 'comp': fracoes, 'dS': dS_mix, 'dH': dH_mix,
        'delta': delta_raio, 'omega': omega, 'Tm': Tm_mix, 'VEC': vec_medio,
        'delta_chi': delta_chi, 'fase': fase_prevista, 'ductilidade': ductilidade,
        'veredito': veredito
    }


# ==========================================
# 3. GERAÇÃO DE GRÁFICOS (Base64)
# ==========================================
def gerar_graficos(resultados: List[Dict]) -> tuple:
    resultados_validos = [r for r in resultados if 'erro' not in r]

    plt.figure(figsize=(8, 5))
    plt.axhspan(-15, 5, xmin=0, xmax=0.66, color='green', alpha=0.1, label='Zona de Estabilidade')
    for res in resultados_validos:
        plt.scatter(res['delta'], res['dH'], s=100, label=res['nome'], edgecolor='black', zorder=5)
    plt.axvline(6.6, color='red', linestyle='--', alpha=0.5)
    plt.xlabel('Distorção Atómica, δ (%)')
    plt.ylabel('Entalpia de Mistura, ΔH (kJ/mol)')
    plt.title('Mapa de Estabilidade Termodinâmica (Zhang)')
    plt.legend()
    plt.grid(True, linestyle=':')

    buf1 = BytesIO()
    plt.savefig(buf1, format='png', bbox_inches='tight')
    img_mapa = base64.b64encode(buf1.getvalue()).decode()
    plt.close()

    plt.figure(figsize=(8, 5))
    temp_range = range(300, 3000, 50)
    for res in resultados_validos:
        g_ss = [res['dH'] * 1000 - t * res['dS'] for t in temp_range]
        plt.plot(list(temp_range), g_ss, label=res['nome'])

    plt.axhline(0, color='black', linewidth=1)
    plt.xlabel('Temperatura (K)')
    plt.ylabel('Energia Livre de Gibbs, ΔG (J/mol)')
    plt.title('Estabilidade de Fase (ΔG < 0)')
    plt.legend()
    plt.grid(True, linestyle=':')

    buf2 = BytesIO()
    plt.savefig(buf2, format='png', bbox_inches='tight')
    img_gibbs = base64.b64encode(buf2.getvalue()).decode()
    plt.close()

    return img_mapa, img_gibbs


# ==========================================
# 4. GERAÇÃO DO RELATÓRIO HTML (Automático)
# ==========================================
def gerar_relatorio_pdf(resultados: List[Dict]):
    img_mapa, img_gibbs = gerar_graficos(resultados)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; max-width: 1000px; margin: auto; padding: 40px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 30px; font-size: 14pt; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10pt; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            th {{ background-color: #2c3e50; color: white; }}
            .diff-pos {{ color: green; font-weight: bold; }}
            .diff-neg {{ color: red; font-weight: bold; }}
            .card {{ background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #eee; }}
            .mecanica {{ background-color: #e8f4f8; padding: 10px; border-left: 4px solid #3498db; margin-top: 15px; font-size: 11pt; }}
            .img-box {{ text-align: center; margin: 20px 0; }}
            .img-box img {{ width: 90%; max-width: 800px; border: 1px solid #ccc; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h1>Relatório Avançado de Materiais: HEAs</h1>
        <p><i>Referência Comparativa: Liga de Cantor | Condições: {REFERENCIA_CANTOR['T_padrao']}, {REFERENCIA_CANTOR['P_padrao']}</i></p>
    """

    for res in resultados:
        if 'erro' in res:
            html += f"<div class='card'><h3 style='color:red;'>{res['nome']} - ERRO</h3><p>{res['erro']}</p></div>"
            continue

        cor_veredito = "green" if "ESTÁVEL" in res['veredito'] else "red"

        html += f"""
        <div class="card">
            <h3 style="margin-top:0;">Liga: {res['nome']}</h3>
            <p><strong>Veredito:</strong> <span style="color:{cor_veredito}; font-weight:bold;">{res['veredito']}</span></p>

            <table>
                <tr>
                    <th>Parâmetro</th><th>Calculado</th><th>Referência (Cantor)</th><th>Diferença</th>
                </tr>
                <tr>
                    <td>Entropia (ΔS)</td><td>{res['dS']:.2f}</td><td>{REFERENCIA_CANTOR['dS']}</td>
                    <td class="{'diff-pos' if res['dS'] >= REFERENCIA_CANTOR['dS'] else 'diff-neg'}">
                        {((res['dS'] / REFERENCIA_CANTOR['dS']) - 1) * 100:+.1f}%
                    </td>
                </tr>
                <tr>
                    <td>Ômega (Ω)</td><td>{res['omega']:.2f}</td><td>{REFERENCIA_CANTOR['omega']}</td>
                    <td class="{'diff-pos' if res['omega'] >= REFERENCIA_CANTOR['omega'] else 'diff-neg'}">
                        {((res['omega'] / REFERENCIA_CANTOR['omega']) - 1) * 100:+.1f}%
                    </td>
                </tr>
                <tr>
                    <td>Distorção (δ)</td><td>{res['delta']:.2f}%</td><td>{REFERENCIA_CANTOR['delta']}%</td>
                    <td>{res['delta'] - REFERENCIA_CANTOR['delta']:+.2f} (Abs)</td>
                </tr>
            </table>

            <div class="mecanica">
                <strong>Previsão Mecânica e Estrutural:</strong><br>
                • <b>Fase Cristalina:</b> {res['fase']} (VEC: {res['VEC']:.2f})<br>
                • <b>Ductilidade:</b> {res['ductilidade']}
            </div>
        </div>
        """

    html += f"""
        <h2>Mapas e Gráficos Termodinâmicos</h2>
        <div class="img-box"><img src="data:image/png;base64,{img_mapa}" /></div>
        <div class="img-box"><img src="data:image/png;base64,{img_gibbs}" /></div>
    </body></html>
    """

    nome_ficheiro = "Relatorio_HEAs.html"
    caminho_absoluto = os.path.abspath(nome_ficheiro)

    with open(nome_ficheiro, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[SUCESSO] Relatório gerado! A abrir no navegador...")
    webbrowser.open(f"file://{caminho_absoluto}")


# ==========================================
# 5. EXECUÇÃO E TESTES
# ==========================================
if __name__ == "__main__":
    ligas_teste = [
        {"nome": "Liga de Cantor Original (Dúctil)", "comp": {'Co': 1, 'Cr': 1, 'Fe': 1, 'Mn': 1, 'Ni': 1}},
        {"nome": "Liga Refratária de Senkov (Dura)", "comp": {'Mo': 1, 'Nb': 1, 'Ta': 1, 'W': 1}},
        {"nome": "Liga com Cobre", "comp": {'Co': 1, 'Cr': 1, 'Cu': 2, 'Mn': 1, 'Ni': 1}}
    ]

    resultados_processados = []

    print(f"{'=' * 60}\nPROCESSAMENTO DE LIGAS\n{'=' * 60}")
    for liga in ligas_teste:
        res = analisar_liga(liga['nome'], liga['comp'])
        resultados_processados.append(res)

        if 'erro' in res:
            print(f"[!] {res['nome']}: ERRO -> {res['erro']}")
        else:
            print(f"[*] {res['nome']:<35} | Veredito: {res['veredito']}")

    # Gerar o relatório HTML no navegador
    gerar_relatorio_pdf(resultados_processados)