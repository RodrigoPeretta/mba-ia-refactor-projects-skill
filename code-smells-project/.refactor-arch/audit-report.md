# ARCHITECTURE AUDIT REPORT

- **Project:** code-smells-project
- **Stack:** Python + Flask 3.1.1
- **Files:** 4 analyzed | ~780 lines of code
- **Architecture:** Monolítica

## Summary

CRITICAL: 7 | HIGH: 5 | MEDIUM: 6 | LOW: 3

## Findings

### [CRITICAL] SQL Injection em todas as queries do módulo de dados
- **ID:** AP-01
- **File:** `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-299`
- **Description:** Todas as queries são montadas por concatenação de strings com valores vindos do request: `"INSERT INTO produtos (...) VALUES ('" + nome + "', '" + descricao + ...` (47-50), `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (110), `query += " AND (nome LIKE '%" + termo + "%' ..."` com `request.args["q"]` (291) e `categoria` (293), `"UPDATE pedidos SET status = '" + novo_status + ...` (280), além de `produto_id`/`quantidade` do corpo do pedido sem checagem de tipo (140, 155, 157-166). Nenhum `?` com parâmetros é usado fora do seed.
- **Impact:** Qualquer cliente anônimo consegue ler, alterar ou apagar o banco inteiro; o login é contornável com `' OR '1'='1' --` no e-mail, autenticando como o primeiro usuário (admin).
- **Recommendation:** Trocar toda concatenação por queries parametrizadas (`cursor.execute("... WHERE id = ?", (id,))`), inclusive na busca dinâmica (montar só trechos constantes e acumular os valores numa lista de parâmetros) (RF-01)

### [CRITICAL] Endpoints administrativos sem autenticação, incluindo execução de SQL arbitrário
- **ID:** AP-06
- **File:** `app.py:47-57, 59-78`
- **Description:** `POST /admin/query` executa diretamente o SQL recebido em `dados.get("sql")` (`cursor.execute(query)`, linha 69) e faz `commit` em qualquer comando não-SELECT; `POST /admin/reset-db` apaga todas as tabelas (`DELETE FROM itens_pedido/pedidos/produtos/usuarios`, 51-54). Nenhuma das rotas verifica identidade.
- **Impact:** Qualquer pessoa na rede (o bind é `0.0.0.0`) pode apagar todos os dados, ler as senhas de todos os usuários ou alterar o schema com uma única requisição.
- **Recommendation:** Manter as rotas e protegê-las com token de administrador lido do ambiente (fechadas por padrão quando o token não estiver configurado); em `/admin/query`, além do token, aceitar apenas um único `SELECT` (RF-05)

### [CRITICAL] Senha dos usuários exposta nas respostas da API
- **ID:** AP-04
- **File:** `models.py:83, 99`
- **Description:** O mapeamento de usuário em `get_todos_usuarios` e `get_usuario_por_id` inclui `"senha": row["senha"]`, devolvido por `GET /usuarios` e `GET /usuarios/<id>` (controllers.py:128-144), sem autenticação.
- **Impact:** Uma chamada anônima a `GET /usuarios` vaza as senhas (em texto plano, ver AP-03) de todos os usuários, inclusive do admin.
- **Recommendation:** Serializar usuários por uma função única que nunca inclua o campo `senha` (RF-04)

### [CRITICAL] Senhas armazenadas e comparadas em texto plano
- **ID:** AP-03
- **File:** `models.py:109-111, 126-129`; `database.py:75-83`
- **Description:** `criar_usuario` grava a senha recebida sem hash (126-129); `login_usuario` compara a senha dentro do SQL (`AND senha = '" + senha + "'`, 110); o seed insere `"admin123"`, `"123456"`, `"senha123"` em claro (76-78).
- **Impact:** Qualquer vazamento do banco (trivial via AP-01, AP-04 ou AP-06) expõe diretamente as credenciais, reaproveitáveis em outros serviços.
- **Recommendation:** Gerar hash com `werkzeug.security.generate_password_hash` no cadastro e no seed e validar com `check_password_hash` no login (buscando o usuário só pelo e-mail) (RF-03)

### [CRITICAL] Secret key hardcoded no código
- **ID:** AP-02
- **File:** `app.py:7`; `controllers.py:289`
- **Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está literal no código e o mesmo valor é repetido literalmente na resposta do health check.
- **Impact:** A chave fica versionada no repositório e é igual em todos os ambientes; quem lê o código (ou chama `/health`) pode forjar sessões/assinaturas do Flask.
- **Recommendation:** Ler `SECRET_KEY` de variável de ambiente num módulo de configuração, documentado em `.env.example` (RF-02)

### [CRITICAL] Health check expõe secret key, caminho do banco e flag de debug
- **ID:** AP-04
- **File:** `controllers.py:284-289`
- **Description:** `GET /health` devolve `"db_path": "loja.db"`, `"debug": True`, `"ambiente": "producao"` e `"secret_key": "minha-chave-super-secreta-123"` para qualquer cliente.
- **Impact:** Um endpoint público de monitoramento entrega a chave de assinatura da aplicação e detalhes de infraestrutura úteis para um atacante.
- **Recommendation:** Remover `secret_key`, `db_path` e `debug` da resposta do health check, mantendo `status`, `database`, `counts` e `versao` (RF-04, RF-02)

### [CRITICAL] God Module de dados e entry point com responsabilidades misturadas
- **ID:** AP-05
- **File:** `models.py:1-314`; `app.py:6-88`
- **Description:** `models.py` concentra funções de 4 domínios (produtos, usuários, pedidos e relatório de vendas), SQL, regra de negócio (checagem/baixa de estoque e cálculo do total em 137-166, faixas de desconto em 256-262) e formatação dos dicts de resposta. `app.py` mistura configuração (7-9), registro de rotas (11-30), handlers com SQL direto (47-78) e inicialização do servidor (80-88). Não existem pastas de camada.
- **Impact:** Qualquer mudança em um domínio exige mexer no mesmo arquivo dos demais; regra de negócio não é testável sem banco; não há fronteira clara entre acesso a dados, regra e apresentação.
- **Recommendation:** Separar em camadas MVC: `config`, `models/` (um repositório por entidade), `services/` (regras de pedido e relatório), `controllers/`, `routes/` (blueprints) e um composition root mínimo (RF-06)

### [HIGH] Regra de negócio espalhada entre controller e "model"
- **ID:** AP-07
- **File:** `controllers.py:208-210, 242-250`; `models.py:137-146, 256-262`
- **Description:** O controller dispara "notificações" (`ENVIANDO EMAIL/SMS/PUSH`, 208-210; aprovação/cancelamento, 247-250) e decide as transições de status válidas (242); o "model" decide regras de domínio — validação de estoque e cálculo do total do pedido (137-146) e faixas de desconto de 10%/5%/2% do relatório (256-262) — e já devolve dicts de erro para o controller interpretar (`if "erro" in resultado`).
- **Impact:** Regras de pedido e de relatório não podem ser reutilizadas nem testadas isoladamente; o cancelamento promete "devolver estoque" mas nenhum código faz isso.
- **Recommendation:** Mover as regras de pedido, status e relatório para uma camada de serviços que lança exceções de domínio; o controller só lê a entrada, chama o serviço e formata a resposta (RF-07)

### [HIGH] Conexão SQLite global compartilhada entre threads
- **ID:** AP-08
- **File:** `database.py:4-10`
- **Description:** `db_connection` é uma variável de módulo reatribuída via `global db_connection` e aberta com `check_same_thread=False`, sendo compartilhada por todas as requisições do servidor multithread do Flask.
- **Impact:** Requisições concorrentes usam a mesma conexão/transação: um `commit` de uma requisição efetiva escritas parciais de outra e cursores podem se intercalar; impossível isolar em testes.
- **Recommendation:** Abrir uma conexão por requisição (`flask.g` + `teardown_appcontext`) com o caminho vindo da configuração (RF-08)

### [HIGH] Criação de pedido com várias escritas sem transação nem rollback
- **ID:** AP-09
- **File:** `models.py:139-168`
- **Description:** `criar_pedido` lê estoque (144), insere o pedido (148-151), insere cada item (157-161) e decrementa o estoque (163-166) e só faz `commit` no fim, sem `rollback` em caso de exceção; a checagem de estoque e o decremento não são atômicos.
- **Impact:** Uma falha no meio (ex.: `produto_id` inválido no segundo laço) deixa escritas pendentes na conexão global, que serão efetivadas pelo próximo `commit` de outra requisição — pedido sem itens ou estoque baixado sem pedido; duas compras simultâneas podem vender além do estoque.
- **Recommendation:** Envolver todo o pedido numa transação explícita (`with conn:` / commit único com rollback no erro) e decrementar com `UPDATE ... WHERE estoque >= ?` (RF-09)

### [HIGH] Debug ligado e bind aberto fixos no código
- **ID:** AP-10
- **File:** `app.py:8, 88`
- **Description:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` estão literais, sem leitura de ambiente.
- **Impact:** O debugger interativo do Werkzeug (execução de código remota) fica exposto em todas as interfaces de rede em qualquer ambiente em que `python app.py` for executado.
- **Recommendation:** Ler `DEBUG` (default `false`), `HOST` e `PORT` de variáveis de ambiente no módulo de configuração (RF-02)

### [HIGH] Acoplamento direto à infraestrutura, sem injeção de dependência
- **ID:** AP-11
- **File:** `controllers.py:2-3, 264-274`; `app.py:4, 47-78`; `models.py:1, 5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286`
- **Description:** O controller `health_check` e as rotas `/admin/*` executam SQL direto via `get_db()`, sem passar por model; `controllers.py` usa `import models` como namespace global de funções; cada função de `models.py` busca a conexão global por conta própria (`db = get_db()`).
- **Impact:** Não há como trocar o banco ou injetar um dublê em testes; SQL aparece em três camadas diferentes.
- **Recommendation:** Concentrar o SQL em repositórios na camada de models que recebem a conexão da requisição; controllers dependem só de serviços/models (RF-08, RF-06)

### [MEDIUM] N+1 queries na listagem de pedidos e agregações separadas
- **ID:** AP-12
- **File:** `models.py:187-199, 219-231, 239-254, 154-156`; `controllers.py:269-274`
- **Description:** Para cada pedido é feita uma query de itens e, para cada item, outra query do nome do produto (187-199 e 219-231); o relatório faz 5 consultas separadas na tabela `pedidos` (239-254) que cabem num `GROUP BY`; `criar_pedido` relê o preço de cada produto já lido no primeiro laço (155).
- **Impact:** Listar N pedidos com M itens custa 1 + N + N·M queries; o tempo cresce linearmente com o histórico de pedidos.
- **Recommendation:** Buscar itens com `JOIN` em produtos para todos os pedidos de uma vez e agrupar em memória; calcular o relatório com uma única query agregada (RF-10)

### [MEDIUM] Mapeamentos, listagens e validações duplicados (e já divergentes)
- **ID:** AP-13
- **File:** `models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233`; `controllers.py:28-50, 72-90`
- **Description:** O mapeamento row → dict de produto aparece 3 vezes e o de usuário 2 vezes; `get_pedidos_usuario` e `get_todos_pedidos` são idênticas exceto pelo `WHERE`; as validações de `criar_produto` e `atualizar_produto` foram copiadas e já divergiram — a atualização não valida tamanho do nome nem categoria.
- **Impact:** Correções precisam ser replicadas em vários pontos (ex.: remover `senha` exigiria mexer em 2 lugares); um produto pode ser atualizado para uma categoria inválida que a criação recusaria.
- **Recommendation:** Uma função de serialização por entidade, uma função de listagem de pedidos com filtro opcional e uma validação única de produto usada na criação e na atualização (RF-07, RF-12)

### [MEDIUM] `try/except Exception` copiado em todos os handlers devolvendo `str(e)`
- **ID:** AP-14
- **File:** `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`; `app.py:77-78`
- **Description:** Cada handler envolve tudo em `except Exception as e: return jsonify({"erro": str(e)}), 500`; não existe `@app.errorhandler`. Erros de cliente viram 500 (ex.: `POST /login` sem corpo → `'NoneType' object has no attribute 'get'`; `preco_min=abc` → `could not convert string to float`).
- **Impact:** Mensagens internas (inclusive trechos de SQL quando a query falha) vazam ao cliente, o status HTTP não distingue erro do cliente de falha do servidor e o tratamento não é uniforme.
- **Recommendation:** Error handler centralizado com exceções de domínio/validação mapeadas para 400/404 e erros inesperados registrados no log e respondidos com 500 genérico (RF-11)

### [MEDIUM] Validação de entrada ausente ou inconsistente
- **ID:** AP-15
- **File:** `controllers.py:43-50, 87-90, 118-121, 153-158, 169-171, 195-201, 239-245`
- **Description:** `preco`/`estoque` são comparados com `< 0` sem checar tipo (string → `TypeError` → 500); `login` e `atualizar_status_pedido` chamam `dados.get` sem checar se o corpo existe; os itens do pedido não validam `produto_id` nem `quantidade` (quantidade negativa **aumenta** o estoque em models.py:164); e-mail não tem formato validado; o status é atualizado sem verificar se o pedido existe (200 para id inexistente).
- **Impact:** Entradas malformadas causam 500, corrompem estoque ou geram respostas de sucesso falsas.
- **Recommendation:** Validar corpo, tipos e faixas em funções de validação dedicadas antes de chamar os serviços, retornando 400 com mensagem clara (RF-12)

### [MEDIUM] Configuração fixa no código e CORS liberado para qualquer origem
- **ID:** AP-16
- **File:** `database.py:5`; `app.py:9, 88`
- **Description:** Caminho do banco `db_path = "loja.db"`, host `0.0.0.0` e porta `5000` literais; `CORS(app)` sem `origins` libera todas as origens para todas as rotas, inclusive `/admin/*`.
- **Impact:** Não é possível mudar banco/porta por ambiente sem editar código; qualquer site pode chamar a API pelo navegador do usuário.
- **Recommendation:** Centralizar em `config` lido do ambiente (`DATABASE_PATH`, `HOST`, `PORT`, `CORS_ORIGINS` com default `*` para preservar o comportamento atual) (RF-02)

### [MEDIUM] `print` como logging, registrando e-mails de usuários
- **ID:** AP-20
- **File:** `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`; `app.py:56`
- **Description:** Eventos e erros são registrados com `print(...)`, sem nível nem logger. Severidade elevada de LOW para MEDIUM porque as linhas 161, 179 e 182 registram o e-mail do usuário (dado pessoal) em cadastro e tentativas de login. As mensagens de inicialização em `app.py:83-86` foram desconsideradas (falso positivo do catálogo).
- **Impact:** Sem controle de nível/destino dos logs; dados pessoais vão para a saída padrão sem possibilidade de filtragem.
- **Recommendation:** Usar `logging` com logger por módulo e não registrar e-mail em claro (RF-14)

### [LOW] Magic numbers e listas de valores inline
- **ID:** AP-18
- **File:** `controllers.py:47-50, 52, 242`; `models.py:257-262`; `app.py:36`; `controllers.py:285`
- **Description:** Limites de nome (2 e 200), lista de categorias válidas, lista de status válidos, faixas de desconto (10000/5000/1000 com 10%/5%/2%) e a versão `"1.0.0"` repetida em dois arquivos estão escritos inline.
- **Impact:** Alterar uma regra exige caçar literais; versões repetidas tendem a divergir.
- **Recommendation:** Extrair para constantes nomeadas no domínio/config (RF-14)

### [LOW] Imports não usados
- **ID:** AP-19
- **File:** `models.py:2`; `database.py:2`
- **Description:** `import sqlite3` em `models.py` e `import os` em `database.py` não são usados em nenhum outro ponto dos arquivos.
- **Impact:** Ruído e falsa impressão de dependência.
- **Recommendation:** Remover os imports não usados (RF-14)

### [LOW] Parâmetros e variáveis chamados `id` sombreando o builtin
- **ID:** AP-21
- **File:** `controllers.py:14, 56, 64, 98, 136, 160`; `models.py:24, 54, 65, 89, 187, 191`
- **Description:** Funções recebem `id` e atribuem `id = models.criar_...`, sombreando o builtin `id()`; cursores nomeados `cursor2`/`cursor3`. O nome do parâmetro de rota `<int:id>` faz parte só do código, não do contrato JSON.
- **Impact:** Leitura mais difícil e risco de bug sutil ao usar o builtin no mesmo escopo.
- **Recommendation:** Renomear variáveis internas (`produto_id`, `usuario_id`, `novo_id`), mantendo os campos do contrato HTTP inalterados (RF-14)

## Deprecated APIs

Nenhuma API deprecated encontrada. Verificado: chamadas de data/hora (`datetime.utcnow`/`utcfromtimestamp` — não usadas; datas vêm do `CURRENT_TIMESTAMP` do SQLite), APIs removidas/obsoletas do Flask 3.x (`before_first_request`, `json_encoder`, `flask.escape`/`flask.Markup` — não usadas), `safe_str_cmp` do Werkzeug, módulos removidos do Python 3.12/3.13 (`distutils`, `imp`, `cgi`, `pkg_resources`), `logging.warn`, `asyncio.get_event_loop`, e as dependências declaradas (`flask==3.1.1`, `flask-cors==5.0.1`, ambas mantidas).

---

**Total: 21 findings**

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
