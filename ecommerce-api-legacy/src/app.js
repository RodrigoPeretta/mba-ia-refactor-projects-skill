const express = require('express');
const settings = require('./config/settings');
const logger = require('./logger');
const { openDatabase, initSchema, seed } = require('./database');
const passwordHasher = require('./services/passwordHasher');
const { createPaymentGateway } = require('./services/paymentGateway');
const { createCheckoutService } = require('./services/checkoutService');
const { createReportService } = require('./services/reportService');
const { createUserService } = require('./services/userService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createRoutes } = require('./routes');
const { createRequireAdmin } = require('./middlewares/auth');
const { createErrorHandler } = require('./middlewares/errorHandler');

// Composition root: cria as dependências e conecta as camadas.
function buildApp({ db }) {
    const paymentGateway = createPaymentGateway({ apiKey: settings.paymentGatewayKey, logger });

    const app = express();
    app.use(express.json());
    app.use(createRoutes({
        checkoutController: createCheckoutController({
            checkoutService: createCheckoutService({ db, paymentGateway, passwordHasher }),
        }),
        reportController: createReportController({ reportService: createReportService({ db }) }),
        userController: createUserController({ userService: createUserService({ db }) }),
        requireAdmin: createRequireAdmin({ adminToken: settings.adminToken }),
    }));
    app.use(createErrorHandler({ logger }));
    return app;
}

async function start() {
    const db = await openDatabase(settings.dbPath);
    await initSchema(db);
    await seed(db, passwordHasher);

    if (!settings.adminToken) {
        logger.warn('ADMIN_TOKEN não definido; rotas administrativas responderão 403');
    }

    buildApp({ db }).listen(settings.port, settings.host, () => {
        logger.info(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        logger.error(`Falha ao iniciar a aplicação: ${err.stack || err}`);
        process.exit(1);
    });
}

module.exports = { buildApp, start };
