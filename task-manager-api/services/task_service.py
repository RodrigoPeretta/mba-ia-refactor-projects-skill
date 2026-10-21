"""Regras e consultas de tasks."""
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from config.settings import DONE_STATUS, TASK_STATUSES
from database import commit, db
from models.category import Category
from models.task import Task
from models.user import User
from utils.errors import NotFoundError
from utils.helpers import calculate_percentage, utcnow

logger = logging.getLogger(__name__)


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def task_detail(task):
    return {**task.to_dict(), 'overdue': task.is_overdue()}


def list_tasks():
    """Tasks com nome do usuário e da categoria, carregados na mesma consulta."""
    query = (
        select(Task)
        .options(joinedload(Task.user), joinedload(Task.category))
        .order_by(Task.id)
    )
    now = utcnow()
    result = []
    for task in db.session.scalars(query):
        data = task.to_dict()
        data['overdue'] = task.is_overdue(now)
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result


def search_tasks(text=None, status=None, priority=None, user_id=None):
    query = select(Task).order_by(Task.id)
    if text:
        pattern = f'%{text}%'
        query = query.where(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
    if status:
        query = query.where(Task.status == status)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if user_id is not None:
        query = query.where(Task.user_id == user_id)
    return [task.to_dict() for task in db.session.scalars(query)]


def count_by_status():
    rows = db.session.execute(select(Task.status, func.count()).group_by(Task.status)).all()
    counts = dict.fromkeys(TASK_STATUSES, 0)
    counts.update({status: total for status, total in rows if status in counts})
    return counts


def count_overdue(now=None):
    return db.session.scalar(
        select(func.count()).select_from(Task).where(Task.overdue_clause(now or utcnow()))
    )


def task_stats():
    total = db.session.scalar(select(func.count()).select_from(Task))
    by_status = count_by_status()
    return {
        'total': total,
        **by_status,
        'overdue': count_overdue(),
        'completion_rate': calculate_percentage(by_status[DONE_STATUS], total),
    }


def _ensure_references(fields):
    if fields.get('user_id') and db.session.get(User, fields['user_id']) is None:
        raise NotFoundError('Usuário não encontrado')
    if fields.get('category_id') and db.session.get(Category, fields['category_id']) is None:
        raise NotFoundError('Categoria não encontrada')


def _apply(task, fields):
    for name in ('title', 'description', 'status', 'priority', 'user_id', 'category_id', 'due_date'):
        if name in fields:
            setattr(task, name, fields[name])
    if 'tags' in fields:
        task.set_tags(fields['tags'])


def create_task(fields):
    _ensure_references(fields)
    task = Task()
    _apply(task, fields)
    db.session.add(task)
    commit('Erro ao criar task')
    logger.info('Task criada: id=%s', task.id)
    return task


def update_task(task, fields):
    _ensure_references(fields)
    _apply(task, fields)
    task.updated_at = utcnow()
    commit('Erro ao atualizar')
    logger.info('Task atualizada: id=%s', task.id)
    return task


def delete_task(task):
    task_id = task.id
    db.session.delete(task)
    commit('Erro ao deletar')
    logger.info('Task deletada: id=%s', task_id)
