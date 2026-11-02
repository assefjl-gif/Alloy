# Pendências

| ID | Pendência | Bloqueia | Responsável | Ação |
|---|---|---|---|---|
| Q-01 | Motor ou dados HEA (tabela de entalpias de pares com fonte) | Fluxo B completo, ΔH_mix e Ω | Responsável pelo projeto | Enviar código/dataset ou referência |
| Q-02 | Hospedagem | Fase 8 | Responsável | Decidir antes da Fase 8 |
| Q-03 | Validador científico | Promover dados a `validado`; liberar ligas e temperatura em produção | Responsável | Nomear professor; conferir edição/página do Callister (CR-10), *a* do Ti, dados da v1.4 |
| Q-04 | Provedor de e-mail | Cadastro e recuperação de senha | Responsável | SMTP institucional ou serviço transacional |
| Q-05 | SSO institucional | Opcional | TI da UFC | Consultar disponibilidade |
| Q-06 | Licença do projeto e dos dados | Repositório científico aberto | Responsável | Definir |
| L-01 | PostgreSQL ausente nesta máquina | Variantes PostgreSQL dos testes (21) | Equipe | Instalar PostgreSQL ou Docker, ou rodar no CI com `ALLOY_TEST_POSTGRES_URL` |
| L-02 | Docker ausente | Fase 8 | Equipe | Docker Desktop ou CI |
| L-04 | Navegadores do Playwright | E2E do frontend | Equipe | `npx playwright install chromium` na Fase 9 |
| T-01 | Gemmi sem pacote para Python 3.15 | Validação CIF (1 teste) | Equipe | Rodar no CI com Python 3.11–3.13 |
| T-02 | Gatilho de soma da composição | Integridade de `composicao_itens` | Agente 02 | Escrever com PostgreSQL disponível; até lá validar no serviço |
| T-03 | `*a*` medido com fonte para os outros 14 metais | ADR-005 pleno | Agente 02 + Q-03 | Cadastrar com fonte validada |
