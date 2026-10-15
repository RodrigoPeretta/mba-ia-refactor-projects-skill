"""Exceções de aplicação convertidas em JSON pelo error handler central."""


class AppError(Exception):
    status = 400

    def __init__(self, message, status=None):
        super().__init__(message)
        self.message = message
        if status:
            self.status = status


class ValidationError(AppError):
    status = 400


class ForbiddenError(AppError):
    status = 403

    def __init__(self, message='Acesso negado'):
        super().__init__(message)


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409
