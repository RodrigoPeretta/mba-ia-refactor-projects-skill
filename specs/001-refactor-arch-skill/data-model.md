# Data Model: Skill `refactor-arch`

As "entidades" desta feature são as estruturas de informação que a skill produz e consome
entre as fases. Elas não são persistidas em banco: existem como blocos de texto no terminal
e como arquivos Markdown em `<projeto>/.refactor-arch/`.

## ProjectProfile (saída da Fase 1)

| Campo | Descrição | Regra |
|---|---|---|
| `language` | Linguagem principal (ex.: Python, JavaScript/Node.js) | Derivada do manifesto + extensão dos arquivos-fonte |
| `framework` | Framework web e versão (ex.: Flask 3.1.1) | Versão lida do manifesto; se for faixa (`^4.18.2`), mostrar a faixa |
| `dependencies` | Dependências diretas relevantes | Lista do manifesto, sem dependências transitivas |
| `database` | Banco e forma de acesso (driver cru / ORM) | Ex.: SQLite via `sqlite3`; SQLite via SQLAlchemy |
| `tables` | Tabelas/entidades de dados | De `CREATE TABLE`, classes de model, `__tablename__` |
| `domain` | Domínio de negócio em uma linha | Inferido de rotas + entidades |
| `architecture` | `monolítica` \| `parcialmente em camadas` \| `em camadas` + justificativa curta | Rubrica de `project-analysis.md` |
| `source_files` | Quantidade e lista de arquivos-fonte analisados | Exclui `.venv/`, `node_modules/`, `.claude/`, `.refactor-arch/`, lockfiles, bancos, `__pycache__/` |
| `loc` | Linhas de código aproximadas | Soma dos arquivos-fonte |
| `run` | Como instalar, preparar (ex.: seed) e iniciar a aplicação, e a porta | De README, `scripts` do manifesto, `app.run`/`listen` |
| `endpoints` | Inventário método + rota | Das rotas registradas no código |

## AntiPattern (catálogo — `references/anti-patterns.md`)

| Campo | Descrição |
|---|---|
| `id` | Identificador estável (ex.: `AP-01`) |
| `name` | Nome do anti-pattern |
| `severity` | Severidade-base: CRITICAL \| HIGH \| MEDIUM \| LOW |
| `signals` | Sinais de detecção concretos, por linguagem (padrões de busca, construções) |
| `false_positives` | Casos parecidos que **não** são o anti-pattern |
| `fix` | ID(s) da transformação no playbook (ex.: `RF-01`) |

Regra: o catálogo tem ≥ 8 entradas e pelo menos uma por severidade; uma entrada é
dedicada a APIs deprecated.

## Finding (ocorrência na Fase 2)

| Campo | Descrição | Validação |
|---|---|---|
| `severity` | Severidade efetiva | Parte da severidade-base; pode subir ou descer um nível com justificativa (ex.: ocorrência isolada e sem exposição) |
| `title` | Nome do anti-pattern ou variação específica | — |
| `antipattern_id` | Referência ao catálogo | Deve existir no catálogo |
| `file` | Caminho relativo à raiz do projeto | Deve existir |
| `lines` | Linha ou intervalo (`7`, `12-40`), ou várias (`28, 47-50`) | Conferidas por leitura antes de emitir |
| `description` | O que está errado, com o trecho/valor relevante | Factual |
| `impact` | Consequência concreta | — |
| `recommendation` | Correção, com referência à transformação do playbook | — |

Agrupamento: ocorrências do mesmo anti-pattern no mesmo arquivo viram **um** finding com
várias linhas; em arquivos diferentes, um finding por arquivo ou um finding com a lista de
`arquivo:linhas`, conforme o template.

## AuditReport (saída da Fase 2 — `.refactor-arch/audit-report.md`)

- Cabeçalho: projeto, stack, número de arquivos e linhas analisados.
- `summary`: contagem por severidade (`CRITICAL: n | HIGH: n | MEDIUM: n | LOW: n`).
- `findings`: lista ordenada CRITICAL → HIGH → MEDIUM → LOW.
- `deprecated_apis`: findings dessa categoria **ou** a declaração "Nenhuma API deprecated
  encontrada", com o que foi verificado.
- `total`: igual à soma do `summary` e ao tamanho de `findings`.
- Encerramento: pergunta de confirmação da Fase 3.

## BehaviorRecord (Fase 3 — `behavior-before.md` e `validation-after.md`)

| Campo | Descrição |
|---|---|
| `step` | Ordem de execução |
| `method`, `path` | Endpoint |
| `request` | Headers relevantes e corpo enviado |
| `status` | Código HTTP recebido |
| `shape` | Tipo do corpo (JSON objeto/lista, texto) e chaves de nível superior |
| `note` | Observações (ex.: "500 no original — defeito conhecido") |

Comparação "antes × depois" por `step`:
- **OK**: mesmo status e mesma forma.
- **CHANGED (intencional)**: diferença causada por uma correção listada (ex.: 500 → 400,
  rota admin agora exige token, campo `senha` removido).
- **REGRESSION**: qualquer outra diferença, ou falha de conexão — bloqueia a conclusão da
  Fase 3 até ser corrigida ou reportada.

## Transformation (playbook — `references/refactoring-playbook.md`)

| Campo | Descrição |
|---|---|
| `id` | Identificador (ex.: `RF-01`) |
| `name` | Nome do padrão de transformação |
| `fixes` | IDs do catálogo que ela resolve |
| `steps` | Passos de aplicação |
| `before` / `after` | Código de exemplo (genérico, Python e/ou JS) |
| `verify` | Como confirmar que a transformação funcionou |

## Transições de estado da execução

```text
START → PHASE_1_DONE → PHASE_2_DONE ─┬─ (resposta ≠ "y") → END_NO_CHANGES
                                     └─ ("y") → BEHAVIOR_CAPTURED → REFACTORED
                                                 → VALIDATING ─┬─ todos OK/CHANGED → END_SUCCESS
                                                               └─ REGRESSION → (corrigir) → VALIDATING
                                                                   └─ (sem solução) → END_REPORTED_FAILURE
```
