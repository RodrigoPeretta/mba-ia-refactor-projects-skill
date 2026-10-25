from flask import Blueprint

from controllers import system_controller as c

system_bp = Blueprint('system', __name__)

system_bp.add_url_rule('/health', view_func=c.health, methods=['GET'])
system_bp.add_url_rule('/', view_func=c.index, methods=['GET'])
