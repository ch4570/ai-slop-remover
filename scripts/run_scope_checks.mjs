#!/usr/bin/env node
// Evaluator-owned bounded browser observations. Semantic/visual verdicts stay human-owned.
import { lstat, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { claimBrowserEvidence, withBrowser } from './browser_harness.mjs';

const suites = JSON.parse(await readFile(new URL('../evals/checks/scope-suites.json', import.meta.url), 'utf8'));
const [caseId, fixture, outputArg] = process.argv.slice(2);
const required = {
  'narrow-spacing': ['spacing-and-state'],
  'audit-read-only': ['audit-observation'],
  'empty-state-copy-only': ['search-and-names'],
  'master-page-consistency': ['shared-master-preserved', 'compare-density-and-actions'],
};
if (process.argv.length !== 5 || !suites[caseId + '-v1'] || !fixture || !outputArg) {
  console.error('Usage: node scripts/run_scope_checks.mjs <case> <product-copy> <trial-directory> (Node 22+ and installed Chrome)');
  process.exit(2);
}
const output = path.resolve(outputArg);
try { await claimBrowserEvidence(output, ['images']); }
catch (error) { console.error(String(error)); process.exit(2); }
await mkdir(path.join(output, 'images'), { recursive: true });
const checks = new Map(required[caseId].map(id => [id, { id, kind: 'behavior', status: 'not-run', reason: 'Installed Chrome observation has not completed.' }]));
const observations = { images: [], focus: [], collectionErrors: [] };
let environment = {};

async function observe(id, callback) {
  const facts = [];
  let failed = false;
  try {
    await callback((matches, detail) => { failed ||= !matches; facts.push({ matches, detail }); });
    checks.set(id, { id, kind: 'behavior', status: failed ? 'fail' : 'pass', evidence: { path: 'browser.json', text: JSON.stringify(facts) } });
  } catch (error) {
    observations.collectionErrors.push('Observation ' + id + ': ' + String(error));
    checks.set(id, { id, kind: 'behavior', status: failed ? 'fail' : 'not-run',
      ...(failed ? {} : { reason: 'Browser observation did not complete: ' + String(error) }),
      evidence: { path: 'browser.json', text: JSON.stringify({ facts, error: String(error) }) } });
  }
}

try {
  const productType = await lstat(fixture);
  if (productType.isSymbolicLink() || !productType.isDirectory()) throw new Error('Product root must be an ordinary directory; no browser traversal was attempted.');
  await withBrowser(fixture, path.join(output, 'images'), async ({ origin, page, pressKey, evaluate, call, screenshot, pause, exceptions }) => {
    environment = { browser: (await call('Browser.getVersion')).product, node: process.version, origin };
    const navigate = async (relative = '') => {
      const previous = await evaluate('performance.timeOrigin');
      await page('Page.navigate', { url: origin + '/' + relative });
      for (let attempt = 0; attempt < 100; attempt += 1) {
        try {
          const ready = await evaluate(`location.origin === ${JSON.stringify(origin)} && performance.timeOrigin !== ${JSON.stringify(previous)} && document.readyState === 'complete' && !!document.querySelector('main') && (${caseId === 'empty-state-copy-only' ? "document.documentElement.dataset.ready === 'true'" : 'true'})`);
          if (ready) return;
        } catch { /* Navigation replaces the execution context. */ }
        await pause(50);
      }
      throw new Error('Fixture did not finish loading');
    };
    const capture = async (name, options) => {
      try { await screenshot(name, options); observations.images.push('images/' + name); }
      catch (error) { observations.collectionErrors.push('Screenshot ' + name + ': ' + String(error)); }
    };
    const setQuery = async (id, value) => evaluate(`(() => { const input = document.getElementById(${JSON.stringify(id)}); input.value = ${JSON.stringify(value)}; input.dispatchEvent(new Event('input', { bubbles: true })); })()`);
    const tab = async () => {
      await pressKey('Tab');
      return evaluate(`(() => { const element = document.activeElement; const style = getComputedStyle(element); return { id: element.id, tag: element.tagName, text: element.textContent.trim().slice(0, 80), outline: style.outline, boxShadow: style.boxShadow, focusVisible: element.matches(':focus-visible') }; })()`);
    };
    const rows = `Array.from(document.querySelectorAll('tbody tr')).map(row => Array.from(row.cells).slice(0,4).map(cell => cell.textContent))`;
    const expectedRows = [['M-101', '김민지', '머그', '12,000원'], ['M-102', '박도윤', '접시', '18,000원'], ['M-103', '이서연', '잔', '9,000원']];
    const checkTable = async (report, expectedPadding) => {
      const state = await evaluate(`({ rows: ${rows}, padding: getComputedStyle(document.querySelector('td')).paddingTop, brand: getComputedStyle(document.querySelector('header')).backgroundColor, radius: getComputedStyle(document.querySelector('.table-scroll')).borderRadius, count: document.querySelectorAll('[data-order]').length })`);
      report(JSON.stringify(state.rows) === JSON.stringify(expectedRows) && state.count === 3 && expectedPadding.includes(state.padding) && state.brand === 'rgb(35, 89, 66)' && state.radius === '8px', state);
      const actions = [];
      for (const order of ['M-101', 'M-102', 'M-103']) {
        actions.push(await evaluate(`(() => { document.querySelector('[data-order="${order}"]').click(); return document.getElementById('detail').textContent; })()`));
      }
      report(actions.every((text, index) => text === ['M-101', 'M-102', 'M-103'][index] + ' 주문을 선택했습니다.'), { actions });
    };

    if (caseId === 'narrow-spacing') {
      await observe('spacing-and-state', async report => {
        await navigate();
        const state = await evaluate(`({ margin: getComputedStyle(document.querySelector('.actions')).marginTop, brand: getComputedStyle(document.getElementById('save')).backgroundColor, text: document.getElementById('save').textContent, title: document.querySelector('h1').textContent })`);
        report(state.margin === '16px' && state.brand === 'rgb(35, 89, 66)' && state.text === '변경 저장' && state.title === '계정 설정', state);
        await setQuery('name', '긴 한국어 이름을 저장하고 다시 확인합니다');
        await evaluate("document.getElementById('save').click()");
        await pause(150);
        const saved = await evaluate(`({ value: localStorage.getItem('display-name'), state: document.getElementById('status').dataset.state, feedback: document.getElementById('status').textContent, disabled: document.getElementById('save').disabled })`);
        report(saved.value === '긴 한국어 이름을 저장하고 다시 확인합니다' && saved.state === 'success' && saved.feedback === '변경 사항을 저장했습니다.' && !saved.disabled, saved);
        await navigate();
        const restored = await evaluate("document.getElementById('name').value");
        report(restored === saved.value, { restored });
      });
    } else if (caseId === 'audit-read-only') {
      await observe('audit-observation', async report => {
        await navigate();
        const state = await evaluate(`({ promotionHeight: document.querySelector('.promotion').getBoundingClientRect().height, ordersTop: document.getElementById('orders').getBoundingClientRect().top, rows: document.querySelectorAll('tbody tr').length })`);
        report(state.rows === 2, state);
        await setQuery('order-search', '김민지');
        const visible = await evaluate("Array.from(document.querySelectorAll('tbody tr')).filter(row => !row.hidden).map(row => row.cells[0].textContent)");
        report(JSON.stringify(visible) === '["M-101"]', { visible });
        await evaluate("document.querySelector('[data-order=\"M-101\"]').click()");
        const detail = await evaluate("document.getElementById('detail').textContent");
        report(detail === 'M-101 상세를 확인 중입니다.', { detail });
        await setQuery('order-search', '');
      });
    } else if (caseId === 'empty-state-copy-only') {
      await observe('search-and-names', async report => {
        await navigate();
        const query = '없는 자료';
        await setQuery('query', query);
        const noMatch = await evaluate(`({ hidden: document.getElementById('empty').hidden, state: document.getElementById('empty').dataset.state, title: document.getElementById('empty-title').textContent, name: document.getElementById('empty-title').getAttribute('aria-label'), body: document.getElementById('empty-body').textContent, labelledby: document.getElementById('empty').getAttribute('aria-labelledby'), describedby: document.getElementById('empty').getAttribute('aria-describedby'), controls: document.getElementById('query').getAttribute('aria-controls'), results: document.querySelectorAll('#results li').length })`);
        report(!noMatch.hidden && noMatch.state === 'no-match' && noMatch.title.includes(query) && noMatch.name.includes(query) && !noMatch.title.includes('{query}') && !noMatch.name.includes('{query}') && noMatch.labelledby === 'empty-title' && noMatch.describedby === 'empty-body' && noMatch.controls === 'results' && noMatch.results === 0, noMatch);
        const ax = await page('Accessibility.getFullAXTree');
        observations.noMatchAX = ax.nodes.filter(node => !node.ignored).map(node => ({ role: node.role?.value, name: node.name?.value, description: node.description?.value }));
        report(observations.noMatchAX.some(node => node.role === 'heading' && node.name === noMatch.name), { accessibleHeadings: observations.noMatchAX.filter(node => node.role === 'heading') });
        await setQuery('query', '배송');
        const recovered = await evaluate(`({ hidden: document.getElementById('empty').hidden, results: Array.from(document.querySelectorAll('#results li')).map(item => item.textContent), count: document.getElementById('count').textContent })`);
        report(recovered.hidden && JSON.stringify(recovered.results) === '["배송 안내","정기 배송 일정"]' && recovered.count === '2개 자료', recovered);
        await navigate('?empty=1');
        const never = await evaluate(`({ state: document.getElementById('empty').dataset.state, title: document.getElementById('empty-title').textContent, body: document.getElementById('empty-body').textContent })`);
        report(never.state === 'never-populated' && never.title === '저장된 항목이 없습니다.' && never.body === '등록된 항목은 이 목록에 표시됩니다.', never);
        await navigate('?lang=en');
        await setQuery('query', query);
        const english = await evaluate("document.getElementById('empty-title').textContent");
        report(english === 'No results for “없는 자료”.', { english });
        await navigate();
        await setQuery('query', '없는 자료');
      });
    } else {
      await observe('shared-master-preserved', async report => {
        await navigate('master.html');
        await checkTable(report, ['16px']);
        await capture('master-wide.png');
      });
      await observe('compare-density-and-actions', async report => {
        await navigate('compare.html');
        await checkTable(report, ['8px', '9px', '10px', '11px', '12px']);
      });
    }
    await capture('wide.png');
    await page('Emulation.setDeviceMetricsOverride', { width: 375, height: 844, deviceScaleFactor: 1, mobile: true });
    await page('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    if (caseId === 'empty-state-copy-only') await setQuery('query', '검색 결과가 없는 길고 구체적인 한국어 자료 이름');
    observations.layout = await evaluate(`({ width: innerWidth, documentWidth: document.documentElement.scrollWidth, tableWidth: document.querySelector('.table-scroll')?.scrollWidth, tableViewport: document.querySelector('.table-scroll')?.clientWidth })`);
    await capture('narrow.png');
    // Reset navigation focus to the start; every captured focus comes from real Tab.
    await evaluate("document.activeElement?.blur(); document.body.tabIndex = -1; document.body.focus(); document.body.removeAttribute('tabindex')");
    for (let step = 0; step < 8; step += 1) {
      const focused = await tab();
      observations.focus.push(focused);
      if ((caseId === 'narrow-spacing' && focused.id === 'save') ||
          (caseId === 'audit-read-only' && focused.id === 'order-search') ||
          (caseId === 'empty-state-copy-only' && focused.id === 'query') ||
          (caseId === 'master-page-consistency' && focused.tag === 'BUTTON')) {
        await capture('keyboard.png', { captureBeyondViewport: false });
        break;
      }
    }
    observations.exceptions = exceptions;
  });
} catch (error) {
  observations.collectionErrors.push(String(error));
  for (const [id, check] of checks) if (check.status === 'not-run') checks.set(id, { ...check, reason: 'Installed Chrome collection unavailable: ' + String(error) });
}
const result = { schema: 1, case: caseId, environment, checks: [...checks.values()], observations,
  limits: ['Source scope is checked separately.', 'Accessible names are captured, not semantically judged by string matching.', 'Images and diagnoses need independent human review.', 'An emulated viewport is not a physical device or screen reader test.'] };
await writeFile(path.join(output, 'browser.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ case: caseId, output, checks: result.checks.map(({ id, status }) => ({ id, status })) }));
