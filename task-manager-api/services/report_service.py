"""Relatórios agregados sobre tasks, usuários e categorias."""
from datetime import timedelta

from sqlalchemy import func, select

from config.settings import (
    DONE_STATUS,
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    TASK_STATUSES,
)
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services.task_service import count_by_status
from services.user_service import task_counts_by_user, tasks_of
from utils.helpers import calculate_percentage, utcnow


def _count(model, *conditions):
    return db.session.scalar(select(func.count()).select_from(model).where(*conditions))


def _count_by_priority():
    rows = dict(db.session.execute(select(Task.priority, func.count()).group_by(Task.priority)).all())
    return {label: rows.get(priority, 0) for priority, label in PRIORITY_LABELS.items()}


def _overdue_tasks(now):
    query = select(Task).where(Task.overdue_clause(now)).order_by(Task.id)
    return [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in db.session.scalars(query)
    ]


def _user_productivity():
    totals = task_counts_by_user()
    completed = dict(
        db.session.execute(
            select(Task.user_id, func.count()).where(Task.status == DONE_STATUS).group_by(Task.user_id)
        ).all()
    )
    result = []
    for user in db.session.scalars(select(User).order_by(User.id)):
        total = totals.get(user.id, 0)
        done = completed.get(user.id, 0)
        result.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': calculate_percentage(done, total),
        })
    return result


def summary_report():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    overdue = _overdue_tasks(now)
    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': _count(Task),
            'total_users': _count(User),
            'total_categories': _count(Category),
        },
        'tasks_by_status': count_by_status(),
        'tasks_by_priority': _count_by_priority(),
        'overdue': {'count': len(overdue), 'tasks': overdue},
        'recent_activity': {
            'tasks_created_last_7_days': _count(Task, Task.created_at >= since),
            'tasks_completed_last_7_days': _count(
                Task, Task.status == DONE_STATUS, Task.updated_at >= since
            ),
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user):
    tasks = tasks_of(user.id)
    now = utcnow()
    by_status = dict.fromkeys(TASK_STATUSES, 0)
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1
    total = len(tasks)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **by_status,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(by_status[DONE_STATUS], total),
        },
    }
