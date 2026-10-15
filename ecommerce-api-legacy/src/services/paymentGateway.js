const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

// Gateway de pagamento simulado. A chave vem da config e nunca é registrada em log.
function createPaymentGateway({ apiKey, logger }) {
    if (!apiKey) {
        logger.warn('PAYMENT_GATEWAY_KEY não definida; gateway de pagamento em modo simulado sem credencial');
    }

    return {
        authorize(cardNumber) {
            logger.info(`Processando pagamento com cartão final ${cardNumber.slice(-4)}`);
            return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { createPaymentGateway };
