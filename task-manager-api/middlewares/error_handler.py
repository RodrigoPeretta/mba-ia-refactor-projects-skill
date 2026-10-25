import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)

HTTP_MESSAGES = {
    400: 'Dados inválidos',
    404: 'Recurso não encontrado',
    405: 'Método não permitido',
    415: 'Dados inválidos',
}


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({'error': HTTP_MESSAGES.get(err.code, err.description)}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
