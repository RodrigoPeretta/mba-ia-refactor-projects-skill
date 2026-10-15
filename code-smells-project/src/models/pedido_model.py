"""Acesso a dados das entidades Pedido e Item de pedido."""
from src.config import settings


def inserir(db, usuario_id, total):
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, settings.STATUS_PEDIDO_INICIAL, total),
    )
    return cursor.lastrowid


def inserir_item(db, pedido_id, produto_id, quantidade, preco_unitario):
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def listar(db, usuario_id=None):
    """Pedidos com seus itens, numa única query (LEFT JOIN), opcionalmente por usuário."""
    sql = """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
               pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
    """
    params = []
    if usuario_id is not None:
        sql += " WHERE p.usuario_id = ?"
        params.append(usuario_id)
    sql += " ORDER BY p.id, i.id"

    pedidos = {}
    for row in db.execute(sql, params).fetchall():
        pedido = pedidos.get(row["id"])
        if pedido is None:
            pedido = pedidos[row["id"]] = {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_nome"] is not None else "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def existe(db, pedido_id):
    return db.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def atualizar_status(db, pedido_id, status):
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def agregados(db):
    """Quantidade, soma e contagem por status numa única query."""
    row = db.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(status = 'pendente'), 0) AS pendentes,
               COALESCE(SUM(status = 'aprovado'), 0) AS aprovados,
               COALESCE(SUM(status = 'cancelado'), 0) AS cancelados
        FROM pedidos
        """
    ).fetchone()
    return dict(row)


def contar(db):
    return db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
