from flask import jsonify, request

from src.controllers import validators
from src.database import get_db
from src.services import pedido_service


def criar_pedido():
    usuario_id, itens = validators.validar_pedido(request.get_json(silent=True))
    resultado = pedido_service.criar_pedido(get_db(), usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_service.listar_pedidos(get_db(), usuario_id), "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": pedido_service.listar_pedidos(get_db()), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    status = validators.validar_status(request.get_json(silent=True))
    pedido_service.atualizar_status(get_db(), pedido_id, status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
