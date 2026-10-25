from datetime import timedelta

from sqlalchemy import case, func

from database import db
from config import settings
from models.category import Category
from models.task import Task
from models.user import User
from services import task_service, user_service
from utils.helpers import calculate_percentage, utcnow


def _count_by_priority():
    counts = dict(db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all())
    return {label: counts.get(priority, 0) for priority, label in settings.PRIORITY_LABELS.items()}


def _overdue_tasks(now):
    tasks = Task.query.filter(Task.overdue_clause(now)).order_by(Task.id).all()
    return [{
        'id': task.id,
        'title': task.title,
        'due_date': str(task.due_date),
        'days_overdue': (now - task.due_date).days,
    } for task in tasks]


def _user_productivity():
    completed = func.coalesce(func.sum(case((Task.status == 'done', 1), else_=0)), 0)
    rows = (db.session.query(User.id, User.name, func.count(Task.id), completed)
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id, User.name)
            .order_by(User.id)
            .all())
    return [{
        'user_id': user_id,
        'user_name': name,
        'total_tasks': total,
        'completed_tasks': done,
        'completion_rate': calculate_percentage(done, total),
    } for user_id, name, total, done in rows]


def summary():
    now = utcnow()
    since = now - timedelta(days=settings.RECENT_ACTIVITY_DAYS)
    overdue = _overdue_tasks(now)
    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.query.count(),
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
        },
        'tasks_by_status': task_service.count_by_status(),
        'tasks_by_priority': _count_by_priority(),
        'overdue': {
            'count': len(overdue),
            'tasks': overdue,
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.query.filter(Task.created_at >= since).count(),
            'tasks_completed_last_7_days': Task.query.filter(
                Task.status == 'done', Task.updated_at >= since).count(),
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user_id):
    user = user_service.get_or_404(user_id)
    tasks = Task.query.filter_by(user_id=user_id).all()
    now = utcnow()
    by_status = {status: 0 for status in settings.VALID_STATUSES}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1
    total = len(tasks)
    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            **by_status,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= settings.HIGH_PRIORITY_MAX),
            'completion_rate': calculate_percentage(by_status['done'], total),
        },
    }
