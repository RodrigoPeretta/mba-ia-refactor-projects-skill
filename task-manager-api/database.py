from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Inicializa a extensão e cria as tabelas que ainda não existem."""
    db.init_app(app)
    with app.app_context():
        import models  # noqa: F401 — registra os models no metadata antes do create_all
        db.create_all()


def commit():
    """Confirma a unidade de trabalho; desfaz tudo se o commit falhar."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
