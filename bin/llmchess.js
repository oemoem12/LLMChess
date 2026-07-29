#!/usr/bin/env node
// npm entry script for LLMChess
// Locates or installs the Python llmchess package, then launches it.

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const MIN_PY_VERSION = [3, 9];
const PY_PACKAGE = 'llmchess';

function log(msg) {
    process.stderr.write(`[llmchess] ${msg}\n`);
}

function findPython() {
    const candidates = process.platform === 'win32'
        ? ['python', 'python3', 'py']
        : ['python3', 'python'];

    for (const cmd of candidates) {
        try {
            const result = require('child_process').spawnSync(cmd, ['--version'], {
                encoding: 'utf8',
                stdio: ['ignore', 'pipe', 'pipe'],
            });
            if (result.status === 0) {
                const match = result.stdout.match(/Python (\d+)\.(\d+)/);
                if (match) {
                    const major = parseInt(match[1], 10);
                    const minor = parseInt(match[2], 10);
                    if (major > MIN_PY_VERSION[0] ||
                        (major === MIN_PY_VERSION[0] && minor >= MIN_PY_VERSION[1])) {
                        return cmd;
                    }
                    log(`Skipping ${cmd} (Python ${major}.${minor} < ${MIN_PY_VERSION.join('.')})`);
                }
            }
        } catch (e) {
            // continue
        }
    }
    return null;
}

function checkInstalled(python) {
    const result = require('child_process').spawnSync(
        python, ['-c', 'import chess_app; print(chess_app.__version__)'],
        { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }
    );
    if (result.status === 0) {
        return result.stdout.trim();
    }
    return null;
}

function installPackage(python) {
    log(`Installing ${PY_PACKAGE} via pip...`);
    return new Promise((resolve, reject) => {
        const pipArgs = [
            '-m', 'pip', 'install', '--user', '--upgrade', PY_PACKAGE,
        ];
        const child = spawn(python, pipArgs, { stdio: 'inherit' });
        child.on('close', (code) => {
            if (code === 0) resolve();
            else reject(new Error(`pip install failed with code ${code}`));
        });
    });
}

function showError(msg) {
    log('');
    log('ERROR: ' + msg);
    log('');
    log('To use llmchess via npm, you need Python 3.9+ on your system.');
    log('Manual install:');
    log('  1. Install Python 3.9 or later');
    log('  2. pip install --user llmchess');
    log('  3. npx llmchess');
    process.exit(1);
}

async function main() {
    const python = findPython();
    if (!python) {
        showError('No Python 3.9+ interpreter found.');
    }

    let version = checkInstalled(python);
    if (!version) {
        try {
            await installPackage(python);
            version = checkInstalled(python);
        } catch (e) {
            showError(`Failed to install llmchess Python package: ${e.message}`);
        }
    }

    if (!version) {
        showError('llmchess Python package is not importable after install.');
    }

    log(`Using Python ${python}, llmchess v${version}`);

    // Launch the Python entry point
    const child = spawn(python, ['-m', 'chess_app'], {
        stdio: 'inherit',
    });

    child.on('exit', (code) => {
        process.exit(code || 0);
    });
}

main().catch((e) => {
    showError(e.message);
});
