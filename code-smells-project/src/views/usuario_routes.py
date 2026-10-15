from flask import Blueprint

from src.controllers import usuario_controller as c

bp = Blueprint("usuarios", __name__)

bp.add_url_rule("/usuarios", "listar_usuarios", c.listar_usuarios, methods=["GET"])
bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", c.buscar_usuario, methods=["GET"])
bp.add_url_rule("/usuarios", "criar_usuario", c.criar_usuario, methods=["POST"])
bp.add_url_rule("/login", "login", c.login, methods=["POST"])
