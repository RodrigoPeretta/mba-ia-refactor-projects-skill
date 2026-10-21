from sqlalchemy import and_, or_

from config.settings import (
    CLOSED_TASK_STATUSES,
    DEFAULT_PRIORITY,
    DEFAULT_TASK_STATUS,
    MAX_PRIORITY,
    MIN_PRIORITY,
    TAGS_SEPARATOR,
    TASK_STATUSES,
)
from database import db
from utils.helpers import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

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
            'tags': self.tags.split(TAGS_SEPARATOR) if self.tags else [],
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

    def set_tags(self, tags):
        self.tags = TAGS_SEPARATOR.join(tags) if isinstance(tags, list) else tags

    @staticmethod
    def validate_status(status):
        return status in TASK_STATUSES

    @staticmethod
    def validate_priority(priority):
        return MIN_PRIORITY <= priority <= MAX_PRIORITY

    def is_overdue(self, now=None):
        if self.due_date is None or self.status in CLOSED_TASK_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    @classmethod
    def overdue_clause(cls, now):
        """Mesma regra de `is_overdue`, como filtro SQL."""
        return and_(
            cls.due_date.isnot(None),
            cls.due_date < now,
            or_(cls.status.is_(None), cls.status.notin_(CLOSED_TASK_STATUSES)),
        )
