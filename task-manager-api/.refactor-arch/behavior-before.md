# Behavior Before Refactoring
Command: `python app.py` (após `python seed.py`) | Port: 5000 | Date: 2026-10-21

Banco: `instance/tasks.db` criado pelo seed (não havia banco antes; nada a restaurar).
Os headers de autenticação enviados nos passos são ignorados pela aplicação original; ficam iguais aos da medição "depois" para que os passos sejam os mesmos.

| Step | Method | Path | Request | Status | Shape | Note |
|---|---|---|---|---|---|---|
| 01 | GET | / | —; — | 200 | object: message, version | raiz |
| 02 | GET | /health | —; — | 200 | object: status, timestamp | health |
| 03 | GET | /tasks | —; — | 200 | list[10] of object: category_id, category_name, created_at, description, due_date, id, overdue, priority, status, tags, title, updated_at, user_id, user_name | lista de tasks (seed: 10) |
| 04 | GET | /tasks/1 | —; — | 200 | object: category_id, created_at, description, due_date, id, overdue, priority, status, tags, title, updated_at, user_id | task do seed |
| 05 | GET | /tasks/999 | —; — | 404 | object: error — error: Task não encontrada | erro esperado 404 |
| 06 | GET | /tasks/search?q=API | —; — | 200 | list[2] of object: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | busca por texto |
| 07 | GET | /tasks/search?status=pending&priority=1 | —; — | 200 | list[2] of object: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | busca por filtros |
| 08 | GET | /tasks/stats | —; — | 200 | object: cancelled, completion_rate, done, in_progress, overdue, pending, total | estatísticas |
| 09 | GET | /users | —; — | 200 | list[3] of object: active, created_at, email, id, name, role, task_count | lista de usuários |
| 10 | GET | /users/1 | —; — | 200 | object: active, created_at, email, id, name, password, role, tasks | usuário do seed |
| 11 | GET | /users/999 | —; — | 404 | object: error — error: Usuário não encontrado | erro esperado 404 |
| 12 | GET | /users/2/tasks | —; — | 200 | list[3] of object: created_at, description, due_date, id, overdue, priority, status, title | tasks do usuário 2 |
| 13 | GET | /reports/summary | —; — | 200 | object: generated_at, overdue, overview, recent_activity, tasks_by_priority, tasks_by_status, user_productivity | relatório geral |
| 14 | GET | /reports/user/1 | —; — | 200 | object: statistics, user | relatório por usuário |
| 15 | GET | /reports/user/999 | —; — | 404 | object: error — error: Usuário não encontrado | erro esperado 404 |
| 16 | GET | /categories | —; — | 200 | list[4] of object: color, created_at, description, id, name, task_count | lista de categorias |
| 17 | POST | /login | —; requests/17.json | 200 | object: message, token, user | login maria (usuário B) |
| 18 | POST | /login | —; requests/18.json | 401 | object: error — error: Credenciais inválidas | senha errada → 401 |
| 19 | POST | /login | —; requests/19.json | 400 | object: error — error: Email e senha são obrigatórios | sem senha → 400 |
| 20 | POST | /login | —; requests/20.json | 200 | object: message, token, user | login joao (admin) |
| 21 | POST | /users | —; requests/21.json | 201 | object: active, created_at, email, id, name, password, role | cadastro público (role padrão) = usuário C |
| 22 | POST | /users | —; requests/22.json | 409 | object: error — error: Email já cadastrado | e-mail duplicado → 409 |
| 23 | POST | /users | —; requests/23.json | 400 | object: error — error: Email inválido | e-mail inválido → 400 |
| 24 | POST | /users | X-Admin-Token; requests/24.json | 201 | object: active, created_at, email, id, name, password, role | role=manager (admin no after) |
| 25 | POST | /login | —; requests/25.json | 200 | object: message, token, user | login do usuário C |
| 26 | POST | /tasks | Bearer token_C (dono); requests/26.json | 201 | object: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | criar task do usuário C |
| 27 | POST | /tasks | Bearer token_C (dono); requests/27.json | 400 | object: error — error: Título muito curto | título curto → 400 |
| 28 | POST | /tasks | Bearer token_C (dono); requests/28.json | 500 | html (não-JSON) | priority string (entrada inválida) |
| 29 | POST | /tasks | X-Admin-Token; requests/29.json | 404 | object: error — error: Usuário não encontrado | user_id inexistente → 404 |
| 30 | PUT | /tasks/11 | Bearer token_C (dono); requests/30.json | 200 | object: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | dono atualiza status/título |
| 31 | PUT | /tasks/11 | Bearer token_C (dono); requests/31.json | 400 | object: error — error: Status inválido | status inválido → 400 |
| 32 | PUT | /tasks/999 | Bearer token_C (dono); requests/30.json | 404 | object: error — error: Task não encontrada | task inexistente → 404 |
| 33 | GET | /tasks/11 | —; — | 200 | object: category_id, created_at, description, due_date, id, overdue, priority, status, tags, title, updated_at, user_id | task atualizada |
| 34 | GET | /users/4/tasks | —; — | 200 | list[1] of object: created_at, description, due_date, id, overdue, priority, status, title | tasks do usuário C |
| 35 | PUT | /users/4 | Bearer token_C (dono); requests/35.json | 200 | object: active, created_at, email, id, name, password, role | dono altera nome |
| 36 | PUT | /users/4 | Bearer token_C (dono); requests/36.json | 400 | object: error — error: Email inválido | e-mail inválido → 400 |
| 37 | GET | /tasks/search?priority=x | —; — | 500 | html (não-JSON) | filtro inválido (entrada inválida) |
| 38 | POST | /categories | X-Admin-Token; requests/38.json | 201 | object: color, created_at, description, id, name | criar categoria |
| 39 | POST | /categories | X-Admin-Token; requests/39.json | 400 | object: error — error: Nome é obrigatório | sem nome → 400 |
| 40 | PUT | /categories/5 | Bearer token de usuário admin; requests/40.json | 200 | object: color, created_at, description, id, name | atualizar categoria (usuário admin no after) |
| 41 | PUT | /categories/5 | X-Admin-Token; requests/41.json | 500 | html (não-JSON) | corpo null (entrada inválida) |
| 42 | PUT | /categories/999 | X-Admin-Token; requests/40.json | 404 | object: error — error: Categoria não encontrada | categoria inexistente → 404 |
| 43 | DELETE | /categories/5 | X-Admin-Token; — | 200 | object: message | excluir categoria |
| 44 | DELETE | /tasks/11 | Bearer token_C (dono); — | 200 | object: message | dono exclui a task |
| 45 | DELETE | /tasks/999 | X-Admin-Token; — | 404 | object: error — error: Task não encontrada | task inexistente → 404 |
| 46 | PUT | /users/4 | X-Admin-Token; requests/46.json | 200 | object: active, created_at, email, id, name, password, role | admin desativa o usuário C |
| 47 | DELETE | /users/4 | X-Admin-Token; — | 200 | object: message | excluir usuário C |
| 48 | DELETE | /users/999 | X-Admin-Token; — | 404 | object: error — error: Usuário não encontrado | usuário inexistente → 404 |
| 49 | GET | /rota-inexistente | —; — | 404 | html (não-JSON) | rota inexistente → 404 |
| 50 | GET | /users/1 | —; — | 200 | object: active, created_at, email, id, name, password, role, tasks | usuário 1 após o roteiro (sem alterações) |
