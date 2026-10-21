from flask import jsonify, request

from controllers import validators
from services import category_service


def list_categories():
    return jsonify(category_service.list_categories()), 200


def create_category():
    fields = validators.validate_category_create(request.get_json(silent=True))
    return jsonify(category_service.create_category(fields).to_dict()), 201


def update_category(cat_id):
    category = category_service.get_category(cat_id)
    fields = validators.validate_category_update(request.get_json(silent=True))
    return jsonify(category_service.update_category(category, fields).to_dict()), 200


def delete_category(cat_id):
    category_service.delete_category(category_service.get_category(cat_id))
    return jsonify({'message': 'Categoria deletada'}), 200
