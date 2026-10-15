"""Regras de negócio e persistência de usuários, incluindo login."""
import logging

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func

from database import commit, db
from models.task import Task
from models.user import User
from utils.errors import AppError, ConflictError, ForbiddenError, NotFoundError

logger = logging.getLogger(__name__)

_TOKEN_SALT = 'task-manager-login'


def get_or_404(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def list_with_task_count():
    rows = db.session.execute(
        db.select(User, func.count(Task.id))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    ).all()
    return [{**user.to_dict(), 'task_count': count} for user, count in rows]


def ensure_email_available(email, current_user_id=None):
    existing = db.session.scalar(db.select(User).where(User.email == email))
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def create(name, email, password, role):
    ensure_email_available(email)
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    commit()
    logger.info('Usuário criado: id=%s', user.id)
    return user


def update(user, fields):
    fields = dict(fields)
    if 'email' in fields:
        ensure_email_available(fields['email'], current_user_id=user.id)
    password = fields.pop('password', None)
    for name, value in fields.items():
        setattr(user, name, value)
    if password is not None:
        user.set_password(password)
    commit()
    return user


def delete(user):
    """Exclui o usuário e as tasks dele na mesma transação (cascade do relacionamento)."""
    user_id = user.id
    db.session.delete(user)
    commit()
    logger.info('Usuário deletado: id=%s', user_id)


def authenticate(email, password):
    user = db.session.scalar(db.select(User).where(User.email == email))
    if not user or not user.check_password(password):
        raise AppError('Credenciais inválidas', 401)
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    if user.has_legacy_password_hash():
        # Regrava o hash MD5 legado com o algoritmo atual no primeiro login bem-sucedido.
        user.set_password(password)
        commit()
    return user


def issue_token(user, secret_key):
    """Token assinado (não previsível) com o id do usuário."""
    return URLSafeTimedSerializer(secret_key, salt=_TOKEN_SALT).dumps({'user_id': user.id})
