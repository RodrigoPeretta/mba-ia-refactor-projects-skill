# ARCHITECTURE AUDIT REPORT

- **Project:** task-manager-api
- **Stack:** Python + Flask 3.0.0
- **Files:** 15 analyzed | ~1158 lines of code
- **Architecture:** Parcialmente em camadas

## Summary

CRITICAL: 4 | HIGH: 3 | MEDIUM: 8 | LOW: 3

## Findings

### [CRITICAL] Hash de senha exposto nas respostas da API
- **ID:** AP-04
- **File:** `models/user.py:16-25`; `routes/user_routes.py:33, 85, 129, 207-211`
- **Description:** `User.to_dict()` inclui `'password': self.password` (o hash MD5). Esse dict é devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`, todos sem autenticação — qualquer cliente obtém o hash de qualquer usuário só iterando ids.
- **Impact:** Vazamento em massa de hashes MD5 sem salt, que são revertidos por rainbow tables em segundos (as senhas do seed são `1234`, `abcd`, `pass`); comprometimento de contas e de reuso de senha em outros sistemas.
- **Recommendation:** Remover `password` da serialização pública do model (serializer explícito sem campos sensíveis) em todas as respostas (RF-04).

### [CRITICAL] Ausência de autenticação: token previsível, rotas destrutivas abertas e escalada de papel
- **ID:** AP-06
- **File:** `routes/user_routes.py:52, 71-72, 119-122, 134-151, 207-211`; `routes/task_routes.py:225-238`; `routes/report_routes.py:211-223`
- **Description:** `POST /login` devolve `'token': 'fake-jwt-token-' + str(user.id)` (prefixo fixo + id) e nenhuma rota valida token algum. `POST /users` aceita `role` do corpo (`data.get('role', 'user')`, aceitando `admin`) e `PUT /users/<id>` permite trocar `role`/`active` de qualquer usuário. `DELETE /users/<id>` (apaga também as tasks do usuário), `DELETE /tasks/<id>` e `DELETE /categories/<id>` não verificam identidade.
- **Impact:** Qualquer pessoa cria um usuário `admin`, promove/desativa contas de terceiros e apaga usuários, tarefas e categorias; o token não prova nada (forjável conhecendo o id).
- **Recommendation:** Manter as rotas e protegê-las: emitir token assinado com `SECRET_KEY` no login, exigir token válido nas rotas de escrita sobre usuários e nas exclusões, e restringir a atribuição de `role` diferente de `user` a administradores autenticados (fechado por padrão) (RF-05).

### [CRITICAL] Senhas com hash MD5 sem salt
- **ID:** AP-03
- **File:** `models/user.py:27-32`; `seed.py:19, 26, 33`
- **Description:** `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara com `==` contra o valor salvo. O seed grava senhas triviais (`'1234'`, `'abcd'`, `'pass'`) com esse hash; a política aceita senhas de 4 caracteres (`routes/user_routes.py:64`).
- **Impact:** Hashes idênticos para senhas iguais, quebra instantânea por força bruta/rainbow table; comparação sem tempo constante.
- **Recommendation:** Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (PBKDF2/scrypt com salt), mantendo compatibilidade de login com hashes MD5 legados até a regravação (RF-03).

### [CRITICAL] Segredos e credenciais hardcoded
- **ID:** AP-02
- **File:** `app.py:13`; `services/notification_service.py:9-10`
- **Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` e credenciais SMTP literais `self.email_user = 'taskmanager@gmail.com'` / `self.email_password = 'senha123'` no código versionado.
- **Impact:** Qualquer pessoa com acesso ao repositório pode assinar sessões/tokens da aplicação e usar a conta de e-mail; segredos não podem ser rotacionados sem deploy.
- **Recommendation:** Mover para variáveis de ambiente lidas por um módulo de config (`.env` + `.env.example` sem valores reais), sem default inseguro em produção (RF-02).

### [HIGH] Regra de negócio, validação e serialização dentro das rotas (fat controller)
- **ID:** AP-07
- **File:** `routes/task_routes.py:11-63, 85-154, 156-223, 273-299`; `routes/user_routes.py:42-90, 92-132, 134-151, 153-183`; `routes/report_routes.py:12-101, 103-155, 157-223`
- **Description:** Os handlers fazem validação + regra + persistência + montagem de resposta em 40–90 linhas cada: cálculo de atraso reimplementado inline (o model já tem `Task.is_overdue`, `validate_status`, `validate_priority` em `models/task.py:38-60`, não usados), estatísticas e taxa de conclusão calculadas nas rotas, exclusão em cascata das tasks decidida em `delete_user` (`user_routes.py:140-142`). O CRUD de categorias está registrado no blueprint de relatórios (`report_routes.py:157-223`), misturando dois recursos no mesmo módulo.
- **Impact:** Regras impossíveis de testar sem HTTP, cópias que divergem e dificuldade de evoluir regras (ex.: alterar o critério de atraso exige mudar 6 lugares).
- **Recommendation:** Extrair services por domínio (tasks, users, categories, reports) com a regra de negócio, controllers finos que só leem a requisição e chamam o service, e mover categorias para seu próprio controller/rotas (RF-07).

### [HIGH] Rotas acopladas diretamente à sessão do ORM e serviço instanciando SMTP
- **ID:** AP-11
- **File:** `routes/task_routes.py:2, 146-154, 217-223, 231-238`; `routes/user_routes.py:2, 80-90, 127-132, 140-151`; `routes/report_routes.py:2, 182-188, 204-209, 217-223`; `services/notification_service.py:5-20`
- **Description:** Os blueprints importam `db` e chamam `db.session.add/delete/commit/rollback` e `Model.query` diretamente, sem camada de serviço/repositório entre a rota e a persistência. `NotificationService` cria `smtplib.SMTP(self.email_host, self.email_port)` dentro de `send_email` com configuração fixa em `__init__`, em vez de receber o transporte/configuração.
- **Impact:** Controle transacional espalhado por 9 handlers, impossível substituir persistência ou SMTP em testes; trocar a infraestrutura obriga a mexer nas rotas.
- **Recommendation:** Centralizar o acesso a dados e o commit/rollback nos services/models; injetar configuração (host, porta, credenciais) no serviço de notificação a partir da config (RF-08, RF-06).

### [HIGH] Debug ligado e bind aberto fixos no código
- **ID:** AP-10
- **File:** `app.py:33-34`
- **Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` literal: debugger interativo do Werkzeug e reloader ativos na execução padrão, escutando em todas as interfaces.
- **Impact:** Em qualquer ambiente acessível pela rede, o debugger permite execução remota de código em caso de erro; stack traces vazam para o cliente.
- **Recommendation:** Ler `DEBUG` (default `false`), `HOST` (default `127.0.0.1`) e `PORT` (default `5000`) de variáveis de ambiente via config (RF-02).

### [MEDIUM] N+1 queries e agregações em loop
- **ID:** AP-12
- **File:** `routes/task_routes.py:14, 41-57, 275-287`; `routes/user_routes.py:12-22`; `routes/report_routes.py:15-30, 53-68, 159-164`
- **Description:** `GET /tasks` faz `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` para cada task (2N+1 queries). `GET /users` acessa o relacionamento lazy `len(u.tasks)` por usuário. `/reports/summary` faz 12 `COUNT` separados sobre `tasks`, carrega a tabela inteira (`Task.query.all()`) para contar atrasadas e faz uma query por usuário; `GET /categories` faz um `COUNT` por categoria; `/tasks/stats` faz 5 `COUNT` + `all()`.
- **Impact:** Latência e carga no banco crescem linearmente com o número de registros; relatórios ficam lentos rapidamente.
- **Recommendation:** Usar `joinedload`/joins para nomes de usuário e categoria, `GROUP BY` para contagens por status/prioridade/usuário/categoria e filtro SQL para atrasadas (RF-10).

### [MEDIUM] Lógica duplicada e cópias divergentes
- **ID:** AP-13
- **File:** `routes/task_routes.py:17-39, 71-80, 92-114, 166-184, 283-287`; `routes/user_routes.py:61-72, 105-122, 162-180`; `routes/report_routes.py:33-37, 132-135`; `models/task.py:23-60`; `utils/helpers.py:19-23, 57-116`
- **Description:** O cálculo de atraso aparece copiado 6 vezes nas rotas enquanto `Task.is_overdue()` existe; `GET /tasks` remonta à mão os campos de `Task.to_dict()`; validações de criação e atualização de task/usuário são duplicadas e já divergiram (`'Formato de data inválido. Use YYYY-MM-DD'` vs `'Formato de data inválido'`; `'Senha deve ter no mínimo 4 caracteres'` vs `'Senha muito curta'`; o update de usuário não valida `name`). `utils/helpers.py` tem `validate_email`, `process_task_data`, `VALID_STATUSES`, `VALID_ROLES` e limites prontos, não usados.
- **Impact:** Correções aplicadas em uma cópia e esquecidas nas outras; comportamento inconsistente entre endpoints.
- **Recommendation:** Concentrar a regra de atraso e a serialização no model, e as validações em um único módulo de validação reutilizado por criação e atualização (RF-07, RF-12).

### [MEDIUM] Validação de entrada ausente ou sem checagem de tipo
- **ID:** AP-15
- **File:** `routes/task_routes.py:104, 113, 166-171, 181-184, 260-264`; `routes/report_routes.py:196-202, 177-180`; `routes/user_routes.py:102-103, 124-125`
- **Description:** `priority < 1` e `data['priority'] < 1` comparam sem checar tipo (`"2"` gera `TypeError` → 500); `len(data['title'])` quebra com `null`/número; `int(priority)` e `int(user_id)` da query string de `/tasks/search` geram `ValueError` → 500; `PUT /categories/<id>` usa `'name' in data` sem checar `None` e aceita nome vazio; `color` não é validada (há `is_valid_color` sem uso); `PUT /users` aceita `name` vazio e `active` de qualquer tipo.
- **Impact:** Erros de cliente viram 500 com página HTML, dados inválidos são gravados (nome vazio, cor arbitrária, `active: "não"`).
- **Recommendation:** Validar presença, tipo e faixa de cada campo em um módulo de validação único antes de chegar ao service, retornando 400 com mensagem (RF-12).

### [MEDIUM] Tratamento de erro genérico e sem handler central
- **ID:** AP-14
- **File:** `routes/task_routes.py:13, 62-63, 137, 151-154, 204, 221-223, 236-238`; `routes/user_routes.py:87-90, 130-132, 149-151`; `routes/report_routes.py:186-188, 207-209, 221-223`; `utils/helpers.py:46, 49, 88`; `app.py:9-31`
- **Description:** 12 `except:` sem tipo (inclusive engolindo `KeyboardInterrupt`/`SystemExit`), `try/except` copiado em todos os handlers, `GET /tasks` envolve todo o handler num `except:` que devolve `'Erro interno'` sem registrar nada. Não há `@app.errorhandler`: exceções fora dos `try` (ex.: `TypeError` de validação) geram 500 em HTML, enquanto o resto responde JSON.
- **Impact:** Erros mascarados e sem diagnóstico; formato de erro inconsistente para o cliente.
- **Recommendation:** Exceções de domínio tipadas (`NotFound`, `ValidationError`, `Conflict`) + error handlers globais que devolvem JSON `{'error': ...}` e registram a exceção; capturar só exceções específicas (RF-11).

### [MEDIUM] API legada `Model.query.get()` (SQLAlchemy 2.x)
- **ID:** AP-17
- **File:** `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/user_routes.py:29, 94, 136, 155`; `routes/report_routes.py:105, 192, 213`
- **Description:** 16 chamadas `Model.query.get(id)`; com Flask-SQLAlchemy 3.1.1 e SQLAlchemy 2.1.4 (instalado no ambiente) essa API é legada e emite `LegacyAPIWarning`.
- **Impact:** Avisos em runtime e quebra quando a API legada for removida.
- **Recommendation:** Substituir por `db.session.get(Model, id)` (RF-13).

### [MEDIUM] `datetime.utcnow()` deprecated (Python 3.12+)
- **ID:** AP-17
- **File:** `models/task.py:15-16, 52`; `models/category.py:11`; `models/user.py:14`; `routes/task_routes.py:31, 72, 215, 285`; `routes/user_routes.py:172`; `routes/report_routes.py:35, 42, 45, 71, 133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66-67, 69-70, 74`
- **Description:** `datetime.utcnow()` (inclusive como `default=datetime.utcnow`/`onupdate` nas colunas) está deprecated desde Python 3.12; o ambiente do projeto usa Python 3.13.14 (`.venv/pyvenv.cfg`).
- **Impact:** `DeprecationWarning` em cada chamada e remoção futura; datetimes naive sem fuso.
- **Recommendation:** Função utilitária única que devolve o instante UTC via `datetime.now(timezone.utc)` (sem tzinfo ao gravar, para manter o formato atual das respostas e compatibilidade com dados existentes) (RF-13).

### [MEDIUM] Configuração fixa no código e CORS aberto
- **ID:** AP-16
- **File:** `app.py:11, 15`; `services/notification_service.py:7-8`
- **Description:** URI do banco `'sqlite:///tasks.db'` literal, `CORS(app)` sem `origins` (libera qualquer origem) e host/porta SMTP (`'smtp.gmail.com'`, `587`) fixos.
- **Impact:** Impossível trocar banco/ambiente sem editar código; qualquer site pode chamar a API pelo navegador do usuário.
- **Recommendation:** Módulo de config lendo `DATABASE_URL`, `CORS_ORIGINS`, `SMTP_*` do ambiente com defaults seguros para desenvolvimento (RF-02).

### [MEDIUM] `print` como logging, registrando dado pessoal
- **ID:** AP-20
- **File:** `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147`; `services/notification_service.py:21, 24`; `utils/helpers.py:39-41`
- **Description:** Eventos e erros registrados com `print`, sem nível nem logger. Severidade elevada de LOW para MEDIUM porque `user_routes.py:83` registra o nome do usuário e `notification_service.py:21` o e-mail do destinatário (dado pessoal).
- **Impact:** Logs sem nível/contexto, impossíveis de filtrar ou desligar, com dados pessoais na saída padrão.
- **Recommendation:** Usar `logging` com logger por módulo, registrando ids em vez de nome/e-mail (RF-14).

### [LOW] Código morto, imports e dependências não usados
- **ID:** AP-19
- **File:** `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `models/task.py:3`; `utils/helpers.py:2-7, 9-116`; `services/notification_service.py:1-48`; `models/user.py:34-38`; `requirements.txt:4-6`
- **Description:** Imports sem uso (`os, sys, json` em app.py; `json, os, sys, time` em task_routes; `hashlib, json` em user_routes; `format_date, calculate_percentage, json` em report_routes; `json` em models/task.py; `os, json, sys, math, hashlib` em helpers). Nenhuma função de `utils/helpers.py` é chamada fora do próprio arquivo; `NotificationService` nunca é importado; `User.is_admin` nunca é usado. `marshmallow`, `requests` e `python-dotenv` estão no manifesto sem nenhum import.
- **Impact:** Ruído, falsa impressão de funcionalidades (notificações) e dependências instaladas sem uso.
- **Recommendation:** Remover imports mortos, reaproveitar ou excluir helpers não usados e remover dependências não importadas (RF-14).

### [LOW] Magic numbers e listas de valores inline
- **ID:** AP-18
- **File:** `routes/task_routes.py:96-100, 103-104, 110, 113, 167-170, 177, 182`; `routes/user_routes.py:64, 71, 115, 120`; `routes/report_routes.py:45, 129`; `models/task.py:39, 46`
- **Description:** Lista de status `['pending', 'in_progress', 'done', 'cancelled']` repetida 4 vezes, papéis `['user', 'admin', 'manager']` 2 vezes, limites de título `3`/`200`, senha mínima `4`, faixa de prioridade `1..5`, janela de `7` dias e "alta prioridade" `<= 2` escritos inline — embora `utils/helpers.py:110-116` já defina constantes equivalentes.
- **Impact:** Mudar uma regra exige caçar literais em vários arquivos, com risco de divergência.
- **Recommendation:** Centralizar em constantes de domínio e reutilizá-las (RF-14).

### [LOW] Código verboso e nomes crípticos
- **ID:** AP-21
- **File:** `routes/task_routes.py:141, 210`; `utils/helpers.py:21-23, 53-55, 103`; `models/task.py:38-60`; `models/user.py:34-38`; `models/category.py:14`; `routes/report_routes.py:24-28`
- **Description:** `type(tags) == list` em vez de `isinstance`; `if cond: return True else: return False` em `validate_status`, `validate_priority`, `is_admin`, `validate_email`, `is_valid_color`; `if` aninhado em 3 níveis em `is_overdue`; nomes `d`, `p`, `p1`..`p5`, `cat`, `t`, `u` fora de laços curtos.
- **Impact:** Leitura e manutenção mais difíceis.
- **Recommendation:** Simplificar para expressões booleanas diretas, usar `isinstance` e nomes descritivos nas variáveis internas (campos do contrato HTTP inalterados) (RF-14).

## Deprecated APIs

- `Model.query.get(id)` em `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/user_routes.py:29, 94, 136, 155`; `routes/report_routes.py:105, 192, 213` → `db.session.get(Model, id)` (finding "API legada `Model.query.get()` (SQLAlchemy 2.x)")
- `datetime.utcnow()` em `models/task.py:15-16, 52`; `models/category.py:11`; `models/user.py:14`; `routes/task_routes.py:31, 72, 215, 285`; `routes/user_routes.py:172`; `routes/report_routes.py:35, 42, 45, 71, 133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66-67, 69-70, 74` → `datetime.now(timezone.utc)` (finding "`datetime.utcnow()` deprecated (Python 3.12+)")

Também verificado, sem ocorrências: `@app.before_first_request`, `flask.escape`/`flask.Markup`/`app.json_encoder`, `engine.execute`, `safe_str_cmp`, `distutils`/`imp`/`cgi`/`pkg_resources`, `logging.warn`.

---

**Total: 18 findings**

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
