const sqlite3 = require('sqlite3');

// Envolve a conexão sqlite3 em Promises e serializa as transações da instância.
class Database {
    constructor(connection) {
        this.connection = connection;
        this.txQueue = Promise.resolve();
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    // Executa fn dentro de BEGIN/COMMIT; qualquer erro faz ROLLBACK de todas as escritas.
    transaction(fn) {
        const result = this.txQueue.then(async () => {
            await this.run('BEGIN');
            try {
                const value = await fn(this);
                await this.run('COMMIT');
                return value;
            } catch (err) {
                await this.run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        this.txQueue = result.catch(() => {});
        return result;
    }

    close() {
        return new Promise((resolve, reject) => {
            this.connection.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

function openDatabase(path) {
    return new Promise((resolve, reject) => {
        const connection = new sqlite3.Database(path, (err) => {
            if (err) return reject(err);
            resolve(new Database(connection));
        });
    });
}

async function initSchema(db) {
    await db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await db.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await db.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
    await db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

// Seed de desenvolvimento; só roda em banco vazio. A senha do usuário de exemplo é gravada como hash.
async function seed(db, { hashPassword }) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM users');
    if (total > 0) return;

    const seedPasswordHash = await hashPassword('123');
    await db.transaction(async (tx) => {
        await tx.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', seedPasswordHash]);
        await tx.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        await tx.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await tx.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
    });
}

module.exports = { openDatabase, initSchema, seed };
