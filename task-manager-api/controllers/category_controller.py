from flask import jsonify, request

from controllers.validators import validate_category
from services import category_service


def list_categories():
    return jsonify(category_service.list_with_task_count()), 200


def create_category():
    fields = validate_category(request.get_json(silent=True))
    category = category_service.create(fields)
    return jsonify(category.to_dict()), 201


def update_category(cat_id):
    category = category_service.get_or_404(cat_id)
    fields = validate_category(request.get_json(silent=True), partial=True)
    category = category_service.update(category, fields)
    return jsonify(category.to_dict()), 200


def delete_category(cat_id):
    category_service.delete(category_service.get_or_404(cat_id))
    return jsonify({'message': 'Categoria deletada'}), 200
