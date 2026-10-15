# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A configuração vem de variáveis de ambiente (ou de um arquivo `.env`; veja `.env.example`). Rotas destrutivas (`DELETE`), a criação de usuários com papel diferente de `user` e a alteração de `role`/`active` exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN`; sem `ADMIN_TOKEN` definido elas respondem 403.

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.
