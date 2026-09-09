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
  assert.equal(result.status, 0, result.error?.message || result.stdout + result.stderr);
}

function runNpm(args, options) {
  // npm test supplies its CLI path. Running that JavaScript through Node avoids
  // npm.cmd shell parsing of tarball and consumer paths containing spaces.
  assert.ok(process.env.npm_execpath, 'Run this suite with npm test.');
  return spawnSync(process.execPath, [process.env.npm_execpath, ...args], {
    encoding: 'utf8', timeout: 30000, ...options,
  });
}

test('help and version work without Python or filesystem changes', (t) => {
  const cwd = temporary(t);
  const env = { ...process.env, AI_SLOP_PYTHON: path.join(cwd, 'absent-python') };
  for (const args of [[], ['--help'], ['install', '--help'], ['--version'], ['--help', '--', 'ignored'], ['-h', '--', 'ignored']]) {
    succeeded(run(args, { cwd, env }));
  }
  assert.equal(run(['--version'], { env }).stdout.trim(), packageInfo.version);
  assert.equal(packageInfo.version, manifest.version);
  assert.deepEqual(readdirSync(cwd), []);
});

for (const prefix of [[], ['install']]) {
  for (const help of ['--help', '-h']) {
    test(`${prefix.join(' ') || 'default'}: ${help} after the option terminator preserves argument errors`, (t) => {
      const project = temporary(t);
      const sentinel = path.join(project, 'user-note.txt');
      writeFileSync(sentinel, 'Keep this project unchanged.');
      const before = statSync(sentinel, { bigint: true }).mtimeNs;
      const result = run([...prefix, '--repo', project, '--agent', 'codex', '--status', '--', help]);
      assert.equal(result.status, 2, result.error?.message || result.stdout + result.stderr);
      assert.equal(result.stdout, '');
      assert.match(result.stderr, /unrecognized arguments: -- (?:--help|-h)/);
      assert.deepEqual(readdirSync(project), ['user-note.txt']);
      assert.equal(readFileSync(sentinel, 'utf8'), 'Keep this project unchanged.');
      assert.equal(statSync(sentinel, { bigint: true }).mtimeNs, before);
    });
  }
}

test('missing Python fails clearly without creating a destination', (t) => {
  const cwd = temporary(t);
  const result = run(['--repo', cwd, '--agent', 'codex'], {
    env: { ...process.env, AI_SLOP_PYTHON: path.join(cwd, 'absent-python') },
  });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Python 3\.9\+ is required/);
  assert.deepEqual(readdirSync(cwd), []);
});

test('list exposes every skill with detected Python and an explicit executable path containing spaces', (t) => {
  const automatic = { ...process.env };
  delete automatic.AI_SLOP_PYTHON;
  const result = run(['--list'], { env: automatic });
  succeeded(result);
  for (const skill of Object.keys(manifest.skills)) assert.ok(result.stdout.includes(skill));

  const environment = path.join(temporary(t), 'python environment');
  const python = process.env.AI_SLOP_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  // Use venv's platform default: Apple's framework Python requires symlinks,
  // while Windows defaults to copies. Both exercise the configured path.
  succeeded(spawnSync(python, ['-m', 'venv', '--without-pip', environment], {
    encoding: 'utf8', timeout: 30000,
  }));
  const executable = path.join(environment, process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  const probe = spawnSync(executable, ['-c', 'import sys; print(sys.version); print(sys.executable)'], {
    encoding: 'utf8', timeout: 15000,
  });
  succeeded(probe);
  t.diagnostic('Explicit Python: ' + probe.stdout.trim());
  const configured = run(['--list'], { env: { ...process.env, AI_SLOP_PYTHON: executable } });
  succeeded(configured);
  assert.equal(configured.stdout, result.stdout);
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

test('status forwards selection, reports every dependency, and preserves user edits', (t) => {
  const project = temporary(t);
  const args = ['--repo', project, '--agent', 'codex', '--skill', 'ux-writing'];
  const missing = run([...args, '--status']);
  succeeded(missing);
  assert.equal(missing.stdout.match(/Status: not installed/g)?.length, 2);
  assert.deepEqual(readdirSync(project), []);
  succeeded(run(args));
  const entry = path.join(project, '.agents', 'skills', 'ui-craft-bundle', 'SKILL.md');
  writeFileSync(entry, 'User customization');
  const before = statSync(entry).mtimeMs;
  const status = run([...args, '--status']);
  succeeded(status);
  assert.match(status.stdout, /ui-craft-bundle:\r?\n[\s\S]*Status: user modifications/);
  assert.match(status.stdout, /ux-writing:\r?\n[\s\S]*Status: identical installation/);
  assert.match(status.stdout, /modified: "SKILL.md"/);
  const expectedDirectory = path.dirname(entry);
  const backupPath = status.stdout.match(/^  Review and back up before reinstalling: ([^\r\n]+)\r?$/m)?.[1];
  const pathDiagnostic = `Expected backup directory: ${expectedDirectory}\nStatus output:\n${status.stdout}`;
  assert.ok(backupPath && path.isAbsolute(backupPath), pathDiagnostic);
  let resolvedBackup;
  assert.doesNotThrow(() => { resolvedBackup = realpathSync.native(backupPath); }, pathDiagnostic);
  assert.equal(resolvedBackup, realpathSync.native(expectedDirectory), pathDiagnostic);
  t.diagnostic(`Backup directory: reported=${backupPath}; expected=${expectedDirectory}; resolved=${resolvedBackup}`);
  assert.equal(readFileSync(entry, 'utf8'), 'User customization');
  assert.equal(statSync(entry).mtimeMs, before);
  assert.equal(run(args).status, 1);
  assert.equal(run([...args, '--status', '--dry-run']).status, 2);
  assert.match(run(['--help']).stdout, /--status/);
});

test('npm tarball has exactly the release payload and equivalent installed command aliases', (t) => {
  const directory = temporary(t);
  // A parent `npm publish --dry-run` propagates its config to lifecycle tests.
  // These isolated fixtures still need a real tarball and local installation.
  const packed = runNpm(['pack', '--dry-run=false', '--ignore-scripts', '--json', '--pack-destination', directory], {
    cwd: root,
  });
  succeeded(packed);
  const [report] = JSON.parse(packed.stdout);
  const expected = [...Object.keys(manifest.files), 'manifest.json', 'package.json', 'bin/ai-slop-remover.js'].sort();
  assert.deepEqual(report.files.map((entry) => entry.path).sort(), expected);
  assert.equal(report.name, packageInfo.name);
  const consumer = path.join(directory, 'consumer');
  mkdirSync(consumer);
  const installed = runNpm(['install', '--dry-run=false', '--offline', '--ignore-scripts', '--no-audit', '--no-fund', '--prefix', consumer, path.join(directory, report.filename)], {
    cwd: directory,
  });
  succeeded(installed);
  const commandOutput = new Map();
  for (const command of ['lutriva', 'ai-slop-remover']) {
    const binName = process.platform === 'win32' ? `${command}.cmd` : command;
    const installedBin = path.join(consumer, 'node_modules', '.bin', binName);
    assert.ok(statSync(installedBin).isFile());
    const output = {};
    for (const argument of ['--version', '--list']) {
      const commandPath = process.platform === 'win32' ? `"${installedBin}"` : installedBin;
      const result = spawnSync(commandPath, [argument], {
        cwd: directory, encoding: 'utf8', timeout: 15000,
        shell: process.platform === 'win32',
      });
      succeeded(result);
      output[argument] = { stdout: result.stdout, stderr: result.stderr };
    }
    const invalid = spawnSync(process.platform === 'win32' ? `"${installedBin}"` : installedBin, ['--list', '--', '--help'], {
      cwd: directory, encoding: 'utf8', timeout: 15000,
      shell: process.platform === 'win32',
    });
    assert.equal(invalid.status, 2, invalid.error?.message || invalid.stdout + invalid.stderr);
    assert.equal(invalid.stdout, '');
    assert.match(invalid.stderr, /unrecognized arguments: -- --help/);
    assert.equal(output['--version'].stdout.trim(), packageInfo.version);
    for (const skill of Object.keys(manifest.skills)) assert.ok(output['--list'].stdout.includes(skill));
    commandOutput.set(command, output);
  }
  assert.deepEqual(commandOutput.get('lutriva'), commandOutput.get('ai-slop-remover'));
  // Exercise the scripts from the packed, then installed skill tree. This catches
  // missing sibling imports and accidental dependencies on the source checkout.
  const project = path.join(directory, 'learning project');
  mkdirSync(project);
  const packagedCli = path.join(consumer, 'node_modules', packageInfo.name, 'bin', 'ai-slop-remover.js');
  succeeded(spawnSync(process.execPath, [packagedCli, '--repo', project, '--agent', 'codex', '--skill', 'ux-writing'], {
    cwd: consumer, encoding: 'utf8', timeout: 15000,
  }));
  const installedSkills = path.join(project, '.agents', 'skills');
  const learningCli = path.join(installedSkills, 'ui-craft-bundle', 'scripts', 'local_learning.py');
  const python = process.env.AI_SLOP_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  for (const operation of ['init', 'status']) {
    const result = spawnSync(python, ['-B', learningCli, operation, '--project', project], {
      cwd: consumer, encoding: 'utf8', timeout: 15000,
    });
    succeeded(result);
    const state = JSON.parse(result.stdout);
    assert.equal(state.state, 'base-only');
    assert.equal(state.automatic_execution, false);
  }
  const policy = JSON.parse(readFileSync(path.join(project, '.lutriva', 'local', 'policy.json'), 'utf8'));
  // Python expands Windows 8.3 names; resolve both spellings with the native API.
  assert.equal(realpathSync.native(policy.base), realpathSync.native(installedSkills));
  const installationStatus = spawnSync(process.execPath, [packagedCli, '--repo', project, '--agent', 'codex', '--skill', 'ux-writing', '--status'], {
    cwd: consumer, encoding: 'utf8', timeout: 15000,
  });
  succeeded(installationStatus);
  assert.equal(installationStatus.stdout.match(/Status: identical installation/g)?.length, 2);
});
