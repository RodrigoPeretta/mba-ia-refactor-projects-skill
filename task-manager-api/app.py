"""Composition root e entry point da Task Manager API (`python app.py`)."""
import logging

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  registra os models antes do create_all
from config import settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def create_app():
    logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    if settings.SECRET_KEY_GENERATED:
        logger.warning('SECRET_KEY não definida; usando chave temporária (tokens expiram a cada reinício)')

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    db.init_app(app)
    app.extensions['notification_service'] = NotificationService(
        settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD
    )

    register_error_handlers(app)
    for blueprint in (system_bp, task_bp, user_bp, category_bp, report_bp):
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
