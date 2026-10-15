import logging

from flask import jsonify, request

from src.controllers import validators
from src.database import get_db
from src.models import usuario_model

logger = logging.getLogger(__name__)


def listar_usuarios():
    return jsonify({"dados": usuario_model.listar(get_db()), "sucesso": True}), 200


def buscar_usuario(usuario_id):
    usuario = usuario_model.buscar_por_id(get_db(), usuario_id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = validators.validar_usuario(request.get_json(silent=True))
    novo_id = usuario_model.criar(get_db(), dados["nome"], dados["email"], dados["senha"])
    logger.info("Usuário criado: id %s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    email, senha = validators.validar_login(request.get_json(silent=True))
    usuario = usuario_model.autenticar(get_db(), email, senha)
    if not usuario:
        logger.info("Login falhou")
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    logger.info("Login bem-sucedido: usuário %s", usuario["id"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
