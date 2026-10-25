# ARCHITECTURE AUDIT REPORT

- **Project:** task-manager-api
- **Stack:** Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLite)
- **Files:** 15 analyzed | ~1158 lines of code
- **Architecture:** Parcialmente em camadas

## Summary

CRITICAL: 5 | HIGH: 2 | MEDIUM: 9 | LOW: 3

## Findings

### [CRITICAL] Token previsível nunca validado e rotas de escrita abertas a qualquer cliente
- **ID:** AP-06
- **File:** `routes/user_routes.py:92-151, 207-211`; `routes/task_routes.py:85-154, 156-223, 225-238`; `routes/report_routes.py:167-223`
- **Description:** O `POST /login` devolve `'token': 'fake-jwt-token-' + str(user.id)` (`user_routes.py:210`) — prefixo fixo + id, trivialmente forjável — e nenhum ponto do código lê o header `Authorization` ou verifica esse token. Com isso, `PUT/DELETE /users/<id>`, `POST/PUT/DELETE /tasks` e `POST/PUT/DELETE /categories` aceitam cliente anônimo. Além disso, `POST /tasks` e `PUT /tasks/<id>` aceitam o campo de dono `user_id` do corpo (`task_routes.py:105, 186-191`) sem compará-lo com o usuário autenticado, permitindo criar ou transferir tasks para outro usuário. Explorável sem autenticação e afetando todos os registros.
- **Impact:** Qualquer cliente pode alterar ou excluir qualquer usuário (inclusive admins e suas tasks em cascata), apagar tasks e categorias e reatribuir tasks de terceiros.
- **Recommendation:** Manter as rotas e emitir um token de sessão assinado no login (RF-16). Nas rotas `PUT /users/<id>`, `DELETE /users/<id>`, `POST /tasks`, `PUT /tasks/<id>` e `DELETE /tasks/<id>`: validar o token de sessão assinado (401 sem token válido) e permitir só ao dono ou a um admin (403). Para o campo `user_id` das tasks: na criação e na alteração, só o próprio usuário ou um admin define o dono (403). Rotas administrativas `POST/PUT/DELETE /categories`: exigir token válido (401) de administrador (403) (RF-05).

### [CRITICAL] Cadastro público aceita o papel (`role`) vindo do corpo
- **ID:** AP-06
- **File:** `routes/user_routes.py:52, 71-78, 119-125`
- **Description:** `POST /users` é público e lê `role = data.get('role', 'user')` (linha 52), aceitando `admin` ou `manager` de um cliente anônimo (linhas 71-78). O `PUT /users/<id>` também aceita `role` e `active` do corpo (linhas 119-125) sem nenhuma checagem de permissão.
- **Impact:** Escalada de privilégio imediata: qualquer pessoa cria uma conta `admin` ou promove/reativa uma conta existente.
- **Recommendation:** Manter o campo no contrato, mas tratá-lo como privilegiado: no `POST /users`, `role` diferente de `user` exige token válido (401 para anônimo) de admin (403 para não-admin); no `PUT /users/<id>`, alterar `role` ou `active` só é permitido a admin (403) (RF-05, RF-16).

### [CRITICAL] Hash da senha exposto nas respostas da API
- **ID:** AP-04
- **File:** `models/user.py:16-25`; `routes/user_routes.py:33, 85, 129, 209`
- **Description:** `User.to_dict()` inclui `'password': self.password` (linha 21) e é usado em `GET /users/<id>` (linha 33), `POST /users` (85), `PUT /users/<id>` (129) e na resposta do `POST /login` (209). Como `GET /users/<id>` não exige autenticação, o hash de qualquer usuário é obtido anonimamente.
- **Impact:** Vazamento dos hashes (MD5 sem salt, ver finding abaixo), que são quebrados em segundos com tabelas prontas.
- **Recommendation:** Remover `password` da serialização pública do model (RF-04), mantendo os demais campos.

### [CRITICAL] Senhas com MD5 sem salt
- **ID:** AP-03
- **File:** `models/user.py:27-32`; `seed.py:19, 26, 33`
- **Description:** `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` (linha 29) e `check_password` compara com `==` (linha 32). O seed cria usuários com senhas `'1234'`, `'abcd'` e `'pass'` através desse mesmo hash. A política mínima é de 4 caracteres (`routes/user_routes.py:64, 115`).
- **Impact:** Hashes sem salt e rápidos permitem recuperação por força bruta/rainbow table; comparação com `==` não é em tempo constante.
- **Recommendation:** Usar `werkzeug.security.generate_password_hash` / `check_password_hash` (PBKDF2/scrypt com salt), já disponível como dependência do Flask (RF-03).

### [CRITICAL] Segredos hardcoded no código
- **ID:** AP-02
- **File:** `app.py:13`; `services/notification_service.py:9-10`
- **Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` (app.py:13) e credenciais SMTP literais `self.email_user = 'taskmanager@gmail.com'` / `self.email_password = 'senha123'` (notification_service.py:9-10).
- **Impact:** Quem tem acesso ao repositório pode assinar sessões/tokens e usar a conta de e-mail; trocar o segredo exige alterar código.
- **Recommendation:** Mover os segredos para variáveis de ambiente lidas por um módulo de config, sem default de produção, e documentá-las em `.env.example` (RF-02).

### [HIGH] Regra de negócio, validação e formatação dentro das rotas (fat routes)
- **ID:** AP-07
- **File:** `routes/task_routes.py:11-63, 85-154, 156-223, 273-299`; `routes/user_routes.py:42-90, 153-183`; `routes/report_routes.py:12-101, 103-155`
- **Description:** Os handlers fazem validação + regra + persistência + formatação no mesmo bloco: `create_task` tem 70 linhas, `update_task` 68, `summary_report` 90. A regra de atraso (`due_date < utcnow()` e status diferente de `done`/`cancelled`) é reimplementada nas rotas embora exista `Task.is_overdue()` (`models/task.py:50-60`); os cálculos de estatística e produtividade dos relatórios ficam inteiros nos handlers. Não existe camada de controllers nem de serviços de domínio (a pasta `services/` só tem o serviço de notificação).
- **Impact:** Regras impossíveis de testar sem HTTP, cópias que divergem e handlers difíceis de manter.
- **Recommendation:** Extrair a regra para services/models e deixar as rotas só com parse → controller → resposta (RF-07).

### [HIGH] Debug ligado e bind em todas as interfaces fixos no código
- **ID:** AP-10
- **File:** `app.py:34`
- **Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger interativo do Werkzeug e o reloader em toda execução e expõe a aplicação em todas as interfaces.
- **Impact:** O debugger permite execução de código remoto se alcançado pela rede; o reloader cria processos filhos.
- **Recommendation:** Ler `DEBUG` (default `false`), host e porta de variáveis de ambiente (RF-02).

### [MEDIUM] N+1 queries e agregações em loop
- **ID:** AP-12
- **File:** `routes/task_routes.py:41-57, 275-287`; `routes/user_routes.py:22`; `routes/report_routes.py:15-30, 53-68, 163`
- **Description:** `GET /tasks` executa `User.query.get` e `Category.query.get` para cada task (linhas 42, 51); `GET /users` acessa o relacionamento lazy `len(u.tasks)` por usuário; `/tasks/stats` faz 5 `COUNT` separados e carrega a tabela inteira para contar atrasadas; `/reports/summary` faz 14 consultas de contagem, carrega todas as tasks e uma query por usuário; `GET /categories` faz um `COUNT` por categoria.
- **Impact:** O número de consultas cresce linearmente com os dados.
- **Recommendation:** Usar `GROUP BY`/agregações e carregamento antecipado (joinedload/selectinload) (RF-10).

### [MEDIUM] Lógica duplicada e cópias que já divergiram
- **ID:** AP-13
- **File:** `routes/task_routes.py:17-39, 71-80, 110, 166-213, 283-287`; `routes/user_routes.py:61, 106, 162-180`; `routes/report_routes.py:33-37, 132-135`; `utils/helpers.py:19-23, 57-108`
- **Description:** O cálculo de atraso está copiado em 6 lugares em vez de usar `Task.is_overdue()`; o mapeamento task → dict de `GET /tasks` (linhas 17-28) repete `Task.to_dict()`; a regex de e-mail aparece duas vezes enquanto `helpers.validate_email` não é usado; `helpers.process_task_data` valida tasks e nunca é chamado. As cópias divergiram: o `POST /tasks` rejeita título vazio, o `PUT /tasks/<id>` faz `len(data['title'])` sem checar nulo; o `POST` mensagem "Formato de data inválido. Use YYYY-MM-DD", o `PUT` só "Formato de data inválido".
- **Impact:** Correções aplicadas em uma cópia não chegam às outras; comportamento inconsistente entre criar e atualizar.
- **Recommendation:** Centralizar a regra no model/serviço e uma única validação para criar/atualizar (RF-07, RF-12).

### [MEDIUM] Tratamento de erro genérico e sem handler central
- **ID:** AP-14
- **File:** `routes/task_routes.py:62-63, 137, 151-154, 204, 221-223, 236-238`; `routes/user_routes.py:87-90, 130-132, 149-151`; `routes/report_routes.py:186-188, 207-209, 221-223`; `utils/helpers.py:46, 49, 88`; `app.py:1-34`
- **Description:** 12 `except:` sem tipo e vários `except Exception as e` copiados em cada handler; não há `@app.errorhandler`. Erros de cliente viram 500: `PUT /categories/<id>` sem corpo faz `'name' in None` (TypeError); `priority` enviada como string em `POST /tasks` gera TypeError em `priority < 1`; `GET /tasks/search?priority=abc` gera ValueError em `int(priority)`. 404 de rotas inexistentes volta em HTML.
- **Impact:** Diagnóstico difícil, formatos de erro inconsistentes e falhas de validação reportadas como erro de servidor.
- **Recommendation:** Error handler centralizado com respostas JSON e exceções de domínio tipadas (RF-11).

### [MEDIUM] Validação de entrada ausente ou inconsistente
- **ID:** AP-15
- **File:** `routes/task_routes.py:113, 167-169, 182, 261, 264`; `routes/user_routes.py:102-103, 124-125`; `routes/report_routes.py:180, 196-202`
- **Description:** `priority` comparada sem checar tipo (linhas 113, 182); `title` nulo no `PUT` quebra `len()`; filtros numéricos da busca sem validação; `name` do usuário pode virar vazio no `PUT` e `active` aceita qualquer tipo; `PUT /categories/<id>` usa `request.get_json()` sem checar nulo, e `color` não é validada em criação nem atualização (o helper `is_valid_color` existe e não é usado).
- **Impact:** Dados inválidos gravados no banco e 500 em vez de 400.
- **Recommendation:** Validação explícita e única por recurso antes da regra de negócio, respondendo 400 (RF-12).

### [MEDIUM] Configuração fixa no código e CORS aberto
- **ID:** AP-16
- **File:** `app.py:11, 15, 34`; `services/notification_service.py:7-8`
- **Description:** URI do banco `'sqlite:///tasks.db'` literal (linha 11), `CORS(app)` sem `origins` (linha 15), porta/host fixos (linha 34) e host/porta SMTP literais.
- **Impact:** Impossível configurar por ambiente sem editar código; qualquer origem pode chamar a API pelo navegador.
- **Recommendation:** Módulo de config lendo variáveis de ambiente com defaults de desenvolvimento e `CORS_ORIGINS` configurável (RF-02).

### [MEDIUM] `datetime.utcnow()` deprecated (Python 3.12+)
- **ID:** AP-17
- **File:** `models/category.py:11`; `models/task.py:15-16, 52`; `models/user.py:14`; `routes/task_routes.py:31, 72, 215, 285`; `routes/user_routes.py:172`; `routes/report_routes.py:35, 42, 45, 71, 133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66-67, 69-70, 74`
- **Description:** `datetime.utcnow()` (inclusive como `default=` de colunas) é deprecated desde o Python 3.12; o ambiente do projeto usa Python 3.13 (`.venv`). Ainda não foi removido, por isso fica em MEDIUM.
- **Impact:** DeprecationWarning em execução e remoção futura; datetimes ingênuos.
- **Recommendation:** Usar um helper único baseado em `datetime.now(timezone.utc)`, preservando o formato serializado (RF-13).

### [MEDIUM] `Model.query.get()` legado no SQLAlchemy 2.x
- **ID:** AP-17
- **File:** `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/user_routes.py:29, 94, 136, 155`; `routes/report_routes.py:105, 192, 213`
- **Description:** 16 chamadas a `Query.get()`, marcado como legado no SQLAlchemy 2.0 (usado pelo Flask-SQLAlchemy 3.1.1) e emissor de `LegacyAPIWarning`.
- **Impact:** Avisos em execução e remoção futura.
- **Recommendation:** Substituir por `db.session.get(Model, id)` (RF-13).

### [MEDIUM] `print` como logging, registrando dado pessoal
- **ID:** AP-20
- **File:** `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147`; `services/notification_service.py:21, 24`; `utils/helpers.py:39-41`
- **Description:** Eventos e erros registrados com `print`, sem logger configurado. Sobe para MEDIUM porque registra dado pessoal: nome do usuário (`user_routes.py:83`) e e-mail do destinatário (`notification_service.py:21`).
- **Impact:** Sem nível, destino ou formato; dado pessoal em stdout.
- **Recommendation:** Usar `logging` com logger por módulo, sem dados pessoais (RF-14).

### [MEDIUM] Serviço instancia o cliente SMTP diretamente
- **ID:** AP-11
- **File:** `services/notification_service.py:4-25`
- **Description:** `NotificationService.send_email` cria `smtplib.SMTP(self.email_host, self.email_port)` dentro do método, com host e credenciais fixos. Severidade descida de HIGH para MEDIUM: o serviço não é usado por nenhuma rota (sem exposição externa) e a correção é trivial.
- **Impact:** Impossível testar ou trocar o transporte sem rede real.
- **Recommendation:** Receber a configuração (e o transporte) por injeção a partir do módulo de config (RF-08).

### [LOW] Código morto, imports e dependências não usados
- **ID:** AP-19
- **File:** `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `models/task.py:3, 38-48`; `models/user.py:34-38`; `utils/helpers.py:3-7, 9-108`; `services/notification_service.py:1-48`; `requirements.txt:4-6`
- **Description:** Imports sem uso (`os, sys, json` em app.py; `json, os, sys, time` em task_routes; `hashlib, json` em user_routes; `format_date, calculate_percentage, json` em report_routes; `json` em models/task; `os, json, sys, math, hashlib` em helpers); `Task.validate_status/validate_priority`, `User.is_admin`, todas as funções de `utils/helpers.py` e o `NotificationService` nunca são chamados; dependências `marshmallow`, `requests` e `python-dotenv` não são importadas em nenhum arquivo.
- **Impact:** Ruído, falsa impressão de que a validação/notificação existe e superfície de dependências maior.
- **Recommendation:** Remover imports mortos, reaproveitar ou remover helpers e manter só dependências usadas (RF-14).

### [LOW] Magic numbers e listas de valores repetidas inline
- **ID:** AP-18
- **File:** `routes/task_routes.py:96, 99, 110, 113, 167, 169, 177, 182`; `routes/user_routes.py:64, 71, 115, 120`; `routes/report_routes.py:45, 129`; `utils/helpers.py:110-116`
- **Description:** Lista de status, lista de papéis, limites de título (3/200), prioridade (1-5), senha mínima (4), janela de 7 dias e "alta prioridade" `<= 2` escritos inline e repetidos, enquanto as constantes `VALID_STATUSES`, `VALID_ROLES`, `MIN_TITLE_LENGTH` etc. existem em `utils/helpers.py` sem uso.
- **Impact:** Mudar uma regra exige caçar todas as cópias.
- **Recommendation:** Constantes de domínio nomeadas num único módulo (RF-14).

### [LOW] Nomes crípticos e código verboso
- **ID:** AP-21
- **File:** `models/category.py:14`; `models/task.py:39-48, 50-60`; `models/user.py:35-38`; `routes/task_routes.py:141, 210`; `routes/report_routes.py:24-28`; `utils/helpers.py:103`
- **Description:** Variáveis `d`, `p`, `p1..p5`; padrões `if x: return True else: return False`; `if` aninhados em `is_overdue`; `type(tags) == list` em vez de `isinstance`.
- **Impact:** Legibilidade reduzida.
- **Recommendation:** Nomes descritivos e expressões booleanas diretas, sem renomear campos do contrato HTTP (RF-14).

## Deprecated APIs

- `datetime.utcnow()` em `models/category.py:11`; `models/task.py:15-16, 52`; `models/user.py:14`; `routes/task_routes.py:31, 72, 215, 285`; `routes/user_routes.py:172`; `routes/report_routes.py:35, 42, 45, 71, 133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66-67, 69-70, 74` → `datetime.now(timezone.utc)` (finding "`datetime.utcnow()` deprecated (Python 3.12+)")
- `Model.query.get(id)` em `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/user_routes.py:29, 94, 136, 155`; `routes/report_routes.py:105, 192, 213` → `db.session.get(Model, id)` (finding "`Model.query.get()` legado no SQLAlchemy 2.x")

---

**Total: 19 findings**

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
