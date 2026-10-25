# Behavior Before Refactoring
Command: python app.py (precedido de python seed.py) | Port: 5000 | Date: 2026-10-24

Roteiro: `.refactor-arch/requests/*.json` (corpos). Tokens: login de joao (admin), maria (A), pedro (B) e do usuário criado (U).

| Step | Method | Path | Request | Status | Shape | Note |
|---|---|---|---|---|---|---|
| 01 | GET | /health | — | 200 | object: status,timestamp | — |
| 02 | GET | / | — | 200 | object: message,version | — |
| 03 | GET | /tasks | — | 200 | list[10]: category_id,category_name,created_at,description,due_date,id,overdue,priority,status,tags,title,updated_at,user_id,user_name | — |
| 04 | GET | /tasks/1 | — | 200 | object: category_id,created_at,description,due_date,id,overdue,priority,status,tags,title,updated_at,user_id | — |
| 05 | GET | /tasks/9999 | id inexistente | 404 | object: error [error=Task não encontrada] | — |
| 06 | GET | /tasks/search?q=API | busca por texto | 200 | list[2]: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 07 | GET | /tasks/search?status=pending&priority=1 | filtros | 200 | list[2]: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 08 | GET | /tasks/search?priority=abc | priority inválida | 500 | non-json:<!doctype html> <htm | — |
| 09 | GET | /tasks/stats | — | 200 | object: cancelled,completion_rate,done,in_progress,overdue,pending,total | — |
| 10 | GET | /users | — | 200 | list[3]: active,created_at,email,id,name,role,task_count | — |
| 11 | GET | /users/1 | — | 200 | object: active,created_at,email,id,name,password,role,tasks | — |
| 12 | GET | /users/9999 | id inexistente | 404 | object: error [error=Usuário não encontrado] | — |
| 13 | GET | /users/1/tasks | — | 200 | list[4]: created_at,description,due_date,id,overdue,priority,status,title | — |
| 14 | GET | /reports/summary | — | 200 | object: generated_at,overdue,overview,recent_activity,tasks_by_priority,tasks_by_status,user_productivity | — |
| 15 | GET | /reports/user/1 | — | 200 | object: statistics,user | — |
| 16 | GET | /reports/user/9999 | id inexistente | 404 | object: error [error=Usuário não encontrado] | — |
| 17 | GET | /categories | — | 200 | list[4]: color,created_at,description,id,name,task_count | — |
| 18 | GET | /rota-inexistente | rota inexistente | 404 | non-json:<!doctype html> <htm | — |
| 19 | POST | /login | joao (admin) | 200 | object: message,token,user | — |
| 20 | POST | /login | maria (A, user) | 200 | object: message,token,user | — |
| 21 | POST | /login | pedro (B, manager) | 200 | object: message,token,user | — |
| 22 | POST | /login | senha errada | 401 | object: error [error=Credenciais inválidas] | — |
| 23 | POST | /login | corpo sem campos | 400 | object: error [error=Dados inválidos] | — |
| 24 | POST | /users | cadastro público (sem role) | 201 | object: active,created_at,email,id,name,password,role | — |
| 25 | POST | /users | email inválido | 400 | object: error [error=Email inválido] | — |
| 26 | POST | /users | email duplicado | 409 | object: error [error=Email já cadastrado] | — |
| 27 | POST | /users | role=admin anônimo | 201 | object: active,created_at,email,id,name,password,role | — |
| 28 | POST | /users | role=admin com token_B | 201 | object: active,created_at,email,id,name,password,role | — |
| 29 | POST | /users | role=manager com X-Admin-Token | 201 | object: active,created_at,email,id,name,password,role | — |
| 30 | POST | /login | login do usuário criado (U) | 200 | object: message,token,user | — |
| 31 | PUT | /users/4 | anônimo | 200 | object: active,created_at,email,id,name,password,role | — |
| 32 | PUT | /users/4 | token adulterado | 200 | object: active,created_at,email,id,name,password,role | — |
| 33 | PUT | /users/4 | token_B (outro usuário) | 200 | object: active,created_at,email,id,name,password,role | — |
| 34 | PUT | /users/4 | dono altera role | 200 | object: active,created_at,email,id,name,password,role | — |
| 35 | PUT | /users/4 | dono altera active | 200 | object: active,created_at,email,id,name,password,role | — |
| 36 | PUT | /users/4 | dono altera name | 200 | object: active,created_at,email,id,name,password,role | — |
| 37 | PUT | /users/4 | email inválido (dono) | 400 | object: error [error=Email inválido] | — |
| 38 | PUT | /users/4 | email duplicado (dono) | 409 | object: error [error=Email já cadastrado] | — |
| 39 | PUT | /users/9999 | id inexistente (admin) | 404 | object: error [error=Usuário não encontrado] | — |
| 40 | PUT | /users/4 | admin (token joao) altera role | 200 | object: active,created_at,email,id,name,password,role | — |
| 41 | GET | /users/4 | leitura após updates | 200 | object: active,created_at,email,id,name,password,role,tasks | — |
| 42 | POST | /tasks | token_A cria p/ si (user_id=2) | 201 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 43 | POST | /tasks | sem título | 400 | object: error [error=Título é obrigatório] | — |
| 44 | POST | /tasks | priority string | 500 | non-json:<!doctype html> <htm | — |
| 45 | POST | /tasks | anônimo | 201 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 46 | POST | /tasks | token_B cria com user_id=A | 201 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 47 | POST | /tasks | admin cria com user_id=A | 201 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 48 | PUT | /tasks/11 | anônimo | 200 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 49 | PUT | /tasks/11 | token adulterado | 200 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 50 | PUT | /tasks/11 | token_B (outro usuário) | 200 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 51 | PUT | /tasks/11 | dono transfere p/ B | 200 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 52 | PUT | /tasks/11 | dono atualiza | 200 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 53 | PUT | /tasks/11 | status inválido (dono) | 400 | object: error [error=Status inválido] | — |
| 54 | PUT | /tasks/9999 | id inexistente (dono A) | 404 | object: error [error=Task não encontrada] | — |
| 55 | PUT | /tasks/14 | admin transfere p/ B | 200 | object: category_id,created_at,description,due_date,id,priority,status,tags,title,updated_at,user_id | — |
| 56 | GET | /tasks/11 | leitura após updates | 200 | object: category_id,created_at,description,due_date,id,overdue,priority,status,tags,title,updated_at,user_id | — |
| 57 | GET | /users/2/tasks | tasks da Maria | 200 | list[5]: created_at,description,due_date,id,overdue,priority,status,title | — |
| 58 | POST | /categories | anônimo | 201 | object: color,created_at,description,id,name | — |
| 59 | POST | /categories | token_B (não admin) | 201 | object: color,created_at,description,id,name | — |
| 60 | POST | /categories | X-Admin-Token | 201 | object: color,created_at,description,id,name | — |
| 61 | POST | /categories | sem nome (admin) | 400 | object: error [error=Nome é obrigatório] | — |
| 62 | PUT | /categories/7 | anônimo | 200 | object: color,created_at,description,id,name | — |
| 63 | PUT | /categories/7 | admin | 200 | object: color,created_at,description,id,name | — |
| 64 | PUT | /categories/7 | sem corpo (admin) | 400 | non-json:<!doctype html> <htm | — |
| 65 | PUT | /categories/9999 | id inexistente (admin) | 404 | object: error [error=Categoria não encontrada] | — |
| 66 | GET | /reports/summary | summary após escritas | 200 | object: generated_at,overdue,overview,recent_activity,tasks_by_priority,tasks_by_status,user_productivity | — |
| 67 | DELETE | /tasks/11 | anônimo | 200 | object: message | — |
| 68 | DELETE | /tasks/11 | token adulterado | 404 | object: error [error=Task não encontrada] | — |
| 69 | DELETE | /tasks/11 | token_B (outro usuário) | 404 | object: error [error=Task não encontrada] | — |
| 70 | DELETE | /tasks/11 | dono (token_A) | 404 | object: error [error=Task não encontrada] | — |
| 71 | DELETE | /tasks/9999 | id inexistente (admin) | 404 | object: error [error=Task não encontrada] | — |
| 72 | DELETE | /categories/7 | anônimo | 200 | object: message | — |
| 73 | DELETE | /categories/7 | token_B (não admin) | 404 | object: error [error=Categoria não encontrada] | — |
| 74 | DELETE | /categories/7 | admin | 404 | object: error [error=Categoria não encontrada] | — |
| 75 | DELETE | /categories/9999 | id inexistente (admin) | 404 | object: error [error=Categoria não encontrada] | — |
| 76 | DELETE | /users/4 | anônimo | 200 | object: message | — |
| 77 | DELETE | /users/4 | token adulterado | 404 | object: error [error=Usuário não encontrado] | — |
| 78 | DELETE | /users/4 | token_B (outro usuário) | 404 | object: error [error=Usuário não encontrado] | — |
| 79 | DELETE | /users/4 | dono (token_U) | 404 | object: error [error=Usuário não encontrado] | — |
| 80 | DELETE | /users/9999 | id inexistente (admin) | 404 | object: error [error=Usuário não encontrado] | — |
