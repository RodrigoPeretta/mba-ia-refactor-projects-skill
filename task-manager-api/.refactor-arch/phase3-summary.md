================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
task-manager-api/
├── app.py                      # composition root (create_app) + entry point
├── database.py                 # db = SQLAlchemy() (init_app no composition root)
├── seed.py                     # seed de desenvolvimento (grava hash forte)
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py             # variáveis de ambiente + constantes de domínio
├── models/
│   ├── task.py                 # to_dict, to_brief_dict, is_overdue, overdue_clause
│   ├── user.py                 # serialização sem senha, hash werkzeug
│   └── category.py
├── services/
│   ├── persistence.py          # commit com rollback e erro 500 padronizado
│   ├── task_service.py
│   ├── user_service.py
│   ├── category_service.py
│   ├── report_service.py       # relatórios com GROUP BY
│   └── notification_service.py # SMTP com config/transporte injetados
├── controllers/
│   ├── validators.py           # validação única por recurso
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   ├── report_controller.py
│   └── system_controller.py
├── routes/                     # só mapeamento URL → controller
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py
│   ├── report_routes.py
│   └── system_routes.py
├── middlewares/
│   ├── auth.py                 # token de sessão assinado, dono-ou-admin, X-Admin-Token
│   └── error_handler.py        # handler central com respostas JSON
└── utils/
    ├── errors.py               # AppError
    └── helpers.py              # utcnow, calculate_percentage
```

## Validation
  ✓ Application boots without errors (python app.py, porta 5000; seed com python seed.py)
  ✓ 22/22 original endpoints respond as expected (OK: 42, CHANGED: 38, REGRESSION: 0, em 80 passos)
  ✓ Config extracted to config/settings.py; no hardcoded secrets
  ✓ 19/19 findings addressed (1 listed as pending: NotificationService mantido, mas sem chamada em nenhuma rota)
  ✓ GETs sobre o seed (passos 01-17) com JSON idêntico ao original após normalizar datas
  ✓ Sem DeprecationWarning/LegacyAPIWarning no log (o original emitia os dois)
  ✓ Processos encerrados e porta 5000 livre; banco de validação removido (não havia banco antes)

## Recommendations Applied (CRITICAL/HIGH)
| Finding | Recommendation clause | Applied in | Validated by |
|---|---|---|---|
| AP-06 Token previsível / rotas abertas | Emitir token de sessão assinado no login | `middlewares/auth.py:20`; `controllers/user_controller.py:54` | 19-21 (login), 32/49/68/77 (token adulterado → 401) |
| AP-06 Token previsível / rotas abertas | Validar o token (401) e só dono/admin (403) em `PUT /users/<id>` | `routes/user_routes.py:11`; `controllers/user_controller.py:28` | 31 (401), 32 (401), 33 (403), 36 (dono 200), 40 (admin 200) |
| AP-06 Token previsível / rotas abertas | Mesma regra em `DELETE /users/<id>` | `routes/user_routes.py:12`; `controllers/user_controller.py:38` | 76 (401), 77 (401), 78 (403), 79 (dono 200) |
| AP-06 Token previsível / rotas abertas | Mesma regra em `POST /tasks` | `routes/task_routes.py:10` | 45 (401), 42 (dono 201) |
| AP-06 Token previsível / rotas abertas | Mesma regra em `PUT /tasks/<id>` | `routes/task_routes.py:11`; `controllers/task_controller.py:25` | 48 (401), 49 (401), 50 (403), 52 (dono 200) |
| AP-06 Token previsível / rotas abertas | Mesma regra em `DELETE /tasks/<id>` | `routes/task_routes.py:12`; `controllers/task_controller.py:35` | 67 (401), 68 (401), 69 (403), 70 (dono 200) |
| AP-06 Token previsível / rotas abertas | `user_id` na criação: só o próprio usuário ou admin (403) | `controllers/task_controller.py:18`; `middlewares/auth.py:81` | 46 (B cria p/ A → 403), 42 (A p/ si → 201), 47 (admin → 201) |
| AP-06 Token previsível / rotas abertas | `user_id` na alteração: só o próprio usuário ou admin (403) | `controllers/task_controller.py:25-28` | 51 (dono transfere p/ B → 403), 55 (admin transfere → 200) |
| AP-06 Token previsível / rotas abertas | `POST/PUT/DELETE /categories`: token válido (401) de admin (403) | `routes/category_routes.py:9-11`; `controllers/category_controller.py:13, 20, 28` | 58/62/72 (401), 59/73 (403), 60/63/74 (admin OK) |
| AP-06 Cadastro aceita `role` | `role` ≠ `user` no `POST /users`: anônimo 401, não admin 403 | `controllers/user_controller.py:20-21` | 27 (401), 28 (403), 29 (X-Admin-Token → 201), 24 (sem role → 201) |
| AP-06 Cadastro aceita `role` | `role`/`active` no `PUT /users/<id>` só para admin (403) | `controllers/user_controller.py:30-31` | 34 (403), 35 (403), 40 (admin altera role → 200) |
| AP-04 Hash exposto | Remover `password` da serialização pública | `models/user.py:19-28` | 11, 24, 29, 36, 40, 41 (sem `password`); check suplementar do /login |
| AP-03 MD5 sem salt | `generate_password_hash`/`check_password_hash` (werkzeug) | `models/user.py:31, 34`; `seed.py` (via `set_password`) | 19-21 (login do seed OK), 22 (senha errada 401), check suplementar (hash `scrypt`, únicos) |
| AP-02 Segredos hardcoded | `SECRET_KEY` por variável de ambiente, sem default literal | `config/settings.py:22-25` | busca por literais vazia; log de boot com aviso de chave temporária |
| AP-02 Segredos hardcoded | Credenciais SMTP por ambiente, documentadas em `.env.example` | `config/settings.py:35-38`; `app.py:32-33`; `.env.example` | busca por literais vazia; boot OK sem SMTP (integração desativada) |
| AP-07 Fat routes | Rotas só com mapeamento; orquestração em controllers | `routes/*.py`; `controllers/*.py` | 01-80 (mesmo status/formato ou CHANGED intencional) |
| AP-07 Fat routes | Regra em services/models, usando `Task.is_overdue` | `models/task.py` (`is_overdue`, `overdue_clause`); `services/task_service.py`; `services/report_service.py` | 03, 04, 09, 13, 14, 15 (JSON idêntico, inclusive `overdue`) |
| AP-10 Debug/bind fixos | `DEBUG` (default false), host e porta por ambiente | `config/settings.py:27-29`; `app.py:45` | `server-after.log`: "Debug mode: off", "Running on http://127.0.0.1:5000" |

## Contract Changes
- GET /users/<id>, POST /users, PUT /users/<id>, POST /login: campo `password` (hash) removido da resposta — motivo: AP-04
- POST /login: `token` passa a ser assinado (itsdangerous) e expira em `SESSION_TOKEN_MAX_AGE`; o campo continua com o mesmo nome — motivo: AP-06
- POST /tasks, PUT /tasks/<id>, DELETE /tasks/<id>: exigem `Authorization: Bearer <token>` (401); escrita só para o dono ou um admin (403); `user_id` de outro usuário → 403 — motivo: AP-06
- PUT /users/<id>, DELETE /users/<id>: exigem token (401) e só o dono ou um admin (403); `role`/`active` só para admin (403) — motivo: AP-06
- POST /users: `role` diferente de `user` exige admin (anônimo 401, não admin 403) — motivo: AP-06
- POST/PUT/DELETE /categories: exigem admin (usuário `admin` ou `X-Admin-Token`): anônimo 401, não admin 403 — motivo: AP-06
- GET /tasks/search: `priority`/`user_id` não numéricos → 400 `Parâmetro ... inválido` (antes 500) — motivo: AP-14/AP-15
- POST/PUT /tasks: `priority` não numérica → 400 `Prioridade inválida`; `title` não string → 400 `Título inválido`; `user_id`/`category_id`/`tags`/`description` de tipo errado → 400 (antes 500 ou gravação inválida) — motivo: AP-15
- PUT /tasks/<id>: mensagem de data inválida unificada com a do POST (`Formato de data inválido. Use YYYY-MM-DD`) — motivo: AP-13
- PUT /users/<id>: `name` vazio → 400 `Nome é obrigatório`; `active` não booleano → 400 — motivo: AP-15
- POST/PUT /categories: `color` fora de `#RRGGBB` → 400 `Cor inválida`; `name` vazio no PUT → 400; PUT sem corpo → 400 JSON `Dados inválidos` (antes 400 HTML) — motivo: AP-15/AP-14
- Todas as rotas: 404/405 e corpo não JSON passam a responder JSON `{"error": ...}` (antes HTML do Werkzeug; 415 vira 400 `Dados inválidos`) — motivo: AP-14
- Servidor: bind padrão em 127.0.0.1 e debug desligado (antes 0.0.0.0 com debug); CORS sem origens por padrão (`CORS_ORIGINS`) — motivo: AP-10/AP-16

## Dependencies Added
Nenhuma. `itsdangerous` (token) e `werkzeug.security` (hash) já vêm com o Flask. Foram removidas do `requirements.txt` `marshmallow` e `requests` (sem nenhum import). `python-dotenv`, que já estava declarado, passou a ser usado em `config/settings.py`.

## Pending
- `NotificationService` (parte do AP-19): agora recebe configuração e transporte por injeção e é criado no composition root, mas nenhuma rota o chama, como já era no original. Ligar a notificação (ex.: ao atribuir uma task) muda o comportamento e é decisão de produto.
- Senhas MD5 já gravadas em bancos existentes não validam mais (`check_password_hash` → falso). Migração/rehash de dados está fora do escopo: rode `python seed.py` de novo ou redefina as senhas.
- Política de senha: o mínimo de 4 caracteres foi mantido porque os usuários do seed usam senhas de 4. Recomenda-se aumentar o mínimo e trocar as senhas de exemplo.
- Fora do escopo das guidelines: refresh/revogação de token e rate limiting no `/login`.
- Observado fora do relatório: `DELETE /categories/<id>` deixa tasks com `category_id` apontando para a categoria apagada (comportamento original mantido). Recomenda-se desvincular (`NULL`) na mesma transação.
- Leituras (`GET /users`, `GET /reports/user/<id>`) continuam públicas e expõem e-mails, como no contrato original; o relatório não pedia proteção. Avalie exigir token.

Evidence: .refactor-arch/behavior-before.md, .refactor-arch/validation-after.md
================================
