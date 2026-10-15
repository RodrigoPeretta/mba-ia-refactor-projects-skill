import logging

from flask import jsonify, request

from src.controllers import validators
from src.database import get_db
from src.exceptions import NotFoundError
from src.models import produto_model

logger = logging.getLogger(__name__)


def _produto_ou_404(db, produto_id):
    produto = produto_model.buscar_por_id(db, produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def listar_produtos():
    produtos = produto_model.listar(get_db())
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(produto_id):
    produto = produto_model.buscar_por_id(get_db(), produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def buscar_produtos():
    resultados = produto_model.buscar(
        get_db(),
        termo=request.args.get("q", ""),
        categoria=request.args.get("categoria"),
        preco_min=validators.parametro_float(request.args, "preco_min"),
        preco_max=validators.parametro_float(request.args, "preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar_produto():
    dados = validators.validar_produto(request.get_json(silent=True))
    novo_id = produto_model.criar(get_db(), **dados)
    logger.info("Produto criado com ID: %s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(produto_id):
    db = get_db()
    _produto_ou_404(db, produto_id)
    dados = validators.validar_produto(request.get_json(silent=True))
    produto_model.atualizar(db, produto_id, **dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(produto_id):
    db = get_db()
    _produto_ou_404(db, produto_id)
    produto_model.deletar(db, produto_id)
    logger.info("Produto %s deletado", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
