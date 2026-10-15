const { AppError } = require('../errors');

const USER_ID_PATTERN = /^\d+$/;

function createUserController({ userService }) {
    return {
        async remove(req, res) {
            const { id } = req.params;
            if (!USER_ID_PATTERN.test(id)) throw new AppError('ID inválido', 400);

            await userService.deleteUser(Number(id));
            res.send('Usuário deletado, junto com suas matrículas e pagamentos.');
        },
    };
}

module.exports = { createUserController };
