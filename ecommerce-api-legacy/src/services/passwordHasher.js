const crypto = require('crypto');
const { promisify } = require('util');
const { PASSWORD_SALT_BYTES, PASSWORD_KEY_LENGTH } = require('../config/constants');

const scrypt = promisify(crypto.scrypt);

// Formato gravado: "<salt hex>:<hash hex>".
async function hashPassword(password) {
    const salt = crypto.randomBytes(PASSWORD_SALT_BYTES).toString('hex');
    const hash = await scrypt(password, salt, PASSWORD_KEY_LENGTH);
    return `${salt}:${hash.toString('hex')}`;
}

module.exports = { hashPassword };
