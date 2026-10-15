// Logger mínimo centralizado. Nunca registre senhas, cartões completos ou chaves.
function write(level, message) {
    const line = `[${new Date().toISOString()}] ${level.toUpperCase()} ${message}`;
    if (level === 'error') console.error(line);
    else if (level === 'warn') console.warn(line);
    else console.log(line);
}

module.exports = {
    info: (message) => write('info', message),
    warn: (message) => write('warn', message),
    error: (message) => write('error', message),
};
