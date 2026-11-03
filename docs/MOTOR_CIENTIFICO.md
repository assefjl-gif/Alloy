# Motor científico (cristalografia e temperatura; HEA em [MOTOR_HEA.md](MOTOR_HEA.md))

Núcleo único de cálculo do Alloy Virtual Lab (ADR-004). Código em `backend/app/engines/`.

## 1. Princípios verificados por teste

| Princípio | Como é garantido | Teste |
|---|---|---|
| Motores puros, sem I/O | Análise estática de imports (`ast`): proíbe `app.api`, `app.repositories`, `app.models`, FastAPI, SQLAlchemy, `open`, `pathlib`, `os` etc. Verificado com violação injetada | `tests/unit/test_arquitetura.py` |
| Uma única constante de Avogadro (CODATA 2018) | Só uma definição de `N_AVOGADRO` em `app/` | idem |
| Resultado igual ao B | Saídas congeladas de A, B e D; motor = B com tolerância 1e-12 | `tests/scientific/test_regressao_versoes.py` |
| Toda divergência explicada | A/D × motor: só N_A (CIE-02), Ti com rede medida (ADR-005) e arredondamento prematuro da HC em A/D (CR-08, ~5e-7) | idem |
| Banco não altera dado | Motor com repositório SQL = motor com JSON, campo a campo | `tests/integration/test_persistencia.py` |

## 2. Módulos

| Módulo | Conteúdo | Origem | Classe do resultado |
|---|---|---|---|
| `crystallography/celula.py` | Célula, rede medida/derivada/**informada** (*a* → R), FEA, densidade | B + v1.4 | analítico |
| `crystallography/passos.py` | Passo a passo de *a* e do FEA (fecha D-12) | v1.4 | analítico |
| `crystallography/miller.py` | (hkl)/(hkil), direções, **famílias de planos em supercélula** | B + v1.4 | analítico |
| `crystallography/planar.py` | Densidade e fração planar **só para famílias validadas** | v1.4 | analítico |
| `crystallography/supercelula.py` | Blocos n×n×n (n ≤ 4), HC em célula primitiva (fecha D-10) | v1.4 | analítico |
| `crystallography/ligas.py` | Vegard, % at ↔ % peso, Hume-Rothery, intersticiais, protótipos ordenados, distorção | v1.4 | estimativa de modelo (distorção: simulação ilustrativa) |
| `crystallography/exportacao.py` | CIF e XYZ | B | — |
| `thermodynamics/termico.py` | Dilatação linear, Lindemann, alotropia, mistura | v1.4 | estimativa de modelo |
| `procedencia.py` | Valor com estado e fonte, política por ambiente, bloco `procedencia` | novo | — |

## 3. Referências dos modelos

| Modelo | Referência | Onde |
|---|---|---|
| Relações de contato, FEA, densidade | Callister & Rethwisch, seções 3.4–3.5 | `celula.py`, `passos.py` |
| Densidade planar (CFC/CCC/CS {100},{110},{111}; HC (0001)) | Callister & Rethwisch, seção 3.11; valores fechados conferidos (ex.: CFC(111) = π/(2√3)) | `planar.py` |
| Lei de Vegard | Vegard, Z. Phys. 5, 17–26 (1921) | `ligas.py` |
| % atômica ↔ % em peso | Callister & Rethwisch, eq. 4.6–4.7 | `ligas.py` |
| Hume-Rothery (±15 %, estrutura, valência) | Callister & Rethwisch, seção 4.3 | `ligas.py` |
| Eletronegatividade ±0,4 | Darken & Gurry, Physical Chemistry of Metals (1953) | `ligas.py` |
| Regra de Hägg (r/R < 0,59) | Hägg (1931), via literatura de intersticiais | `ligas.py` |
| Raio livre dos sítios (CCC 0,155R; CFC/HC 0,414R; CS 0,732R) | Geometria de esferas rígidas (derivação analítica) | `ligas.py` |
| Dilatação linear | Callister & Rethwisch, seção 19.3 | `termico.py` |
| Critério de Lindemann (f = 0,10) | Lindemann, Phys. Z. 11, 609–612 (1910) | `termico.py` |

> As referências citadas pela edição do Callister ainda precisam de edição e página (CR-10, Q-03). As demais referências também devem ser conferidas pelo validador científico antes da publicação.

## 4. Política de dados (PI-02, ADR-014)

| Dado | Estado inicial | Em `dev`/`test` | Em `prod` |
|---|---|---|---|
| Seed do B (raio, massa, densidade, c/a, *a* do Ti) | `aguardando_validacao` | usado, com aviso | **usado, com aviso** (já estava em produção na v1.1; ver decisão abaixo) |
| Dados da v1.4 (χ, valência, T_f, α, raios de C/N/H, alotropia) | `rascunho`, sem fonte | usados, com aviso em `procedencia.avisos` e listados em `dados_usados` | **recusados** (`DADO_NAO_VALIDADO`). Regras de Hume-Rothery que dependem deles ficam `indisponivel`; Vegard e densidade continuam |

**Decisão registrada (complemento do ADR-014):** o seed do B alimenta o motor de células em todos os ambientes, com aviso explícito. Bloqueá-lo deixaria a aplicação sem a função central até a validação humana. Os dados novos da v1.4 nunca tiveram fonte e por isso ficam bloqueados em produção.

## 5. Mudanças de comportamento em relação às origens

| Mudança | Antes | Agora | Por quê |
|---|---|---|---|
| Repositório | Padrão implícito (`repositorio_padrao()` dentro do motor) | Injetado obrigatoriamente | Motor puro (ADR-004) |
| Densidade planar | A publicava para qualquer plano | Só famílias validadas; demais retornam `validado: false` + motivo | CIE-04 |
| Ordenação L1₂/L1₀/B2 | A apresentava como fase | Protótipo geométrico com aviso "hipotético" | Ex.: Fe–Cr não forma B2 (forma σ) |
| *a* informado | Só na A, sem `a_fonte` | `a_fonte = "informado"`, R derivado com validação de faixa | Rastreabilidade |
| Densidade do Ti | A/D: 4,792 g/cm³ (+6,3 %) | 4,500 g/cm³ (−0,2 %) | ADR-005 |

## 6. Limitações conhecidas

- A validação CIF com Gemmi está prevista, mas o Gemmi não tem pacote para Python 3.15 nesta máquina. O teste fica pulado aqui e deve rodar no CI com Python 3.11–3.13.
- O α do modelo térmico é constante: abaixo de 20 °C é extrapolação (a resposta avisa).
- A fração 0,10 de Lindemann é o limite inferior da faixa ~0,1–0,15 citada na literatura.
- A distorção de rede é ilustrativa e não resolve elasticidade.
