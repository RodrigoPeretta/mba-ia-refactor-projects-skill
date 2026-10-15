# Behavior Before Refactoring
Command: python app.py (after python seed.py) | Port: 5000 | Date: 2026-10-15

| Step | Method | Path | Request | Status | Shape | Note |
|---|---|---|---|---|---|---|
| 01 | GET | / | — | 200 | object: message, version | — |
| 02 | GET | /health | — | 200 | object: status, timestamp | — |
| 03 | GET | /tasks | — | 200 | list[10]: category_id, category_name, created_at, description, due_date, id, overdue, priority, status, tags, title, updated_at, user_id, user_name | — |
| 04 | GET | /tasks/1 | — | 200 | object: category_id, created_at, description, due_date, id, overdue, priority, status, tags, title, updated_at, user_id | — |
| 05 | GET | /tasks/9999 | — | 404 | object: error | — |
| 06 | GET | /tasks/search?q=API | — | 200 | list[2]: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | — |
| 07 | GET | /tasks/search?status=pending&priority=1 | — | 200 | list[2]: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | — |
| 08 | GET | /tasks/stats | — | 200 | object: cancelled, completion_rate, done, in_progress, overdue, pending, total | — |
| 09 | GET | /users | — | 200 | list[3]: active, created_at, email, id, name, role, task_count | — |
| 10 | GET | /users/1 | — | 200 | object: active, created_at, email, id, name, password, role, tasks | resposta inclui hash `password` |
| 11 | GET | /users/9999 | — | 404 | object: error | — |
| 12 | GET | /users/1/tasks | — | 200 | list[4]: created_at, description, due_date, id, overdue, priority, status, title | — |
| 13 | GET | /reports/summary | — | 200 | object: generated_at, overdue, overview, recent_activity, tasks_by_priority, tasks_by_status, user_productivity | — |
| 14 | GET | /reports/user/1 | — | 200 | object: statistics, user | — |
| 15 | GET | /reports/user/9999 | — | 404 | object: error | — |
| 16 | GET | /categories | — | 200 | list[4]: color, created_at, description, id, name, task_count | — |
| 17 | POST | /login | requests/17.json | 200 | object: message, token, user | token previsível fake-jwt-token-1; inclui `password` |
| 18 | POST | /login | requests/18.json | 401 | object: error | — |
| 19 | POST | /users | requests/19.json | 201 | object: active, created_at, email, id, name, password, role | resposta inclui hash `password` |
| 20 | POST | /users | requests/20.json | 400 | object: error | — |
| 21 | POST | /users | requests/21.json | 409 | object: error | — |
| 22 | POST | /users | requests/22.json | 201 | object: active, created_at, email, id, name, password, role | cadastro público aceitou role=admin |
| 23 | POST | /categories | requests/23.json | 201 | object: color, created_at, description, id, name | — |
| 24 | POST | /categories | requests/24.json | 400 | object: error | — |
| 25 | POST | /tasks | requests/25.json | 201 | object: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | — |
| 26 | POST | /tasks | requests/26.json | 400 | object: error | — |
| 27 | POST | /tasks | requests/27.json | 500 | non-JSON (html) | erro não tratado (TypeError/ValueError) → página HTML do debugger |
| 28 | POST | /tasks | requests/28.json | 404 | object: error | — |
| 29 | PUT | /tasks/11 | requests/29.json | 200 | object: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | — |
| 30 | PUT | /tasks/11 | requests/30.json | 400 | object: error | — |
| 31 | PUT | /tasks/9999 | requests/31.json | 404 | object: error | — |
| 32 | PUT | /users/4 | requests/32.json | 200 | object: active, created_at, email, id, name, password, role | resposta inclui hash `password` |
| 33 | PUT | /users/4 | requests/33.json | 400 | object: error | — |
| 34 | PUT | /users/4 | requests/34.json | 200 | object: active, created_at, email, id, name, password, role | resposta inclui hash `password` |
| 35 | PUT | /categories/5 | requests/35.json | 200 | object: color, created_at, description, id, name | — |
| 36 | PUT | /categories/9999 | requests/36.json | 404 | object: error | — |
| 37 | GET | /tasks/11 | — | 200 | object: category_id, created_at, description, due_date, id, overdue, priority, status, tags, title, updated_at, user_id | — |
| 38 | GET | /users/4/tasks | — | 200 | list[1]: created_at, description, due_date, id, overdue, priority, status, title | — |
| 39 | GET | /tasks/search?priority=abc | — | 500 | non-JSON (html) | erro não tratado (TypeError/ValueError) → página HTML do debugger |
| 40 | DELETE | /tasks/11 | — | 200 | object: message | — |
| 41 | DELETE | /tasks/9999 | — | 404 | object: error | — |
| 42 | DELETE | /categories/5 | — | 200 | object: message | — |
| 43 | DELETE | /categories/9999 | — | 404 | object: error | — |
| 44 | DELETE | /users/4 | — | 200 | object: message | — |
| 45 | DELETE | /users/9999 | — | 404 | object: error | — |
| 46 | DELETE | /users/5 | — | 200 | object: message | — |
| 47 | GET | /tasks/stats | — | 200 | object: cancelled, completion_rate, done, in_progress, overdue, pending, total | — |

IDs criados pelo roteiro: user=4 admin=5 cat=5 task=11

Warnings in server log: DeprecationWarning datetime.utcnow() (11x); LegacyAPIWarning Query.get() (14x)
