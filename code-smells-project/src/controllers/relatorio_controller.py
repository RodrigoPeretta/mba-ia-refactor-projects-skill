from flask import jsonify

from src.database import get_db
from src.services import relatorio_service


def relatorio_vendas():
    return jsonify({"dados": relatorio_service.relatorio_vendas(get_db()), "sucesso": True}), 200
