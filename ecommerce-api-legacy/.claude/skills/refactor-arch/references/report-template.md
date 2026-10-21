# Report Template

Formatos obrigatórios das saídas das 3 fases. Rótulos e cabeçalhos ficam **exatamente** como
abaixo (em inglês); o conteúdo descritivo é escrito em português (pt-BR). Tudo entre `<...>`
é preenchido com dados do projeto; nada de exemplo deve sobrar no texto final.

---

## Fase 1 — Project Analysis

Impresso no terminal, dentro de um bloco de código:

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão, se declarada>
Framework:     <framework> <versão exatamente como no manifesto>
Dependencies:  <dependências diretas, separadas por vírgula>
Database:      <banco> (<forma de acesso: SQL cru via driver X | ORM Y>)
Domain:        <domínio em uma linha> (<entidades principais>)
Architecture:  <Monolítica | Parcialmente em camadas | Em camadas> — <justificativa curta>
Source files:  <N> files analyzed (~<L> lines)
DB tables:     <tabela1>, <tabela2>, ...
Entry point:   <arquivo> (<comando de execução>, porta <P>)
Endpoints:     <N> (<GET a, POST b, PUT c, DELETE d>)
================================
```

Regras:
- `Source files` conta só arquivos-fonte (regras de exclusão em `project-analysis.md`).
- `DB tables` vem do código (DDL ou models); se não houver banco, escreva `N/A`.
- Se a versão do framework não estiver declarada, escreva `<framework> (versão não declarada)`.

---

## Fase 2 — Architecture Audit Report

O mesmo conteúdo Markdown é impresso no terminal **e** gravado no arquivo do relatório.

```markdown
# ARCHITECTURE AUDIT REPORT

- **Project:** <nome do diretório do projeto>
- **Stack:** <Language> + <Framework>
- **Files:** <N> analyzed | ~<L> lines of code
- **Architecture:** <classificação da Fase 1>

## Summary

CRITICAL: <a> | HIGH: <b> | MEDIUM: <c> | LOW: <d>

## Findings

### [CRITICAL] <Título do anti-pattern ou da variação>
- **ID:** <AP-xx do catálogo>
- **File:** `<caminho>:<linhas>`
- **Description:** <o que está errado, citando o trecho, valor ou chamada relevante>
- **Impact:** <consequência concreta>
- **Recommendation:** <correção> (<RF-xx do playbook>)

### [HIGH] ...

### [MEDIUM] ...

### [LOW] ...

## Deprecated APIs

<Uma das duas formas:>
- <API obsoleta> em `<arquivo>:<linhas>` → <substituto moderno> (finding "<título>")
<ou>
Nenhuma API deprecated encontrada. Verificado: <o que foi conferido — ex.: chamadas de data/hora, métodos de ORM, APIs de buffer/URL/fs, versões das dependências declaradas>.

---

**Total: <N> findings**

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Regras do relatório:
1. **Ordenação**: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade,
   do maior impacto para o menor.
2. **Arquivo e linhas** obrigatórios em todo finding. Formatos aceitos: `app.py:7`,
   `models.py:12-40`, `models.py:28, 47-50, 92`. Quando o mesmo problema aparece em vários
   arquivos, use uma linha `File:` com a lista separada por `;`
   (ex.: `` `a.py:10-12`; `b.py:40` ``).
3. **Agrupamento**: ocorrências do **mesmo** anti-pattern com a **mesma** causa viram um
   único finding com todas as linhas. Anti-patterns diferentes nunca são fundidos, mesmo no
   mesmo trecho.
4. **Consistência**: a soma do Summary = número de blocos `###` = Total.
5. **APIs deprecated** aparecem nos Findings (com severidade própria) **e** são resumidas na
   seção `## Deprecated APIs`. A seção nunca é omitida.
6. **Sem placeholders**: nenhum `<...>` pode sobrar.
7. A última linha é sempre a pergunta de confirmação.

---

## Fase 3 — Refactoring Complete

Impresso no terminal:

````text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
<árvore de diretórios do projeto refatorado, só código e config — sem .venv, node_modules, .git>
```

## Validation
  ✓ Application boots without errors (<comando>, porta <P>)
  ✓ <n>/<n> original endpoints respond as expected (OK: <a>, CHANGED: <b>, REGRESSION: 0)
  ✓ Config extracted to <módulo>; no hardcoded secrets
  ✓ <n>/<n> findings addressed (<p> listed as pending)
  <use ✗ e explique em uma linha em qualquer item que tenha falhado>

## Recommendations Applied (CRITICAL/HIGH)
| Finding | Recommendation clause | Applied in | Validated by |
|---|---|---|---|
| <AP-xx título> | <trecho da recomendação> | <arquivo:linha ou "Pending"> | <passo(s) de validation-after.md> |

## Contract Changes
- <METHOD> <rota>: <o que mudou> — motivo: <finding>
<ou "Nenhuma">

## Dependencies Added
- <pacote>: <justificativa>
<ou "Nenhuma">

## Pending
- <item fora do escopo da refatoração>: <motivo e recomendação>
<ou "Nenhuma">

Evidence: .refactor-arch/behavior-before.md, .refactor-arch/validation-after.md
================================
````

Regras:
- Um item de `Validation` só recebe ✓ se foi efetivamente executado nesta sessão.
- Todo `CHANGED` de `validation-after.md` precisa aparecer em `Contract Changes`.
- Em `Recommendations Applied`, cada cláusula das recomendações CRITICAL/HIGH ocupa uma
  linha. Cláusula de segurança só conta como aplicada se um passo da validação prova o
  efeito (ex.: requisição anônima → 401); sem isso, ela vai para `Pending`.
