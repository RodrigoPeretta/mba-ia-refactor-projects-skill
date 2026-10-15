# Behavior Before Refactoring
Command: npm start (node src/app.js) | Port: 3000 | Date: 2026-10-15

Roteiro: `.refactor-arch/run-requests.sh` (corpos em `.refactor-arch/requests/`). Banco em memória, recriado e semeado a cada boot.

| Step | Method | Path | Request | Status | Shape | Note |
|---|---|---|---|---|---|---|
| 1 | GET | /api/admin/financial-report | — | 200 | json array: course, revenue, students[student, paid] | `[Docker(0, []), Clean Architecture(997, [Leonan 997])]` — curso sem matrícula vem primeiro |
| 2 | POST | /api/checkout | requests/02.json | 200 | json object: msg, enrollment_id | `{"msg":"Sucesso","enrollment_id":2}`; usuário novo id 2 |
| 3 | POST | /api/checkout | requests/03.json | 400 | text/html: "Pagamento recusado" | cartão iniciando em 5 |
| 4 | POST | /api/checkout | requests/04.json | 400 | text/html: "Bad Request" | faltam c_id e card |
| 5 | POST | /api/checkout | requests/05.json | 404 | text/html: "Curso não encontrado" | c_id 999 |
| 6 | POST | /api/checkout | requests/06.json | 200 | json object: msg, enrollment_id | usuário existente (gui@...), enrollment_id 3 |
| 7 | GET | /api/admin/financial-report | — | 200 | json array: course, revenue, students[student, paid] | `[Clean Architecture(1994, [Leonan 997, Guilherme 997]), Docker(497, [Guilherme 497])]` |
| 8 | DELETE | /api/users/2 | — | 200 | text/html: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." | matrículas/pagamentos do usuário 2 permanecem |
| 9 | GET | /api/admin/financial-report | — | 200 | json array: course, revenue, students[student, paid] | órfãos: `[Clean Architecture(1994, [Leonan, Unknown 997]), Docker(497, [Unknown 497])]` |
| 10 | DELETE | /api/users/abc | — | 200 | text/html: mesma mensagem do passo 8 | id não numérico aceito |
| 11 | POST | /api/checkout | requests/11.json | 200 | json object: msg, enrollment_id | usuário novo **sem `pwd`** criado com senha padrão "123456"; enrollment_id 4 |
| 12 | POST | /api/checkout | requests/12.json | 000 (sem resposta) | — | `card` numérico → `TypeError: cc.startsWith is not a function` (AppManager.js:46) **derruba o processo** |

## Server log (relevante)

```
Frankenstein LMS rodando na porta 3000...
Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef
[LOG] Salvando no cache: last_checkout_2
...
TypeError: cc.startsWith is not a function
```

Servidor encerrado (caiu no passo 12); porta 3000 confirmada livre; nenhum processo node do projeto restante.
