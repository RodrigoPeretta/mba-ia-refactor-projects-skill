const { AppError } = require('../errors');
const { PAYMENT_STATUS } = require('../config/constants');
const courseModel = require('../models/courseModel');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');

function createCheckoutService({ db, paymentGateway, passwordHasher }) {
    // Matricula o aluno no curso após o pagamento ser aprovado. Retorna o id da matrícula.
    async function checkout({ name, email, password, courseId, cardNumber }) {
        const course = await courseModel.findActiveById(db, courseId);
        if (!course) throw new AppError('Curso não encontrado', 404);

        const existingUser = await userModel.findByEmail(db, email);
        if (!existingUser && !password) throw new AppError('Bad Request', 400);

        const status = paymentGateway.authorize(cardNumber);
        if (status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

        const passwordHash = existingUser ? null : await passwordHasher.hashPassword(password);

        return db.transaction(async (tx) => {
            const userId = existingUser
                ? existingUser.id
                : await userModel.create(tx, { name, email, passwordHash });
            const enrollmentId = await enrollmentModel.create(tx, { userId, courseId });
            await paymentModel.create(tx, { enrollmentId, amount: course.price, status });
            await auditLogModel.create(tx, `Checkout curso ${courseId} por ${userId}`);
            return enrollmentId;
        });
    }

    return { checkout };
}

module.exports = { createCheckoutService };
