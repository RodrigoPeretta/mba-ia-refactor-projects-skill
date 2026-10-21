"""Regras e consultas de usuários, incluindo autenticação por e-mail e senha."""
import logging

from sqlalchemy import delete, func, select

from database import commit, db
from models.task import Task
from models.user import User
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from utils.helpers import utcnow

logger = logging.getLogger(__name__)


def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def task_counts_by_user():
    rows = db.session.execute(
        select(Task.user_id, func.count()).where(Task.user_id.isnot(None)).group_by(Task.user_id)
    ).all()
    return dict(rows)


def list_users():
    counts = task_counts_by_user()
    users = db.session.scalars(select(User).order_by(User.id))
    return [{**user.to_dict(), 'task_count': counts.get(user.id, 0)} for user in users]


def tasks_of(user_id):
    return db.session.scalars(select(Task).where(Task.user_id == user_id).order_by(Task.id)).all()


def user_detail(user):
    return {**user.to_dict(), 'tasks': [task.to_dict() for task in tasks_of(user.id)]}


def user_tasks(user):
    now = utcnow()
    return [task.to_summary_dict(now) for task in tasks_of(user.id)]


def _ensure_email_available(email, current_user_id=None):
    existing = db.session.scalar(select(User).where(User.email == email))
    if existing is not None and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def create_user(fields):
    _ensure_email_available(fields['email'])
    user = User(name=fields['name'], email=fields['email'], role=fields['role'])
    user.set_password(fields['password'])
    db.session.add(user)
    commit('Erro ao criar usuário')
    logger.info('Usuário criado: id=%s', user.id)
    return user


def update_user(user, fields):
    if 'email' in fields:
        _ensure_email_available(fields['email'], current_user_id=user.id)
    for name in ('name', 'email', 'role', 'active'):
        if name in fields:
            setattr(user, name, fields[name])
    if 'password' in fields:
        user.set_password(fields['password'])
    commit('Erro ao atualizar')
    logger.info('Usuário atualizado: id=%s', user.id)
    return user


def delete_user(user):
    """Exclui o usuário e as tasks dele na mesma transação."""
    user_id = user.id
    db.session.execute(delete(Task).where(Task.user_id == user_id))
    db.session.delete(user)
    commit('Erro ao deletar')
    logger.info('Usuário deletado: id=%s', user_id)


def authenticate(email, password):
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    return user
