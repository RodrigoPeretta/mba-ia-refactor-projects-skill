from flask import jsonify, request

from controllers.validators import parse_int_param, validate_task
from middlewares.auth import ensure_can_assign, ensure_owner_or_admin
from services import task_service


def list_tasks():
    return jsonify(task_service.list_with_details()), 200


def get_task(task_id):
    return jsonify(task_service.get_detail(task_id)), 200


def create_task():
    fields = validate_task(request.get_json(silent=True))
    ensure_can_assign(fields.get('user_id'))
    task = task_service.create(fields)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = task_service.get_or_404(task_id)
    ensure_owner_or_admin(task.user_id)
    fields = validate_task(request.get_json(silent=True), partial=True)
    if 'user_id' in fields:
        ensure_can_assign(fields['user_id'])
    task = task_service.update(task, fields)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = task_service.get_or_404(task_id)
    ensure_owner_or_admin(task.user_id)
    task_service.delete(task)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    results = task_service.search(
        text=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=parse_int_param(request.args.get('priority', ''), 'priority'),
        user_id=parse_int_param(request.args.get('user_id', ''), 'user_id'),
    )
    return jsonify(results), 200


def task_stats():
    return jsonify(task_service.stats()), 200
