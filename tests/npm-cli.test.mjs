import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const root = fileURLToPath(new URL('../', import.meta.url));
const cli = path.join(root, 'bin/ai-slop-remover.js');
const manifest = JSON.parse(readFileSync(path.join(root, 'manifest.json'), 'utf8'));
const packageInfo = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'));
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';

function temporary(t) {
  const dir = realpathSync(mkdtempSync(path.join(tmpdir(), 'slop npm ')));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

function run(args, options = {}) {
  return spawnSync(process.execPath, [cli, ...args], {
    cwd: root,
    encoding: 'utf8',
    timeout: 15000,
    ...options,
  });
}

function succeeded(result) {
  assert.equal(result.status, 0, result.stdout + result.stderr);
}

test('help and version work without Python or filesystem changes', (t) => {
  const cwd = temporary(t);
  const env = { ...process.env, AI_SLOP_PYTHON: path.join(cwd, 'absent-python') };
  for (const args of [[], ['--help'], ['install', '--help'], ['--version']]) {
    succeeded(run(args, { cwd, env }));
  }
  assert.equal(run(['--version'], { env }).stdout.trim(), packageInfo.version);
  assert.equal(packageInfo.version, manifest.version);
  assert.deepEqual(readdirSync(cwd), []);
});

test('missing Python fails clearly without creating a destination', (t) => {
  const cwd = temporary(t);
  const result = run(['--repo', cwd, '--agent', 'codex'], {
    env: { ...process.env, AI_SLOP_PYTHON: path.join(cwd, 'absent-python') },
  });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Python 3\.9\+ is required/);
  assert.deepEqual(readdirSync(cwd), []);
});

test('list exposes every packaged skill', () => {
  const result = run(['--list']);
  succeeded(result);
  for (const skill of Object.keys(manifest.skills)) assert.ok(result.stdout.includes(skill));
});

for (const agent of ['codex', 'claude']) {
  test(`${agent}: arguments with spaces survive, dry-run is read-only, and reinstall preserves files`, (t) => {
    const project = temporary(t);
    const args = ['install', '--repo', project, '--agent', agent];
    succeeded(run([...args, '--dry-run']));
    assert.deepEqual(readdirSync(project), []);
    succeeded(run(args));
    const skillRoot = path.join(project, agent === 'codex' ? '.agents' : '.claude', 'skills');
    assert.deepEqual(readdirSync(skillRoot).sort(), Object.keys(manifest.skills).sort());
    const entry = path.join(skillRoot, 'ai-slop-remover', 'SKILL.md');
    const before = statSync(entry).mtimeMs;
    succeeded(run(args));
    assert.equal(statSync(entry).mtimeMs, before);
    writeFileSync(entry, 'User customization');
    const refused = run(args);
    assert.equal(refused.status, 1);
    assert.equal(readFileSync(entry, 'utf8'), 'User customization');
  });
}

test('selection forwards to dependency-aware installer and preserves argument errors', (t) => {
  const project = temporary(t);
  succeeded(run(['--repo', project, '--agent', 'codex', '--skill', 'ux-writing']));
  assert.deepEqual(readdirSync(path.join(project, '.agents', 'skills')).sort(), ['ui-craft-bundle', 'ux-writing']);
  assert.equal(run(['--repo', project]).status, 2);
  assert.equal(run(['--definitely-invalid']).status, 2);
});

test('npm tarball has exactly the release payload and a working installed CLI', (t) => {
  const directory = temporary(t);
  // A parent `npm publish --dry-run` propagates its config to lifecycle tests.
  // These isolated fixtures still need a real tarball and local installation.
  const packed = spawnSync(npm, ['pack', '--dry-run=false', '--ignore-scripts', '--json', '--pack-destination', directory], {
    cwd: root, encoding: 'utf8', timeout: 30000,
  });
  succeeded(packed);
  const [report] = JSON.parse(packed.stdout);
  const expected = [...Object.keys(manifest.files), 'manifest.json', 'package.json', 'bin/ai-slop-remover.js'].sort();
  assert.deepEqual(report.files.map((entry) => entry.path).sort(), expected);
  assert.equal(report.name, packageInfo.name);
  const consumer = path.join(directory, 'consumer');
  mkdirSync(consumer);
  const installed = spawnSync(npm, ['install', '--dry-run=false', '--offline', '--ignore-scripts', '--no-audit', '--no-fund', '--prefix', consumer, path.join(directory, report.filename)], {
    cwd: directory, encoding: 'utf8', timeout: 30000,
  });
  succeeded(installed);
  const installedCli = path.join(consumer, 'node_modules', packageInfo.name, 'bin', 'ai-slop-remover.js');
  const result = spawnSync(process.execPath, [installedCli, '--list'], { cwd: directory, encoding: 'utf8', timeout: 15000 });
  succeeded(result);
  for (const skill of Object.keys(manifest.skills)) assert.ok(result.stdout.includes(skill));
  const binName = process.platform === 'win32' ? 'ai-slop-remover.cmd' : 'ai-slop-remover';
  assert.ok(statSync(path.join(consumer, 'node_modules', '.bin', binName)).isFile());
});
