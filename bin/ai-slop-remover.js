#!/usr/bin/env node

import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const packageRoot = new URL('../', import.meta.url);
const { version } = JSON.parse(readFileSync(new URL('package.json', packageRoot), 'utf8'));
const args = process.argv.slice(2);
if (args[0] === 'install') args.shift();

if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  console.log(`Lutriva ${version}

Install product UI/UX skills for Codex or Claude Code.
Requires Python 3.9+ for the bundled, hash-verifying installer.

Usage:
  lutriva --list
  lutriva [install] --repo <project> --agent codex|claude [--dry-run]
  lutriva --repo <project> --agent codex --skill ux-writing
  lutriva --dest <exact-ui-craft-bundle-directory>

Repeat --skill to select multiple skills and their dependencies.
Project installs default to all seven skills. Existing files are never overwritten.
The ai-slop-remover command remains available as a compatibility alias.
Set AI_SLOP_PYTHON to an exact Python executable path if automatic detection fails.`);
  process.exit(0);
}
if (args.length === 1 && args[0] === '--version') {
  console.log(version);
  process.exit(0);
}

const candidates = process.env.AI_SLOP_PYTHON
  ? [[process.env.AI_SLOP_PYTHON, []]]
  : process.platform === 'win32'
    ? [['py', ['-3']], ['python3', []], ['python', []]]
    : [['python3', []], ['python', []]];

for (const [command, prefix] of candidates) {
  const probe = spawnSync(command, [...prefix, '-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'], {
    stdio: 'ignore',
    timeout: 5000,
    windowsHide: true,
  });
  if (probe.error || probe.status !== 0) continue;
  const result = spawnSync(command, [...prefix, fileURLToPath(new URL('install.py', packageRoot)), ...args], {
    stdio: 'inherit',
    windowsHide: true,
  });
  if (result.error) console.error(`Could not run the installer: ${result.error.message}`);
  process.exit(result.status ?? 1);
}

console.error('Python 3.9+ is required. Install Python or set AI_SLOP_PYTHON to its executable path, then retry. No skills were installed.');
process.exit(1);
