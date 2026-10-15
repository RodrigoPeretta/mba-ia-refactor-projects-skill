"""Regras de negócio de pedidos (coordena pedidos, itens e estoque de produtos)."""
from src.exceptions import BusinessRuleError, NotFoundError
from src.models import pedido_model, produto_model
from src.services import notificacao_service


def criar_pedido(db, usuario_id, itens):
    """Valida estoque, grava pedido + itens e baixa o estoque numa única transação."""
    produtos = produto_model.buscar_varios(db, [item["produto_id"] for item in itens])

    total = 0
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise BusinessRuleError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise BusinessRuleError(f"Estoque insuficiente para {produto['nome']}")
        total = total + (produto["preco"] * item["quantidade"])

    with db:  # BEGIN ... COMMIT; ROLLBACK automático em qualquer exceção
        pedido_id = pedido_model.inserir(db, usuario_id, total)
        for item in itens:
            produto = produtos[item["produto_id"]]
            pedido_model.inserir_item(db, pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            if not produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"]):
                raise BusinessRuleError(f"Estoque insuficiente para {produto['nome']}")

    notificacao_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_pedidos(db, usuario_id=None):
    return pedido_model.listar(db, usuario_id)


def atualizar_status(db, pedido_id, status):
    if not pedido_model.existe(db, pedido_id):
        raise NotFoundError("Pedido não encontrado")
    pedido_model.atualizar_status(db, pedido_id, status)
    notificacao_service.status_alterado(pedido_id, status)
