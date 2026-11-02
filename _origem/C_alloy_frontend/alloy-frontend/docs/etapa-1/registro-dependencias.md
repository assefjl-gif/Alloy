# Registro de dependências pendentes (1.9 — atualizado até a Etapa 8)

Cada item é algo que o front-end **não pode** fazer corretamente sem um serviço ou dado que hoje não existe. Para cada um, a interface usa um adaptador e mostra o estado (desativado com explicação, ou modo demonstrativo rotulado). O mesmo registro é exibido dentro do app em **Configurações → Pendências** (`src/services/adapters/pending.ts`), para que ninguém confunda demonstração com produção.

| ID | Pendência | Quem resolve | Comportamento atual do front |
|---|---|---|---|
| D-01 | Motor HEA (`hea_engine.py`) ausente no projeto; `pesquisa_front1.17.py` não executa | Back-end HEA | Módulo HEA em modo **demonstrativo** com valores fictícios de semente fixa; detecta e usa `/api/analyze` real quando o servidor existir |
| D-02 | Campo de estrutura sugerida no resultado HEA | Back-end HEA | Regra de correspondência: estrutura única citada em `fase` → abertura direta; senão, escolha do usuário rotulada |
| D-03 | Turmas, tarefas, avaliações (modo professor) | Back-end plataforma | Rascunhos locais; botão Publicar informa que **nada foi publicado** |
| D-04 | Workspaces no servidor | Back-end plataforma | Armazenamento local rotulado + exportar/importar JSON |
| D-05 | Exportação CIF/XYZ fora da versão FastAPI | Back-end CrystaLab | Habilitada só quando `/v1/export/*` responde; com o servidor stdlib fica desativada com explicação |
| D-06 | Exportação PDF pelo motor | Back-end CrystaLab | PDF pelo diálogo de impressão do navegador (folha de estilo de impressão) |
| D-07 | Parâmetros térmicos (coeficiente de expansão) | Dados/motor | Animação de expansão térmica **ilustrativa**, sem números |
| D-08 | Serviço de IA generativa | Plataforma | Recurso desativado e identificado; adaptador pronto |
| D-09 | Coordenadas fracionárias da HC (`base`, previsto na v1.1.0) | Back-end CrystaLab | Painel do átomo mostra fracionárias só se `base` vier; senão informa a ausência |
| D-10 | Vetores de rede explícitos na resposta | Back-end CrystaLab | Supercélula usa a convenção de desenho documentada (cúbica: eixos unitários; HC: prisma hexagonal) |
| D-11 | Poliedros de coordenação e famílias de planos | Back-end CrystaLab | Opções desativadas com explicação |
| D-12 | Passos intermediários do FEA | Back-end CrystaLab | Fórmula simbólica exibida; valores intermediários não são inventados |
| D-13 | Camadas compactas (posições A/B/C) para a animação de empilhamento | Back-end CrystaLab | Animação esquemática rotulada como ilustração, sem medidas |
| D-14 | Código da v1.1.0 (`crystalab/` com `/v1`, CSP, Three local) — só o changelog está no projeto | Equipe | Front compatível com campos aditivos da v1.1.0; testado contra a v1.0 |
| D-15 | Contrato OpenAPI executável (`/openapi.json`) | Back-end CrystaLab | Contratos TypeScript manuais + validação zod em tempo de execução |
| D-16 | Polônio sem fonte autorizada (referências §5) e Ti com +6,26 % (CR-01, corrigido só na v1.1.0) | Especialista em materiais | Avisos exibidos a partir de `avisos` quando o motor enviar; o front não corrige valores |
| D-17 | Faixas de parâmetros para exercícios gerados | Especialista em materiais | Exercícios usam apenas materiais do catálogo do motor; faixas livres desativadas até validação |
| D-18 | Sincronização de notas offline com servidor | Back-end plataforma | Notas ficam neste navegador; aviso de recuperação ao reconectar |
| D-19 | Ferramentas de build/QA do plano (Vite, ESLint, axe-core, Lighthouse CI) — registro npm bloqueado neste ambiente | Equipe (CI) | Build com esbuild, lint próprio, auditoria de acessibilidade própria; ver `docs/decisoes-tecnicas.md` |
| D-20 | Medições no equipamento-alvo (notebook intermediário, celular real, leitor de tela) | QA | Medido apenas em contêiner headless; metas não declaradas atingidas |
