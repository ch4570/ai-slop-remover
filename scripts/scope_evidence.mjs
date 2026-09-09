// Versioned identities shared with check_scope.py; hashes bind records, not their truth.
import { createHash, randomUUID } from 'node:crypto';
import { lstat, readFile, readdir, readlink, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const evaluatorFiles = ['scripts/check_scope.py', 'scripts/compare_evals.py', 'scripts/run_scope_checks.mjs',
  'scripts/scope_evidence.mjs', 'scripts/browser_harness.mjs', 'evals/checks/scope-suites.json'];
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value)
    .sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b)))
    .map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
  return JSON.stringify(value);
}
export const canonicalDigest = value => hash(canonical(value));
export const fileDigest = async target => hash(await readFile(target));

export async function productDigest(product) {
  const entries = Object.create(null);
  async function visit(relative) {
    const target = path.join(product, relative);
    const metadata = await lstat(target);
    const entry = { mode: metadata.mode & 0o7777 };
    if (metadata.isSymbolicLink()) Object.assign(entry, { type: 'symlink', target: await readlink(target) });
    else if (metadata.isDirectory()) entry.type = 'directory';
    else if (metadata.isFile()) Object.assign(entry, { type: 'file', sha256: hash(await readFile(target)) });
    else entry.type = 'special';
    entries[relative] = entry;
    if (entry.type === 'directory') for (const name of await readdir(target)) {
      await visit(relative === '.' ? name : relative + '/' + name);
    }
  }
  try { await visit('.'); }
  catch (error) { if (error.code === 'ENOENT' && !Object.keys(entries).length) entries['.'] = { type: 'absent' }; else throw error; }
  return canonicalDigest(entries);
}

export async function observationBinding(caseId, product, trial) {
  const contextPath = path.join(trial, 'evidence-context.json');
  try { await writeFile(contextPath, JSON.stringify({ schema: 1, case: caseId, trial_id: randomUUID().replaceAll('-', '') }), { flag: 'wx' }); }
  catch (error) { if (error.code !== 'EEXIST') throw error; }
  const context = JSON.parse(await readFile(contextPath, 'utf8'));
  if (context.schema !== 1 || context.case !== caseId || !/^[0-9a-f]{32}$/.test(context.trial_id)
      || Object.keys(context).sort().join(',') !== 'case,schema,trial_id') throw new Error('Invalid trial evidence context');
  let task;
  try { task = await readFile(path.join(trial, 'TASK.md')); }
  catch (error) { if (error.code !== 'ENOENT') throw error; task = await readFile(path.join(root, 'evals/fixtures', caseId, 'TASK.md')); }
  const evaluator = Object.fromEntries(await Promise.all(evaluatorFiles.map(async name => [name, hash(await readFile(path.join(root, name)))])));
  return { schema: 2, case: caseId, trial_id: context.trial_id, product_sha256: await productDigest(product),
    task_sha256: hash(task), evaluator_sha256: canonicalDigest(evaluator) };
}
