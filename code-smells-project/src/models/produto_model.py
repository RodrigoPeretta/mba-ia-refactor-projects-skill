"""Acesso a dados da entidade Produto."""

PUBLIC_FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def to_dict(row):
    return {campo: row[campo] for campo in PUBLIC_FIELDS}


def listar(db):
    return [to_dict(row) for row in db.execute("SELECT * FROM produtos").fetchall()]


def buscar_por_id(db, produto_id):
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return to_dict(row) if row else None


def buscar(db, termo=None, categoria=None, preco_min=None, preco_max=None):
    clausulas, params = ["1=1"], []
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clausulas.append("categoria = ?")
        params.append(categoria)
    if preco_min:
        clausulas.append("preco >= ?")
        params.append(preco_min)
    if preco_max:
        clausulas.append("preco <= ?")
        params.append(preco_max)
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(clausulas)
    return [to_dict(row) for row in db.execute(sql, params).fetchall()]


def criar(db, nome, descricao, preco, estoque, categoria):
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(db, produto_id, nome, descricao, preco, estoque, categoria):
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def deletar(db, produto_id):
    with db:
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def buscar_varios(db, produto_ids):
    """Produtos por id, num dicionário {id: row} (uma única query)."""
    ids = list(set(produto_ids))
    if not ids:
        return {}
    marcadores = ",".join("?" for _ in ids)
    rows = db.execute(f"SELECT * FROM produtos WHERE id IN ({marcadores})", ids).fetchall()
    return {row["id"]: row for row in rows}


def baixar_estoque(db, produto_id, quantidade):
    """Decrementa o estoque de forma atômica; retorna False se não houver saldo."""
    cursor = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount == 1


def contar(db):
    return db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
