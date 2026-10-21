"""Validação de entrada por recurso. Criação e atualização compartilham as mesmas regras.

Cada função devolve só os campos aceitos, já normalizados, ou lança ValidationError (400)
com as mensagens originais da API.
"""
from config.settings import (
    DATE_FORMAT,
    DEFAULT_CATEGORY_COLOR,
    DEFAULT_PRIORITY,
    DEFAULT_ROLE,
    DEFAULT_TASK_STATUS,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_TITLE_LENGTH,
    USER_ROLES,
)
from models.task import Task
from utils.errors import ValidationError
from utils.helpers import is_valid_color, parse_date, validate_email


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_object(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError('Dados inválidos')
    return data


def parse_int_param(value, message):
    """Parâmetro inteiro opcional da query string ('' ou ausente → None)."""
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(message)


# --- Tasks -----------------------------------------------------------------------------

def _title(title, missing_message=None):
    if missing_message and not title:
        raise ValidationError(missing_message)
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _status(status):
    if not Task.validate_status(status):
        raise ValidationError('Status inválido')
    return status


def _priority(priority):
    if not _is_int(priority):
        raise ValidationError('Prioridade inválida')
    if not Task.validate_priority(priority):
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return priority


def _reference(value, message):
    """user_id/category_id: vazio → None; senão precisa ser inteiro."""
    if not value:
        return None
    if not _is_int(value):
        raise ValidationError(message)
    return value


def _due_date(value, message):
    if not value:
        return None
    parsed = parse_date(value, DATE_FORMAT)
    if parsed is None:
        raise ValidationError(message)
    return parsed


def _tags(tags):
    if tags is None or isinstance(tags, str):
        return tags
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        return tags
    raise ValidationError('Tags inválidas')


def _description(description):
    if description is not None and not isinstance(description, str):
        raise ValidationError('Descrição inválida')
    return description


def validate_task_create(data):
    data = require_object(data)
    fields = {
        'title': _title(data.get('title'), missing_message='Título é obrigatório'),
        'description': _description(data.get('description', '')),
        'status': _status(data.get('status', DEFAULT_TASK_STATUS)),
        'priority': _priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': _reference(data.get('user_id'), 'Usuário inválido'),
        'category_id': _reference(data.get('category_id'), 'Categoria inválida'),
        'due_date': _due_date(data.get('due_date'), 'Formato de data inválido. Use YYYY-MM-DD'),
    }
    if data.get('tags'):
        fields['tags'] = _tags(data['tags'])
    return fields


def validate_task_update(data):
    data = require_object(data)
    fields = {}
    if 'title' in data:
        fields['title'] = _title(data['title'])
    if 'description' in data:
        fields['description'] = _description(data['description'])
    if 'status' in data:
        fields['status'] = _status(data['status'])
    if 'priority' in data:
        fields['priority'] = _priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = _reference(data['user_id'], 'Usuário inválido')
    if 'category_id' in data:
        fields['category_id'] = _reference(data['category_id'], 'Categoria inválida')
    if 'due_date' in data:
        fields['due_date'] = _due_date(data['due_date'], 'Formato de data inválido')
    if 'tags' in data:
        fields['tags'] = _tags(data['tags'])
    return fields


# --- Usuários ------------------------------------------------------------------------------

def _email(email):
    if not validate_email(email):
        raise ValidationError('Email inválido')
    return email


def _role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_user_create(data):
    data = require_object(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password or not isinstance(password, str):
        raise ValidationError('Senha é obrigatória')
    _email(email)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    return {
        'name': name,
        'email': email,
        'password': password,
        'role': _role(data.get('role', DEFAULT_ROLE)),
    }


def validate_user_update(data):
    data = require_object(data)
    fields = {}
    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'email' in data:
        fields['email'] = _email(data['email'])
    if 'password' in data:
        password = data['password']
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        fields['password'] = password
    if 'role' in data:
        fields['role'] = _role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active inválido')
        fields['active'] = data['active']
    return fields


def validate_login(data):
    data = require_object(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')
    return email, password


# --- Categorias ----------------------------------------------------------------------------

def _color(color):
    if not is_valid_color(color):
        raise ValidationError('Cor inválida')
    return color


def validate_category_create(data):
    data = require_object(data)
    name = data.get('name')
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    return {
        'name': name,
        'description': _description(data.get('description', '')),
        'color': _color(data.get('color', DEFAULT_CATEGORY_COLOR)),
    }


def validate_category_update(data):
    data = require_object(data, allow_empty=True)
    fields = {}
    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'description' in data:
        fields['description'] = _description(data['description'])
    if 'color' in data:
        fields['color'] = _color(data['color'])
    return fields
