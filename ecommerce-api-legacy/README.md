# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

## Configuração

As variáveis de ambiente estão documentadas em `.env.example` (todas opcionais):

- `PORT` (padrão `3000`) e `HOST` (padrão `127.0.0.1`)
- `DB_PATH` (padrão `:memory:`)
- `ADMIN_TOKEN`: exigido no header `X-Admin-Token` em `GET /api/admin/financial-report` e `DELETE /api/users/:id`; sem ele essas rotas respondem 403
- `PAYMENT_GATEWAY_KEY`: chave do gateway de pagamento

Exemplo: `ADMIN_TOKEN=meu-token npm start` (no PowerShell: `$env:ADMIN_TOKEN="meu-token"; npm start`).

## Estrutura

`src/app.js` (composition root e entry point) → `routes/` → `controllers/` → `services/` → `models/` → `database.js`; config em `src/config/`; auth e error handler em `src/middlewares/`.

Exemplos de requisições estão em `api.http`.
