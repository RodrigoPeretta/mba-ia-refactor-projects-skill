# Validation After Refactoring
Command: `python app.py` (após `python seed.py`; env de teste: `ADMIN_TOKEN=refactor-arch-validation DEBUG=false PYTHONWARNINGS=default`) | Port: 5000 | Date: 2026-10-21
Boot: OK (sem erros no log; único aviso: `SECRET_KEY` não definida → chave temporária, comportamento previsto)

Passos com sufixo de letra (ex.: `26a`) são as variantes de autenticação da Etapa 8 e só existem na medição "depois".
Usuário A = Carla (id 4, criada no passo 21, token_C); usuário B = Maria (id 2, token_B); admin = `X-Admin-Token` ou token do João (role `admin`).

| Step | Method | Path | Request | Before | After | Shape | Result | Note |
|---|---|---|---|---|---|---|---|---|
| 01 | GET | / | —; — | 200 | 200 | igual | OK | raiz |
| 02 | GET | /health | —; — | 200 | 200 | igual | OK | health |
| 03 | GET | /tasks | —; — | 200 | 200 | igual | OK | lista de tasks (seed: 10) |
| 04 | GET | /tasks/1 | —; — | 200 | 200 | igual | OK | task do seed |
| 05 | GET | /tasks/999 | —; — | 404 | 404 | igual | OK | erro esperado 404 |
| 06 | GET | /tasks/search?q=API | —; — | 200 | 200 | igual | OK | busca por texto |
| 07 | GET | /tasks/search?status=pending&priority=1 | —; — | 200 | 200 | igual | OK | busca por filtros |
| 08 | GET | /tasks/stats | —; — | 200 | 200 | igual | OK | estatísticas |
| 09 | GET | /users | —; — | 200 | 200 | igual | OK | lista de usuários |
| 10 | GET | /users/1 | —; — | 200 | 200 | object: active, created_at, email, id, name, password, role, tasks → object: active, created_at, email, id, name, role, tasks | CHANGED | campo `password` removido (AP-04) |
| 11 | GET | /users/999 | —; — | 404 | 404 | igual | OK | erro esperado 404 |
| 12 | GET | /users/2/tasks | —; — | 200 | 200 | igual | OK | tasks do usuário 2 |
| 13 | GET | /reports/summary | —; — | 200 | 200 | igual | OK | relatório geral |
| 14 | GET | /reports/user/1 | —; — | 200 | 200 | igual | OK | relatório por usuário |
| 15 | GET | /reports/user/999 | —; — | 404 | 404 | igual | OK | erro esperado 404 |
| 16 | GET | /categories | —; — | 200 | 200 | igual | OK | lista de categorias |
| 17 | POST | /login | —; requests/17.json | 200 | 200 | igual | CHANGED | `user` sem `password`; `token` agora assinado (AP-04, AP-06) |
| 18 | POST | /login | —; requests/18.json | 401 | 401 | igual | OK | senha errada → 401 |
| 19 | POST | /login | —; requests/19.json | 400 | 400 | igual | OK | sem senha → 400 |
| 20 | POST | /login | —; requests/20.json | 200 | 200 | igual | CHANGED | `user` sem `password`; `token` agora assinado (AP-04, AP-06) |
| 21 | POST | /users | —; requests/21.json | 201 | 201 | object: active, created_at, email, id, name, password, role → object: active, created_at, email, id, name, role | CHANGED | campo `password` removido (AP-04) |
| 22 | POST | /users | —; requests/22.json | 409 | 409 | igual | OK | e-mail duplicado → 409 |
| 23 | POST | /users | —; requests/23.json | 400 | 400 | igual | OK | e-mail inválido → 400 |
| 24a | POST | /users | —; requests/24a.json | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: role privilegiado sem token → 401 (AP-06) |
| 24b | POST | /users | Bearer token_B (outro usuário); requests/24b.json | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: role privilegiado com token de não-admin → 403 (AP-06) |
| 24 | POST | /users | X-Admin-Token; requests/24.json | 201 | 201 | object: active, created_at, email, id, name, password, role → object: active, created_at, email, id, name, role | CHANGED | campo `password` removido; role privilegiado exige admin (AP-04, AP-06) |
| 25 | POST | /login | —; requests/25.json | 200 | 200 | igual | CHANGED | `user` sem `password`; `token` agora assinado (AP-04, AP-06) |
| 26a | POST | /tasks | —; requests/26.json | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: criar task sem token → 401 (AP-06) |
| 26b | POST | /tasks | Bearer token_B (outro usuário); requests/26.json | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: criar task para C com token de B → 403 (AP-06) |
| 26 | POST | /tasks | Bearer token_C (dono); requests/26.json | 201 | 201 | igual | OK | criar task do usuário C |
| 27 | POST | /tasks | Bearer token_C (dono); requests/27.json | 400 | 400 | igual | OK | título curto → 400 |
| 28 | POST | /tasks | Bearer token_C (dono); requests/28.json | 500 | 400 | html (não-JSON) → object: error — error: Prioridade inválida | CHANGED | 500 HTML de entrada inválida virou 400 JSON (AP-14/AP-15) |
| 29 | POST | /tasks | X-Admin-Token; requests/29.json | 404 | 404 | igual | OK | user_id inexistente → 404 |
| 30a | PUT | /tasks/11 | —; requests/30.json | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: sem token → 401 (AP-06) |
| 30b | PUT | /tasks/11 | Bearer token_C adulterado; requests/30.json | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: token adulterado → 401 (AP-06) |
| 30c | PUT | /tasks/11 | Bearer token_B (outro usuário); requests/30.json | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: token de outro usuário → 403 (AP-06) |
| 30 | PUT | /tasks/11 | Bearer token_C (dono); requests/30.json | 200 | 200 | igual | OK | dono atualiza status/título |
| 30d | PUT | /tasks/11 | X-Admin-Token; requests/30d.json | — | 200 | object: category_id, created_at, description, due_date, id, priority, status, tags, title, updated_at, user_id | CHANGED | variante de autenticação: admin atualiza task de C (AP-06) |
| 31 | PUT | /tasks/11 | Bearer token_C (dono); requests/31.json | 400 | 400 | igual | OK | status inválido → 400 |
| 32 | PUT | /tasks/999 | Bearer token_C (dono); requests/30.json | 404 | 404 | igual | OK | task inexistente → 404 |
| 33 | GET | /tasks/11 | —; — | 200 | 200 | igual | OK | task atualizada |
| 34 | GET | /users/4/tasks | —; — | 200 | 200 | igual | OK | tasks do usuário C |
| 35a | PUT | /users/4 | —; requests/35.json | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: sem token → 401 (AP-06) |
| 35b | PUT | /users/4 | Bearer token_C adulterado; requests/35.json | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: token adulterado → 401 (AP-06) |
| 35c | PUT | /users/4 | Bearer token_B (outro usuário); requests/35.json | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: token de outro usuário → 403 (AP-06) |
| 35 | PUT | /users/4 | Bearer token_C (dono); requests/35.json | 200 | 200 | object: active, created_at, email, id, name, password, role → object: active, created_at, email, id, name, role | CHANGED | campo `password` removido; exige token do dono/admin (AP-04, AP-06) |
| 35d | PUT | /users/4 | Bearer token_C (dono); requests/35d.json | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: dono tenta virar admin → 403 (AP-06) |
| 35e | PUT | /users/4 | X-Admin-Token; requests/35e.json | — | 200 | object: active, created_at, email, id, name, role | CHANGED | variante de autenticação: admin altera role (AP-06) |
| 36 | PUT | /users/4 | Bearer token_C (dono); requests/36.json | 400 | 400 | igual | OK | e-mail inválido → 400 |
| 37 | GET | /tasks/search?priority=x | —; — | 500 | 400 | html (não-JSON) → object: error — error: Prioridade inválida | CHANGED | 500 HTML de entrada inválida virou 400 JSON (AP-14/AP-15) |
| 38a | POST | /categories | —; requests/38.json | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: sem token → 403 (AP-06) |
| 38b | POST | /categories | Bearer token_B (outro usuário); requests/38.json | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: usuário não-admin → 403 (AP-06) |
| 38 | POST | /categories | X-Admin-Token; requests/38.json | 201 | 201 | igual | OK | criar categoria |
| 39 | POST | /categories | X-Admin-Token; requests/39.json | 400 | 400 | igual | OK | sem nome → 400 |
| 40a | PUT | /categories/5 | —; requests/40.json | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: sem token → 403 (AP-06) |
| 40 | PUT | /categories/5 | Bearer token de usuário admin; requests/40.json | 200 | 200 | igual | OK | atualizar categoria (usuário admin no after) |
| 41 | PUT | /categories/5 | X-Admin-Token; requests/41.json | 500 | 400 | html (não-JSON) → object: error — error: Dados inválidos | CHANGED | 500 HTML de entrada inválida virou 400 JSON (AP-14/AP-15) |
| 42 | PUT | /categories/999 | X-Admin-Token; requests/40.json | 404 | 404 | igual | OK | categoria inexistente → 404 |
| 43a | DELETE | /categories/5 | —; — | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: sem token → 403 (AP-06) |
| 43 | DELETE | /categories/5 | X-Admin-Token; — | 200 | 200 | igual | OK | excluir categoria |
| 44a | DELETE | /tasks/11 | —; — | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: sem token → 401 (AP-06) |
| 44b | DELETE | /tasks/11 | Bearer token_B (outro usuário); — | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: token de outro usuário → 403 (AP-06) |
| 44 | DELETE | /tasks/11 | Bearer token_C (dono); — | 200 | 200 | igual | OK | dono exclui a task |
| 45 | DELETE | /tasks/999 | X-Admin-Token; — | 404 | 404 | igual | OK | task inexistente → 404 |
| 46a | DELETE | /users/4 | —; — | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: sem token → 401 (AP-06) |
| 46b | DELETE | /users/4 | Bearer token_C adulterado; — | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: token adulterado → 401 (AP-06) |
| 46c | DELETE | /users/4 | Bearer token_B (outro usuário); — | — | 403 | object: error — error: Acesso negado | CHANGED | variante de autenticação: token de outro usuário → 403 (AP-06) |
| 46 | PUT | /users/4 | X-Admin-Token; requests/46.json | 200 | 200 | object: active, created_at, email, id, name, password, role → object: active, created_at, email, id, name, role | CHANGED | campo `password` removido; `active` exige admin (AP-04, AP-06) |
| 46d | PUT | /users/4 | Bearer token_C (dono); requests/35.json | — | 401 | object: error — error: Autenticação necessária | CHANGED | variante de autenticação: token de usuário desativado → 401 (AP-06) |
| 47 | DELETE | /users/4 | X-Admin-Token; — | 200 | 200 | igual | OK | excluir usuário C |
| 48 | DELETE | /users/999 | X-Admin-Token; — | 404 | 404 | igual | OK | usuário inexistente → 404 |
| 49 | GET | /rota-inexistente | —; — | 404 | 404 | html (não-JSON) → object: error — error: Recurso não encontrado | CHANGED | 404 HTML virou 404 JSON padronizado (AP-14) |
| 50 | GET | /users/1 | —; — | 200 | 200 | object: active, created_at, email, id, name, password, role, tasks → object: active, created_at, email, id, name, role, tasks | CHANGED | campo `password` removido (AP-04) |

Summary: OK 37 | CHANGED 36 | REGRESSION 0
Warnings in server log: nenhum warning de depreciação (`datetime.utcnow`/`Query.get`, presentes em `server-before.log`, sumiram); apenas o aviso de `SECRET_KEY` temporária.

## Comparação de valores (leituras)

Corpos comparados campo a campo, ignorando campos voláteis (`created_at`, `updated_at`, `due_date`, `generated_at`, `timestamp`, `token`, `password`): passos 01, 03, 04, 06, 07, 08, 09, 10, 12, 13, 14, 16, 21, 26, 30, 35, 38, 40 e 50 são **idênticos**. Os passos 33 e 34 diferem só em `priority` (2 → 1), efeito da variante 30d (admin atualiza a task), que só existe nesta medição. Formato de datas inalterado (ex.: `"due_date": "2026-12-31 00:00:00"`).

## Verificações adicionais (test client, banco temporário fora do projeto)

| Verificação | Resultado |
|---|---|
| Queries em `GET /tasks` (10 tasks) | 1 (antes: 1 + 2N = 21) |
| Queries em `GET /users` / `GET /categories` / `GET /tasks/stats` / `GET /reports/summary` | 2 / 2 / 3 / 11, constantes com o volume |
| `DELETE /users/2` (admin) com 3 tasks | 200; tasks do usuário 0 e usuário removido na mesma transação |
| Mesma senha gera hashes diferentes | sim (scrypt com salt) |
| Login com hash MD5 legado no banco | 401 `Credenciais inválidas` (sem 500) |
| Token de sessão expirado (`SESSION_TOKEN_MAX_AGE=1`) | 401 `Autenticação necessária` |
