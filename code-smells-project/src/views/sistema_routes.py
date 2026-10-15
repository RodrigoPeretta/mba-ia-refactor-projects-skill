from flask import Blueprint

from src.controllers import sistema_controller as c

bp = Blueprint("sistema", __name__)

bp.add_url_rule("/", "index", c.index, methods=["GET"])
bp.add_url_rule("/health", "health_check", c.health_check, methods=["GET"])
