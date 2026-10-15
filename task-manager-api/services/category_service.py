"""Persistência de categorias."""
from sqlalchemy import func

from database import commit, db
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError


def get_or_404(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_with_task_count():
    rows = db.session.execute(
        db.select(Category, func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
    ).all()
    return [{**category.to_dict(), 'task_count': count} for category, count in rows]


def create(fields):
    category = Category(**fields)
    db.session.add(category)
    commit()
    return category


def update(category, fields):
    for name, value in fields.items():
        setattr(category, name, value)
    commit()
    return category


def delete(category):
    """As tasks da categoria ficam sem categoria (category_id = NULL), como antes."""
    db.session.delete(category)
    commit()
