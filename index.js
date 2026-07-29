// Programmatic API for llmchess (npm).
// For now, this just re-exports the launcher as a programmatic helper.

const { spawn } = require('child_process');

/**
 * Launch the LLM Chess GUI as a child process.
 * @param {Object} [options]
 * @param {string} [options.python] - Python executable to use (default: auto-detect)
 * @returns {import('child_process').ChildProcess}
 */
function launch(options = {}) {
    const args = [];
    const env = { ...process.env };

    if (options.python) {
        env.LLMCHESS_PYTHON = options.python;
    }

    const child = spawn(process.execPath, [require.resolve('./bin/llmchess.js')], {
        stdio: 'inherit',
        env,
    });
    return child;
}

module.exports = { launch };
