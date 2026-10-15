from flask import jsonify, request

from controllers.validators import parse_int_param, validate_task
from services import task_service


def list_tasks():
    return jsonify(task_service.list_with_owner_names()), 200


def get_task(task_id):
    task = task_service.get_or_404(task_id)
    return jsonify({**task.to_dict(), 'overdue': task.is_overdue()}), 200


def create_task():
    fields = validate_task(request.get_json(silent=True))
    task = task_service.create(fields)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = task_service.get_or_404(task_id)
    fields = validate_task(request.get_json(silent=True), partial=True)
    task = task_service.update(task, fields)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task_service.delete(task_service.get_or_404(task_id))
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    tasks = task_service.search(
        text=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=parse_int_param(request.args.get('priority', ''), 'priority'),
        user_id=parse_int_param(request.args.get('user_id', ''), 'user_id'),
    )
    return jsonify([task.to_dict() for task in tasks]), 200


def task_stats():
    return jsonify(task_service.stats()), 200
