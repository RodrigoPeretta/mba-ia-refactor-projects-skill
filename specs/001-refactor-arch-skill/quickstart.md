# Quickstart: validar a skill `refactor-arch` ponta a ponta

Roteiro para provar que a skill atende à spec em cada projeto. Formatos de saída:
[contracts/skill-interface.md](contracts/skill-interface.md). Estruturas:
[data-model.md](data-model.md).

## Pré-requisitos

- Claude Code CLI instalado (`claude --version`).
- Python 3 e Node.js no PATH; `curl` disponível.
- Repositório clonado com a tag `baseline` (código original dos 3 projetos).

## 1. Distribuir a skill (fonte da verdade: `code-smells-project`)

```bash
SRC=code-smells-project/.claude/skills/refactor-arch
for p in ecommerce-api-legacy task-manager-api; do
  rm -rf "$p/.claude/skills/refactor-arch"; mkdir -p "$p/.claude/skills"
  cp -r "$SRC" "$p/.claude/skills/"
done
# SC-008: as três cópias devem ter o mesmo hash
for p in code-smells-project ecommerce-api-legacy task-manager-api; do
  (cd "$p/.claude/skills/refactor-arch" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum)
done
```

## 2. Partir do código original

```bash
git checkout baseline -- <projeto>/      # restaura só o código do projeto
git clean -fdx <projeto>/ -e .claude/    # remove artefatos gerados (bancos, .refactor-arch/, venvs)
```

## 3. Cenário A — recusa (Princípio II, SC-005)

```bash
cd <projeto> && claude "/refactor-arch"
# responder: n
git status --short .    # esperado: apenas .refactor-arch/ (relatório) como novo
```

Conferir no relatório: template seguido, ≥ 5 findings, ≥ 1 CRITICAL/HIGH, ordem
CRITICAL → LOW, seção de APIs deprecated, e que cada `arquivo:linha` aponta para o problema
descrito (SC-002, SC-004).

## 4. Cenário B — refatoração completa

```bash
cd <projeto> && claude "/refactor-arch"
# responder: y
```

Esperado ao final:
- `.refactor-arch/behavior-before.md` e `.refactor-arch/validation-after.md` existem, e a
  comparação não tem nenhum `REGRESSION` (SC-006).
- Bloco `PHASE 3: REFACTORING COMPLETE` com a nova árvore, validação ✓ e mudanças de
  contrato listadas.
- Nenhum servidor ficou rodando: a porta do projeto está livre.

Verificação independente da skill:
- Subir a aplicação com o comando original do README e chamar alguns endpoints.
- Buscar segredos literais no código: nenhum valor como chave, senha ou token hardcoded (SC-009).

## 5. Entregar

```bash
cp <projeto>/.refactor-arch/audit-report.md reports/audit-project-N.md
git add <projeto> reports/audit-project-N.md && git commit -m "refactor(<projeto>): ..."
```

Marcar o checklist de validação do enunciado para o projeto no README (SC-007).

## 6. Iterar

Se algum critério falhar: ajustar a skill em `code-smells-project/.claude/skills/refactor-arch/`,
registrar a mudança e o motivo no README, voltar ao passo 1 e refazer os projetos
afetados a partir do passo 2.

| Projeto | Comando de execução original | Porta | Preparo |
|---|---|---|---|
| code-smells-project | `python app.py` | 5000 | — (seed automático no boot) |
| ecommerce-api-legacy | `npm start` | 3000 | `npm install` |
| task-manager-api | `python app.py` | 5000 | `python seed.py` antes do primeiro boot |
