"""Validação de entrada das requisições (mensagens originais preservadas)."""
import re

from src.config import settings
from src.exceptions import AppError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar_produto(dados):
    """Regras únicas de produto, usadas na criação e na atualização."""
    if not dados or not isinstance(dados, dict):
        raise AppError("Dados inválidos")
    if "nome" not in dados:
        raise AppError("Nome é obrigatório")
    if "preco" not in dados:
        raise AppError("Preço é obrigatório")
    if "estoque" not in dados:
        raise AppError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", settings.CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise AppError("Nome deve ser um texto")
    if not isinstance(descricao, str):
        raise AppError("Descrição deve ser um texto")
    if not _numero(preco):
        raise AppError("Preço deve ser numérico")
    if not _numero(estoque):
        raise AppError("Estoque deve ser numérico")
    if preco < 0:
        raise AppError("Preço não pode ser negativo")
    if estoque < 0:
        raise AppError("Estoque não pode ser negativo")
    if len(nome) < settings.NOME_PRODUTO_MIN:
        raise AppError("Nome muito curto")
    if len(nome) > settings.NOME_PRODUTO_MAX:
        raise AppError("Nome muito longo")
    if categoria not in settings.CATEGORIAS_VALIDAS:
        raise AppError("Categoria inválida. Válidas: " + str(settings.CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def parametro_float(args, nome):
    valor = args.get(nome)
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise AppError(f"{nome} deve ser numérico") from None


def validar_usuario(dados):
    if not dados or not isinstance(dados, dict):
        raise AppError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise AppError("Nome, email e senha são obrigatórios")
    if not all(isinstance(v, str) for v in (nome, email, senha)):
        raise AppError("Nome, email e senha devem ser textos")
    if not EMAIL_RE.match(email):
        raise AppError("Email inválido")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise AppError("Email e senha são obrigatórios")
    return email, senha


def validar_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise AppError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise AppError("Usuario ID é obrigatório")
    if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
        raise AppError("Usuario ID inválido")
    if not itens or not isinstance(itens, list):
        raise AppError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if not (
            isinstance(item, dict)
            and isinstance(item.get("produto_id"), int)
            and isinstance(item.get("quantidade"), int)
            and not isinstance(item.get("quantidade"), bool)
            and item["quantidade"] > 0
        ):
            raise AppError("Cada item deve ter produto_id e quantidade (inteiro maior que zero)")
    return usuario_id, itens


def validar_status(dados):
    dados = dados if isinstance(dados, dict) else {}
    status = dados.get("status", "")
    if status not in settings.STATUS_PEDIDO_VALIDOS:
        raise AppError("Status inválido")
    return status
