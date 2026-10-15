"""Tratamento de erro centralizado: toda falha vira JSON no envelope da API."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.exceptions import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app_error(err):
        corpo = {"erro": err.message}
        if err.sucesso is not None:
            corpo["sucesso"] = err.sucesso
        return jsonify(corpo), err.status

    @app.errorhandler(HTTPException)
    def _http_error(err):
        return jsonify({"erro": err.description}), err.code

    @app.errorhandler(Exception)
    def _unexpected(err):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno"}), 500
