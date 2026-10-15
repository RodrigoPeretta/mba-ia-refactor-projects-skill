# Validation After Refactoring
Command: `python app.py` (via `.venv/Scripts/python.exe app.py`, `ADMIN_TOKEN=refactor-arch-validation DEBUG=false PYTHONWARNINGS=default`) | Port: 5000 | Date: 2026-10-15
Boot: OK (sem erros no log; `server-after.log`)

Estado inicial idêntico ao da medição "antes": `loja.db` removido e recriado/semeado no boot.
Comparação feita por status, forma **e valores** dos corpos (ignorando `criado_em`): fora as
linhas CHANGED, todos os corpos são idênticos aos originais (incluindo pedidos com itens,
totais e relatório de vendas).

| Step | Method | Path | Before | After | Shape | Result | Note |
|---|---|---|---|---|---|---|---|
| 1 | GET | / | 200 | 200 | igual | OK | — |
| 2 | GET | /health | 200 | 200 | sem `secret_key`, `db_path`, `debug` | CHANGED | dados sensíveis removidos (AP-04, AP-02) |
| 3 | GET | /produtos | 200 | 200 | igual | OK | — |
| 4 | GET | /produtos/1 | 200 | 200 | igual | OK | — |
| 5 | GET | /produtos/9999 | 404 | 404 | igual | OK | — |
| 6 | GET | /produtos/busca?q=Mouse | 200 | 200 | igual | OK | — |
| 7 | GET | /produtos/busca?categoria=informatica&preco_min=100&preco_max=500 | 200 | 200 | igual | OK | — |
| 8 | GET | /produtos/busca?q=O'Brien | 500 | 200 | object: dados([]), sucesso, total | CHANGED | aspas não quebram mais a query (AP-01) |
| 9 | GET | /usuarios | 200 | 200 | sem `senha` | CHANGED | campo sensível removido (AP-04) |
| 10 | GET | /usuarios/1 | 200 | 200 | sem `senha` | CHANGED | campo sensível removido (AP-04) |
| 11 | POST | /produtos | 201 | 201 | igual | OK | id criado = 11 |
| 12 | POST | /produtos | 400 | 400 | igual | OK | mesma mensagem |
| 13 | POST | /produtos | 400 | 400 | igual | OK | mesma mensagem |
| 14 | PUT | /produtos/11 | 200 | 200 | igual | OK | — |
| 15 | PUT | /produtos/9999 | 404 | 404 | igual | OK | — |
| 16 | POST | /usuarios | 201 | 201 | igual | OK | senha gravada com hash scrypt |
| 17 | POST | /usuarios | 400 | 400 | igual | OK | — |
| 18 | POST | /login | 200 | 200 | igual | OK | login do seed funciona com hash |
| 19 | POST | /login | 401 | 401 | igual | OK | — |
| 20 | POST | /login | 400 | 400 | igual | OK | — |
| 21 | POST | /login | 200 | 401 | object: erro, sucesso | CHANGED | bypass por SQL injection bloqueado (AP-01, AP-03) |
| 22 | POST | /login | 200 | 200 | igual | OK | usuário criado no passo 16 |
| 23 | POST | /pedidos | 201 | 201 | igual | OK | pedido 1, total 479.7 |
| 24 | POST | /pedidos | 400 | 400 | igual | OK | — |
| 25 | POST | /pedidos | 400 | 400 | igual | OK | — |
| 26 | POST | /pedidos | 400 | 400 | igual | OK | — |
| 27 | GET | /pedidos | 200 | 200 | igual | OK | uma query com JOIN; itens idênticos |
| 28 | GET | /pedidos/usuario/2 | 200 | 200 | igual | OK | — |
| 29 | PUT | /pedidos/1/status | 200 | 200 | igual | OK | — |
| 30 | PUT | /pedidos/1/status | 400 | 400 | igual | OK | — |
| 31 | GET | /relatorios/vendas | 200 | 200 | igual | OK | valores idênticos |
| 32 | GET | /usuarios/9999 | 404 | 404 | igual | OK | — |
| 33 | DELETE | /produtos/11 | 200 | 200 | igual | OK | — |
| 34 | DELETE | /produtos/9999 | 404 | 404 | igual | OK | — |
| 35 | POST | /produtos | 500 | 400 | igual (erro) | CHANGED | entrada inválida: 500 → 400 "Preço deve ser numérico" (AP-15/AP-14) |
| 36 | GET | /produtos/busca?preco_min=abc | 500 | 400 | igual (erro) | CHANGED | entrada inválida: 500 → 400 (AP-15/AP-14) |
| 37 | POST | /admin/query | 200 | 403 / 200 com token | igual | CHANGED | rota protegida por `X-Admin-Token` (AP-06) |
| 38 | POST | /admin/query | 400 | 403 / 400 com token | igual | CHANGED | rota protegida (AP-06) |
| 39 | POST | /admin/reset-db | 200 | 403 / 200 com token | igual | CHANGED | rota protegida (AP-06) |
| 40 | GET | /health | 200 | 200 | sem `secret_key`, `db_path`, `debug` | CHANGED | counts zerados após reset, como antes (AP-04) |

Summary: OK 29 | CHANGED 11 | REGRESSION 0
Warnings in server log: nenhum além de "This is a development server" (presente também no original) e o aviso esperado de `SECRET_KEY` não definida.

## Verificações adicionais (test client, banco temporário)
- Pedido `[{produto 1, qtd 6}, {produto 1, qtd 6}]` (estoque 10): 400 "Estoque insuficiente", 0 pedidos, 0 itens, estoque intacto → rollback OK (AP-09).
- Senha do seed gravada como `scrypt:32768:8:1$...` (AP-03).
- Quantidade negativa no pedido → 400 (antes aumentava o estoque) (AP-15).
- `PUT /pedidos/999/status` → 404 (antes 200) (AP-15).
- `/admin/query` com token: `DROP TABLE` e `SELECT 1; DELETE ...` → 400 "Apenas uma consulta SELECT é permitida"; token errado → 403; tabela intacta (AP-06).
- Rota inexistente → 404 com corpo JSON `{"erro": ...}` (antes HTML) (AP-14).
- `POST /login` sem corpo → 400 (antes 500) (AP-15).
