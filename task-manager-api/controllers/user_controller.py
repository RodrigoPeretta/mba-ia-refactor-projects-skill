from flask import current_app, jsonify, request

from config import settings
from controllers.validators import (validate_login, validate_role, validate_user_create,
                                    validate_user_update)
from middlewares.auth import ensure_admin
from services import task_service, user_service
from utils.helpers import utcnow


def list_users():
    return jsonify(user_service.list_with_task_count()), 200


def get_user(user_id):
    user = user_service.get_or_404(user_id)
    tasks = task_service.list_by_user(user_id)
    return jsonify({**user.to_dict(), 'tasks': [task.to_dict() for task in tasks]}), 200


def create_user():
    data = validate_user_create(request.get_json(silent=True))
    user_service.ensure_email_available(data['email'])
    validate_role(data['role'])
    if data['role'] != settings.DEFAULT_ROLE:
        # Papel privilegiado só pode ser atribuído por um administrador.
        ensure_admin()
    user = user_service.create(**data)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = user_service.get_or_404(user_id)
    fields = validate_user_update(request.get_json(silent=True))
    if 'role' in fields or 'active' in fields:
        # Alterar papel ou ativação de uma conta é operação administrativa.
        ensure_admin()
    user = user_service.update(user, fields)
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user_service.delete(user_service.get_or_404(user_id))
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user_service.get_or_404(user_id)
    now = utcnow()
    tasks = task_service.list_by_user(user_id)
    return jsonify([task.to_summary_dict(now) for task in tasks]), 200


def login():
    email, password = validate_login(request.get_json(silent=True))
    user = user_service.authenticate(email, password)
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': user_service.issue_token(user, current_app.config['SECRET_KEY']),
    }), 200
