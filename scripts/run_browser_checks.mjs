#!/usr/bin/env node
// Optional maintainer driver: existing Chrome + Node 22+, no installed packages.
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { claimBrowserEvidence, withBrowser } from './browser_harness.mjs';

const [fixture, outputArg] = process.argv.slice(2);
if (!fixture || !outputArg || process.argv.length !== 4 || typeof WebSocket === 'undefined') {
  console.error('Usage: node scripts/run_browser_checks.mjs <fixture-copy> <evidence-directory> (Node 22+ and Chrome required)');
  process.exit(2);
}
const output = path.resolve(outputArg);
try { await claimBrowserEvidence(output, ['wide.png', 'narrow.png', 'keyboard.png']); }
catch (error) { console.error(String(error)); process.exit(2); }
const source = await readFile(new URL('../evals/checks/search-editor.js', import.meta.url), 'utf8');
const suite = JSON.parse(await readFile(new URL('../evals/checks/suite.json', import.meta.url), 'utf8'));
const required = Object.entries(suite.cases['search-editor']).filter(([, kind]) => kind === 'behavior').map(([id]) => id);
const checks = [], collectionErrors = [], focusOrder = [];
let browser = null, origin = null, layout = null, narrowState = null, exceptions = [];
const observe = async ({ origin: browserOrigin, page, pressKey, evaluate, call, addBinding, screenshot, pause, exceptions: browserExceptions }) => {
  origin = browserOrigin;
  exceptions = browserExceptions;
  browser = (await call('Browser.getVersion')).product;
  let activeCheckIds = new Set();
  // Binding events reach the driver before the evaluation response, even when
  // the originating document is destroyed before its batch can return.
  await addBinding('__lutrivaRecordCheck', payload => {
    try {
      const check = JSON.parse(payload);
      if (!check || !required.includes(check.id) || !activeCheckIds.has(check.id) || check.kind !== 'behavior' ||
          !['pass', 'fail'].includes(check.status) || typeof check.evidence?.text !== 'string') {
        throw new Error('Invalid completed behavior observation.');
      }
      if (checks.some(previous => previous.id === check.id)) throw new Error(`Duplicate behavior observation: ${check.id}`);
      checks.push(check);
    } catch (error) {
      collectionErrors.push('Cannot collect streamed behavior observation: ' + String(error));
    }
  });
  const publishCheck = 'check => globalThis.__lutrivaRecordCheck(JSON.stringify(check))';
  const evaluateBatch = async (name, snapshot, ids) => {
    // Startup and other phases cannot publish observations for this batch.
    activeCheckIds = new Set(ids);
    try { return await evaluate(`${name}(${JSON.stringify(snapshot)}, ${publishCheck})`); }
    finally { activeCheckIds.clear(); }
  };
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
  await screenshot('wide.png');
  const retry = await evaluateBatch('evaluateSearchEditor', snapshot, [
    'search-matches', 'query-history', 'failed-save-draft', 'failed-save-feedback', 'failed-save-storage', 'retry-persists',
  ]);
  checks.push(await observeSavedReload('retry-reload', retry.expected));
  snapshot = await resetFixture();
  const ordinary = await evaluateBatch('evaluateOrdinarySave', snapshot, ['composition-enter', 'ordinary-save']);
  checks.push(await observeSavedReload('ordinary-reload', ordinary.expected));
  snapshot = await resetFixture();
  const enter = await evaluate(`prepareOrdinaryEnter(${JSON.stringify(snapshot)})`);
  if (enter.selectionFound) {
    await pressKey('Enter');
    await pause(150);
  }
  checks.push(await evaluate(`observeOrdinaryEnter(${JSON.stringify(enter)})`));
  checks.push(await observeSavedReload('ordinary-enter-reload', enter.expected));
  snapshot = await resetFixture();
  // Preserve concrete failures and distinguish unavailable observations while
  // later checks run independently, outside the navigated document.
  const observeNavigation = async (id, observe) => {
    let check;
    try {
      check = await observe();
      if (id === 'history-back' || id === 'history-forward') {
        // A concrete mismatch can coexist with a later timeout/read error.
        // A trusted event at the wrong entry is only a behavior failure.
        const { navigations } = JSON.parse(check.evidence.text);
        for (const step of navigations) {
          const errors = [step.trustedPopstate === false ? step.reason : null, step.observationError].filter(Boolean);
          if (errors.length) collectionErrors.push('Navigation ' + id + ': ' + errors.join(' '));
        }
      }
    }
    catch (error) {
      collectionErrors.push('Navigation ' + id + ': ' + String(error));
      check ??= { id, kind: 'behavior', status: 'not-run',
        reason: 'Navigation observation did not complete: ' + String(error) };
    }
    checks.push(check);
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
  narrowState = await evaluate(`(async () => {
    const title = document.getElementById('title');
    title.value = '저장에 실패해도 다시 수정할 수 있어야 하는 긴 한국어 메모 제목';
    title.dispatchEvent(new Event('input', {bubbles:true}));
    document.getElementById('fail-save').checked = true;
    document.getElementById('save').click();
    await new Promise(resolve => setTimeout(resolve, 150));
    return {title:title.value,status:document.getElementById('status').dataset.state,feedback:document.getElementById('status').textContent};
  })()`);
  await screenshot('narrow.png');
  layout = await evaluate(`({ width: innerWidth, documentWidth: document.documentElement.scrollWidth, active: document.activeElement?.id, motionReduced: matchMedia('(prefers-reduced-motion: reduce)').matches })`);
  await page('Runtime.evaluate', { expression: 'document.activeElement?.blur()' });
  for (let step = 0; step < 9; step += 1) {
    await pressKey('Tab');
    const focused = await evaluate(`({id:document.activeElement?.id,tag:document.activeElement?.tagName,text:document.activeElement?.textContent?.slice(0,70)})`);
    focusOrder.push(focused);
    if (focused.id === 'save') await screenshot('keyboard.png', { captureBeyondViewport: false });
  }
};
try {
  await withBrowser(fixture, output, observe);
} catch (error) {
  collectionErrors.push(String(error));
}
// Keep completed observations even when a later reload, image or transport fails.
// Every remaining suite check is explicitly unobserved, never an invented pass.
const recorded = new Map(checks.map(check => [check.id, check]));
const completeChecks = required.map(id => recorded.get(id) || {
  id, kind: 'behavior', status: 'not-run',
  reason: 'Browser collection did not complete this observation: ' + (collectionErrors.join(' ') || 'Required observation was not collected.'),
});
const evidence = { browser, origin, checks: completeChecks, layout, narrowState, focusOrder, exceptions, collectionErrors,
  limitations: ['Synthetic composition events do not prove OS IME behavior.', 'Screenshots require actual visual inspection.', 'Emulated viewport is not a physical device.'] };
await mkdir(output, { recursive: true });
await writeFile(path.join(output, 'browser.json'), JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify({ output, passed: completeChecks.filter(check => check.status === 'pass').length, failed: completeChecks.filter(check => check.status === 'fail').length, notRun: completeChecks.filter(check => check.status === 'not-run').length, exceptions: exceptions.length, collectionErrors: collectionErrors.length }));
if (exceptions.length || collectionErrors.length) process.exitCode = 1;
