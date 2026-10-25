# Validation After Refactoring
Command: python app.py (precedido de python seed.py), com ADMIN_TOKEN=refactor-arch-validation, DEBUG=false, PYTHONWARNINGS=default | Port: 5000 | Date: 2026-10-24
Boot: OK (sem erros no log; `server-after.log`)

Comparação: status + formato (chaves de nível superior). Além disso, o JSON completo foi comparado depois de normalizar datas, `password`, `token` e `generated_at`. A coluna "Deep" mostra o resultado: os 17 GETs sobre o seed (passos 01-17) deram **igual**, inclusive `/tasks`, `/tasks/stats`, `/reports/summary` e `/categories`, depois de trocar os loops com N+1 por GROUP BY/selectinload.

| Step | Method | Path | Variant | Before | After | Deep | Result | Note |
|---|---|---|---|---|---|---|---|---|
| 01 | GET | /health | — | 200 | 200 | igual | OK | — |
| 02 | GET | / | — | 200 | 200 | igual | OK | — |
| 03 | GET | /tasks | — | 200 | 200 | igual | OK | — |
| 04 | GET | /tasks/1 | — | 200 | 200 | igual | OK | — |
| 05 | GET | /tasks/9999 | id inexistente | 404 | 404 | igual | OK | — |
| 06 | GET | /tasks/search?q=API | busca por texto | 200 | 200 | igual | OK | — |
| 07 | GET | /tasks/search?status=pending&priority=1 | filtros | 200 | 200 | igual | OK | — |
| 08 | GET | /tasks/search?priority=abc | priority inválida | 500 | 400 | n/a | CHANGED | 500 por entrada inválida virou 400 JSON (AP-14/AP-15) |
| 09 | GET | /tasks/stats | — | 200 | 200 | igual | OK | — |
| 10 | GET | /users | — | 200 | 200 | igual | OK | — |
| 11 | GET | /users/1 | — | 200 | 200 | igual | CHANGED | campo `password` removido da resposta (AP-04) |
| 12 | GET | /users/9999 | id inexistente | 404 | 404 | igual | OK | — |
| 13 | GET | /users/1/tasks | — | 200 | 200 | igual | OK | — |
| 14 | GET | /reports/summary | — | 200 | 200 | igual | OK | — |
| 15 | GET | /reports/user/1 | — | 200 | 200 | igual | OK | — |
| 16 | GET | /reports/user/9999 | id inexistente | 404 | 404 | igual | OK | — |
| 17 | GET | /categories | — | 200 | 200 | igual | OK | — |
| 18 | GET | /rota-inexistente | rota inexistente | 404 | 404 | n/a | CHANGED | 404 agora com corpo JSON padronizado (AP-14) |
| 19 | POST | /login | joao (admin) | 200 | 200 | igual | OK | — |
| 20 | POST | /login | maria (A, user) | 200 | 200 | igual | OK | — |
| 21 | POST | /login | pedro (B, manager) | 200 | 200 | igual | OK | — |
| 22 | POST | /login | senha errada | 401 | 401 | igual | OK | — |
| 23 | POST | /login | corpo sem campos | 400 | 400 | igual | OK | — |
| 24 | POST | /users | cadastro público (sem role) | 201 | 201 | igual | CHANGED | campo `password` removido da resposta (AP-04) |
| 25 | POST | /users | email inválido | 400 | 400 | igual | OK | — |
| 26 | POST | /users | email duplicado | 409 | 409 | igual | OK | — |
| 27 | POST | /users | role=admin anônimo | 201 | 401 | DIFERENTE | CHANGED | role privilegiado no cadastro, anônimo → 401 (AP-06) |
| 28 | POST | /users | role=admin com token_B | 201 | 403 | DIFERENTE | CHANGED | role privilegiado no cadastro, usuário não admin → 403 (AP-06) |
| 29 | POST | /users | role=manager com X-Admin-Token | 201 | 201 | DIFERENTE | CHANGED | admin via X-Admin-Token cria com role privilegiado; `password` removido (AP-04) |
| 30 | POST | /login | login do usuário criado (U) | 200 | 200 | igual | OK | — |
| 31 | PUT | /users/4 | anônimo | 200 | 401 | DIFERENTE | CHANGED | rota de escrita exige token de sessão válido → 401 (AP-06, RF-16) |
| 32 | PUT | /users/4 | token adulterado | 200 | 401 | DIFERENTE | CHANGED | token adulterado → 401 (AP-06, RF-16) |
| 33 | PUT | /users/4 | token_B (outro usuário) | 200 | 403 | DIFERENTE | CHANGED | autenticado sem ser dono/admin → 403 (AP-06, RF-16) |
| 34 | PUT | /users/4 | dono altera role | 200 | 403 | DIFERENTE | CHANGED | dono não altera campo privilegiado `role` → 403 (AP-06) |
| 35 | PUT | /users/4 | dono altera active | 200 | 403 | DIFERENTE | CHANGED | dono não altera campo privilegiado `active` → 403 (AP-06) |
| 36 | PUT | /users/4 | dono altera name | 200 | 200 | DIFERENTE | CHANGED | `password` removido; role/active seguem os originais porque 34/35 foram barrados |
| 37 | PUT | /users/4 | email inválido (dono) | 400 | 400 | igual | OK | — |
| 38 | PUT | /users/4 | email duplicado (dono) | 409 | 409 | igual | OK | — |
| 39 | PUT | /users/9999 | id inexistente (admin) | 404 | 404 | igual | OK | — |
| 40 | PUT | /users/4 | admin (token joao) altera role | 200 | 200 | DIFERENTE | CHANGED | `password` removido (AP-04); `active` continua true porque 35 foi barrado |
| 41 | GET | /users/4 | leitura após updates | 200 | 200 | DIFERENTE | CHANGED | `password` removido (AP-04); `active` continua true porque 35 foi barrado |
| 42 | POST | /tasks | token_A cria p/ si (user_id=2) | 201 | 201 | igual | OK | — |
| 43 | POST | /tasks | sem título | 400 | 400 | igual | OK | — |
| 44 | POST | /tasks | priority string | 500 | 400 | n/a | CHANGED | 500 por `priority` string virou 400 JSON (AP-15) |
| 45 | POST | /tasks | anônimo | 201 | 401 | DIFERENTE | CHANGED | rota de escrita exige token de sessão válido → 401 (AP-06, RF-16) |
| 46 | POST | /tasks | token_B cria com user_id=A | 201 | 403 | DIFERENTE | CHANGED | criar task com `user_id` de outro usuário → 403 (AP-06, RF-16) |
| 47 | POST | /tasks | admin cria com user_id=A | 201 | 201 | DIFERENTE | OK | mesmo formato; só o id muda (passos 45/46 barrados) |
| 48 | PUT | /tasks/11 | anônimo | 200 | 401 | DIFERENTE | CHANGED | rota de escrita exige token de sessão válido → 401 (AP-06, RF-16) |
| 49 | PUT | /tasks/11 | token adulterado | 200 | 401 | DIFERENTE | CHANGED | token adulterado → 401 (AP-06, RF-16) |
| 50 | PUT | /tasks/11 | token_B (outro usuário) | 200 | 403 | DIFERENTE | CHANGED | autenticado sem ser dono/admin → 403 (AP-06, RF-16) |
| 51 | PUT | /tasks/11 | dono transfere p/ B | 200 | 403 | DIFERENTE | CHANGED | dono transferir a task para outro usuário → 403 (AP-06, RF-16) |
| 52 | PUT | /tasks/11 | dono atualiza | 200 | 200 | DIFERENTE | OK | mesmo formato; `user_id` continua 2 porque a transferência do passo 51 foi barrada |
| 53 | PUT | /tasks/11 | status inválido (dono) | 400 | 400 | igual | OK | — |
| 54 | PUT | /tasks/9999 | id inexistente (dono A) | 404 | 404 | igual | OK | — |
| 55 | PUT | /tasks/12 | admin transfere p/ B | 200 | 200 | DIFERENTE | OK | mesmo formato; só o id muda |
| 56 | GET | /tasks/11 | leitura após updates | 200 | 200 | DIFERENTE | OK | mesmo formato; `user_id` continua 2 (passo 51 barrado) |
| 57 | GET | /users/2/tasks | tasks da Maria | 200 | 200 | DIFERENTE | CHANGED | 4 tasks em vez de 5: as criações/transferência dos passos 45, 46 e 51 foram barradas |
| 58 | POST | /categories | anônimo | 201 | 401 | DIFERENTE | CHANGED | rota de escrita exige token de sessão válido → 401 (AP-06, RF-16) |
| 59 | POST | /categories | token_B (não admin) | 201 | 403 | DIFERENTE | CHANGED | rota administrativa, usuário não admin → 403 (AP-06, RF-05) |
| 60 | POST | /categories | X-Admin-Token | 201 | 201 | DIFERENTE | OK | mesmo formato; só o id muda (passo 58/59 barrados) |
| 61 | POST | /categories | sem nome (admin) | 400 | 400 | igual | OK | — |
| 62 | PUT | /categories/5 | anônimo | 200 | 401 | DIFERENTE | CHANGED | rota de escrita exige token de sessão válido → 401 (AP-06, RF-16) |
| 63 | PUT | /categories/5 | admin | 200 | 200 | DIFERENTE | OK | mesmo formato; só o id muda |
| 64 | PUT | /categories/5 | sem corpo (admin) | 400 | 400 | n/a | CHANGED | 400 continua 400, agora com corpo JSON `{"error": "Dados inválidos"}` (AP-14) |
| 65 | PUT | /categories/9999 | id inexistente (admin) | 404 | 404 | igual | OK | — |
| 66 | GET | /reports/summary | summary após escritas | 200 | 200 | DIFERENTE | OK | mesmo formato; contagens menores porque as escritas não autorizadas foram barradas |
| 67 | DELETE | /tasks/11 | anônimo | 200 | 401 | DIFERENTE | CHANGED | rota de escrita exige token de sessão válido → 401 (AP-06, RF-16) |
| 68 | DELETE | /tasks/11 | token adulterado | 404 | 401 | DIFERENTE | CHANGED | token adulterado → 401 (no original, 404 porque o passo 67 já tinha apagado a task) |
| 69 | DELETE | /tasks/11 | token_B (outro usuário) | 404 | 403 | DIFERENTE | CHANGED | outro usuário → 403 (no original, 404 porque o passo 67 já tinha apagado a task) |
| 70 | DELETE | /tasks/11 | dono (token_A) | 404 | 200 | DIFERENTE | CHANGED | dono exclui → 200 (no original, 404 porque o passo 67 anônimo já tinha apagado) |
| 71 | DELETE | /tasks/9999 | id inexistente (admin) | 404 | 404 | igual | OK | — |
| 72 | DELETE | /categories/5 | anônimo | 200 | 401 | DIFERENTE | CHANGED | rota de escrita exige token de sessão válido → 401 (AP-06, RF-16) |
| 73 | DELETE | /categories/5 | token_B (não admin) | 404 | 403 | DIFERENTE | CHANGED | usuário não admin → 403 (no original, 404 porque o passo 72 já tinha apagado) |
| 74 | DELETE | /categories/5 | admin | 404 | 200 | DIFERENTE | CHANGED | admin exclui → 200 (no original, 404 porque o passo 72 anônimo já tinha apagado) |
| 75 | DELETE | /categories/9999 | id inexistente (admin) | 404 | 404 | igual | OK | — |
| 76 | DELETE | /users/4 | anônimo | 200 | 401 | DIFERENTE | CHANGED | rota de escrita exige token de sessão válido → 401 (AP-06, RF-16) |
| 77 | DELETE | /users/4 | token adulterado | 404 | 401 | DIFERENTE | CHANGED | token adulterado → 401 (no original, 404 porque o passo 76 já tinha apagado) |
| 78 | DELETE | /users/4 | token_B (outro usuário) | 404 | 403 | DIFERENTE | CHANGED | outro usuário → 403 (no original, 404 porque o passo 76 já tinha apagado) |
| 79 | DELETE | /users/4 | dono (token_U) | 404 | 200 | DIFERENTE | CHANGED | dono exclui a própria conta → 200 (no original, 404 porque o passo 76 já tinha apagado) |
| 80 | DELETE | /users/9999 | id inexistente (admin) | 404 | 404 | igual | OK | — |

Summary: OK 42 | CHANGED 38 | REGRESSION 0
Warnings in server log: nenhum warning de depreciação (no original havia `DeprecationWarning` de `datetime.utcnow()` e `LegacyAPIWarning` de `Query.get()`). Só aparecem o aviso de `SECRET_KEY` não definida (esperado sem `.env`) e o aviso padrão do servidor de desenvolvimento do Werkzeug.

## Supplementary checks (só na versão refatorada)

| Check | Resultado |
|---|---|
| Senhas do seed no banco | `scrypt:32768:8:1$…` (162 caracteres), hashes diferentes entre si; logins dos 3 usuários do seed funcionam (passos 19-21) |
| Token de usuário desativado (admin faz PUT `active=false` em maria e depois maria usa o token antigo) | 401 `Autenticação necessária`; login dela → 403 `Usuário inativo` |
| `X-Admin-Token` errado em DELETE /categories/1 | 401 |
| Sem `ADMIN_TOKEN` configurado, qualquer `X-Admin-Token` | 401: o header não é aceito como credencial (rota fechada por padrão) |
| POST /tasks sem `Content-Type: application/json` | 400 `Dados inválidos` (antes: 415 HTML) |
| Resposta do /login | sem a chave `password` |
| POST /categories com `color` inválida | 400 `Cor inválida` |
| Admin faz DELETE /users/1 (dono de 4 tasks) | 200; 0 tasks do usuário 1 sobram (tudo numa única transação) |
