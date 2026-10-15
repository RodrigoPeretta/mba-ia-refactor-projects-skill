"""Relatórios agregados sobre tasks, usuários e categorias."""
from datetime import timedelta

from sqlalchemy import case, func

from config import settings
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services import task_service
from utils.helpers import calculate_percentage, utcnow


def _overdue_tasks(now):
    tasks = db.session.scalars(
        db.select(Task).where(Task.overdue_clause(now)).order_by(Task.id)
    ).all()
    return [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in tasks
    ]


def _user_productivity():
    completed = func.coalesce(func.sum(case((Task.status == 'done', 1), else_=0)), 0)
    rows = db.session.execute(
        db.select(User.id, User.name, func.count(Task.id), completed)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    ).all()
    return [
        {
            'user_id': user_id,
            'user_name': name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': calculate_percentage(done, total),
        }
        for user_id, name, total, done in rows
    ]


def summary():
    now = utcnow()
    by_status = task_service.count_by(Task.status)
    by_priority = task_service.count_by(Task.priority)
    since = now - timedelta(days=settings.REPORT_RECENT_DAYS)
    overdue = _overdue_tasks(now)

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': sum(by_status.values()),
            'total_users': db.session.scalar(db.select(func.count(User.id))),
            'total_categories': db.session.scalar(db.select(func.count(Category.id))),
        },
        'tasks_by_status': {status: by_status.get(status, 0) for status in settings.VALID_STATUSES},
        'tasks_by_priority': {
            label: by_priority.get(priority, 0)
            for priority, label in settings.PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue),
            'tasks': overdue,
        },
        'recent_activity': {
            'tasks_created_last_7_days': db.session.scalar(
                db.select(func.count(Task.id)).where(Task.created_at >= since)),
            'tasks_completed_last_7_days': db.session.scalar(
                db.select(func.count(Task.id)).where(Task.status == 'done',
                                                     Task.updated_at >= since)),
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user):
    now = utcnow()
    tasks = task_service.list_by_user(user.id)
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
            'high_priority': sum(1 for task in tasks
                                 if task.priority is not None
                                 and task.priority <= settings.HIGH_PRIORITY_MAX),
            'completion_rate': calculate_percentage(by_status['done'], total),
        },
    }
