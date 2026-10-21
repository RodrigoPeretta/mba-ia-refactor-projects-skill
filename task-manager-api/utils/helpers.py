"""Funções utilitárias sem dependência das camadas da aplicação."""
import re
from datetime import datetime, timezone

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def utcnow():
    """UTC atual sem tzinfo: compatível com as colunas DateTime já gravadas e com `str()` nas respostas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


def is_valid_color(color):
    return isinstance(color, str) and len(color) == 7 and color[0] == '#'


def parse_date(value, date_format):
    try:
        return datetime.strptime(value, date_format)
    except (TypeError, ValueError):
        return None
