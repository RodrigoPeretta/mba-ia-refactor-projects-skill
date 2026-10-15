// Constantes de regra da aplicação.
const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Gateway simulado: cartões com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

const CARD_NUMBER_PATTERN = /^\d{12,19}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+$/;

// Parâmetros do scrypt para hash de senha.
const PASSWORD_SALT_BYTES = 16;
const PASSWORD_KEY_LENGTH = 64;

module.exports = {
    PAYMENT_STATUS,
    APPROVED_CARD_PREFIX,
    CARD_NUMBER_PATTERN,
    EMAIL_PATTERN,
    PASSWORD_SALT_BYTES,
    PASSWORD_KEY_LENGTH,
};
