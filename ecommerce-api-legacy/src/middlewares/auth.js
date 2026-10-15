const crypto = require('crypto');

// Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem ADMIN_TOKEN configurado, a rota fica fechada (403).
function createRequireAdmin({ adminToken }) {
    const expected = adminToken ? Buffer.from(adminToken) : null;

    return function requireAdmin(req, res, next) {
        const received = Buffer.from(req.get('X-Admin-Token') || '');
        const authorized = expected !== null
            && received.length === expected.length
            && crypto.timingSafeEqual(received, expected);
        if (!authorized) return res.status(403).send('Acesso negado');
        next();
    };
}

module.exports = { createRequireAdmin };
