const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');

function createUserService({ db }) {
    // Remove o usuário com suas matrículas e pagamentos, tudo na mesma transação.
    function deleteUser(userId) {
        return db.transaction(async (tx) => {
            await paymentModel.deleteByUserId(tx, userId);
            await enrollmentModel.deleteByUserId(tx, userId);
            await userModel.deleteById(tx, userId);
        });
    }

    return { deleteUser };
}

module.exports = { createUserService };
