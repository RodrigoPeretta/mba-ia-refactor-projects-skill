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

As variáveis de ambiente estão documentadas em `.env.example`. Copie o arquivo para `.env` e ajuste os valores; o `python-dotenv` carrega o `.env` no boot. Sem `.env`, a aplicação sobe em `127.0.0.1:5000` com `DEBUG=false` e gera uma `SECRET_KEY` temporária a cada boot.

## Autenticação

- `POST /login` devolve um `token` de sessão assinado, válido por `SESSION_TOKEN_MAX_AGE` segundos. Envie-o como `Authorization: Bearer <token>`.
- Escrita em tasks (`POST/PUT/DELETE /tasks`) e em usuários (`PUT/DELETE /users/<id>`) exige token. Só o dono ou um admin pode escrever; o campo `user_id` de uma task só pode apontar para o próprio usuário, exceto para admins.
- `POST/PUT/DELETE /categories`, `role`/`active` de usuários e cadastro com `role` diferente de `user` exigem admin: um usuário com `role=admin` ou o header `X-Admin-Token` igual a `ADMIN_TOKEN`.
- Sem credencial válida a resposta é 401; com credencial mas sem permissão, 403.
