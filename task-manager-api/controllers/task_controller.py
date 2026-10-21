from flask import jsonify, request

from controllers import validators
from middlewares.auth import current_user, ensure_owner_or_admin, is_admin
from services import task_service
from utils.errors import ForbiddenError


def _ensure_can_assign(user_id):
    """Atribuir a task a outro usuário exige admin; a si mesmo ou a ninguém, basta estar autenticado."""
    user = current_user()
    if user_id is None or is_admin() or (user is not None and user.id == user_id):
        return
    raise ForbiddenError('Acesso negado')


def list_tasks():
    return jsonify(task_service.list_tasks()), 200


def get_task(task_id):
    return jsonify(task_service.task_detail(task_service.get_task(task_id))), 200


def create_task():
    fields = validators.validate_task_create(request.get_json(silent=True))
    _ensure_can_assign(fields['user_id'])
    return jsonify(task_service.create_task(fields).to_dict()), 201


def update_task(task_id):
    task = task_service.get_task(task_id)
    ensure_owner_or_admin(task.user_id)
    fields = validators.validate_task_update(request.get_json(silent=True))
    if 'user_id' in fields:
        _ensure_can_assign(fields['user_id'])
    return jsonify(task_service.update_task(task, fields).to_dict()), 200


def delete_task(task_id):
    task = task_service.get_task(task_id)
    ensure_owner_or_admin(task.user_id)
    task_service.delete_task(task)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    args = request.args
    results = task_service.search_tasks(
        text=args.get('q', ''),
        status=args.get('status', ''),
        priority=validators.parse_int_param(args.get('priority', ''), 'Prioridade inválida'),
        user_id=validators.parse_int_param(args.get('user_id', ''), 'Usuário inválido'),
    )
    return jsonify(results), 200


def task_stats():
    return jsonify(task_service.task_stats()), 200
