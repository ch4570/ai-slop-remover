#!/usr/bin/env node
// Optional maintainer driver: existing Chrome + Node 22+, no installed packages.
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { access, mkdir, mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const [fixtureArg, outputArg] = process.argv.slice(2);
if (!fixtureArg || !outputArg || process.argv.length !== 4 || typeof WebSocket === 'undefined') {
  console.error('Usage: node scripts/run_browser_checks.mjs <fixture-copy> <evidence-directory> (Node 22+ and Chrome required)');
  process.exit(2);
}
const fixture = await realpath(fixtureArg);
const output = path.resolve(outputArg);
const source = await readFile(new URL('../evals/checks/search-editor.js', import.meta.url), 'utf8');
const chromePaths = process.env.AI_SLOP_CHROME ? [process.env.AI_SLOP_CHROME] : [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
];
let executable;
for (const candidate of chromePaths) {
  try { await access(candidate); executable = candidate; break; } catch { /* Try an installed browser. */ }
}
if (!executable) throw new Error('Chrome unavailable; set AI_SLOP_CHROME to its executable. Browser checks not run.');
const profile = await mkdtemp(path.join(tmpdir(), 'slop-browser-'));
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const server = createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname);
    const requested = await realpath(path.join(fixture, pathname === '/' ? 'index.html' : pathname));
    if (!requested.startsWith(fixture + path.sep)) throw new Error('Outside fixture');
    const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };
    response.writeHead(200, { 'Content-Type': types[path.extname(requested)] || 'text/plain', 'Cache-Control': 'no-store' });
    response.end(await readFile(requested));
  } catch {
    response.writeHead(404); response.end('Not found');
  }
});
let chrome, socket;
const pending = new Map();
let sequence = 0;
const exceptions = [];
try {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  chrome = spawn(executable, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check', '--disable-background-networking', 'about:blank'], { stdio: 'ignore' });
  let launchError;
  chrome.on('error', error => { launchError = error; });
  let debug;
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (launchError) throw launchError;
    if (chrome.exitCode !== null) throw new Error('Chrome exited before the debugging endpoint was ready');
    try { debug = (await readFile(path.join(profile, 'DevToolsActivePort'), 'utf8')).trim().split('\n'); break; } catch { await pause(100); }
  }
  if (!debug) throw new Error('Chrome debugging endpoint did not become ready');
  socket = new WebSocket(`ws://127.0.0.1:${debug[0]}${debug[1]}`);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', () => reject(new Error('Cannot connect to Chrome')), { once: true });
  });
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
    if (!pending.has(message.id)) return;
    const entry = pending.get(message.id); pending.delete(message.id); clearTimeout(entry.timer);
    if (message.error) entry.reject(new Error(message.error.message)); else entry.resolve(message.result);
  });
  function call(method, params = {}, sessionId) {
    const id = ++sequence;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { pending.delete(id); reject(new Error(`Chrome timeout: ${method}`)); }, 15000);
      pending.set(id, { resolve, reject, timer });
      socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    });
  }
  const { targetId } = await call('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await call('Target.attachToTarget', { targetId, flatten: true });
  const page = (method, params) => call(method, params, sessionId);
  const evaluate = async expression => {
    const result = await page('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  await page('Page.enable'); await page('Runtime.enable');
  await page('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  const waitForFixture = async (previousTimeOrigin = null) => {
    for (let attempt = 0; attempt < 100; attempt += 1) {
      try {
        const ready = await evaluate(`location.origin === ${JSON.stringify(origin)} && performance.timeOrigin !== ${JSON.stringify(previousTimeOrigin)} && document.readyState === 'complete' && !!document.getElementById('save')`);
        if (ready) return;
      } catch { /* The old execution context can disappear during navigation. */ }
      await pause(50);
    }
    throw new Error('Fixture did not finish loading');
  };
  const reloadFixture = async () => {
    const previousTimeOrigin = await evaluate('performance.timeOrigin');
    await page('Page.reload', { ignoreCache: true });
    await waitForFixture(previousTimeOrigin);
    await evaluate(source);
  };
  const navigateFixture = async url => {
    const previousTimeOrigin = await evaluate('performance.timeOrigin');
    await page('Page.navigate', { url });
    await waitForFixture(previousTimeOrigin);
    await evaluate(source);
  };
  const resetFixture = async () => {
    const snapshot = await evaluate('seedSearchEditor()');
    await reloadFixture();
    return snapshot;
  };
  const observeSavedReload = async (id, expected) => {
    await reloadFixture();
    return evaluate(`observeReload(${JSON.stringify(id)}, ${JSON.stringify(expected)})`);
  };
  await page('Page.navigate', { url: origin });
  await waitForFixture();
  await evaluate(source);
  let snapshot = await resetFixture();
  await mkdir(output, { recursive: true });
  const screenshot = async name => {
    const result = await page('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
    await writeFile(path.join(output, name), Buffer.from(result.data, 'base64'));
  };
  await screenshot('wide.png');
  const retry = await evaluate(`evaluateSearchEditor(${JSON.stringify(snapshot)})`);
  // Keep observations outside the page so reloads cannot discard earlier failures.
  const checks = [...retry.checks];
  checks.push(await observeSavedReload('retry-reload', retry.expected));
  snapshot = await resetFixture();
  const ordinary = await evaluate(`evaluateOrdinarySave(${JSON.stringify(snapshot)})`);
  checks.push(...ordinary.checks);
  checks.push(await observeSavedReload('ordinary-reload', ordinary.expected));
  snapshot = await resetFixture();
  const enter = await evaluate(`prepareOrdinaryEnter(${JSON.stringify(snapshot)})`);
  if (enter.selectionFound) {
    await page('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', text: '\r', windowsVirtualKeyCode: 13 });
    await page('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
    await pause(150);
  }
  checks.push(await evaluate(`observeOrdinaryEnter(${JSON.stringify(enter)})`));
  checks.push(await observeSavedReload('ordinary-enter-reload', enter.expected));
  snapshot = await resetFixture();
  // Preserve concrete failures and distinguish unavailable observations while
  // later checks run independently, outside the navigated document.
  const observeNavigation = async (id, observe) => {
    try { checks.push(await observe()); }
    catch (error) {
      checks.push({ id, kind: 'behavior', status: 'not-run',
        reason: 'Navigation observation did not complete: ' + String(error) });
    }
  };
  let entries;
  await observeNavigation('history-back', async () => {
    entries = await evaluate('prepareSearchHistory()');
    return evaluate(`evaluateHistoryTraversal('history-back', ${JSON.stringify(snapshot)}, 'back', ${JSON.stringify([entries[1], entries[0]])})`);
  });
  await observeNavigation('history-forward', async () => {
    if (!entries) throw new Error('History entry preparation did not complete.');
    return evaluate(`evaluateHistoryTraversal('history-forward', ${JSON.stringify(snapshot)}, 'forward', ${JSON.stringify([entries[1], entries[2]])})`);
  });
  // A body-only match also checks that shared URLs use the same search semantics.
  const sharedQuery = '긴 한국어';
  const sharedUrl = new URL(origin);
  sharedUrl.searchParams.set('q', sharedQuery);
  await observeNavigation('query-direct-entry', async () => {
    await navigateFixture(sharedUrl.href);
    return evaluate(`observeQueryRestoration('query-direct-entry', ${JSON.stringify(snapshot)}, ${JSON.stringify(sharedQuery)})`);
  });
  await observeNavigation('query-reload', async () => {
    await reloadFixture();
    return evaluate(`observeQueryRestoration('query-reload', ${JSON.stringify(snapshot)}, ${JSON.stringify(sharedQuery)})`);
  });
  await navigateFixture(origin);
  await resetFixture();
  await page('Emulation.setDeviceMetricsOverride', { width: 375, height: 844, deviceScaleFactor: 1, mobile: true });
  await page('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
  const narrowState = await evaluate(`(async () => {
    const title = document.getElementById('title');
    title.value = '저장에 실패해도 다시 수정할 수 있어야 하는 긴 한국어 메모 제목';
    title.dispatchEvent(new Event('input', {bubbles:true}));
    document.getElementById('fail-save').checked = true;
    document.getElementById('save').click();
    await new Promise(resolve => setTimeout(resolve, 150));
    return {title:title.value,status:document.getElementById('status').dataset.state,feedback:document.getElementById('status').textContent};
  })()`);
  await screenshot('narrow.png');
  const layout = await evaluate(`({ width: innerWidth, documentWidth: document.documentElement.scrollWidth, active: document.activeElement?.id, motionReduced: matchMedia('(prefers-reduced-motion: reduce)').matches })`);
  await page('Runtime.evaluate', { expression: 'document.activeElement?.blur()' });
  const focusOrder = [];
  for (let step = 0; step < 9; step += 1) {
    await page('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
    await page('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
    const focused = await evaluate(`({id:document.activeElement?.id,tag:document.activeElement?.tagName,text:document.activeElement?.textContent?.slice(0,70)})`);
    focusOrder.push(focused);
    if (focused.id === 'save') await screenshot('keyboard.png');
  }
  const version = await call('Browser.getVersion');
  const evidence = { browser: version.product, origin, checks, layout, narrowState, focusOrder, exceptions, limitations: ['Synthetic composition events do not prove OS IME behavior.', 'Screenshots require actual visual inspection.', 'Emulated viewport is not a physical device.'] };
  await writeFile(path.join(output, 'browser.json'), JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify({ output, passed: checks.filter(check => check.status === 'pass').length, failed: checks.filter(check => check.status === 'fail').length, notRun: checks.filter(check => check.status === 'not-run').length, exceptions: exceptions.length }));
  if (exceptions.length) process.exitCode = 1;
} finally {
  for (const entry of pending.values()) clearTimeout(entry.timer);
  socket?.close();
  if (chrome && chrome.exitCode === null) {
    const exited = new Promise(resolve => chrome.once('exit', resolve));
    chrome.kill('SIGTERM');
    await Promise.race([exited, pause(2000)]);
    if (chrome.exitCode === null) { chrome.kill('SIGKILL'); await Promise.race([exited, pause(2000)]); }
  }
  await new Promise(resolve => server.close(resolve));
  await rm(profile, { recursive: true, force: true });
}
