# Validation After Refactoring
Command: npm start (node src/app.js), com `ADMIN_TOKEN=refactor-arch-validation DEBUG=false` | Port: 3000 | Date: 2026-10-15
Boot: OK (sem erros no log)

Mesmo roteiro (`.refactor-arch/run-requests.sh`), mesma ordem e mesmos corpos de `behavior-before.md`, com banco em memória recriado no boot. Rotas protegidas executadas com `X-Admin-Token`; os casos sem token (ou com token errado) foram executados à parte.

| Step | Method | Path | Before | After | Shape | Result | Note |
|---|---|---|---|---|---|---|---|
| 1 | GET | /api/admin/financial-report | 200 | 403 sem token / 200 com token | igual (corpo idêntico, mesma ordem) | CHANGED | rota protegida (AP-06); sem token: `Acesso negado` (text) |
| 2 | POST | /api/checkout | 200 | 200 | igual (`msg`, `enrollment_id` = 2) | OK | — |
| 3 | POST | /api/checkout | 400 | 400 | igual (text "Pagamento recusado") | OK | usuário não é mais criado quando o pagamento é recusado (sem efeito visível no contrato) |
| 4 | POST | /api/checkout | 400 | 400 | igual (text "Bad Request") | OK | — |
| 5 | POST | /api/checkout | 404 | 404 | igual (text "Curso não encontrado") | OK | — |
| 6 | POST | /api/checkout | 200 | 200 | igual (`enrollment_id` = 3) | OK | — |
| 7 | GET | /api/admin/financial-report | 200 | 200 (com token) | igual (corpo idêntico) | OK | — |
| 8 | DELETE | /api/users/2 | 200 | 403 sem token / 200 com token | text, mensagem nova | CHANGED | rota protegida (AP-06); exclui matrículas e pagamentos na mesma transação; mensagem "Usuário deletado, junto com suas matrículas e pagamentos." (AP-09) |
| 9 | GET | /api/admin/financial-report | 200 | 200 (com token) | mesmas chaves; sem alunos `Unknown` | CHANGED | sem órfãos após a exclusão do passo 8 (AP-09): `[Docker(0, []), Clean Architecture(997, [Leonan])]` |
| 10 | DELETE | /api/users/abc | 200 | 400 (com token) | text "ID inválido" | CHANGED | id não numérico rejeitado (AP-15) |
| 11 | POST | /api/checkout | 200 | 400 | text "Bad Request" | CHANGED | usuário novo sem `pwd` não recebe mais a senha padrão "123456" (AP-03, RF-03) |
| 12 | POST | /api/checkout | 000 (processo caiu) | 400 | text "Bad Request" | CHANGED | `card` numérico: queda do servidor virou 400 (AP-15/AP-14) |

Verificações extras:
- `GET /api/admin/financial-report` com `X-Admin-Token: errado` → 403 `Acesso negado`.
- `POST /api/checkout` com JSON malformado → 400 `Bad Request` (error handler central).
- Rollback (RF-09): com a tabela `payments` removida, o checkout falha e nenhum usuário nem matrícula é gravado (users = 1, enrollments = 1 antes e depois).
- Seed: a senha do usuário `Leonan` é gravada como `salt:hash` scrypt (não em claro).
- Log: o número do cartão aparece só mascarado (`cartão final 4444`); a chave do gateway não aparece.

Summary: OK 6 | CHANGED 6 | REGRESSION 0
Warnings in server log: `PAYMENT_GATEWAY_KEY não definida; gateway de pagamento em modo simulado sem credencial` (esperado: a variável não foi definida na validação). Nenhum aviso de depreciação.
