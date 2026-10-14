<!--
Sync Impact Report
Version change: (template) → 1.0.0
Modified principles: n/a (adoção inicial)
Added sections: Core Principles I–VI, Restrições Técnicas, Fluxo de Trabalho, Governance
Removed sections: none
Templates requiring updates:
  ✅ .specify/templates/plan-template.md (Constitution Check genérico, lido em runtime)
  ✅ .specify/templates/spec-template.md (genérico, sem alteração)
  ✅ .specify/templates/tasks-template.md (genérico, sem alteração)
Follow-up TODOs: none
-->

# Refactor-Arch Skill Constitution

## Core Principles

### I. Skill Agnóstica de Tecnologia (NON-NEGOTIABLE)
A skill `refactor-arch` MUST detectar stack, framework, banco e arquitetura por heurísticas
(manifestos de dependência, imports, entry points), nunca por conhecimento prévio de um
projeto específico. O `SKILL.md` e os arquivos de referência MUST NOT citar nomes de
arquivos, rotas, tabelas ou domínios dos projetos-alvo como regra; exemplos de código são
permitidos apenas como ilustração genérica de um padrão. A mesma pasta da skill MUST ser
copiada sem alterações para os 3 projetos, e o critério de pronto é funcionar em 3/3.
Rationale: o enunciado avalia agnosticismo justamente rodando a skill em stacks e níveis de
organização diferentes; uma skill acoplada a um projeto falha nos outros dois.

### II. Confirmação Humana Antes de Qualquer Modificação (NON-NEGOTIABLE)
As Fases 1 (Análise) e 2 (Auditoria) são somente leitura sobre o código do projeto-alvo. Ao
final da Fase 2 a skill MUST parar e pedir confirmação explícita; sem resposta afirmativa
nenhum arquivo do projeto-alvo é criado, alterado, movido ou removido. A única escrita
permitida antes da confirmação é o próprio relatório de auditoria, fora do código-fonte.
Rationale: requisito obrigatório do enunciado; o humano revisa o relatório antes da
refatoração.

### III. Achados Verificáveis e Classificados
Todo finding MUST ter arquivo e linha(s) exatos, severidade na escala do enunciado
(CRITICAL, HIGH, MEDIUM, LOW, baseada em MVC/SOLID), descrição, impacto e recomendação,
e o relatório MUST seguir o template de referência, ordenado de CRITICAL para LOW. A skill
MUST NOT inventar findings para atingir mínimos: se uma categoria não se aplica (ex.: APIs
deprecated inexistentes), o relatório declara isso explicitamente. Linhas citadas MUST ser
conferidas no arquivo antes de entrar no relatório.
Rationale: o checklist de validação exige arquivo/linha exatos e ordenação; achados falsos
destroem a confiança no relatório e levam a refatorações erradas.

### IV. Refatoração Preserva Comportamento e é Validada em Execução
A Fase 3 MUST reestruturar o projeto para MVC (config, models, views/routes, controllers,
error handling centralizado, entry point claro) preservando o contrato público: rotas,
métodos HTTP, formato do JSON e códigos de status de sucesso. Correções de segurança que
alteram contrato (ex.: remover senha da resposta, exigir token em rota administrativa) são
permitidas e preferidas a remover a rota, e MUST ser listadas no resumo final. A validação
MUST ser feita executando a aplicação (boot sem erro + chamada real a todos os endpoints
originais), não por leitura de código; falha na validação obriga a corrigir antes de
declarar a fase concluída.
Rationale: critério de aceite eliminatório ("aplicação funciona após refatoração" em 3/3).

### V. Conhecimento nas Referências, Orquestração no SKILL.md
O `SKILL.md` MUST ser um orquestrador enxuto das 3 fases, carregando os arquivos de
referência sob demanda (progressive disclosure). As referências, em Markdown, MUST cobrir
as 5 áreas exigidas: heurísticas de análise de projeto, catálogo de anti-patterns (≥ 8, com
severidades distribuídas e detecção de APIs deprecated), template de relatório, guidelines
da arquitetura MVC alvo e playbook de refatoração (≥ 8 transformações com código
antes/depois). Sinais de detecção MUST ser acionáveis ("SQL montado por concatenação com
entrada do request"), nunca vagos ("código ruim").
Rationale: separa o "como agir" (prompt) do "o que saber" (domínio), mantém o contexto do
agente pequeno e torna cada área revisável isoladamente.

### VI. Iteração Rastreável e Reprodutível
Cada execução da skill MUST partir do código original (tag git `baseline`), para que
iterações sejam comparáveis. Mudanças na skill entre iterações, e o motivo, MUST ser
registradas no README; resultados (findings por severidade, validação) MUST ser reportados
como observados, inclusive falhas.
Rationale: o enunciado prevê 2–4 iterações; sem baseline a segunda rodada audita código já
refatorado e os números deixam de ter significado.

## Restrições Técnicas

- **Ferramenta**: Claude Code, com Custom Skills em `.claude/skills/refactor-arch/`. O nome
  `refactor-arch` e o arquivo `SKILL.md` são fixos.
- **Formato**: `SKILL.md` + arquivos de referência em Markdown, na mesma pasta da skill.
- **Projetos-alvo**: `code-smells-project/` (Python/Flask), `ecommerce-api-legacy/`
  (Node.js/Express), `task-manager-api/` (Python/Flask parcialmente em camadas).
- **Dependências na refatoração**: preferir biblioteca padrão e dependências já presentes
  (ex.: `werkzeug.security`, `crypto` do Node) a adicionar pacotes; toda dependência nova
  MUST ser justificada no resumo da Fase 3.
- **Segredos**: nenhuma credencial hardcoded no código refatorado; configuração via
  variáveis de ambiente com defaults seguros para desenvolvimento e `.env.example`
  documentando as variáveis.
- **Entregáveis**: relatórios em `reports/audit-project-{1,2,3}.md` na raiz do repositório;
  código refatorado commitado; README com as seções Análise Manual, Construção da Skill,
  Resultados e Como Executar.

## Fluxo de Trabalho

Ordem: (1) análise manual dos 3 projetos (`docs/analise-manual.md`), (2) SDD via spec-kit —
`/speckit-constitution` → `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` →
`/speckit-implement` — produzindo a skill, (3) execução de `/refactor-arch` em cada projeto a
partir da tag `baseline`, salvando o relatório da Fase 2 e commitando o resultado da Fase 3,
(4) iteração na skill quando algum critério de aceite falhar, com nova cópia para os 3
projetos, (5) README final. Cada artefato do SDD é apresentado ao usuário antes da fase
seguinte.

## Governance

Esta constitution rege as decisões deste desafio e prevalece sobre práticas ad-hoc.
Qualquer desvio (ex.: endpoint removido em vez de protegido, critério de aceite não atingido
em algum projeto) MUST ser justificado explicitamente no README. Emendas são feitas via
`/speckit-constitution`, com versionamento semântico: MAJOR para remoção/redefinição de
princípio, MINOR para princípio ou seção nova, PATCH para clarificações. Todo
`/speckit-plan` MUST incluir um Constitution Check contra os seis princípios acima.

**Version**: 1.0.0 | **Ratified**: 2026-10-08 | **Last Amended**: 2026-10-08
