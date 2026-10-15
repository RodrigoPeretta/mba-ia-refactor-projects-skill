# ARCHITECTURE AUDIT REPORT

- **Project:** code-smells-project
- **Stack:** Python + Flask
- **Files:** 4 analyzed | ~780 lines of code
- **Architecture:** Parcialmente em camadas

## Summary

CRITICAL: 7 | HIGH: 5 | MEDIUM: 6 | LOW: 3

## Findings

### [CRITICAL] SQL Injection por concatenação de strings em todas as queries
- **ID:** AP-01
- **File:** `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299`
- **Description:** Todas as queries do módulo de dados são montadas com `+` a partir de valores vindos do request: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (login), `"... nome LIKE '%" + termo + "%'"` (busca, vindo de `request.args["q"]`), `"UPDATE pedidos SET status = '" + novo_status + "'"` e os INSERT/UPDATE de produtos e usuários com `nome`, `descricao`, `categoria`, `email`. Nenhuma usa parâmetros (`?`).
- **Impact:** Explorável sem autenticação: `email = "admin@loja.com' --"` no `POST /login` autentica como admin sem senha; a busca `GET /produtos/busca?q=` permite `UNION SELECT` para extrair a tabela `usuarios` (com senhas); campos de texto do cadastro de produto permitem alterar ou apagar dados.
- **Recommendation:** Usar queries parametrizadas (`cursor.execute("... WHERE id = ?", (id,))`) em todos os pontos; na busca dinâmica concatenar só trechos constantes e passar os valores na lista de parâmetros (RF-01)

### [CRITICAL] Endpoints administrativos sem autenticação, incluindo execução de SQL arbitrário
- **ID:** AP-06
- **File:** `app.py:47-57, 59-78`
- **Description:** `POST /admin/query` executa diretamente o SQL recebido no corpo (`cursor.execute(query)` com `query = dados.get("sql")`) e faz `commit` de qualquer comando que não comece com `SELECT`; `POST /admin/reset-db` apaga todas as tabelas (`DELETE FROM itens_pedido/pedidos/produtos/usuarios`). Não há nenhuma verificação de identidade antes da ação — a aplicação não possui mecanismo de autenticação em nenhuma rota.
- **Impact:** Qualquer cliente da rede pode ler, alterar ou destruir todo o banco (`DROP TABLE`, `DELETE`, leitura de senhas) com uma única requisição.
- **Recommendation:** Remover o endpoint de SQL arbitrário; proteger o reset com autenticação de administrador (token via configuração) ou restringi-lo a ambiente de desenvolvimento, com decorator aplicado no blueprint de admin (RF-05)

### [CRITICAL] Senha dos usuários exposta nas respostas da API
- **ID:** AP-04
- **File:** `models.py:79-86, 95-102`; `controllers.py:128-144`
- **Description:** O mapeamento de usuário inclui `"senha": row["senha"]`, e `GET /usuarios` e `GET /usuarios/<id>` devolvem esse dicionário inteiro ao cliente.
- **Impact:** Qualquer pessoa obtém e-mail e senha (em claro, ver AP-03) de todos os usuários, inclusive do admin, com um `GET` sem autenticação — afeta todos os registros.
- **Recommendation:** Serializar usuários com um formato público explícito que nunca contém `senha` (RF-04)

### [CRITICAL] Senhas armazenadas e comparadas em texto plano
- **ID:** AP-03
- **File:** `models.py:109-111, 126-129`; `database.py:75-83`
- **Description:** `criar_usuario` grava a senha recebida sem hash; `login_usuario` compara a senha dentro do SQL (`AND senha = '" + senha + "'`); o seed insere senhas em claro (`"admin123"`, `"123456"`, `"senha123"`).
- **Impact:** Qualquer vazamento do banco (trivial aqui via AP-01/AP-06/AP-04) entrega as senhas reais dos usuários, reutilizáveis em outros serviços.
- **Recommendation:** Gerar hash com salt (`werkzeug.security.generate_password_hash`) no cadastro e no seed, e validar no login com `check_password_hash` buscando o usuário só pelo e-mail (RF-03)

### [CRITICAL] SECRET_KEY hardcoded no código-fonte
- **ID:** AP-02
- **File:** `app.py:7`; `controllers.py:289`
- **Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está literal no entry point e o mesmo valor está repetido literalmente na resposta do health check.
- **Impact:** A chave fica versionada no repositório; qualquer pessoa com acesso ao código (ou ao `/health`) pode forjar sessões/cookies assinados pelo Flask.
- **Recommendation:** Ler `SECRET_KEY` de variável de ambiente em um módulo de configuração, com `.env.example` documentando a variável (RF-02)

### [CRITICAL] Health check expõe secret_key, caminho do banco e flag de debug
- **ID:** AP-04
- **File:** `controllers.py:276-290`
- **Description:** `GET /health` devolve `"secret_key": "minha-chave-super-secreta-123"`, `"db_path": "loja.db"`, `"debug": True` e `"ambiente": "producao"` (valor fixo e falso) para qualquer chamador.
- **Impact:** Endpoint público de monitoramento entrega a chave de assinatura da aplicação e detalhes de infraestrutura que facilitam ataques.
- **Recommendation:** Restringir o health check a status, conectividade do banco e contagens; remover segredos e configuração da resposta (RF-04, RF-02)

### [CRITICAL] God Modules: models.py e app.py concentram várias responsabilidades e domínios
- **ID:** AP-05
- **File:** `models.py:1-314`; `app.py:6-88`
- **Description:** `models.py` reúne funções de 4 domínios (produtos, usuários, pedidos, relatórios) misturando SQL, regra de negócio (checagem de estoque em `criar_pedido`, faixas de desconto em `relatorio_vendas` 256-262) e formatação da resposta (dicionários prontos para o JSON). `app.py` mistura configuração (7-9), registro de rotas (11-30), handlers com SQL direto (47-78) e boot do servidor (80-88).
- **Impact:** Qualquer mudança em um domínio toca o mesmo arquivo dos outros; não é possível testar regra de negócio sem banco nem trocar a persistência sem reescrever as regras.
- **Recommendation:** Separar por camada e domínio: config, repositórios/models por entidade, serviços com as regras, controllers finos, rotas em blueprints e um composition root (RF-06)

### [HIGH] Criação de pedido sem transação e com checagem de estoque não atômica
- **ID:** AP-09
- **File:** `models.py:133-169, 65-70`
- **Description:** `criar_pedido` faz INSERT em `pedidos`, vários INSERT em `itens_pedido` e UPDATE de estoque com um único `commit` no final e nenhum `rollback`; como a conexão é global (AP-08), uma exceção no meio deixa escritas pendentes que serão gravadas pelo próximo `commit` de qualquer outra requisição. A checagem de estoque (linha 144) é separada do débito (163-166), e itens repetidos do mesmo produto passam cada um na checagem individual, permitindo estoque negativo. `deletar_produto` apaga o produto sem tratar `itens_pedido` que o referenciam (órfãos exibidos como "Desconhecido").
- **Impact:** Pedidos parciais, estoque inconsistente/negativo e histórico de pedidos com itens órfãos.
- **Recommendation:** Envolver o pedido inteiro em uma transação com `rollback` no erro, agregar quantidades por produto antes de validar e debitar com `UPDATE ... WHERE estoque >= ?`; tratar o vínculo com pedidos antes de excluir produto (RF-09)

### [HIGH] Conexão SQLite global e compartilhada entre threads
- **ID:** AP-08
- **File:** `database.py:4-10`
- **Description:** `db_connection` é uma variável de módulo reatribuída via `global db_connection` e aberta com `check_same_thread=False`; todas as requisições (servidor com threads) usam o mesmo objeto de conexão e os mesmos commits.
- **Impact:** Requisições concorrentes interferem nas transações umas das outras (o commit de uma grava escritas pendentes da outra) e o estado não pode ser isolado em testes.
- **Recommendation:** Abrir uma conexão por requisição (`flask.g` + `teardown_appcontext`) a partir do caminho configurado, injetada nos repositórios (RF-08)

### [HIGH] Debug ligado e bind aberto fixos no código
- **ID:** AP-10
- **File:** `app.py:8, 88`
- **Description:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` estão literais; o reloader e o debugger interativo do Werkzeug ficam ativos na execução padrão, expostos em todas as interfaces.
- **Impact:** O debugger do Werkzeug permite execução de código se o PIN for obtido, e stack traces vazam detalhes internos para a rede.
- **Recommendation:** Ler `DEBUG`, `HOST` e `PORT` de variáveis de ambiente com default seguro (`DEBUG=false`) (RF-02)

### [HIGH] Regras de negócio e notificações nos controllers; regra de desconto e montagem de resposta no model
- **ID:** AP-07
- **File:** `controllers.py:24-62, 64-96, 188-220, 237-255`; `models.py:256-273`
- **Description:** Os handlers de produto contêm as regras de domínio (categorias válidas, limites de nome, preço/estoque não negativos); `criar_pedido` e `atualizar_status_pedido` disparam "notificações" (e-mail, SMS, push, devolução de estoque) dentro do handler, e a transição de status não verifica se o pedido existe. No sentido inverso, `models.relatorio_vendas` decide a política de desconto e já monta o JSON de resposta.
- **Impact:** Regras não reutilizáveis nem testáveis sem HTTP; o aviso "Devolver estoque." no cancelamento nunca é executado de fato, e o estoque não é devolvido.
- **Recommendation:** Mover validações de domínio, cálculo de desconto, transições de status e notificações para uma camada de serviços; controllers só leem a entrada, chamam o serviço e devolvem a resposta (RF-07)

### [HIGH] Acoplamento direto à infraestrutura fora da camada de dados
- **ID:** AP-11
- **File:** `controllers.py:2-3, 264-274`; `app.py:4, 49-55, 66-76`
- **Description:** O controller `health_check` e os handlers de admin em `app.py` chamam `get_db()` e executam SQL diretamente, sem passar por model/repositório; `controllers` usa `import models` como namespace global de funções com efeitos colaterais, sem qualquer injeção de dependência.
- **Impact:** Acesso a dados espalhado por três arquivos; impossível substituir o banco ou isolar camadas em testes.
- **Recommendation:** Concentrar todo SQL em repositórios recebidos pelos serviços (injetados no composition root); controllers dependem só dos serviços (RF-08, RF-06)

### [MEDIUM] Validação de entrada ausente ou inconsistente
- **ID:** AP-15
- **File:** `controllers.py:43-50, 72-90, 118-121, 169-171, 195-201, 239-240`; `models.py:139-146, 275-283`
- **Description:** `login` e `atualizar_status_pedido` chamam `dados.get(...)` sem checar se o corpo existe (sem JSON → `AttributeError` → 500); `preco < 0` compara sem checar tipo (string → `TypeError` → 500); `float(preco_min)` com valor inválido vira 500; os itens do pedido não validam `produto_id`/`quantidade` (ausente → `KeyError`, quantidade negativa aumenta estoque); a atualização de produto não valida tamanho do nome nem categoria, que a criação valida; atualizar status de pedido inexistente retorna 200; e-mail não tem formato validado.
- **Impact:** Erros de cliente viram 500, dados inválidos entram no banco e as regras de criação e atualização divergem.
- **Recommendation:** Validar corpo, tipos e campos obrigatórios em um único validador por recurso, usado na criação e na atualização, retornando 400/404 (RF-12)

### [MEDIUM] Tratamento de erro genérico repetido em todos os handlers, sem error handler central
- **ID:** AP-14
- **File:** `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`; `app.py:77-78`
- **Description:** Cada handler repete `except Exception as e: return jsonify({"erro": str(e)}), 500`, devolvendo a mensagem crua da exceção (inclusive erros de SQL); não existe `@app.errorhandler` e os formatos de erro variam (`{"erro"}`, `{"erro", "sucesso": False}`, `{"status": "erro", "detalhes"}`).
- **Impact:** Mensagens internas vazam para o cliente, erros de cliente viram 500 e não há ponto único para logar ou padronizar falhas.
- **Recommendation:** Exceções de domínio (`NotFound`, `ValidationError`) tratadas por error handlers centralizados que mantêm o formato `{"erro": ...}` e escondem detalhes de erros inesperados (RF-11)

### [MEDIUM] N+1 queries na listagem de pedidos e agregações separadas no relatório
- **ID:** AP-12
- **File:** `models.py:186-199, 218-231, 239-254, 139-141, 154-156`
- **Description:** Para cada pedido é feita uma query de itens e, para cada item, uma query do nome do produto (`cursor2`/`cursor3` dentro de laços aninhados); o relatório executa 5 `COUNT`/`SUM` separados sobre `pedidos` que cabem em uma consulta com agregação condicional; `criar_pedido` lê cada produto duas vezes.
- **Impact:** O número de queries cresce com pedidos × itens; a listagem de todos os pedidos degrada linearmente com o histórico.
- **Recommendation:** Buscar itens com `JOIN produtos` filtrando por todos os pedidos de uma vez e agrupar em memória; consolidar o relatório em uma única query com `SUM(CASE ...)` (RF-10)

### [MEDIUM] print() como logging, registrando e-mails de usuários
- **ID:** AP-20
- **File:** `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`; `app.py:56`
- **Description:** Eventos e erros são registrados com `print`, sem nível nem logger configurado; `controllers.py:161, 179, 182` imprimem o e-mail do usuário no cadastro e em cada tentativa de login. Severidade elevada de LOW para MEDIUM conforme o catálogo, por registrar dado pessoal. As mensagens de inicialização em `app.py:83-86` são falso positivo (entry point).
- **Impact:** Sem controle de nível/destino dos logs, e dado pessoal (e-mail) gravado em saída padrão sem necessidade.
- **Recommendation:** Usar `logging` com logger por módulo, sem registrar e-mail/PII (RF-14)

### [MEDIUM] Duplicação de mapeamentos, consultas e validações (com cópias divergentes)
- **ID:** AP-13
- **File:** `models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233`; `controllers.py:28-50, 72-90`
- **Description:** O mapeamento linha → dicionário de produto aparece 3 vezes e o de usuário 2 vezes; `get_pedidos_usuario` e `get_todos_pedidos` são idênticas exceto pelo `WHERE`; as validações de criar e atualizar produto são cópias que já divergiram (a atualização não valida tamanho do nome nem categoria).
- **Impact:** Correções precisam ser replicadas em vários pontos, e a divergência já permite gravar via PUT dados que o POST rejeita.
- **Recommendation:** Um serializador por entidade, uma única consulta de pedidos com filtro opcional e um validador compartilhado entre criação e atualização (RF-07, RF-12)

### [MEDIUM] Configuração fixa no código e CORS liberado para qualquer origem
- **ID:** AP-16
- **File:** `database.py:5`; `app.py:9, 88`; `controllers.py:285-287`
- **Description:** O caminho do banco (`db_path = "loja.db"`), a porta `5000` e o host estão literais; `CORS(app)` é aplicado sem `origins`, aceitando qualquer origem; versão e ambiente aparecem como literais na resposta do health check.
- **Impact:** Não é possível mudar banco, porta ou origens permitidas por ambiente sem editar código; qualquer site pode chamar a API pelo navegador.
- **Recommendation:** Centralizar em um módulo de configuração lido do ambiente (`DATABASE_PATH`, `PORT`, `CORS_ORIGINS`) com defaults iguais aos atuais (RF-02)

### [LOW] Magic numbers e listas de valores válidos inline
- **ID:** AP-18
- **File:** `models.py:247-253, 257-262`; `controllers.py:47-50, 52, 242`; `app.py:36`; `controllers.py:285`
- **Description:** Faixas e percentuais de desconto (`10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02`), limites de nome (`2`, `200`), lista de categorias, lista de status e strings de status (`'pendente'`, `'aprovado'`, `'cancelado'`) estão escritos inline; a versão `"1.0.0"` está repetida em dois arquivos.
- **Impact:** Mudança de regra exige caçar literais espalhados e é fácil deixar cópias inconsistentes.
- **Recommendation:** Extrair para constantes nomeadas no domínio (RF-14)

### [LOW] Parâmetros chamados `id` sombreando builtin e nomes sem significado
- **ID:** AP-21
- **File:** `controllers.py:14, 56, 64, 98, 136, 160`; `models.py:24, 54, 65, 89, 187, 191, 219, 223`
- **Description:** Funções recebem e criam variáveis `id`, sombreando o builtin do Python; cursores aninhados chamados `cursor2`/`cursor3`. O parâmetro de rota `<int:id>` é contrato e não muda — só as variáveis internas.
- **Impact:** Leitura mais difícil e risco de uso acidental do builtin sombreado.
- **Recommendation:** Renomear para `produto_id`, `usuario_id`, `novo_id` etc. internamente (RF-14)

### [LOW] Imports não usados
- **ID:** AP-19
- **File:** `models.py:2`; `database.py:2`
- **Description:** `import sqlite3` em `models.py` e `import os` em `database.py` não são usados em nenhum ponto do arquivo. As duas dependências do manifesto (`flask`, `flask-cors`) são usadas.
- **Impact:** Ruído e dependências aparentes que não existem.
- **Recommendation:** Remover os imports (RF-14)

## Deprecated APIs

Nenhuma API deprecated encontrada. Verificado: chamadas de data/hora (`datetime.utcnow`/`utcfromtimestamp` — não usadas; datas vêm do `CURRENT_TIMESTAMP` do SQLite), APIs Flask removidas ou obsoletas (`before_first_request`, `json_encoder`, `flask.escape`, `flask.Markup` — ausentes; o registro via `add_url_rule`/`@app.route` é atual em Flask 3.1.1), `safe_str_cmp`, módulos removidos do Python (`distutils`, `imp`, `cgi`, `pkg_resources`), `logging.warn`, `asyncio.get_event_loop`, e as dependências declaradas (`flask==3.1.1`, `flask-cors==5.0.1`), nenhuma descontinuada. Avisos que só aparecem em execução serão coletados na Fase 3.

---

**Total: 21 findings**

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
