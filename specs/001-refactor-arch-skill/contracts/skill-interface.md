# Contract: interface da skill `refactor-arch`

## Invocação

| Forma | Efeito |
|---|---|
| `claude "/refactor-arch"` (dentro da pasta do projeto) | Executa as 3 fases; relatório em `.refactor-arch/audit-report.md` |
| `/refactor-arch` (dentro de uma sessão já aberta na pasta do projeto) | Idem |
| `/refactor-arch <caminho>` | Idem, mas o relatório da Fase 2 é gravado em `<caminho>` (relativo ao projeto) |

- Pré-condição: o diretório de trabalho é a raiz do projeto-alvo.
- A skill só roda por invocação explícita (`disable-model-invocation: true`).

## Saídas no terminal

Os formatos exatos estão em `references/report-template.md`; os blocos obrigatórios são:

1. **Fase 1**: bloco `PHASE 1: PROJECT ANALYSIS` com `Language`, `Framework`,
   `Dependencies`, `Domain`, `Architecture`, `Source files`, `DB tables`.
2. **Fase 2**: bloco `ARCHITECTURE AUDIT REPORT` com cabeçalho (`Project`, `Stack`,
   `Files`), `## Summary`, `## Findings` (cada um com `### [SEVERITY] Título`, `File:`,
   `Description:`, `Impact:`, `Recommendation:`), seção de APIs deprecated, `Total`, e a
   pergunta final: `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`.
3. **Fase 3**: bloco `PHASE 3: REFACTORING COMPLETE` com `## New Project Structure`
   (árvore), `## Validation` (itens ✓/✗), `## Contract Changes` e `## Pending` (itens fora
   do escopo).

## Interação de confirmação

| Resposta do usuário | Comportamento |
|---|---|
| `y`, `yes`, `s`, `sim` (sem diferenciar maiúsculas) | Inicia a Fase 3 |
| Qualquer outra coisa, inclusive vazio | Encerra; informa que nenhum arquivo de código foi alterado e onde está o relatório |

## Arquivos gravados

| Momento | Arquivo | Conteúdo |
|---|---|---|
| Fim da Fase 2 | `.refactor-arch/audit-report.md` (ou `<caminho>`) | Relatório completo da Fase 2 |
| Início da Fase 3 | `.refactor-arch/behavior-before.md` | Referência de comportamento da aplicação original |
| Fim da Fase 3 | `.refactor-arch/validation-after.md` | Mesmo roteiro na aplicação refatorada + comparação |
| Fase 3 | código do projeto, `.env.example` | Refatoração MVC |

Nenhum arquivo além do relatório é criado ou alterado antes da confirmação.

## Variáveis de ambiente introduzidas na refatoração (convenção)

| Variável | Uso | Default de desenvolvimento |
|---|---|---|
| `SECRET_KEY` (ou equivalente da stack) | Chave da aplicação | Valor gerado aleatoriamente em memória no boot, com aviso no log |
| `ADMIN_TOKEN` | Libera rotas administrativas/destrutivas via header `X-Admin-Token` | Não definida → rotas administrativas respondem 403 |
| `DEBUG` | Liga modo debug | `false` |
| `HOST` / `PORT` | Bind do servidor | `127.0.0.1` / porta original do projeto |
| `DATABASE_URL` / `DB_PATH` | Localização do banco | Valor original do projeto |
| Credenciais de integrações (SMTP, gateway de pagamento…) | Segredos de terceiros | Vazias; a integração fica desativada |

Todas documentadas em `.env.example` na raiz do projeto refatorado.
