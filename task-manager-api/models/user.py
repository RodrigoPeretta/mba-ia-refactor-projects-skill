from werkzeug.security import check_password_hash, generate_password_hash

from config.settings import ADMIN_ROLE, DEFAULT_ROLE
from database import db
from utils.helpers import utcnow


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Serialização pública: o hash da senha nunca sai da aplicação."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        try:
            return check_password_hash(self.password, password)
        except ValueError:
            # hash em formato antigo (MD5 sem salt): só volta a valer após novo seed/troca de senha
            return False

    def is_admin(self):
        return self.role == ADMIN_ROLE
