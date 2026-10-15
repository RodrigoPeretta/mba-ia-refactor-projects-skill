from sqlalchemy import and_

from config import settings
from database import db
from utils.helpers import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=settings.DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=settings.DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_summary_dict(self, now=None):
        """Versão resumida usada na listagem de tasks de um usuário."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(now),
        }

    @staticmethod
    def is_valid_status(status):
        return status in settings.VALID_STATUSES

    @staticmethod
    def is_valid_priority(priority):
        return (isinstance(priority, int) and not isinstance(priority, bool)
                and settings.MIN_PRIORITY <= priority <= settings.MAX_PRIORITY)

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now
                    and self.status not in settings.CLOSED_STATUSES)

    @classmethod
    def overdue_clause(cls, now):
        """Mesmo critério de is_overdue(), como filtro SQL."""
        return and_(cls.due_date.isnot(None), cls.due_date < now,
                    cls.status.notin_(settings.CLOSED_STATUSES))
