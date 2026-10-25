"""Validação de entrada, única para criação e atualização de cada recurso."""
import re
from datetime import datetime

from config import settings
from utils.errors import AppError

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def require_body(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise AppError('Dados inválidos')
    return data


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _optional_id(value, message):
    if not value:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise AppError(message)


def _optional_text(value, message):
    if value is None or isinstance(value, str):
        return value
    raise AppError(message)


def parse_int_param(value, name):
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise AppError(f'Parâmetro {name} inválido')


# --- Tasks ---

def _task_title(data, partial):
    title = data.get('title')
    if not partial and not title:
        raise AppError('Título é obrigatório')
    if not isinstance(title, str):
        raise AppError('Título inválido')
    if len(title) < settings.TITLE_MIN_LENGTH:
        raise AppError('Título muito curto')
    if len(title) > settings.TITLE_MAX_LENGTH:
        raise AppError('Título muito longo')
    return title


def _task_priority(value):
    if not _is_number(value):
        raise AppError('Prioridade inválida')
    if not settings.PRIORITY_MIN <= value <= settings.PRIORITY_MAX:
        raise AppError(f'Prioridade deve ser entre {settings.PRIORITY_MIN} e {settings.PRIORITY_MAX}')
    return value


def _task_due_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, settings.DATE_FORMAT)
    except (TypeError, ValueError):
        raise AppError('Formato de data inválido. Use YYYY-MM-DD')


def _task_tags(value):
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return ','.join(value)
    raise AppError('Tags inválidas')


def validate_task(data, partial=False):
    """Retorna só os campos enviados, já convertidos para o formato do model."""
    data = require_body(data)
    fields = {}
    if not partial or 'title' in data:
        fields['title'] = _task_title(data, partial)
    if 'description' in data:
        fields['description'] = _optional_text(data['description'], 'Descrição inválida')
    if 'status' in data:
        if data['status'] not in settings.VALID_STATUSES:
            raise AppError('Status inválido')
        fields['status'] = data['status']
    if 'priority' in data:
        fields['priority'] = _task_priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = _optional_id(data['user_id'], 'Usuário inválido')
    if 'category_id' in data:
        fields['category_id'] = _optional_id(data['category_id'], 'Categoria inválida')
    if 'due_date' in data:
        fields['due_date'] = _task_due_date(data['due_date'])
    if 'tags' in data:
        fields['tags'] = _task_tags(data['tags'])
    return fields


# --- Users ---

def _user_email(value):
    if not isinstance(value, str) or not EMAIL_PATTERN.match(value):
        raise AppError('Email inválido')
    return value


def _user_role(value):
    if value not in settings.VALID_ROLES:
        raise AppError('Role inválido')
    return value


def validate_user_create(data):
    data = require_body(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not name or not isinstance(name, str):
        raise AppError('Nome é obrigatório')
    if not email:
        raise AppError('Email é obrigatório')
    if not password:
        raise AppError('Senha é obrigatória')
    _user_email(email)
    if not isinstance(password, str) or len(password) < settings.MIN_PASSWORD_LENGTH:
        raise AppError(f'Senha deve ter no mínimo {settings.MIN_PASSWORD_LENGTH} caracteres')
    role = _user_role(data.get('role', settings.DEFAULT_ROLE))
    return {'name': name, 'email': email, 'password': password, 'role': role}


def validate_user_update(data):
    data = require_body(data)
    fields = {}
    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            raise AppError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'email' in data:
        fields['email'] = _user_email(data['email'])
    if 'password' in data:
        password = data['password']
        if not isinstance(password, str) or len(password) < settings.MIN_PASSWORD_LENGTH:
            raise AppError('Senha muito curta')
        fields['password'] = password
    if 'role' in data:
        fields['role'] = _user_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise AppError('Campo active deve ser booleano')
        fields['active'] = data['active']
    return fields


def validate_login(data):
    data = require_body(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise AppError('Email e senha são obrigatórios')
    return email, password


# --- Categories ---

def _category_color(value):
    if not isinstance(value, str) or not COLOR_PATTERN.match(value):
        raise AppError('Cor inválida')
    return value


def validate_category(data, partial=False):
    data = require_body(data, allow_empty=partial)
    fields = {}
    if not partial or 'name' in data:
        if not data.get('name') or not isinstance(data['name'], str):
            raise AppError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'description' in data:
        fields['description'] = _optional_text(data['description'], 'Descrição inválida')
    if 'color' in data:
        fields['color'] = _category_color(data['color'])
    return fields
