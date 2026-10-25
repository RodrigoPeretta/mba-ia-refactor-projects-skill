import logging

from sqlalchemy.exc import SQLAlchemyError

from database import db
from utils.errors import AppError

logger = logging.getLogger(__name__)


def commit(error_message):
    """Confirma a unidade de trabalho da requisição; em falha, desfaz tudo e responde 500."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception(error_message)
        raise AppError(error_message, 500)
