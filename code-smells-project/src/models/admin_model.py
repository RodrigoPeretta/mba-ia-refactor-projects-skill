"""Operações administrativas sobre o banco (somente leitura e limpeza)."""
import sqlite3

from src.exceptions import AppError


def consultar_somente_leitura(db, sql):
    """Executa uma única consulta SELECT com a conexão em modo somente leitura."""
    db.execute("PRAGMA query_only = ON")
    try:
        rows = db.execute(sql).fetchall()
    except sqlite3.Error as exc:
        raise AppError("Erro ao executar a consulta") from exc
    finally:
        db.execute("PRAGMA query_only = OFF")
    return [dict(row) for row in rows]


def limpar_tabelas(db):
    with db:
        db.execute("DELETE FROM itens_pedido")
        db.execute("DELETE FROM pedidos")
        db.execute("DELETE FROM produtos")
        db.execute("DELETE FROM usuarios")
