import logging

from flask import jsonify, request

from src.database import get_db
from src.exceptions import AppError
from src.models import admin_model

logger = logging.getLogger(__name__)


def reset_database():
    admin_model.limpar_tabelas(get_db())
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = request.get_json(silent=True)
    query = (dados.get("sql", "") if isinstance(dados, dict) else "") or ""
    if not isinstance(query, str) or not query.strip():
        return jsonify({"erro": "Query não informada"}), 400

    sql = query.strip().rstrip(";").strip()
    if not sql.upper().startswith("SELECT") or ";" in sql:
        raise AppError("Apenas uma consulta SELECT é permitida")

    resultado = admin_model.consultar_somente_leitura(get_db(), sql)
    return jsonify({"dados": resultado, "sucesso": True}), 200
