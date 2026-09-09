// Installed Chrome transport only; adapters own readiness, seeds and assertions.
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { access, lstat, mkdir, mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const keys = {
  Tab: { key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 },
  Enter: { key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r' },
  Escape: { key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 },
  Space: { key: ' ', code: 'Space', windowsVirtualKeyCode: 32, text: ' ' },
};

// Bounded DOM key presses. CDP uses Shift=8; native key codes are platform-specific.
export async function pressKey(page, key, options = {}) {
  if (typeof key !== 'string' || !Object.hasOwn(keys, key)) {
    throw new TypeError('pressKey supports only Tab, Enter, Escape, and Space.');
  }
  if (options === null || typeof options !== 'object' ||
      ![Object.prototype, null].includes(Object.getPrototypeOf(options)) ||
      Reflect.ownKeys(options).some(name => name !== 'shift') ||
      (Object.hasOwn(options, 'shift') && typeof options.shift !== 'boolean')) {
    throw new TypeError('pressKey options support only a boolean shift.');
  }
  const { text, ...identity } = keys[key];
  const event = { ...identity, modifiers: options.shift ? 8 : 0 };
  await page('Input.dispatchKeyEvent', { type: 'keyDown', ...event, ...(text === undefined ? {} : { text }) });
  await page('Input.dispatchKeyEvent', { type: 'keyUp', ...event });
}

export async function claimBrowserEvidence(outputArg, imagePaths) {
  const output = path.resolve(outputArg);
  const marker = '.browser-evidence-started';
  const reused = () => new Error(`Browser evidence already exists or collection has started at ${output}; use a new output path. Existing artifacts were preserved.`);
  // Check only the adapter's browser artifacts; prepared scope metadata may exist.
  for (const name of ['browser.json', ...imagePaths, marker]) {
    try { await lstat(path.join(output, name)); }
    catch (error) { if (error.code === 'ENOENT') continue; throw error; }
    throw reused();
  }
  await mkdir(output, { recursive: true });
  try {
    // Exclusive creation admits one collector. Keep the marker after interruption
    // and completion so neither an unfinished nor a completed run can be reused.
    await writeFile(path.join(output, marker), 'Browser evidence collection started. Use a new output path for another collection.\n', { flag: 'wx' });
  } catch (error) {
    if (error.code === 'EEXIST') throw reused();
    throw error;
  }
}

export async function withBrowser(fixtureArg, outputArg, observe) {
  if (typeof WebSocket === 'undefined') throw new Error('Browser checks require Node 22+ with WebSocket.');
  const fixture = await realpath(fixtureArg);
  const output = path.resolve(outputArg);
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
  const pending = new Map(), bindings = new Map();
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
      try {
        // Chrome can create this file before both endpoint lines are written.
        const candidate = (await readFile(path.join(profile, 'DevToolsActivePort'), 'utf8')).trim().split(/\r?\n/);
        const [port, browserPath] = candidate;
        if (candidate.length === 2 && /^\d+$/.test(port) && Number(port) >= 1 && Number(port) <= 65535 &&
            /^\/devtools\/browser\/[^/?#\s]+$/.test(browserPath)) {
          debug = candidate;
          break;
        }
      } catch { /* Wait for Chrome to publish the endpoint file. */ }
      await pause(100);
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
      if (message.method === 'Runtime.bindingCalled') {
        const binding = bindings.get(message.params.name);
        if (binding?.sessionId === message.sessionId) binding.receive(message.params.payload);
      }
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
    const addBinding = async (name, receive) => {
      if (bindings.has(name)) throw new Error(`Page binding already registered: ${name}`);
      bindings.set(name, { sessionId, receive });
      try { await page('Runtime.addBinding', { name }); }
      catch (error) { bindings.delete(name); throw error; }
    };
    const evaluate = async expression => {
      const result = await page('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
      return result.result.value;
    };
    await page('Page.enable'); await page('Runtime.enable');
    await page('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
    await mkdir(output, { recursive: true });
    // Full-page capture can reframe scroll containers; focus evidence needs viewport mode.
    const screenshot = async (name, { captureBeyondViewport = true } = {}) => {
      const result = await page('Page.captureScreenshot', { format: 'png', captureBeyondViewport });
      await writeFile(path.join(output, name), Buffer.from(result.data, 'base64'));
    };
    return await observe({ origin, page, pressKey: (key, options) => pressKey(page, key, options),
      evaluate, call, addBinding, screenshot, pause, exceptions });
  } finally {
    for (const entry of pending.values()) clearTimeout(entry.timer);
    socket?.close();
    if (chrome && chrome.exitCode === null && chrome.signalCode === null) {
      const exited = new Promise(resolve => chrome.once('exit', resolve));
      chrome.kill('SIGTERM');
      await Promise.race([exited, pause(2000)]);
      if (chrome.exitCode === null && chrome.signalCode === null) { chrome.kill('SIGKILL'); await Promise.race([exited, pause(2000)]); }
    }
    await new Promise(resolve => server.close(resolve));
    // Chrome helpers can finish profile writes just after the browser exits.
    await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
  }
}
