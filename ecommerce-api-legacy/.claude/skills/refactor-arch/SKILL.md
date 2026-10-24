---
name: refactor-arch
description: Audita e refatora para o padrão MVC um projeto backend de qualquer linguagem ou framework, em 3 fases — análise da stack e da arquitetura, relatório de auditoria de anti-patterns (severidade, arquivo e linha exatos) com pausa para confirmação, e refatoração validada subindo a aplicação e chamando os endpoints. Use quando o usuário pedir auditoria arquitetural, detecção de code smells/anti-patterns ou refatoração de um projeto legado para MVC.
argument-hint: "[caminho-do-relatorio]"
disable-model-invocation: true
---

# refactor-arch — Auditoria e Refatoração Arquitetural

Você é um arquiteto de software sênior. O projeto-alvo é o **diretório de trabalho atual**.
Execute as fases abaixo **em ordem**, sem pular nenhuma. A skill é agnóstica de tecnologia:
tudo o que você afirmar sobre o projeto deve vir dos arquivos dele, nunca de suposição.

Argumento recebido: `$ARGUMENTS`
- Vazio → o relatório da Fase 2 vai para `.refactor-arch/audit-report.md`.
- Preenchido → o relatório vai para esse caminho (relativo ao diretório atual).

## Regras globais (valem para todas as fases)

1. **Fases 1 e 2 são somente leitura.** Permitido: ler arquivos, listar, buscar (Glob/Grep),
   `git status`/`git log`. Proibido antes da confirmação: editar, criar, mover ou apagar
   arquivos do projeto, instalar dependências, subir a aplicação ou rodar seeds/migrations.
   A **única** escrita permitida antes da confirmação é o arquivo do relatório.
2. **Nada sem evidência.** Todo finding cita arquivo e linhas que você **leu** e conferiu.
   Não invente findings para atingir números; se uma categoria não se aplica, diga isso.
3. **Agnóstico.** Use as heurísticas das referências; não assuma framework, estrutura de
   pastas ou comandos que você não viu no projeto.
4. **Idioma.** Rótulos e cabeçalhos exatamente como no template (em inglês); descrições,
   impactos e recomendações em português (pt-BR).
5. **Contrato preservado.** Na Fase 3, rotas, métodos HTTP, formato das respostas e status de
   sucesso continuam os mesmos, exceto as mudanças de segurança previstas nas guidelines — e
   toda mudança de contrato é listada no resumo final.
6. **Honestidade no resultado.** Se a validação falhar e você não conseguir corrigir,
   reporte a falha. Nunca declare sucesso sem ter executado a validação.

## Arquivos de referência (carregue somente na fase indicada)

| Fase | Leia |
|---|---|
| 1 — Análise | `${CLAUDE_SKILL_DIR}/references/project-analysis.md` e a seção "Fase 1" de `${CLAUDE_SKILL_DIR}/references/report-template.md` |
| 2 — Auditoria | `${CLAUDE_SKILL_DIR}/references/anti-patterns.md` e a seção "Fase 2" de `${CLAUDE_SKILL_DIR}/references/report-template.md` |
| 3 — Refatoração | `${CLAUDE_SKILL_DIR}/references/mvc-guidelines.md`, `${CLAUDE_SKILL_DIR}/references/refactoring-playbook.md`, `${CLAUDE_SKILL_DIR}/references/validation-procedure.md` e a seção "Fase 3" de `${CLAUDE_SKILL_DIR}/references/report-template.md` |

---

## Fase 1 — Análise do projeto

1. Leia `project-analysis.md`.
2. Rode `git status --short` (se for um repositório git) e guarde o resultado: ele é a
   referência para provar que nada mudou até a confirmação.
3. Liste os arquivos do projeto e separe os **arquivos-fonte** conforme as regras de
   exclusão da referência. Leia **todos** os arquivos-fonte por inteiro, além do manifesto de
   dependências, README e arquivos de exemplo de requisições, se existirem.
4. Preencha o perfil do projeto: linguagem, framework e versão, dependências, banco e
   tabelas, domínio, classificação da arquitetura (com a justificativa), arquivos e linhas,
   como executar (instalação, preparo, comando, porta) e o inventário de endpoints
   (método + rota + arquivo:linha onde é registrado).
5. Imprima o bloco da Fase 1 exatamente no formato do `report-template.md`.

Não pare aqui: siga direto para a Fase 2.

## Fase 2 — Auditoria

1. Leia `anti-patterns.md`.
2. Para **cada** arquivo-fonte, verifique **cada** entrada do catálogo usando os sinais de
   detecção (buscas com Grep + leitura do contexto). Registre candidatos com arquivo e linhas.
3. **Confirme cada candidato**: releia as linhas citadas e descarte o que for falso positivo
   segundo a entrada do catálogo. Ajuste a severidade só quando a entrada permitir e
   justifique na descrição.
4. Agrupe ocorrências do mesmo anti-pattern conforme as regras do template (um finding pode
   listar várias linhas ou vários `arquivo:linhas`).
5. Verifique explicitamente a categoria **APIs deprecated** (AP-17). Se não houver nenhuma,
   o relatório precisa dizer isso e listar o que foi verificado.
6. Monte o relatório no formato "Fase 2" do template: ordene CRITICAL → HIGH → MEDIUM → LOW
   e confira que o Summary, a quantidade de findings e o Total batem. Confira também a
   coerência com a Fase 1: se houver finding AP-05 (God Class/Module), a arquitetura é
   **Monolítica** — corrija a classificação no cabeçalho do relatório se a Fase 1 tiver
   dito outra coisa. As recomendações seguem a "Recomendação padrão" de cada entrada do
   catálogo, quando houver.
7. Grave o relatório no caminho definido pelo argumento (padrão
   `.refactor-arch/audit-report.md`) e imprima-o.
8. Termine com exatamente esta linha e **encerre a sua resposta** — não execute mais nada:

   `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`

### Ao receber a resposta

- `y`, `yes`, `s` ou `sim` (sem diferenciar maiúsculas): siga para a Fase 3.
- Qualquer outra resposta, inclusive vazia: responda que a refatoração foi cancelada,
  que **nenhum arquivo de código foi alterado** e onde está o relatório. Encerre.

---

## Fase 3 — Refatoração

Só entre aqui após uma confirmação afirmativa.

1. **Carregar conhecimento**: leia `mvc-guidelines.md`, `refactoring-playbook.md` e
   `validation-procedure.md`.
2. **Capturar o comportamento original** (`validation-procedure.md`, etapas 1–5): prepare o
   ambiente isolado, suba a aplicação **original**, execute o roteiro de requisições e grave
   `.refactor-arch/behavior-before.md`. Encerre o servidor e confirme a porta livre.
3. **Escolher o layout alvo** pela classificação da Fase 1 (`mvc-guidelines.md`, seção
   "Layouts alvo"): monolítico → layout novo; parcialmente em camadas → completar as camadas
   que faltam, preservando as que já cumprem sua função.
4. **Planejar**: monte a lista finding → transformação (`RF-xx` do playbook), com CRITICAL e
   HIGH primeiro. Todo finding do relatório precisa estar resolvido ou, se fora do escopo
   definido nas guidelines, listado como pendência com o motivo. Para CRITICAL e HIGH,
   **quebre a recomendação em cláusulas** (cada rota, campo ou regra que ela cita) e
   planeje cada cláusula: a recomendação é aplicada **por inteiro**, não pela metade. Se
   o login do projeto emite token, aplique RF-16: o token emitido tem que ser **validado** nas rotas
   que a recomendação manda proteger (emitir sem validar não resolve nada).
5. **Aplicar de forma incremental**, uma camada por vez: config → models/serviços →
   controllers → views/rotas → error handling/middlewares → composition root. Remova o
   código antigo só depois que o novo estiver no lugar. Mantenha o **comando de execução
   original** funcionando e crie `.env.example` com todas as variáveis introduzidas.
6. **Validar** (`validation-procedure.md`, etapas 6–9): reinicialize o banco, suba a
   aplicação refatorada com o comando original, execute **o mesmo roteiro**, grave
   `.refactor-arch/validation-after.md` e classifique cada passo como OK, CHANGED
   (intencional) ou REGRESSION.
7. **Corrigir**: enquanto houver REGRESSION ou erro de boot, corrija e repita o passo 6. Se
   após 3 tentativas ainda houver falha, pare e reporte o que falhou e por quê.
8. **Limpar** (`validation-procedure.md`, etapa 10): encerre todos os processos que você
   iniciou — inclusive processos filhos de auto-reload — e confirme as portas livres.
   Remova bancos e arquivos temporários gerados pela validação e restaure o backup do banco,
   se houver.
9. **Resumo final**: monte o bloco "Fase 3" do template com a nova estrutura (árvore),
   validação item a item, o mapa recomendação → aplicação → passo de validação (CRITICAL e
   HIGH), mudanças de contrato, dependências adicionadas (com justificativa) e pendências.
   Grave-o em `.refactor-arch/phase3-summary.md` e imprima o mesmo conteúdo no terminal.

## Antes de encerrar, confira

- [ ] O bloco da Fase 1 e o relatório da Fase 2 seguem o template.
- [ ] Todo finding tem arquivo e linhas conferidos; a ordem é CRITICAL → LOW; Summary e Total batem.
- [ ] Nenhum arquivo do projeto foi alterado antes da confirmação.
- [ ] (Fase 3) Config sem segredos literais; models, views/rotas, controllers e error handler centralizado separados; entry point claro.
- [ ] (Fase 3) A aplicação sobe com o comando original e não há REGRESSION em `validation-after.md`.
- [ ] (Fase 3) Cada cláusula das recomendações CRITICAL/HIGH foi aplicada e provada por um passo da validação, ou está em `Pending` com o motivo.
- [ ] (Fase 3) Se há login, nenhuma rota de escrita protegida aceita cliente anônimo nem token de outro usuário.
- [ ] (Fase 3) Nenhum processo iniciado por você continua rodando.
- [ ] (Fase 3) O resumo final está gravado em `.refactor-arch/phase3-summary.md`.
