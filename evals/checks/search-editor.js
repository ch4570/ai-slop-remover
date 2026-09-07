/* Evaluator-owned: load in a fresh fixture tab, then await evaluateSearchEditor().
   Synthetic events verify app handlers; they do not prove OS-level IME behavior. */
async function evaluateSearchEditor() {
  const results = [];
  const el = id => document.getElementById(id);
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const input = (id, value) => {
    el(id).value = value;
    el(id).dispatchEvent(new Event('input', { bubbles: true }));
  };
  const record = (id, pass, observed) => results.push({
    id, kind: 'behavior', status: pass ? 'pass' : 'fail',
    evidence: { text: JSON.stringify(observed) },
  });
  const saved = () => JSON.parse(localStorage.getItem('haneul-eval-notes') || 'null');
  if (!['query', 'notes', 'title', 'body', 'editor', 'save', 'fail-save', 'status'].every(el)) {
    throw new Error('Fixture DOM contract is missing; behavior checks were not run.');
  }
  const initialHistory = history.length;
  input('query', '배'); input('query', '배송'); input('query', '배송 확인');
  record('search-matches', el('notes').children.length === 1 && el('notes').textContent.includes('배송 확인'), {
    query: el('query').value, matches: el('notes').textContent,
  });
  record('query-history', history.length === initialHistory && new URL(location.href).searchParams.get('q') === '배송 확인', {
    before: initialHistory, after: history.length, urlQuery: new URL(location.href).searchParams.get('q'),
  });
  input('query', '');
  el('notes').querySelector('button').click();
  input('title', '실패해도 남아야 하는 초안');
  input('body', '저장 재시도에 사용할 내용');
  el('fail-save').checked = true;
  const beforeFailure = localStorage.getItem('haneul-eval-notes');
  el('save').click();
  await wait(150);
  const failure = {
    title: el('title').value, body: el('body').value, feedback: el('status').textContent,
    state: el('status').dataset.state, disabled: el('save').disabled,
    storageUnchanged: localStorage.getItem('haneul-eval-notes') === beforeFailure,
  };
  record('failed-save-draft', failure.title === '실패해도 남아야 하는 초안' && failure.body === '저장 재시도에 사용할 내용' && failure.storageUnchanged, failure);
  record('failed-save-feedback', failure.state === 'error' && !failure.disabled && /실패|못|오류/.test(failure.feedback), failure);
  el('fail-save').checked = false;
  el('save').click();
  await wait(150);
  const persisted = saved()?.find(note => note.id === 1);
  record('retry-persists', persisted?.title === '실패해도 남아야 하는 초안' && persisted?.body === '저장 재시도에 사용할 내용' && !el('save').disabled, {
    persisted, feedback: el('status').textContent, disabled: el('save').disabled,
  });
  let submissions = 0;
  const observeSubmit = () => { submissions += 1; };
  el('editor').addEventListener('submit', observeSubmit, true);
  const beforeComposition = localStorage.getItem('haneul-eval-notes');
  input('title', '한글 조합 중');
  el('title').dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }));
  el('title').dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', isComposing: true, bubbles: true, cancelable: true }));
  el('title').dispatchEvent(new CompositionEvent('compositionend', { data: '중', bubbles: true }));
  await wait(150);
  record('composition-enter', submissions === 0 && localStorage.getItem('haneul-eval-notes') === beforeComposition, {
    syntheticComposition: true, submissions, storageUnchanged: localStorage.getItem('haneul-eval-notes') === beforeComposition,
  });
  el('editor').removeEventListener('submit', observeSubmit, true);
  input('title', '저장 성공 확인');
  el('save').click();
  await wait(150);
  record('ordinary-save', saved()?.find(note => note.id === 1)?.title === '저장 성공 확인' && !el('save').disabled, {
    persisted: saved()?.find(note => note.id === 1), feedback: el('status').textContent,
  });
  return results;
}

// Dispatch a real browser Enter key between these functions. A synthetic DOM
// KeyboardEvent cannot exercise native implicit form submission correctly.
function prepareOrdinaryEnter() {
  const title = document.getElementById('title');
  title.value = 'Enter로 저장한 메모';
  title.dispatchEvent(new Event('input', { bubbles: true }));
  title.focus();
}
function observeOrdinaryEnter() {
  const persisted = JSON.parse(localStorage.getItem('haneul-eval-notes') || 'null')?.find(note => note.id === 1);
  const disabled = document.getElementById('save').disabled;
  return {
    id: 'ordinary-enter', kind: 'behavior',
    status: persisted?.title === 'Enter로 저장한 메모' && !disabled ? 'pass' : 'fail',
    evidence: { text: JSON.stringify({ browserKeyboard: true, persisted, disabled }) },
  };
}
