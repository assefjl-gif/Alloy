# Alloy Virtual Lab — instruções para o Claude Code

Plataforma de engenharia de materiais para ensino e pesquisa: **CrystaLab** (células unitárias, Miller,
densidade, soluções sólidas, temperatura), **HEA** (ligas de alta entropia), contas com histórico e
questões corrigidas no servidor. Visão geral e comandos: [README.md](README.md).

## Princípios do projeto

1. **Nenhum dado científico inventado.** Todo resultado traz `procedencia`. O que não tem base volta `null`, com o motivo.
2. **Um motor, um lugar.** A ciência roda só no backend (`backend/app/engines/`). O front exibe e não recalcula.
3. **Produção é estrita:** dados não validados são recusados, a demonstração é proibida e os segredos são obrigatórios.
4. Código que executa não é resultado científico validado. Validação exige parecer do especialista e fonte verificável.

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `backend/` | FastAPI: `app/engines/` (motores), `services/`, `api/` (`/api/v1`), `models/`, `repositories/`, `security/`, `educational/`; testes em `tests/` |
| `frontend/` | React 19 + TypeScript, viewer Three.js, design system em `src/design-system/`, testes em `tests/` |
| `database/` | migrações Alembic, DDL de referência, seeds versionados |
| `infrastructure/`, `docker-compose.yml`, `.github/` | Docker, Caddy, observabilidade, CI |
| `scripts/` | exportação do OpenAPI, teste de contrato, geração de seed |
| `docs/` | arquitetura, API, banco, motores, requisitos, gates, relatórios |
| `docs/agents/` | especificações dos 15 agentes e a hierarquia (documentos originais) |
| `docs/agent_reports/`, `docs/architecture/`, `docs/research/` | relatórios de agentes, decisões de arquitetura, inventário bibliográfico |
| `_origem/`, `_auditoria/` | bases recebidas (**somente leitura**) e scripts da auditoria |

## Equipe de agentes

- **`docs/agents/`** guarda as especificações originais (fonte da verdade). **`.claude/agents/`** guarda os 15 subagentes
  que o Claude Code reconhece, gerados a partir delas. Se divergirem, vale o documento original.
- **Hierarquia e workflow:** `docs/agents/16_hierarquia_dos_agentes_e_workflow.md`. Leia antes de coordenar trabalho de várias áreas.
- **`supervisor`** coordena: recebe o pedido, monta tarefas com responsável único, delega, exige evidência, aprova pelos
  portões G0 a G5 e reporta ao usuário. Para usá-lo como sessão principal: `claude --agent supervisor`.
- **Especialistas:** `api-architect`, `backend-engineer`, `database-engineer`, `frontend-engineer`, `integration-engineer`,
  `materials-science-specialist`, `hea-specialist`, `crystallography-engineer`, `machine-learning-engineer`,
  `pedagogical-engineer`, `learning-analytics`, `adversarial-qa-tester`, `devsecops-engineer`, `academic-research-auditor`.
- Só o supervisor tem a ferramenta `Agent`. Os especialistas pedem consultas no relatório e o supervisor as encaminha.
- Cada subagente recebe só as ferramentas de que precisa (por exemplo, o QA não tem `Edit`).

## Fluxo de trabalho

1. **Planejar:** entender o pedido, inspecionar o estado real do repositório (os documentos podem estar defasados) e registrar a linha de base.
2. **Delegar:** um responsável por entrega, com arquivos permitidos e proibidos, dependências e critérios de aceite.
3. **Executar:** mudanças pequenas e reversíveis, só no escopo autorizado, com testes.
4. **Revisar:** QA, parecer científico, auditoria bibliográfica e segurança conforme a tarefa.
5. **Integrar e consolidar:** só entregas aprovadas; relatório final com fontes, testes reais, limitações e pendências.

## Regras

- Entenda a arquitetura antes de propor mudanças. Não reestruture em larga escala sem pedido.
- Depois de qualquer alteração autorizada, rode os testes relevantes e informe o resultado real:
  - backend: `cd backend && ../.venv/Scripts/python -m pytest`
  - frontend: `cd frontend && npm run typecheck && npm run lint && npm test` (e `npm run e2e` para fluxos)
- Registre decisões, alterações, evidências, riscos e limitações (histórico em `docs/HISTORICO_DE_ALTERACOES.md`, relatórios em `docs/agent_reports/`).
- Não declare "testado", "validado" ou "seguro" sem ter executado a verificação.
- **Não modifique código, banco de dados ou infraestrutura sem autorização explícita.** Não faça commit, push, deploy, migração nem exclusão de dados sem pedido do usuário.
- **Credenciais:** não leia, imprima nem registre `.env`, tokens, senhas ou dados pessoais de estudantes. Use `.env.example` como referência.
- Contratos de API, esquema do banco e fórmulas científicas só mudam com contrato ou parecer documentado e aprovação.
