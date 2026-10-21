"""Error handler central: toda resposta de erro é JSON no formato `{"error": <mensagem>}`."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db
from utils.errors import AppError

logger = logging.getLogger(__name__)

_HTTP_MESSAGES = {
    400: 'Dados inválidos',
    404: 'Recurso não encontrado',
    405: 'Método não permitido',
}


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(HTTPException)
    def _http_error(err):
        return jsonify({'error': _HTTP_MESSAGES.get(err.code, err.description)}), err.code

    @app.errorhandler(Exception)
    def _unexpected(err):
        db.session.rollback()
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
