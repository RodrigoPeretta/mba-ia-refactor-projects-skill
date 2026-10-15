"""Notificações de pedido.

Não há integração real (e-mail/SMS/push) configurada: os eventos são apenas registrados no
log, como no comportamento original.
"""
import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação (email/sms/push): pedido %s criado para usuário %s", pedido_id, usuario_id)


def status_alterado(pedido_id, status):
    if status == "aprovado":
        logger.info("Notificação: pedido %s aprovado; preparar envio", pedido_id)
    elif status == "cancelado":
        logger.info("Notificação: pedido %s cancelado; devolver estoque", pedido_id)
