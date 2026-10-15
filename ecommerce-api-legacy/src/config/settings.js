// Configuração lida do ambiente. Nenhum segredo literal: sem valor, a variável fica vazia.
const settings = {
    port: Number(process.env.PORT || 3000),
    host: process.env.HOST || '127.0.0.1',
    dbPath: process.env.DB_PATH || ':memory:',
    adminToken: process.env.ADMIN_TOKEN || null,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
};

module.exports = Object.freeze(settings);
