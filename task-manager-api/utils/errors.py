class AppError(Exception):
    """Erro de aplicação com mensagem e status HTTP já definidos."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status
