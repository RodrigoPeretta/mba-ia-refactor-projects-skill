# Anti-patterns Catalog — Fase 2

Catálogo usado para auditar o código. Cada entrada traz a **severidade-base**, **sinais de
detecção** acionáveis (o que buscar e o que ler em volta), **falsos positivos** a descartar
e a transformação do playbook que corrige (`RF-xx`, em `refactoring-playbook.md`).

## Escala de severidade

| Severidade | Quando usar (baseada em MVC e SOLID) |
|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: impede o funcionamento correto, expõe dados sensíveis (credenciais hardcoded, SQL injection, senha em claro) ou viola completamente a separação de responsabilidades (God Class com banco + regra + roteamento) |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e testes: regra de negócio pesada no controller/rota, acoplamento forte sem injeção de dependência, estado global mutável |
| **MEDIUM** | Padronização, duplicação, performance moderada: N+1, middleware inadequado, validação ausente, tratamento de erro inconsistente, APIs deprecated |
| **LOW** | Legibilidade: nomes ruins, magic numbers, código morto, logging improvisado |

**Ajuste de severidade**: parta da severidade-base. Suba um nível quando a ocorrência é
explorável sem autenticação ou afeta todos os registros; desça um nível quando é isolada,
sem exposição externa e de correção trivial. Todo ajuste é justificado na `Description`.
Nunca desça um CRITICAL de segurança (AP-01 a AP-04, AP-06) abaixo de HIGH.

## Como auditar

1. Para cada arquivo-fonte, rode as buscas dos sinais de **todas** as entradas (Grep com as
   regex sugeridas, adaptando à linguagem) e leia o contexto de cada ocorrência.
2. Confirme lendo as linhas: um sinal é só um candidato. Aplique a lista de falsos positivos.
3. Registre arquivo e linhas **exatos** (número da linha no arquivo atual).
4. Sinais estruturais (AP-05, AP-07, AP-11, AP-13) exigem leitura do arquivo inteiro,
   não só busca.

---

## CRITICAL

### AP-01 — SQL Injection (SQL montado com entrada externa)
- **Severidade-base:** CRITICAL
- **Sinais:**
  - Python: `cursor.execute(`/`db.execute(`/`text(` cujo argumento usa `+`, `%`, `.format(` ou
    f-string com variável. Regex: `execute\(\s*(f["']|["'].*["']\s*(\+|%)|.*\.format\()`.
  - JS/TS: `db.run|get|all|query|exec(` com template literal contendo `${` ou concatenação
    `+`. Regex: ``\.(run|get|all|query|exec)\(\s*(`[^`]*\$\{|["'][^"']*["']\s*\+)``.
  - ORM: `raw(`, `query(` ou `literal(` com string interpolada.
  - Ache a origem da variável: request (`request.args/json/form`, `req.body/params/query`),
    parâmetro de função chamada pelo controller, ou valor vindo do banco.
- **Falsos positivos:** concatenação só de **trechos constantes** (ex.: montar
  `" AND total >= ?"` e passar o valor na lista de parâmetros); nomes de tabela/coluna de uma
  allowlist fixa.
- **Fix:** RF-01

### AP-02 — Segredos e credenciais hardcoded
- **Severidade-base:** CRITICAL
- **Sinais:**
  - Atribuição literal a nomes como `SECRET_KEY`, `secret`, `password`, `passwd`, `pass`,
    `pwd`, `token`, `api_key`, `apiKey`, `private_key`, `access_key`, `client_secret`,
    `smtp_*`, `db_pass`, `dbPass`, `connection_string`.
    Regex: `(?i)(secret|passw(or)?d|pwd|pass|token|api_?key|private_?key|smtp\w*)\s*[:=]\s*["'][^"']{4,}["']`.
  - Prefixos de chaves reais: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xox[bp]-`.
  - URIs com credencial embutida: `://usuario:senha@`.
  - Segredo literal dentro de dicionário de config exportado.
- **Falsos positivos:** leitura de ambiente com default vazio (`os.environ.get("X")`,
  `process.env.X`); valores claramente de exemplo em `.env.example`; senhas de usuários de
  **seed** (avaliar em AP-03, não aqui).
- **Fix:** RF-02

### AP-03 — Senha em texto plano ou hash fraco
- **Severidade-base:** CRITICAL
- **Sinais:**
  - Senha recebida do request gravada direto no banco (INSERT/atribuição sem hash).
  - Login comparando senha no SQL (`WHERE ... senha = ?`/`password = '...'`) ou com `==`
    contra o valor salvo.
  - `hashlib.md5`, `hashlib.sha1`, `sha256` sem salt, `crypto.createHash('md5'|'sha1')`
    aplicados a senha.
  - Base64 ou função caseira usada como "hash" (`toString('base64')`, loops que concatenam).
  - Senha padrão silenciosa (`pwd || "123456"`).
  - Seeds com senhas em claro inseridas no banco.
- **Falsos positivos:** hash com `bcrypt`, `argon2`, `scrypt`, `pbkdf2`
  (`werkzeug.security.generate_password_hash`) com salt.
- **Fix:** RF-03

### AP-04 — Dado sensível exposto em resposta ou log
- **Severidade-base:** CRITICAL
- **Sinais:**
  - Serializer/`to_dict`/`toJSON`/dict de resposta incluindo `senha`, `password`, `hash`,
    `token`, `secret`, número de cartão, CPF.
  - Endpoint de saúde/status/debug devolvendo `secret_key`, credenciais, caminho do banco,
    flag de debug.
  - Log/`print`/`console.log` com cartão, senha, token ou chave de API.
  - Mensagem de exceção crua devolvida ao cliente contendo SQL ou caminhos (avaliar junto
    com AP-14; aqui só se expuser dado sensível).
- **Falsos positivos:** e-mail do próprio usuário na resposta do próprio cadastro.
- **Fix:** RF-04 (serialização), RF-02 (segredos), RF-14 (logs)

### AP-05 — God Class / God Module
- **Severidade-base:** CRITICAL
- **Sinais:**
  - Um arquivo ou classe com **3 ou mais** destas responsabilidades: conexão/DDL/seed do
    banco, queries, regra de negócio, validação de entrada, roteamento/registro de rotas,
    formatação de resposta, integração externa (pagamento, e-mail).
  - Um módulo cobrindo **vários domínios** (ex.: funções de 4 entidades diferentes no mesmo
    arquivo de "models").
  - Classe "Manager"/"Helper"/"Utils" com métodos de domínios distintos; método que
    registra rotas na mesma classe que abre a conexão com o banco.
- **Falsos positivos:** composition root que só **conecta** as camadas (cria app, registra
  blueprints/routers, injeta dependências), sem lógica.
- **Fix:** RF-06

### AP-06 — Endpoint administrativo, destrutivo ou de execução arbitrária sem autenticação
- **Severidade-base:** CRITICAL
- **Sinais:**
  - Rotas com `admin`, `reset`, `drop`, `query`, `exec`, `debug`, `internal`, relatórios
    financeiros, ou DELETE de recursos de terceiros, **sem** nenhuma verificação de
    identidade antes da ação.
  - Endpoint que executa SQL/comando recebido no corpo (`execute(body["sql"])`, `eval`,
    `exec`, `child_process`).
  - Token previsível (prefixo fixo + id do usuário, valor constante) e nenhuma rota que o
    valide.
  - Cadastro público que aceita o campo de papel/perfil (`role`, `tipo`, `is_admin`) vindo do
    corpo.
- **Falsos positivos:** rotas protegidas por decorator/middleware de auth aplicado no
  blueprint/router.
- **Fix:** RF-05

---

## HIGH

### AP-07 — Regra de negócio em controller/rota (fat controller)
- **Severidade-base:** HIGH
- **Sinais:**
  - Handler de rota com cálculos de domínio (totais, descontos, saldos, prazos, status),
    regras de transição de estado, decisões de aprovação, ou várias escritas coordenadas.
  - Handler com mais de ~30 linhas fazendo validação + regra + persistência + resposta.
  - Notificações/integrações disparadas de dentro do handler.
  - Lógica de domínio que existe no model (ex.: métodos `is_*`, `validate_*`) mas é
    **reimplementada** na rota.
  - O inverso também conta: "model" que decide regra de outro domínio e já monta resposta.
- **Falsos positivos:** handler que só lê parâmetros, chama um serviço e devolve a resposta.
- **Fix:** RF-07

### AP-08 — Estado global mutável
- **Severidade-base:** HIGH
- **Sinais:**
  - Variável de módulo reatribuída em função (`global x`; `let cache = {}` alterado em
    funções exportadas).
  - Conexão de banco singleton global compartilhada entre requisições/threads
    (`check_same_thread=False` + variável global).
  - Caches, contadores, listas de notificações em memória de módulo, sem limite e sem dono.
  - Primitivo exportado esperando ser "atualizado" por quem importa (cópia por valor).
- **Falsos positivos:** constantes imutáveis; objeto de extensão do framework criado uma vez
  e configurado no composition root (`db = SQLAlchemy()` + `init_app`).
- **Fix:** RF-08

### AP-09 — Múltiplas escritas sem transação
- **Severidade-base:** HIGH
- **Sinais:**
  - Sequência de INSERT/UPDATE/DELETE relacionados (cabeçalho + linhas + saldo; assinatura +
    cobrança) sem `BEGIN`/`commit`/`rollback` envolvendo todos, ou com `return` no meio
    deixando escritas pendentes.
  - Callbacks encadeados em que a falha de uma escrita não desfaz as anteriores.
  - Exclusão de registro pai sem tratar filhos (órfãos) ou com loop manual de exclusões.
  - Checagem e atualização separadas ("lê saldo" → "debita saldo") sem atomicidade.
- **Falsos positivos:** escrita única por requisição; ORM com unit of work em que o commit é
  único e há rollback no erro.
- **Fix:** RF-09

### AP-10 — Debug ligado ou bind aberto fixo no código
- **Severidade-base:** HIGH
- **Sinais:** `debug=True`, `DEBUG = True`, `app.run(... host="0.0.0.0" ...)` literais;
  `NODE_ENV` ignorado; stack trace enviado ao cliente; reloader ativo em execução padrão.
- **Falsos positivos:** debug lido de variável de ambiente com default `false`.
- **Fix:** RF-02

### AP-11 — Acoplamento forte sem injeção de dependência
- **Severidade-base:** HIGH
- **Sinais:**
  - Regra de negócio importando e instanciando infraestrutura diretamente (abrir conexão,
    cliente SMTP, gateway) em vez de recebê-la.
  - Controllers chamando SQL/driver diretamente, sem model/repositório.
  - Módulos importados como `import models` / `require('./manager')` e usados como
    namespace global de funções com efeitos colaterais.
- **Falsos positivos:** uso do objeto `db` do ORM dentro da camada Model.
- **Fix:** RF-08, RF-06

---

## MEDIUM

### AP-12 — N+1 queries e agregação em loop
- **Severidade-base:** MEDIUM
- **Sinais:**
  - Query dentro de `for`/`forEach`/`map` que percorre o resultado de outra query.
  - ORM: acesso a relacionamento lazy dentro de loop (`len(c.invoices)`, `item.owner.name`),
    `Model.query.get(x.fk)` em loop.
  - Vários `COUNT`/`SUM` separados sobre a mesma tabela que caberiam num `GROUP BY`.
  - Carregar a tabela inteira (`.all()`/`SELECT *`) para contar ou filtrar em memória.
- **Falsos positivos:** loop com número fixo e pequeno de iterações sobre constantes.
- **Fix:** RF-10

### AP-13 — Duplicação de lógica (e cópias divergentes)
- **Severidade-base:** MEDIUM
- **Sinais:**
  - Blocos de 5+ linhas praticamente iguais em funções diferentes (mapeamento row → dict,
    validações de criação/atualização, cálculos).
  - Duas funções que fazem o mesmo com uma diferença de filtro.
  - Helpers/constantes/métodos de model **existentes e não usados** enquanto a lógica é
    reescrita inline.
  - Cópias que já divergiram (uma valida campo que a outra não valida).
- **Falsos positivos:** estruturas parecidas com regras de negócio realmente diferentes.
- **Fix:** RF-07, RF-12

### AP-14 — Tratamento de erro genérico ou não centralizado
- **Severidade-base:** MEDIUM
- **Sinais:**
  - Python: `except:` sem tipo; `except Exception as e: return ... str(e)`; o mesmo
    `try/except` copiado em todos os handlers.
  - JS: `(err, ...) => {` sem checar `err`; `catch (e) {}` vazio; respostas de erro em
    formatos diferentes (`text/plain` aqui, JSON ali).
  - Ausência de error handler global (`@app.errorhandler`, middleware `(err, req, res, next)`).
  - Erro de cliente (body ausente, tipo errado) virando 500.
- **Falsos positivos:** `try/except` específico que converte uma exceção conhecida em
  resposta de domínio.
- **Fix:** RF-11

### AP-15 — Validação de entrada ausente ou inconsistente
- **Severidade-base:** MEDIUM
- **Sinais:** acesso a `request.get_json()`/`req.body` sem checar nulo; comparação numérica
  sem checar tipo (`priority < 1` com string); campos obrigatórios não verificados; formato
  de e-mail/cartão/data não validado; regras diferentes entre criar e atualizar.
- **Falsos positivos:** validação feita por schema (marshmallow, pydantic, joi, zod) aplicado
  antes do handler.
- **Fix:** RF-12

### AP-16 — Configuração fixa no código / middleware inadequado
- **Severidade-base:** MEDIUM
- **Sinais:** porta, host, caminho/URI do banco, URLs externas literais no código; `CORS(app)`
  ou `cors()` sem `origins`; banco `:memory:` fixo sem opção de persistência;
  middleware registrado para tudo sem necessidade.
- **Falsos positivos:** valor default usado só quando a variável de ambiente não existe.
- **Fix:** RF-02

### AP-17 — APIs deprecated
- **Severidade-base:** MEDIUM (HIGH se a API já foi **removida** na versão declarada no
  manifesto ou na versão do runtime; LOW se for apenas estilo legado sem previsão de remoção)
- **Sinais:** busque as chamadas da tabela abaixo. Registre cada uso com arquivo e linhas e
  indique o substituto.

| Ecossistema | Obsoleto | Substituto moderno |
|---|---|---|
| Python ≥ 3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()` (inclusive como `default=datetime.utcnow` em colunas) | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` |
| SQLAlchemy ≥ 2.0 / Flask-SQLAlchemy ≥ 3.0 | `Model.query.get(id)`, `session.query(M).get(id)` | `db.session.get(M, id)` |
| SQLAlchemy ≥ 2.0 | `engine.execute(...)`, string SQL crua sem `text()` | `with engine.connect() as c: c.execute(text(...))` |
| Flask ≥ 2.3 | `@app.before_first_request` | inicialização no app factory / `with app.app_context()` |
| Flask ≥ 2.2/3.0 | `app.json_encoder`, `flask.json.JSONEncoder`, `flask.escape`, `flask.Markup` | `app.json` (provider), `markupsafe.escape`, `markupsafe.Markup` |
| Werkzeug ≥ 2.1 | `safe_str_cmp` | `hmac.compare_digest` |
| Python ≥ 3.12/3.13 | `distutils`, `imp`, `cgi`, `pkg_resources`, `collections.Mapping` | `setuptools`/`packaging`, `importlib`, `email`/`urllib.parse`, `importlib.metadata`, `collections.abc.Mapping` |
| Python | `logging.warn`, `asyncio.get_event_loop()` sem loop ativo | `logging.warning`, `asyncio.run()` |
| Node.js | `new Buffer(x)`, `Buffer(x)` | `Buffer.from(x)`, `Buffer.alloc(n)` |
| Node.js | `url.parse()`, `querystring` | `new URL()`, `URLSearchParams` |
| Node.js | `fs.exists()`, `util.isArray()`/`util.isDate()`… | `fs.existsSync()`/`fs.promises.access()`, `Array.isArray()`… |
| Node.js | `crypto.createCipher()`/`createDecipher()` | `crypto.createCipheriv()`/`createDecipheriv()` |
| Express 4/5 | `req.param()`, `res.send(status)`, `res.json(status, body)`, `app.del()` | `req.params`/`req.query`/`req.body`, `res.sendStatus()`, `res.status(s).json(b)`, `app.delete()` |
| Express ≥ 4.16 | pacote `body-parser` só para JSON/urlencoded | `express.json()`, `express.urlencoded()` |
| JS | `String.prototype.substr()`, `getYear()` | `slice()`/`substring()`, `getFullYear()` |
| Mongoose ≥ 7 | API de callbacks (`Model.find(q, cb)`) | Promises/`await` |

  Além da tabela: dependências diretas sabidamente descontinuadas (ex.: `request`) e
  pacotes marcados como deprecated pelo gerenciador de pacotes. Avisos de depreciação que
  só aparecem ao instalar ou rodar são coletados na Fase 3 e listados em `Pending`.
- **Falsos positivos:** o mesmo nome de método em outra biblioteca (ex.: `dict.get`,
  `Map.get`) — confirme que é a API da tabela.
- **Fix:** RF-13

---

## LOW

### AP-18 — Magic numbers e strings mágicas
- **Severidade-base:** LOW
- **Sinais:** literais numéricos de regra (limites, faixas de desconto, tamanhos mínimos,
  dias) e listas de valores válidos (status, papéis, categorias) escritos inline, ainda mais
  quando repetidos em vários lugares.
- **Falsos positivos:** `0`, `1`, `-1`, `100` em cálculos óbvios; códigos HTTP.
- **Fix:** RF-14

### AP-19 — Código morto, imports e dependências não usados
- **Severidade-base:** LOW
- **Sinais:** `import` cujo nome não aparece no restante do arquivo; funções/classes/
  serviços nunca chamados; variáveis exportadas não importadas; dependências do manifesto
  sem nenhum import.
- **Falsos positivos:** imports com efeito colateral necessário (registro de models para o
  ORM, por exemplo `from models import *` antes do `create_all`).
- **Fix:** RF-14

### AP-20 — `print`/`console.log` como logging
- **Severidade-base:** LOW (MEDIUM se registrar dado pessoal — e AP-04 se registrar segredo)
- **Sinais:** `print(` / `console.log(` em handlers, models e serviços para registrar
  eventos ou erros; ausência de `logging`/logger configurado.
- **Falsos positivos:** mensagem única de inicialização no entry point; scripts de CLI/seed.
- **Fix:** RF-14

### AP-21 — Nomes crípticos ou que sombreiam builtins
- **Severidade-base:** LOW
- **Sinais:** variáveis de uma letra fora de laços curtos (`x`, `d`, `t`); abreviações
  sem vogais no contrato ou no código (`nm`, `qtd`, `addr`); parâmetros chamados `id`, `type`, `list`, `input` (Python);
  `self = this` misturado com `this`; código verboso (`if x: return True else: return
  False`, `type(x) == list`).
- **Falsos positivos:** nomes curtos idiomáticos (`i`, `k, v`, `req`, `res`, `db`).
  Nomes de campos do **contrato HTTP** não são renomeados (romperia clientes) — o
  finding recomenda renomear só as variáveis internas.
- **Fix:** RF-14

---

## Resumo do catálogo

| ID | Anti-pattern | Severidade-base | Fix |
|---|---|---|---|
| AP-01 | SQL Injection | CRITICAL | RF-01 |
| AP-02 | Segredos hardcoded | CRITICAL | RF-02 |
| AP-03 | Senha em claro / hash fraco | CRITICAL | RF-03 |
| AP-04 | Dado sensível exposto | CRITICAL | RF-04 |
| AP-05 | God Class / God Module | CRITICAL | RF-06 |
| AP-06 | Endpoint admin/destrutivo sem auth | CRITICAL | RF-05 |
| AP-07 | Regra de negócio em controller/rota | HIGH | RF-07 |
| AP-08 | Estado global mutável | HIGH | RF-08 |
| AP-09 | Múltiplas escritas sem transação | HIGH | RF-09 |
| AP-10 | Debug / bind aberto no código | HIGH | RF-02 |
| AP-11 | Acoplamento sem injeção de dependência | HIGH | RF-08, RF-06 |
| AP-12 | N+1 / agregação em loop | MEDIUM | RF-10 |
| AP-13 | Duplicação de lógica | MEDIUM | RF-07, RF-12 |
| AP-14 | Erro genérico / não centralizado | MEDIUM | RF-11 |
| AP-15 | Validação ausente | MEDIUM | RF-12 |
| AP-16 | Configuração fixa / middleware inadequado | MEDIUM | RF-02 |
| AP-17 | APIs deprecated | MEDIUM | RF-13 |
| AP-18 | Magic numbers/strings | LOW | RF-14 |
| AP-19 | Código morto / imports não usados | LOW | RF-14 |
| AP-20 | print/console.log como logging | LOW | RF-14 |
| AP-21 | Nomes crípticos | LOW | RF-14 |

Callbacks profundamente aninhados (≥ 3 níveis) que dificultam transação e tratamento de
erro são registrados dentro de AP-09 ou AP-14, conforme o efeito, e corrigidos com RF-15.
