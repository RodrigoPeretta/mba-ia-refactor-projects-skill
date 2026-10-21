from flask import jsonify, request

from config.settings import DEFAULT_ROLE
from controllers import validators
from middlewares.auth import ensure_admin, ensure_authenticated, ensure_owner_or_admin
from services import auth_service, user_service


def list_users():
    return jsonify(user_service.list_users()), 200


def get_user(user_id):
    return jsonify(user_service.user_detail(user_service.get_user(user_id))), 200


def create_user():
    fields = validators.validate_user_create(request.get_json(silent=True))
    if fields['role'] != DEFAULT_ROLE:
        # cadastro com papel privilegiado só por admin
        ensure_authenticated()
        ensure_admin()
    return jsonify(user_service.create_user(fields).to_dict()), 201


def update_user(user_id):
    user = user_service.get_user(user_id)
    ensure_owner_or_admin(user.id)
    fields = validators.validate_user_update(request.get_json(silent=True))
    if 'role' in fields or 'active' in fields:
        ensure_admin()
    return jsonify(user_service.update_user(user, fields).to_dict()), 200


def delete_user(user_id):
    user = user_service.get_user(user_id)
    ensure_owner_or_admin(user.id)
    user_service.delete_user(user)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    return jsonify(user_service.user_tasks(user_service.get_user(user_id))), 200


def login():
    email, password = validators.validate_login(request.get_json(silent=True))
    user = user_service.authenticate(email, password)
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': auth_service.issue_token(user),
    }), 200
