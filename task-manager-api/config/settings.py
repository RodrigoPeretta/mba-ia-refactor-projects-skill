"""Configuração da aplicação: variáveis de ambiente e constantes de domínio.

Nenhum segredo fica no código. Sem `.env`, os defaults abaixo valem para desenvolvimento.
"""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _bool(name, default='false'):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes')


def _list(name):
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


# --- Aplicação -------------------------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY') or None
SECRET_KEY_GENERATED = SECRET_KEY is None
if SECRET_KEY_GENERATED:
    SECRET_KEY = secrets.token_hex(32)  # temporária: tokens emitidos expiram a cada reinício

DEBUG = _bool('DEBUG')
HOST = os.environ.get('HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', '5000'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
CORS_ORIGINS = _list('CORS_ORIGINS')

# --- Autenticação ------------------------------------------------------------------
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN') or None  # ausente → X-Admin-Token sempre recusado
SESSION_TOKEN_MAX_AGE = int(os.environ.get('SESSION_TOKEN_MAX_AGE', '3600'))

# --- Integração de e-mail (vazia → notificações desativadas) ------------------------
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

# --- Constantes de domínio -----------------------------------------------------------
TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
CLOSED_TASK_STATUSES = ('done', 'cancelled')
DEFAULT_TASK_STATUS = 'pending'
DONE_STATUS = 'done'

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # prioridade <= 2 conta como alta no relatório do usuário
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TAGS_SEPARATOR = ','
DATE_FORMAT = '%Y-%m-%d'

USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
ADMIN_ROLE = 'admin'
MIN_PASSWORD_LENGTH = 4

DEFAULT_CATEGORY_COLOR = '#000000'
RECENT_ACTIVITY_DAYS = 7
