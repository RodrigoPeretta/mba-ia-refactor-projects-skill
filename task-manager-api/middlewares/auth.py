"""Autenticação e autorização das rotas.

- Token de sessão: `Authorization: Bearer <token>` emitido pelo `POST /login`.
- Operador: `X-Admin-Token` igual à variável `ADMIN_TOKEN` (sem ela, nunca aceito).
- Admin = operador ou usuário autenticado com papel administrativo.
"""
from functools import wraps

from flask import g, request

from services import auth_service
from utils.errors import ForbiddenError, UnauthorizedError

_BEARER_PREFIX = 'Bearer '


def load_identity():
    if 'current_user' in g:
        return
    header = request.headers.get('Authorization', '')
    token = header[len(_BEARER_PREFIX):] if header.startswith(_BEARER_PREFIX) else None
    g.current_user = auth_service.user_from_token(token) if token else None
    g.admin_token = auth_service.is_valid_admin_token(request.headers.get('X-Admin-Token', ''))


def current_user():
    load_identity()
    return g.current_user


def is_authenticated():
    load_identity()
    return g.current_user is not None or g.admin_token


def is_admin():
    load_identity()
    return g.admin_token or (g.current_user is not None and g.current_user.is_admin())


def ensure_authenticated():
    if not is_authenticated():
        raise UnauthorizedError('Autenticação necessária')


def ensure_admin():
    if not is_admin():
        raise ForbiddenError('Acesso negado')


def ensure_owner_or_admin(owner_id):
    user = current_user()
    if is_admin() or (user is not None and owner_id is not None and user.id == owner_id):
        return
    raise ForbiddenError('Acesso negado')


def require_auth(view):
    """401 sem token de sessão válido (ou X-Admin-Token válido)."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        ensure_authenticated()
        return view(*args, **kwargs)
    return wrapper


def require_admin(view):
    """Rotas administrativas: fechadas por padrão (403) para quem não é admin."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        ensure_admin()
        return view(*args, **kwargs)
    return wrapper
