# ARCHITECTURE AUDIT REPORT

- **Project:** task-manager-api
- **Stack:** Python + Flask 3.0.0
- **Files:** 15 analyzed | ~1158 lines of code
- **Architecture:** Parcialmente em camadas

## Summary

CRITICAL: 5 | HIGH: 2 | MEDIUM: 9 | LOW: 3

## Findings

### [CRITICAL] Token previsível nunca validado e rotas de escrita abertas a qualquer cliente
- **ID:** AP-06
- **File:** `routes/user_routes.py:92-132, 134-151, 207-211`; `routes/task_routes.py:85, 156-223, 225-238`; `routes/report_routes.py:167-223`
- **Description:** O login devolve `'token': 'fake-jwt-token-' + str(user.id)` (`user_routes.py:210`): prefixo fixo + id sequencial, sem assinatura. Nenhum ponto do código lê o header `Authorization` nem valida esse token (busca por `Authorization`, `Bearer`, `verify`, `loads` sem resultados). Com isso, `PUT /users/<id>` (inclusive `role` e `active`), `DELETE /users/<id>` (que apaga também as tasks do usuário), `POST /tasks`, `PUT /tasks/<id>`, `DELETE /tasks/<id>` e `POST|PUT|DELETE /categories` aceitam cliente anônimo.
- **Impact:** Qualquer pessoa na rede promove a própria conta a `admin`, desativa ou apaga qualquer usuário, altera e exclui tasks de terceiros e apaga categorias. O "token" pode ser forjado para qualquer id sem conhecer senha.
- **Recommendation:** Manter todas as rotas e emitir no login um token de sessão assinado com `SECRET_KEY` (vindo do ambiente) e com expiração. Nas rotas de escrita sobre usuários (`PUT /users/<id>`, `DELETE /users/<id>`) e sobre recursos com dono (`POST /tasks`, `PUT /tasks/<id>`, `DELETE /tasks/<id>`, dono = `task.user_id`): validar o token de sessão assinado (401 sem token válido) e permitir só ao dono ou a um admin (403); alterar `role`/`active` só por admin. Nas rotas administrativas de categorias (`POST /categories`, `PUT /categories/<id>`, `DELETE /categories/<id>`), exigir token de admin, fechado por padrão (RF-16, RF-05).

### [CRITICAL] Cadastro público aceita o papel (`role`) vindo do corpo
- **ID:** AP-06
- **File:** `routes/user_routes.py:52, 71-72, 78`
- **Description:** `POST /users` lê `role = data.get('role', 'user')` e grava qualquer valor da allowlist `['user', 'admin', 'manager']`, sem nenhuma verificação de quem está criando a conta.
- **Impact:** Escalada de privilégio sem autenticação: `POST /users` com `"role": "admin"` cria um administrador.
- **Recommendation:** Manter a rota e o campo; o cadastro anônimo só pode criar `role = 'user'`. Criar conta com `role` diferente de `user` exige token de admin válido (401 sem token, 403 se não for admin) (RF-16, RF-05).

### [CRITICAL] Hash da senha exposto nas respostas da API
- **ID:** AP-04
- **File:** `models/user.py:16-25`; `routes/user_routes.py:33, 85, 129, 209`
- **Description:** `User.to_dict()` inclui `'password': self.password` (`models/user.py:21`). O método é usado nas respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
- **Impact:** Qualquer cliente lê o hash MD5 de qualquer usuário via `GET /users/<id>` (rota anônima) e o quebra offline em segundos (ver finding de hash fraco).
- **Recommendation:** Remover `password` da serialização pública do model; se algum fluxo interno precisar do hash, usar um método separado que nunca é devolvido em resposta (RF-04).

### [CRITICAL] Senhas com MD5 sem salt e política mínima de 4 caracteres
- **ID:** AP-03
- **File:** `models/user.py:3, 27-32`; `routes/user_routes.py:64, 115`
- **Description:** `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara com `==`. MD5 sem salt é reversível por tabela/força bruta; a validação aceita senhas de 4 caracteres (`len(password) < 4`), e o seed usa `1234`, `abcd`, `pass`.
- **Impact:** Vazamento do banco (ou do hash exposto pela API) revela as senhas; senhas iguais geram hashes iguais; comparação com `==` não é de tempo constante.
- **Recommendation:** Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (PBKDF2/scrypt com salt, já disponível via Flask); senhas antigas em MD5 são re-hashadas no próximo login bem-sucedido ou pelo seed (RF-03).

### [CRITICAL] Segredos hardcoded no código
- **ID:** AP-02
- **File:** `app.py:13`; `services/notification_service.py:9-10`
- **Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` e as credenciais SMTP `self.email_user = 'taskmanager@gmail.com'` / `self.email_password = 'senha123'` estão literais no código versionado.
- **Impact:** Quem tem acesso ao repositório pode assinar sessões/tokens em nome da aplicação e usar a conta de e-mail; trocar o segredo exige novo deploy.
- **Recommendation:** Ler `SECRET_KEY` e as credenciais SMTP de variáveis de ambiente (módulo de config + `.env.example` sem valores reais); sem `SECRET_KEY` definida, gerar uma aleatória só para desenvolvimento e avisar no log (RF-02).

### [HIGH] Regra de negócio, validação e formatação dentro das rotas (fat routes)
- **ID:** AP-07
- **File:** `routes/task_routes.py:11-63, 85-154, 156-223, 273-299`; `routes/user_routes.py:42-90, 92-132, 185-211`; `routes/report_routes.py:12-101, 103-155, 157-223`
- **Description:** Os handlers fazem validação, regra de domínio (atraso, taxa de conclusão, contagem por status/prioridade, unicidade de e-mail, transição de status), persistência e montagem da resposta no mesmo corpo — `summary_report` tem 89 linhas, `create_task` 69. A regra de atraso já existe em `Task.is_overdue()` (`models/task.py:50-60`) e é reimplementada nas rotas. Além disso, o CRUD de categorias (`report_routes.py:157-223`) está dentro do blueprint de relatórios, misturando dois domínios no mesmo módulo. Não há camada de controllers nem de services de domínio.
- **Impact:** Regras não testáveis sem HTTP, cópias que divergem, e qualquer mudança de regra exige mexer em várias rotas.
- **Recommendation:** Criar `services/` por domínio (tasks, users, categories, reports) com as regras e consultas, `controllers/` que leem a requisição e chamam o serviço, e rotas finas que só registram URL → controller; mover categorias para módulos próprios mantendo as URLs (RF-07).

### [HIGH] Debug ligado e bind em todas as interfaces fixos no código
- **ID:** AP-10
- **File:** `app.py:33-34`
- **Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger interativo do Werkzeug e o reloader em qualquer execução de `python app.py`, escutando em todas as interfaces.
- **Impact:** O debugger expõe stack traces e um console Python remoto na rede; o reloader cria processo filho que segura a porta.
- **Recommendation:** Ler `DEBUG` (padrão `false`), `HOST` (padrão `127.0.0.1`) e `PORT` (padrão `5000`) do ambiente pelo módulo de config (RF-02).

### [MEDIUM] N+1 queries e agregações em loop
- **ID:** AP-12
- **File:** `routes/task_routes.py:14, 41-57, 275-287`; `routes/user_routes.py:12, 22`; `routes/report_routes.py:15-30, 46-51, 53-68, 159-164`
- **Description:** `GET /tasks` faz `User.query.get` e `Category.query.get` para cada task; `GET /users` acessa o relacionamento lazy `len(u.tasks)` por usuário; o resumo faz uma query de tasks por usuário e 12 `COUNT` separados sobre `tasks`, além de `Task.query.all()` para contar atrasadas em memória; `GET /categories` faz um `COUNT` por categoria; `/tasks/stats` repete 5 `COUNT` + `all()`.
- **Impact:** O número de queries cresce linearmente com o volume (1 + 2N em `GET /tasks`), degradando a latência com a base real.
- **Recommendation:** Usar `GROUP BY` (`func.count` agrupado por status, prioridade, `user_id`, `category_id`), carregar relacionamentos com `joinedload`/`selectinload` e filtrar atrasadas no SQL (RF-10).

### [MEDIUM] Lógica duplicada e cópias que já divergiram
- **ID:** AP-13
- **File:** `routes/task_routes.py:17-28, 30-39, 71-80, 92-144, 166-213, 283-287`; `routes/user_routes.py:61, 106, 162-180`; `routes/report_routes.py:33-43, 132-135`; `models/task.py:38-60`; `utils/helpers.py:19-23, 57-116`
- **Description:** A regra de atraso aparece em 6 lugares das rotas, enquanto `Task.is_overdue()` não é usado; `GET /tasks` remonta à mão o mesmo dict de `Task.to_dict()`; a validação de task existe em `create_task`, em `update_task` e em `utils.helpers.process_task_data` (não usada); `Task.validate_status/validate_priority`, `validate_email`, `VALID_STATUSES`, `VALID_ROLES` e `MIN_PASSWORD_LENGTH` existem e não são usados, enquanto as rotas repetem os literais. As cópias divergem: `process_task_data` aceita `dd/mm/aaaa` e faz `strip()` do título; as rotas não; o update não valida o tipo de `priority`.
- **Impact:** Correções feitas em uma cópia não chegam às outras; o mesmo campo é aceito numa rota e recusado em outra.
- **Recommendation:** Uma única fonte por regra: `Task.is_overdue()` e `to_dict()` no model, validadores únicos compartilhados entre criação e atualização, usando as constantes centrais (RF-07, RF-12).

### [MEDIUM] Tratamento de erro genérico e sem handler central
- **ID:** AP-14
- **File:** `routes/task_routes.py:62, 137, 204, 236`; `routes/user_routes.py:130, 149`; `routes/report_routes.py:186, 207, 221`; `utils/helpers.py:46, 49, 88`; `app.py:9-34`
- **Description:** 12 blocos `except:` sem tipo, o mesmo `try/commit/rollback/500` copiado em cada handler, e nenhum `@app.errorhandler`. Erros de cliente viram 500 com página HTML: `POST /tasks` com `"priority": "a"` (`'a' < 1` → `TypeError`), `GET /tasks/search?priority=x` (`int('x')` → `ValueError`), `PUT /categories/<id>` sem corpo (`'name' in None`). Rotas inexistentes devolvem 404 em HTML, enquanto o resto da API responde JSON.
- **Impact:** Respostas de erro inconsistentes, exceções silenciadas (inclusive `KeyboardInterrupt`/`SystemExit` em `except:`), e falhas de entrada aparecem como erro do servidor.
- **Recommendation:** Exceções de domínio (`ValidationError` → 400, `NotFoundError` → 404, `ConflictError` → 409, `AuthError` → 401/403) e error handler central que devolve sempre `{"error": ...}` em JSON, inclusive para 404/405/500 do framework (RF-11).

### [MEDIUM] Validação de entrada ausente ou inconsistente
- **ID:** AP-15
- **File:** `routes/task_routes.py:113, 116-124, 166-171, 182, 260-264`; `routes/user_routes.py:102-103, 124-125`; `routes/report_routes.py:173-180, 196-202`
- **Description:** `priority` é comparada sem checar tipo (create e update); `title` no update não verifica tipo nem vazio; `user_id`/`category_id` não têm tipo validado; filtros `priority`/`user_id` da busca usam `int()` sem tratamento; `PUT /users` aceita `name` vazio e `active` não booleano; `PUT /categories` não checa corpo nulo nem `name` vazio; `color` nunca é validada (`is_valid_color` existe em `utils/helpers.py:52-55`).
- **Impact:** Dados inválidos gravados no banco e 500 em vez de 400 para erros do cliente.
- **Recommendation:** Validadores por recurso (criação e atualização com as mesmas regras), checando corpo JSON, tipos, faixas e formatos antes de chamar o serviço, com respostas 400 nas mensagens atuais (RF-12).

### [MEDIUM] Configuração fixa no código e CORS aberto
- **ID:** AP-16
- **File:** `app.py:11, 15, 34`; `services/notification_service.py:7-8`
- **Description:** URI do banco `'sqlite:///tasks.db'`, host/porta do servidor e host/porta SMTP literais; `CORS(app)` sem `origins` libera qualquer origem para todas as rotas.
- **Impact:** Não é possível trocar banco, porta ou origens permitidas por ambiente sem editar código; qualquer site pode chamar a API pelo navegador do usuário.
- **Recommendation:** Módulo de config lendo `DATABASE_URL`, `HOST`, `PORT`, `CORS_ORIGINS`, `SMTP_*` do ambiente (com `python-dotenv`, já declarado), defaults iguais aos atuais e `.env.example` (RF-02).

### [MEDIUM] `datetime.utcnow()` deprecated (Python 3.12+)
- **ID:** AP-17
- **File:** `models/task.py:15, 16, 52`; `models/user.py:14`; `models/category.py:11`; `routes/task_routes.py:31, 72, 215, 285`; `routes/user_routes.py:172`; `routes/report_routes.py:35, 42, 45, 71, 133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66, 67, 69, 70, 74`
- **Description:** 22 usos de `datetime.utcnow`, inclusive como `default=`/`onupdate=` das colunas. A API é deprecated desde o Python 3.12 (o `.venv` usa 3.13.14) e emite `DeprecationWarning`; ainda não foi removida, por isso MEDIUM.
- **Impact:** Avisos em runtime e remoção futura; datetimes ingênuos misturados com UTC.
- **Recommendation:** Função única `utcnow()` baseada em `datetime.now(timezone.utc)` (sem tzinfo, para manter o formato de `str()` nas respostas e a comparação com as colunas atuais) e uso dela em models, serviços e seed (RF-13).

### [MEDIUM] `Model.query.get()` legado no SQLAlchemy 2.x
- **ID:** AP-17
- **File:** `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/user_routes.py:29, 94, 136, 155`; `routes/report_routes.py:105, 192, 213`
- **Description:** 16 chamadas `X.query.get(id)`. Com Flask-SQLAlchemy 3.1.1 e SQLAlchemy 2.1.4 instalado, `Query.get()` é API legada e emite `LegacyAPIWarning`.
- **Impact:** Avisos em runtime e remoção prevista em versões futuras do SQLAlchemy.
- **Recommendation:** Substituir por `db.session.get(Model, id)` dentro da camada de dados (RF-13).

### [MEDIUM] `print` como logging, registrando dado pessoal
- **ID:** AP-20
- **File:** `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147`; `services/notification_service.py:21, 24`; `utils/helpers.py:39, 41`
- **Description:** Eventos e erros registrados com `print`, sem `logging`. Severidade elevada de LOW para MEDIUM porque registra dado pessoal: `user_routes.py:83` imprime o nome do usuário, `notification_service.py:21` o e-mail do destinatário, e `user_routes.py:89` imprime `str(e)` de erros do banco, que pode incluir os parâmetros do INSERT (e-mail e hash da senha).
- **Impact:** Sem nível, formato nem destino configuráveis; dados pessoais vão para a saída padrão.
- **Recommendation:** `logging` configurado no composition root, loggers por módulo, mensagens com ids em vez de nomes/e-mails e sem `str(e)` de erros de banco (RF-14).

### [MEDIUM] Serviço instancia o cliente SMTP diretamente
- **ID:** AP-11
- **File:** `services/notification_service.py:4-25`
- **Description:** `NotificationService.send_email` cria `smtplib.SMTP(self.email_host, self.email_port)` e faz login dentro do método, com host e credenciais fixos no construtor, em vez de receber o transporte/config. Severidade reduzida de HIGH para MEDIUM: o serviço não é chamado por nenhuma rota (ver código morto), então hoje não há exposição externa, e a correção é isolada.
- **Impact:** Impossível testar ou trocar o transporte de e-mail sem rede real; config acoplada à classe.
- **Recommendation:** Receber a configuração SMTP (do módulo de config) e a fábrica de conexão por injeção no construtor (RF-08, RF-06).

### [LOW] Código morto, imports e dependências não usados
- **ID:** AP-19
- **File:** `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `models/task.py:3`; `utils/helpers.py:3-7, 9-55, 57-108`; `services/notification_service.py:4-48`; `models/user.py:34-38`; `requirements.txt:4-6`
- **Description:** Imports não usados: `os, sys, json` (app), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes), `json` (models/task), `os, json, sys, math, hashlib` (helpers). Funções nunca chamadas: todos os helpers de `utils/helpers.py`, `NotificationService` inteiro, `User.is_admin`. Dependências sem nenhum import: `marshmallow`, `requests`, `python-dotenv`.
- **Impact:** Ruído na leitura, falsa impressão de que existe validação/notificação, e dependências instaladas sem uso.
- **Recommendation:** Remover imports mortos; reaproveitar o que tem função na nova estrutura (constantes, `is_admin`, `is_overdue`, `python-dotenv` na config) e remover o resto, incluindo dependências sem uso (RF-14).

### [LOW] Magic numbers e listas de valores repetidas inline
- **ID:** AP-18
- **File:** `routes/task_routes.py:96-100, 103-104, 110, 113, 167-170, 177, 182`; `routes/user_routes.py:52, 64, 71, 115, 120`; `routes/report_routes.py:24-28, 45, 129, 180`
- **Description:** Status válidos, papéis válidos, limites de título (3/200), faixa de prioridade (1–5), tamanho mínimo de senha (4), "alta prioridade" (`<= 2`), janela de 7 dias e cor padrão `#000000` escritos inline e repetidos, embora `utils/helpers.py:110-116` defina constantes equivalentes.
- **Impact:** Mudar uma regra exige caçar literais em vários arquivos.
- **Recommendation:** Constantes de domínio num único módulo, usadas por models, validadores e serviços (RF-14).

### [LOW] Nomes crípticos e código verboso
- **ID:** AP-21
- **File:** `models/task.py:38-60`; `models/user.py:34-38`; `models/category.py:14-21`; `routes/report_routes.py:24-28, 190-202`; `routes/task_routes.py:141, 210`; `utils/helpers.py:21-23, 53-55, 103`
- **Description:** `if cond: return True else: return False` em vez de retornar a expressão; `if`s aninhados de 4 níveis em `is_overdue`; `type(x) == list` em vez de `isinstance`; variáveis `d`, `p`, `p1..p5`, `cat`.
- **Impact:** Leitura mais lenta e mais pontos para erro.
- **Recommendation:** Simplificar para expressões booleanas diretas, `isinstance`, e nomes descritivos nas variáveis internas, sem renomear campos do contrato HTTP (RF-14).

## Deprecated APIs

- `datetime.utcnow()` em `models/task.py:15, 16, 52`; `models/user.py:14`; `models/category.py:11`; `routes/task_routes.py:31, 72, 215, 285`; `routes/user_routes.py:172`; `routes/report_routes.py:35, 42, 45, 71, 133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66, 67, 69, 70, 74` → `datetime.now(timezone.utc)` (finding "`datetime.utcnow()` deprecated (Python 3.12+)")
- `Model.query.get(id)` em `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/user_routes.py:29, 94, 136, 155`; `routes/report_routes.py:105, 192, 213` → `db.session.get(Model, id)` (finding "`Model.query.get()` legado no SQLAlchemy 2.x")

Verificado também, sem ocorrências: `before_first_request`, `app.json_encoder`/`flask.escape`/`flask.Markup`, `safe_str_cmp`, `engine.execute`, `distutils`/`imp`/`cgi`/`pkg_resources`, `logging.warn`; dependências declaradas (`flask==3.0.0`, `flask-sqlalchemy==3.1.1`, `flask-cors==4.0.0`, `marshmallow==3.20.1`, `requests==2.31.0`, `python-dotenv==1.0.0`) sem pacote descontinuado.

---

**Total: 19 findings**

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
