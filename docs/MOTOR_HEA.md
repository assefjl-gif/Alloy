# Motor HEA

Código: `backend/app/engines/hea/analitico.py` (versão do motor **1.0.0**). Rotas:
`GET /api/v1/hea/bootstrap` e `POST /api/v1/hea/analyses` (ver [API.md](API.md)).

## 1. Princípio

O motor calcula **só o que tem base citável** (PI-02). Uma grandeza sem base volta como `null`, e o
motivo vem em `indisponiveis`. A interface mostra "—" e o motivo. Nenhum valor é estimado para
preencher a tela: dureza, ductilidade, ΔH_mix, Ω e a curva de Gibbs ficam indisponíveis até haver
modelo e dados com fonte (questão **Q-01**).

O HEA Virtual Lab v1.17 (fonte do contrato do frontend) dependia de um `hea_engine` que nunca fez
parte do material recebido (achado D-01 da auditoria). Por isso este motor foi **construído do zero**
a partir da literatura. Não é um porte.

## 2. Grandezas

| Grandeza | Fórmula | Classe | Dados usados | Fonte do modelo |
|---|---|---|---|---|
| ΔS_mix | −R·Σ xᵢ ln xᵢ | analítico (solução ideal) | nenhum (só a composição) | entropia configuracional de Boltzmann |
| δ | 100·√(Σ xᵢ(1 − rᵢ/r̄)²), r̄ = Σ xᵢ rᵢ | estimativa | raio atômico (seed base, `aguardando_validacao`) | Zhang et al., *Adv. Eng. Mater.* 10, 534 (2008) |
| T_m | Σ xᵢ·T_f,ᵢ | estimativa (regra das misturas) | temperatura de fusão (seed v1.4, `rascunho`) | prática usual na literatura de HEA |
| VEC | Σ xᵢ·VECᵢ | estimativa | VEC (seed `hea/vec.json`, `aguardando_validacao`) | Guo et al., *J. Appl. Phys.* 109, 103505 (2011) |
| fase | VEC ≥ 8,0 → CFC; VEC < 6,87 → CCC; entre os dois → CFC + CCC | estimativa | VEC | Guo et al. (2011) |
| ΔH_mix, Ω | — | **indisponível** | entalpias binárias de Miedema (inexistentes) | Yang & Zhang, *Mater. Chem. Phys.* 132, 233 (2012) |

R = 8,314462618 J/(mol·K) (CODATA 2018). As quantidades informadas são normalizadas para frações molares.

**Limiares** devolvidos no bootstrap: ΔS_mix ≥ 1,5R (definição por entropia), δ ≤ 6,6 %,
Ω ≥ 1,1 e VEC 8,0. São critérios da literatura, não dados de material.

**Veredito:** sem Ω não existe veredito de estabilidade. O texto começa com `INCONCLUSIVO —` e lista
os critérios parciais (δ favorável ou desfavorável).

## 3. Política de dados

* **dev/test:** valores `rascunho` e `aguardando_validacao` são usados. Cada um aparece em
  `procedencia.dados_usados`, e um aviso é emitido.
* **prod:** só valores `validado` com fonte são usados. Como nenhum está validado ainda, a produção devolve
  **apenas ΔS_mix**. δ, T_m e VEC voltam `null`, cada um com o motivo. `/meta/capabilities` informa
  "Parcial".

## 4. Verificação

* `tests/unit/engines/test_hea.py`: ΔS = R·ln n para ligas equimolares (n = 2…6); AlCoCrFeNi conferido à mão
  (δ, VEC = 7,2, T_m); critério CCC para CrMoW (VEC = 6,0); política de produção; entradas inválidas.
* `tests/api/test_api.py`: CoCrFeNi (VEC 8,25 → CFC), bootstrap, elemento sem dados e produção (só ΔS_mix).
* `tests/integration/test_servico_calculo.py`: resultado pelo banco é igual ao do seed JSON, e a execução fica
  gravada no histórico.
* Contrato real: `scripts/contrato_frontend.mts` valida as respostas HEA com os esquemas zod do front.

## 5. Para completar o motor (Q-01)

1. Cadastrar a matriz de ΔH_mix binária (Miedema / Takeuchi & Inoue, 2005) **com fonte e revisão**, em
   uma tabela de pares. O banco já prevê `composicao_itens` e `valores_propriedade`.
2. Calcular ΔH_mix = Σ_{i<j} 4·ΔH_ij·xᵢxⱼ e Ω = T_m·ΔS_mix/|ΔH_mix|. Só então emitir veredito.
3. Curva G×T: ΔG = ΔH_mix − T·ΔS_mix, como `simulacao_ilustrativa`.
4. Dureza e ductilidade: só com modelo publicado e dataset. O ML continua reservado (`engines/machine_learning/`).
