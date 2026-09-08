import assert from 'node:assert/strict';
import childProcess from 'node:child_process';
import { EventEmitter } from 'node:events';
import fs from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { withBrowser } from '../scripts/browser_harness.mjs';

const completeEndpoint = '9222\n/devtools/browser/startup-control';

for (const scenario of [
  {
    name: 'startup waits for complete valid endpoint data before opening a socket',
    reads: ['', '9222\n', '0\n/devtools/browser/control', '65536\n/devtools/browser/control',
      'port\n/devtools/browser/control', '9222\n/devtools/browser/', '9222\n/wrong/path', completeEndpoint],
  },
  { name: 'startup accepts an immediately complete endpoint', reads: [completeEndpoint] },
  { name: 'startup accepts a complete endpoint with CRLF line endings', reads: [completeEndpoint.replace('\n', '\r\n') + '\r\n'] },
  { name: 'startup stops after 100 incomplete reads and cleans up', reads: ['9222\n'], unavailable: true },
]) {
  test(scenario.name, async t => {
    const fixture = await fs.mkdtemp(path.join(tmpdir(), 'lutriva-startup-test-'));
    const oldChrome = process.env.AI_SLOP_CHROME;
    const oldWebSocket = Object.getOwnPropertyDescriptor(globalThis, 'WebSocket');
    const originalReadFile = fs.readFile;
    const originalSetTimeout = globalThis.setTimeout;
    const attemptedUrls = [], methods = [], delays = [], signals = [];
    let profile, reads = 0, observed = 0, closed = 0;
    t.after(async () => {
      t.mock.restoreAll();
      syncBuiltinESMExports();
      if (oldWebSocket) Object.defineProperty(globalThis, 'WebSocket', oldWebSocket);
      else delete globalThis.WebSocket;
      if (oldChrome === undefined) delete process.env.AI_SLOP_CHROME;
      else process.env.AI_SLOP_CHROME = oldChrome;
      await fs.rm(fixture, { recursive: true, force: true });
    });

    // Exercise withBrowser's startup and cleanup without launching a real process.
    process.env.AI_SLOP_CHROME = process.execPath;
    t.mock.method(childProcess, 'spawn', (executable, args) => {
      assert.equal(executable, process.execPath);
      profile = args.find(arg => arg.startsWith('--user-data-dir=')).slice('--user-data-dir='.length);
      const processControl = new EventEmitter();
      processControl.exitCode = processControl.signalCode = null;
      processControl.kill = signal => {
        signals.push(signal);
        processControl.signalCode = signal;
        processControl.emit('exit', null, signal);
        return true;
      };
      return processControl;
    });
    t.mock.method(fs, 'readFile', async (file, ...options) => {
      if (file === path.join(profile, 'DevToolsActivePort')) {
        return scenario.reads[Math.min(reads++, scenario.reads.length - 1)];
      }
      return originalReadFile(file, ...options);
    });
    t.mock.method(globalThis, 'setTimeout', (callback, delay, ...args) => {
      // Count the real retry budget while avoiding ten seconds of artificial waiting.
      if (delay === 100) delays.push(delay);
      return originalSetTimeout(callback, delay === 100 || delay === 2000 ? 0 : delay, ...args);
    });
    syncBuiltinESMExports();
    globalThis.WebSocket = class extends EventTarget {
      constructor(url) {
        super();
        attemptedUrls.push(url);
        assert.equal(url, 'ws://127.0.0.1:9222/devtools/browser/startup-control');
        setImmediate(() => this.dispatchEvent(new Event('open')));
      }
      send(raw) {
        const { id, method } = JSON.parse(raw);
        methods.push(method);
        const result = method === 'Target.createTarget' ? { targetId: 'control-target' }
          : method === 'Target.attachToTarget' ? { sessionId: 'control-session' } : {};
        setImmediate(() => {
          const event = new Event('message');
          Object.defineProperty(event, 'data', { value: JSON.stringify({ id, result }) });
          this.dispatchEvent(event);
        });
      }
      close() { closed += 1; }
    };

    const run = withBrowser(fixture, path.join(fixture, 'evidence'), async () => {
      observed += 1;
      return 'observed';
    });
    if (scenario.unavailable) {
      await assert.rejects(run, /Chrome debugging endpoint did not become ready/);
      assert.equal(reads, 100);
      assert.equal(delays.length, 100);
      assert.deepEqual(attemptedUrls, []);
      assert.equal(observed, 0);
      assert.equal(closed, 0);
    } else {
      assert.equal(await run, 'observed');
      assert.equal(reads, scenario.reads.length);
      assert.equal(delays.length, scenario.reads.length - 1);
      assert.equal(attemptedUrls.length, 1);
      assert.equal(observed, 1);
      assert.equal(closed, 1);
      assert.deepEqual(methods, ['Target.createTarget', 'Target.attachToTarget',
        'Page.enable', 'Runtime.enable', 'Emulation.setDeviceMetricsOverride']);
    }
    assert.deepEqual(signals, ['SIGTERM']);
    await assert.rejects(fs.lstat(profile), { code: 'ENOENT' });
  });
}
