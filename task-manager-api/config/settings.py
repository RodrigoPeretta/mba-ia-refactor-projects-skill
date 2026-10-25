"""Configuração da aplicação: variáveis de ambiente e constantes de domínio."""
import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _bool(name, default='false'):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes')


def _list(name):
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


# --- Ambiente ---
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    logger.warning('SECRET_KEY não definida; usando chave temporária (tokens expiram a cada boot)')

DEBUG = _bool('DEBUG')
HOST = os.environ.get('HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', '5000'))
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
CORS_ORIGINS = _list('CORS_ORIGINS')
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN') or None
SESSION_TOKEN_MAX_AGE = int(os.environ.get('SESSION_TOKEN_MAX_AGE', '3600'))

SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

# --- Constantes de domínio ---
VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
FINAL_STATUSES = ('done', 'cancelled')
DEFAULT_STATUS = 'pending'

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
DATE_FORMAT = '%Y-%m-%d'

VALID_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
ADMIN_ROLE = 'admin'
MIN_PASSWORD_LENGTH = 4

DEFAULT_COLOR = '#000000'
RECENT_ACTIVITY_DAYS = 7
