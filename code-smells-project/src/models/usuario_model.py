"""Acesso a dados da entidade Usuário (a senha nunca sai deste módulo)."""
from werkzeug.security import check_password_hash, generate_password_hash

from src.config import settings

PUBLIC_FIELDS = ("id", "nome", "email", "tipo", "criado_em")
LOGIN_FIELDS = ("id", "nome", "email", "tipo")


def to_dict(row, campos=PUBLIC_FIELDS):
    return {campo: row[campo] for campo in campos}


def listar(db):
    return [to_dict(row) for row in db.execute("SELECT * FROM usuarios").fetchall()]


def buscar_por_id(db, usuario_id):
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return to_dict(row) if row else None


def criar(db, nome, email, senha, tipo=settings.TIPO_USUARIO_PADRAO):
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def _senha_confere(hash_salvo, senha):
    try:
        return bool(hash_salvo) and check_password_hash(hash_salvo, senha)
    except ValueError:  # valor salvo não é um hash reconhecido
        return False


def autenticar(db, email, senha):
    """Dados públicos do usuário quando e-mail e senha conferem; senão None."""
    row = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None or not _senha_confere(row["senha"], senha):
        return None
    return to_dict(row, LOGIN_FIELDS)


def contar(db):
    return db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
