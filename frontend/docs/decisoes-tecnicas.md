# Decisões técnicas

| # | Decisão | Por quê | Consequência |
|---|---|---|---|
| DT-01 | **Nenhum valor científico é calculado no front-end.** Densidade, FEA, a, posições, Miller e estabilidade vêm do motor | Regra inegociável do plano | Sem motor, os cálculos ficam indisponíveis — nunca simulados. A única geometria local (distâncias/ângulos entre posições do motor, réplicas) é rotulada como “geometria do visualizador” |
| DT-02 | esbuild 0.28 no lugar do Vite; lint próprio no lugar do ESLint; `.editorconfig` no lugar do Prettier | Registro npm bloqueado no ambiente (D-19) | Mesmo empacotador interno do Vite; troca mecânica quando houver registro |
| DT-03 | Contratos TypeScript manuais validados com zod em tempo de execução | Não há `/openapi.json` executável (D-15) | Resposta fora do contrato vira erro tipado “contrato”, nunca dado parcial |
| DT-04 | Toda E/S passa por `services/api/http.ts` (regra R1 do lint) com AbortController, tempo-limite e `LatestRunner` | Cancelamento e descarte de respostas obsoletas (2.7/4.11) | Uma resposta antiga nunca sobrescreve a cena atual |
| DT-05 | Modo demonstrativo explícito: `config.js`, `?demo=`, preferência; semente fixa; selo em todo dado fictício | 2.6 e regra de rotulagem | `Math.random` proibido (R2); dados demonstrativos reproduzíveis |
| DT-06 | Roteador por hash e estado de cena em `?s=v1.<base64url>` validado por esquema estrito (≤ 1 800 caracteres) | Servidor Python sem reescrita de rotas; links seguros | Campos desconhecidos, versão errada ou tamanho excessivo são recusados com mensagem |
| DT-07 | Uma camada de operações (`commands/bus.ts`) para terminal, formulários, paleta e viewer; `toCommand` gera o comando canônico | Sem caminhos divergentes (Sugestão 3) | Teste de equivalência cobre 49 operações |
| DT-08 | Viewer: Three.js r160 local e sob demanda, render sob demanda, `InstancedMesh`, nível de detalhe por tamanho de cena | Orçamento do bundle e GPU parada sem uso | Inicial 201 kB gzip; 0 quadros com a cena parada |
| DT-09 | Supercélula HC com prisma de 3 células primitivas e convenção de translação documentada | O motor não envia vetores de rede (D-10) | Réplicas só gráficas e excluídas das contagens |
| DT-10 | Resultado HEA transportado como cópia congelada; na URL vai só a impressão digital, a cópia fica na aba | O resultado completo não cabe no limite da URL | Recarregar mantém a cópia; alteração é detectada e recusada |
| DT-11 | i18n gerado de tabelas TSV com as 3 línguas lado a lado; tipagem das chaves derivada do pt-BR | Chave inexistente é erro de compilação; tradução faltante é erro de teste | Textos que vêm do motor continuam em português, com aviso |
| DT-12 | Design system por tokens CSS; 6 categorias + nota com cor, ícone, rótulo e padrão de borda | Cor nunca é o único código (7.4) | Contraste dos pares de tokens testado automaticamente nos dois temas |
| DT-13 | Service worker: pré-cache dos ativos com hash; network-first para HTML/config; stale-while-revalidate só para tabelas do motor; POST nunca em cache | Offline sem servir cálculo velho | Cálculos offline mostram “exige servidor” |
| DT-14 | Auditoria de acessibilidade própria via árvore de acessibilidade do Chromium | axe-core/Lighthouse indisponíveis (D-19) | Cobre 12 regras; não substitui Lighthouse nem leitor de tela |
| DT-15 | Testes contra o motor real e um servidor de contrato `/v1` apenas para teste | “Nunca simular produção” | O servidor `/v1` reproduz rotas do FastAPI usando as funções do próprio motor |
