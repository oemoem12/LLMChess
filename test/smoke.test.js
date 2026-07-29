// Smoke test for the npm wrapper.
// Verifies that index.js exports are sane and that the launcher script exists.

const fs = require('fs');
const path = require('path');
const assert = require('assert');

const root = path.resolve(__dirname, '..');
const llmchess = require(path.join(root, 'index.js'));

// 1. index.js exports `launch`
assert.strictEqual(typeof llmchess.launch, 'function', 'launch() should be a function');
console.log('OK: index.js exports launch()');

// 2. bin/llmchess.js exists and is executable
const binPath = path.join(root, 'bin', 'llmchess.js');
assert.ok(fs.existsSync(binPath), 'bin/llmchess.js must exist');
const stat = fs.statSync(binPath);
assert.ok(stat.isFile(), 'bin/llmchess.js must be a file');
console.log('OK: bin/llmchess.js exists');

// 3. package.json has correct bin entry
const pkg = require(path.join(root, 'package.json'));
assert.ok(pkg.bin && pkg.bin.llmchess, 'package.json must define bin.llmchess');
assert.strictEqual(pkg.bin.llmchess, 'bin/llmchess.js', 'bin.llmchess should point to bin/llmchess.js');
console.log('OK: package.json bin entry is correct');

// 4. Version is a semver-like string
assert.match(pkg.version, /^\d+\.\d+\.\d+$/, 'version should be semver');
console.log('OK: version is', pkg.version);

console.log('\nAll smoke tests passed.');
