// Erro de aplicação com status HTTP; convertido em resposta pelo error handler central.
class AppError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.status = status;
    }
}

module.exports = { AppError };
