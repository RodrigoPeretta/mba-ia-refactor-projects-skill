from flask import Blueprint

from controllers import user_controller as controller
from middlewares.auth import require_auth

user_bp = Blueprint('users', __name__)

user_bp.add_url_rule('/users', view_func=controller.list_users, methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=controller.get_user, methods=['GET'])
user_bp.add_url_rule('/users', view_func=controller.create_user, methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_auth(controller.update_user), methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_auth(controller.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', view_func=controller.get_user_tasks, methods=['GET'])
user_bp.add_url_rule('/login', view_func=controller.login, methods=['POST'])
