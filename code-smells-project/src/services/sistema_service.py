"""Estado operacional da aplicação (health check)."""
from src.models import pedido_model, produto_model, usuario_model


def contagens(db):
    return {
        "produtos": produto_model.contar(db),
        "usuarios": usuario_model.contar(db),
        "pedidos": pedido_model.contar(db),
    }
