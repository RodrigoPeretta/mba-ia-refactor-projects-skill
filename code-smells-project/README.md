# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Toda a configuração vem de variáveis de ambiente (veja `.env.example`). Sem nenhuma variável
definida a aplicação sobe com defaults de desenvolvimento: `127.0.0.1:5000`, debug desligado e
`SECRET_KEY` temporária.

As rotas `/admin/*` exigem o header `X-Admin-Token` igual à variável `ADMIN_TOKEN`; sem ela
configurada, respondem 403. `/admin/query` aceita apenas uma consulta `SELECT`.

## Estrutura

```
app.py              # entry point (python app.py)
src/
├── app.py          # composition root (create_app)
├── config/         # settings: variáveis de ambiente e constantes
├── database.py     # conexão por requisição, schema e seed
├── exceptions.py   # erros da aplicação
├── models/         # acesso a dados por entidade
├── services/       # regras de pedido, relatório, notificações
├── controllers/    # orquestração das requisições e validação
├── views/          # blueprints (método + URL → controller)
└── middlewares/    # error handler central e autenticação admin
```
