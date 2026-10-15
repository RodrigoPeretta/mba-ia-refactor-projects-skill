from flask import Blueprint

from src.controllers import relatorio_controller as c

bp = Blueprint("relatorios", __name__)

bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", c.relatorio_vendas, methods=["GET"])
