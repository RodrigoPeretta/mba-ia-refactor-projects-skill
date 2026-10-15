"""Composition root e entry point: cria a aplicação e conecta as camadas."""
import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database import init_db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def create_app():
    logging.basicConfig(level=settings.LOG_LEVEL,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    if not settings.SECRET_KEY_FROM_ENV:
        logger.warning('SECRET_KEY não definida; usando chave temporária (tokens não sobrevivem a reinícios)')
    if not settings.ADMIN_TOKEN:
        logger.warning('ADMIN_TOKEN não definido; rotas administrativas responderão 403')

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    init_db(app)

    app.extensions['notification_service'] = NotificationService(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        user=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
    )

    for blueprint in (system_bp, task_bp, user_bp, category_bp, report_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
