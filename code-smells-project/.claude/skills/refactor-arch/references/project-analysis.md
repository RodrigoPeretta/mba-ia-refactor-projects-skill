# Project Analysis — Heurísticas da Fase 1

Objetivo: montar o perfil do projeto **só a partir dos arquivos**, sem executar nada.
Cada campo abaixo tem a fonte de onde deve ser extraído e a regra de desempate.

## 1. Arquivos-fonte (o que analisar)

Considere arquivo-fonte todo arquivo de código da aplicação: `.py`, `.js`, `.mjs`, `.cjs`,
`.ts`, `.go`, `.java`, `.rb`, `.php`, `.cs` etc., incluindo scripts de seed/migração
escritos na linguagem do projeto.

**Exclua** sempre:
- Dependências e ambientes: `node_modules/`, `.venv/`, `venv/`, `env/`, `vendor/`,
  `site-packages/`, `__pycache__/`, `*.pyc`, `dist/`, `build/`, `.next/`, `target/`.
- Ferramentas e metadados: `.git/`, `.claude/`, `.refactor-arch/`, `.idea/`, `.vscode/`.
- Lockfiles e manifestos (lidos à parte): `package-lock.json`, `yarn.lock`,
  `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`.
- Dados e artefatos: bancos (`*.db`, `*.sqlite*`), logs, imagens, `.env`.

Conte as linhas de cada arquivo-fonte (aproximação: total de linhas do arquivo) e informe
o total. A lista de arquivos-fonte é a lista que será auditada na Fase 2.

## 2. Linguagem (manifesto → linguagem)

| Manifesto encontrado na raiz | Linguagem |
|---|---|
| `requirements*.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `setup.cfg` | Python |
| `package.json` | JavaScript (Node.js); TypeScript se houver `tsconfig.json` ou `typescript` nas dependências |
| `go.mod` | Go |
| `pom.xml`, `build.gradle(.kts)` | Java/Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `*.csproj` | C# |

Desempate: se houver mais de um manifesto, a linguagem principal é a da maioria dos
arquivos-fonte. Versão da linguagem: `engines.node` (package.json), `python_requires` /
`requires-python` (Python), `.python-version`, `.nvmrc`; se nada declarar, omita a versão.

## 3. Framework e versão

Detecte pelo **par** dependência declarada + import/uso no código (as duas evidências):

| Dependência | Uso no código | Framework |
|---|---|---|
| `flask` | `from flask import Flask`, `Flask(__name__)` | Flask |
| `django` | `settings.py`, `urls.py`, `INSTALLED_APPS` | Django |
| `fastapi` | `FastAPI()`, `@app.get` | FastAPI |
| `express` | `require('express')` / `import express`, `express()` | Express |
| `fastify`, `koa`, `@nestjs/core`, `hapi` | instância correspondente | Fastify / Koa / NestJS / hapi |
| `gin-gonic/gin`, `labstack/echo` | `gin.Default()`, `echo.New()` | Gin / Echo |
| `spring-boot-starter-web` | `@RestController` | Spring Boot |

Versão: copie **exatamente** como está no manifesto (`flask==3.1.1` → `3.1.1`;
`"express": "^4.18.2"` → `^4.18.2`). Sem pin, escreva "versão não declarada".

Dependências: liste as diretas do manifesto (não as transitivas do lockfile). Marque
dependências declaradas que não aparecem em nenhum import — isso é sinal para AP-19 na
Fase 2.

## 4. Banco de dados e tabelas

| Sinal | Banco / acesso |
|---|---|
| `import sqlite3`, `require('sqlite3')`, `better-sqlite3` | SQLite, SQL cru via driver |
| `sqlite:///` em URI, `:memory:` | SQLite (arquivo ou memória) |
| `flask_sqlalchemy`, `sqlalchemy` | ORM SQLAlchemy (banco pela URI) |
| `psycopg`, `pg`, `mysql`, `mysql2`, `pymysql` | PostgreSQL / MySQL via driver |
| `mongoose`, `mongodb`, `pymongo` | MongoDB |
| `sequelize`, `typeorm`, `prisma`, `knex` | ORM/query builder (banco pela config) |

Tabelas, em ordem de preferência:
1. DDL no código: `CREATE TABLE [IF NOT EXISTS] <nome>`.
2. Models de ORM: `__tablename__ = '<nome>'`, `class X(db.Model)` (nome padrão do ORM),
   `sequelize.define('<nome>'`, `new Schema(` + `model('<nome>'`.
3. Migrations, se existirem.

Registre também se o banco é recriado/semeado no boot (DDL ou inserts executados na
inicialização) ou se existe um script de seed separado — isso muda o preparo da Fase 3.

## 5. Domínio da aplicação

Infira de três fontes e escreva uma linha com o domínio e as entidades principais:
1. Nomes das tabelas/entidades.
2. Prefixos das rotas (`/orders`, `/api/invoices`...).
3. Textos do README e mensagens/strings da aplicação.

Exemplo de formato: `API de faturamento (clientes, faturas, pagamentos)`. Use os termos do
próprio projeto, inclusive o idioma em que estão escritos.

## 6. Entry point, execução e porta

| Onde procurar | O que extrair |
|---|---|
| README (seções "como rodar", "run", "setup") | Comandos de instalação, preparo (seed, migrate) e execução — **prioridade máxima** |
| `package.json` → `scripts.start`, `main` | Comando e arquivo de entrada |
| Python: arquivo com `if __name__ == "__main__":` + `app.run(...)` | Entry point e `host`/`port` |
| Node: `app.listen(<porta>)` ou `listen(config.port)` | Porta (siga a variável até o valor) |
| `Procfile`, `Dockerfile` (`CMD`), `docker-compose.yml` | Comando alternativo |

Porta padrão quando nada for declarado: Flask 5000, Express (sem valor) 3000, Django 8000,
FastAPI/uvicorn 8000. Anote também se o modo debug/reload está ligado (cria processos
filhos — relevante para a Fase 3).

## 7. Inventário de endpoints

Liste todas as rotas como `MÉTODO /caminho → arquivo:linha`:

| Stack | Padrões de registro |
|---|---|
| Flask | `@app.route(...)`, `@<bp>.route(...)`, `app.add_url_rule(...)`, `methods=[...]` (padrão GET), prefixo de `Blueprint(..., url_prefix=)` e de `register_blueprint(..., url_prefix=)` |
| Express | `app.get/post/put/patch/delete(...)`, `router.<método>(...)` + prefixo de `app.use('<prefixo>', router)` |
| FastAPI | `@app.get(...)`, `APIRouter(prefix=)` |
| Django | `path(...)`/`re_path(...)` em `urls.py` |

Também anote, por endpoint, o que for necessário para chamá-lo depois: parâmetros de
caminho, campos obrigatórios do corpo (das validações no código) e exemplos prontos em
arquivos `.http`, coleções Postman/Insomnia ou README.

## 8. Classificação da arquitetura

Avalie as responsabilidades: **roteamento**, **orquestração da requisição** (controller),
**regra de negócio**, **acesso a dados**, **configuração**, **tratamento de erro**.

| Classificação | Critério objetivo |
|---|---|
| **Monolítica** | Não há pastas/módulos de camada, ou há módulos com nomes de camada mas ≥ 3 responsabilidades misturadas no mesmo arquivo/classe (ex.: um arquivo com SQL + regra + rotas; uma classe que cria o banco, registra rotas e chama integrações externas) |
| **Parcialmente em camadas** | Existem pastas/módulos de camada (ex.: `models/`, `routes/`, `services/`, `utils/`) e o acesso a dados está separado das rotas, mas pelo menos uma camada do MVC alvo falta (controllers, config, error handling) ou concentra responsabilidade de outra (regra de negócio nas rotas) |
| **Em camadas** | Todas as camadas do MVC alvo existem e cada uma cumpre só a sua responsabilidade |

Na justificativa, cite as evidências (ex.: "3 arquivos; o módulo de dados mistura SQL,
regras de dois domínios e formatação de resposta; sem config nem error handler"). Para projetos parcialmente em
camadas, diga quais camadas existem e quais faltam.

## 9. Checklist do perfil

- [ ] Linguagem e framework com evidência de manifesto **e** de código
- [ ] Versão do framework copiada do manifesto
- [ ] Contagem de arquivos-fonte e linhas aplicando as exclusões
- [ ] Banco, tabelas e forma de preparo (boot ou seed)
- [ ] Domínio com as entidades principais
- [ ] Comando de execução, preparo e porta
- [ ] Inventário completo de endpoints com arquivo:linha
- [ ] Classificação da arquitetura com justificativa
