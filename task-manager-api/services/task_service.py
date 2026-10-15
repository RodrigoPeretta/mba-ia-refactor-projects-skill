"""Regras de negócio e persistência de tasks."""
import logging

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import commit, db
from models.category import Category
from models.task import Task
from models.user import User
from utils.errors import NotFoundError
from utils.helpers import calculate_percentage, utcnow

logger = logging.getLogger(__name__)


def get_or_404(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def list_with_owner_names():
    """Todas as tasks com nome do usuário e da categoria (uma única query com JOIN)."""
    now = utcnow()
    tasks = db.session.scalars(
        db.select(Task)
        .options(joinedload(Task.user), joinedload(Task.category))
        .order_by(Task.id)
    ).all()
    return [
        {
            **task.to_dict(),
            'overdue': task.is_overdue(now),
            'user_name': task.user.name if task.user else None,
            'category_name': task.category.name if task.category else None,
        }
        for task in tasks
    ]


def _exists(model, pk):
    if not isinstance(pk, int) or isinstance(pk, bool):
        return False
    return db.session.get(model, pk) is not None


def _ensure_references(fields):
    if fields.get('user_id') and not _exists(User, fields['user_id']):
        raise NotFoundError('Usuário não encontrado')
    if fields.get('category_id') and not _exists(Category, fields['category_id']):
        raise NotFoundError('Categoria não encontrada')


def create(fields):
    _ensure_references(fields)
    task = Task(**fields)
    db.session.add(task)
    commit()
    logger.info('Task criada: id=%s', task.id)
    return task


def update(task, fields):
    _ensure_references(fields)
    for name, value in fields.items():
        setattr(task, name, value)
    task.updated_at = utcnow()
    commit()
    logger.info('Task atualizada: id=%s', task.id)
    return task


def delete(task):
    task_id = task.id
    db.session.delete(task)
    commit()
    logger.info('Task deletada: id=%s', task_id)


def search(text=None, status=None, priority=None, user_id=None):
    query = db.select(Task).order_by(Task.id)
    if text:
        query = query.where(db.or_(Task.title.like(f'%{text}%'),
                                   Task.description.like(f'%{text}%')))
    if status:
        query = query.where(Task.status == status)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if user_id is not None:
        query = query.where(Task.user_id == user_id)
    return db.session.scalars(query).all()


def list_by_user(user_id):
    return db.session.scalars(
        db.select(Task).where(Task.user_id == user_id).order_by(Task.id)
    ).all()


def count_by(column):
    """Contagem de tasks agrupada por uma coluna (um único GROUP BY)."""
    rows = db.session.execute(db.select(column, func.count(Task.id)).group_by(column)).all()
    return {value: count for value, count in rows}


def count_overdue(now=None):
    now = now or utcnow()
    return db.session.scalar(db.select(func.count(Task.id)).where(Task.overdue_clause(now)))


def stats():
    by_status = count_by(Task.status)
    total = sum(by_status.values())
    done = by_status.get('done', 0)
    return {
        'total': total,
        'pending': by_status.get('pending', 0),
        'in_progress': by_status.get('in_progress', 0),
        'done': done,
        'cancelled': by_status.get('cancelled', 0),
        'overdue': count_overdue(),
        'completion_rate': calculate_percentage(done, total),
    }
