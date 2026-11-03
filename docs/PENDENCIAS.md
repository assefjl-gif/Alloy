# Pendências

Atualizado na Fase 10. "Responsável" = quem precisa agir; nada aqui se resolve só com código.

## Decisões e insumos humanos

| ID | Pendência | Bloqueia | Responsável | Ação |
|---|---|---|---|---|
| Q-01 | Entalpias binárias de mistura (Miedema / Takeuchi & Inoue) com fonte | ΔH_mix, Ω, veredito HEA, curva G×T | Responsável pelo projeto | Fornecer a tabela ou o dataset de referência ([MOTOR_HEA §5](MOTOR_HEA.md)) |
| Q-02 | Hospedagem | Publicação | Responsável | Escolher o host (o compose roda em qualquer VM com Docker) |
| Q-03 | Validador científico | Promover dados a `validado`, liberar δ, T_m, VEC, ligas e temperatura em produção | Responsável | Nomear um professor; conferir o Callister (edição e página, CR-10), o *a* do Ti, os dados da v1.4 e a tabela VEC (Guo 2011) |
| Q-04 | Provedor de e-mail | Verificação de e-mail e recuperação de senha | Responsável | SMTP institucional ou serviço transacional |
| Q-05 | SSO institucional | Opcional | TI da UFC | Consultar disponibilidade |
| Q-06 | Licença do projeto e dos dados | Repositório científico aberto | Responsável | Definir |
| Q-07 | Publicar o repositório no GitHub | Execução do CI (Linux/Windows, PostgreSQL, imagens) | Responsável | Criar o repositório e fazer o push |

## Limitações do ambiente usado na consolidação

| ID | Limitação | Efeito | Como fechar |
|---|---|---|---|
| L-01 | Sem PostgreSQL | 23 variantes PostgreSQL dos testes puladas | Job `backend-linux` do CI, ou `ALLOY_TEST_POSTGRES_URL` local |
| L-02 | Sem Docker | Imagens, compose e Caddyfile não executados | Job `imagens` do CI ou Docker Desktop |
| T-01 | Gemmi sem pacote para Python 3.15 | 1 teste de validação CIF pulado | CI com Python 3.12 (`.[validacao]`) |

## Técnicas (próximas implementações)

| ID | Pendência | Prioridade | Observação |
|---|---|---|---|
| T-02 | Gatilho de soma da composição (`composicao_itens`) | média | escrever e testar com PostgreSQL |
| T-03 | *a* medido com fonte para os outros 14 metais | média | ADR-005 pleno; depende de Q-03 |
| T-04 | API de instituições, turmas e matrículas | alta | as tabelas e o RBAC existem; hoje os vínculos são criados direto no banco |
| T-05 | Atividades, atribuições a turmas, entregas e notas | alta | tabelas prontas; o Fluxo C completo (professor → turma → desempenho) depende de T-04 |
| T-06 | Limitador de login compartilhado (banco ou Redis) | média antes de escalar | hoje vale por processo |
| T-07 | `pip-audit` e `npm audit` no CI | média | varredura de dependências |
| T-08 | Migrar as atividades didáticas locais (`#/aprender`) para os geradores do servidor | média | o servidor já tem 3 geradores; o front local continua como prática offline |
| T-09 | Diagrama de fases (`/thermodynamics/phase-diagram`) | baixa | especificação em A/docs/2 |
| T-10 | Repositório de materiais e ligas (`/materials`, `/sources`) e upload de tutoriais (`/files`) | média | Fluxo D; tabelas prontas |
| T-11 | Remover os aliases `/v1` | baixa | depois de confirmar que não há clientes antigos |
| T-12 | E2E 4.9 (gerenciador de camadas) intermitente: 1 falha em uma rodada completa, 5/5 isolado | baixa | investigar com trace no CI; possível corrida entre comandos de terminal enviados em sequência |
