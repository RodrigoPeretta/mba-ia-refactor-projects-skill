# Feature Specification: Skill `refactor-arch` — Auditoria e Refatoração Arquitetural Automatizada

**Feature Branch**: `001-refactor-arch-skill`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Criar uma Skill que analisa uma codebase (detectando linguagem, framework e arquitetura atual), identifica anti-patterns e code smells classificados por severidade com arquivo e linha exatos, gera um relatório de auditoria estruturado, pede confirmação e então refatora o projeto para o padrão MVC, validando que a aplicação continua funcionando. A skill deve ser agnóstica de tecnologia e funcionar nos 3 projetos legados fornecidos (2 Python/Flask e 1 Node.js/Express)."

## User Scenarios & Testing *(mandatory)*

O ator principal é o **desenvolvedor que herdou um projeto legado** e invoca a skill de dentro
da pasta do projeto. Um ator secundário é o **avaliador do desafio**, que roda a mesma skill
nos três projetos e confere o checklist de validação.

### User Story 1 - Diagnóstico do projeto (Fase 1) (Priority: P1)

Ao invocar `/refactor-arch` na raiz de um projeto, o desenvolvedor recebe um resumo do que é o
projeto — linguagem, framework e versão, dependências principais, domínio da aplicação,
arquitetura atual, quantidade de arquivos-fonte analisados e tabelas/entidades de dados —
sem precisar informar nada sobre a stack.

**Why this priority**: é a base das demais fases; uma stack detectada errada invalida a
auditoria e a refatoração. É também critério eliminatório (3/3 projetos).

**Independent Test**: invocar a skill em cada um dos 3 projetos, responder "n" na
confirmação, e comparar o resumo impresso com a realidade do projeto (manifesto de
dependências, arquivos existentes, tabelas criadas).

**Acceptance Scenarios**:

1. **Given** um projeto Flask monolítico de e-commerce, **When** a skill é invocada,
   **Then** o resumo informa Python, Flask com a versão do manifesto, domínio de e-commerce
   (produtos, pedidos, usuários), arquitetura monolítica sem separação de camadas, o número
   real de arquivos-fonte e as tabelas do banco.
2. **Given** um projeto Node.js/Express, **When** a skill é invocada, **Then** o resumo
   informa JavaScript/Node.js, Express com a versão do manifesto e o domínio correto (LMS com
   checkout), sem nenhuma alteração na skill entre um projeto e outro.
3. **Given** um projeto Flask que já possui pastas de models/routes/services, **When** a skill
   é invocada, **Then** o resumo identifica o domínio de Task Manager e descreve a arquitetura
   como "parcialmente em camadas", apontando as camadas existentes e as ausentes.

---

### User Story 2 - Relatório de auditoria com pausa para confirmação (Fase 2) (Priority: P1)

Após o diagnóstico, a skill cruza o código com um catálogo de anti-patterns e apresenta um
relatório de auditoria padronizado: resumo de contagem por severidade e a lista de findings,
cada um com severidade, arquivo e linhas exatos, descrição, impacto e recomendação. Ao final,
a skill pergunta se deve prosseguir com a refatoração e **não modifica nenhum arquivo do
projeto** até receber uma resposta afirmativa.

**Why this priority**: é o principal valor para o humano (saber o que está errado e com que
gravidade) e contém dois critérios eliminatórios (≥ 5 findings, ≥ 1 CRITICAL ou HIGH). A
pausa é obrigatória pelo enunciado.

**Independent Test**: invocar a skill, responder "n", conferir que o relatório segue o
template, que cada arquivo/linha citado existe e corresponde ao problema descrito, e que o
código do projeto permanece inalterado.

**Acceptance Scenarios**:

1. **Given** a Fase 1 concluída, **When** a Fase 2 termina, **Then** o relatório lista os
   findings ordenados de CRITICAL para LOW, cada um com arquivo e intervalo de linhas que
   existem no projeto, e o resumo de contagem bate com a lista.
2. **Given** um projeto que usa APIs obsoletas, **When** a auditoria roda, **Then** o
   relatório inclui findings de API deprecated indicando o equivalente moderno; **Given** um
   projeto sem APIs obsoletas, **Then** o relatório declara explicitamente que nenhuma foi
   encontrada.
3. **Given** o relatório apresentado, **When** o usuário responde "n" (ou qualquer coisa que
   não seja confirmação), **Then** a skill encerra sem alterar nenhum arquivo de código do
   projeto, e o relatório permanece salvo para consulta.
4. **Given** o relatório apresentado, **When** o usuário responde "y", **Then** a skill segue
   para a Fase 3.

---

### User Story 3 - Refatoração para MVC com validação em execução (Fase 3) (Priority: P1)

Confirmada a refatoração, a skill registra como a aplicação responde **antes** da mudança,
reestrutura o projeto no padrão MVC eliminando os problemas do relatório, e então sobe a
aplicação refatorada e chama todos os endpoints originais para provar que ela continua
funcionando. Ao final, imprime a nova estrutura de diretórios, o resultado da validação e as
mudanças intencionais de contrato feitas por segurança.

**Why this priority**: "a aplicação funciona após a refatoração" é critério eliminatório em
3/3 projetos; sem validação real a refatoração não tem valor demonstrável.

**Independent Test**: confirmar a Fase 3 em um projeto partindo do código original, e
verificar a estrutura criada, o boot da aplicação e a resposta de cada endpoint original.

**Acceptance Scenarios**:

1. **Given** a confirmação do usuário, **When** a Fase 3 termina, **Then** o projeto tem
   camadas separadas de configuração, models, views/rotas, controllers e tratamento de erro
   centralizado, com um único entry point identificável.
2. **Given** o projeto refatorado, **When** a validação roda, **Then** a aplicação inicia sem
   erros e todos os endpoints originais respondem com o mesmo código de status de sucesso e o
   mesmo formato de resposta registrados antes da refatoração.
3. **Given** um finding de segurança que exige mudar o contrato (ex.: senha devolvida na
   resposta, rota administrativa aberta), **When** a refatoração o corrige, **Then** a rota
   continua existindo (protegida ou com o campo sensível removido) e a mudança aparece listada
   no resumo final como alteração intencional.
4. **Given** uma falha de boot ou um endpoint que regrediu na validação, **When** a skill
   detecta a falha, **Then** ela corrige e valida de novo antes de declarar a fase concluída,
   ou, se não conseguir, reporta a falha explicitamente em vez de anunciar sucesso.

---

### User Story 4 - Reuso em outra stack e em projeto parcialmente organizado (Priority: P2)

O desenvolvedor copia a pasta da skill, sem alterações, para outro projeto — de outra
linguagem ou já parcialmente organizado em camadas — e as três fases funcionam do mesmo
jeito, adaptando a refatoração ao ponto de partida: um monolito é decomposto; um projeto já
em camadas é reorganizado de forma incremental, sem descartar o que já está adequado.

**Why this priority**: é o que prova que a skill é agnóstica de tecnologia; depende das
histórias 1–3 estarem funcionando em um projeto primeiro.

**Independent Test**: copiar a pasta da skill para os outros dois projetos, comparar que o
conteúdo é idêntico, e executar as três fases em cada um.

**Acceptance Scenarios**:

1. **Given** a skill copiada sem alterações para o projeto Node.js/Express, **When** as três
   fases rodam, **Then** todos os critérios das histórias 1–3 são atendidos nesse projeto.
2. **Given** a skill copiada para o projeto Flask parcialmente em camadas, **When** a Fase 3
   roda, **Then** as camadas existentes que já cumprem sua responsabilidade são preservadas,
   as ausentes (ex.: controllers, config, tratamento de erro) são criadas, e todos os
   endpoints continuam respondendo.

---

### User Story 5 - Entrega documentada e reprodutível (Priority: P3)

O avaliador encontra no repositório os três relatórios de auditoria, o código refatorado de
cada projeto, a skill copiada nos três projetos e um README que explica a análise manual, as
decisões de construção da skill, os resultados (com checklist preenchido e evidências da
aplicação rodando) e como executar tudo de novo.

**Why this priority**: é entregável obrigatório, mas não é uma capacidade da skill em si; só
pode ser feito depois das execuções.

**Independent Test**: um terceiro clona o repositório, segue a seção "Como Executar" do
README, e consegue reproduzir a execução da skill em qualquer um dos projetos a partir do
código original.

**Acceptance Scenarios**:

1. **Given** as três execuções concluídas, **When** o avaliador abre a pasta de relatórios,
   **Then** encontra um relatório por projeto, cada um com o conteúdo da Fase 2 daquela execução.
2. **Given** o README, **When** o avaliador lê a seção de resultados, **Then** encontra a
   contagem de findings por severidade de cada projeto, a comparação de estrutura antes/depois,
   o checklist de validação preenchido e evidências (logs ou screenshots) das aplicações
   rodando após a refatoração.

---

### Edge Cases

- **Usuário recusa a Fase 3**: a skill encerra limpa, sem nenhum arquivo de código alterado; o
  relatório continua disponível.
- **Resposta ambígua na confirmação** ("talvez", vazio): tratada como recusa — a skill só
  prossegue com confirmação explícita.
- **Aplicação original não sobe** (ex.: dependências não instaladas, passo de seed exigido pelo
  README): a skill segue as instruções de execução do próprio projeto (README, scripts do
  manifesto) e prepara um ambiente isolado de dependências; se mesmo assim o original não
  subir, registra isso e valida a versão refatorada contra os endpoints declarados no código.
- **Endpoints que alteram dados** (criação, exclusão, reset): a validação usa dados de
  teste próprios e executa operações destrutivas por último, para não contaminar as demais
  verificações; o estado do banco é reinicializado entre a medição "antes" e "depois".
- **Endpoint que já falhava antes** (ex.: erro 500 com entrada inválida): a comparação não
  exige reproduzir o defeito; a refatoração pode convertê-lo em erro de cliente (4xx), e isso
  é reportado como correção.
- **Porta ocupada ou processo que não encerra** (ex.: servidor com auto-reload que cria
  processo filho): a skill encerra a árvore de processos que iniciou e confirma que a porta
  foi liberada.
- **Banco em memória**: dados de seed recriados a cada boot; a validação não depende de
  estado persistido entre execuções.
- **Categoria do catálogo que não se aplica** (ex.: nenhum uso de API deprecated): declarada
  como "não encontrada" no relatório, sem finding inventado.
- **Projeto parcialmente organizado**: a skill não recria do zero camadas que já cumprem sua
  função; move ou extrai apenas o que viola as responsabilidades da arquitetura alvo.
- **Menos de 5 problemas reais**: a skill reporta o que encontrou; não infla a contagem.

## Requirements *(mandatory)*

### Functional Requirements

**Invocação e fluxo**

- **FR-001**: A skill MUST ser invocável pelo nome `refactor-arch` a partir da raiz do
  projeto-alvo, sem parâmetros obrigatórios.
- **FR-002**: A skill MUST executar as fases na ordem Análise → Auditoria → (confirmação) →
  Refatoração, imprimindo um cabeçalho identificando cada fase.

**Fase 1 — Análise**

- **FR-003**: A skill MUST detectar linguagem, framework (com versão declarada no manifesto),
  dependências principais, tipo de banco de dados e tabelas/entidades, apenas a partir dos
  arquivos do projeto.
- **FR-004**: A skill MUST descrever o domínio da aplicação a partir de rotas, entidades e
  nomes do código.
- **FR-005**: A skill MUST classificar a arquitetura atual (ex.: monolítica, parcialmente em
  camadas, em camadas) e informar quantos arquivos-fonte analisou, excluindo dependências
  instaladas, ambientes virtuais, artefatos gerados e a própria pasta da skill.
- **FR-006**: A skill MUST imprimir o resumo da Fase 1 no formato definido nos arquivos de
  referência.

**Fase 2 — Auditoria**

- **FR-007**: A skill MUST comparar o código contra um catálogo de anti-patterns com no
  mínimo 8 entradas, cobrindo as 4 severidades (CRITICAL, HIGH, MEDIUM, LOW), cada uma com
  sinais de detecção concretos.
- **FR-008**: O catálogo MUST incluir a detecção de APIs deprecated, recomendando o
  equivalente moderno; quando nenhuma for encontrada, o relatório MUST dizer isso
  explicitamente.
- **FR-009**: Cada finding MUST conter severidade, título, arquivo, linha ou intervalo de
  linhas, descrição, impacto e recomendação; arquivo e linhas MUST ser conferidos no código
  antes de entrar no relatório.
- **FR-010**: O relatório MUST seguir o template de referência e listar os findings ordenados
  por severidade (CRITICAL → HIGH → MEDIUM → LOW), com resumo de contagem por severidade e
  total consistentes com a lista.
- **FR-011**: A skill MUST NOT incluir findings sem evidência no código para atingir mínimos.
- **FR-012**: A skill MUST salvar o relatório completo da Fase 2 em um arquivo Markdown
  (caminho padrão definido nos arquivos de referência, sobrescrevível por argumento opcional
  na invocação), além de imprimi-lo.
- **FR-013**: Ao final da Fase 2, a skill MUST pedir confirmação explícita para prosseguir e
  MUST NOT criar, alterar, mover ou remover arquivos de código do projeto antes de uma
  resposta afirmativa. Qualquer resposta que não seja afirmativa encerra a skill.

**Fase 3 — Refatoração e validação**

- **FR-014**: Antes de alterar o código, a skill MUST subir a aplicação original e registrar a
  resposta (código de status e formato) de cada endpoint existente, para uso como referência.
- **FR-015**: A skill MUST reestruturar o projeto no padrão MVC definido nos arquivos de
  referência: módulo de configuração, models, views/rotas, controllers, tratamento de erro
  centralizado e um entry point (composition root) claro.
- **FR-016**: A skill MUST aplicar as transformações do playbook de refatoração (no mínimo 8
  padrões, cada um com exemplo antes/depois) correspondentes aos findings do relatório, com
  prioridade para CRITICAL e HIGH.
- **FR-017**: A skill MUST remover segredos do código, lendo-os de variáveis de ambiente com
  valores padrão seguros para desenvolvimento, e documentar as variáveis em um arquivo de
  exemplo de ambiente.
- **FR-018**: A skill MUST preservar rotas, métodos HTTP, formato de resposta e códigos de
  status de sucesso. Quando uma correção de segurança exigir mudar o contrato, a skill MUST
  manter a rota (protegendo-a ou removendo o dado sensível) em vez de removê-la, e MUST
  listar a mudança no resumo final.
- **FR-019**: Em projetos já parcialmente organizados, a skill MUST preservar as camadas que
  já cumprem sua responsabilidade e reorganizar de forma incremental.
- **FR-020**: A skill MUST validar o resultado executando a aplicação refatorada: boot sem
  erros e chamada real a todos os endpoints registrados no FR-014, comparando com a
  referência.
- **FR-021**: Se a validação falhar, a skill MUST corrigir e validar novamente; se não
  conseguir, MUST reportar a falha explicitamente no resumo final.
- **FR-022**: Ao final, a skill MUST imprimir a nova estrutura de diretórios, o resultado da
  validação item a item e a lista de mudanças intencionais de contrato e de dependências
  adicionadas (com justificativa).
- **FR-023**: A skill MUST encerrar todos os processos que iniciou durante a validação.

**Portabilidade e conhecimento**

- **FR-024**: A skill MUST funcionar copiando sua pasta, sem alterações, para qualquer um dos
  3 projetos-alvo.
- **FR-025**: As instruções principais da skill e seus arquivos de referência MUST NOT conter
  regras específicas de um projeto-alvo (nomes de arquivos, rotas, tabelas ou domínios); o
  conhecimento MUST ser expresso como heurísticas e padrões genéricos.
- **FR-026**: Os arquivos de referência MUST cobrir as 5 áreas de conhecimento: heurísticas de
  análise de projeto, catálogo de anti-patterns, template de relatório, guidelines da
  arquitetura MVC alvo e playbook de refatoração.

**Entrega**

- **FR-027**: O repositório MUST conter o relatório da Fase 2 de cada projeto em
  `reports/audit-project-{1,2,3}.md` na raiz.
- **FR-028**: O código refatorado de cada projeto MUST ser commitado no repositório, e cada
  execução MUST partir do código original (marcado como baseline no versionamento).
- **FR-029**: O README MUST conter as seções Análise Manual, Construção da Skill, Resultados
  e Como Executar, com o conteúdo exigido pelo enunciado.

### Key Entities

- **Perfil do Projeto**: resultado da Fase 1 — linguagem, framework/versão, dependências,
  banco e tabelas, domínio, classificação da arquitetura, arquivos analisados, como executar.
- **Anti-pattern (catálogo)**: nome, severidade-base, sinais de detecção, exemplos de
  ocorrência e referência à transformação do playbook que o corrige.
- **Finding**: ocorrência concreta de um anti-pattern — severidade, título, arquivo, linhas,
  descrição, impacto, recomendação.
- **Relatório de Auditoria**: cabeçalho do projeto, resumo por severidade, lista ordenada de
  findings, seção de APIs deprecated, total.
- **Transformação (playbook)**: padrão de refatoração com problema, passos e código
  antes/depois, ligado a um ou mais anti-patterns.
- **Referência de Comportamento**: para cada endpoint original — método, rota, requisição de
  teste, código de status e formato de resposta antes e depois da refatoração.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 3 de 3 projetos, a Fase 1 informa corretamente linguagem, framework e
  domínio, e o número de arquivos analisados coincide com a contagem real de arquivos-fonte.
- **SC-002**: Em 3 de 3 projetos, a Fase 2 reporta pelo menos 5 findings, com pelo menos 1
  CRITICAL ou HIGH.
- **SC-003**: Em cada projeto, pelo menos 5 dos problemas documentados na análise manual
  aparecem no relatório da skill.
- **SC-004**: 100% dos findings citam arquivo e linhas que existem e correspondem ao problema
  descrito (conferência manual de todos os findings dos 3 relatórios).
- **SC-005**: Em 3 de 3 projetos, nenhum arquivo de código é alterado entre o início da
  execução e a confirmação do usuário (verificável pelo versionamento: só o relatório muda).
- **SC-006**: Em 3 de 3 projetos, após a Fase 3, a aplicação inicia sem erros e 100% dos
  endpoints originais respondem — com o mesmo status de sucesso da referência ou com a
  mudança intencional listada no resumo.
- **SC-007**: Em 3 de 3 projetos, o checklist de validação do enunciado (Fases 1, 2 e 3) fica
  com todos os itens marcados.
- **SC-008**: A pasta da skill é idêntica, byte a byte, nos 3 projetos.
- **SC-009**: Após a refatoração, nenhuma credencial ou chave fica literal no código-fonte dos
  3 projetos.
- **SC-010**: O catálogo de anti-patterns tem ≥ 8 entradas cobrindo as 4 severidades e o
  playbook tem ≥ 8 transformações com exemplo antes/depois.

## Assumptions

- A ferramenta agêntica é o Claude Code (exigência de formato do enunciado: skill em
  `.claude/skills/refactor-arch/` com `SKILL.md` e referências em Markdown); por ser uma
  restrição do enunciado, e não uma escolha de implementação, ela aparece nesta spec.
- A skill é executada em sessão interativa, para que a pausa de confirmação da Fase 2 possa
  receber a resposta do usuário.
- A máquina tem os runtimes dos projetos-alvo (Python 3 e Node.js) e acesso ao registro de
  pacotes para instalar dependências em ambiente isolado por projeto.
- **Destino do relatório**: por padrão a skill salva o relatório dentro do projeto auditado
  (fora do código-fonte); o arquivo é então movido/copiado para
  `reports/audit-project-N.md` na raiz do repositório como parte da entrega. Um argumento
  opcional na invocação permite apontar diretamente outro caminho.
- **Autenticação nas rotas administrativas protegidas**: um token simples lido de variável
  de ambiente é suficiente para o escopo do desafio; um sistema completo de usuários/sessões
  está fora do escopo.
- Não existem testes automatizados nos projetos-alvo; a validação de comportamento é feita
  por chamadas reais aos endpoints, e criar uma suíte de testes completa está fora do escopo.
- Os problemas documentados em `docs/analise-manual.md` são a referência para o SC-003.
- Cada execução parte do estado marcado pela tag de versionamento `baseline`.
