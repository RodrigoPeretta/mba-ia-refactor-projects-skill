"""Composition root: cria a aplicação e conecta config, banco, middlewares e rotas."""
from flask import Flask
from flask_cors import CORS

from src import database
from src.config import settings
from src.middlewares.error_handler import register_error_handlers
from src.views import (
    admin_routes,
    pedido_routes,
    produto_routes,
    relatorio_routes,
    sistema_routes,
    usuario_routes,
)

BLUEPRINTS = (
    produto_routes.bp,
    usuario_routes.bp,
    pedido_routes.bp,
    relatorio_routes.bp,
    sistema_routes.bp,
    admin_routes.bp,
)


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.SECRET_KEY,
        DEBUG=settings.DEBUG,
        DB_PATH=settings.DB_PATH,
    )
    if overrides:
        app.config.update(overrides)

    CORS(app, origins=settings.CORS_ORIGINS)
    database.init_app(app)
    register_error_handlers(app)
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    return app
