"""Configuração da aplicação: variáveis de ambiente e constantes de domínio."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def _list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --- Ambiente ---------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
if not os.environ.get("SECRET_KEY"):
    logger.warning("SECRET_KEY não definida; usando chave temporária gerada no boot")

DEBUG = _bool("DEBUG")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "5000"))
DB_PATH = os.environ.get("DB_PATH", "loja.db")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN") or None  # ausente → rotas /admin respondem 403
CORS_ORIGINS = _list("CORS_ORIGINS", "*")
APP_ENV = os.environ.get("APP_ENV", "producao")

# --- Constantes da aplicação -------------------------------------------------
APP_VERSION = "1.0.0"

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
STATUS_PEDIDO_INICIAL = "pendente"

TIPO_USUARIO_PADRAO = "cliente"

# (faturamento mínimo exclusivo, taxa de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
