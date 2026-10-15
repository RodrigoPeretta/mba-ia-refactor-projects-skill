import logging

from flask import jsonify

from src.config import settings
from src.database import get_db
from src.services import sistema_service

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": settings.APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    try:
        counts = sistema_service.contagens(get_db())
    except Exception:  # o health check responde o próprio formato de falha
        logger.exception("Health check falhou")
        return jsonify({"status": "erro", "detalhes": "Banco de dados indisponível"}), 500
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": settings.APP_VERSION,
        "ambiente": settings.APP_ENV,
    }), 200
