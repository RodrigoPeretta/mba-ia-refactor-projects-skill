# Análise Manual

Análise feita lendo o código dos três projetos **antes** de construir a skill, e confirmada
executando cada aplicação original (smoke test chamando todos os endpoints com
`PYTHONWARNINGS=default` para expor warnings de depreciação). Quando um problema foi
reproduzido em execução, a evidência aparece em **Evidência**.

Severidades conforme o enunciado: **CRITICAL** (segurança/arquitetura que expõe dados ou
quebra completamente a separação de responsabilidades), **HIGH** (violações fortes de
MVC/SOLID), **MEDIUM** (padronização, duplicação, performance moderada), **LOW**
(legibilidade, nomes, magic numbers).

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|:-:|:-:|:-:|:-:|:-:|
| code-smells-project | Python 3 + Flask 3.1.1 + sqlite3 | 4 | 3 | 4 | 3 | 14 |
| ecommerce-api-legacy | Node.js + Express 4 + sqlite3 | 4 | 4 | 3 | 3 | 14 |
| task-manager-api | Python 3 + Flask 3.0 + Flask-SQLAlchemy 3.1 | 3 | 3 | 5 | 3 | 14 |

---

## Projeto 1 — code-smells-project (API de E-commerce, Python/Flask)

Monolito em 4 arquivos (780 linhas): `app.py` (rotas + endpoints admin), `controllers.py`
(validação + resposta HTTP), `models.py` (SQL cru + regra de negócio), `database.py`
(conexão global + schema + seed). Domínio: produtos, usuários, pedidos, itens de pedido e
relatório de vendas.

### [CRITICAL] P1-01 — SQL Injection por concatenação de strings
- **Onde:** `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 149-151, 174, 279-281, 289-297`
- **O quê:** praticamente toda query monta SQL concatenando entrada do usuário
  (`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`).
- **Evidência:** `POST /login` com `{"email": "' OR 1=1 --"}` retornou **200 logado como Admin**.
- **Por que importa:** bypass de autenticação e leitura/alteração arbitrária do banco por
  qualquer cliente. O próprio `database.py:70-83` usa placeholders `?` no seed — a correção
  é conhecida e foi ignorada no resto do código.

### [CRITICAL] P1-02 — Endpoints administrativos sem autenticação, incluindo execução de SQL arbitrário
- **Onde:** `app.py:47-57` (`POST /admin/reset-db`), `app.py:59-78` (`POST /admin/query`)
- **O quê:** um endpoint executa qualquer SQL recebido no body; outro apaga todas as tabelas.
  Nenhum dos dois exige autenticação.
- **Evidência:** `POST /admin/query {"sql": "SELECT email, senha FROM usuarios"}` devolveu
  todos os e-mails com senhas.
- **Por que importa:** é um "backdoor" de banco exposto na API — comprometimento total com
  uma única requisição.

### [CRITICAL] P1-03 — Credenciais hardcoded, vazadas pela API, e debug ligado em 0.0.0.0
- **Onde:** `app.py:7` (`SECRET_KEY = "minha-chave-super-secreta-123"`), `app.py:8, 88`
  (`DEBUG = True`, `host="0.0.0.0"`), `controllers.py:285-289` (`/health` devolve
  `secret_key`, `debug`, `db_path`)
- **Evidência:** `GET /health` retornou a `secret_key` em texto.
- **Por que importa:** a chave versionada permite forjar sessões; o debugger do Werkzeug
  exposto em todas as interfaces permite execução remota de código.

### [CRITICAL] P1-04 — Senhas em texto plano, armazenadas e devolvidas pela API
- **Onde:** `database.py:76-78` (seed), `models.py:126-129` (INSERT da senha crua),
  `models.py:109-111` (comparação direta no SQL), `models.py:83, 99` (campo `senha` no dict
  de resposta)
- **Evidência:** `GET /usuarios` e `GET /usuarios/1` retornam `"senha": "admin123"`.
- **Por que importa:** vazamento do banco (ou de um único endpoint) expõe a senha real de
  todos os usuários — e senhas costumam ser reutilizadas em outros serviços.

### [HIGH] P1-05 — Regra de negócio espalhada entre models e controllers (sem camada de domínio)
- **Onde:** `models.py:133-169` (`criar_pedido` valida estoque, calcula total e baixa
  estoque), `models.py:256-262` (faixas de desconto do relatório), `controllers.py:24-62`
  (validação de produto), `controllers.py:208-210, 247-250` (notificações como `print`)
- **Por que importa:** "model" aqui é ao mesmo tempo repositório SQL, mapeador e regra de
  negócio; o controller também decide regra. Não há onde testar a regra de pedido sem
  banco e HTTP.

### [HIGH] P1-06 — Conexão global mutável compartilhada entre threads, com schema e seed embutidos
- **Onde:** `database.py:4-11` (`db_connection` global, `check_same_thread=False`),
  `database.py:14-84` (CREATE TABLE + seed dentro de `get_db()`)
- **Por que importa:** uma única conexão sqlite compartilhada por todas as requisições
  concorrentes (estado global mutável); qualquer chamada a `get_db()` pode disparar
  criação de schema e seed — efeito colateral escondido num getter.

### [HIGH] P1-07 — Criação de pedido não atômica
- **Onde:** `models.py:139-168`
- **O quê:** valida estoque num loop e faz INSERT/UPDATE em outro, sem transação explícita
  nem rollback. Se algo falhar no meio, as escritas parciais ficam pendentes na conexão
  global e são commitadas pela **próxima** requisição que chamar `commit()`.
- **Por que importa:** pedido sem itens, estoque baixado sem pedido, e condição de corrida
  entre "checar estoque" e "baixar estoque".

### [MEDIUM] P1-08 — Queries N+1
- **Onde:** `models.py:187-199` e `models.py:219-231` (1 query de pedidos + 1 por pedido
  + 1 por item); `models.py:239-254` (5 queries de COUNT/SUM que caberiam num `GROUP BY`)
- **Por que importa:** custo cresce linearmente com pedidos × itens; em produção vira
  gargalo de latência.

### [MEDIUM] P1-09 — Duplicação de código (e validações divergentes)
- **Onde:** mapeamento row→dict repetido em `models.py:12-21, 31-40, 304-313` (produto) e
  `79-86, 95-102` (usuário); `get_pedidos_usuario` e `get_todos_pedidos` quase idênticos
  (`models.py:171-201` × `203-233`); validação de produto duplicada em
  `controllers.py:28-50` × `72-90`
- **Por que importa:** a cópia já divergiu — `atualizar_produto` não valida tamanho do nome
  nem categoria, então um PUT aceita dados que o POST rejeita.

### [MEDIUM] P1-10 — Tratamento de erro não centralizado, que vaza detalhes internos
- **Onde:** todos os controllers repetem `except Exception as e: return jsonify({"erro": str(e)}), 500`
  (`controllers.py:10-12, 21-22, 60-62, ...`); `controllers.py:169-170, 239-240` chamam
  `dados.get(...)` sem checar se o body existe
- **Por que importa:** mensagens de exceção (SQL, caminhos) vão para o cliente; um body
  vazio vira 500 em vez de 400; não existe um único ponto para padronizar erros.

### [MEDIUM] P1-11 — CORS liberado para qualquer origem
- **Onde:** `app.py:9` (`CORS(app)`)
- **Por que importa:** qualquer site pode chamar a API a partir do navegador da vítima —
  combinado com P1-02, amplia a superfície de ataque. Middleware configurado sem critério.

### [LOW] P1-12 — Logging via `print`, incluindo dados pessoais
- **Onde:** `controllers.py:8, 57, 106, 161, 179, 182, 208-210, 219`
- **Por que importa:** sem nível, sem formato, sem destino configurável; registra e-mails
  de usuários no stdout.

### [LOW] P1-13 — Magic numbers e listas mágicas
- **Onde:** `models.py:257-262` (10000/5000/1000 e 0.1/0.05/0.02), `controllers.py:52`
  (categorias válidas), `controllers.py:242` (status válidos), `controllers.py:47-50`
  (limites 2/200 do nome)
- **Por que importa:** regras de negócio sem nome, impossíveis de reaproveitar ou de
  encontrar por busca.

### [LOW] P1-14 — Nomes ruins e imports não usados
- **Onde:** parâmetro/variável `id` sombreando o builtin (`controllers.py:14, 56, 160`);
  `import sqlite3` sem uso (`models.py:2`), `import os` sem uso (`database.py:2`);
  `"ambiente": "producao"` e versão fixos no código (`controllers.py:285-286`)

**APIs deprecated:** nenhuma encontrada — Flask 3.1 e `sqlite3` são usados com APIs atuais
(nenhum warning de depreciação no log do servidor).

---

## Projeto 2 — ecommerce-api-legacy (LMS com checkout, Node.js/Express)

Três arquivos (180 linhas): `app.js` (bootstrap), `AppManager.js` (uma classe com banco,
schema, seed, rotas e regras), `utils.js` (config + "cripto" + cache global). Domínio:
usuários, cursos, matrículas, pagamentos e log de auditoria. Endpoints: `POST /api/checkout`,
`GET /api/admin/financial-report`, `DELETE /api/users/:id`.

### [CRITICAL] P2-01 — Credenciais e chave de pagamento hardcoded
- **Onde:** `utils.js:1-7` (`dbPass: "senha_super_secreta_prod_123"`,
  `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser`)
- **Por que importa:** segredos de produção versionados no repositório; trocar de ambiente
  exige editar código.

### [CRITICAL] P2-02 — Número do cartão e chave do gateway escritos em log
- **Onde:** `AppManager.js:45` (`console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`)
- **Por que importa:** viola PCI-DSS de forma direta — o PAN completo e a chave live vão
  para qualquer agregador de logs.

### [CRITICAL] P2-03 — "Hash" de senha reversível e com colisões, e senha padrão silenciosa
- **Onde:** `utils.js:17-23` (`badCrypto`), `AppManager.js:68` (`badCrypto(p || "123456")`),
  `AppManager.js:18` (seed com senha `'123'` em texto)
- **Evidência:** `badCrypto` usa só os 2 primeiros caracteres do base64 da senha, repetidos.
  `senhaforte` e `senha123` geram o mesmo valor `c2c2c2c2c2`; `123` e `123456` geram
  `MTMTMTMTMT`. O loop de 10.000 iterações não acrescenta nada.
- **Por que importa:** qualquer senha que comece com as mesmas letras "confere"; e um
  checkout sem `pwd` cria a conta com senha `123456` sem avisar ninguém.

### [CRITICAL] P2-04 — God Class `AppManager`
- **Onde:** `AppManager.js:4-139`; instanciada em `app.js:8-10`
- **O quê:** uma classe concentra conexão, DDL, seed, registro de rotas, validação de
  entrada, regra de pagamento, criação de usuário, matrícula, auditoria e relatório.
- **Por que importa:** separação de responsabilidades inexistente — nenhuma parte pode ser
  testada ou trocada isoladamente.

### [HIGH] P2-05 — Checkout sem transação, em "callback hell"
- **Onde:** `AppManager.js:37-77` (5 níveis de callbacks aninhados), `AppManager.js:50-61`
  (INSERT de matrícula e de pagamento separados), `AppManager.js:57` (erro do audit log ignorado)
- **Por que importa:** se o INSERT de pagamento falhar, a matrícula já gravada fica sem
  pagamento; o fluxo é ilegível e impossível de compor.

### [HIGH] P2-06 — Endpoints administrativos sem autenticação, e exclusão que deixa órfãos
- **Onde:** `AppManager.js:80` (`GET /api/admin/financial-report`), `AppManager.js:131-137`
  (`DELETE /api/users/:id` ignora `err` e não remove matrículas/pagamentos)
- **Evidência:** depois de `DELETE /api/users/1`, o relatório financeiro continua contando
  o pagamento de 997, agora com aluno `"Unknown"`. A própria resposta admite:
  *"as matrículas e pagamentos ficaram sujos no banco"*.
- **Por que importa:** qualquer um lê dados financeiros e apaga usuários; integridade
  referencial quebrada.

### [HIGH] P2-07 — Estado global mutável
- **Onde:** `utils.js:9-10` (`globalCache`, `totalRevenue`), `utils.js:12-15` (`logAndCache`)
- **O quê:** cache em objeto de módulo que só cresce e nunca é lido; `totalRevenue` é um
  primitivo exportado (copiado por valor), importado em `AppManager.js:2` e nunca usado.
- **Por que importa:** vazamento de memória em produção e estado compartilhado escondido
  entre requisições.

### [HIGH] P2-08 — Regra de negócio dentro do handler de rota
- **Onde:** `AppManager.js:46` (aprovação de pagamento = `cc.startsWith("4")`),
  `AppManager.js:66-72` (criação implícita de usuário dentro do checkout)
- **Por que importa:** a "rota" decide pagamento e cadastro; trocar o gateway exige mexer
  no roteamento.

### [MEDIUM] P2-09 — N+1 no relatório financeiro, com erros ignorados
- **Onde:** `AppManager.js:89-127` (1 query de cursos + 1 por curso + 2 por matrícula),
  `AppManager.js:92, 104, 106` (o `err` dos callbacks é descartado)
- **Por que importa:** custo cresce com matrículas; se a query da linha 92 falhar,
  `enrollments.length` sobre `undefined` derruba o processo inteiro.

### [MEDIUM] P2-10 — Validação ausente e respostas inconsistentes
- **Onde:** `AppManager.js:35` (não valida formato de e-mail, cartão nem `pwd`);
  `AppManager.js:35, 38, 48` respondem `text/plain` enquanto `AppManager.js:60` responde JSON
- **Evidência:** `POST /api/checkout {"usr": "x"}` → `400 "Bad Request"` em texto puro.
- **Por que importa:** o cliente não consegue tratar erros de forma uniforme; dados
  inválidos chegam ao banco.

### [MEDIUM] P2-11 — Configuração fixa no código (banco em memória, porta)
- **Onde:** `AppManager.js:7` (`new sqlite3.Database(':memory:')`), `utils.js:6` (`port: 3000`)
- **Por que importa:** todos os dados se perdem a cada restart e não há como apontar para
  outro banco ou porta por variável de ambiente.

### [LOW] P2-12 — Nomes crípticos
- **Onde:** `AppManager.js:29-33` (`u`, `e`, `p`, `cid`, `cc`), contrato com `usr`, `eml`,
  `pwd`, `c_id`; `const self = this` (`AppManager.js:26`) misturado com `this` (`52-54`)

### [LOW] P2-13 — Magic numbers
- **Onde:** `utils.js:19` (`10000`), `utils.js:22` (`10`), `AppManager.js:46` (prefixo `"4"`)

### [LOW] P2-14 — Logging com `console.log` e uso de `let` onde não há reatribuição
- **Onde:** `app.js:13`, `utils.js:13`, `AppManager.js:29-33, 81, 86, 90`

**APIs deprecated:** nenhuma API de runtime deprecated no código da aplicação. O
`npm install` avisa que `tar@6.2.1` (transitiva via `sqlite3@5.1.7` → `node-gyp`) está
deprecated e tem vulnerabilidades publicadas — dependência a ser atualizada.

---

## Projeto 3 — task-manager-api (Task Manager, Python/Flask)

Já tem camadas (`models/`, `routes/`, `services/`, `utils/`), com
Flask-SQLAlchemy. Domínio: tasks, usuários, categorias e relatórios. A organização é
**aparente**: as rotas concentram a regra de negócio, e o que existe em `utils/` e nos
models para evitar isso não é usado.

### [CRITICAL] P3-01 — Credenciais hardcoded
- **Onde:** `app.py:13` (`SECRET_KEY = 'super-secret-key-123'`),
  `services/notification_service.py:7-10` (host, usuário e **senha** SMTP)
- **Por que importa:** segredos versionados; a senha do e-mail transacional fica exposta a
  quem tiver acesso ao repositório.

### [CRITICAL] P3-02 — Senhas com MD5 sem salt
- **Onde:** `models/user.py:27-32`; seed com senhas triviais em `seed.py:19, 26, 33`
- **Por que importa:** MD5 é quebrado por tabela de hash em segundos — o hash de `1234`
  (`81dc9bdb...`) é o primeiro resultado de qualquer busca.

### [CRITICAL] P3-03 — Hash da senha exposto em todas as respostas de usuário
- **Onde:** `models/user.py:21` (`to_dict` inclui `password`), usado em
  `routes/user_routes.py:33` (GET), `85` (POST), `129` (PUT) e `209` (login)
- **Evidência:** `POST /users` e `POST /login` retornam `"password": "81dc9bdb..."`.
- **Por que importa:** somado a P3-02, qualquer resposta de usuário entrega a senha
  praticamente em claro.

### [HIGH] P3-04 — Autenticação de fachada e escalonamento de privilégio
- **Onde:** `routes/user_routes.py:210` (`'token': 'fake-jwt-token-' + str(user.id)`),
  `routes/user_routes.py:52, 71-78` (role vem do body, `admin` aceito)
- **Por que importa:** o token é previsível e nenhuma rota o verifica; qualquer cliente
  cria um usuário `admin` e apaga qualquer usuário ou task.

### [HIGH] P3-05 — Modo debug em 0.0.0.0
- **Onde:** `app.py:34` (`app.run(debug=True, host='0.0.0.0')`)
- **Evidência:** `POST /tasks {"priority": "alta"}` → 500 com página HTML do debugger do
  Werkzeug e traceback completo.
- **Por que importa:** vaza código e caminhos, e o console do debugger permite executar
  código remotamente.

### [HIGH] P3-06 — "Fat routes": regra de negócio nas rotas, e a camada de domínio existente é ignorada
- **Onde:** `routes/task_routes.py:85-154, 156-223` (validação + regra + persistência);
  `routes/report_routes.py:12-101` (agregações); lógica de "atrasada" reimplementada **6
  vezes** (`task_routes.py:30-39, 71-80, 283-287`, `user_routes.py:171-180`,
  `report_routes.py:34-43, 132-135`) enquanto `Task.is_overdue()` existe em
  `models/task.py:50-60`; `utils/helpers.py:57-108` (`process_task_data`) e as constantes
  `helpers.py:110-116` existem e **não são usados**
- **Por que importa:** não há controller nem service — a rota é a regra. E as cópias
  divergem: `helpers.parse_date` aceita `dd/mm/yyyy` e converte prioridade para `int`; as
  rotas não fazem nenhuma das duas coisas.

### [MEDIUM] P3-07 — Queries N+1
- **Onde:** `routes/task_routes.py:41-57` (2 queries extras por task),
  `routes/user_routes.py:22` (lazy load de `u.tasks` por usuário),
  `routes/report_routes.py:53-68` (1 query por usuário), `report_routes.py:159-164`
  (1 COUNT por categoria); `report_routes.py:15-28` e `task_routes.py:275-279` fazem 9 e
  5 COUNTs separados em vez de um `GROUP BY`
- **Por que importa:** `GET /tasks` com N tasks faz 2N+1 queries.

### [MEDIUM] P3-08 — APIs deprecated
- **`Query.get()`** (legado desde SQLAlchemy 2.0 → usar `db.session.get(Model, id)`):
  `task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`;
  `user_routes.py:29, 94, 136, 155`; `report_routes.py:105, 192, 213`
- **`datetime.utcnow()`** (deprecated no Python 3.12+ → `datetime.now(timezone.utc)`):
  `models/task.py:15-16, 52`, `models/user.py:14`, `models/category.py:11`,
  `task_routes.py:31, 72, 215, 285`, `user_routes.py:172`,
  `report_routes.py:35, 42, 45, 71, 133`, `notification_service.py:35`, `helpers.py:38`,
  `seed.py:66-74`
- **Evidência:** o servidor emitiu `LegacyAPIWarning` e `DeprecationWarning` exatamente
  nessas linhas durante o smoke test (Python 3.13).
- **Por que importa:** vão quebrar em upgrades de SQLAlchemy/Python; `utcnow()` ainda
  gera datetimes "naive", fonte clássica de bugs de fuso.

### [MEDIUM] P3-09 — `except:` genérico e validação de tipos ausente
- **Onde:** bare `except:` em `task_routes.py:62, 137, 204, 236`,
  `user_routes.py:130, 149`, `report_routes.py:186, 207, 221`, `helpers.py:46, 48, 88`;
  `task_routes.py:113, 182` comparam `priority` sem checar tipo;
  `report_routes.py:196-197` não checa body nulo
- **Evidência:** `priority: "alta"` → `TypeError` → 500 (deveria ser 400).
- **Por que importa:** `except:` engole até `KeyboardInterrupt` e esconde a causa real;
  erro do cliente vira erro do servidor.

### [MEDIUM] P3-10 — Coesão errada: CRUD de categorias dentro de `report_routes.py`
- **Onde:** `routes/report_routes.py:157-223`
- **Por que importa:** quem procura a rota de categorias não a encontra; o blueprint de
  relatórios passa a ter dois motivos para mudar (viola SRP).

### [MEDIUM] P3-11 — Integridade referencial feita à mão (ou não feita)
- **Onde:** `user_routes.py:140-142` (apaga tasks num loop em vez de cascade);
  `report_routes.py:218` (apagar categoria deixa tasks com `category_id` apontando para
  um registro inexistente)
- **Por que importa:** a regra de integridade fica fora do model e é inconsistente entre
  entidades.

### [LOW] P3-12 — Imports e dependências não usados
- **Onde:** `app.py:7` (`os, sys, json`), `task_routes.py:7` (`json, os, sys, time`),
  `user_routes.py:6` (`hashlib, json`), `report_routes.py:7-8` (`format_date`,
  `calculate_percentage`, `json`), `helpers.py:3-7` (`os, json, sys, math, hashlib`),
  `models/task.py:3` (`json`); `requirements.txt:4-6` (`marshmallow`, `requests`,
  `python-dotenv` nunca importados)

### [LOW] P3-13 — Magic numbers e strings repetidas
- **Onde:** lista de status em `task_routes.py:110, 177` e `models/task.py:39`; roles em
  `user_routes.py:71, 120`; limites de prioridade em `task_routes.py:113, 182`; senha
  mínima `4` em `user_routes.py:64, 115`; `priority <= 2` em `report_routes.py:129`;
  `7` dias em `report_routes.py:45` — enquanto as constantes já existem em `helpers.py:110-116`

### [LOW] P3-14 — Código verboso e não idiomático
- **Onde:** `if ...: return True else: return False` em `models/user.py:34-38` e
  `models/task.py:38-48`; `type(tags) == list` em `task_routes.py:141, 210`; montagem
  manual de dict em `task_routes.py:17-28` duplicando `Task.to_dict()`; `print` como
  logging em todas as rotas

---

## Padrões recorrentes → insumo para o catálogo da skill

| Anti-pattern | P1 | P2 | P3 | Severidade-base |
|---|:-:|:-:|:-:|---|
| SQL Injection (SQL concatenado com entrada) | ✓ | | | CRITICAL |
| Credenciais/segredos hardcoded | ✓ | ✓ | ✓ | CRITICAL |
| Senha em texto plano ou hash fraco (MD5, base64, caseiro) | ✓ | ✓ | ✓ | CRITICAL |
| Dado sensível exposto em resposta ou log | ✓ | ✓ | ✓ | CRITICAL |
| God Class / God Module | ✓ | ✓ | | CRITICAL |
| Endpoint administrativo/destrutivo sem autenticação | ✓ | ✓ | ✓ | CRITICAL/HIGH |
| Debug ligado em produção / bind em 0.0.0.0 | ✓ | | ✓ | HIGH |
| Regra de negócio em rota/controller ("fat controller") | ✓ | ✓ | ✓ | HIGH |
| Estado global mutável | ✓ | ✓ | | HIGH |
| Operação multi-escrita sem transação | ✓ | ✓ | | HIGH |
| Queries N+1 / agregação em loop | ✓ | ✓ | ✓ | MEDIUM |
| Duplicação de lógica (e cópias que divergem) | ✓ | | ✓ | MEDIUM |
| Error handling genérico, não centralizado | ✓ | ✓ | ✓ | MEDIUM |
| Validação de entrada ausente/inconsistente | ✓ | ✓ | ✓ | MEDIUM |
| APIs deprecated | | (dep.) | ✓ | MEDIUM |
| Configuração fixa no código (porta, DB, CORS) | ✓ | ✓ | ✓ | MEDIUM |
| Magic numbers/strings | ✓ | ✓ | ✓ | LOW |
| Imports/código morto | ✓ | | ✓ | LOW |
| `print`/`console.log` como logging | ✓ | ✓ | ✓ | LOW |
| Nomes crípticos | ✓ | ✓ | | LOW |

## Comportamento de referência (baseline antes da refatoração)

Todos os endpoints dos três projetos responderam no estado original. É esse contrato
(rotas, métodos, códigos de status e formato do JSON) que a Fase 3 precisa preservar.

| Projeto | Endpoints exercitados | Resultado |
|---|---|---|
| P1 (porta 5000) | `GET /`, `/health`, `/produtos`, `/produtos/busca`, `/produtos/:id`; `POST/PUT/DELETE /produtos`; `GET/POST /usuarios`, `GET /usuarios/:id`; `POST /login`; `POST/GET /pedidos`, `GET /pedidos/usuario/:id`, `PUT /pedidos/:id/status`; `GET /relatorios/vendas`; `POST /admin/query` | todos 2xx/404 esperados |
| P2 (porta 3000) | `POST /api/checkout` (aprovado, recusado, inválido), `GET /api/admin/financial-report`, `DELETE /api/users/:id` | 200 / 400 / 400 / 200 / 200 |
| P3 (porta 5000, após `seed.py`) | `GET /`, `/health`; CRUD de `/tasks`, `/tasks/search`, `/tasks/stats`; CRUD de `/users`, `/users/:id/tasks`, `POST /login`; `/reports/summary`, `/reports/user/:id`; CRUD de `/categories` | todos 2xx, exceto o 500 de P3-09 |
