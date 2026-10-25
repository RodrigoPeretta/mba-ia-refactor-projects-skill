"""Autenticação por token de sessão assinado e autorização dono-ou-admin."""
import hmac
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from config import settings
from database import db
from models.user import User
from utils.errors import AppError

_SALT = 'session-token'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT)


def issue_token(user):
    return _serializer().dumps({'user_id': user.id})


def _user_from_bearer():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    try:
        data = _serializer().loads(header[7:], max_age=settings.SESSION_TOKEN_MAX_AGE)
    except BadSignature:  # inclui SignatureExpired
        return None
    user = db.session.get(User, data.get('user_id'))
    return user if user is not None and user.active else None


def _is_admin_token():
    """X-Admin-Token válido (credencial de operador). Sem ADMIN_TOKEN, sempre falso."""
    token = request.headers.get('X-Admin-Token', '')
    return bool(settings.ADMIN_TOKEN) and hmac.compare_digest(token, settings.ADMIN_TOKEN)


def load_identity():
    """Carrega a identidade da requisição em g, sem exigir credencial."""
    g.current_user = _user_from_bearer()
    g.admin_token = _is_admin_token()


def is_authenticated():
    return g.get('current_user') is not None or g.get('admin_token', False)


def is_admin():
    user = g.get('current_user')
    return g.get('admin_token', False) or (user is not None and user.is_admin())


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        load_identity()
        if not is_authenticated():
            raise AppError('Autenticação necessária', 401)
        return view(*args, **kwargs)
    return wrapper


def ensure_admin():
    if not is_authenticated():
        raise AppError('Autenticação necessária', 401)
    if not is_admin():
        raise AppError('Acesso negado', 403)


def ensure_owner_or_admin(owner_id):
    user = g.get('current_user')
    if is_admin() or (user is not None and owner_id is not None and user.id == owner_id):
        return
    raise AppError('Acesso negado', 403)


def ensure_can_assign(owner_id):
    """Campo de dono vindo do corpo: só o próprio usuário ou um admin define."""
    if owner_id is None:
        return
    ensure_owner_or_admin(owner_id)
