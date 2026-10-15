"""Notificações por e-mail. O transporte SMTP é configurado pelo composition root."""
import logging
import smtplib
from email.message import EmailMessage

from utils.helpers import utcnow

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, host, port, user, password, smtp_factory=smtplib.SMTP):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self._smtp_factory = smtp_factory
        self.notifications = []

    @property
    def enabled(self):
        return bool(self.host and self.user and self.password)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.warning('SMTP não configurado; e-mail não enviado')
            return False
        message = EmailMessage()
        message['From'] = self.user
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)
        try:
            with self._smtp_factory(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(message)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('Falha ao enviar e-mail')
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f"Prioridade: {task.priority}\nStatus: {task.status}")
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utcnow(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
