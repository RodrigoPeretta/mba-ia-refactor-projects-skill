function findByEmail(db, email) {
    return db.get('SELECT id FROM users WHERE email = ?', [email]);
}

async function create(db, { name, email, passwordHash }) {
    const { lastID } = await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
    return lastID;
}

function deleteById(db, id) {
    return db.run('DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, create, deleteById };
