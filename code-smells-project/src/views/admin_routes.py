from flask import Blueprint

from src.controllers import admin_controller as c
from src.middlewares.auth import require_admin

bp = Blueprint("admin", __name__)

bp.add_url_rule("/admin/reset-db", "reset_database", require_admin(c.reset_database), methods=["POST"])
bp.add_url_rule("/admin/query", "executar_query", require_admin(c.executar_query), methods=["POST"])
