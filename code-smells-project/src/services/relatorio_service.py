"""Relatórios agregados de vendas."""
from src.config import settings
from src.models import pedido_model


def calcular_desconto(faturamento):
    for faturamento_minimo, taxa in settings.FAIXAS_DESCONTO:
        if faturamento > faturamento_minimo:
            return faturamento * taxa
    return 0


def relatorio_vendas(db):
    dados = pedido_model.agregados(db)
    total_pedidos = dados["total_pedidos"]
    faturamento = dados["faturamento"]
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": dados["pendentes"],
        "pedidos_aprovados": dados["aprovados"],
        "pedidos_cancelados": dados["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
