from sqlalchemy import func

from database import db
from config import settings
from models.category import Category
from models.task import Task
from services.persistence import commit
from utils.errors import AppError


def get_or_404(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise AppError('Categoria não encontrada', 404)
    return category


def list_with_task_count():
    counts = dict(db.session.query(Task.category_id, func.count(Task.id))
                  .group_by(Task.category_id).all())
    return [{**category.to_dict(), 'task_count': counts.get(category.id, 0)}
            for category in Category.query.all()]


def create(fields):
    category = Category(name=fields['name'],
                        description=fields.get('description', ''),
                        color=fields.get('color', settings.DEFAULT_COLOR))
    db.session.add(category)
    commit('Erro ao criar categoria')
    return category


def update(category, fields):
    for name, value in fields.items():
        setattr(category, name, value)
    commit('Erro ao atualizar')
    return category


def delete(category):
    db.session.delete(category)
    commit('Erro ao deletar')
