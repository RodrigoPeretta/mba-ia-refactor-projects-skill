"""Regras e consultas de categorias."""
import logging

from sqlalchemy import func, select

from database import commit, db
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError

logger = logging.getLogger(__name__)


def get_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    counts = dict(
        db.session.execute(
            select(Task.category_id, func.count())
            .where(Task.category_id.isnot(None))
            .group_by(Task.category_id)
        ).all()
    )
    categories = db.session.scalars(select(Category).order_by(Category.id))
    return [{**category.to_dict(), 'task_count': counts.get(category.id, 0)} for category in categories]


def create_category(fields):
    category = Category(**fields)
    db.session.add(category)
    commit('Erro ao criar categoria')
    logger.info('Categoria criada: id=%s', category.id)
    return category


def update_category(category, fields):
    for name, value in fields.items():
        setattr(category, name, value)
    commit('Erro ao atualizar')
    return category


def delete_category(category):
    """As tasks da categoria ficam sem categoria (o ORM anula `category_id` na mesma transação)."""
    category_id = category.id
    db.session.delete(category)
    commit('Erro ao deletar')
    logger.info('Categoria deletada: id=%s', category_id)
