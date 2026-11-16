# Alloy Virtual Lab — Biblioteca de Agentes de IA

Este pacote contém a definição operacional de uma equipe de 15 agentes especializados e um manual central de hierarquia e workflow.

## Conteúdo

| Arquivo | Agente / documento |
|---|---|
| `01_agente_supervisor_arquiteto_chefe.md` | Supervisor Geral e Arquiteto-Chefe |
| `02_agente_arquiteto_de_api.md` | Arquiteto de API |
| `03_agente_engenheiro_backend.md` | Engenheiro Backend |
| `04_agente_engenheiro_banco_de_dados.md` | Engenheiro de Banco de Dados |
| `05_agente_engenheiro_frontend.md` | Engenheiro Frontend |
| `06_agente_engenheiro_de_integracao.md` | Engenheiro de Integração |
| `07_agente_especialista_ciencia_dos_materiais.md` | Especialista em Ciência dos Materiais |
| `08_agente_especialista_hea.md` | Especialista em Ligas de Alta Entropia |
| `09_agente_engenheiro_cristalografia.md` | Engenheiro de Cristalografia |
| `10_agente_engenheiro_machine_learning.md` | Engenheiro de Machine Learning |
| `11_agente_engenheiro_pedagogico.md` | Engenheiro Pedagógico |
| `12_agente_avaliacao_learning_analytics.md` | Avaliação e Learning Analytics |
| `13_agente_tester_qa_adversarial.md` | Tester / QA Adversarial |
| `14_agente_devsecops_infraestrutura.md` | DevOps, Infraestrutura e Segurança |
| `15_agente_pesquisa_academica_e_auditoria_bibliografica.md` | Pesquisador Acadêmico e Auditor Bibliográfico |
| `16_hierarquia_dos_agentes_e_workflow.md` | Hierarquia, comunicação, portões e workflows |

## Como utilizar
1. Coloque os arquivos em uma pasta de documentação do projeto, por exemplo `docs/agents/`.
2. Leia primeiro `16_hierarquia_dos_agentes_e_workflow.md`.
3. Configure o agente orquestrador com o arquivo `01_agente_supervisor_arquiteto_chefe.md` e a instrução mestre do documento 16.
4. Forneça a cada agente apenas seu arquivo individual, o contexto necessário e a tarefa designada.
5. Exija o formato de handoff e os critérios de aceite definidos no documento 16.
6. Antes de permitir alterações, instrua os agentes a inspecionar o repositório atual. Os documentos descrevem papéis e processos; não substituem a análise do código real.

## Compatibilidade e execução
Os arquivos são especificações de comportamento e prompts de agente em Markdown. Eles não criam automaticamente agentes, não iniciam processos paralelos e não concedem permissões no Claude Code. A execução depende do mecanismo de subagentes/orquestração disponível no ambiente. Se não houver suporte a subagentes, o Supervisor pode delegar tarefas sequencialmente em sessões separadas, usando os relatórios de handoff.

## Princípio de segurança
Nenhum agente deve executar exclusões, migrações destrutivas, publicação, alteração de dados reais ou mudança de escopo sem autorização apropriada. Segredos e dados pessoais não devem ser incluídos nos prompts ou relatórios.
