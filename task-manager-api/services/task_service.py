import logging

from sqlalchemy import func
from sqlalchemy.orm import selectinload

from database import db
from config import settings
from models.category import Category
from models.task import Task
from models.user import User
from services.persistence import commit
from utils.errors import AppError
from utils.helpers import calculate_percentage, utcnow

logger = logging.getLogger(__name__)


def get_or_404(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise AppError('Task não encontrada', 404)
    return task


def _ensure_references(fields):
    if fields.get('user_id') and db.session.get(User, fields['user_id']) is None:
        raise AppError('Usuário não encontrado', 404)
    if fields.get('category_id') and db.session.get(Category, fields['category_id']) is None:
        raise AppError('Categoria não encontrada', 404)


def list_with_details():
    now = utcnow()
    tasks = Task.query.options(selectinload(Task.user), selectinload(Task.category)).all()
    result = []
    for task in tasks:
        data = task.to_dict()
        data['overdue'] = task.is_overdue(now)
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result


def get_detail(task_id):
    task = get_or_404(task_id)
    return {**task.to_dict(), 'overdue': task.is_overdue()}


def create(fields):
    _ensure_references(fields)
    task = Task(
        title=fields['title'],
        description=fields.get('description', ''),
        status=fields.get('status', settings.DEFAULT_STATUS),
        priority=fields.get('priority', settings.DEFAULT_PRIORITY),
        user_id=fields.get('user_id'),
        category_id=fields.get('category_id'),
        due_date=fields.get('due_date'),
        tags=fields.get('tags'),
    )
    db.session.add(task)
    commit('Erro ao criar task')
    logger.info('Task criada: id=%s', task.id)
    return task


def update(task, fields):
    _ensure_references(fields)
    for name, value in fields.items():
        setattr(task, name, value)
    task.updated_at = utcnow()
    commit('Erro ao atualizar')
    logger.info('Task atualizada: id=%s', task.id)
    return task


def delete(task):
    task_id = task.id
    db.session.delete(task)
    commit('Erro ao deletar')
    logger.info('Task deletada: id=%s', task_id)


def search(text=None, status=None, priority=None, user_id=None):
    query = Task.query
    if text:
        query = query.filter(db.or_(Task.title.like(f'%{text}%'),
                                    Task.description.like(f'%{text}%')))
    if status:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    return [task.to_dict() for task in query.all()]


def count_by_status():
    rows = db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    counts = dict(rows)
    return {status: counts.get(status, 0) for status in settings.VALID_STATUSES}


def count_overdue(now):
    return Task.query.filter(Task.overdue_clause(now)).count()


def stats():
    by_status = count_by_status()
    total = Task.query.count()
    return {
        'total': total,
        **by_status,
        'overdue': count_overdue(utcnow()),
        'completion_rate': calculate_percentage(by_status['done'], total),
    }


def list_for_user(user_id):
    now = utcnow()
    return [task.to_brief_dict(now) for task in Task.query.filter_by(user_id=user_id).all()]
