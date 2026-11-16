# Aprovação do contrato R1 pelo Supervisor (portão G1) — 12/11/2026

Contrato: `docs/architecture/2026-11-12_contrato_R1.md` (api-architect, R1-API-01).
Decisão: **APROVADO COM RESSALVAS** para implementação pelo backend-engineer. O contrato foi lido pelo
Supervisor pelo relatório do arquiteto; nenhum teste foi executado sobre ele.

## Respostas às dúvidas do arquiteto

| Dúvida | Decisão |
|---|---|
| D-a `ThermalRequest.liga` com `solutos` | Em R1, `/thermodynamics/thermal` recusa liga multicomponente com 400 `liga_multicomponente_nao_suportada`. O motor térmico não foi especificado para isso. |
| D-b caso `Xx` em `scripts/contrato_frontend.mts` | O backend-engineer troca SÓ esse caso (o arquivo tem alteração anterior não commitada, que deve ser preservada). |
| D-c gabarito do exercício de FEA (V-15) | Aceito: o exercício corrige contra o valor do motor. Fica pendência de revisão pelo pedagogical-engineer. |
| D-d `a_em_R`/`raio_relativo` × `fea` novo no HC | Não alterar nesta rodada; registrar em `convencoes`/aviso. Pendência para o crystallography-engineer. |
| D-e letras de Wyckoff | `wyckoff: null` nos campos novos até conferência do auditor bibliográfico. |
| D-f versão do motor de cristalografia | 2.1.0. |
| D-g produção com massas não validadas | É o pretendido: produção é estrita; base mássica indisponível com motivo. |
| D-h faixas com `verificada: false` | A API sempre envia a marca; o front exibe a faixa com o rótulo "limiar não verificado na fonte". |
| 7.1 a 7.13 (decisões próprias do arquiteto) | Aceitas, inclusive V-14 fora do contrato e `temperatura_k` fora de R1. |

## Ressalvas

- V-1 a V-16 são mudanças de valor ou de comportamento. Entram no histórico de alterações e precisam de
  teste de regressão que fixe o valor novo com a derivação do parecer correspondente.
- ΔH_mix, Ω e a curva de ΔG continuam `null`: a matriz de pares (Q-01) não existe no repositório.
- Nenhuma referência bibliográfica foi verificada; todos os `criterios` saem com `verificada: false`.
