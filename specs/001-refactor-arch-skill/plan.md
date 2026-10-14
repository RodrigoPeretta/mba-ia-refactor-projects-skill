# Implementation Plan: Skill `refactor-arch`

**Branch**: `001-refactor-arch-skill` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-refactor-arch-skill/spec.md`

## Summary

Construir uma Custom Skill do Claude Code, `refactor-arch`, composta por um `SKILL.md`
orquestrador e 6 arquivos de referência em Markdown, que conduz o agente por três fases sobre
o projeto do diretório atual: **Análise** (perfil da stack e da arquitetura por heurísticas),
**Auditoria** (cruzamento com um catálogo de anti-patterns, relatório padronizado salvo em
`.refactor-arch/audit-report.md` e pausa obrigatória para confirmação) e **Refatoração**
(captura do comportamento original, reestruturação para MVC guiada por um playbook de
transformações, validação subindo a aplicação e chamando todos os endpoints). A mesma pasta
é copiada sem alterações para os 3 projetos-alvo; a execução parte sempre da tag `baseline`.
As decisões técnicas estão em [research.md](research.md).

## Technical Context

**Language/Version**: Markdown (instruções para o agente). Projetos-alvo: Python 3.13
(Flask 3.0/3.1) e Node.js 22 (Express 4).

**Primary Dependencies**: Claude Code ≥ 2.1 com Custom Skills (`.claude/skills/`). Na
validação: `curl` e o runtime de cada projeto (`python -m venv`, `npm`). Na refatoração:
apenas bibliotecas já presentes na stack (ex.: `werkzeug.security`, `crypto` do Node).

**Storage**: arquivos Markdown gerados pela skill em `<projeto>/.refactor-arch/`. Projetos-alvo
usam SQLite (arquivo ou memória).

**Testing**: validação em execução (boot + chamadas HTTP reais comparadas com a referência
"antes"), conferência manual dos findings contra o código e checklist de validação do
enunciado. Não há suíte automatizada nos projetos-alvo.

**Target Platform**: Windows 11 (máquina de execução) e POSIX; a skill traz comandos para
ambos.

**Project Type**: skill de agente (prompt + base de conhecimento), aplicada a web APIs.

**Performance Goals**: N/A (execução interativa única por projeto).

**Constraints**: `SKILL.md` < 500 linhas; nenhuma escrita no código do projeto antes da
confirmação; pasta da skill idêntica nos 3 projetos; sem regras específicas de um projeto;
sem segredos literais no código refatorado.

**Scale/Scope**: 3 projetos de ~150 a ~1.000 linhas; catálogo com ≥ 8 anti-patterns
(planejados: 21) e playbook com ≥ 8 transformações (planejadas: 15).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Status |
|---|---|---|
| I. Agnóstica (NON-NEGOTIABLE) | Detecção por manifesto/imports (`project-analysis.md`); catálogo com sinais para Python e JS; sem nomes de projetos nas regras; validação com `curl` em vez de script atrelado a um runtime (R3); cópia única copiada para os 3 projetos e conferida por hash (quickstart) | ✅ |
| II. Confirmação antes de modificar (NON-NEGOTIABLE) | Fases 1–2 somente leitura; install e boot da aplicação movidos para a Fase 3 (R12); única escrita antes do "y" é `.refactor-arch/audit-report.md` (R4); `git status` após recusar é critério do quickstart | ✅ |
| III. Achados verificáveis | Template com arquivo/linhas obrigatórios; passo explícito de conferência das linhas antes de emitir o relatório; regra "não inventar" e seção de deprecated com "nenhuma encontrada" | ✅ |
| IV. Comportamento preservado e validado | Referência "antes" capturada após o "y" e roteiro repetido "depois" (R8); proteger em vez de remover (R7); loop corrigir/revalidar com relato de falha | ✅ |
| V. Conhecimento nas referências | `SKILL.md` orquestrador + 6 referências cobrindo as 5 áreas (a 6ª é o procedimento de validação); progressive disclosure por fase | ✅ |
| VI. Iteração reprodutível | Tag `baseline` + reset documentado no quickstart; iterações registradas no README | ✅ |

**Re-check pós-design (Fase 1)**: ✅ sem violações — os artefatos de design (data-model,
contrato de interface, quickstart) não introduzem dependência de projeto específico nem
escrita antes da confirmação.

## Project Structure

### Documentation (this feature)

```text
specs/001-refactor-arch-skill/
├── spec.md              # especificação (/speckit-specify)
├── plan.md              # este arquivo
├── research.md          # decisões da Fase 0
├── data-model.md        # entidades e formatos (perfil, finding, relatório, referência)
├── quickstart.md        # roteiro de validação ponta a ponta
├── contracts/
│   └── skill-interface.md   # invocação, saídas por fase, arquivos gravados
├── checklists/
│   └── requirements.md  # qualidade da spec
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
code-smells-project/
└── .claude/skills/refactor-arch/          # fonte da verdade da skill
    ├── SKILL.md                           # orquestrador das 3 fases (< 500 linhas)
    └── references/
        ├── project-analysis.md            # área 1: heurísticas de stack, DB, domínio, arquitetura
        ├── anti-patterns.md               # área 2: catálogo (≥ 8) + APIs deprecated
        ├── report-template.md             # área 3: formato da Fase 1, Fase 2 e Fase 3
        ├── mvc-guidelines.md              # área 4: camadas, responsabilidades, layouts alvo
        ├── refactoring-playbook.md        # área 5: transformações antes/depois (≥ 8)
        └── validation-procedure.md        # apoio à Fase 3: boot, roteiro HTTP, encerramento

ecommerce-api-legacy/.claude/skills/refactor-arch/   # cópia idêntica
task-manager-api/.claude/skills/refactor-arch/       # cópia idêntica

reports/
├── audit-project-1.md                     # cópia de code-smells-project/.refactor-arch/audit-report.md
├── audit-project-2.md
└── audit-project-3.md

docs/analise-manual.md                     # análise manual (vira seção do README)
README.md                                  # documentação final do desafio
```

**Structure Decision**: a skill é desenvolvida em `code-smells-project/` (exigência do
enunciado) e copiada para os outros dois projetos. As referências ficam em uma subpasta
`references/` para separar visualmente o orquestrador da base de conhecimento; o `SKILL.md`
aponta para cada arquivo no momento da fase em que ele é necessário:

| Fase | Arquivos carregados |
|---|---|
| 1 — Análise | `project-analysis.md`, `report-template.md` (formato Fase 1) |
| 2 — Auditoria | `anti-patterns.md`, `report-template.md` (formato Fase 2) |
| 3 — Refatoração | `mvc-guidelines.md`, `refactoring-playbook.md`, `validation-procedure.md`, `report-template.md` (formato Fase 3) |

### Conteúdo planejado das referências

- **project-analysis.md**: tabela manifesto → linguagem (`requirements.txt`/`pyproject.toml`
  → Python; `package.json` → Node; `go.mod`, `pom.xml`, `Gemfile`, `composer.json` como
  extensão); detecção de framework por dependência + import; extração de versão; detecção do
  entry point e do comando de execução (README, `scripts.start`, `if __name__`); banco
  (driver/ORM) e tabelas (`CREATE TABLE`, classes de model, `__tablename__`); inferência de
  domínio a partir de rotas e entidades; rubrica de arquitetura (monolítica / parcialmente
  em camadas / em camadas); regras de contagem de arquivos-fonte (exclui `.venv`,
  `node_modules`, `.claude`, `.refactor-arch`, arquivos gerados).
- **anti-patterns.md** (21 entradas planejadas, AP-01…AP-21): CRITICAL (6) — SQL injection,
  segredos hardcoded, senha em texto plano/hash fraco, dado sensível exposto em resposta ou
  log, God Class/Module, endpoint administrativo ou de execução arbitrária sem autenticação;
  HIGH (5) — regra de negócio em controller/rota, estado global mutável, escrita múltipla
  sem transação, debug/bind aberto em produção, acoplamento sem injeção de dependência;
  MEDIUM (6) — N+1/agregação em loop, duplicação de lógica, tratamento de erro genérico/não
  centralizado, validação ausente, configuração fixa no código/CORS aberto, **APIs
  deprecated** (tabela Python/Node + warnings de runtime/install); LOW (4) — magic numbers,
  código morto/imports não usados, `print`/`console.log` como logging, nomes crípticos.
  Cada uma com sinais de busca por linguagem, falsos positivos e ID da transformação.
- **report-template.md**: formatos exatos das três saídas, baseados no exemplo do
  enunciado, com regras de ordenação, contagem e seção de deprecated.
- **mvc-guidelines.md**: responsabilidades e regras de dependência de cada camada (config,
  models + services de domínio, views/routes, controllers, middlewares, composition root);
  layouts alvo para monolito e para projeto parcialmente em camadas (R5); regras de
  preservação do contrato e do comando de execução; escopo de segurança da Fase 3 (R7).
- **refactoring-playbook.md** (15 transformações planejadas, RF-01…RF-15, cada uma com
  antes/depois em Python e/ou JS): queries parametrizadas; segredos → config/env; hash de
  senha; allowlist de serialização; proteção de rota administrativa por token; God Class →
  camadas; fat controller → model/service; estado global → instância injetada; transação em
  escrita múltipla; N+1 → JOIN/eager loading/GROUP BY; error handler centralizado; validação
  extraída; substituição de APIs deprecated; constantes nomeadas + logging + limpeza de
  código morto; callbacks aninhados → async/await.
- **validation-procedure.md**: preparar ambiente isolado; checar porta; subir em background;
  polling; montar o inventário de endpoints a partir das rotas registradas; montar
  requisições (exemplos do projeto → campos obrigatórios); ordem de execução; registrar
  `behavior-before.md`; resetar o banco; repetir e registrar `validation-after.md`;
  comparar; encerrar a árvore de processos (Windows/POSIX) e conferir a porta.

## Complexity Tracking

Sem violações da constitution a justificar.
