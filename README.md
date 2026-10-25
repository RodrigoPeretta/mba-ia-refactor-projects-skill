# Refatoração Arquitetural Automatizada com a skill `refactor-arch`

Solução do desafio "Criação de Skills — Refatoração Arquitetural Automatizada" (MBA IA,
Full Cycle). A entrega é uma Custom Skill do **Claude Code**, `/refactor-arch`, que trabalha
em 3 fases sobre qualquer projeto backend:

1. **Análise**: detecta linguagem, framework, banco, domínio e arquitetura.
2. **Auditoria**: cruza o código com um catálogo de 21 anti-patterns e gera um relatório com
   severidade e `arquivo:linha`. Depois **para e pede confirmação**.
3. **Refatoração**: reestrutura para MVC e **prova que a aplicação continua funcionando**,
   subindo a versão original e a refatorada e comparando as respostas de todos os endpoints.

A mesma pasta da skill, idêntica byte a byte, foi executada nos 3 projetos legados: dois em
Python/Flask e um em Node.js/Express. O P1 e o P2 rodaram com a v1.1, e o P3 com a v1.2.2
(ver a revisão abaixo). Os critérios de aceite foram atingidos nos 3.

| | Projeto 1 · code-smells-project | Projeto 2 · ecommerce-api-legacy | Projeto 3 · task-manager-api |
|---|---|---|---|
| Stack | Python + Flask 3.1.1 | Node.js + Express ^4.18.2 | Python + Flask 3.0.0 + SQLAlchemy |
| Ponto de partida | Monolito (4 arquivos) | God Class (3 arquivos) | Parcialmente em camadas (15 arquivos) |
| Findings (C / H / M / L) | 21 (7 / 5 / 6 / 3) | 18 (5 / 5 / 4 / 4) | 19 (5 / 2 / 9 / 3) |
| Validação em execução | 40 passos, 0 regressões | 12 passos, 0 regressões | 80 passos (com variantes de autenticação), 0 regressões |
| Relatório | [audit-project-1.md](reports/audit-project-1.md) | [audit-project-2.md](reports/audit-project-2.md) | [audit-project-3.md](reports/audit-project-3.md) |

> **Revisão após a correção (skill v1.2.2).** O feedback apontou que, no P3, o login emitia
> um token assinado que nenhuma rota validava, e por isso `PUT /users/<id>` continuava aberto
> a clientes anônimos. A skill ganhou o padrão **RF-16**: validar o token de sessão e
> autorizar só o dono ou um admin, inclusive quando o corpo traz o campo de dono
> (`user_id`). A Fase 3 passou a aplicar cada cláusula da recomendação e a gravar o resumo
> em arquivo. O P3 foi refatorado de novo a partir do código original. Uma das execuções
> intermediárias falhou no teste de ataque e foi descartada. Detalhes em
> [Histórico das iterações](#desafios-encontrados-e-como-resolvi) e no
> [teste de ataque](docs/iterations/p3-v1.2-teste-de-ataque.md) (v1.1: 8/24 → v1.2.2: 24/24).

O projeto foi desenvolvido com **SDD (Spec-Driven Development)** via
[spec-kit](https://github.com/github/spec-kit). A constitution, a spec, o plan, a research e
as tasks estão em [`specs/001-refactor-arch-skill/`](specs/001-refactor-arch-skill/) e
[`.specify/memory/constitution.md`](.specify/memory/constitution.md).

---

## Sumário

- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)
- [Estrutura do repositório](#estrutura-do-repositório)

---

## A) Análise Manual

Antes de escrever a skill, li o código dos 3 projetos e **rodei cada aplicação original**,
chamando todos os endpoints com warnings de depreciação habilitados. Assim, vários problemas
foram confirmados em execução, e não só por leitura. Encontrei 14 problemas por projeto. O
documento completo, com todas as linhas e a evidência de cada achado, está em
[`docs/analise-manual.md`](docs/analise-manual.md). Abaixo está o resumo.

### Projeto 1: code-smells-project (API de e-commerce, Flask)

| # | Sev. | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| P1-01 | CRITICAL | SQL Injection (SQL concatenado com entrada) | `models.py:28, 47-50, 109-111, …` | **Confirmado:** login com `' OR 1=1 --` entrou como Admin |
| P1-02 | CRITICAL | `/admin/query` executa SQL arbitrário e `/admin/reset-db` apaga tudo, sem autenticação | `app.py:47-78` | **Confirmado:** uma chamada devolveu todos os e-mails e senhas |
| P1-03 | CRITICAL | `SECRET_KEY` hardcoded e devolvida no `/health`; debug ligado em `0.0.0.0` | `app.py:7-8, 88`; `controllers.py:285-289` | Permite forjar sessões; o debugger do Werkzeug permite executar código remotamente |
| P1-04 | CRITICAL | Senhas em texto plano, devolvidas pela API | `database.py:76-78`; `models.py:83, 99, 126-129` | `GET /usuarios` retornava `"senha": "admin123"` |
| P1-05 | HIGH | Regra de negócio espalhada entre "models" e controllers | `models.py:133-169, 256-262` | Sem camada de domínio, a regra não pode ser testada sem banco e HTTP |
| P1-06 | HIGH | Conexão SQLite global compartilhada entre threads | `database.py:4-11` | Estado global mutável, com schema e seed escondidos dentro de um getter |
| P1-07 | HIGH | Criação de pedido sem transação | `models.py:139-168` | Uma falha no meio deixa escritas parciais, que o próximo `commit` grava |
| P1-08 | MEDIUM | Queries N+1 | `models.py:187-199, 219-231` | O custo cresce com pedidos × itens |
| P1-09 | MEDIUM | Duplicação, com cópias que já divergiram | `models.py:12-40, 171-233`; `controllers.py:28-90` | O `PUT` aceita dados que o `POST` rejeita |
| P1-10 | MEDIUM | `except Exception` com `str(e)` em todo handler | `controllers.py` (todos) | Vaza detalhes internos, e um body vazio vira 500 |
| P1-11 | MEDIUM | CORS aberto para qualquer origem | `app.py:9` | Middleware configurado sem critério |
| P1-12 | LOW | `print` como logging, incluindo e-mails | `controllers.py:8, 161, 179, …` | Sem nível nem destino, e registra dado pessoal |
| P1-13 | LOW | Magic numbers (faixas de desconto, limites) | `models.py:257-262`; `controllers.py:52, 242` | Regras sem nome, difíceis de reaproveitar |
| P1-14 | LOW | `id` sombreando o builtin e imports sem uso | `controllers.py:14, 56`; `models.py:2` | Legibilidade |

### Projeto 2: ecommerce-api-legacy (LMS com checkout, Express)

| # | Sev. | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| P2-01 | CRITICAL | Credenciais e chave `pk_live_` hardcoded | `utils.js:1-7` | Segredos de produção versionados no repositório |
| P2-02 | CRITICAL | Número do cartão e chave do gateway no log | `AppManager.js:45` | Violação direta de PCI-DSS |
| P2-03 | CRITICAL | "Hash" de senha caseiro, com colisões, e senha padrão `123456` | `utils.js:17-23`; `AppManager.js:68` | **Confirmado:** `senhaforte` e `senha123` geram o mesmo "hash" `c2c2c2c2c2` |
| P2-04 | CRITICAL | God Class `AppManager` (banco, schema, rotas, pagamento, relatório) | `AppManager.js:4-139` | Separação de responsabilidades inexistente |
| P2-05 | HIGH | Checkout sem transação, em callback hell (5 níveis) | `AppManager.js:37-77` | Matrícula gravada sem pagamento se a segunda escrita falhar |
| P2-06 | HIGH | Rotas de admin sem autenticação; DELETE deixa registros órfãos | `AppManager.js:80, 131-137` | **Confirmado:** o relatório continuou com o aluno "Unknown" e o pagamento dele |
| P2-07 | HIGH | Estado global mutável (`globalCache`, `totalRevenue`) | `utils.js:9-15` | Vazamento de memória e estado escondido entre requisições |
| P2-08 | HIGH | Aprovação de pagamento (`startsWith("4")`) dentro da rota | `AppManager.js:46, 66-72` | Trocar o gateway exige mexer no roteamento |
| P2-09 | MEDIUM | N+1 no relatório financeiro, com `err` ignorado | `AppManager.js:89-127` | Um erro na query derruba o processo |
| P2-10 | MEDIUM | Validação ausente; respostas em texto e em JSON misturadas | `AppManager.js:35, 38, 48, 60` | O cliente não consegue tratar erros de forma uniforme |
| P2-11 | MEDIUM | Banco `:memory:` e porta fixos no código | `AppManager.js:7`; `utils.js:6` | Os dados se perdem a cada restart, sem configuração por ambiente |
| P2-12 | LOW | Nomes crípticos (`u`, `e`, `p`, `cc`) | `AppManager.js:29-33` | Legibilidade |
| P2-13 | LOW | Magic numbers | `utils.js:19, 22` | Legibilidade |
| P2-14 | LOW | `console.log` como logging | `app.js:13`; `utils.js:13` | Sem nível nem destino |

### Projeto 3: task-manager-api (Task Manager, Flask + SQLAlchemy)

| # | Sev. | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| P3-01 | CRITICAL | `SECRET_KEY` e senha SMTP hardcoded | `app.py:13`; `notification_service.py:7-10` | Segredos versionados |
| P3-02 | CRITICAL | Senhas com MD5 sem salt | `models/user.py:27-32` | Quebrável por tabela de hash em segundos |
| P3-03 | CRITICAL | Hash da senha em todas as respostas de usuário | `models/user.py:21` | **Confirmado:** `POST /login` retornava `"password": "81dc9bdb..."` |
| P3-04 | HIGH | Token falso (`fake-jwt-token-<id>`) e criação de `admin` pelo cadastro público | `user_routes.py:52, 71-78, 210` | Qualquer cliente vira admin |
| P3-05 | HIGH | Debug ligado em `0.0.0.0` | `app.py:34` | **Confirmado:** `priority: "alta"` devolveu a página do debugger com traceback |
| P3-06 | HIGH | Rotas "gordas", com a lógica de atraso reimplementada **6 vezes** enquanto o model e os helpers existentes ficam sem uso | `task_routes.py`, `user_routes.py`, `report_routes.py` | A camada de domínio existe, mas é ignorada, e as cópias divergem |
| P3-07 | MEDIUM | Queries N+1 | `task_routes.py:41-57`; `report_routes.py:53-68, 159-164` | `GET /tasks` faz 2N+1 queries |
| P3-08 | MEDIUM | **APIs deprecated**: `Query.get()` (SQLAlchemy 2.x) e `datetime.utcnow()` (Python 3.12+) | 16 e 23 ocorrências | **Confirmado** por `LegacyAPIWarning` e `DeprecationWarning` em execução |
| P3-09 | MEDIUM | `except:` genérico e tipos não validados | `task_routes.py:62, 113, …` | Erro do cliente vira 500 |
| P3-10 | MEDIUM | CRUD de categorias dentro de `report_routes.py` | `report_routes.py:157-223` | Coesão errada (viola o SRP) |
| P3-11 | MEDIUM | Integridade referencial manual ou ausente | `user_routes.py:140-142`; `report_routes.py:218` | Apagar um usuário remove as tasks num loop manual. A parte da categoria órfã estava errada ([correção](#resumo-dos-relatórios-de-auditoria)) |
| P3-12 | LOW | Imports e dependências não usados | `app.py:7`; `requirements.txt:4-6` | Ruído e dependências desnecessárias |
| P3-13 | LOW | Magic numbers e strings repetidas, com as constantes existindo sem uso | `helpers.py:110-116` | Legibilidade |
| P3-14 | LOW | Código verboso (`if x: return True else: return False`) | `models/user.py:34-38` | Legibilidade |

A análise terminou com uma tabela de **padrões recorrentes**, que mostra quais
anti-patterns aparecem em quais projetos. Essa tabela virou a base do catálogo da skill
([`docs/analise-manual.md`](docs/analise-manual.md#padrões-recorrentes--insumo-para-o-catálogo-da-skill)).

---

## B) Construção da Skill

### Estrutura

```text
.claude/skills/refactor-arch/
├── SKILL.md                         # orquestrador das 3 fases (≈ 140 linhas)
└── references/
    ├── project-analysis.md          # área 1: heurísticas de stack, banco, domínio e arquitetura
    ├── anti-patterns.md             # área 2: catálogo AP-01…AP-21 + tabela de APIs deprecated
    ├── report-template.md           # área 3: formatos exatos das saídas das 3 fases
    ├── mvc-guidelines.md            # área 4: camadas, regras de dependência, layouts alvo
    ├── refactoring-playbook.md      # área 5: RF-01…RF-16, com código antes/depois
    └── validation-procedure.md      # apoio à Fase 3: subir, testar, comparar, encerrar processos
```

### Decisões de design

- **`SKILL.md` é o prompt; as referências são o conhecimento.** O `SKILL.md` só orquestra:
  diz o que fazer em cada fase, quais são os portões entre elas e **qual referência carregar
  em cada fase**. Esse é o progressive disclosure recomendado pela documentação do Claude
  Code: só o `SKILL.md` entra no contexto ao invocar, e cada referência é lida quando a fase
  precisa dela.
- **`disable-model-invocation: true`.** A skill reescreve o projeto inteiro, então só roda
  quando o humano digita `/refactor-arch`, nunca por iniciativa do modelo.
- **Fases 1 e 2 são estritamente somente leitura.** Instalar dependências e subir a aplicação
  original criam arquivos (banco SQLite, `__pycache__`, `node_modules`), por isso foram
  movidos para **depois** do "y". A única escrita antes da confirmação é o relatório, em
  `.refactor-arch/audit-report.md`, e isso é verificável com `git status`.
- **A validação é medida, não afirmada.** No início da Fase 3, a skill sobe a aplicação
  **original**, executa um roteiro de requisições montado a partir do inventário de endpoints
  e grava `behavior-before.md`. Depois da refatoração, roda **o mesmo roteiro** e classifica
  cada passo como `OK`, `CHANGED (intencional)` ou `REGRESSION` em `validation-after.md`.
  Qualquer `REGRESSION` obriga a corrigir antes de declarar a fase concluída.
- **Proteger, não remover.** Endpoints perigosos (execução de SQL, reset de banco, exclusões)
  continuam existindo, mas exigem credencial e ficam fechados por padrão. Rotas
  administrativas usam o header `X-Admin-Token` igual a `ADMIN_TOKEN`. Rotas sobre recursos
  de usuário usam o token do login, quando o projeto tem login (item seguinte). Assim o requisito "os endpoints originais continuam respondendo"
  convive com a correção de segurança. Toda mudança de contrato é listada no resumo final.
- **Token emitido tem que ser validado.** Quando o login do projeto já emite token, as rotas
  de escrita sobre usuários e sobre recursos com dono exigem `Authorization: Bearer <token>`:
  401 sem token válido e 403 para quem não é o dono nem admin (RF-16). O `X-Admin-Token`
  fica para as rotas administrativas sem dono. A skill não cria login onde não existe.
- **Recomendação aplicada por inteiro.** Na Fase 3, cada recomendação CRITICAL/HIGH é
  quebrada em cláusulas (cada rota, campo ou regra citada). Cada cláusula precisa de um
  passo de validação que prove o efeito, ou vai para `Pending` com o motivo. O resumo final
  mostra esse mapa na tabela `Recommendations Applied`.
- **O layout alvo depende do ponto de partida.** Um monolito ganha um layout `src/` novo,
  como no exemplo do enunciado. Um projeto parcialmente em camadas mantém as pastas que já
  cumprem sua função e ganha só as que faltam. Nos dois casos, o comando de execução
  original (`python app.py`, `npm start`) continua funcionando.
- **Sem scripts auxiliares.** A validação usa apenas o shell, o runtime do projeto e
  `curl`. Um script em Python não rodaria num projeto Node sem Python instalado, e
  vice-versa.

### Catálogo de anti-patterns (21 entradas) e por quê

| Severidade | Anti-patterns | Por que entraram |
|---|---|---|
| CRITICAL (6) | AP-01 SQL Injection · AP-02 segredos hardcoded · AP-03 senha em claro ou hash fraco · AP-04 dado sensível em resposta/log · AP-05 God Class/Module · AP-06 endpoint admin/destrutivo sem auth | Os 6 apareceram em pelo menos um projeto, e todos expõem dados ou destroem a separação de responsabilidades: exatamente a definição de CRITICAL do enunciado |
| HIGH (5) | AP-07 regra de negócio em controller/rota · AP-08 estado global mutável · AP-09 várias escritas sem transação · AP-10 debug/bind aberto · AP-11 acoplamento sem DI | Os exemplos de HIGH do enunciado (fat controller, acoplamento, estado global), mais os dois problemas de integridade e exposição que a baseline mostrou |
| MEDIUM (6) | AP-12 N+1 · AP-13 duplicação · AP-14 erro genérico/não centralizado · AP-15 validação ausente · AP-16 config fixa/CORS aberto · **AP-17 APIs deprecated** | Os exemplos de MEDIUM do enunciado, mais a categoria **obrigatória** de APIs deprecated |
| LOW (4) | AP-18 magic numbers · AP-19 código morto/imports · AP-20 `print`/`console.log` · AP-21 nomes crípticos | Legibilidade; apareceram nos 3 projetos |

Cada entrada tem **sinais de detecção acionáveis**: regex sugerida por linguagem, o que ler em
volta do trecho, **falsos positivos** a descartar e a transformação (`RF-xx`) que a corrige. Um
exemplo: "chamada `execute(` cujo argumento usa `+`, `%`, `.format(` ou f-string com
variável vinda do request", em vez de algo vago como "SQL inseguro". A **AP-17** traz uma
tabela "API obsoleta → substituto moderno" para Python, SQLAlchemy, Flask, Node e Express.

O **playbook** tem 16 transformações. Todas têm código antes/depois e um passo de
verificação: queries parametrizadas, config via ambiente, hash de senha (com bibliotecas que
a stack já tem, como `werkzeug.security` e `crypto.scrypt`), allowlist de serialização,
token de admin, God Class → camadas, fat controller → service, estado global → injeção,
transação, N+1 → JOIN/GROUP BY, error handler central, validação, APIs deprecated,
constantes/logging/limpeza, callbacks → async/await e, desde a v1.2, validação do token de
sessão com autorização dono-ou-admin.

### Como garanti que a skill é agnóstica de tecnologia

1. **Detecção por evidência dupla.** O framework só é aceito com dependência no manifesto
   **e** uso no código, com tabelas para Flask, Django, FastAPI, Express, Fastify, NestJS,
   Gin, Spring e outros.
2. **Nenhuma regra cita um projeto-alvo.** A primeira versão tinha exemplos com termos dos
   próprios projetos (`courses`, `setupRoutes`, `is_overdue`, o envelope `dados`/`sucesso`).
   Todos foram reescritos num domínio neutro (faturas, clientes, assinaturas, planos) e
   checados com uma busca automatizada pelos termos dos 3 projetos.
3. **A skill copia o envelope do projeto.** As guidelines mandam preservar os nomes de chave,
   a flag de sucesso e o idioma das mensagens **do próprio projeto**, em vez de impor um
   formato.
4. **Comandos para Windows e POSIX** no procedimento de validação.
5. **Prova:** a pasta foi copiada sem alteração e o hash é o mesmo nas 3 cópias. A skill
   funcionou em Flask com SQL cru, Flask com ORM e Express com callbacks.

### Desafios encontrados e como resolvi

| Desafio | Como apareceu | Solução |
|---|---|---|
| **Processo filho do auto-reload** | Na baseline manual, o `debug=True` do Flask criou um processo filho que sobreviveu ao término do pai. O teste do projeto seguinte respondeu **com a aplicação errada** | O procedimento encerra pela **porta** e pela **árvore** de processos (`taskkill /T`, `lsof` + `kill`) e confirma que a porta ficou livre |
| **Arquitetura mal classificada** (iteração 1) | No P1, a skill classificou como "parcialmente em camadas" porque existem arquivos `models.py` e `controllers.py`. Isso levaria ao layout errado na Fase 3 | Regra explícita: **arquivo solto com nome de camada não é camada**, os critérios são avaliados em ordem, e um finding de God Module força "Monolítica" |
| **Recomendação contraditória** (iteração 1) | O relatório recomendou "remover o endpoint `/admin/query`", contra a decisão de preservar o contrato | Cada entrada de risco do catálogo ganhou uma "Recomendação padrão": proteger e restringir, nunca remover |
| **Caminho real do SQLite** | Flask-SQLAlchemy resolve `sqlite:///tasks.db` para `instance/tasks.db` | O procedimento manda confirmar o arquivo realmente criado antes de resetar o banco entre as medições |
| **Dados que mudam entre execuções** | Ids, timestamps e hashes diferentes a cada rodada | A comparação usa status + "forma" (tipo e chaves) e ignora valores voláteis |
| **Token emitido e nunca validado** (feedback da correção) | No P3, o relatório recomendava "exigir token válido nas rotas de escrita sobre usuários", mas a Fase 3 só passou a **emitir** um token assinado no login. Nenhuma rota o validava, e `PUT /users/<id>` seguia aceitando que um anônimo trocasse o e-mail e a senha de outro usuário. A causa estava na própria skill: as guidelines colocavam "autenticação de usuários" fora do escopo da Fase 3, contradizendo a recomendação da Fase 2. E a validação nunca testava "usuário A altera B" | v1.2: RF-16 no playbook; escopo corrigido (validar o token que o login já emite é obrigatório); recomendação quebrada em cláusulas e provada por passo de validação; a validação roda 5 variantes por rota protegida (sem token, token adulterado, token de outro usuário, dono, admin) |
| **Resultado diferente entre execuções** | Com a mesma skill (v1.2/v1.2.1), uma execução do P3 checou o `user_id` vindo do corpo e a outra não: na segunda, um usuário criava e transferia tasks para outro. A validação da própria skill deu 0 regressões nas duas, porque o roteiro não tinha esse caso | v1.2.2: o RF-16 cita explicitamente o campo de dono e a distinção 401 × 403, a recomendação padrão do AP-06 também, e a validação ganhou as variantes "criar em nome de outro" e "transferir para outro". O teste de ataque independente roda a cada execução |
| **Destino do relatório** | A skill não tem como saber de forma agnóstica se o projeto é o "N" | Ela grava em `.refactor-arch/audit-report.md`, e a cópia para `reports/` é um passo de entrega. Também aceita um argumento opcional com o caminho |

Histórico das iterações:

| Versão | Execução | Resultado | Mudança seguinte |
|---|---|---|---|
| v1 | P1, resposta "n" | 21 findings, 14/14 achados manuais, pausa funcionou, mas a arquitetura veio errada e uma recomendação contradizia o contrato | v1.1: rubrica de arquitetura e "recomendação padrão" |
| v1.1 | P1 completo | Monolítica ✓, recomendação correta ✓, 0 regressões | nenhuma |
| v1.1 | P2 completo | Sem nenhuma mudança na skill, 0 regressões | nenhuma |
| v1.1 | P3 completo | Sem nenhuma mudança na skill, 0 regressões, **mas** a recomendação do AP-06 foi aplicada pela metade (token emitido e não validado), o que só apareceu na correção | v1.2: RF-16, escopo de auth, recomendação por cláusula, variantes de ataque na validação |
| v1.2 | P3 completo, a partir do código original | 19 findings; o AP-06 agora nomeia cada rota e a regra 401/403; 73 passos, 0 regressões; teste de ataque **24/24** (v1.1: 8/24). Mas o resumo da Fase 3 só foi impresso no terminal e se perdeu | v1.2.1: gravar o resumo em `.refactor-arch/phase3-summary.md` |
| v1.2.1 | P3 completo, a partir do código original | 20 findings, 76 passos, 0 regressões, resumo gravado. **Teste de ataque 21/24**: um usuário criava tasks em nome de outro e transferia as próprias tasks (`user_id` no corpo). A recomendação não cobria o campo de dono, e a v1.2 só tinha acertado por acaso. Execução **descartada** ([resumo](docs/iterations/p3-v1.2.1-phase3-summary.md)) | v1.2.2: campo de dono e 401 × 403 explícitos no RF-16, no AP-06 e na validação |
| v1.2.2 | P3 completo, a partir do código original | 19 findings; recomendação do AP-06 cita o `user_id`; 80 passos, 0 regressões; teste de ataque **24/24**; [`phase3-summary.md`](task-manager-api/.refactor-arch/phase3-summary.md) com o mapa recomendação → código → passo de validação | nenhuma (entregue) |

A v1.2 só acrescenta regras que disparam quando o login **emite token**. O P1 (login sem
token) e o P2 (sem login) não têm esse caso, então as refatorações deles, feitas com a v1.1,
continuam válidas e não foram refeitas.

O relatório da iteração 1, o resumo da execução descartada e o teste de ataque estão em
[`docs/iterations/`](docs/iterations/).

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Achados manuais cobertos | APIs deprecated |
|---|:-:|:-:|:-:|:-:|:-:|:-:|---|
| 1 · code-smells-project | 7 | 5 | 6 | 3 | **21** | 14/14 | Nenhuma (correto: Flask 3.1 com APIs atuais) |
| 2 · ecommerce-api-legacy | 5 | 5 | 4 | 4 | **18** | 14/14 | Nenhuma no código; dependências transitivas deprecated do `sqlite3` anotadas |
| 3 · task-manager-api | 5 | 2 | 9 | 3 | **19** | 13/14 | `Query.get()` (16 usos) e `datetime.utcnow()` (23 usos), **substituídas** na Fase 3 |

A skill também encontrou problemas que **eu não tinha visto** na análise manual:
- **P1:** itens repetidos no mesmo pedido passam um a um na checagem de estoque e podem deixar
  o estoque negativo; o cancelamento de pedido diz "devolver estoque", mas nada faz isso.
- **P2:** enviar `card` como número em vez de texto **derrubava o processo** do servidor
  original (`cc.startsWith is not a function`).
- **P3:** a busca com `priority=abc` respondia 500.

**Correção da análise manual (P3-11).** Eu tinha anotado que apagar uma categoria deixava
tasks com `category_id` órfão. A execução v1.2.1 da skill mostrou que não: o
`relationship` com backref faz o SQLAlchemy gravar `category_id = NULL` nas tasks antes de
apagar a categoria. Confirmei isso por fora, no código original e no refatorado, e o
resultado foi `NULL` nos dois casos. A parte válida do P3-11 é a exclusão das tasks de um
usuário num loop manual, que a refatoração trocou por um único `DELETE` em lote na mesma
transação da exclusão do usuário (`services/user_service.py`). Já a execução v1.2.2 voltou
a afirmar, sem testar, que a categoria deixa órfãos (item "Observado fora do relatório" do
`Pending` em `phase3-summary.md`). Essa afirmação está **errada** e foi mantida no arquivo só porque é
um artefato gerado pela skill.

### Estrutura antes × depois

<table>
<tr><th>Projeto</th><th>Antes</th><th>Depois</th></tr>
<tr><td><b>1</b><br>Flask<br>monolito</td><td>

```text
app.py          # config + rotas + SQL admin + boot
controllers.py  # validação + regra + resposta
models.py       # SQL de 4 domínios + regra + formatação
database.py     # conexão global + schema + seed
```

</td><td>

```text
app.py                  # entry point fino
.env.example
src/
├── app.py              # composition root (create_app)
├── config/settings.py
├── database.py         # conexão por requisição (flask.g)
├── exceptions.py
├── models/             # produto, usuario, pedido, admin
├── services/           # pedido, relatorio, notificacao, sistema
├── controllers/        # 6 controllers + validators
├── views/              # 6 blueprints
└── middlewares/        # error_handler, auth
```

</td></tr>
<tr><td><b>2</b><br>Express<br>God Class</td><td>

```text
src/
├── app.js         # bootstrap
├── AppManager.js  # banco + schema + seed + rotas
│                  #   + pagamento + relatório
└── utils.js       # config com segredos + "cripto"
                   #   + cache global
```

</td><td>

```text
.env.example
src/
├── app.js            # composition root + listen
├── config/           # settings (env), constants
├── database.js       # conexão, schema, seed, wrappers Promise
├── errors.js, logger.js
├── models/           # user, course, enrollment, payment, auditLog
├── services/         # checkout, report, user, paymentGateway, passwordHasher
├── controllers/      # checkout, report, user
├── routes/index.js
└── middlewares/      # auth, errorHandler, asyncHandler
```

</td></tr>
<tr><td><b>3</b><br>Flask<br>parcial</td><td>

```text
app.py, database.py, seed.py
models/    # task, user, category
routes/    # task, user, report (+ CRUD de categorias)
services/  # notification (sem uso)
utils/     # helpers (sem uso)
```

</td><td>

```text
app.py, database.py, seed.py, .env.example
config/        # NOVO: settings (env + constantes)
models/        # mantido: + regras de domínio, serialização segura
routes/        # mantido: só mapeamento; + category_routes, system_routes
controllers/   # NOVO: task, user, report, category, system + validators
services/      # mantido + task, user, report, category, persistence
middlewares/   # NOVO: error_handler, auth (token de sessão, dono-ou-admin, X-Admin-Token)
utils/         # mantido: helpers usados de fato + errors
```

</td></tr>
</table>

### Checklist de validação

| Item | P1 | P2 | P3 |
|---|:-:|:-:|:-:|
| **Fase 1: Análise** | | | |
| Linguagem detectada corretamente | ✅ Python | ✅ JavaScript/Node.js | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express ^4.18.2 | ✅ Flask 3.0.0 + Flask-SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Número de arquivos condiz com a realidade | ✅ 4 (780 linhas) | ✅ 3 (180 linhas) | ✅ 15 (1.158 linhas) |
| **Fase 2: Auditoria** | | | |
| Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 21 | ✅ 18 | ✅ 19 |
| Detecção de APIs deprecated (se aplicável) | ✅ N/A declarado | ✅ N/A no código, dependências anotadas | ✅ 2 APIs |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3: Refatoração** | | | |
| Estrutura de diretórios segue o padrão MVC | ✅ | ✅ | ✅ |
| Configuração extraída para módulo de config (sem hardcode) | ✅ | ✅ | ✅ |
| Models criados para abstrair dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `views/` | ✅ `routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ | ✅ | ✅ |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 19/19 | ✅ 3/3 | ✅ todos |

**Critérios de aceite:** stack detectada (3/3) · ≥ 5 findings (3/3) · ≥ 1 CRITICAL ou HIGH
(3/3) · aplicação funcionando após a refatoração (3/3).

### Evidências das aplicações rodando após a refatoração

Cada projeto tem em `.refactor-arch/` o roteiro executado antes e depois, além dos logs do
servidor:

| Projeto | Comparação | Resultado |
|---|---|---|
| 1 | [`behavior-before.md`](code-smells-project/.refactor-arch/behavior-before.md) → [`validation-after.md`](code-smells-project/.refactor-arch/validation-after.md) | OK 29 · CHANGED 11 · **REGRESSION 0** |
| 2 | [`behavior-before.md`](ecommerce-api-legacy/.refactor-arch/behavior-before.md) → [`validation-after.md`](ecommerce-api-legacy/.refactor-arch/validation-after.md) | OK 6 · CHANGED 6 · **REGRESSION 0** |
| 3 | [`behavior-before.md`](task-manager-api/.refactor-arch/behavior-before.md) → [`validation-after.md`](task-manager-api/.refactor-arch/validation-after.md) | OK 42 · CHANGED 38 · **REGRESSION 0** em 80 passos, sem nenhum warning de depreciação (antes eram 25). O resumo da Fase 3 está em [`phase3-summary.md`](task-manager-api/.refactor-arch/phase3-summary.md) |

Trecho do log do P1 refatorado ([`server-after.log`](code-smells-project/.refactor-arch/server-after.log)):

```text
WARNING src.config.settings: SECRET_KEY não definida; usando chave temporária gerada no boot
INFO src.database: Banco semeado com dados de exemplo
INFO __main__: Servidor iniciado em http://127.0.0.1:5000
 * Serving Flask app 'src.app'
 * Debug mode: off
```

**Verificação independente.** Além da validação feita pela própria skill, rodei contra cada
projeto refatorado o **mesmo smoke test que usei na análise manual**, escrito antes da skill
existir:

| Projeto | Mesmo status do original | Diferenças (todas intencionais) |
|---|---|---|
| 1 | 18 de 20 | login com `' OR 1=1 --`: 200 → **401**; `/admin/query` sem token: 200 → **403** |
| 2 | 3 de 6 | 3 chamadas de admin sem token → **403** (com token: mesmo corpo do original) |
| 3 (v1.1) | 19 de 23 | `priority: "alta"`: 500 → **400**; 3 DELETE sem token → **403** (com token: 200) |

No P3, a verificação independente é um **teste de ataque** escrito depois do feedback. Ele
rodou contra o código de cada execução da skill:
[`p3-v1.2-teste-de-ataque.md`](docs/iterations/p3-v1.2-teste-de-ataque.md).

| Cenário | v1.1 | v1.2 | v1.2.1 | v1.2.2 |
|---|:-:|:-:|:-:|:-:|
| Anônimo troca e-mail e senha da Maria (`PUT /users/2`) | **200** | 401 | 401 | 401 |
| Token legado, forjado ou adulterado | **200** | 401 | 401 | 401 |
| Usuário altera outro usuário, ou a task de outro | **200** | 403 | 403 | 403 |
| Usuário cria ou transfere task para outro (`user_id`) | **200/201** | 403 | **200/201** | 403 |
| Dono altera o próprio cadastro; admin altera qualquer um | 200 | 200 | 200 | 200 |
| Token de usuário desativado | **200** | 401 | 401 | 401 |
| **Total** | **8/24** | **24/24** | **21/24** | **24/24** |

Também verifiquei por fora a exclusão de categoria (ver a correção do P3-11 acima): o
`category_id` das tasks vira `NULL` no original e no refatorado.

Também conferi por fora da skill: `senha`/`password`/`secret_key` não aparecem mais em
nenhuma resposta; `DROP TABLE` em `/admin/query` é recusado mesmo com token; o login com as
senhas do seed funciona (agora com hash `scrypt`); o número do cartão não aparece mais no
log; não ficou nenhum servidor rodando.

### Mudanças intencionais de contrato

| Projeto | Mudança | Motivo |
|---|---|---|
| 1 | `senha` sai de `/usuarios`; `secret_key`, `db_path` e `debug` saem de `/health` | AP-04 |
| 1 | `/admin/query` e `/admin/reset-db` exigem `X-Admin-Token`; `/admin/query` aceita só um `SELECT` | AP-06 |
| 1 | Entrada inválida (tipos, body vazio, aspas na busca) → 400 em vez de 500; pedido inexistente → 404 | AP-15, AP-14 |
| 2 | Relatório financeiro e `DELETE /api/users/:id` exigem `X-Admin-Token` (o `api.http` foi atualizado) | AP-06 |
| 2 | Exclusão de usuário apaga as matrículas e os pagamentos na mesma transação; checkout sem `pwd` → 400 | AP-09, AP-03 |
| 3 | `password` sai de todas as respostas; o login devolve um token **assinado e com validade** (`SESSION_TOKEN_MAX_AGE`) em vez de `fake-jwt-token-<id>` | AP-04, AP-06 |
| 3 | `PUT`/`DELETE /users/<id>`, `POST /tasks` e `PUT`/`DELETE /tasks/<id>` exigem `Authorization: Bearer <token>`: 401 sem token válido, 403 se quem chama não é o dono nem admin | AP-06 (RF-16) |
| 3 | Alterar `role`/`active`, cadastrar com papel privilegiado e atribuir task a outro usuário exigem admin (`X-Admin-Token` ou token de usuário `admin`) | AP-06 |
| 3 | `POST`/`PUT`/`DELETE /categories` (recurso sem dono) exigem admin; sem `ADMIN_TOKEN` configurado, ficam fechadas para quem não é usuário `admin` | AP-06 (RF-05) |
| 3 | Entrada inválida → 400 em vez de 500; 404 de rota inexistente em JSON | AP-15, AP-14 |
| 3 | Dependências sem uso removidas (`marshmallow`, `requests`) | AP-19 |

A mudança mais ampla é a do P3. As escritas sobre usuários e tasks passaram a exigir o token
do login, e o dono e o admin continuam com o comportamento original. As leituras e o
cadastro público (`POST /users` com papel padrão) seguem abertos, como no original.

### Como a skill se comportou em cada stack

- **Flask monolito (P1):** fez a decomposição completa para `src/`, com 6 domínios. O caso
  mais trabalhoso: 40 passos de validação, incluindo provar que um pedido acima do estoque
  desfaz tudo (transação).
- **Express (P2):** detectou a stack sem nenhuma mudança na skill. Transformou o callback
  hell em `async/await` com wrappers de Promise (RF-15) e trocou o "hash" caseiro por
  `crypto.scrypt`, sem nenhuma dependência nova.
- **Flask em camadas (P3):** foi o teste de adaptação. A skill **não recriou** o projeto:
  manteve `models/`, `routes/`, `services/` e `utils/`, criou só `config/`, `controllers/`
  e `middlewares/`, passou a usar os métodos de model que já existiam e eram ignorados, e
  separou o CRUD de categorias. Desde a v1.2, ela reaproveita o login existente: o token
  passa a ser validado (`middlewares/auth.py`) e a autorização é dono-ou-admin, inclusive
  para o `user_id` das tasks.
- **Limitações observadas:**
  - **O resultado varia entre execuções.** Com a mesma skill, a v1.2 cobriu o `user_id` e a
    v1.2.1 não. Só o teste de ataque, rodado por fora, pegou a diferença. Por isso a regra
    virou texto explícito na v1.2.2, e o teste independente continua necessário a cada
    execução.
  - Na v1.1, a recomendação de autenticação do P3 foi aplicada pela metade e o roteiro de
    validação não pegou a falha. Ela só apareceu na correção.
  - A skill às vezes afirma, sem testar, comportamentos que a execução desmente (P3-11: a
    v1.2.1 testou e acertou; a v1.2.2 afirmou sem testar e errou).
  - Hashes MD5 já gravados: a execução da v1.1 regravava o hash no primeiro login. A da
    v1.2.2 não regrava, então um banco antigo com MD5 responde 401 até rodar o `seed.py` ou
    trocar a senha. Isso está listado em `Pending`, só afeta bancos criados antes da
    refatoração, e as guidelines tratam migração de dados já gravados como fora do escopo.
  - Refresh e revogação de token e rate limiting ficaram fora do escopo.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code CLI](https://code.claude.com/docs) instalado e autenticado
  (`npm install -g @anthropic-ai/claude-code`; conferir com `claude --version`)
- Python 3.10+ e Node.js 18+ no PATH
- `curl`, que já vem no Linux, no macOS e no Windows 10+
- Git, para voltar ao código original

### Executar a skill em cada projeto

A sessão do Claude precisa começar **dentro da pasta do projeto**, para que a cópia local da
skill seja carregada:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução:
1. A skill imprime a **Fase 1**, gera o relatório da **Fase 2** em
   `.refactor-arch/audit-report.md` e pergunta
   `Proceed with refactoring (Phase 3)? [y/n]`.
2. Responda `n` para só auditar (nenhum arquivo de código é alterado) ou `y` para refatorar.
3. Na Fase 3, aprove as permissões pedidas para criar o ambiente, subir o servidor, rodar
   `curl` e editar arquivos.

Opcional: `claude "/refactor-arch reports/meu-relatorio.md"` grava o relatório em outro
caminho.

> No Windows, se o PowerShell bloquear o `claude.ps1` por política de execução, use
> `claude.cmd "/refactor-arch"` ou rode pelo Git Bash.

### Reexecutar a partir do código original

O código original dos 3 projetos está marcado pela tag `baseline`. Na raiz do repositório:

```bash
# restaura o código original e APAGA os arquivos criados pela refatoração (mantém a skill)
git restore --source=baseline --staged --worktree -- <projeto>/ ":(exclude)<projeto>/.claude"
# remove o que não é rastreado: .refactor-arch/, bancos, __pycache__, venvs
git clean -fdx <projeto>/ -e .claude
```

> Use `git restore`, e não `git checkout baseline -- <projeto>/`. O `checkout` não apaga os
> arquivos criados depois da baseline (`controllers/`, `config/`…), e a skill encontraria
> um projeto meio refatorado.

### Validar que a refatoração funcionou

1. Abra `<projeto>/.refactor-arch/validation-after.md`. A linha `Summary` deve mostrar
   `REGRESSION 0`, e cada `CHANGED` deve estar explicado na coluna Note.
2. Suba a aplicação com o comando original e chame alguns endpoints:

| Projeto | Preparar | Subir | Exemplo |
|---|---|---|---|
| 1 | `python -m venv .venv` + `pip install -r requirements.txt` | `python app.py` | `curl http://127.0.0.1:5000/produtos` |
| 2 | `npm install` | `npm start` | requisições de `api.http` |
| 3 | `python -m venv .venv` + `pip install -r requirements.txt` + `python seed.py` | `python app.py` | `curl http://127.0.0.1:5000/tasks` |

3. Para as rotas administrativas, suba com `ADMIN_TOKEN=<valor>` e envie o header
   `X-Admin-Token: <valor>`. As variáveis de cada projeto estão documentadas em
   `.env.example`.
4. No P3, as escritas sobre usuários e tasks usam o token do login:

   ```bash
   TOKEN=$(curl -s -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" \
     -d '{"email":"maria@email.com","password":"abcd"}' | python -c "import sys,json;print(json.load(sys.stdin)['token'])")
   curl -i -X PUT http://127.0.0.1:5000/users/2 -H "Content-Type: application/json" \
     -d '{"name":"Maria S."}'                                  # 401: sem token
   curl -i -X PUT http://127.0.0.1:5000/users/3 -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" -d '{"name":"x"}'     # 403: não é o dono
   curl -i -X PUT http://127.0.0.1:5000/users/2 -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" -d '{"name":"Maria S."}'  # 200: dono
   ```

---

## Estrutura do repositório

```text
mba-ia-refactor-projects-skill/
├── README.md                       # este documento
├── code-smells-project/            # Projeto 1 refatorado
│   ├── .claude/skills/refactor-arch/   # fonte da verdade da skill
│   └── .refactor-arch/                 # relatório + evidências da execução
├── ecommerce-api-legacy/           # Projeto 2 refatorado (cópia idêntica da skill)
├── task-manager-api/               # Projeto 3 refatorado (cópia idêntica da skill)
├── reports/
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
├── docs/
│   ├── analise-manual.md           # análise manual completa
│   └── iterations/                 # iteração 1 (P1), execução descartada e teste de ataque do P3
├── specs/001-refactor-arch-skill/  # SDD: spec, plan, research, data-model, contracts, tasks
└── .specify/, .claude/skills/speckit-*   # spec-kit
```

Enunciado original do desafio:
[devfullcycle/mba-ia-refactor-projects-skill](https://github.com/devfullcycle/mba-ia-refactor-projects-skill).
