# Validation After Refactoring
Command: python app.py (after python seed.py; env ADMIN_TOKEN=refactor-arch-validation DEBUG=false PYTHONWARNINGS=default) | Port: 5000 | Date: 2026-10-15
Boot: OK (sem erros no log)

Comparação de valores: além do status e da forma, os corpos JSON de todos os passos foram comparados com os da medição "antes" ignorando campos voláteis (created_at, updated_at, due_date, generated_at, timestamp, token, password) — idênticos em todos os passos exceto 27 e 39.

| Step | Method | Path | Before | After | Shape | Result | Note |
|---|---|---|---|---|---|---|---|
| 01 | GET | / | 200 | 200 | igual | OK | — |
| 02 | GET | /health | 200 | 200 | igual | OK | — |
| 03 | GET | /tasks | 200 | 200 | igual | OK | — |
| 04 | GET | /tasks/1 | 200 | 200 | igual | OK | — |
| 05 | GET | /tasks/9999 | 404 | 404 | igual | OK | — |
| 06 | GET | /tasks/search?q=API | 200 | 200 | igual | OK | — |
| 07 | GET | /tasks/search?status=pending&priority=1 | 200 | 200 | igual | OK | — |
| 08 | GET | /tasks/stats | 200 | 200 | igual | OK | — |
| 09 | GET | /users | 200 | 200 | igual | OK | — |
| 10 | GET | /users/1 | 200 | 200 | sem `password` | CHANGED | campo `password` removido (AP-04) |
| 11 | GET | /users/9999 | 404 | 404 | igual | OK | — |
| 12 | GET | /users/1/tasks | 200 | 200 | igual | OK | — |
| 13 | GET | /reports/summary | 200 | 200 | igual | OK | — |
| 14 | GET | /reports/user/1 | 200 | 200 | igual | OK | — |
| 15 | GET | /reports/user/9999 | 404 | 404 | igual | OK | — |
| 16 | GET | /categories | 200 | 200 | igual | OK | — |
| 17 | POST | /login | 200 | 200 | igual | CHANGED | `user` sem `password` (AP-04); token assinado em vez de `fake-jwt-token-<id>` (AP-06) |
| 18 | POST | /login | 401 | 401 | igual | OK | — |
| 19 | POST | /users | 201 | 201 | sem `password` | CHANGED | campo `password` removido (AP-04) |
| 20 | POST | /users | 400 | 400 | igual | OK | — |
| 21 | POST | /users | 409 | 409 | igual | OK | — |
| 22 | POST | /users | 201 | 403 / 201 com token | sem `password` | CHANGED | rota protegida por X-Admin-Token (AP-06); papel privilegiado exige token; `password` removido (AP-04) |
| 23 | POST | /categories | 201 | 201 | igual | OK | — |
| 24 | POST | /categories | 400 | 400 | igual | OK | — |
| 25 | POST | /tasks | 201 | 201 | igual | OK | — |
| 26 | POST | /tasks | 400 | 400 | igual | OK | — |
| 27 | POST | /tasks | 500 | 400 | non-JSON (html) → object: error | CHANGED | 500 HTML (TypeError) → 400 JSON `Prioridade deve ser entre 1 e 5` (AP-15) |
| 28 | POST | /tasks | 404 | 404 | igual | OK | — |
| 29 | PUT | /tasks/11 | 200 | 200 | igual | OK | — |
| 30 | PUT | /tasks/11 | 400 | 400 | igual | OK | — |
| 31 | PUT | /tasks/9999 | 404 | 404 | igual | OK | — |
| 32 | PUT | /users/4 | 200 | 200 | sem `password` | CHANGED | campo `password` removido (AP-04) |
| 33 | PUT | /users/4 | 400 | 400 | igual | OK | — |
| 34 | PUT | /users/4 | 200 | 403 / 200 com token | sem `password` | CHANGED | rota protegida por X-Admin-Token (AP-06); alterar role/active exige token; `password` removido (AP-04) |
| 35 | PUT | /categories/5 | 200 | 200 | igual | OK | — |
| 36 | PUT | /categories/9999 | 404 | 404 | igual | OK | — |
| 37 | GET | /tasks/11 | 200 | 200 | igual | OK | — |
| 38 | GET | /users/4/tasks | 200 | 200 | igual | OK | — |
| 39 | GET | /tasks/search?priority=abc | 500 | 400 | non-JSON (html) → object: error | CHANGED | 500 HTML (ValueError) → 400 JSON `Parâmetro priority inválido` (AP-15) |
| 40 | DELETE | /tasks/11 | 200 | 403 / 200 com token | igual | CHANGED | rota protegida por X-Admin-Token (AP-06) |
| 41 | DELETE | /tasks/9999 | 404 | 403 / 404 com token | igual | CHANGED | rota protegida por X-Admin-Token (AP-06) |
| 42 | DELETE | /categories/5 | 200 | 403 / 200 com token | igual | CHANGED | rota protegida por X-Admin-Token (AP-06) |
| 43 | DELETE | /categories/9999 | 404 | 403 / 404 com token | igual | CHANGED | rota protegida por X-Admin-Token (AP-06) |
| 44 | DELETE | /users/4 | 200 | 403 / 200 com token | igual | CHANGED | rota protegida por X-Admin-Token (AP-06) |
| 45 | DELETE | /users/9999 | 404 | 403 / 404 com token | igual | CHANGED | rota protegida por X-Admin-Token (AP-06) |
| 46 | DELETE | /users/5 | 200 | 403 / 200 com token | igual | CHANGED | rota protegida por X-Admin-Token (AP-06) |
| 47 | GET | /tasks/stats | 200 | 200 | igual | OK | — |

Summary: OK 32 | CHANGED 15 | REGRESSION 0
Warnings in server log: nenhum warning de depreciação (antes: 11× DeprecationWarning datetime.utcnow(), 14× LegacyAPIWarning Query.get()); apenas os avisos esperados de `SECRET_KEY` não definida e do servidor de desenvolvimento do Werkzeug.

Verificações extras: senhas do seed gravadas com hash `scrypt` (werkzeug); nenhuma resposta contém `password`; rota inexistente responde 404 em JSON; sem `CORS_ORIGINS` nenhum header `Access-Control-Allow-Origin` é enviado.
