"""Configuração da aplicação: variáveis de ambiente e constantes de domínio."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _bool(name, default='false'):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes')


def _list(name):
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


# --- Ambiente -------------------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
SECRET_KEY_FROM_ENV = bool(os.environ.get('SECRET_KEY'))
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN') or None  # ausente → rotas administrativas fechadas (403)
DEBUG = _bool('DEBUG')
HOST = os.environ.get('HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', '5000'))
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
CORS_ORIGINS = _list('CORS_ORIGINS')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

# --- Constantes de domínio ------------------------------------------------
VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
CLOSED_STATUSES = ('done', 'cancelled')
DEFAULT_STATUS = 'pending'

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como "alta" no relatório do usuário
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DATE_FORMAT = '%Y-%m-%d'

VALID_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
MIN_PASSWORD_LENGTH = 4
EMAIL_REGEX = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

DEFAULT_COLOR = '#000000'
COLOR_REGEX = r'^#[0-9a-fA-F]{6}$'

REPORT_RECENT_DAYS = 7
