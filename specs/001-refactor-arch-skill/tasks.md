---

description: "Task list for the refactor-arch skill"
---

# Tasks: Skill `refactor-arch`

**Input**: Design documents from `/specs/001-refactor-arch-skill/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/skill-interface.md, quickstart.md

**Tests**: a spec não pede suíte automatizada. A verificação de cada história é a execução
real da skill nos projetos-alvo, seguindo `quickstart.md`, e entra como tarefa da própria
história.

**Organization**: tarefas agrupadas por user story (spec.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: história atendida (US1–US5)

## Path Conventions

- `SK/` = `code-smells-project/.claude/skills/refactor-arch/` (fonte da verdade da skill)
- `SK/references/` = arquivos de referência
- Caminhos de projeto relativos à raiz do repositório `mba-ia-refactor-projects-skill/`

---

## Phase 1: Setup

**Purpose**: versionar o que já existe e criar a pasta da skill

- [ ] T001 Commitar a análise manual e os artefatos de SDD (`docs/analise-manual.md`, `.specify/`, `.claude/skills/speckit-*`, `specs/001-refactor-arch-skill/`) no branch `main`, sem tocar no código dos projetos, e enviar a tag `baseline` para o fork (`git push origin main --tags`)
- [ ] T002 Criar a estrutura `SK/` e `SK/references/` em `code-smells-project/.claude/skills/refactor-arch/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: esqueleto do orquestrador e formatos de saída usados por todas as fases

- [ ] T003 Criar `SK/SKILL.md` com frontmatter (`name: refactor-arch`, `description` dizendo o que faz e quando usar, `argument-hint: "[caminho-do-relatorio]"`, `disable-model-invocation: true`), regras globais (agnóstico; Fases 1–2 somente leitura; nada de install/boot antes do "y"; não inventar findings; idioma: rótulos em inglês e texto em pt-BR), o fluxo das 3 fases com os portões entre elas, e a tabela "fase → referências a carregar" do plan.md
- [ ] T004 [P] Criar `SK/references/report-template.md` com os 3 formatos de saída do contrato (`PHASE 1: PROJECT ANALYSIS` com Language/Framework/Dependencies/Domain/Architecture/Source files/DB tables; `ARCHITECTURE AUDIT REPORT` com cabeçalho, `## Summary`, `## Findings` em `### [SEVERITY] Título` + `File:`/`Description:`/`Impact:`/`Recommendation:`, seção de APIs deprecated, `Total` e a pergunta `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`; `PHASE 3: REFACTORING COMPLETE` com `## New Project Structure`, `## Validation`, `## Contract Changes`, `## Pending`) e as regras de ordenação CRITICAL → LOW, agrupamento de ocorrências e consistência entre Summary, lista e Total

**Checkpoint**: orquestrador e formatos prontos; as fases podem ser preenchidas

---

## Phase 3: User Story 1 - Diagnóstico do projeto (Priority: P1) 🎯 MVP

**Goal**: a skill imprime um perfil correto da stack e da arquitetura de qualquer projeto-alvo

**Independent Test**: invocar `/refactor-arch` no `code-smells-project` e conferir o bloco da Fase 1 contra o projeto real (manifesto, arquivos, tabelas)

- [ ] T005 [P] [US1] Escrever `SK/references/project-analysis.md`: tabela manifesto → linguagem (`requirements.txt`, `pyproject.toml`, `Pipfile`, `package.json`, `go.mod`, `pom.xml`, `Gemfile`, `composer.json`); detecção de framework por dependência + import, com extração da versão (faixas como `^4.18.2` mostradas como estão); detecção do banco (driver cru ou ORM) e das tabelas (`CREATE TABLE`, classes de model, `__tablename__`); inferência de domínio a partir de rotas e entidades; rubrica de arquitetura `monolítica` / `parcialmente em camadas` / `em camadas` com critérios objetivos; regras de contagem de arquivos-fonte e linhas (excluir `.venv/`, `venv/`, `node_modules/`, `.claude/`, `.refactor-arch/`, lockfiles, bancos, `__pycache__/`); como descobrir o comando de execução, passos de preparo (ex.: seed citado no README), porta e inventário de endpoints (método + rota) — todos os campos de `ProjectProfile` do data-model.md
- [ ] T006 [US1] Escrever a seção "Fase 1 — Análise" em `SK/SKILL.md`: carregar `project-analysis.md`, coletar os campos do `ProjectProfile` só com leitura/busca, imprimir no formato Fase 1 do `report-template.md`, guardar o inventário de endpoints e o modo de execução para a Fase 3
- [ ] T007 [US1] Validar a Fase 1 no `code-smells-project` (a partir da `baseline`): rodar `claude "/refactor-arch"`, conferir linguagem, framework/versão, domínio, número de arquivos e tabelas; ajustar `SK/references/project-analysis.md` se algo vier errado

**Checkpoint**: Fase 1 correta no projeto 1

---

## Phase 4: User Story 2 - Relatório de auditoria com pausa (Priority: P1)

**Goal**: relatório padronizado, verificável, salvo em arquivo, com pausa obrigatória

**Independent Test**: cenário A do quickstart (responder "n"): relatório no template, ≥ 5 findings, ≥ 1 CRITICAL/HIGH, linhas corretas, `git status` mostra apenas `.refactor-arch/`

- [ ] T008 [US2] Escrever em `SK/references/anti-patterns.md` a estrutura do catálogo (campos `id`, `name`, `severity`, `signals` por linguagem, `false_positives`, `fix` do data-model.md), a escala de severidade do enunciado e a regra de ajuste de severidade, seguidas das entradas CRITICAL: AP-01 SQL injection (SQL montado por concatenação/f-string/template com entrada do request), AP-02 segredos hardcoded (atribuição literal a chaves como `SECRET_KEY`, `password`, `apiKey`, `pk_live_`, `smtp`), AP-03 senha em texto plano ou hash fraco (comparação direta, MD5/SHA1 sem salt, base64, hash caseiro), AP-04 dado sensível exposto em resposta ou log (senha/hash em `to_dict`/serializer, cartão ou chave em log, segredo em `/health`), AP-05 God Class/Module (um arquivo ou classe com banco + regra + rotas, ou > 1 domínio), AP-06 endpoint administrativo, destrutivo ou de execução arbitrária sem autenticação
- [ ] T009 [US2] Acrescentar a `SK/references/anti-patterns.md` as entradas HIGH: AP-07 regra de negócio em rota/controller, AP-08 estado global mutável (conexão/cache/contador em variável de módulo), AP-09 operação com múltiplas escritas sem transação, AP-10 debug ligado ou bind `0.0.0.0` fixo no código, AP-11 acoplamento sem injeção de dependência (instanciação direta de infraestrutura dentro da regra)
- [ ] T010 [US2] Acrescentar a `SK/references/anti-patterns.md` as entradas MEDIUM: AP-12 N+1 / agregação em loop (query dentro de `for`/`forEach`, lazy load em loop, vários COUNT que caberiam num `GROUP BY`), AP-13 duplicação de lógica (inclusive cópias divergentes e helpers existentes não usados), AP-14 tratamento de erro genérico ou não centralizado (`except:`, `except Exception` devolvendo `str(e)`, callback `err` ignorado), AP-15 validação de entrada ausente/inconsistente (sem checagem de tipo, body nulo), AP-16 configuração fixa no código (porta, caminho de banco, CORS aberto), AP-17 APIs deprecated com a tabela "obsoleto → moderno" (Python: `datetime.utcnow()`, `Query.get()`, `before_first_request`, `pkg_resources`, `asyncio.get_event_loop()` fora de loop...; Node: `new Buffer()`, `url.parse()`, `fs.exists()`, `crypto.createCipher()`, `req.param()`, dependências marcadas deprecated no install...) e a instrução de também considerar warnings emitidos no install e no boot quando disponíveis
- [ ] T011 [US2] Acrescentar a `SK/references/anti-patterns.md` as entradas LOW: AP-18 magic numbers/strings, AP-19 código morto e imports/dependências não usados, AP-20 `print`/`console.log` como logging, AP-21 nomes crípticos ou que sombreiam builtins; conferir que cada entrada aponta para uma transformação `RF-xx` existente no playbook (lista planejada no plan.md)
- [ ] T012 [US2] Escrever a seção "Fase 2 — Auditoria" em `SK/SKILL.md`: carregar `anti-patterns.md`; varrer cada arquivo-fonte por todas as entradas; **reler as linhas citadas** antes de registrar cada finding; agrupar ocorrências; ordenar; montar o relatório no formato do template (incluindo "Nenhuma API deprecated encontrada" quando for o caso); gravar em `.refactor-arch/audit-report.md` ou no caminho de `$ARGUMENTS`; imprimir; terminar com a pergunta de confirmação e **encerrar o turno**; regras de resposta do contrato (`y`/`yes`/`s`/`sim` prossegue; qualquer outra coisa encerra informando que nada foi alterado)
- [ ] T013 [US2] Validar o cenário A no `code-smells-project` (a partir da `baseline`): responder "n", conferir template, ordenação, ≥ 5 findings, ≥ 1 CRITICAL/HIGH, cada `arquivo:linha` contra o código, e pelo menos 5 dos achados P1-01…P1-14 de `docs/analise-manual.md` presentes; rodar `git status --short code-smells-project` e confirmar que só `.refactor-arch/` aparece; ajustar `SK/references/anti-patterns.md` ou `SK/SKILL.md` se algo falhar

**Checkpoint**: Fases 1 e 2 completas no projeto 1, sem nenhuma escrita indevida

---

## Phase 5: User Story 3 - Refatoração MVC com validação em execução (Priority: P1)

**Goal**: projeto reestruturado em MVC, com comportamento original preservado e provado em execução

**Independent Test**: cenário B do quickstart no `code-smells-project`: estrutura MVC, boot sem erro, nenhum `REGRESSION` em `.refactor-arch/validation-after.md`, porta liberada ao final

- [ ] T014 [P] [US3] Escrever `SK/references/mvc-guidelines.md`: responsabilidades e regras de dependência de cada camada (config; models + `services/` de domínio como parte da camada Model; views/routes; controllers só orquestram; middlewares; composition root), o que cada camada pode importar, os dois layouts alvo (monolítico → `src/` como no exemplo do enunciado; parcialmente em camadas → completar as camadas que faltam sem renomear as que funcionam, `routes/` aceito como Views/Routes), a regra de manter o comando de execução original funcionando (entry point fino delegando ao composition root, ou manifesto atualizado), preservação do contrato HTTP, e o escopo de segurança da Fase 3 de research.md R7 (token `X-Admin-Token`/`ADMIN_TOKEN` fechado por padrão, allowlist de serialização, hash com biblioteca da stack, seeds com hash, autenticação completa como pendência), com a tabela de variáveis de ambiente do contrato
- [ ] T015 [P] [US3] Escrever `SK/references/refactoring-playbook.md` com 15 transformações, cada uma com `id`, `fixes` (IDs do catálogo), passos, código **antes/depois** genérico (Python e/ou JS) e como verificar: RF-01 queries parametrizadas; RF-02 segredos e flags → módulo de config + variáveis de ambiente + `.env.example`; RF-03 hash de senha (`werkzeug.security` / `crypto.scrypt`) incluindo seeds; RF-04 allowlist de serialização (remover senha/hash da saída); RF-05 proteção de rota administrativa por token; RF-06 God Class/Module → camadas; RF-07 fat controller/rota → model/service; RF-08 estado global → instância criada no composition root e injetada; RF-09 transação em escrita múltipla (commit/rollback); RF-10 N+1 → JOIN/eager loading/`GROUP BY`; RF-11 error handler centralizado (Flask `errorhandler`, middleware de erro do Express) com mensagens sem detalhes internos; RF-12 validação extraída e reutilizada (400 em vez de 500); RF-13 substituição de APIs deprecated; RF-14 constantes nomeadas, logging configurado e remoção de código morto; RF-15 callbacks aninhados → `async/await` com wrappers de Promise
- [ ] T016 [P] [US3] Escrever `SK/references/validation-procedure.md`: preparar ambiente isolado só se faltar (`python -m venv .venv` + `pip install -r`, ou `npm install`); detectar SO; checar porta livre; subir em background com o comando original e as variáveis (`ADMIN_TOKEN` de teste, `DEBUG=false`); polling até responder (timeout); montar o roteiro a partir do inventário da Fase 1 (requisições de exemplos do projeto → campos obrigatórios das validações; ordem leituras → criações → atualizações → exclusões → destrutivas globais); chamar com `curl -s -o <arquivo> -w "%{http_code}"`; registrar `BehaviorRecord` (step, method, path, request, status, shape, note) em `.refactor-arch/behavior-before.md`; reinicializar o banco (remover o arquivo SQLite e refazer o preparo; banco em memória recria no boot); repetir após a refatoração em `.refactor-arch/validation-after.md` com a classificação OK / CHANGED (intencional) / REGRESSION; rotas administrativas chamadas com e sem o header; encerrar a árvore (`taskkill /T /F /PID` no Windows; `kill` do grupo de processos em POSIX) e confirmar a porta livre
- [ ] T017 [US3] Escrever a seção "Fase 3 — Refatoração" em `SK/SKILL.md`: (1) carregar `mvc-guidelines.md`, `refactoring-playbook.md` e `validation-procedure.md`; (2) capturar `behavior-before.md` na aplicação original; (3) escolher o layout alvo pela classificação da Fase 1; (4) planejar finding → transformação, CRITICAL e HIGH primeiro; (5) aplicar de forma incremental, mantendo o entry point original funcionando e criando `.env.example`; (6) validar com o mesmo roteiro e comparar; (7) corrigir e revalidar enquanto houver `REGRESSION`, ou reportar a falha explicitamente; (8) encerrar todos os processos iniciados; (9) imprimir o bloco `PHASE 3: REFACTORING COMPLETE` com nova árvore, validação item a item, mudanças de contrato, dependências adicionadas com justificativa e pendências
- [ ] T018 [US3] Revisar `SK/SKILL.md` e `SK/references/*.md` contra FR-025: nenhuma regra cita nome de arquivo, rota, tabela ou domínio de um projeto-alvo; `SKILL.md` com menos de 500 linhas; todos os links para referências resolvem; catálogo com ≥ 8 entradas nas 4 severidades e playbook com ≥ 8 transformações com antes/depois
- [ ] T019 [US3] Executar o cenário B no `code-smells-project` (reset para a `baseline` conforme quickstart, `claude "/refactor-arch"`, responder "y"); conferir estrutura MVC, config sem hardcode, models, views/routes, controllers, error handler centralizado, entry point; confirmar que `.refactor-arch/validation-after.md` não tem `REGRESSION` e que a porta 5000 ficou livre; ajustar a skill e repetir a partir da `baseline` se falhar
- [ ] T020 [US3] Verificar o projeto 1 por fora da skill: subir com `python app.py`, chamar alguns endpoints com `curl`, procurar segredos literais no código refatorado (SC-009); copiar `code-smells-project/.refactor-arch/audit-report.md` para `reports/audit-project-1.md`; commitar `code-smells-project/` e `reports/audit-project-1.md`

**Checkpoint**: MVP completo — as 3 fases funcionam e o projeto 1 está entregue

---

## Phase 6: User Story 4 - Reuso em outra stack e em projeto parcialmente organizado (Priority: P2)

**Goal**: a mesma pasta da skill funciona no projeto Node.js/Express e no Flask já em camadas

**Independent Test**: hashes iguais nas 3 cópias; cenários A e B passando nos projetos 2 e 3

- [ ] T021 [US4] Copiar `SK/` para `ecommerce-api-legacy/.claude/skills/refactor-arch/` e `task-manager-api/.claude/skills/refactor-arch/` e conferir o hash das 3 cópias (quickstart, passo 1)
- [ ] T022 [US4] Executar o cenário A no `ecommerce-api-legacy` (stack Node.js/Express detectada, domínio LMS com checkout, ≥ 5 findings, ≥ 1 CRITICAL/HIGH, linhas corretas, ≥ 5 dos achados P2-01…P2-14, deprecated reportado, `git status` só com `.refactor-arch/`)
- [ ] T023 [US4] Executar o cenário B no `ecommerce-api-legacy` (`npm start` continua funcionando; checkout aprovado/recusado/inválido, relatório financeiro e exclusão de usuário sem `REGRESSION`; rotas protegidas listadas em Contract Changes); copiar o relatório para `reports/audit-project-2.md` e commitar `ecommerce-api-legacy/` e o relatório
- [ ] T024 [US4] Executar o cenário A no `task-manager-api` (Python/Flask e domínio Task Manager detectados; arquitetura "parcialmente em camadas"; findings mesmo com camadas existentes; APIs deprecated `Query.get()`/`datetime.utcnow()` presentes; ≥ 5 dos achados P3-01…P3-14)
- [ ] T025 [US4] Executar o cenário B no `task-manager-api` (o preparo com `python seed.py` é descoberto pela skill; camadas existentes preservadas e as faltantes criadas; todos os endpoints sem `REGRESSION`); copiar o relatório para `reports/audit-project-3.md` e commitar `task-manager-api/` e o relatório
- [ ] T026 [US4] Se a skill tiver sido alterada durante T022–T025: registrar a mudança e o motivo, recopiar para os 3 projetos (T021) e reexecutar, a partir da `baseline`, os projetos já entregues cuja execução seria afetada pela mudança, substituindo relatório e código commitados

**Checkpoint**: critérios de aceite atendidos em 3/3 projetos com a mesma skill

---

## Phase 7: User Story 5 - Entrega documentada e reprodutível (Priority: P3)

**Goal**: README completo com evidências; repositório público pronto para avaliação

**Independent Test**: seguindo só o README, um terceiro reproduz a execução em qualquer projeto a partir da `baseline`

- [ ] T027 [P] [US5] Escrever a seção "Análise Manual" no `README.md` a partir de `docs/analise-manual.md` (problemas por projeto, severidade, justificativa)
- [ ] T028 [P] [US5] Escrever a seção "Construção da Skill" no `README.md`: estrutura do `SKILL.md` e das referências, anti-patterns do catálogo e por quê, como foi garantido o agnosticismo, desafios encontrados e como foram resolvidos (incluindo as iterações de T007, T013, T019, T022–T026)
- [ ] T029 [US5] Escrever a seção "Resultados" no `README.md`: findings por severidade de cada relatório, estrutura antes/depois de cada projeto, checklist de validação do enunciado preenchido para os 3 projetos, evidências das aplicações rodando (trechos de `.refactor-arch/validation-after.md` e/ou screenshots em `docs/`), observações sobre o comportamento em cada stack
- [ ] T030 [US5] Escrever a seção "Como Executar" no `README.md`: pré-requisitos (Claude Code CLI, Python, Node, curl), comandos por projeto, como validar a refatoração, como voltar à `baseline` para reexecutar

**Checkpoint**: entregável documentado

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T031 Rodar `/speckit-analyze` para checar a consistência entre spec, plan e tasks, e corrigir divergências encontradas nos artefatos
- [ ] T032 Conferência final: hashes iguais das 3 cópias da skill; os 3 relatórios em `reports/`; nenhuma credencial literal nos 3 projetos refatorados; nenhum servidor órfão nas portas 3000/5000; `.gitignore` cobrindo `.venv/`, `node_modules/`, `*.db` e `.env`
- [ ] T033 Commitar o README e enviar `main` para o fork público (`git push origin main`), conferindo no GitHub que skill, código refatorado, `reports/` e README estão visíveis

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **US1** → **US2** → **US3** → **US4** → **US5** → **Polish**
- As histórias são sequenciais por natureza: cada fase da skill depende da anterior (a Fase 2 usa o perfil da Fase 1; a Fase 3 usa o relatório e o inventário de endpoints), e US4/US5 dependem da skill completa.

### Within Each User Story

- Referências antes da seção correspondente do `SKILL.md`
- Seção do `SKILL.md` antes da execução de validação
- Execução de validação sempre a partir da `baseline`

### Parallel Opportunities

- T004 em paralelo com T003 (arquivos diferentes)
- T005 pode começar junto com T003/T004
- T014, T015 e T016 (três referências independentes da Fase 3) em paralelo
- T027 e T028 em paralelo

---

## Parallel Example: User Story 3

```text
Task: "Escrever SK/references/mvc-guidelines.md"           (T014)
Task: "Escrever SK/references/refactoring-playbook.md"     (T015)
Task: "Escrever SK/references/validation-procedure.md"     (T016)
# depois: T017 (seção Fase 3 do SKILL.md), que referencia os três
```

---

## Implementation Strategy

### MVP First

1. Phase 1 + Phase 2
2. US1 → validar a Fase 1 no projeto 1 (T007)
3. US2 → validar o cenário A no projeto 1 (T013)
4. US3 → validar o cenário B e entregar o projeto 1 (T019–T020) — **MVP**: skill completa funcionando em um projeto

### Incremental Delivery

5. US4 → Node.js (projeto 2) e Flask em camadas (projeto 3), iterando a skill se preciso (T026)
6. US5 → README com resultados reais
7. Polish → consistência, conferência final, push

---

## Notes

- Execuções reais da skill (T007, T013, T019, T022–T025) usam o Claude Code CLI em sessão interativa iniciada dentro da pasta do projeto; o usuário responde à confirmação da Fase 2.
- Toda reexecução parte da `baseline` (`git checkout baseline -- <projeto>/` + limpeza dos artefatos gerados).
- Commit ao fim de cada projeto entregue (T020, T023, T025) e ao fim da documentação (T033).
