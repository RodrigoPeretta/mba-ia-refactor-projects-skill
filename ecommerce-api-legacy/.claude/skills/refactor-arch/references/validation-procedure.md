# Validation Procedure — Fase 3

Como provar, **executando**, que a aplicação refatorada se comporta como a original. O
mesmo roteiro roda duas vezes: na aplicação original (etapas 1–5, antes de qualquer
mudança) e na refatorada (etapas 6–9). Use apenas ferramentas universais: o shell, o
runtime do projeto e `curl`.

Artefatos (todos em `.refactor-arch/`):
- `behavior-before.md` — resultado na aplicação original
- `validation-after.md` — resultado na refatorada + comparação
- `requests/` — corpos JSON usados nas requisições
- `server-before.log`, `server-after.log` — saída do servidor

---

## Etapa 1 — Preparar o ambiente (isolado, só se faltar)

Detecte o sistema: `uname -s` (Linux/Darwin) ou variável `OS=Windows_NT` / `uname` com
`MINGW`/`MSYS` (Windows com Git Bash).

| Stack | Se faltar | Comando de Python/Node a usar |
|---|---|---|
| Python | `.venv/` → `python -m venv .venv` e `<py> -m pip install -r requirements.txt` (ou `pip install .` com `pyproject.toml`) | `<py>` = `.venv/Scripts/python.exe` (Windows) ou `.venv/bin/python` (POSIX) |
| Node | `node_modules/` → `npm install` (ou `npm ci` se houver lockfile e ele for consistente) | `npm start` / `node <main>` |

Nunca instale nada globalmente. Anote os avisos de depreciação emitidos pelo instalador
(ex.: `npm warn deprecated ...`) para a seção `Pending` do resumo.

## Etapa 2 — Estado do banco

1. Pelo perfil da Fase 1, identifique onde o banco fica. Para SQLite em arquivo, o caminho
   real pode diferir do literal (ex.: Flask-SQLAlchemy resolve `sqlite:///arquivo.db` para
   `instance/arquivo.db`) — confirme após o primeiro boot procurando o `*.db` criado.
2. Se o arquivo já existir antes da validação, **mova-o** para `.refactor-arch/db-backup/`
   (ele será restaurado ao final). Assim as duas medições partem do mesmo estado.
3. Execute o preparo documentado (ex.: script de seed) quando o projeto exigir. Banco em
   memória ou criado no boot não precisa de preparo.

## Etapa 3 — Subir a aplicação

1. Confirme que a porta está livre:
   - Windows: `netstat -ano | findstr :<PORTA> | findstr LISTENING` (vazio = livre)
   - POSIX: `lsof -iTCP:<PORTA> -sTCP:LISTEN` ou `ss -ltn "sport = :<PORTA>"`
   Se estiver ocupada por processo que você não iniciou, **pare e avise o usuário**.
2. Suba **em background** com o comando de execução do projeto, redirecionando a saída
   para o log. Na refatorada, defina as variáveis de teste:
   - `ADMIN_TOKEN=refactor-arch-validation` (para exercitar rotas administrativas)
   - `DEBUG=false`
   - Python: `PYTHONWARNINGS=default` (expõe warnings de depreciação no log)
   Exemplo: `PYTHONWARNINGS=default <py> app.py > .refactor-arch/server-before.log 2>&1 &`
3. Polling até responder (no máximo ~30 s): `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<PORTA>/<rota GET simples>`
   repetido a cada 1 s. Se não subir, leia o log, registre o erro e trate como falha de boot.

## Etapa 4 — Roteiro de requisições

Monte o roteiro a partir do **inventário de endpoints da Fase 1** — todos os endpoints entram.

1. **Corpo das requisições**, em ordem de preferência: exemplos do próprio projeto (`.http`,
   README, coleções) → campos obrigatórios lidos nas validações do código → valores
   plausíveis do domínio. Grave cada corpo em `.refactor-arch/requests/<passo>.json` e envie
   com `--data @arquivo` (evita problemas de aspas no shell).
2. **IDs**: use IDs que existem no seed para leituras; para atualizar/excluir, prefira o
   registro **criado pelo próprio roteiro** (capture o id da resposta da criação).
3. **Ordem**: leituras → criações → atualizações → leituras dependentes → exclusões →
   rotas destrutivas globais (reset, limpeza) **por último**.
4. Inclua pelo menos um caso de erro esperado por recurso (ex.: id inexistente → 404;
   corpo inválido → 400) para provar que o tratamento de erro continua correto.
5. Comando por passo:
   ```bash
   curl -s -o .refactor-arch/tmp/<passo>.out -w "%{http_code}" -X <MÉTODO> \
        -H "Content-Type: application/json" [-H "X-Admin-Token: $ADMIN_TOKEN"] \
        [--data @.refactor-arch/requests/<passo>.json] http://127.0.0.1:<PORTA><rota>
   ```
6. Para cada passo registre um `BehaviorRecord`: `step`, `method`, `path`, `request`
   (headers relevantes + arquivo do corpo), `status`, `shape` (tipo do corpo e chaves de
   nível superior; para listas, as chaves do primeiro item), `note`.

## Etapa 5 — Gravar `behavior-before.md` e encerrar

```markdown
# Behavior Before Refactoring
Command: <comando> | Port: <porta> | Date: <data>

| Step | Method | Path | Request | Status | Shape | Note |
|---|---|---|---|---|---|---|
| 1 | GET | /items | — | 200 | object: data, success | — |
| 2 | POST | /items | requests/02.json | 201 | object: data(id), success | id criado = 11 |
```

Depois **encerre o servidor** (Etapa 10) e confirme a porta livre antes de refatorar.

## Etapa 6 — Reinicializar o estado

Remova o banco gerado pela medição "antes" (o arquivo SQLite criado, não o backup) e refaça
o preparo da Etapa 2, para que a medição "depois" parta do mesmo estado inicial.

## Etapa 7 — Subir a aplicação refatorada

Mesmo procedimento da Etapa 3, com o **comando de execução original** e as variáveis de
teste. O log vai para `server-after.log`. Falha de boot = corrigir antes de seguir.

## Etapa 8 — Repetir o roteiro

Execute **os mesmos passos**, na mesma ordem e com os mesmos corpos. Para cada rota que
passou a exigir token, rode o passo duas vezes: sem o header (esperado 403) e com o header
(esperado o comportamento original).

**Rotas protegidas por token de sessão (RF-16).** Antes delas, faça login com **dois**
usuários do seed (A e B) e capture os tokens (`token_A`, `token_B`); envie com
`-H "Authorization: Bearer <token>"`. Para cada rota de escrita protegida sobre um recurso
de A, rode:

| Variante | Esperado |
|---|---|
| sem `Authorization` | 401 |
| token adulterado (ex.: último caractere trocado) | 401 |
| `token_B` (outro usuário, não admin) | 403 |
| `token_A` (dono) | comportamento original |
| admin (`X-Admin-Token` ou token de usuário admin) | comportamento original |

Inclua também a tentativa do **dono** de alterar campo privilegiado (papel/ativo) → 403.
As variantes de ataque vêm antes da variante que altera ou exclui o recurso, para que ele
ainda exista. Registre cada variante como um passo próprio.

## Etapa 9 — Gravar `validation-after.md` e comparar

```markdown
# Validation After Refactoring
Command: <comando> | Port: <porta> | Date: <data>
Boot: OK (sem erros no log)

| Step | Method | Path | Before | After | Shape | Result | Note |
|---|---|---|---|---|---|---|---|
| 1 | GET | /items | 200 | 200 | igual | OK | — |
| 7 | GET | /items/1 | 200 | 200 | sem `password` | CHANGED | campo sensível removido (AP-04) |
| 9 | POST | /admin/reset | 200 | 403 / 200 com token | igual | CHANGED | rota protegida (AP-06) |

Summary: OK <a> | CHANGED <b> | REGRESSION <c>
Warnings in server log: <nenhum | lista>
```

Classificação:
- **OK** — mesmo status e mesma forma (ignorar valores voláteis: ids, datas, hashes, ordem
  de chaves).
- **CHANGED** — diferença causada por uma correção listada nas guidelines (campo sensível
  removido, rota protegida, 500 de entrada inválida que virou 4xx, erro com corpo JSON
  padronizado). Cada CHANGED vai para `Contract Changes` no resumo.
- **REGRESSION** — qualquer outra diferença, falha de conexão ou erro no log. Corrija e
  repita as Etapas 6–9.

## Etapa 10 — Encerrar processos (sempre, inclusive em falha)

Servidores com auto-reload/debug criam um **processo filho** que mantém a porta aberta
mesmo depois que o processo iniciado termina. Encerre pela porta e pela árvore:

- **Windows (Git Bash ou PowerShell)**:
  1. PID do processo que escuta: `netstat -ano | findstr :<PORTA> | findstr LISTENING`
     (última coluna).
  2. `taskkill /T /F /PID <pid>` (no Git Bash: `taskkill //T //F //PID <pid>`).
  3. Repita 1–2 até não haver mais listener; encerre também o job em background que você
     iniciou.
  4. Se ainda sobrar processo, liste por linha de comando e encerre os que apontam para o
     projeto: `powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*<caminho-do-projeto>*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"`
- **POSIX**: `kill <pid>` do job; depois `lsof -tiTCP:<PORTA> -sTCP:LISTEN | xargs -r kill`;
  se persistir, `pkill -f "<comando de execução>"`.

Confirme a porta livre (Etapa 3.1). Por fim, apague o banco gerado na validação, restaure
o backup de `.refactor-arch/db-backup/` se houver, e remova `.refactor-arch/tmp/`.
