# Research: Skill `refactor-arch`

Decisões técnicas da Fase 0. Fonte primária para o formato de skill: documentação oficial do
Claude Code (https://code.claude.com/docs/en/skills), consultada em 2026-10-14. Fonte para o
comportamento dos projetos-alvo: execução da baseline registrada em `docs/analise-manual.md`.

---

## R1 — Formato da skill e frontmatter

- **Decision**: `.claude/skills/refactor-arch/SKILL.md` com frontmatter:
  `name: refactor-arch`, `description` (o que faz e quando usar),
  `argument-hint: "[caminho-do-relatorio]"`, `disable-model-invocation: true`.
  Referências em `references/*.md`, linkadas a partir do `SKILL.md`.
- **Rationale**: a doc oficial define que só o `SKILL.md` é carregado ao invocar; arquivos de
  apoio são lidos sob demanda quando o `SKILL.md` aponta para eles (progressive disclosure),
  e recomenda manter o `SKILL.md` abaixo de 500 linhas. `disable-model-invocation: true`
  impede que o Claude dispare por conta própria uma skill que reescreve o projeto — ela só
  roda quando o humano digita `/refactor-arch`.
- **Alternatives considered**: deixar a invocação automática habilitada (rejeitado: risco de
  refatoração não solicitada); `context: fork` para rodar em subagente (rejeitado: a Fase 2
  precisa conversar com o usuário para obter a confirmação, e um subagente em background não
  recebe essa resposta).

## R2 — Descoberta da skill ao rodar dentro de cada projeto

- **Decision**: cada projeto recebe sua própria cópia em
  `<projeto>/.claude/skills/refactor-arch/`, e a skill é executada iniciando o Claude Code
  dentro da pasta do projeto (`cd <projeto> && claude "/refactor-arch"`).
- **Rationale**: o Claude Code carrega `.claude/skills/` do diretório inicial e de cada pai
  até a raiz do repositório. Iniciando dentro do projeto, a cópia local é encontrada e o
  diretório de trabalho já é o projeto-alvo, o que evita que a skill precise "descobrir"
  qual projeto auditar. As skills `speckit-*` da raiz também carregam, sem conflito de nome.
- **Alternatives considered**: uma única cópia na raiz com o caminho do projeto como
  argumento (rejeitado: o enunciado exige a skill dentro dos 3 projetos e o comando sem
  argumentos).

## R3 — Validação em execução sem scripts auxiliares

- **Decision**: a skill não traz scripts executáveis. A validação da Fase 3 é feita pelo
  agente com ferramentas de shell universais: sobe a aplicação em background, faz polling
  até responder, chama cada endpoint com `curl` e encerra a árvore de processos. O
  procedimento passo a passo, com comandos para POSIX e Windows, fica em
  `references/validation-procedure.md`.
- **Rationale**: um script em Python não roda num projeto Node sem Python instalado, e
  vice-versa; `curl` existe nativamente em Linux, macOS e Windows 10+. Manter tudo em
  Markdown também segue a restrição do enunciado ("formato dos arquivos de referência:
  Markdown") e o Princípio I (agnóstico).
- **Alternatives considered**: script Python de smoke test (como o usado na baseline manual —
  rejeitado pelo acoplamento de runtime); suíte de testes gerada por stack (rejeitado:
  escopo maior que o desafio, e a spec assume validação por chamadas reais).

## R4 — Onde a skill grava seus artefatos

- **Decision**: pasta `.refactor-arch/` na raiz do projeto-alvo, com `audit-report.md`
  (Fase 2), `behavior-before.md` (referência de comportamento capturada no início da Fase 3)
  e `validation-after.md` (resultado da validação). Se a invocação recebe um caminho como
  argumento, o relatório é gravado nesse caminho em vez do padrão.
- **Rationale**: fica fora do código-fonte (Princípio II permite apenas o relatório antes
  da confirmação), é previsível em qualquer stack e os arquivos servem de evidência para o
  README ("logs mostrando as aplicações rodando"). A cópia para
  `reports/audit-project-N.md` é um passo de entrega, feito fora da skill.
- **Alternatives considered**: gravar direto em `../reports/` (rejeitado: depende da
  estrutura do repositório-pai, não é agnóstico); só imprimir no terminal (rejeitado: o
  relatório se perde e o FR-012 exige arquivo).

## R5 — Estrutura MVC alvo conforme o ponto de partida

- **Decision**: duas estratégias, escolhidas pela classificação da Fase 1:
  - **Monolítico / sem camadas** → layout novo sob `src/` (`config/`, `models/`, `views/`,
    `controllers/`, `middlewares/`, composition root), como no exemplo do enunciado.
  - **Parcialmente em camadas** → mantém o layout existente no nível em que está e completa
    as camadas que faltam (ex.: cria `controllers/`, `config/`, `middlewares/`, tira regra de
    negócio das rotas), sem renomear o que já cumpre a função (`routes/` é aceito como a
    camada "Views/Routes").
  - Em ambos os casos o **comando de execução original continua funcionando** (`python app.py`,
    `npm start`): o arquivo de entrada original vira um entry point fino que delega ao
    composition root, ou o manifesto é atualizado para o novo caminho.
- **Rationale**: atende ao FR-019 (incremental em projeto organizado) e mantém válidas as
  instruções de execução dos READMEs, o que também simplifica a validação "antes x depois".
- **Alternatives considered**: forçar `src/` em todos os projetos (rejeitado: no projeto
  parcialmente organizado seria reescrever o que já está certo).

## R6 — Onde fica a regra de negócio no MVC alvo

- **Decision**: Model = entidades + acesso a dados + regras de domínio. Regras que cruzam
  várias entidades (ex.: fechar um pedido valida estoque, calcula total e baixa estoque)
  ficam em `services/`, considerado parte da camada Model. Controllers só orquestram:
  leem a requisição, chamam model/service e montam a resposta. Views/Routes só mapeiam
  URL → controller e serializam a saída.
- **Rationale**: o enunciado classifica "lógica de negócio pesada dentro de Controllers" como
  HIGH; colocá-la no Model (ou em serviços de domínio) é o que torna os controllers finos e a
  regra testável sem HTTP.
- **Alternatives considered**: regra no controller (é o anti-pattern); camada de "use cases"
  estilo Clean Architecture (rejeitado: foge do MVC pedido).

## R7 — Correções de segurança que tocam o contrato

- **Decision**:
  - **Rotas administrativas/destrutivas** (reset de banco, execução de query, exclusão
    em massa, relatórios administrativos, exclusão de registros por id sem dono): mantidas,
    exigindo o header `X-Admin-Token` igual à variável de ambiente `ADMIN_TOKEN`. Sem a
    variável configurada, a rota responde 403 (fechada por padrão). Uma rota de execução de
    SQL arbitrário também passa a aceitar só leitura.
  - **Dados sensíveis na resposta** (senha/hash): removidos por allowlist no serializer.
  - **Senhas**: hash forte com a biblioteca já disponível na stack (`werkzeug.security` no
    Flask, `crypto.scrypt` no Node); seeds passam a gravar o hash, para que o login dos
    usuários de exemplo continue funcionando.
  - **Autenticação completa** (sessões/JWT reais, autorização por recurso) fica **fora do
    escopo** da refatoração: a skill registra como pendência no resumo, e corrige o que é
    local (ex.: não permitir que o cadastro público crie um `admin`).
- **Rationale**: decisão aprovada pelo usuário ("proteger em vez de remover"), Princípio IV
  e FR-018; token por variável de ambiente é suficiente para o escopo (Assumptions da spec).
  Na validação, a skill configura `ADMIN_TOKEN` e chama as rotas com e sem o header, provando
  que elas funcionam e que estão protegidas.
- **Alternatives considered**: remover as rotas perigosas (rejeitado: quebra "endpoints
  originais respondem"); implementar JWT (rejeitado: escopo e mudança de contrato em todas
  as rotas).

## R8 — Referência de comportamento e dados de teste

- **Decision**: no início da Fase 3 (após o "y"), a skill sobe a aplicação **original** e
  registra, para cada endpoint, método, rota, corpo enviado, status e chaves de nível
  superior do JSON. As requisições são montadas a partir de exemplos do próprio projeto
  (arquivos `.http`, README, coleções) e, na falta deles, dos campos obrigatórios lidos nas
  validações do código. Ordem: leituras → criações → atualizações → exclusões → rotas
  destrutivas globais por último. O banco é reinicializado antes da medição "depois"
  (arquivo SQLite removido/recriado pelo seed, ou banco em memória recriado no boot).
- **Rationale**: comparar o mesmo roteiro antes e depois é o que torna o FR-020 objetivo;
  ordenar as destrutivas por último evita falsos negativos.
- **Alternatives considered**: comparar só código de status sem registrar o original
  (rejeitado: não detecta mudança de formato); comparar o corpo inteiro (rejeitado: ids,
  timestamps e hashes variam entre execuções).

## R9 — Ambiente de execução e processos

- **Decision**: dependências instaladas em ambiente isolado dentro do projeto (`.venv` para
  Python, `node_modules` para Node), só se ainda não existirem; nunca instalação global.
  Antes do boot, a skill verifica se a porta está livre. Para encerrar, usa
  `taskkill /T /F /PID <pid>` no Windows e `kill -- -<pgid>` (ou `pkill -P` + `kill`) em
  POSIX, e confirma que a porta foi liberada.
- **Rationale**: na baseline manual, o reloader do Flask (`debug=True`) criou um processo
  filho que sobreviveu ao término do pai e continuou ocupando a porta — a execução do
  projeto seguinte respondeu com a aplicação errada. Matar a árvore e conferir a porta evita
  isso.
- **Alternatives considered**: matar só o PID iniciado (falhou na prática).

## R10 — Catálogo: detecção acionável e APIs deprecated

- **Decision**: cada entrada do catálogo traz ID, severidade-base, sinais de detecção
  concretos por linguagem (padrões de busca), falsos positivos conhecidos e a transformação
  do playbook que o corrige. A seção de APIs deprecated é uma tabela "API obsoleta →
  substituto moderno" para Python e Node, e manda **também** checar warnings de depreciação
  emitidos no boot e no install de dependências.
- **Rationale**: "seja específico nos sinais de detecção" (dicas do enunciado). A
  baseline mostrou que o P3 emite `LegacyAPIWarning`/`DeprecationWarning` no runtime e que o
  `npm install` do P2 avisa sobre dependência deprecated — sinais que a leitura estática
  sozinha poderia perder.
- **Alternatives considered**: catálogo genérico sem padrões de busca (rejeitado: produz
  findings vagos e sem linha exata).

## R11 — Idioma da saída

- **Decision**: cabeçalhos e rótulos fixos em inglês, exatamente como no exemplo do
  enunciado (`PHASE 1: PROJECT ANALYSIS`, `ARCHITECTURE AUDIT REPORT`, `File:`,
  `Description:`…); texto descritivo em português (pt-BR).
- **Rationale**: o template do enunciado mistura assim; manter rótulos fixos facilita
  conferir o relatório contra o template.
- **Alternatives considered**: tudo em inglês ou tudo em português (ambos se afastam do
  exemplo do enunciado).

## R12 — Garantia de "nenhuma modificação antes da confirmação"

- **Decision**: o `SKILL.md` declara as Fases 1–2 como somente leitura (apenas leitura de
  arquivos, busca e comandos que não escrevem — ex.: `git status`, listar arquivos; nada
  de instalar dependências nem subir a aplicação antes do "y"), grava apenas o relatório e
  termina a Fase 2 com a pergunta, encerrando o turno sem nenhuma outra ação. Instalar
  dependências e rodar a aplicação original passam a ser os primeiros passos da Fase 3.
- **Rationale**: subir a aplicação original cria arquivos (ex.: SQLite, `__pycache__`) e
  instalar dependências altera o projeto; colocar isso depois da confirmação mantém o
  Princípio II literal e verificável por `git status`.
- **Alternatives considered**: capturar a referência de comportamento na Fase 1 (rejeitado
  por gerar escrita antes da confirmação).
