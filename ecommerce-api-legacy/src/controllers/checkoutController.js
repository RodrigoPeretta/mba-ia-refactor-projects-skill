const { AppError } = require('../errors');
const { CARD_NUMBER_PATTERN, EMAIL_PATTERN } = require('../config/constants');

// Converte o corpo do contrato (usr, eml, pwd, c_id, card) na entrada do serviço.
function parseCheckoutInput(body) {
    const { usr, eml, pwd, c_id: courseId, card } = body || {};

    if (!usr || !eml || !courseId || !card) throw new AppError('Bad Request', 400);
    if (typeof usr !== 'string' || typeof eml !== 'string' || !EMAIL_PATTERN.test(eml)) {
        throw new AppError('Bad Request', 400);
    }
    if (typeof card !== 'string' || !CARD_NUMBER_PATTERN.test(card)) throw new AppError('Bad Request', 400);
    if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') throw new AppError('Bad Request', 400);

    return { name: usr, email: eml, password: pwd || null, courseId: Number(courseId), cardNumber: card };
}

function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const input = parseCheckoutInput(req.body);
            const enrollmentId = await checkoutService.checkout(input);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
