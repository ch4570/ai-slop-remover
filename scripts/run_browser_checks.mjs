#!/usr/bin/env node
// Optional maintainer driver: existing Chrome + Node 22+, no installed packages.
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { withBrowser } from './browser_harness.mjs';

const [fixture, outputArg] = process.argv.slice(2);
if (!fixture || !outputArg || process.argv.length !== 4 || typeof WebSocket === 'undefined') {
  console.error('Usage: node scripts/run_browser_checks.mjs <fixture-copy> <evidence-directory> (Node 22+ and Chrome required)');
  process.exit(2);
}
const output = path.resolve(outputArg);
const source = await readFile(new URL('../evals/checks/search-editor.js', import.meta.url), 'utf8');
await withBrowser(fixture, output, async ({ origin, page, evaluate, call, screenshot, pause, exceptions }) => {
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
});
