# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Todas as variáveis estão em [`.env.example`](.env.example) (copie para `.env`). Sem nenhuma
delas a aplicação sobe com defaults de desenvolvimento: `127.0.0.1:5000`, debug desligado e
`SECRET_KEY` temporária.

## Autenticação

- `POST /login` devolve um `token` de sessão assinado (validade em `SESSION_TOKEN_MAX_AGE`).
  Envie-o como `Authorization: Bearer <token>`.
- Escrita em usuários (`PUT`/`DELETE /users/<id>`) e em tasks (`POST /tasks`,
  `PUT`/`DELETE /tasks/<id>`): 401 sem token válido; 403 se quem chama não é o dono nem admin.
  Alterar `role`/`active` e atribuir task a outro usuário exigem admin.
- `POST /users` com `role` diferente de `user` exige admin.
- Escrita em categorias exige admin.
- Admin = usuário com `role` `admin` (token de sessão) **ou** header `X-Admin-Token` igual à
  variável `ADMIN_TOKEN` (sem ela, esse header nunca é aceito).

## Estrutura

```text
app.py           composition root (create_app) e entry point
config/          variáveis de ambiente e constantes de domínio
database.py      instância do SQLAlchemy e commit transacional
models/          entidades (Task, User, Category) e regras de uma entidade
services/        regras de negócio, consultas agregadas, tokens e notificações
controllers/     orquestração das requisições e validação de entrada
routes/          blueprints: só mapeiam URL → controller
middlewares/     autenticação/autorização e error handler central
utils/           helpers e exceções de aplicação
```
