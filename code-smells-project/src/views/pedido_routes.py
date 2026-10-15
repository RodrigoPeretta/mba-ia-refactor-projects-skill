from flask import Blueprint

from src.controllers import pedido_controller as c

bp = Blueprint("pedidos", __name__)

bp.add_url_rule("/pedidos", "criar_pedido", c.criar_pedido, methods=["POST"])
bp.add_url_rule("/pedidos", "listar_todos_pedidos", c.listar_todos_pedidos, methods=["GET"])
bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", c.listar_pedidos_usuario, methods=["GET"])
bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", c.atualizar_status_pedido, methods=["PUT"])
