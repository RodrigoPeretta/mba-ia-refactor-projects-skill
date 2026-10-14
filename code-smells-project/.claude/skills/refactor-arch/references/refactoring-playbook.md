# Refactoring Playbook — Fase 3

Transformações concretas para cada anti-pattern do catálogo. Os exemplos usam um domínio
genérico (faturas, clientes, contas) e servem como **padrão**: adapte nomes, envelope de
resposta e estilo ao projeto, preservando o contrato (ver `mvc-guidelines.md` §3).

Ordem recomendada de aplicação: RF-02 → RF-06/RF-07/RF-08 (estrutura) → RF-01, RF-03,
RF-04, RF-05, RF-09 (segurança e integridade) → RF-10 a RF-15 (qualidade).

---

## RF-01 — Queries parametrizadas
**Corrige:** AP-01

1. Troque toda concatenação/interpolação de valores por placeholders do driver
   (`?` no SQLite, `%s` no psycopg/mysql, `$1` no pg) e passe os valores separados.
2. Filtros dinâmicos: monte a cláusula com trechos **constantes** e acumule os valores numa
   lista.
3. Nomes de coluna/ordenação vindos do usuário: valide contra uma allowlist.

```python
# antes
cursor.execute("SELECT * FROM invoices WHERE customer = '" + name + "'")

# depois
cursor.execute("SELECT * FROM invoices WHERE customer = ?", (name,))

# filtro dinâmico
clauses, params = ["1=1"], []
if term:
    clauses.append("(title LIKE ? OR notes LIKE ?)")
    params += [f"%{term}%", f"%{term}%"]
if min_total is not None:
    clauses.append("total >= ?")
    params.append(min_total)
cursor.execute(f"SELECT * FROM invoices WHERE {' AND '.join(clauses)}", params)
```

```javascript
// antes
db.get(`SELECT * FROM accounts WHERE email = '${email}'`, cb);
// depois
db.get("SELECT * FROM accounts WHERE email = ?", [email], cb);
```

**Verificar:** nenhuma chamada de execução recebe string com `+`, `%`, `.format`, f-string
ou `${}` contendo valor externo; um valor com `'` não quebra a query.

---

## RF-02 — Configuração e segredos via ambiente
**Corrige:** AP-02, AP-10, AP-16

1. Crie o módulo de config com todas as variáveis, defaults seguros e constantes.
2. Substitua cada literal (chave, senha, porta, host, debug, caminho do banco, CORS) pela
   leitura da config.
3. Crie `.env.example` listando as variáveis sem valores reais.

```python
# antes (app.py)
app.config["SECRET_KEY"] = "my-secret-123"
app.run(host="0.0.0.0", port=5000, debug=True)

# depois (src/config/settings.py)
import os, secrets, logging

def _bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")

SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
if "SECRET_KEY" not in os.environ:
    logging.getLogger(__name__).warning("SECRET_KEY não definida; usando chave temporária")
DEBUG = _bool("DEBUG")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "5000"))
DB_PATH = os.environ.get("DB_PATH", "app.db")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")  # None → rotas admin fechadas
CORS_ORIGINS = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]

# entry point
app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

```javascript
// antes (utils.js)
const config = { dbPass: "prod-pass", billingApiKey: "sk_live_abc", port: 3000 };

// depois (src/config/settings.js)
const settings = {
  port: Number(process.env.PORT || 3000),
  host: process.env.HOST || "127.0.0.1",
  dbPath: process.env.DB_PATH || ":memory:",
  billingApiKey: process.env.BILLING_API_KEY || "",
  adminToken: process.env.ADMIN_TOKEN || null,
};
module.exports = Object.freeze(settings);
```

```text
# .env.example
SECRET_KEY=
ADMIN_TOKEN=
DEBUG=false
HOST=127.0.0.1
PORT=5000
```

**Verificar:** busca pelos padrões de AP-02 não encontra literais; a aplicação sobe sem
nenhuma variável definida (defaults) e com elas definidas.

---

## RF-03 — Hash de senha forte (incluindo seeds)
**Corrige:** AP-03

1. Na criação/alteração de senha, grave só o hash (com salt) gerado pela biblioteca da stack.
2. No login, busque o usuário pelo identificador e compare com a função de verificação —
   nunca compare a senha dentro do SQL.
3. Seeds de desenvolvimento passam a gravar o hash.
4. Remova senhas padrão silenciosas: senha ausente é erro de validação (400).

```python
# antes
cursor.execute("INSERT INTO accounts (email, password) VALUES (?, ?)", (email, pwd))
row = cursor.execute("SELECT * FROM accounts WHERE email=? AND password=?", (email, pwd)).fetchone()
# ou: self.password = hashlib.md5(pwd.encode()).hexdigest()

# depois
from werkzeug.security import generate_password_hash, check_password_hash
cursor.execute("INSERT INTO accounts (email, password) VALUES (?, ?)",
               (email, generate_password_hash(pwd)))
row = cursor.execute("SELECT * FROM accounts WHERE email = ?", (email,)).fetchone()
ok = row is not None and check_password_hash(row["password"], pwd)
```

```javascript
// depois (Node, sem dependência nova)
const crypto = require("crypto");
function hashPassword(pwd) {
  const salt = crypto.randomBytes(16).toString("hex");
  const hash = crypto.scryptSync(pwd, salt, 64).toString("hex");
  return `${salt}:${hash}`;
}
function verifyPassword(pwd, stored) {
  const [salt, hash] = stored.split(":");
  const test = crypto.scryptSync(pwd, salt, 64);
  return crypto.timingSafeEqual(Buffer.from(hash, "hex"), test);
}
```

**Verificar:** nenhuma senha em claro no banco após o seed; login com a senha certa funciona
e com a errada falha; duas senhas diferentes geram hashes diferentes.

---

## RF-04 — Serialização por allowlist
**Corrige:** AP-04

1. Defina, no model, a função de serialização pública com a lista explícita de campos.
2. Use essa função em todas as respostas; nunca devolva a linha/objeto inteiro.
3. Health/status devolve só estado operacional (`status`, `database`), nunca config.

```python
# antes
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}

# depois
PUBLIC_FIELDS = ("id", "name", "email", "role", "created_at")
def to_dict(self):
    return {f: _jsonable(getattr(self, f)) for f in PUBLIC_FIELDS}
```

**Verificar:** nenhuma resposta contém campos de senha/hash/segredo (buscar as chaves no
corpo das respostas da validação).

---

## RF-05 — Proteção de rota administrativa por token
**Corrige:** AP-06

1. Crie o middleware/decorator que compara `X-Admin-Token` com `ADMIN_TOKEN` usando
   comparação de tempo constante; sem `ADMIN_TOKEN` configurado, responde 403.
2. Aplique nas rotas administrativas/destrutivas. Mantenha a rota.
3. Execução de SQL arbitrário: aceite só `SELECT` (uma única instrução), além do token.
4. Cadastro público: ignore/rejeite papel privilegiado sem token.

```python
# antes — qualquer cliente executa SQL ou apaga o banco
@app.route("/admin/run-sql", methods=["POST"])
def run_sql():
    return jsonify(db.execute(request.get_json()["sql"]).fetchall())

# depois — rota mantida, protegida e restrita a leitura
@bp.route("/admin/run-sql", methods=["POST"])
@require_admin
def run_sql():
    sql = (request.get_json(silent=True) or {}).get("sql", "").strip()
    if not sql.upper().startswith("SELECT") or ";" in sql.rstrip(";"):
        raise AppError("Apenas uma consulta SELECT é permitida", 400)
    return jsonify([dict(r) for r in get_db().execute(sql).fetchall()])
```

```python
# src/middlewares/auth.py
import hmac
from functools import wraps
from flask import request, jsonify
from src.config import settings

def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        if not settings.ADMIN_TOKEN or not hmac.compare_digest(token, settings.ADMIN_TOKEN):
            return jsonify({"error": "Acesso negado"}), 403
        return view(*args, **kwargs)
    return wrapper
```

```javascript
// antes: app.delete("/api/things/:id", (req, res) => db.run("DELETE ...", [req.params.id], ...));
// depois — src/middlewares/auth.js
const crypto = require("crypto");
const settings = require("../config/settings");
module.exports = function requireAdmin(req, res, next) {
  const token = req.get("X-Admin-Token") || "";
  const expected = settings.adminToken;
  const ok = expected && token.length === expected.length &&
    crypto.timingSafeEqual(Buffer.from(token), Buffer.from(expected));
  if (!ok) return res.status(403).json({ error: "Acesso negado" });
  next();
};
// router.delete("/api/things/:id", requireAdmin, controller.remove);
```

**Verificar:** sem header → 403; com header correto → comportamento original.

---

## RF-06 — God Class / God Module → camadas
**Corrige:** AP-05, AP-11

1. Liste as responsabilidades do arquivo/classe (banco, queries, regra, validação, rotas,
   resposta, integrações) e os domínios que ele cobre.
2. Crie os módulos de destino conforme o layout alvo, um por entidade/agregado.
3. Mova, nesta ordem: conexão/schema/seed → `database`; queries → models; regras → services;
   validação + resposta → controllers; registro de rotas → views/routes; integração →
   serviço injetado.
4. O arquivo original vira composition root ou entry point fino (ou é removido se o comando
   de execução apontar para outro arquivo).

```javascript
// antes: class Manager { constructor(){ this.db = new sqlite3.Database(...) }
//          createTables(){...}  registerRoutes(app){ app.post('/api/x', (req,res)=>{ /* SQL+regra */ }) } }

// depois
// src/database.js          → createDb(), initSchema(db), seed(db)
// src/models/invoiceModel.js → findById(db, id), insert(db, data)
// src/services/billingService.js → subscribe({ db, billingClient }, input)
// src/controllers/billingController.js → (req, res, next) => service + resposta
// src/routes/billingRoutes.js → router.post('/api/subscriptions', controller.subscribe)
// src/app.js (composition root)
function buildApp({ db, settings }) {
  const app = express();
  app.use(express.json());
  app.use(billingRoutes({ db, settings }));
  app.use(errorHandler);
  return app;
}
```

**Verificar:** nenhum arquivo mistura 3+ responsabilidades; o composition root só conecta.

---

## RF-07 — Fat controller/rota → model/service
**Corrige:** AP-07, AP-13

1. Extraia a regra (cálculos, transições, decisões) para um método do model (uma entidade)
   ou função de service (várias entidades).
2. O controller passa a: ler/validar entrada → chamar a regra → montar a resposta.
3. Se o model já tinha o método (ex.: um `is_*` ou `calculate_*`), **use-o** e apague as
   cópias.

```python
# antes (rota)
@bp.route("/customers/<int:customer_id>")
def get_customer(customer_id):
    c = Customer.query.get(customer_id)
    data = c.to_dict()
    if c.open_balance > c.credit_limit and c.status != "blocked":
        data["over_limit"] = True
    else:
        data["over_limit"] = False
    return jsonify(data)

# depois
# models/customer.py
def is_over_limit(self):
    return self.open_balance > self.credit_limit and self.status not in BLOCKED_STATUSES

# controllers/customer_controller.py
def get_customer(customer_id):
    c = customer_service.get_or_404(customer_id)
    return jsonify({**c.to_dict(), "over_limit": c.is_over_limit()}), 200

# routes/invoice_routes.py
bp.add_url_rule("/customers/<int:customer_id>", view_func=customer_controller.get_customer)
```

**Verificar:** handlers de rota com poucas linhas; nenhuma regra duplicada.

---

## RF-08 — Estado global → instância criada no composition root
**Corrige:** AP-08, AP-11

1. Remova variáveis de módulo mutáveis (conexão, cache, contadores).
2. Conexão: por requisição (Flask: `g` + `teardown_appcontext`) ou criada no composition
   root e passada às camadas.
3. Cache/registro em memória que ninguém lê: remova. Se for necessário, vire instância
   injetada.

```python
# antes
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("app.db", check_same_thread=False)
    return db_connection

# depois (src/database.py)
import sqlite3
from flask import g, current_app

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_schema(get_db())
```

**Verificar:** busca por `global ` e por objetos de módulo mutados não encontra estado
compartilhado.

---

## RF-09 — Transação em operações com várias escritas
**Corrige:** AP-09

1. Agrupe as escritas relacionadas num bloco transacional: tudo é confirmado junto ou
   desfeito junto.
2. Faça as validações antes de escrever; re-cheque condições críticas (estoque, saldo) dentro
   da transação, de forma atômica (`UPDATE ... SET qty = qty - ? WHERE id = ? AND qty >= ?`).
3. Exclusão com filhos: exclua/desvincule os filhos na mesma transação (ou `ON DELETE
   CASCADE`/`cascade` do ORM).

```python
# antes — validação e escritas separadas, return no meio, commit só no fim
def create_invoice(db, customer_id, lines):
    for line in lines:
        if stock_of(db, line["sku"]) < line["qty"]:
            return {"error": "sem saldo"}           # escritas anteriores ficam pendentes
    cur = db.execute("INSERT INTO invoices (customer_id) VALUES (?)", (customer_id,))
    for line in lines:
        db.execute("INSERT INTO invoice_lines ...", (...))
        db.execute("UPDATE stock SET qty = qty - ? WHERE sku = ?", (line["qty"], line["sku"]))
    db.commit()                                      # falha no meio = estado parcial

# depois (sqlite3)
def create_invoice(db, customer_id, lines):
    total = sum(line["qty"] * line["unit_price"] for line in lines)
    with db:  # BEGIN ... COMMIT; ROLLBACK automático se qualquer escrita lançar exceção
        cur = db.execute("INSERT INTO invoices (customer_id, total) VALUES (?, ?)",
                         (customer_id, total))
        for line in lines:
            db.execute("INSERT INTO invoice_lines (invoice_id, sku, qty) VALUES (?, ?, ?)",
                       (cur.lastrowid, line["sku"], line["qty"]))
            updated = db.execute(
                "UPDATE stock SET qty = qty - ? WHERE sku = ? AND qty >= ?",
                (line["qty"], line["sku"], line["qty"])).rowcount
            if updated == 0:
                raise AppError(f"Saldo insuficiente para {line['sku']}")  # desfaz tudo
    return cur.lastrowid
```

```javascript
// antes — a segunda escrita falha e a primeira já foi gravada
db.run("INSERT INTO subscriptions ...", [a, p], function (err) {
  db.run("INSERT INTO charges ...", [this.lastID, amount], (err2) => {
    if (err2) return res.status(500).send("Erro");   // assinatura sem cobrança
  });
});

// depois (sqlite3 + promessas)
await run(db, "BEGIN");
try {
  const { lastID } = await run(db, "INSERT INTO subscriptions (account_id, plan_id) VALUES (?, ?)", [accountId, planId]);
  await run(db, "INSERT INTO charges (subscription_id, amount, status) VALUES (?, ?, ?)", [lastID, amount, status]);
  await run(db, "COMMIT");
} catch (err) {
  await run(db, "ROLLBACK");
  throw err;
}
```

**Verificar:** forçar falha na segunda escrita (ex.: dado inválido) não deixa a primeira gravada.

---

## RF-10 — N+1 → JOIN, eager loading ou GROUP BY
**Corrige:** AP-12

```python
# antes: 1 query por fatura + 1 por linha
for inv in invoices:
    lines = db.execute("SELECT * FROM invoice_lines WHERE invoice_id = ?", (inv["id"],)).fetchall()

# depois: uma query com JOIN e agrupamento em memória
rows = db.execute("""
    SELECT i.id, i.status, l.sku, l.qty, p.name AS product_name
    FROM invoices i
    LEFT JOIN invoice_lines l ON l.invoice_id = i.id
    LEFT JOIN products p ON p.id = l.product_id
    ORDER BY i.id
""").fetchall()

# contagens: um GROUP BY em vez de N COUNTs
counts = dict(db.execute("SELECT status, COUNT(*) FROM invoices GROUP BY status").fetchall())
```

```python
# ORM: eager loading
from sqlalchemy.orm import joinedload
invoices = db.session.scalars(select(Invoice).options(joinedload(Invoice.customer))).all()
```

**Verificar:** a quantidade de queries não cresce com o número de registros; o JSON de
saída é idêntico ao anterior (mesmas chaves e ordem dos itens).

---

## RF-11 — Error handler centralizado
**Corrige:** AP-14

1. Defina exceções de aplicação (`NotFoundError`, `ValidationError`) ou use as do framework.
2. Registre um handler global que converte exceções em respostas JSON padronizadas e loga o
   erro; erros inesperados viram 500 com mensagem genérica (sem `str(e)`).
3. Remova os `try/except` repetidos dos handlers.

```python
# antes — repetido em todo handler, devolvendo detalhes internos
def list_invoices():
    try:
        return jsonify(models.all_invoices()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500      # vaza SQL/caminhos; body ausente vira 500
```

```python
# depois — src/middlewares/error_handler.py
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

class AppError(Exception):
    status = 400
    def __init__(self, message, status=None):
        super().__init__(message)
        self.message = message
        if status:
            self.status = status

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app_error(err):
        return jsonify({"error": err.message}), err.status

    @app.errorhandler(HTTPException)
    def _http_error(err):
        return jsonify({"error": err.description}), err.code

    @app.errorhandler(Exception)
    def _unexpected(err):
        logging.getLogger(__name__).exception("Erro não tratado")
        return jsonify({"error": "Erro interno"}), 500
```

```javascript
// antes: db.all(sql, [], (err, rows) => { res.json(rows); });   // err ignorado
// depois — src/middlewares/errorHandler.js (último app.use)
module.exports = function errorHandler(err, req, res, next) {
  const status = err.status || 500;
  if (status >= 500) console.error(err);
  res.status(status).json({ error: status >= 500 ? "Erro interno" : err.message });
};
// handlers async: encaminhe erros com next(err) ou um wrapper asyncHandler
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
```

Use **o envelope de erro que o projeto já usava** (nomes de chave, flag de sucesso, idioma da
mensagem) — os exemplos acima usam `error` apenas como ilustração.

**Verificar:** nenhum `except:`/`catch` vazio; erro inesperado responde 500 genérico e o
detalhe aparece só no log.

---

## RF-12 — Validação extraída e reutilizada
**Corrige:** AP-15, AP-13

1. Centralize as regras de entrada de cada recurso numa função/schema (no controller ou num
   módulo de validação), usada por criação e atualização (com campos opcionais na
   atualização).
2. Cheque corpo nulo e tipos antes de comparar; entrada inválida → 400 com mensagem.
3. Reaproveite constantes da config (limites, valores válidos).

```python
# antes
data = request.get_json()
if data["priority"] < 1 or data["priority"] > 5: ...   # TypeError → 500 com string

# depois
def validate_invoice(data, partial=False):
    if not isinstance(data, dict):
        raise AppError("Dados inválidos")
    errors = []
    if not partial or "amount" in data:
        amount = data.get("amount")
        if not isinstance(amount, (int, float)) or amount < 0:
            errors.append("amount deve ser um número >= 0")
    if "status" in data and data["status"] not in VALID_STATUSES:
        errors.append("Status inválido")
    if errors:
        raise AppError("; ".join(errors))
    return data
```

Mantenha as mensagens de erro originais quando elas existirem (fazem parte do contrato).

**Verificar:** corpo vazio e tipo errado retornam 400; criação e atualização aplicam as
mesmas regras.

---

## RF-13 — Substituição de APIs deprecated
**Corrige:** AP-17

Aplique a coluna "Substituto moderno" da tabela de AP-17. Exemplos:

```python
# antes
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
invoice = Invoice.query.get(invoice_id)

# depois
from datetime import datetime, timezone
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)  # mantém datetimes naive já gravados
created_at = db.Column(db.DateTime, default=utcnow)
invoice = db.session.get(Invoice, invoice_id)
```

```javascript
// antes
const b = new Buffer(str);
const { pathname } = url.parse(req.url);
// depois
const b = Buffer.from(str);
const { pathname } = new URL(req.url, `http://${req.headers.host}`);
```

Ao trocar `utcnow()` por datetimes "aware", **mantenha a compatibilidade** com valores já
gravados e comparações (ex.: `replace(tzinfo=None)` como acima), para não mudar o formato
das datas na resposta.

**Verificar:** boot e validação sem warnings de depreciação dessas APIs; formato das datas
na resposta inalterado.

---

## RF-14 — Constantes nomeadas, logging e limpeza
**Corrige:** AP-18, AP-19, AP-20, AP-21

1. Mova números e listas de regra para constantes nomeadas na config (ou no model dono da
   regra) e use-as em todos os lugares.
2. Substitua `print`/`console.log` de eventos por logger configurado (`logging.getLogger`,
   ou um logger simples no Node); não registre dados pessoais nem segredos.
3. Remova imports, funções, variáveis e dependências do manifesto que não são usados.
4. Renomeie variáveis internas crípticas e as que sombreiam builtins; **não** renomeie
   campos do contrato HTTP.

```python
# antes
if revenue > 10000: discount = revenue * 0.1
elif revenue > 5000: discount = revenue * 0.05

# depois (config)
DISCOUNT_TIERS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))  # (faturamento mínimo, taxa)
# (model/service)
def discount_for(revenue):
    for threshold, rate in DISCOUNT_TIERS:
        if revenue > threshold:
            return revenue * rate
    return 0
```

**Verificar:** busca por `print(`/`console.log(` só encontra a mensagem de boot; nenhum
import sem uso.

---

## RF-15 — Callbacks aninhados → async/await
**Corrige:** AP-09, AP-14 (quando causados por callback hell)

1. Crie wrappers de Promise para a API de callback do driver (ou use a versão com Promise).
2. Reescreva o fluxo como sequência `await` dentro de `try/catch`, com transação (RF-09) e
   erros encaminhados ao error handler (RF-11).
3. Paralelize com `Promise.all` só o que é independente.

```javascript
// src/database.js
const run = (db, sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));
const get = (db, sql, params = []) => new Promise((resolve, reject) =>
  db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
const all = (db, sql, params = []) => new Promise((resolve, reject) =>
  db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));

// antes: db.get(..., (e1, a) => { db.get(..., (e2, b) => { db.run(..., function (e3) { ... }) }) })
// depois
async function subscribe(db, input) {
  const plan = await get(db, "SELECT * FROM plans WHERE id = ? AND active = 1", [input.planId]);
  if (!plan) throw new NotFoundError("Plano não encontrado");
  const account = await findOrCreateAccount(db, input);
  return createSubscription(db, account.id, plan);   // transação dentro (RF-09)
}
```

**Verificar:** nenhum callback com mais de 2 níveis; todo erro de banco chega ao error
handler.
