"""Proteção das rotas administrativas por token (fechadas por padrão)."""
import hmac
from functools import wraps

from flask import jsonify, request

from src.config import settings


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        esperado = settings.ADMIN_TOKEN
        if not esperado or not hmac.compare_digest(token.encode(), esperado.encode()):
            return jsonify({"erro": "Acesso negado"}), 403
        return view(*args, **kwargs)
    return wrapper
