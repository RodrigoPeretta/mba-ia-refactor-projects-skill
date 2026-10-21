"""Tokens de sessão assinados e credencial de administrador (sem conhecer HTTP)."""
import hmac

from itsdangerous import BadSignature, URLSafeTimedSerializer

from config import settings
from database import db
from models.user import User

_SALT = 'session-token'


def _serializer():
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt=_SALT)


def issue_token(user):
    return _serializer().dumps({'user_id': user.id})


def user_from_token(token):
    """Usuário ativo dono do token, ou None se o token for inválido, expirado ou de usuário inativo."""
    try:
        data = _serializer().loads(token, max_age=settings.SESSION_TOKEN_MAX_AGE)
    except BadSignature:  # inclui SignatureExpired
        return None
    user_id = data.get('user_id') if isinstance(data, dict) else None
    user = db.session.get(User, user_id) if isinstance(user_id, int) else None
    return user if user is not None and user.active else None


def is_valid_admin_token(token):
    if not settings.ADMIN_TOKEN or not token:
        return False
    return hmac.compare_digest(token.encode(), settings.ADMIN_TOKEN.encode())
