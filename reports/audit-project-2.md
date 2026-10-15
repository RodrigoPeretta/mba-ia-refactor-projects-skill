# ARCHITECTURE AUDIT REPORT

- **Project:** ecommerce-api-legacy
- **Stack:** JavaScript (Node.js) + Express ^4.18.2
- **Files:** 3 analyzed | ~180 lines of code
- **Architecture:** Monolítica

## Summary

CRITICAL: 5 | HIGH: 5 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Endpoints administrativo e destrutivo sem autenticação
- **ID:** AP-06
- **File:** `src/AppManager.js:80-129, 131-137`
- **Description:** `GET /api/admin/financial-report` devolve faturamento por curso e nome de todos os alunos, e `DELETE /api/users/:id` apaga qualquer usuário pelo id; nenhum dos dois faz qualquer verificação de identidade antes da ação (não existe middleware de auth na aplicação).
- **Impact:** Qualquer cliente anônimo lê dados financeiros e pessoais de todos os alunos e apaga contas arbitrárias, deixando matrículas e pagamentos órfãos.
- **Recommendation:** Manter as duas rotas e protegê-las com token de administrador lido do ambiente (fechadas por padrão quando o token não estiver configurado), via middleware aplicado no router (RF-05).

### [CRITICAL] Segredos e credenciais hardcoded no objeto de config
- **ID:** AP-02
- **File:** `src/utils.js:1-7`
- **Description:** O objeto `config` exportado contém `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` (prefixo de chave real de produção) e `smtpUser` literais.
- **Impact:** Qualquer pessoa com acesso ao repositório obtém a chave do gateway de pagamento e a senha do banco; rotacionar exige alterar código e fazer deploy.
- **Recommendation:** Mover para variáveis de ambiente lidas por um módulo de configuração, sem defaults secretos, e documentar em `.env.example` (RF-02).

### [CRITICAL] Número do cartão e chave do gateway gravados em log
- **ID:** AP-04
- **File:** `src/AppManager.js:45`
- **Description:** `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` escreve o número completo do cartão (PAN) e a chave `pk_live_` em stdout a cada checkout.
- **Impact:** Vazamento de dados de cartão e de credencial para qualquer sistema de coleta de logs (violação direta de PCI-DSS).
- **Recommendation:** Remover o cartão e a chave do log; se necessário, registrar apenas os 4 últimos dígitos mascarados via logger (RF-14, RF-02).

### [CRITICAL] Hash de senha caseiro, senha padrão silenciosa e seed em texto plano
- **ID:** AP-03
- **File:** `src/utils.js:17-23`; `src/AppManager.js:18, 68`
- **Description:** `badCrypto` faz um loop que concatena os 2 primeiros caracteres de `Buffer.from(pwd).toString('base64')` e corta em 10 caracteres — reversível, sem salt e com colisões (senhas com o mesmo prefixo geram o mesmo "hash"). O checkout usa `badCrypto(p || "123456")`, criando conta com senha padrão quando `pwd` não vem, e o seed insere `pass = '123'` em claro.
- **Impact:** Quem tiver acesso ao banco recupera ou forja senhas trivialmente; contas criadas sem senha ficam acessíveis com `123456`.
- **Recommendation:** Substituir por `crypto.scrypt` com salt aleatório (módulo nativo) e gerar o hash também no seed; não aplicar senha padrão (RF-03).

### [CRITICAL] God Class `AppManager`
- **ID:** AP-05
- **File:** `src/AppManager.js:4-139`
- **Description:** A mesma classe abre a conexão (`new sqlite3.Database(':memory:')`, linha 7), cria o schema e o seed (10-23), registra as rotas (25-137), executa SQL, decide a regra de pagamento (46), cria usuário, matrícula, pagamento e auditoria, monta o relatório financeiro e formata as respostas.
- **Impact:** Impossível testar regra de negócio sem subir Express e banco; qualquer mudança em uma responsabilidade arrisca as outras.
- **Recommendation:** Separar em config, conexão/schema/seed, models por entidade, serviços de checkout/relatório, controllers, rotas e composition root (RF-06).

### [HIGH] Regra de negócio dentro dos handlers de rota
- **ID:** AP-07
- **File:** `src/AppManager.js:28-78, 80-129`
- **Description:** O handler de checkout (50 linhas) decide aprovação do pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`), cria usuário, matrícula, pagamento e auditoria; o handler do relatório calcula a receita (`courseData.revenue += payment.amount` apenas quando `status === 'PAID'`).
- **Impact:** Regras de pagamento e faturamento não reutilizáveis nem testáveis isoladamente.
- **Recommendation:** Extrair `CheckoutService` e `ReportService`; os controllers só leem a requisição, chamam o serviço e respondem (RF-07).

### [HIGH] Checkout com várias escritas sem transação
- **ID:** AP-09
- **File:** `src/AppManager.js:50-61, 69-71`
- **Description:** Inserção de usuário, matrícula, pagamento e auditoria são feitas em callbacks encadeados (4 níveis) sem `BEGIN/COMMIT/ROLLBACK`; se o INSERT de `payments` falhar, a matrícula já gravada permanece; o erro do INSERT em `audit_logs` (57) é ignorado.
- **Impact:** Matrículas sem pagamento e usuários criados por checkouts que falharam deixam o banco inconsistente.
- **Recommendation:** Executar o fluxo em uma transação única com rollback no erro, reescrito com `async/await` (RF-09, RF-15).

### [HIGH] Exclusão de usuário deixa matrículas e pagamentos órfãos
- **ID:** AP-09
- **File:** `src/AppManager.js:131-137`
- **Description:** `DELETE FROM users WHERE id = ?` não trata `enrollments` e `payments` do usuário — a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco".
- **Impact:** Registros órfãos; o relatório financeiro passa a mostrar `Unknown` com receita de usuário inexistente.
- **Recommendation:** Excluir pagamentos, matrículas e o usuário na mesma transação (RF-09).

### [HIGH] Estado global mutável em módulo de utilitários
- **ID:** AP-08
- **File:** `src/utils.js:9-15, 25`
- **Description:** `globalCache` é um objeto de módulo, sem limite nem dono, alterado por `logAndCache` a cada checkout (`AppManager.js:59`) e exportado diretamente.
- **Impact:** Crescimento ilimitado de memória e estado compartilhado invisível entre requisições; impossível isolar em testes.
- **Recommendation:** Encapsular o cache em uma instância injetada no serviço (com dono e limite) ou removê-lo, já que nada o lê (RF-08).

### [HIGH] Acoplamento direto ao driver, sem injeção de dependência
- **ID:** AP-11
- **File:** `src/AppManager.js:1, 7, 37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133`
- **Description:** A classe instancia o driver `sqlite3` no construtor e os handlers chamam `this.db.get/run/all` diretamente com SQL inline; não há model/repositório nem forma de injetar outra conexão.
- **Impact:** Trocar o banco ou testar com banco isolado exige reescrever os handlers.
- **Recommendation:** Criar a conexão no composition root e injetá-la em models por entidade, usados pelos serviços (RF-08, RF-06).

### [MEDIUM] N+1 queries no relatório financeiro
- **ID:** AP-12
- **File:** `src/AppManager.js:83-106`
- **Description:** `SELECT * FROM courses`, depois um `SELECT * FROM enrollments` por curso e, por matrícula, um `SELECT ... FROM users` e um `SELECT ... FROM payments` — 1 + C + 2·E queries.
- **Impact:** Tempo de resposta cresce linearmente com matrículas; a ordem dos itens depende da ordem de chegada dos callbacks.
- **Recommendation:** Uma query com `LEFT JOIN` de courses → enrollments → users → payments e agregação em memória em ordem determinística (RF-10).

### [MEDIUM] Tratamento de erro ignorado e não centralizado
- **ID:** AP-14
- **File:** `src/AppManager.js:38, 57, 92-93, 104, 106, 133-135`
- **Description:** O `err` é ignorado nos callbacks das linhas 57, 92, 104, 106 e 133 (em 92, um erro faz `enrollments.length` lançar `TypeError` e derrubar o processo); na 38 um erro de banco vira 404 "Curso não encontrado"; o DELETE sempre responde sucesso. Erros saem como `text/plain` e sucessos como JSON; não há middleware `(err, req, res, next)`.
- **Impact:** Falhas silenciosas, possível queda do servidor e respostas de erro inconsistentes.
- **Recommendation:** Propagar erros com `async/await` para um error handler central que preserve os status e mensagens atuais (RF-11, RF-15).

### [MEDIUM] Validação de entrada ausente no checkout e no DELETE
- **ID:** AP-15
- **File:** `src/AppManager.js:29-35, 132`
- **Description:** O checkout só verifica presença de `usr`, `eml`, `c_id` e `card`; não valida tipo (ex.: `card` numérico faria `cc.startsWith` lançar `TypeError` → 500), formato de e-mail, formato do cartão, nem `pwd`. O `:id` do DELETE não é validado como inteiro.
- **Impact:** Entradas inválidas viram 500 ou registros inconsistentes.
- **Recommendation:** Validador dedicado para o corpo do checkout e para o id, respondendo 400 (RF-12).

### [MEDIUM] Configuração fixa no código
- **ID:** AP-16
- **File:** `src/utils.js:6`; `src/AppManager.js:7`
- **Description:** Porta `3000` literal e banco `:memory:` fixo, sem opção de ambiente.
- **Impact:** Não é possível mudar porta ou persistir o banco sem editar código.
- **Recommendation:** Ler `PORT` e `DB_PATH` do ambiente com defaults iguais aos atuais (RF-02).

### [LOW] Código morto, exports e config não usados
- **ID:** AP-19
- **File:** `src/AppManager.js:2`; `src/utils.js:2-3, 5, 10, 25`
- **Description:** `totalRevenue` é importado em `AppManager.js` e nunca usado (e o primitivo exportado nunca é atualizado); `globalCache` é exportado sem importador; `config.dbUser`, `config.dbPass` e `config.smtpUser` não são lidos em lugar nenhum; o cache escrito por `logAndCache` nunca é lido.
- **Impact:** Ruído e falsa impressão de funcionalidades (receita total, SMTP) inexistentes.
- **Recommendation:** Remover os itens não usados (RF-14).

### [LOW] Strings e números mágicos de regra
- **ID:** AP-18
- **File:** `src/AppManager.js:21, 46, 48, 54, 108`; `src/utils.js:19`
- **Description:** Status `'PAID'`/`'DENIED'` repetidos inline; regra de aprovação pelo prefixo `"4"` do cartão literal; `10000` iterações sem significado no "hash".
- **Impact:** Risco de divergência ao alterar um status ou a regra em um só lugar.
- **Recommendation:** Constantes nomeadas para status de pagamento e prefixo aprovado (RF-14).

### [LOW] `console.log` como logging
- **ID:** AP-20
- **File:** `src/utils.js:13`
- **Description:** `logAndCache` usa `console.log("[LOG] Salvando no cache: ...")` como log de evento, sem logger configurado (o log da linha 45 de `AppManager.js` está no finding AP-04; o de inicialização em `app.js:13` é falso positivo).
- **Impact:** Sem níveis nem controle de saída.
- **Recommendation:** Logger mínimo centralizado (RF-14).

### [LOW] Nomes crípticos e `self = this` misturado com `this`
- **ID:** AP-21
- **File:** `src/AppManager.js:26, 29-33, 52, 54, 57`; `src/utils.js:17`
- **Description:** Variáveis `u`, `e`, `p`, `cid`, `cc`, `enrId`; `const self = this` usado junto com `this` (que muda de significado dentro de `function(err)` para expor `lastID`); função chamada `badCrypto`. Os campos do contrato (`usr`, `eml`, `pwd`, `c_id`, `card`) são preservados.
- **Impact:** Leitura difícil e risco de erro com o `this` dinâmico.
- **Recommendation:** Renomear apenas variáveis internas e eliminar `self` com `async/await` (RF-14, RF-15).

## Deprecated APIs

Nenhuma API deprecated encontrada. Verificado: `Buffer` (usa `Buffer.from`, forma moderna), APIs de URL/querystring/fs/util/crypto (não usadas), APIs do Express 4 (`req.param`, `res.send(status)`, `res.json(status, body)`, `app.del`, `body-parser` — nenhuma usada; JSON via `express.json()`), `substr`/`getYear` (não usados) e as dependências diretas `express ^4.18.2` (lock 4.22.1) e `sqlite3 ^5.1.6` (lock 5.1.7), nenhuma marcada como deprecated. O `package-lock.json` marca como deprecated apenas dependências transitivas da cadeia de build do `sqlite3` (ex.: `glob`, `tar`, `rimraf`, `inflight`); os avisos de instalação serão coletados na Fase 3.

---

**Total: 18 findings**

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
