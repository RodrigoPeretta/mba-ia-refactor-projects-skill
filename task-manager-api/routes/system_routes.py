from flask import Blueprint

from controllers import system_controller as controller

system_bp = Blueprint('system', __name__)

system_bp.add_url_rule('/health', view_func=controller.health, methods=['GET'])
system_bp.add_url_rule('/', view_func=controller.index, methods=['GET'])
