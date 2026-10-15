from flask import Blueprint

from src.controllers import produto_controller as c

bp = Blueprint("produtos", __name__)

bp.add_url_rule("/produtos", "listar_produtos", c.listar_produtos, methods=["GET"])
bp.add_url_rule("/produtos/busca", "buscar_produtos", c.buscar_produtos, methods=["GET"])
bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", c.buscar_produto, methods=["GET"])
bp.add_url_rule("/produtos", "criar_produto", c.criar_produto, methods=["POST"])
bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", c.atualizar_produto, methods=["PUT"])
bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", c.deletar_produto, methods=["DELETE"])
