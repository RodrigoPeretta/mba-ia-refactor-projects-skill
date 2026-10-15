"""Proteção de rotas administrativas/destrutivas pelo header X-Admin-Token."""
import hmac
from functools import wraps

from flask import request

from config import settings
from utils.errors import ForbiddenError


def is_admin_request():
    token = request.headers.get('X-Admin-Token', '')
    expected = settings.ADMIN_TOKEN
    # Sem ADMIN_TOKEN configurado, nenhuma requisição é administrativa (fechado por padrão).
    return bool(expected) and hmac.compare_digest(token.encode(), expected.encode())


def ensure_admin():
    if not is_admin_request():
        raise ForbiddenError()


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        ensure_admin()
        return view(*args, **kwargs)
    return wrapper
