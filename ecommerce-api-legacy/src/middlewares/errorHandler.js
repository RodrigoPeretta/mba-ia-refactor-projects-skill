const { AppError } = require('../errors');

// Error handler central (último middleware). Mantém o formato texto das respostas de erro originais.
function createErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return function errorHandler(err, req, res, next) {
        if (err instanceof AppError) return res.status(err.status).send(err.message);
        if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');

        logger.error(`Erro não tratado em ${req.method} ${req.path}: ${err.stack || err}`);
        res.status(500).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
