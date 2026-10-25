from flask import jsonify, request

from config import settings
from controllers.validators import validate_login, validate_user_create, validate_user_update
from middlewares.auth import ensure_admin, ensure_owner_or_admin, issue_token, load_identity
from services import task_service, user_service


def list_users():
    return jsonify(user_service.list_with_task_count()), 200


def get_user(user_id):
    return jsonify(user_service.get_with_tasks(user_id)), 200


def create_user():
    load_identity()
    fields = validate_user_create(request.get_json(silent=True))
    if fields['role'] != settings.DEFAULT_ROLE:
        ensure_admin()
    user = user_service.create(fields)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = user_service.get_or_404(user_id)
    ensure_owner_or_admin(user.id)
    fields = validate_user_update(request.get_json(silent=True))
    if 'role' in fields or 'active' in fields:
        ensure_admin()
    user = user_service.update(user, fields)
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user = user_service.get_or_404(user_id)
    ensure_owner_or_admin(user.id)
    user_service.delete(user)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user_service.get_or_404(user_id)
    return jsonify(task_service.list_for_user(user_id)), 200


def login():
    email, password = validate_login(request.get_json(silent=True))
    user = user_service.authenticate(email, password)
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user),
    }), 200
