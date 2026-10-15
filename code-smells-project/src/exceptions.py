"""Exceções da aplicação, convertidas em resposta JSON pelo error handler central."""


class AppError(Exception):
    """Erro esperado; `sucesso` só entra no corpo quando informado (envelope original)."""

    status = 400

    def __init__(self, message, status=None, sucesso=None):
        super().__init__(message)
        self.message = message
        if status is not None:
            self.status = status
        self.sucesso = sucesso


class NotFoundError(AppError):
    status = 404


class BusinessRuleError(AppError):
    """Regra de negócio violada (ex.: estoque insuficiente)."""

    def __init__(self, message):
        super().__init__(message, status=400, sucesso=False)
