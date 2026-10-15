# Behavior Before Refactoring
Command: `python app.py` (via `.venv/Scripts/python.exe app.py`, `PYTHONWARNINGS=default`) | Port: 5000 | Date: 2026-10-15

Banco: `loja.db` inexistente antes da medição → criado e semeado no boot (10 produtos, 3 usuários).
Log do servidor: `server-before.log` (único aviso: "This is a development server").

| Step | Method | Path | Request | Status | Shape | Note |
|---|---|---|---|---|---|---|
| 1 | GET | / | — | 200 | object: endpoints(obj), mensagem, versao | — |
| 2 | GET | /health | — | 200 | object: ambiente, counts(pedidos,produtos,usuarios), database, db_path, debug, secret_key, status, versao | expõe `secret_key` e `db_path` |
| 3 | GET | /produtos | — | 200 | object: dados(list[ativo,categoria,criado_em,descricao,estoque,id,nome,preco]), sucesso | 10 produtos |
| 4 | GET | /produtos/1 | — | 200 | object: dados(obj produto), sucesso | — |
| 5 | GET | /produtos/9999 | — | 404 | object: erro, sucesso | "Produto não encontrado" |
| 6 | GET | /produtos/busca?q=Mouse | — | 200 | object: dados(list produto), sucesso, total | 1 resultado |
| 7 | GET | /produtos/busca?categoria=informatica&preco_min=100&preco_max=500 | — | 200 | object: dados(list produto), sucesso, total | — |
| 8 | GET | /produtos/busca?q=O'Brien | — | 500 | object: erro | `near "Brien": syntax error` (SQL injection) |
| 9 | GET | /usuarios | — | 200 | object: dados(list[criado_em,email,id,nome,senha,tipo]), sucesso | expõe `senha` em claro |
| 10 | GET | /usuarios/1 | — | 200 | object: dados(obj usuário com senha), sucesso | expõe `senha` |
| 11 | POST | /produtos | requests/11.json | 201 | object: dados(id), mensagem, sucesso | id criado = 11 |
| 12 | POST | /produtos | requests/12.json | 400 | object: erro | "Nome é obrigatório" |
| 13 | POST | /produtos | requests/13.json | 400 | object: erro | "Categoria inválida. Válidas: [...]" |
| 14 | PUT | /produtos/11 | requests/14.json | 200 | object: mensagem, sucesso | — |
| 15 | PUT | /produtos/9999 | requests/15.json | 404 | object: erro | — |
| 16 | POST | /usuarios | requests/16.json | 201 | object: dados(id), sucesso | id criado = 4 |
| 17 | POST | /usuarios | requests/17.json | 400 | object: erro | — |
| 18 | POST | /login | requests/18.json | 200 | object: dados(email,id,nome,tipo), mensagem, sucesso | admin do seed |
| 19 | POST | /login | requests/19.json | 401 | object: erro, sucesso | senha errada |
| 20 | POST | /login | requests/20.json | 400 | object: erro | sem senha |
| 21 | POST | /login | requests/21.json | 200 | object: dados(email,id,nome,tipo), mensagem, sucesso | **bypass por SQL injection** → loga como admin |
| 22 | POST | /login | requests/22.json | 200 | object: dados(email,id,nome,tipo), mensagem, sucesso | usuário criado no passo 16 |
| 23 | POST | /pedidos | requests/23.json | 201 | object: dados(pedido_id,total), mensagem, sucesso | pedido 1, total 479.7 |
| 24 | POST | /pedidos | requests/24.json | 400 | object: erro | sem itens |
| 25 | POST | /pedidos | requests/25.json | 400 | object: erro, sucesso | produto inexistente |
| 26 | POST | /pedidos | requests/26.json | 400 | object: erro, sucesso | estoque insuficiente |
| 27 | GET | /pedidos | — | 200 | object: dados(list[criado_em,id,itens,status,total,usuario_id]), sucesso | itens com produto_nome |
| 28 | GET | /pedidos/usuario/2 | — | 200 | object: dados(list pedido), sucesso | — |
| 29 | PUT | /pedidos/1/status | requests/29.json | 200 | object: mensagem, sucesso | aprovado |
| 30 | PUT | /pedidos/1/status | requests/30.json | 400 | object: erro | "Status inválido" |
| 31 | GET | /relatorios/vendas | — | 200 | object: dados(8 métricas), sucesso | faturamento 479.7, aprovados 1 |
| 32 | GET | /usuarios/9999 | — | 404 | object: erro | — |
| 33 | DELETE | /produtos/11 | — | 200 | object: mensagem, sucesso | — |
| 34 | DELETE | /produtos/9999 | — | 404 | object: erro | — |
| 35 | POST | /produtos | requests/35.json | 500 | object: erro | preco string → TypeError cru |
| 36 | GET | /produtos/busca?preco_min=abc | — | 500 | object: erro | float() cru |
| 37 | POST | /admin/query | requests/37.json | 200 | object: dados(list[id,nome]), sucesso | sem autenticação |
| 38 | POST | /admin/query | requests/38.json | 400 | object: erro | "Query não informada" |
| 39 | POST | /admin/reset-db | — | 200 | object: mensagem, sucesso | sem autenticação; apaga tudo |
| 40 | GET | /health | — | 200 | object: (igual ao passo 2) | counts zerados após reset |
