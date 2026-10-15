"""Validação de entrada única, usada pela criação e pela atualização de cada recurso.

As mensagens de erro são as mesmas que a API já devolvia (fazem parte do contrato).
"""
import re
from datetime import datetime

from config import settings
from models.task import Task
from utils.errors import ValidationError


def require_body(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def _is_text(value):
    return isinstance(value, str)


def _parse_date(value, message):
    try:
        return datetime.strptime(value, settings.DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(message)


def _normalize_tags(tags):
    if tags is None or _is_text(tags):
        return tags
    if isinstance(tags, list) and all(_is_text(tag) for tag in tags):
        return ','.join(tags)
    raise ValidationError('Tags inválidas')


def _reference_id(value):
    """IDs de usuário/categoria vazios significam "sem vínculo"."""
    return value if value else None


# --- Tasks ----------------------------------------------------------------

def validate_task(data, partial=False):
    """Valida o corpo de POST (partial=False) ou PUT (partial=True) de /tasks."""
    require_body(data)
    fields = {}

    if not partial or 'title' in data:
        title = data.get('title')
        if not partial and not title:
            raise ValidationError('Título é obrigatório')
        if not _is_text(title):
            raise ValidationError('Título inválido')
        if len(title) < settings.MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > settings.MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')
        fields['title'] = title

    if not partial or 'description' in data:
        fields['description'] = data.get('description', '')

    if not partial or 'status' in data:
        status = data.get('status', settings.DEFAULT_STATUS)
        if not Task.is_valid_status(status):
            raise ValidationError('Status inválido')
        fields['status'] = status

    if not partial or 'priority' in data:
        priority = data.get('priority', settings.DEFAULT_PRIORITY)
        if not Task.is_valid_priority(priority):
            raise ValidationError('Prioridade deve ser entre 1 e 5')
        fields['priority'] = priority

    for key in ('user_id', 'category_id'):
        if not partial or key in data:
            fields[key] = _reference_id(data.get(key))

    if partial:
        if 'due_date' in data:
            due_date = data['due_date']
            fields['due_date'] = (_parse_date(due_date, 'Formato de data inválido')
                                  if due_date else None)
        if 'tags' in data:
            fields['tags'] = _normalize_tags(data['tags'])
    else:
        if data.get('due_date'):
            fields['due_date'] = _parse_date(
                data['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
        if data.get('tags'):
            fields['tags'] = _normalize_tags(data['tags'])

    return fields


def parse_int_param(value, name):
    """Converte um parâmetro de query string opcional para inteiro."""
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido')


# --- Usuários -------------------------------------------------------------

def _valid_email(email):
    return _is_text(email) and re.match(settings.EMAIL_REGEX, email) is not None


def validate_user_create(data):
    require_body(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not _is_text(name):
        raise ValidationError('Nome inválido')
    if not _valid_email(email):
        raise ValidationError('Email inválido')
    if not _is_text(password) or len(password) < settings.MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')

    return {'name': name, 'email': email, 'password': password,
            'role': data.get('role', settings.DEFAULT_ROLE)}


def validate_role(role):
    if role not in settings.VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_user_update(data):
    require_body(data)
    fields = {}
    if 'name' in data:
        if not data['name'] or not _is_text(data['name']):
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'email' in data:
        if not _valid_email(data['email']):
            raise ValidationError('Email inválido')
        fields['email'] = data['email']
    if 'password' in data:
        password = data['password']
        if not _is_text(password) or len(password) < settings.MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        fields['password'] = password
    if 'role' in data:
        fields['role'] = validate_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        fields['active'] = data['active']
    return fields


def validate_login(data):
    require_body(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password or not _is_text(email) or not _is_text(password):
        raise ValidationError('Email e senha são obrigatórios')
    return email, password


# --- Categorias -----------------------------------------------------------

def _validate_color(color):
    if not _is_text(color) or not re.match(settings.COLOR_REGEX, color):
        raise ValidationError('Cor inválida')
    return color


def validate_category(data, partial=False):
    require_body(data)
    fields = {}
    if not partial or 'name' in data:
        name = data.get('name')
        if not name or not _is_text(name):
            raise ValidationError('Nome é obrigatório')
        fields['name'] = name
    if not partial or 'description' in data:
        fields['description'] = data.get('description', '')
    if not partial or 'color' in data:
        fields['color'] = _validate_color(data.get('color', settings.DEFAULT_COLOR))
    return fields
