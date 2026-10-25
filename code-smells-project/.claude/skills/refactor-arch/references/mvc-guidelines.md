# MVC Guidelines — Arquitetura alvo da Fase 3

Regras da arquitetura para a qual o projeto é refatorado. Valem para qualquer stack; os
nomes de arquivo seguem a convenção da linguagem (`snake_case.py`, `camelCase.js`/
`kebab-case.js`).

## 1. Camadas e responsabilidades

| Camada | Responsável por | Não pode |
|---|---|---|
| **Config** (`config/`) | Ler variáveis de ambiente, defaults seguros de desenvolvimento, constantes da aplicação (limites, listas de valores válidos) | Ter segredos literais; importar qualquer outra camada |
| **Model** (`models/`) | Entidades, acesso a dados (queries parametrizadas, ORM), regras de domínio de **uma** entidade, serialização segura (allowlist de campos) | Conhecer HTTP (`request`, `req`, `res`, status codes); formatar resposta |
| **Services** (`services/`, parte da camada Model) | Regras de negócio que coordenam **várias** entidades ou integrações (fechar uma fatura, contratar uma assinatura, relatórios agregados, notificações), transações | Conhecer HTTP |
| **Controller** (`controllers/`) | Orquestrar a requisição: extrair e validar entrada, chamar model/service, escolher status e montar a resposta | Ter SQL; ter regra de negócio; acessar o banco diretamente |
| **View / Routes** (`views/` ou `routes/`) | Mapear método + URL → função do controller (blueprints/routers); serializar saída quando houver template/presenter | Ter lógica além do mapeamento |
| **Middlewares** (`middlewares/`) | Preocupações transversais: error handler central, autenticação de rotas administrativas, logging de requisição | Ter regra de domínio |
| **Database** (`database.py`/`db.js` ou `config/database.*`) | Criar/fechar conexões, inicializar schema, seed de desenvolvimento | Ser estado global mutável acessado por todos (ver §4) |
| **Composition root** (`app.py`/`app.js`, `create_app()`) | Criar a aplicação, carregar config, inicializar banco, registrar middlewares e rotas, injetar dependências | Ter rota com lógica, SQL ou regra |

### Regra de dependência

```text
views/routes → controllers → services → models → database
      ↑                                     ↑
 middlewares                             config  (qualquer camada pode ler config)
composition root → conhece todas e só as conecta
```

Uma camada só importa as que estão à sua direita. Models nunca importam controllers;
controllers nunca importam o driver do banco.

## 2. Layouts alvo

Escolha pelo resultado da Fase 1.

### 2a. Projeto monolítico (sem camadas reais)

Crie o layout abaixo dentro de `src/` (Python: pacote com `__init__.py`; Node: pasta comum).
Crie apenas os módulos que o domínio do projeto precisa — um model/controller/rota por
entidade ou agregado de negócio.

```text
src/
├── config/
│   └── settings.(py|js)          # env vars + constantes
├── database.(py|js)              # conexão, schema, seed
├── models/
│   └── <entidade>_model.(py|js)  # um por entidade
├── services/                     # só se houver regra entre entidades
│   └── <processo>_service.(py|js)
├── controllers/
│   └── <entidade>_controller.(py|js)
├── views/                        # ou routes/
│   └── <entidade>_routes.(py|js)
├── middlewares/
│   ├── error_handler.(py|js)
│   └── auth.(py|js)              # se houver rota administrativa ou login (token de sessão)
└── app.(py|js)                   # composition root (create_app / buildApp)
```

O arquivo de entrada original (ex.: `app.py`, `src/app.js`, o `main` do `package.json`)
**continua existindo** como entry point fino que importa o composition root e inicia o
servidor. Se não for possível mantê-lo no mesmo caminho, atualize o manifesto
(`scripts.start`, `main`) e o README para que o comando de execução documentado continue
funcionando.

### 2b. Projeto parcialmente em camadas

**Não recrie o projeto.** Mantenha a estrutura no nível em que ela está (ex.: `models/`,
`routes/`, `services/`, `utils/` na raiz) e:
1. Crie as camadas que **faltam** (tipicamente `controllers/`, `config/`, `middlewares/`).
2. Tire das rotas a orquestração (vai para controllers) e a regra de negócio (vai para
   models/services). As rotas ficam só com o mapeamento.
3. Mova código que está na camada errada (ex.: CRUD de uma entidade dentro do módulo de
   rotas de outra → módulo próprio).
4. Reaproveite helpers/constantes/métodos de model que já existem e eram ignorados; apague
   duplicatas e código morto.
5. `routes/` é aceito como a camada Views/Routes — não renomeie só por nome.

## 3. Preservação do contrato

Obrigatório manter, para cada endpoint original:
- método HTTP e caminho (incluindo parâmetros e prefixos);
- nomes dos campos de entrada e de saída;
- envelope da resposta (ex.: se as respostas eram `{"data": ..., "success": true}`, continuam
  assim — com os nomes de chave do próprio projeto);
- código de status de sucesso (200/201…) e de erros já tratados (400/404…);
- tipo de corpo (JSON continua JSON; se a rota respondia texto puro, mantenha o texto ou
  liste a mudança para JSON em Contract Changes).

Mudanças **permitidas**, sempre listadas em `Contract Changes` do resumo:
- remover campos sensíveis da saída (senha, hash, segredos);
- exigir token em rotas administrativas/destrutivas (§5);
- exigir token de sessão em rotas de escrita sobre recursos de usuário: 401 sem token
  válido, 403 para quem não é dono nem admin (§5);
- transformar um erro 500 causado por entrada inválida em 400/404/422;
- respostas de erro passando a ter corpo JSON padronizado.

## 4. Estado e dependências

- Nada de variável de módulo mutável compartilhada entre requisições. Conexões: uma por
  requisição/contexto (ex.: `flask.g` + `teardown_appcontext`) ou um objeto criado no
  composition root e passado às camadas (injeção por construtor/parâmetro/factory).
- Clientes de integração (SMTP, gateway) são criados no composition root a partir da config
  e injetados no serviço que precisa deles; sem credencial configurada, a integração fica
  desativada (log de aviso, sem exceção).
- Caches em memória só com dono explícito (instância injetada) e propósito real; se nunca
  são lidos, remova.

## 5. Escopo de segurança da Fase 3

Corrija **sempre**:
- **SQL injection** → queries parametrizadas (RF-01).
- **Segredos** → variáveis de ambiente; `SECRET_KEY` sem valor configurado gera chave
  aleatória no boot com aviso no log (RF-02).
- **Debug/bind** → `DEBUG` (default `false`), `HOST` (default `127.0.0.1`), `PORT` (default =
  porta original) lidos da config (RF-02).
- **Senhas** → hash forte com biblioteca **já disponível** na stack (`werkzeug.security` em
  Flask; `crypto.scrypt`/`crypto.randomBytes` do Node); seeds de desenvolvimento gravam o
  hash, para que o login dos usuários de exemplo continue funcionando (RF-03).
- **Exposição** → allowlist de campos na serialização; nada de segredo em health/log (RF-04).
- **Rotas administrativas/destrutivas** → middleware/decorator que exige o header
  `X-Admin-Token` igual à variável `ADMIN_TOKEN`. Sem `ADMIN_TOKEN` configurado, a rota
  responde **403** (fechada por padrão). Rota de execução de SQL arbitrário: além do token,
  aceitar apenas leitura (`SELECT`) (RF-05).
- **Elevação de privilégio no cadastro** → o cadastro público não aceita papel privilegiado
  vindo do corpo, a menos que a requisição traga o token de admin.
- **Token de login sem validação** → se o login do projeto **já emite token**, o token de
  sessão é assinado e **validado** nas rotas que o relatório mandar proteger, com
  autorização dono-ou-admin (RF-16), inclusive para o campo de dono enviado no corpo
  (criar ou transferir um registro para outro usuário exige admin). Emitir um token que
  nenhuma rota valida não conta como correção.

A recomendação de cada finding CRITICAL/HIGH é aplicada **por inteiro**: se ela pede para
proteger um conjunto de rotas, todas as rotas do conjunto ficam protegidas. O que não for
aplicado vai para `Pending` com o motivo — nunca é dado como resolvido.

Fora do escopo (listar em `Pending` com a recomendação):
- **criar** autenticação de usuários num projeto que não tem login nenhum (nesse caso,
  proteja com `X-Admin-Token`, RF-05); refresh/revogação de tokens; rate limiting;
- migração de dados já gravados em produção (ex.: rehash de senhas existentes);
- troca de banco de dados ou de framework.

## 6. Variáveis de ambiente (convenção)

| Variável | Uso | Default de desenvolvimento |
|---|---|---|
| `SECRET_KEY` (ou equivalente da stack) | Chave da aplicação | Aleatória gerada no boot, com aviso |
| `ADMIN_TOKEN` | Libera rotas administrativas via header `X-Admin-Token` | Ausente → rotas administrativas respondem 403 |
| `SESSION_TOKEN_MAX_AGE` | Validade, em segundos, do token de sessão (só com login) | `3600` |
| `DEBUG` | Modo debug | `false` |
| `HOST` / `PORT` | Bind do servidor | `127.0.0.1` / porta original |
| `DATABASE_URL` / `DB_PATH` | Localização do banco | Valor original do projeto |
| `CORS_ORIGINS` | Origens permitidas | Lista vazia ou origem local de desenvolvimento |
| Credenciais de integrações (`SMTP_*`, `<SERVIÇO>_API_KEY`…) | Segredos de terceiros | Vazias → integração desativada |

Documente todas em `.env.example` (sem valores reais). Use `python-dotenv`/`dotenv` só se
já estiver nas dependências; caso contrário, leia direto do ambiente.

## 7. Checklist da arquitetura alvo

- [ ] Config isolada, sem segredos literais, com `.env.example`
- [ ] Models abstraem os dados (nenhum SQL fora da camada Model)
- [ ] Views/Routes só mapeiam URL → controller
- [ ] Controllers só orquestram (sem SQL, sem regra de negócio)
- [ ] Regras entre entidades em services, com transação quando há várias escritas
- [ ] Error handler centralizado registrado no composition root
- [ ] Entry point claro; comando de execução original funcionando
- [ ] Nenhum estado global mutável compartilhado
