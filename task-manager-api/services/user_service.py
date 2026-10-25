import logging

from sqlalchemy import func

from database import db
from models.task import Task
from models.user import User
from services.persistence import commit
from utils.errors import AppError

logger = logging.getLogger(__name__)


def get_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise AppError('Usuário não encontrado', 404)
    return user


def _ensure_email_available(email, user_id=None):
    existing = User.query.filter_by(email=email).first()
    if existing is not None and existing.id != user_id:
        raise AppError('Email já cadastrado', 409)


def list_with_task_count():
    counts = dict(db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all())
    return [{**user.to_dict(), 'task_count': counts.get(user.id, 0)} for user in User.query.all()]


def get_with_tasks(user_id):
    user = get_or_404(user_id)
    tasks = Task.query.filter_by(user_id=user_id).all()
    return {**user.to_dict(), 'tasks': [task.to_dict() for task in tasks]}


def create(fields):
    _ensure_email_available(fields['email'])
    user = User(name=fields['name'], email=fields['email'], role=fields['role'])
    user.set_password(fields['password'])
    db.session.add(user)
    commit('Erro ao criar usuário')
    logger.info('Usuário criado: id=%s', user.id)
    return user


def update(user, fields):
    if 'email' in fields:
        _ensure_email_available(fields['email'], user.id)
    for name, value in fields.items():
        if name == 'password':
            user.set_password(value)
        else:
            setattr(user, name, value)
    commit('Erro ao atualizar')
    return user


def delete(user):
    """Exclui o usuário e suas tasks numa única transação."""
    user_id = user.id
    Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    db.session.delete(user)
    commit('Erro ao deletar')
    logger.info('Usuário deletado: id=%s', user_id)


def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        raise AppError('Credenciais inválidas', 401)
    if not user.active:
        raise AppError('Usuário inativo', 403)
    return user
